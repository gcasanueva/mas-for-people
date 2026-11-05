"""Pruebas de guardar_agente (paso 6, CU-02, RF-04, CA-02), sin MCP (RNF-01)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from conftest import RAIZ_PROYECTO
from mas.core.almacen import Almacen
from mas.core.catalogo import Catalogo
from mas.core.creacion import a_id, guardar_agente, opciones_creacion
from mas.core.salas import GestorSalas


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    r = tmp_path / "raiz"
    shutil.copytree(RAIZ_PROYECTO / "agentes", r / "agentes")
    shutil.copytree(RAIZ_PROYECTO / "skills", r / "skills")
    return r


@pytest.fixture
def catalogo(raiz: Path) -> Catalogo:
    return Catalogo(raiz)


def datos(**cambios) -> dict:
    base = {
        "nombre": "Ingeniera de datos",
        "especialidad": "Diseña tableros y mediciones para decidir con datos.",
        "familia": "Ingeniería",
        "postura": "pragmática",
        "skills": ["arquitectura-software"],
        "formato_salida": "propuesta-tecnica",
        "instrucciones": "Eres una ingeniera de datos.\n\n## Cómo trabajas\n- Mide antes de decidir.",
    }
    base.update(cambios)
    return base


def test_a_id():
    assert a_id("Ingeniera de Datos") == "ingeniera-de-datos"
    assert a_id("  Economía   política! ") == "economia-politica"


def test_borrador_no_escribe_nada(catalogo: Catalogo, raiz: Path):
    r = guardar_agente(catalogo, **datos(), solo_validar=True)
    assert r["ok"] and r["guardado"] is False
    assert r["id"] == "ingeniera-de-datos"
    assert r["ruta"] == "mis-agentes/ingenieria/ingeniera-de-datos/agente.md"
    assert r["agente_md"].startswith("---\nname: ingeniera-de-datos")
    assert "title: Ingeniera de datos" in r["agente_md"]
    assert not (raiz / "mis-agentes").exists()
    assert "ingeniera-de-datos" not in catalogo.agentes


def test_guardar_y_aparece_sin_reiniciar(catalogo: Catalogo, raiz: Path):
    """CA-02: queda como archivo válido y aparece en el catálogo."""
    r = guardar_agente(catalogo, **datos())
    assert r["ok"] and r["guardado"] is True and not r["reemplaza"]
    archivo = raiz / r["ruta"]
    assert archivo.is_file()
    assert "ingeniera-de-datos" in catalogo.agentes
    assert catalogo.es_propio("ingeniera-de-datos")
    otro = Catalogo(raiz)  # otro proceso (el visor) lo lee igual, sin errores
    assert otro.errores == [] and otro.agente("ingeniera-de-datos").familia == "ingenieria"
    assert [a.id for a in otro.listar(texto="tableros")] == ["ingeniera-de-datos"]


def test_un_agente_creado_entra_a_una_sala(catalogo: Catalogo, tmp_path: Path):
    guardar_agente(catalogo, **datos())
    gestor = GestorSalas(catalogo, Almacen(tmp_path / "s.db"))
    sala_id = gestor.abrir_sala("Medir consumo", ["ingeniera-de-datos", "periodista"])["sala_id"]
    t = gestor.siguiente_turno(sala_id)
    assert t["agente"]["id"] == "ingeniera-de-datos" and t["agente"]["postura"] == "pragmática"
    assert [s["id"] for s in t["skills"]] == ["arquitectura-software"]


def test_errores_claros_y_opciones(catalogo: Catalogo, raiz: Path):
    r = guardar_agente(catalogo, **datos(formato_salida="poema", skills=["magia"], instrucciones=" "))
    assert not r["ok"]
    texto = " ".join(r["errores"])
    assert "poema" in texto and "instrucciones" in texto
    assert "propuesta-tecnica" in r["formatos_validos"] and "segmentacion" in r["skills_disponibles"]
    r = guardar_agente(catalogo, **datos(skills=["magia"]))
    assert not r["ok"] and "La skill 'magia' no existe" in r["errores"][0]
    r = guardar_agente(catalogo, **datos(sensible=True))
    assert not r["ok"] and "disclaimer" in r["errores"][0]
    assert not (raiz / "mis-agentes").exists()


def test_agente_sensible_con_aviso(catalogo: Catalogo):
    r = guardar_agente(catalogo, **datos(nombre="Orientadora de salud", familia="salud", formato_salida="nota-critica",
                                         skills=[], sensible=True, aviso="No reemplaza una consulta médica."))
    assert r["ok"], r
    assert catalogo.agente("orientadora-de-salud").sensible


def test_no_pisa_un_agente_existente_sin_reemplazar(catalogo: Catalogo):
    r = guardar_agente(catalogo, **datos(nombre="Periodista"))
    assert not r["ok"] and "reemplazar=true" in r["errores"][0]
    r = guardar_agente(catalogo, **datos(nombre="Verificador"))
    assert not r["ok"] and "agente de sistema" in r["errores"][0]


def test_editar_un_agente_propio(catalogo: Catalogo, raiz: Path):
    guardar_agente(catalogo, **datos())
    r = guardar_agente(catalogo, **datos(postura="escéptica"), reemplazar=True)
    assert r["ok"] and r["reemplaza"]
    assert catalogo.agente("ingeniera-de-datos").postura == "escéptica"
    # Cambiar de familia mueve el archivo y no deja el viejo.
    r = guardar_agente(catalogo, **datos(familia="datos"), id="ingeniera-de-datos", reemplazar=True)
    assert r["ok"] and r["ruta"] == "mis-agentes/datos/ingeniera-de-datos/agente.md"
    assert not (raiz / "mis-agentes/ingenieria/ingeniera-de-datos").exists()
    assert catalogo.errores == [] and catalogo.agente("ingeniera-de-datos").familia == "datos"


def test_editar_un_agente_base_en_su_sitio(catalogo: Catalogo, raiz: Path):
    base = catalogo.agente("periodista")
    r = guardar_agente(
        catalogo, nombre="Periodista", especialidad=base.descripcion, familia="comunicacion", postura="curioso",
        skills=base.skills, formato_salida=base.formato_salida, instrucciones=base.instrucciones, reemplazar=True,
    )
    assert r["ok"] and r["ruta"] == "agentes/comunicacion/periodista/agente.md"
    assert catalogo.agente("periodista").postura == "curioso" and not catalogo.es_propio("periodista")


def test_opciones_de_creacion(catalogo: Catalogo):
    op = opciones_creacion(catalogo)
    assert "ingenieria" in op["familias"]
    assert "veredicto" not in [f["id"] for f in op["formatos"]]
    assert len(op["skills"]) == 18
