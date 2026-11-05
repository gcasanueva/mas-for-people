"""Servidor MCP de MAS for People.

Herramientas (contratos de la ERS):

- ``listar_agentes(familia?, texto?)`` → lista de fichas (RF-03, CU-01).
- ``ver_agente(id)`` → agente completo y skills que usa.
- ``abrir_sala``, ``siguiente_turno``, ``publicar_turno``, ``veredicto`` →
  ciclo de una sala (RF-05 a RF-09). La lógica está en ``core/salas.py``.
- ``ver_sala(sala_id?, vista, agente?)`` → historial en Markdown (RF-10).

El servidor no llama a ningún modelo: Claude Desktop razona y el servidor
solo entrega datos. Se comunica por stdio, así que nada se imprime en la
salida estándar; los avisos van a la salida de errores (stderr), que Claude
Desktop guarda en sus registros.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from mas import __version__
from mas.core import textos
from mas.core.almacen import Almacen
from mas.core.catalogo import Catalogo, NoEncontrado
from mas.core.formatos import formato
from mas.core.modelos import Artefacto
from mas.core.salas import ErrorSala, GestorSalas

from .raiz import ubicar_bd, ubicar_raiz

SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)
ESCRITURA = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


def esquema_artefacto() -> dict[str, Any]:
    """Esquema JSON del artefacto, sin referencias y con descripciones en español.

    Va dentro del esquema de ``publicar_turno`` para que Claude sepa qué
    campos mandar; la validación real la hace el núcleo (mensajes en español).
    """
    esquema = Artefacto.model_json_schema()
    defs = esquema.pop("$defs", {})
    for nombre, prop in esquema["properties"].items():
        ref = prop.pop("$ref", None)
        if ref:
            prop.update(defs[ref.rsplit("/", 1)[-1]])
        prop.pop("title", None)
        if nombre in textos.ARTEFACTO_CAMPOS:
            prop["description"] = textos.ARTEFACTO_CAMPOS[nombre]
    esquema.pop("title", None)
    esquema["description"] = textos.PARAM_ARTEFACTO
    return esquema


def _reemplazar_esquema(nuevo: dict[str, Any]):
    def aplicar(esquema: dict[str, Any]) -> None:
        esquema.clear()
        esquema.update(nuevo)

    return aplicar


def _errores(catalogo: Catalogo) -> list[str]:
    return [str(e) for e in catalogo.errores]


def listar_agentes(catalogo: Catalogo, familia: str | None = None, texto: str | None = None) -> dict[str, Any]:
    """Lógica de ``listar_agentes`` (separada para poder probarla sin MCP)."""
    catalogo.recargar()  # los cambios hechos a mano se ven sin reiniciar (RNF-04)
    agentes = [a.ficha() for a in catalogo.listar(familia=familia or None, texto=texto or None)]
    return {
        "agentes": agentes,
        "total": len(agentes),
        "familias": sorted(catalogo.familias()),
        "errores": _errores(catalogo),
    }


def ver_agente(catalogo: Catalogo, id: str) -> dict[str, Any]:
    """Lógica de ``ver_agente``. Lanza ``NoEncontrado`` si el id no existe."""
    catalogo.recargar()
    agente = catalogo.agente(id.strip())
    fmt = formato(agente.formato_salida)
    return {
        **agente.ficha(),
        "version": agente.version,
        "formato_salida": {
            "id": agente.formato_salida,
            "nombre": fmt.nombre if fmt else agente.formato_salida,
            "secciones": list(fmt.secciones) if fmt else [],
        },
        "limites": {
            "max_turnos": agente.limites.max_turnos,
            "max_palabras_turno": agente.limites.max_palabras_turno,
        },
        "sensible": agente.sensible,
        "aviso": agente.aviso,
        "instrucciones": agente.instrucciones,
        "skills": [{"id": s.id, "descripcion": s.descripcion} for s in catalogo.skills_de(agente)],
        "agente_md": agente.a_agente_md(),
    }


def crear_servidor(raiz: Path | str, bd: Path | str | None = None) -> MCPServer:
    """Crea el servidor MCP sobre el catálogo de ``raiz`` y la base ``bd``."""
    raiz = Path(raiz)
    catalogo = Catalogo(raiz)
    almacen = Almacen(bd if bd is not None else ubicar_bd(raiz))
    salas = GestorSalas(catalogo, almacen)
    mcp = MCPServer(
        name="mas-for-people",
        title="MAS for People",
        instructions=textos.SERVIDOR_INSTRUCCIONES,
        version=__version__,
    )

    @mcp.tool(name="listar_agentes", title="Listar agentes", description=textos.HERRAMIENTA_LISTAR, annotations=SOLO_LECTURA)
    def _listar_agentes(
        familia: Annotated[str | None, Field(description=textos.PARAM_FAMILIA)] = None,
        texto: Annotated[str | None, Field(description=textos.PARAM_TEXTO)] = None,
    ) -> dict[str, Any]:
        return listar_agentes(catalogo, familia, texto)

    @mcp.tool(name="ver_agente", title="Ver agente", description=textos.HERRAMIENTA_VER, annotations=SOLO_LECTURA)
    def _ver_agente(id: Annotated[str, Field(description=textos.PARAM_ID)]) -> dict[str, Any]:
        try:
            return ver_agente(catalogo, id)
        except NoEncontrado as exc:
            raise ToolError(f"{exc} Usa listar_agentes para ver los ids disponibles.") from None

    _registrar_salas(mcp, salas)

    mcp.catalogo = catalogo  # type: ignore[attr-defined]  # útil en pruebas
    mcp.salas = salas  # type: ignore[attr-defined]
    return mcp


def _registrar_salas(mcp: MCPServer, salas: GestorSalas) -> None:
    """Herramientas del ciclo de una sala (paso 3)."""

    def ejecutar(funcion, *args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except ErrorSala as exc:
            raise ToolError(str(exc)) from None

    @mcp.tool(name="abrir_sala", title="Abrir sala", description=textos.HERRAMIENTA_ABRIR_SALA, annotations=ESCRITURA)
    def _abrir_sala(
        objetivo: Annotated[str, Field(description=textos.PARAM_OBJETIVO)],
        agentes: Annotated[list[str], Field(description=textos.PARAM_AGENTES)],
        protocolo: Annotated[str, Field(description=textos.PARAM_PROTOCOLO)] = "debate",
        max_rondas: Annotated[int, Field(description=textos.PARAM_MAX_RONDAS)] = 2,
        max_palabras: Annotated[int, Field(description=textos.PARAM_MAX_PALABRAS)] = 400,
        posturas: Annotated[dict[str, str] | None, Field(description=textos.PARAM_POSTURAS)] = None,
    ) -> dict[str, Any]:
        return ejecutar(salas.abrir_sala, objetivo, agentes, protocolo, max_rondas, max_palabras, posturas)

    @mcp.tool(
        name="siguiente_turno", title="Siguiente turno", description=textos.HERRAMIENTA_SIGUIENTE_TURNO,
        annotations=ESCRITURA,
    )
    def _siguiente_turno(sala_id: Annotated[str, Field(description=textos.PARAM_SALA_ID)]) -> dict[str, Any]:
        return ejecutar(salas.siguiente_turno, sala_id)

    @mcp.tool(
        name="publicar_turno", title="Publicar turno", description=textos.HERRAMIENTA_PUBLICAR_TURNO,
        annotations=ESCRITURA,
    )
    def _publicar_turno(
        sala_id: Annotated[str, Field(description=textos.PARAM_SALA_ID)],
        turno_id: Annotated[str, Field(description=textos.PARAM_TURNO_ID)],
        contenido: Annotated[str, Field(description=textos.PARAM_CONTENIDO)],
        artefacto: Annotated[
            dict[str, Any], Field(json_schema_extra=_reemplazar_esquema(esquema_artefacto()))
        ],
    ) -> dict[str, Any]:
        return ejecutar(salas.publicar_turno, sala_id, turno_id, contenido, artefacto)

    @mcp.tool(name="veredicto", title="Veredicto", description=textos.HERRAMIENTA_VEREDICTO, annotations=ESCRITURA)
    def _veredicto(
        sala_id: Annotated[str, Field(description=textos.PARAM_SALA_ID)],
        contenido: Annotated[str | None, Field(description=textos.PARAM_VEREDICTO_CONTENIDO)] = None,
        acuerdos: Annotated[list[str] | None, Field(description=textos.PARAM_ACUERDOS)] = None,
        desacuerdos: Annotated[list[str] | None, Field(description=textos.PARAM_DESACUERDOS)] = None,
        confianza: Annotated[float | None, Field(description=textos.PARAM_CONFIANZA)] = None,
        plan: Annotated[list[str] | None, Field(description=textos.PARAM_PLAN)] = None,
    ) -> dict[str, Any]:
        return ejecutar(salas.veredicto, sala_id, contenido, acuerdos, desacuerdos, confianza, plan)

    @mcp.tool(name="ver_sala", title="Ver sala", description=textos.HERRAMIENTA_VER_SALA, annotations=SOLO_LECTURA)
    def _ver_sala(
        sala_id: Annotated[str | None, Field(description=textos.PARAM_SALA_ID)] = None,
        vista: Annotated[str, Field(description=textos.PARAM_VISTA)] = "mesa",
        agente: Annotated[str | None, Field(description=textos.PARAM_AGENTE_HILO)] = None,
    ) -> str:
        return ejecutar(salas.ver_sala, sala_id, vista, agente)


def main() -> None:
    """Punto de entrada de ``mas-servidor`` (lo lanza Claude Desktop)."""
    # En Windows la consola puede no usar UTF-8; que una tilde no tumbe el servidor.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        raiz = ubicar_raiz()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    servidor = crear_servidor(raiz)
    catalogo: Catalogo = servidor.catalogo  # type: ignore[attr-defined]
    salas: GestorSalas = servidor.salas  # type: ignore[attr-defined]
    print(
        textos.SERVIDOR_INICIADO.format(
            raiz=raiz, agentes=len(catalogo.agentes), skills=len(catalogo.skills), bd=salas.almacen.ruta
        ),
        file=sys.stderr,
    )
    if catalogo.errores:
        print(textos.SERVIDOR_ERRORES_CATALOGO.format(n=len(catalogo.errores)), file=sys.stderr)
        for error in catalogo.errores:
            print(f"  * {error}", file=sys.stderr)
    servidor.run("stdio")


if __name__ == "__main__":
    main()
