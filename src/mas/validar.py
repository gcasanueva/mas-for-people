"""Comando ``mas-validar``: revisa el catálogo y muestra agentes y errores.

Uso: ``uv run mas-validar [carpeta]`` (por defecto, la carpeta actual).
Sale con código 1 si algún archivo tiene errores.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mas.core.catalogo import Catalogo


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    raiz = Path(args[0]) if args else Path.cwd()
    catalogo = Catalogo(raiz)

    for familia, agentes in catalogo.familias().items():
        print(f"\n{familia}")
        for a in agentes:
            print(f"  - {a.nombre} ({a.id}) · postura: {a.postura} · skills: {', '.join(a.skills) or '-'}")
    print(f"\n{len(catalogo.agentes)} agentes y {len(catalogo.skills)} skills cargados.")

    if catalogo.errores:
        print(f"\n{len(catalogo.errores)} problema(s) por corregir:")
        for error in catalogo.errores:
            print(f"  * {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
