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
from mas.servidor.raiz import ubicar_bd, ubicar_raiz

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


async def test_expone_las_herramientas_del_catalogo_y_de_salas():
    async with Client(crear_servidor(RAIZ_PROYECTO)) as cliente:
        herramientas = {h.name: h for h in (await cliente.list_tools()).tools}
    assert sorted(herramientas) == [
        "abrir_sala", "exportar_agentes", "exportar_sala", "guardar_agente", "listar_agentes", "publicar_turno",
        "siguiente_turno", "ver_agente", "ver_sala", "veredicto",
    ]
    for nombre in ("listar_agentes", "ver_agente", "ver_sala"):
        assert herramientas[nombre].annotations.read_only_hint is True
    for h in herramientas.values():
        assert h.description  # en español, para que Claude sepa cuándo usarla


async def test_listar_todos():
    error, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {})
    assert not error
    assert datos["total"] == 9
    assert set(datos["agentes"][0]) == {"id", "nombre", "familia", "postura", "descripcion", "propio"}
    assert datos["errores"] == []


async def test_listar_por_familia_y_texto():
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"familia": "Ingeniería"})
    # CA-01: "muéstrame los ingenieros" -> los 3 de ingeniería con su postura
    assert {(a["id"], a["postura"]) for a in datos["agentes"]} == {
        ("ingeniero-industrial", "conservador"), ("ingeniero-ambiental", "innovador"),
        ("ingeniero-informatico", "pragmático"),
    }
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"texto": "escéptico"})
    assert [a["id"] for a in datos["agentes"]] == ["periodista", "abogado-del-diablo"]
    _, datos = await _llamar(RAIZ_PROYECTO, "listar_agentes", {"familia": "", "texto": ""})
    assert datos["total"] == 9


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


# --- Salas por MCP -----------------------------------------------------------


def _texto(turno: dict) -> str:
    return "\n\n".join(f"## {s}\nTexto." for s in turno["formato_salida"]["secciones"])


async def test_sala_panel_completa_por_mcp(tmp_path: Path):
    async with Client(crear_servidor(RAIZ_PROYECTO, tmp_path / "mas.db")) as c:
        r = await c.call_tool("abrir_sala", {"objetivo": "Bajar costos", "agentes": ["periodista", "ingeniero-industrial"],
                                            "protocolo": "panel"})
        sala_id = r.structured_content["sala_id"]
        while True:
            t = (await c.call_tool("siguiente_turno", {"sala_id": sala_id})).structured_content
            if t.get("estado") == "listo_para_veredicto":
                break
            art = {"postura": "propuesta", "resumen": "Idea", "confianza": 0.5}
            r = await c.call_tool("publicar_turno", {"sala_id": sala_id, "turno_id": t["turno_id"],
                                                      "contenido": "sin formato", "artefacto": art})
            assert r.structured_content["ok"] is False and r.structured_content["errores"]
            r = await c.call_tool("publicar_turno", {"sala_id": sala_id, "turno_id": t["turno_id"],
                                                      "contenido": _texto(t), "artefacto": art})
            assert r.structured_content["ok"] is True
        v = (await c.call_tool("veredicto", {"sala_id": sala_id})).structured_content
        assert v["agente"]["id"] == "verificador" and len(v["mesa"]) == 2
        r = await c.call_tool("veredicto", {"sala_id": sala_id, "contenido": _texto(v), "confianza": 0.8,
                                             "acuerdos": ["A"], "plan": ["Paso 1"]})
        assert r.structured_content["estado"] == "cerrada"
        r = await c.call_tool("ver_sala", {"sala_id": sala_id, "vista": "veredicto"})
        assert "**Confianza:** 0.80" in r.content[0].text
        r = await c.call_tool("ver_sala", {})
        assert sala_id in r.content[0].text


async def test_errores_de_sala_llegan_como_error_de_herramienta(tmp_path: Path):
    async with Client(crear_servidor(RAIZ_PROYECTO, tmp_path / "mas.db")) as c:
        r = await c.call_tool("siguiente_turno", {"sala_id": "nada"})
        assert r.is_error and "No existe una sala con el id 'nada'" in r.content[0].text
        r = await c.call_tool("abrir_sala", {"objetivo": "x", "agentes": ["periodista", "periodista"]})
        assert r.is_error and "dos veces" in r.content[0].text


async def test_esquema_de_publicar_turno_describe_el_artefacto():
    async with Client(crear_servidor(RAIZ_PROYECTO)) as c:
        h = next(h for h in (await c.list_tools()).tools if h.name == "publicar_turno")
    art = h.input_schema["properties"]["artefacto"]
    assert art["required"] == ["postura", "resumen", "confianza"]
    assert art["properties"]["postura"]["enum"] == ["propuesta", "apoyo", "objecion", "correccion"]
    assert "$ref" not in str(art)


def test_bd_por_defecto_y_variable(tmp_path: Path):
    assert ubicar_bd(tmp_path, {}) == (tmp_path / "datos" / "mas.db").resolve()
    assert ubicar_bd(tmp_path, {"MAS_BD": str(tmp_path / "x.db")}) == (tmp_path / "x.db").resolve()


# --- Prueba de punta a punta por stdio (como lo usa Claude Desktop) ---------


async def test_servidor_real_por_stdio(tmp_path: Path):
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mas.servidor.app"],
        cwd=str(tmp_path),  # Claude Desktop puede arrancarlo en cualquier carpeta
        env={"MAS_CARPETA": str(RAIZ_PROYECTO), "MAS_BD": str(tmp_path / "mas.db")},
    )
    async with Client(parametros) as cliente:
        r = await cliente.call_tool("listar_agentes", {"familia": "economia"})
        sala = await cliente.call_tool("abrir_sala", {"objetivo": "x", "agentes": ["periodista", "economista-ortodoxo"]})
    assert not r.is_error
    assert [a["id"] for a in r.structured_content["agentes"]] == ["economista-heterodoxo", "economista-ortodoxo"]
    assert not sala.is_error
    assert (tmp_path / "mas.db").exists()  # la base va donde dice MAS_BD


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


# --- Paso 6: guardar_agente y prompts -------------------------------------------


async def test_guardar_agente_por_mcp(tmp_path: Path):
    import shutil

    raiz = tmp_path / "raiz"
    shutil.copytree(RAIZ_PROYECTO / "agentes", raiz / "agentes")
    shutil.copytree(RAIZ_PROYECTO / "skills", raiz / "skills")
    datos = {"nombre": "Abogada laboral", "especialidad": "Revisa riesgos laborales de una decisión.",
             "familia": "derecho", "postura": "prudente", "formato_salida": "objeciones-priorizadas",
             "instrucciones": "Eres abogada laboral.", "sensible": True, "aviso": "No es asesoría legal."}
    async with Client(crear_servidor(raiz, tmp_path / "mas.db")) as c:
        r = (await c.call_tool("guardar_agente", datos | {"solo_validar": True})).structured_content
        assert r["ok"] and r["guardado"] is False
        r = (await c.call_tool("guardar_agente", datos)).structured_content
        assert r["ok"] and r["guardado"] is True
        lista = (await c.call_tool("listar_agentes", {"familia": "derecho"})).structured_content
    assert [(a["id"], a["propio"]) for a in lista["agentes"]] == [("abogada-laboral", True)]


async def test_prompts_debate_panel_y_crear_agente():
    async with Client(crear_servidor(RAIZ_PROYECTO)) as c:
        prompts = {p.name: p for p in (await c.list_prompts()).prompts}
        assert sorted(prompts) == ["crear_agente", "debate", "panel"]
        assert [a.name for a in prompts["debate"].arguments] == ["objetivo", "agentes", "rondas"]
        d = await c.get_prompt("debate", {"objetivo": "Bajar 30% la energía", "rondas": "3"})
        texto = d.messages[0].content.text
        assert "Bajar 30% la energía" in texto and "max_rondas 3" in texto
        assert "sugiere un equipo" in texto and "consenso" in texto  # RF-11 y reglas del moderador
        p = await c.get_prompt("panel", {"objetivo": "x", "agentes": "periodista, investigador"})
        assert "periodista, investigador" in p.messages[0].content.text
        cr = await c.get_prompt("crear_agente", {"descripcion": "una nutricionista"})
        texto = cr.messages[0].content.text
    assert "una nutricionista" in texto and "solo_validar=true" in texto
    assert "propuesta-tecnica" in texto and "segmentacion" in texto


async def test_exportar_por_mcp(tmp_path: Path):
    async with Client(crear_servidor(RAIZ_PROYECTO, tmp_path / "mas.db")) as c:
        r = await c.call_tool("exportar_agentes", {"carpeta": str(tmp_path), "agentes": ["periodista"]})
        assert r.structured_content["escritos"][0] == ".claude/agents/periodista.md"
        r = await c.call_tool("exportar_agentes", {"carpeta": str(tmp_path / "no-hay")})
        assert r.is_error and "no existe" in r.content[0].text
        sala = (await c.call_tool("abrir_sala", {"objetivo": "x", "agentes": ["periodista", "investigador"]})).structured_content
        r = await c.call_tool("exportar_sala", {"sala_id": sala["sala_id"], "archivo": str(tmp_path / "sala.md")})
    assert (tmp_path / "sala.md").is_file() and r.structured_content["ok"]
