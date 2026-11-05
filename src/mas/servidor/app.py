"""Servidor MCP de MAS for People (paso 2: catálogo de agentes).

Herramientas (contratos de la ERS):

- ``listar_agentes(familia?, texto?)`` → lista de fichas (RF-03, CU-01).
- ``ver_agente(id)`` → agente completo y skills que usa.

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
from mas.core.catalogo import Catalogo, NoEncontrado
from mas.core.formatos import formato

from .raiz import ubicar_raiz

SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)


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


def crear_servidor(raiz: Path | str) -> MCPServer:
    """Crea el servidor MCP sobre el catálogo de ``raiz``."""
    catalogo = Catalogo(raiz)
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

    mcp.catalogo = catalogo  # type: ignore[attr-defined]  # útil en pruebas
    return mcp


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
    print(
        textos.SERVIDOR_INICIADO.format(raiz=raiz, agentes=len(catalogo.agentes), skills=len(catalogo.skills)),
        file=sys.stderr,
    )
    if catalogo.errores:
        print(textos.SERVIDOR_ERRORES_CATALOGO.format(n=len(catalogo.errores)), file=sys.stderr)
        for error in catalogo.errores:
            print(f"  * {error}", file=sys.stderr)
    servidor.run("stdio")


if __name__ == "__main__":
    main()
