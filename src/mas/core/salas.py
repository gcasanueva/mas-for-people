"""Gestor de salas: abre salas, reparte turnos, valida respuestas y cierra.

Es el "moderador" del lado del servidor: no razona, solo aplica el
protocolo. Claude hace de cada agente por turnos (ver la ERS, "Ciclo de
turnos de una sala"):

    abrir_sala -> (siguiente_turno -> Claude responde -> publicar_turno)... -> veredicto x2

No importa nada de MCP (RNF-01): el servidor y las pruebas lo usan igual.
"""

from __future__ import annotations

from importlib import resources
from typing import Any

from pydantic import ValidationError

from . import textos
from .almacen import Almacen
from .catalogo import Catalogo, NoEncontrado, parsear_agente
from .formatos import FormatoSalida, formato, secciones_faltantes
from .modelos import (
    Agente,
    Artefacto,
    EstadoSala,
    Mesa,
    Protocolo,
    Sala,
    Turno,
    Veredicto,
    contar_palabras,
    traducir_errores,
)
from .protocolos import ProtocoloSala, TransicionInvalida, disponibles, obtener
from .vistas import vista_hilos, vista_lista_salas, vista_mesa, vista_veredicto

# Contar palabras es aproximado: se deja un margen antes de rechazar (RF-14).
TOLERANCIA_PALABRAS = 1.1

LISTO_PARA_VEREDICTO = "listo_para_veredicto"


class ErrorSala(Exception):
    """Algo que Claude o el usuario deben corregir (mensaje en español)."""


def cargar_verificador() -> Agente:
    """El agente de sistema que escribe el veredicto (viene con el programa)."""
    texto = resources.files("mas.core").joinpath("sistema/verificador.md").read_text(encoding="utf-8")
    resultado = parsear_agente(texto, "sistema/verificador.md")
    if isinstance(resultado, list):  # pragma: no cover - lo cubre una prueba
        raise RuntimeError("; ".join(str(e) for e in resultado))
    return resultado


def _formato_dict(fmt: FormatoSalida) -> dict[str, Any]:
    return {"id": fmt.id, "nombre": fmt.nombre, "secciones": list(fmt.secciones)}


def _limite(max_palabras: int) -> int:
    return int(max_palabras * TOLERANCIA_PALABRAS)


class GestorSalas:
    """Lógica de las herramientas de sala sobre un catálogo y un almacén."""

    def __init__(self, catalogo: Catalogo, almacen: Almacen) -> None:
        self.catalogo = catalogo
        self.almacen = almacen
        self.verificador = cargar_verificador()

    # Ayudas ------------------------------------------------------------------

    def _sala(self, sala_id: str) -> Sala:
        sala = self.almacen.sala(sala_id.strip())
        if sala is None:
            raise ErrorSala(textos.SALA_NO_ENCONTRADA.format(id=sala_id))
        return sala

    @staticmethod
    def _protocolo(sala: Sala) -> ProtocoloSala:
        proto = obtener(sala.protocolo)
        if proto is None:
            raise ErrorSala(
                textos.PROTOCOLO_NO_DISPONIBLE.format(
                    protocolo=sala.protocolo.value, disponibles=", ".join(p.value for p in disponibles())
                )
            )
        return proto

    def _agente(self, agente_id: str) -> Agente:
        try:
            return self.catalogo.agente(agente_id)
        except NoEncontrado:
            raise ErrorSala(textos.SALA_AGENTE_INEXISTENTE.format(id=agente_id)) from None

    def _cambiar_estado(self, con: Any, sala: Sala, proto: ProtocoloSala, estado: EstadoSala) -> None:
        try:
            proto.validar_transicion(sala.estado, estado)
        except TransicionInvalida as exc:
            raise ErrorSala(str(exc)) from None
        if sala.estado != estado:
            self.almacen.cambiar_estado(con, sala.id, estado)
            sala.estado = estado

    # abrir_sala --------------------------------------------------------------

    def abrir_sala(
        self,
        objetivo: str,
        agentes: list[str],
        protocolo: str = Protocolo.PANEL.value,
        max_rondas: int = 2,
        max_palabras: int = 400,
        posturas: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Crea la sala y devuelve su id y el orden de turnos previsto (RF-05)."""
        self.catalogo.recargar()
        try:
            proto_enum = Protocolo(protocolo.strip().lower())
        except ValueError:
            raise ErrorSala(
                textos.PROTOCOLO_DESCONOCIDO.format(
                    protocolo=protocolo, disponibles=", ".join(p.value for p in Protocolo)
                )
            ) from None
        agentes = [a.strip() for a in agentes]
        faltan = [a for a in agentes if a not in self.catalogo.agentes]
        if faltan:
            raise ErrorSala(" ".join(textos.SALA_AGENTE_INEXISTENTE.format(id=a) for a in faltan))
        posturas = {k.strip(): v for k, v in (posturas or {}).items() if v and v.strip()}
        fuera = [k for k in posturas if k not in agentes]
        if fuera:
            raise ErrorSala(" ".join(textos.SALA_POSTURA_FUERA.format(id=k) for k in fuera))
        try:
            sala = Sala(
                objetivo=objetivo,
                agentes=agentes,
                posturas=posturas,
                protocolo=proto_enum,
                max_rondas=1 if proto_enum is Protocolo.PANEL else max_rondas,
                max_palabras=max_palabras,
            )
        except ValidationError as exc:
            raise ErrorSala(" ".join(str(e) for e in traducir_errores(exc, "sala"))) from None
        proto = self._protocolo(sala)
        self.almacen.crear_sala(sala)
        return {
            "sala_id": sala.id,
            "protocolo": sala.protocolo.value,
            "estado": sala.estado.value,
            "max_palabras": sala.max_palabras,
            "plan": [p.como_dict() for p in proto.plan(sala)],
            "indicacion": textos.SALA_ABIERTA,
        }

    # siguiente_turno ---------------------------------------------------------

    def siguiente_turno(self, sala_id: str) -> dict[str, Any]:
        """Crea (o repite, si sigue pendiente) el turno que toca (RF-06)."""
        self.catalogo.recargar()
        with self.almacen.transaccion() as con:
            sala = self.almacen.sala(sala_id.strip(), con)
            if sala is None:
                raise ErrorSala(textos.SALA_NO_ENCONTRADA.format(id=sala_id))
            if sala.estado is EstadoSala.CERRADA:
                raise ErrorSala(textos.SALA_CERRADA.format(id=sala.id))
            proto = self._protocolo(sala)
            turnos = self.almacen.turnos(sala.id, con)
            if sala.estado is EstadoSala.VERIFICACION:
                return self._listo(sala)
            pendiente = next((t for t in turnos if t.artefacto is None), None)
            if pendiente is None:
                paso = proto.siguiente(sala, turnos)
                if paso is None:
                    return self._listo(sala)
                self._agente(paso.agente_id)  # el agente aún existe en el catálogo
                pendiente = Turno(sala_id=sala.id, agente_id=paso.agente_id, ronda=paso.ronda)
                self.almacen.crear_turno(con, pendiente, paso.orden)
                self._cambiar_estado(con, sala, proto, proto.estado_de_ronda(paso.ronda))
                turnos.append(pendiente)
        return self._contexto_turno(sala, proto, pendiente, turnos)

    @staticmethod
    def _listo(sala: Sala) -> dict[str, Any]:
        return {"sala_id": sala.id, "estado": LISTO_PARA_VEREDICTO, "indicacion": textos.LISTO_PARA_VEREDICTO}

    def _contexto_turno(
        self, sala: Sala, proto: ProtocoloSala, turno: Turno, turnos: list[Turno]
    ) -> dict[str, Any]:
        """Lo único que recibe el agente: instrucciones, skills, hilo y mesa (RF-06, RNF-02)."""
        agente = self._agente(turno.agente_id)
        fmt = formato(agente.formato_salida)
        assert fmt is not None  # el modelo Agente ya valida el formato
        postura = sala.posturas.get(agente.id, agente.postura)
        publicados = [t for t in turnos if t.artefacto is not None]
        hilo = [{"ronda": t.ronda, "contenido": t.contenido} for t in publicados if t.agente_id == agente.id]
        ve_mesa = proto.ve_mesa(sala, turno.ronda)
        resumen_mesa = Mesa.desde_turnos(sala.id, publicados).resumen(excluir=agente.id) if ve_mesa else []
        skills = [
            {"id": s.id, "descripcion": s.descripcion, "instrucciones": s.instrucciones}
            for s in self.catalogo.skills_de(agente)
        ]
        restantes = len(proto.plan(sala)) - len(publicados) - 1
        datos: dict[str, Any] = {
            "sala_id": sala.id,
            "turno_id": turno.id,
            "objetivo": sala.objetivo,
            "agente": {"id": agente.id, "nombre": agente.nombre, "postura": postura},
            "ronda": turno.ronda,
            "instrucciones": agente.instrucciones,
            "skills": skills,
            "hilo": hilo,
            "resumen_mesa": resumen_mesa,
            "formato_salida": _formato_dict(fmt),
            "max_palabras": sala.max_palabras,
            "posturas_artefacto": sorted(p.value for p in proto.posturas_permitidas(turno.ronda)),
            "turnos_restantes": max(restantes, 0),
            "indicacion": textos.TURNO_INDICACION.format(
                nombre=agente.nombre,
                postura=postura,
                secciones=", ".join(fmt.secciones),
                max_palabras=sala.max_palabras,
                mesa=textos.TURNO_INDICACION_MESA if ve_mesa else textos.TURNO_INDICACION_SIN_MESA,
            ),
        }
        if agente.sensible and agente.aviso:
            datos["aviso"] = agente.aviso
        datos["palabras_contexto"] = palabras_contexto(datos)
        return datos

    # publicar_turno ----------------------------------------------------------

    def publicar_turno(
        self, sala_id: str, turno_id: str, contenido: str, artefacto: dict[str, Any] | Artefacto
    ) -> dict[str, Any]:
        """Valida la respuesta del agente y la guarda en su hilo y en la mesa (RF-07).

        Si algo no cumple, no guarda nada y devuelve ``ok: False`` con la
        lista de cosas a corregir (CA-05).
        """
        self.catalogo.recargar()
        with self.almacen.transaccion() as con:
            sala = self.almacen.sala(sala_id.strip(), con)
            if sala is None:
                raise ErrorSala(textos.SALA_NO_ENCONTRADA.format(id=sala_id))
            if sala.estado is EstadoSala.CERRADA:
                raise ErrorSala(textos.SALA_CERRADA.format(id=sala.id))
            proto = self._protocolo(sala)
            turnos = self.almacen.turnos(sala.id, con)
            turno = next((t for t in turnos if t.id == turno_id.strip()), None)
            if turno is None:
                raise ErrorSala(textos.TURNO_NO_ENCONTRADO.format(turno_id=turno_id, sala_id=sala.id))
            if turno.artefacto is not None:
                raise ErrorSala(textos.TURNO_YA_PUBLICADO.format(turno_id=turno.id))
            agente = self._agente(turno.agente_id)

            errores: list[str] = []
            art: Artefacto | None = None
            try:
                art = artefacto if isinstance(artefacto, Artefacto) else Artefacto.model_validate(artefacto)
            except ValidationError as exc:
                errores += [str(e) for e in traducir_errores(exc, "artefacto")]
            if art is not None:
                permitidas = proto.posturas_permitidas(turno.ronda)
                if art.postura not in permitidas:
                    errores.append(
                        textos.TURNO_POSTURA_NO_PERMITIDA.format(
                            permitidas=", ".join(sorted(p.value for p in permitidas)), postura=art.postura.value
                        )
                    )
                ids = {t.id for t in turnos}
                errores += [textos.TURNO_RESPONDE_A_INEXISTENTE.format(id=r) for r in art.responde_a if r not in ids]
            errores += self._errores_texto(contenido, agente.formato_salida, sala.max_palabras)
            if errores:
                return {"ok": False, "errores": errores, "indicacion": textos.TURNO_CORREGIR}

            assert art is not None
            turno = turno.model_copy(update={"contenido": contenido.strip(), "artefacto": art})
            self.almacen.publicar_turno(con, turno)
            publicados = sum(1 for t in turnos if t.artefacto is not None) + 1
            quedan = proto.siguiente(sala, turnos) is not None
        return {
            "ok": True,
            "turno_id": turno.id,
            "palabras": turno.palabras,
            "turnos_publicados": publicados,
            "indicacion": textos.TURNO_PUBLICADO_SIGUE if quedan else textos.TURNO_PUBLICADO_VEREDICTO,
        }

    @staticmethod
    def _errores_texto(contenido: str, id_formato: str, max_palabras: int) -> list[str]:
        errores: list[str] = []
        fmt = formato(id_formato)
        if not contenido or not contenido.strip():
            return [textos.CONTENIDO_VACIO]
        if fmt is not None:
            faltan = secciones_faltantes(contenido, fmt)
            if faltan:
                errores.append(
                    textos.TURNO_FALTAN_SECCIONES.format(formato=fmt.nombre, faltan=", ".join(faltan), ejemplo=faltan[0])
                )
        palabras = contar_palabras(contenido)
        if palabras > _limite(max_palabras):
            errores.append(textos.TURNO_DEMASIADO_LARGO.format(palabras=palabras, limite=max_palabras))
        return errores

    # veredicto ---------------------------------------------------------------

    def veredicto(
        self,
        sala_id: str,
        contenido: str | None = None,
        acuerdos: list[str] | None = None,
        desacuerdos: list[str] | None = None,
        confianza: float | None = None,
        plan: list[str] | None = None,
    ) -> dict[str, Any]:
        """Primera llamada: turno del verificador. Segunda (con contenido): guarda y cierra (RF-09)."""
        with self.almacen.transaccion() as con:
            sala = self.almacen.sala(sala_id.strip(), con)
            if sala is None:
                raise ErrorSala(textos.SALA_NO_ENCONTRADA.format(id=sala_id))
            if sala.estado is EstadoSala.CERRADA:
                guardado = self.almacen.veredicto(sala.id, con)
                return {"ok": True, "estado": sala.estado.value, "veredicto": _veredicto_dict(guardado),
                        "indicacion": textos.VEREDICTO_YA_GUARDADO}
            proto = self._protocolo(sala)
            turnos = self.almacen.turnos(sala.id, con)
            hay_contenido = bool(contenido and contenido.strip())

            if sala.estado is not EstadoSala.VERIFICACION:
                if hay_contenido:
                    raise ErrorSala(textos.VEREDICTO_PRIMERO_SIN_CONTENIDO)
                quedan = any(t.artefacto is None for t in turnos) or proto.siguiente(sala, turnos) is not None
                if quedan:
                    raise ErrorSala(textos.VEREDICTO_FALTAN_TURNOS.format(id=sala.id))
                self._cambiar_estado(con, sala, proto, EstadoSala.VERIFICACION)

            if not hay_contenido:
                return self._turno_verificador(sala, turnos)

            assert contenido is not None
            errores = self._errores_texto(
                contenido, self.verificador.formato_salida, self.verificador.limites.max_palabras_turno
            )
            if confianza is None:
                errores.append(textos.VEREDICTO_FALTA_CONFIANZA)
            v: Veredicto | None = None
            if confianza is not None:
                try:
                    v = Veredicto(
                        sala_id=sala.id,
                        acuerdos=acuerdos or [],
                        desacuerdos=desacuerdos or [],
                        confianza=confianza,
                        plan=plan or [],
                        contenido=contenido.strip(),
                    )
                except ValidationError as exc:
                    errores += [str(e) for e in traducir_errores(exc, "veredicto")]
            if errores:
                return {"ok": False, "errores": errores, "indicacion": textos.VEREDICTO_CORREGIR}
            assert v is not None
            self.almacen.guardar_veredicto(con, v)
            self._cambiar_estado(con, sala, proto, EstadoSala.CERRADA)
        return {"ok": True, "estado": EstadoSala.CERRADA.value, "veredicto": _veredicto_dict(v),
                "indicacion": textos.VEREDICTO_GUARDADO}

    def _turno_verificador(self, sala: Sala, turnos: list[Turno]) -> dict[str, Any]:
        fmt = formato(self.verificador.formato_salida)
        assert fmt is not None
        nombres = {a: self.catalogo.agentes[a].nombre if a in self.catalogo.agentes else a for a in sala.agentes}
        mesa = [
            {
                "turno_id": t.id,
                "agente": t.agente_id,
                "nombre": nombres.get(t.agente_id, t.agente_id),
                "ronda": t.ronda,
                "artefacto": t.artefacto.model_dump(mode="json"),
            }
            for t in turnos
            if t.artefacto is not None
        ]
        limite = self.verificador.limites.max_palabras_turno
        datos: dict[str, Any] = {
            "sala_id": sala.id,
            "estado": sala.estado.value,
            "objetivo": sala.objetivo,
            "protocolo": sala.protocolo.value,
            "agente": {"id": self.verificador.id, "nombre": self.verificador.nombre, "postura": self.verificador.postura},
            "instrucciones": self.verificador.instrucciones,
            "mesa": mesa,
            "formato_salida": _formato_dict(fmt),
            "max_palabras": limite,
            "indicacion": textos.VEREDICTO_INDICACION.format(secciones=", ".join(fmt.secciones), max_palabras=limite),
        }
        datos["palabras_contexto"] = palabras_contexto(datos)
        return datos

    # ver_sala ----------------------------------------------------------------

    def ver_sala(self, sala_id: str | None = None, vista: str = "mesa", agente: str | None = None) -> str:
        """Historial legible en Markdown (RF-10, CU-05). Sin sala_id, lista las salas."""
        if not sala_id or not sala_id.strip():
            return vista_lista_salas(self.almacen.listar_salas())
        sala = self._sala(sala_id)
        vista = (vista or "mesa").strip().lower()
        turnos = [t for t in self.almacen.turnos(sala.id) if t.artefacto is not None]
        nombres = {a: (self.catalogo.agentes[a].nombre if a in self.catalogo.agentes else a) for a in sala.agentes}
        if vista == "mesa":
            return vista_mesa(sala, turnos, nombres)
        if vista == "hilo":
            if agente and agente.strip():
                if agente.strip() not in sala.agentes:
                    raise ErrorSala(textos.VISTA_AGENTE_FUERA.format(id=agente, agentes=", ".join(sala.agentes)))
                return vista_hilos(sala, turnos, nombres, [agente.strip()])
            return vista_hilos(sala, turnos, nombres, sala.agentes)
        if vista == "veredicto":
            return vista_veredicto(sala, self.almacen.veredicto(sala.id))
        raise ErrorSala(textos.VISTA_DESCONOCIDA.format(vista=vista))


def _veredicto_dict(v: Veredicto | None) -> dict[str, Any] | None:
    return v.model_dump(mode="json") if v else None


def palabras_contexto(datos: Any) -> int:
    """Palabras de todo lo que se entrega en un turno (para vigilar RNF-02)."""
    if isinstance(datos, str):
        return contar_palabras(datos)
    if isinstance(datos, dict):
        return sum(palabras_contexto(v) for v in datos.values())
    if isinstance(datos, list):
        return sum(palabras_contexto(v) for v in datos)
    return 0
