from __future__ import annotations

from pathlib import Path

import pytest

from conftest import RAIZ_PROYECTO, crear_agente, crear_skill, escribir
from mas.core.catalogo import Catalogo, NoEncontrado


# --- Catálogo de ejemplo del repositorio -------------------------------------


def test_catalogo_del_repo_carga_sin_errores():
    cat = Catalogo(RAIZ_PROYECTO)
    assert [str(e) for e in cat.errores] == []
    assert set(cat.agentes) == {"ingeniero-industrial", "economista-ortodoxo", "periodista"}
    assert len(cat.skills) == 6


def test_cada_agente_del_repo_usa_skills_existentes():
    cat = Catalogo(RAIZ_PROYECTO)
    for agente in cat.agentes.values():
        assert [s.id for s in cat.skills_de(agente)] == agente.skills


def test_listar_por_familia_y_texto():
    cat = Catalogo(RAIZ_PROYECTO)
    assert [a.id for a in cat.listar(familia="ingenieria")] == ["ingeniero-industrial"]
    assert [a.id for a in cat.listar(familia="Ingeniería")] == ["ingeniero-industrial"]
    assert [a.id for a in cat.listar(texto="ESCÉPTICO")] == ["periodista"]
    assert [a.id for a in cat.listar(texto="costo beneficio")] == ["economista-ortodoxo"]
    assert cat.listar(texto="astronauta") == []


def test_familias_y_ficha():
    cat = Catalogo(RAIZ_PROYECTO)
    assert list(cat.familias()) == ["comunicacion", "economia", "ingenieria"]
    ficha = cat.agente("ingeniero-industrial").ficha()
    assert ficha == {
        "id": "ingeniero-industrial",
        "nombre": "Ingeniero industrial",
        "familia": "ingenieria",
        "postura": "conservador",
        "descripcion": ficha["descripcion"],
    }


def test_agente_inexistente_mensaje_en_espanol():
    cat = Catalogo(RAIZ_PROYECTO)
    with pytest.raises(NoEncontrado, match="No existe un agente con el id 'doctor'"):
        cat.agente("doctor")


# --- Validación y errores ----------------------------------------------------


def test_agente_invalido_no_se_carga_y_se_reporta(raiz_vacia: Path):
    crear_skill(raiz_vacia, "s1")
    crear_agente(raiz_vacia, "ingenieria", "bueno", skills="s1")
    crear_agente(
        raiz_vacia,
        "ingenieria",
        "malo",
        texto="---\nname: malo\ndescription: x\noutput_contract: propuesta-tecnica\n---\n\nHola\n",
    )
    cat = Catalogo(raiz_vacia)
    assert list(cat.agentes) == ["bueno"]
    assert [str(e) for e in cat.errores] == [
        "agentes/ingenieria/malo/agente.md · stance: Falta el campo obligatorio."
    ]


def test_familia_se_toma_de_la_carpeta(raiz_vacia: Path):
    crear_agente(raiz_vacia, "economia", "a1")
    assert Catalogo(raiz_vacia).agente("a1").familia == "economia"


def test_familia_que_no_coincide_con_la_carpeta(raiz_vacia: Path):
    texto = "---\nname: a1\ndescription: x\nfamily: economia\nstance: x\noutput_contract: veredicto\n---\nHola\n"
    crear_agente(raiz_vacia, "ingenieria", "a1", texto=texto)
    cat = Catalogo(raiz_vacia)
    assert not cat.agentes
    assert cat.errores[0].campo == "family"
    assert "agentes/economia/" in cat.errores[0].mensaje


def test_skill_inexistente(raiz_vacia: Path):
    crear_agente(raiz_vacia, "ingenieria", "a1", skills="no-existe")
    cat = Catalogo(raiz_vacia)
    assert not cat.agentes
    assert cat.errores[0].campo == "skills.0"
    assert "skills/no-existe/SKILL.md" in cat.errores[0].mensaje


def test_yaml_roto(raiz_vacia: Path):
    crear_agente(raiz_vacia, "x", "a1", texto="---\nname: [a1\n---\nHola\n")
    cat = Catalogo(raiz_vacia)
    assert not cat.agentes
    assert "encabezado YAML" in cat.errores[0].mensaje
    assert cat.errores[0].archivo == "agentes/x/a1/agente.md"


def test_sin_encabezado(raiz_vacia: Path):
    crear_agente(raiz_vacia, "x", "a1", texto="Solo texto.\n")
    assert "Falta el encabezado YAML" in Catalogo(raiz_vacia).errores[0].mensaje


def test_sin_instrucciones(raiz_vacia: Path):
    texto = "---\nname: a1\ndescription: x\nstance: x\noutput_contract: veredicto\n---\n\n"
    crear_agente(raiz_vacia, "x", "a1", texto=texto)
    err = Catalogo(raiz_vacia).errores[0]
    assert err.campo is None
    assert "instrucciones" in err.mensaje


def test_id_duplicado(raiz_vacia: Path):
    crear_agente(raiz_vacia, "a", "uno")
    texto = "---\nname: uno\ndescription: x\nstance: x\noutput_contract: veredicto\n---\nHola\n"
    escribir(raiz_vacia / "agentes" / "b" / "otro" / "agente.md", texto)
    cat = Catalogo(raiz_vacia)
    assert len(cat.agentes) == 1
    assert "Ya existe un agente" in cat.errores[0].mensaje


def test_skill_con_nombre_distinto_a_su_carpeta(raiz_vacia: Path):
    escribir(raiz_vacia / "skills" / "carpeta" / "SKILL.md", "---\nname: otro\ndescription: d\n---\nx\n")
    cat = Catalogo(raiz_vacia)
    assert not cat.skills
    assert cat.errores[0].campo == "name"


def test_skill_conserva_campos_extra_del_estandar(raiz_vacia: Path):
    escribir(raiz_vacia / "skills" / "s1" / "SKILL.md",
             "---\nname: s1\ndescription: d\nlicense: MIT\n---\nx\n")
    skill = Catalogo(raiz_vacia).skill("s1")
    assert skill.model_extra == {"license": "MIT"}


def test_recargar_sin_reiniciar(raiz_vacia: Path):
    cat = Catalogo(raiz_vacia)
    assert cat.agentes == {}
    crear_agente(raiz_vacia, "ingenieria", "nuevo")
    assert cat.recargar() == []
    assert "nuevo" in cat.agentes


def test_editado_a_mano_se_recarga(raiz_vacia: Path):
    ruta = crear_agente(raiz_vacia, "ingenieria", "a1")
    cat = Catalogo(raiz_vacia)
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("stance: neutral", "stance: innovador"), encoding="utf-8")
    cat.recargar()
    assert cat.agente("a1").postura == "innovador"


def test_sin_carpeta_de_agentes(tmp_path: Path):
    cat = Catalogo(tmp_path)
    assert "No se encontró la carpeta de agentes" in cat.errores[0].mensaje


def test_nucleo_no_importa_mcp_ni_visor():
    """RNF-01: core/ no depende del servidor MCP ni de la ventana."""
    carpeta = RAIZ_PROYECTO / "src" / "mas" / "core"
    for archivo in carpeta.rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for prohibido in ("import mcp", "from mcp", "PySide6", "mas.visor", "mas.mcp_server"):
            assert prohibido not in texto, f"{archivo.name} importa {prohibido}"


def test_comando_validar(capsys, raiz_vacia: Path):
    from mas.validar import main

    assert main([str(RAIZ_PROYECTO)]) == 0
    assert "3 agentes y 6 skills cargados." in capsys.readouterr().out
    crear_agente(raiz_vacia, "x", "a1", texto="Solo texto.\n")
    assert main([str(raiz_vacia)]) == 1
    assert "1 problema(s) por corregir" in capsys.readouterr().out
