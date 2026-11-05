"""Pruebas del paso 7: exportar a Claude Code (CU-06, RF-12) y sala a Markdown (RF-15)."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest

from conftest import RAIZ_PROYECTO
from mas.core.almacen import Almacen
from mas.core.catalogo import Catalogo
from mas.core.exportar import ErrorExportar, exportar_claude_code, subagente_md
from mas.core.salas import ErrorSala, GestorSalas


@pytest.fixture
def catalogo() -> Catalogo:
    return Catalogo(RAIZ_PROYECTO)


def test_subagente_tiene_el_formato_de_claude_code(catalogo: Catalogo):
    post = frontmatter.loads(subagente_md(catalogo.agente("periodista")))
    assert set(post.metadata) == {"name", "description", "skills"}  # solo campos que Claude Code entiende
    assert post.metadata["name"] == "periodista"
    assert post.metadata["skills"] == "verificacion-fuentes, piramide-invertida"
    assert post.content.startswith("Eres Periodista. Tu postura por defecto es: escéptico.")
    assert "Lo que se afirma, Lo que falta verificar, Preguntas críticas, Fuentes" in post.content


def test_exportar_algunos_agentes(catalogo: Catalogo, tmp_path: Path):
    r = exportar_claude_code(catalogo, tmp_path, ["periodista", "investigador"])
    assert r["ok"] and r["agentes"] == ["periodista", "investigador"] and r["omitidos"] == []
    assert (tmp_path / ".claude/agents/periodista.md").is_file()
    assert (tmp_path / ".claude/agents/investigador.md").is_file()
    for skill in ("verificacion-fuentes", "piramide-invertida", "busqueda-literatura", "evaluar-evidencia"):
        assert (tmp_path / f".claude/skills/{skill}/SKILL.md").is_file()
    assert len(list((tmp_path / ".claude/skills").iterdir())) == 4


def test_exportar_todos_y_no_pisar_cambios(catalogo: Catalogo, tmp_path: Path):
    r = exportar_claude_code(catalogo, tmp_path)
    assert len(r["agentes"]) == 9 and len(list((tmp_path / ".claude/agents").glob("*.md"))) == 9
    # Volver a exportar lo mismo no molesta.
    assert exportar_claude_code(catalogo, tmp_path)["omitidos"] == []
    # Un archivo cambiado a mano no se pisa sin reemplazar.
    editado = tmp_path / ".claude/agents/periodista.md"
    editado.write_text("mío", encoding="utf-8")
    (tmp_path / ".claude/skills/deteccion-sesgos/SKILL.md").write_text("mía", encoding="utf-8")
    r = exportar_claude_code(catalogo, tmp_path)
    assert r["omitidos"] == [".claude/agents/periodista.md", ".claude/skills/deteccion-sesgos/"]
    assert editado.read_text(encoding="utf-8") == "mío"
    r = exportar_claude_code(catalogo, tmp_path, ["periodista"], reemplazar=True)
    assert r["omitidos"] == [] and editado.read_text(encoding="utf-8").startswith("---\nname: periodista")


def test_exportar_errores_claros(catalogo: Catalogo, tmp_path: Path):
    with pytest.raises(ErrorExportar, match="no existe"):
        exportar_claude_code(catalogo, tmp_path / "no-hay")
    with pytest.raises(ErrorExportar, match="astronauta"):
        exportar_claude_code(catalogo, tmp_path, ["astronauta"])
    assert not (tmp_path / ".claude").exists()


def test_comando_mas_exportar(tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch):
    from mas.exportar import main

    monkeypatch.setenv("MAS_CARPETA", str(RAIZ_PROYECTO))
    assert main([str(tmp_path), "abogado-del-diablo"]) == 0
    salida = capsys.readouterr().out
    assert "1 agente(s) exportado(s)" in salida and ".claude/agents/abogado-del-diablo.md" in salida
    assert main([]) == 2
    assert main([str(tmp_path / "no-hay")]) == 1


def test_exportar_sala_a_markdown(catalogo: Catalogo, tmp_path: Path):
    gestor = GestorSalas(catalogo, Almacen(tmp_path / "s.db"))
    sala_id = gestor.abrir_sala("Bajar costos", ["periodista", "investigador"], "panel")["sala_id"]
    destino = tmp_path / "informe"
    r = gestor.exportar_sala(sala_id, str(destino))
    assert r["ok"] and r["ruta"].endswith("informe.md")
    texto = Path(r["ruta"]).read_text(encoding="utf-8")
    assert texto.startswith(f"# Sala {sala_id}") and "## Mesa" in texto and "## Veredicto" in texto
    with pytest.raises(ErrorSala, match="No existe una sala"):
        gestor.exportar_sala("nada")


def test_exportar_sala_por_defecto_va_a_exportados(tmp_path: Path):
    import shutil

    raiz = tmp_path / "raiz"
    shutil.copytree(RAIZ_PROYECTO / "agentes", raiz / "agentes")
    shutil.copytree(RAIZ_PROYECTO / "skills", raiz / "skills")
    gestor = GestorSalas(Catalogo(raiz), Almacen(tmp_path / "s.db"))
    sala_id = gestor.abrir_sala("x", ["periodista", "investigador"])["sala_id"]
    r = gestor.exportar_sala(sala_id)
    assert Path(r["ruta"]) == (raiz / "exportados" / f"sala-{sala_id}.md").resolve()
