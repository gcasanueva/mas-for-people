"""Pruebas del servidor MCP (paso 2): listar_agentes y ver_agente."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from conftest import RAIZ_PROYECTO, crear_agente, crear_skill, escribir
from mas.servidor.app import crear_servidor
from mas.servidor.config import archivo_config_claude, bloque_config
from mas.servidor.raiz import ubicar_raiz

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _llamar(raiz: Path, herramienta: str, argumentos: dict) -> tuple[bool, dict | str]:
    async with Client(crear_servidor(raiz)) as cliente:
        r = await cliente.call_tool(herramienta, argumentos)
    if r.is_error:
        return True, r.content[0].text
    return False, r.structured_content


# --- Herramientas ------------------------------------------------------------


async def test_expone_las_dos_herramientas_de_solo_lectura():
    async with Client(crear_servidor(RAIZ_PROYECTO)) as cliente:
        herramientas = (await cliente.list_tools()).tools
    assert sorted(h.name for h in herramientas) == ["listar_agentes", "ver_agente"]
    for h in herramientas:
        assert h.annotations.read_only_hint is True
        assert h.description  # en español, para que Claude sepa cuándo usarla


async def test_listar_todos():
    error, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {})
    assert not error
    assert datos["total"] == 3
    assert {a["id"] for a in datos["agentes"]} == {"ingeniero-industrial", "economista-ortodoxo", "periodista"}
    assert set(datos["agentes"][0]) == {"id", "nombre", "familia", "postura", "descripcion"}
    assert datos["errores"] == []


async def test_listar_por_familia_y_texto():
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"familia": "Ingeniería"})
    assert [a["id"] for a in datos["agentes"]] == ["ingeniero-industrial"]
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"texto": "escéptico"})
    assert [a["id"] for a in datos["agentes"]] == ["periodista"]
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"familia": "", "texto": ""})
    assert datos["total"] == 3


async def test_ver_agente_completo():
    error, datos = await _llamar(RAIZ_PROYECTO, "ver_agente", {"id": "ingeniero-industrial"})
    assert not error
    assert datos["postura"] == "conservador"
    assert datos["formato_salida"]["id"] == "propuesta-tecnica"
    assert "Riesgos" in datos["formato_salida"]["secciones"]
    assert [s["id"] for s in datos["skills"]] == ["mejora-procesos", "analisis-costos"]
    assert datos["instrucciones"]
    assert datos["agente_md"].startswith("---\nname: ingeniero-industrial")


async def test_ver_agente_inexistente_da_error_claro():
    error, texto = await _llamar(RAIZ_PROYECTO, "ver_agente", {"id": "astronauta"})
    assert error
    assert "No existe un agente con el id 'astronauta'" in texto
    assert "listar_agentes" in texto


async def test_ve_cambios_hechos_a_mano_sin_reiniciar(raiz_vacia: Path):
    servidor = crear_servidor(raiz_vacia)
    async with Client(servidor) as cliente:
        r = await cliente.call_tool("listar_agentes", {})
        assert r.structured_content["total"] == 0
        crear_skill(raiz_vacia, "s1")
        crear_agente(raiz_vacia, "pruebas", "nuevo", skills="s1")
        r = await cliente.call_tool("listar_agentes", {})
        assert [a["id"] for a in r.structured_content["agentes"]] == ["nuevo"]


async def test_informa_archivos_con_errores(raiz_vacia: Path):
    escribir(raiz_vacia / "agentes" / "pruebas" / "malo" / "agente.md", "---\nname: malo\n---\n\nHola")
    _, datos = await _llamar(raiz_vacia, "listar_agentes", {})
    assert datos["total"] == 0
    assert any("agentes/pruebas/malo/agente.md · stance" in e for e in datos["errores"])


# --- Prueba de punta a punta por stdio (como lo usa Claude Desktop) ---------


async def test_servidor_real_por_stdio(tmp_path: Path):
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mas.servidor.app"],
        cwd=str(tmp_path),  # Claude Desktop puede arrancarlo en cualquier carpeta
        env={"MAS_CARPETA": str(RAIZ_PROYECTO)},
    )
    async with Client(parametros) as cliente:
        r = await cliente.call_tool("listar_agentes", {"familia": "economia"})
    assert not r.is_error
    assert [a["id"] for a in r.structured_content["agentes"]] == ["economista-ortodoxo"]


# --- Ubicar la carpeta y mas-config ---------------------------------------


def test_ubicar_raiz(tmp_path_factory: pytest.TempPathFactory, raiz_vacia: Path):
    tmp_path = tmp_path_factory.mktemp("otra")
    assert ubicar_raiz(cwd=tmp_path, entorno={"MAS_CARPETA": str(raiz_vacia)}) == raiz_vacia.resolve()
    assert ubicar_raiz(cwd=raiz_vacia, entorno={}) == raiz_vacia.resolve()
    # Desde cualquier otra carpeta, usa la del repositorio instalado.
    assert ubicar_raiz(cwd=tmp_path, entorno={}) == RAIZ_PROYECTO


def test_bloque_config_es_json_valido_en_windows():
    raiz = Path(r"C:\Users\gabriel\mas-for-people")
    texto = json.dumps(bloque_config(raiz, r"C:\Users\gabriel\.local\bin\uv.exe"))
    datos = json.loads(texto)["mcpServers"]["mas-for-people"]
    assert datos["args"][-2:] == ["run", "mas-servidor"]
    assert datos["args"][0] == "--directory"
    ruta = archivo_config_claude("win32", {"APPDATA": r"C:\Users\gabriel\AppData\Roaming"})
    assert ruta.endswith("claude_desktop_config.json") and "Claude" in ruta


def test_nucleo_no_importa_mcp():
    # RNF-01: la lógica del núcleo no depende de la capa MCP.
    for archivo in (RAIZ_PROYECTO / "src" / "mas" / "core").rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        assert "import mcp" not in texto and "from mcp" not in texto, archivo
        assert "mas.servidor" not in texto, archivo
