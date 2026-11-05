"""Ubicar la carpeta del proyecto (la que tiene ``agentes/`` y ``skills/``)."""

from __future__ import annotations

import os
from pathlib import Path

from mas.core import textos

VARIABLE_RAIZ = "MAS_CARPETA"


def _es_raiz(carpeta: Path) -> bool:
    return (carpeta / "agentes").is_dir()


def ubicar_raiz(cwd: Path | None = None, entorno: dict[str, str] | None = None) -> Path:
    """Devuelve la carpeta raíz del catálogo.

    Orden: variable de entorno ``MAS_CARPETA``, carpeta actual y, por último,
    la carpeta del repositorio donde está instalado este código. Claude
    Desktop no siempre arranca el servidor en la carpeta del proyecto, por eso
    hay más de una opción.
    """
    entorno = os.environ if entorno is None else entorno
    candidatas: list[Path] = []
    if entorno.get(VARIABLE_RAIZ):
        candidatas.append(Path(entorno[VARIABLE_RAIZ]).expanduser())
    candidatas.append(cwd or Path.cwd())
    # src/mas/servidor/raiz.py -> raíz del repositorio
    candidatas.append(Path(__file__).resolve().parents[3])
    for carpeta in candidatas:
        if _es_raiz(carpeta):
            return carpeta.resolve()
    raise FileNotFoundError(textos.RAIZ_NO_ENCONTRADA)
