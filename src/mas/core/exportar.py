"""Exportar agentes y skills al formato de Claude Code (CU-06, RF-12).

Cada agente se escribe como subagente en ``<carpeta>/.claude/agents/<id>.md``
y cada skill que usa se copia en ``<carpeta>/.claude/skills/<id>/``. Así el
agente trabaja en Claude Code con su propio contexto, como subagente real.

``agente.md`` ya es un superconjunto del formato de Claude Code: aquí se
dejan solo los campos que Claude Code entiende (``name``, ``description``,
``tools``, ``model``, ``skills``) y lo propio de MAS for People (postura,
formato de salida, aviso) pasa al cuerpo como instrucciones.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from . import textos
from .catalogo import Catalogo, NoEncontrado
from .formatos import formato
from .modelos import Agente

# Valores de ``model`` que acepta Claude Code; otro valor se omite (hereda).
MODELOS_CLAUDE_CODE = frozenset({"sonnet", "opus", "haiku", "inherit"})


class ErrorExportar(Exception):
    """Algo que el usuario debe corregir para exportar (mensaje en español)."""


def subagente_md(agente: Agente) -> str:
    """Contenido del archivo de subagente de Claude Code para ``agente``."""
    datos: dict[str, Any] = {"name": agente.id, "description": agente.descripcion}
    if agente.herramientas:
        datos["tools"] = ", ".join(agente.herramientas)
    if isinstance(agente.modelo, str) and agente.modelo in MODELOS_CLAUDE_CODE:
        datos["model"] = agente.modelo
    if agente.skills:
        datos["skills"] = ", ".join(agente.skills)
    encabezado = yaml.safe_dump(datos, allow_unicode=True, sort_keys=False, width=1000)

    partes = [
        textos.EXPORTAR_CUERPO_INICIO.format(nombre=agente.nombre or agente.id, postura=agente.postura),
        "",
        agente.instrucciones.strip(),
    ]
    fmt = formato(agente.formato_salida)
    if fmt is not None:
        partes += ["", textos.EXPORTAR_FORMATO.format(nombre=fmt.nombre, secciones=", ".join(fmt.secciones))]
    if agente.sensible and agente.aviso:
        partes += ["", textos.EXPORTAR_AVISO.format(aviso=agente.aviso)]
    return f"---\n{encabezado}---\n\n" + "\n".join(partes).strip() + "\n"


def exportar_claude_code(
    catalogo: Catalogo,
    carpeta: str | Path,
    agentes: list[str] | None = None,
    reemplazar: bool = False,
) -> dict[str, Any]:
    """Escribe los agentes (todos si ``agentes`` está vacío) y sus skills en ``carpeta/.claude``."""
    catalogo.recargar()
    destino = Path(str(carpeta).strip()).expanduser()
    if not str(carpeta).strip() or not destino.is_dir():
        raise ErrorExportar(textos.EXPORTAR_CARPETA_NO_EXISTE.format(carpeta=carpeta))
    ids = [a.strip() for a in (agentes or []) if a and a.strip()] or sorted(catalogo.agentes)
    elegidos: list[Agente] = []
    for id_ in ids:
        try:
            elegidos.append(catalogo.agente(id_))
        except NoEncontrado:
            raise ErrorExportar(textos.SALA_AGENTE_INEXISTENTE.format(id=id_)) from None

    dir_agentes = destino / ".claude" / "agents"
    dir_skills = destino / ".claude" / "skills"
    escritos: list[str] = []
    omitidos: list[str] = []

    for agente in elegidos:
        ruta = dir_agentes / f"{agente.id}.md"
        texto = subagente_md(agente)
        if ruta.exists() and not reemplazar and ruta.read_text(encoding="utf-8") != texto:
            omitidos.append(_rel(ruta, destino))
            continue
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")
        escritos.append(_rel(ruta, destino))

    skills = sorted({s for a in elegidos for s in a.skills if s in catalogo.skills})
    for id_skill in skills:
        origen = catalogo.skills[id_skill].ruta
        assert origen is not None
        carpeta_skill = dir_skills / id_skill
        if carpeta_skill.exists() and not reemplazar and not _misma_carpeta(origen.parent, carpeta_skill):
            omitidos.append(_rel(carpeta_skill, destino) + "/")
            continue
        shutil.copytree(origen.parent, carpeta_skill, dirs_exist_ok=True)
        escritos.append(_rel(carpeta_skill / origen.name, destino))

    return {
        "ok": True,
        "carpeta": str(destino.resolve()),
        "agentes": [a.id for a in elegidos],
        "escritos": escritos,
        "omitidos": omitidos,
        "indicacion": textos.EXPORTAR_OMITIDOS if omitidos else textos.EXPORTAR_LISTO,
    }


def _rel(ruta: Path, base: Path) -> str:
    return ruta.relative_to(base).as_posix()


def _misma_carpeta(a: Path, b: Path) -> bool:
    """Si la skill ya exportada es idéntica a la del catálogo."""
    archivos_a = {p.relative_to(a): p.read_bytes() for p in a.rglob("*") if p.is_file()}
    archivos_b = {p.relative_to(b): p.read_bytes() for p in b.rglob("*") if p.is_file()}
    return archivos_a == archivos_b
