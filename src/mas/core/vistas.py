"""Vistas en Markdown de una sala (``ver_sala``, CU-05).

Funciones puras: reciben datos ya leídos y devuelven texto.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import textos
from .formatos import FORMATOS
from .modelos import Agente, Sala, Skill, Turno, Veredicto


def _fecha(sala: Sala) -> str:
    return sala.creada.astimezone().strftime("%Y-%m-%d %H:%M")


def _corto(texto: str, maximo: int = 80) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


def encabezado(sala: Sala) -> str:
    return (
        f"# Sala {sala.id}\n\n"
        f"**Objetivo:** {sala.objetivo}\n\n"
        f"Protocolo: {sala.protocolo.value} · Estado: {sala.estado.value} · "
        f"Agentes: {', '.join(sala.agentes)} · Creada: {_fecha(sala)}\n"
    )


def vista_lista_salas(salas: list[Sala]) -> str:
    if not salas:
        return textos.VISTA_SIN_SALAS
    filas = [
        textos.VISTA_TITULO_SALAS,
        "",
        "| sala_id | Fecha | Protocolo | Estado | Objetivo |",
        "|---|---|---|---|---|",
    ]
    filas += [
        f"| {s.id} | {_fecha(s)} | {s.protocolo.value} | {s.estado.value} | {_corto(s.objetivo).replace('|', '/')} |"
        for s in salas
    ]
    return "\n".join(filas) + "\n"


def _lista(titulo: str, elementos: Iterable[str]) -> list[str]:
    elementos = list(elementos)
    if not elementos:
        return []
    return [f"- {titulo}:"] + [f"  - {e}" for e in elementos]


def vista_mesa(sala: Sala, turnos: list[Turno], nombres: dict[str, str]) -> str:
    return encabezado(sala) + _seccion_mesa(turnos, nombres)


def _seccion_mesa(turnos: list[Turno], nombres: dict[str, str]) -> str:
    partes = ["", "## Mesa", ""]
    if not turnos:
        partes.append(textos.VISTA_MESA_VACIA)
    varias_rondas = len({t.ronda for t in turnos}) > 1
    nivel = "####" if varias_rondas else "###"
    ronda_actual = 0
    for t in turnos:
        a = t.artefacto
        assert a is not None
        if varias_rondas and t.ronda != ronda_actual:
            ronda_actual = t.ronda
            partes += [textos.VISTA_RONDA.format(ronda=t.ronda), ""]
        partes.append(
            f"{nivel} {nombres.get(t.agente_id, t.agente_id)} · ronda {t.ronda} · {a.postura.value} "
            f"· confianza {a.confianza:.2f}"
        )
        partes.append("")
        partes.append(a.resumen)
        detalle = _lista("Supuestos", a.supuestos) + _lista("Riesgos", a.riesgos)
        if a.responde_a:
            detalle.append(f"- Responde a: {', '.join(a.responde_a)}")
        if a.cambiaria_de_opinion_si:
            detalle.append(f"- Cambiaría de opinión si: {a.cambiaria_de_opinion_si}")
        if detalle:
            partes += [""] + detalle
        partes.append(f"\n_turno {t.id} · {t.palabras} palabras_\n")
    return "\n".join(partes).rstrip() + "\n"


def vista_hilos(sala: Sala, turnos: list[Turno], nombres: dict[str, str], agentes: list[str]) -> str:
    return encabezado(sala) + _seccion_hilos(turnos, nombres, agentes)


def _seccion_hilos(turnos: list[Turno], nombres: dict[str, str], agentes: list[str]) -> str:
    partes = [""]
    for agente_id in agentes:
        nombre = nombres.get(agente_id, agente_id)
        partes += [f"## Hilo de {nombre}", ""]
        propios = [t for t in turnos if t.agente_id == agente_id]
        if not propios:
            partes += [textos.VISTA_HILO_VACIO.format(nombre=nombre), ""]
        for t in propios:
            partes += [f"### Ronda {t.ronda} · {t.palabras} palabras", "", t.contenido.strip(), ""]
    return "\n".join(partes).rstrip() + "\n"


def vista_veredicto(sala: Sala, v: Veredicto | None) -> str:
    return encabezado(sala) + _seccion_veredicto(sala, v)


def _seccion_veredicto(sala: Sala, v: Veredicto | None) -> str:
    partes = ["", "## Veredicto", ""]
    if v is None:
        partes.append(textos.VISTA_SIN_VEREDICTO.format(estado=sala.estado.value))
        return "\n".join(partes) + "\n"
    partes += [f"**Confianza:** {v.confianza:.2f}", "", v.contenido.strip()]
    resumen = _lista("Acuerdos", v.acuerdos) + _lista("Desacuerdos", v.desacuerdos) + _lista("Plan", v.plan)
    if resumen:
        partes += ["", "---", ""] + resumen
    return "\n".join(partes).rstrip() + "\n"


def vista_completa(
    sala: Sala, turnos: list[Turno], nombres: dict[str, str], veredicto: Veredicto | None
) -> str:
    """Toda la sala en un documento: mesa, hilos y veredicto (RF-15, RF-19)."""
    return (
        encabezado(sala)
        + _seccion_mesa(turnos, nombres)
        + _seccion_hilos(turnos, nombres, sala.agentes)
        + _seccion_veredicto(sala, veredicto)
    )


def vista_agente(agente: Agente, skills: list[Skill], propio: bool = False) -> str:
    """Ficha de un agente para el visor (RF-16): postura, skills y formato."""
    fmt = FORMATOS.get(agente.formato_salida)
    partes = [
        f"# {agente.nombre or agente.id}",
        "",
        agente.descripcion,
        "",
        f"- **Id:** `{agente.id}`",
        f"- **Familia:** {agente.familia}",
        f"- **Postura:** {agente.postura}",
        f"- **Versión:** {agente.version}",
        *([textos.VISTA_ORIGEN_PROPIO] if propio else []),
        f"- **Límites:** {agente.limites.max_turnos} turnos, "
        f"{agente.limites.max_palabras_turno} palabras por turno",
    ]
    if agente.sensible and agente.aviso:
        partes += ["", f"> **Aviso:** {agente.aviso}"]
    partes += ["", "## Skills", ""]
    if skills:
        partes += [f"- **{s.id}**: {s.descripcion}" for s in skills]
    else:
        partes.append(textos.VISOR_SIN_SKILLS)
    partes += ["", "## Formato de salida", ""]
    if fmt:
        partes.append(f"**{fmt.nombre}** (`{fmt.id}`): " + ", ".join(fmt.secciones) + ".")
    else:
        partes.append(f"`{agente.formato_salida}`")
    partes += ["", "## Instrucciones", "", agente.instrucciones.strip()]
    if agente.ruta:
        partes += ["", f"_{agente.ruta}_"]
    return "\n".join(partes) + "\n"
