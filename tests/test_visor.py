"""Pruebas del visor (paso 4): lectura por el núcleo y ventana sin pantalla."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

from conftest import RAIZ_PROYECTO
from mas.core.almacen import Almacen
from mas.core.catalogo import Catalogo
from mas.core.consulta import ConsultaSalas
from mas.core.salas import GestorSalas
from mas.core.vistas import vista_agente
from test_salas import AGENTES, OBJETIVO, VEREDICTO, artefacto, jugar_turnos, texto_valido


@pytest.fixture
def bd(tmp_path: Path) -> Path:
    return tmp_path / "salas.db"


@pytest.fixture
def catalogo() -> Catalogo:
    return Catalogo(RAIZ_PROYECTO)


@pytest.fixture
def gestor(bd: Path, catalogo: Catalogo) -> GestorSalas:
    return GestorSalas(catalogo, Almacen(bd))


def cerrar(gestor: GestorSalas, sala_id: str) -> None:
    jugar_turnos(gestor, sala_id)
    gestor.veredicto(sala_id)
    r = gestor.veredicto(sala_id, contenido=VEREDICTO, acuerdos=["Medir primero"], desacuerdos=["Plazo"],
                         confianza=0.6, plan=["Auditar"])
    assert r.get("estado") == "cerrada" or r.get("ok", True), r


# --- Núcleo: ConsultaSalas ----------------------------------------------------


def test_sin_base_no_falla(tmp_path: Path):
    consulta = ConsultaSalas(tmp_path / "no-existe.db")
    assert consulta.listar() == [] and consulta.detalle("x") is None
    assert not (tmp_path / "no-existe.db").exists()  # leer nunca crea la base


def test_lista_busca_y_detalla(gestor: GestorSalas, bd: Path, catalogo: Catalogo):
    cerrada = gestor.abrir_sala(OBJETIVO, AGENTES, "panel")["sala_id"]
    cerrar(gestor, cerrada)
    en_curso = gestor.abrir_sala("Lanzar una app de recetas", AGENTES[:2], "panel")["sala_id"]
    consulta = ConsultaSalas(bd, catalogo)

    assert [s.id for s in consulta.listar()] == [en_curso, cerrada]
    assert [s.id for s in consulta.listar("energético")] == [cerrada]
    assert consulta.listar("no aparece") == []

    d = consulta.detalle(cerrada)
    assert not d.en_curso and len(d.turnos) == 3 and d.pendientes == 0
    assert d.veredicto and "Medir primero" in d.veredicto_md()
    assert "Ingeniero industrial" in d.mesa_md()
    assert d.hilo_md("periodista").startswith("## Hilo de")
    completo = d.completo_md()
    for parte in ("## Mesa", "## Hilo de", "## Veredicto", OBJETIVO):
        assert parte in completo

    d2 = consulta.detalle(en_curso)
    assert d2.en_curso and d2.turnos == [] and d2.veredicto is None
    antes = d2.firma()
    t = gestor.siguiente_turno(en_curso)
    assert consulta.detalle(en_curso).pendientes == 1
    gestor.publicar_turno(en_curso, t["turno_id"], texto_valido(t), artefacto())
    despues = consulta.detalle(en_curso)
    assert len(despues.turnos) == 1 and despues.firma() != antes


def test_leer_mientras_el_servidor_escribe(gestor: GestorSalas, bd: Path):
    """RNF-10: con una escritura abierta, el visor sigue leyendo sin error de bloqueo."""
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES, "panel")["sala_id"]
    consulta = ConsultaSalas(bd)
    with gestor.almacen.transaccion():
        assert [s.id for s in consulta.listar()] == [sala_id]
        assert consulta.detalle(sala_id) is not None


def test_ficha_de_agente(catalogo: Catalogo):
    agente = catalogo.agente("ingeniero-industrial")
    texto = vista_agente(agente, catalogo.skills_de(agente))
    assert agente.postura in texto and "## Skills" in texto and "Propuesta técnica" in texto


def test_visor_no_usa_sql():
    """RNF-11: el visor lee a través del núcleo, nunca importa sqlite3."""
    for archivo in (RAIZ_PROYECTO / "src" / "mas" / "visor").rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        modulos = {a.name for n in ast.walk(arbol) if isinstance(n, ast.Import) for a in n.names}
        modulos |= {n.module for n in ast.walk(arbol) if isinstance(n, ast.ImportFrom) and n.module}
        assert not any(m and m.split(".")[0] == "sqlite3" for m in modulos), archivo


# --- Ventana (Qt sin pantalla) ------------------------------------------------


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_ventana_muestra_y_refresca(qapp, gestor: GestorSalas, bd: Path, tmp_path: Path):
    from mas.visor.app import crear_ventana

    cerrada = gestor.abrir_sala(OBJETIVO, AGENTES, "panel")["sala_id"]
    cerrar(gestor, cerrada)
    ventana = crear_ventana(RAIZ_PROYECTO, bd)
    salas = ventana.salas

    assert salas.tabla.rowCount() == 1
    salas.tabla.selectRow(0)
    detalle = salas.detalle
    assert detalle.detalle.sala.id == cerrada
    assert len(detalle.columnas) == 3  # una columna de hilo por agente
    assert "Medir primero" in detalle.veredicto.markdown_actual()

    # Una sala nueva aparece sola al refrescar (RF-18), sin perder la elegida.
    nueva = gestor.abrir_sala("Lanzar una app de recetas", AGENTES[:2], "panel")["sala_id"]
    ventana.refrescar()
    assert salas.tabla.rowCount() == 2 and salas.sala_elegida() == cerrada

    # Turnos de una sala en curso aparecen en Hilos (CA-07).
    salas.tabla.selectRow(0)
    assert salas.sala_elegida() == nueva
    t = gestor.siguiente_turno(nueva)
    gestor.publicar_turno(nueva, t["turno_id"], texto_valido(t, "Texto nuevo del hilo."), artefacto())
    ventana.refrescar()
    assert "Texto nuevo del hilo." in detalle.columnas[t["agente"]["id"]].markdown_actual()

    # Buscar (RF-19).
    salas.buscador.setText("recetas")
    assert salas.tabla.rowCount() == 1
    salas.buscador.setText("nada parecido")
    assert salas.vacio.isVisibleTo(salas)

    # Exportar (RF-19).
    salas.buscador.clear()
    salas.tabla.selectRow(1)
    destino = salas.exportar(tmp_path / "sala.md")
    assert destino and "## Veredicto" in destino.read_text(encoding="utf-8")

    # Catálogo (RF-16).
    cat = ventana.catalogo
    assert cat.arbol.topLevelItemCount() >= 3
    familia = cat.arbol.topLevelItem(0)
    cat.arbol.setCurrentItem(familia.child(0))
    assert "## Formato de salida" in cat.ficha.markdown_actual()
    ventana.close()
