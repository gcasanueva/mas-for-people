from __future__ import annotations

from pathlib import Path

import pytest

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

SKILL = """---
name: {nombre}
description: Skill de prueba.
---

Instrucciones de prueba.
"""

AGENTE = """---
name: {nombre}
description: Agente de prueba.
stance: neutral
skills: [{skills}]
output_contract: propuesta-tecnica
---

Eres un agente de prueba.
"""


@pytest.fixture
def raiz_vacia(tmp_path: Path) -> Path:
    (tmp_path / "agentes").mkdir()
    (tmp_path / "skills").mkdir()
    return tmp_path


def escribir(ruta: Path, texto: str) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def crear_skill(raiz: Path, nombre: str) -> Path:
    return escribir(raiz / "skills" / nombre / "SKILL.md", SKILL.format(nombre=nombre))


def crear_agente(raiz: Path, familia: str, nombre: str, skills: str = "", texto: str | None = None) -> Path:
    contenido = texto if texto is not None else AGENTE.format(nombre=nombre, skills=skills)
    return escribir(raiz / "agentes" / familia / nombre / "agente.md", contenido)
