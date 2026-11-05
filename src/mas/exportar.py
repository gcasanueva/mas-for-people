"""Comando ``mas-exportar``: copia agentes del catálogo a Claude Code.

Uso: ``uv run mas-exportar <carpeta-del-proyecto> [id-agente ...] [--reemplazar]``.
Escribe ``<carpeta>/.claude/agents/<id>.md`` y ``<carpeta>/.claude/skills/<id>/``.
"""

from __future__ import annotations

import sys

from mas.core import textos
from mas.core.catalogo import Catalogo
from mas.core.exportar import ErrorExportar, exportar_claude_code
from mas.core.raiz import ubicar_raiz


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    reemplazar = "--reemplazar" in args
    posicionales = [a for a in args if not a.startswith("--")]
    if not posicionales or "--ayuda" in args or "-h" in args:
        print(textos.CLI_EXPORTAR_USO)
        return 0 if posicionales or "--ayuda" in args or "-h" in args else 2
    carpeta, ids = posicionales[0], posicionales[1:]
    try:
        catalogo = Catalogo(ubicar_raiz())
        r = exportar_claude_code(catalogo, carpeta, ids, reemplazar)
    except (ErrorExportar, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(textos.CLI_EXPORTAR_RESUMEN.format(n=len(r["agentes"]), carpeta=r["carpeta"]))
    for ruta in r["escritos"]:
        print(f"  + {ruta}")
    for ruta in r["omitidos"]:
        print(textos.CLI_EXPORTAR_OMITIDO.format(ruta=ruta))
    print(r["indicacion"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
