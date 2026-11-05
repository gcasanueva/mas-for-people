"""Comando ``mas-config``: imprime el bloque para conectar Claude Desktop.

Uso: ``uv run mas-config`` dentro de la carpeta del proyecto. Calcula las
rutas de este computador (incluida la de ``uv``) para que solo haya que
copiar y pegar.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from mas.core import textos

from .raiz import ubicar_raiz


def archivo_config_claude(plataforma: str | None = None, entorno: dict[str, str] | None = None) -> str:
    """Ruta habitual de ``claude_desktop_config.json`` en cada sistema."""
    plataforma = plataforma or sys.platform
    entorno = os.environ if entorno is None else entorno
    if plataforma.startswith("win"):
        return str(Path(entorno.get("APPDATA", r"%APPDATA%")) / "Claude" / "claude_desktop_config.json")
    if plataforma == "darwin":
        return "~/Library/Application Support/Claude/claude_desktop_config.json"
    return "~/.config/Claude/claude_desktop_config.json"


def bloque_config(raiz: Path, uv: str) -> dict:
    """El bloque ``mcpServers`` que va en la configuración de Claude Desktop."""
    return {
        "mcpServers": {
            "mas-for-people": {
                "command": uv,
                "args": ["--directory", str(raiz), "run", "mas-servidor"],
            }
        }
    }


def main() -> int:
    raiz = ubicar_raiz()
    uv = shutil.which("uv")
    print(f"\n{textos.CONFIG_TITULO}\n")
    print(textos.CONFIG_PASOS.format(archivo=archivo_config_claude()))
    print()
    print(json.dumps(bloque_config(raiz, uv or "uv"), indent=2, ensure_ascii=False))
    if not uv:
        print(f"\n{textos.CONFIG_SIN_UV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
