"""Pruebas del ciclo de una sala en modo panel (paso 3), sin MCP (RNF-01)."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from conftest import RAIZ_PROYECTO
from mas.core.almacen import Almacen
from mas.core.catalogo import Catalogo
from mas.core.formatos import formato, secciones_faltantes
from mas.core.modelos import EstadoSala
from mas.core.protocolos import Panel, TransicionInvalida
from mas.core.salas import LISTO_PARA_VEREDICTO, ErrorSala, GestorSalas, cargar_verificador

AGENTES = ["ingeniero-industrial", "economista-ortodoxo", "periodista"]
OBJETIVO = "Reducir 30% el consumo energético de una planta de envasado"


@pytest.fixture
def bd(tmp_path: Path) -> Path:
    return tmp_path / "salas.db"


@pytest.fixture
def gestor(bd: Path) -> GestorSalas:
    return GestorSalas(Catalogo(RAIZ_PROYECTO), Almacen(bd))


def texto_valido(turno: dict, relleno: str = "Texto de la sección.") -> str:
    return "\n\n".join(f"## {s}\n{relleno}" for s in turno["formato_salida"]["secciones"])


def artefacto(**cambios) -> dict:
    datos = {"postura": "propuesta", "resumen": "Cambiar motores por unos de alta eficiencia.", "confianza": 0.7,
             "supuestos": ["Tarifa estable"], "riesgos": ["Paradas de línea"]}
    datos.update(cambios)
    return datos


def jugar_turnos(gestor: GestorSalas, sala_id: str) -> list[dict]:
    """Juega todos los turnos con respuestas válidas y devuelve los contextos recibidos."""
    contextos = []
    while True:
        t = gestor.siguiente_turno(sala_id)
        if t.get("estado") == LISTO_PARA_VEREDICTO:
            return contextos
        contextos.append(t)
        r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t), artefacto(resumen=f"Idea de {t['agente']['id']}"))
        assert r["ok"], r


VEREDICTO = "## Acuerdos\nMedir primero.\n\n## Desacuerdos\nPlazo.\n\n## Confianza\n0.6\n\n## Plan de acción\n1. Auditar."


# --- Ciclo completo ------------------------------------------------------------


def test_panel_de_punta_a_punta(gestor: GestorSalas, bd: Path):
    abierta = gestor.abrir_sala(OBJETIVO, AGENTES, "panel")
    sala_id = abierta["sala_id"]
    assert abierta["estado"] == "abierta"
    assert [p["agente"] for p in abierta["plan"]] == AGENTES
    assert {p["ronda"] for p in abierta["plan"]} == {1}

    contextos = jugar_turnos(gestor, sala_id)
    assert [c["agente"]["id"] for c in contextos] == AGENTES
    for c in contextos:
        assert c["objetivo"] == OBJETIVO
        assert c["instrucciones"] and c["skills"]  # el periodista y los demás traen skills
        assert c["hilo"] == [] and c["resumen_mesa"] == []  # panel: nadie ve a los demás
        assert c["posturas_artefacto"] == ["propuesta"]
    assert [c["turnos_restantes"] for c in contextos] == [2, 1, 0]
    assert gestor.almacen.sala(sala_id).estado is EstadoSala.PROPUESTAS

    turno_v = gestor.veredicto(sala_id)
    assert turno_v["agente"]["id"] == "verificador"
    assert turno_v["objetivo"] == OBJETIVO
    assert [m["agente"] for m in turno_v["mesa"]] == AGENTES
    assert turno_v["mesa"][0]["artefacto"]["riesgos"] == ["Paradas de línea"]
    assert turno_v["formato_salida"]["secciones"] == ["Acuerdos", "Desacuerdos", "Confianza", "Plan de acción"]
    # Pedirlo de nuevo devuelve lo mismo (si Claude se pierde, no rompe nada).
    assert gestor.veredicto(sala_id)["mesa"] == turno_v["mesa"]
    assert gestor.siguiente_turno(sala_id)["estado"] == LISTO_PARA_VEREDICTO

    cierre = gestor.veredicto(sala_id, VEREDICTO, acuerdos=["Medir primero"], desacuerdos=["Plazo"],
                              confianza=0.6, plan=["Auditar"])
    assert cierre["ok"] and cierre["estado"] == "cerrada"
    assert cierre["veredicto"]["plan"] == ["Auditar"]

    # CA-06: otra instancia (como si pasaran días) lee la sala cerrada.
    otro = GestorSalas(Catalogo(RAIZ_PROYECTO), Almacen(bd))
    assert otro.almacen.sala(sala_id).estado is EstadoSala.CERRADA
    assert len(otro.almacen.turnos(sala_id)) == 3
    assert otro.almacen.veredicto(sala_id).confianza == 0.6
    assert otro.veredicto(sala_id)["veredicto"]["acuerdos"] == ["Medir primero"]
    with pytest.raises(ErrorSala, match="ya está cerrada"):
        otro.siguiente_turno(sala_id)


def test_siguiente_turno_repite_el_pendiente(gestor: GestorSalas):
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES[:2])["sala_id"]
    a = gestor.siguiente_turno(sala_id)
    b = gestor.siguiente_turno(sala_id)
    assert a["turno_id"] == b["turno_id"] and a["agente"] == b["agente"]
    assert len(gestor.almacen.turnos(sala_id)) == 1


def test_postura_de_sala_reemplaza_la_del_agente(gestor: GestorSalas):
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES[:2], posturas={"ingeniero-industrial": "innovador"})["sala_id"]
    t = gestor.siguiente_turno(sala_id)
    assert t["agente"]["postura"] == "innovador"
    assert "innovador" in t["indicacion"]


# --- publicar_turno rechaza lo que no cumple (CA-05) ---------------------------


def test_publicar_rechaza_y_luego_acepta_la_correccion(gestor: GestorSalas):
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES[:2], max_palabras=100)["sala_id"]
    t = gestor.siguiente_turno(sala_id)

    r = gestor.publicar_turno(sala_id, t["turno_id"], "## Propuesta\nSolo esto.", artefacto())
    assert not r["ok"]
    assert "Supuestos, Riesgos, Confianza, Qué cambiaría mi opinión" in r["errores"][0]

    r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t, "palabra " * 40), artefacto())
    assert not r["ok"] and "límite de la sala es 100" in r["errores"][0]

    r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t),
                              artefacto(postura="objecion", confianza=3, responde_a=["nada"]))
    assert not r["ok"]
    texto = " ".join(r["errores"])
    assert "artefacto · confianza" in texto
    assert all(t2.artefacto is None for t2 in gestor.almacen.turnos(sala_id))  # no se guardó nada

    r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t), artefacto(postura="objecion"))
    assert not r["ok"] and "solo puede tener postura propuesta" in r["errores"][0]

    r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t), artefacto(responde_a=["zzz"]))
    assert not r["ok"] and "zzz" in r["errores"][0]

    r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t), artefacto())
    assert r["ok"] and r["turnos_publicados"] == 1
    with pytest.raises(ErrorSala, match="ya se publicó"):
        gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t), artefacto())


def test_publicar_turno_de_otra_sala(gestor: GestorSalas):
    s1 = gestor.abrir_sala(OBJETIVO, AGENTES[:2])["sala_id"]
    s2 = gestor.abrir_sala(OBJETIVO, AGENTES[:2])["sala_id"]
    t = gestor.siguiente_turno(s1)
    with pytest.raises(ErrorSala, match="no pertenece a la sala"):
        gestor.publicar_turno(s2, t["turno_id"], texto_valido(t), artefacto())


def test_secciones_se_reconocen_con_distintos_estilos():
    fmt = formato("propuesta-tecnica")
    texto = (
        "## Propuesta\nx\n**Supuestos:** y\n- RIESGOS — z\nconfianza: 0.7\n"
        "### 5. Que cambiaria mi opinion\nw"
    )
    assert secciones_faltantes(texto, fmt) == []
    assert secciones_faltantes("Hablo de riesgos en medio de una frase.", fmt) == list(fmt.secciones)


# --- veredicto -----------------------------------------------------------------


def test_veredicto_no_deja_saltar_estados(gestor: GestorSalas):
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES[:2])["sala_id"]
    with pytest.raises(ErrorSala, match="quedan turnos"):
        gestor.veredicto(sala_id)
    jugar_turnos(gestor, sala_id)
    with pytest.raises(ErrorSala, match="Primero llama a veredicto solo con el sala_id"):
        gestor.veredicto(sala_id, VEREDICTO, confianza=0.5)
    gestor.veredicto(sala_id)

    r = gestor.veredicto(sala_id, "## Acuerdos\nalgo")
    assert not r["ok"]
    assert any("Desacuerdos" in e for e in r["errores"])
    assert any("confianza" in e for e in r["errores"])
    r = gestor.veredicto(sala_id, VEREDICTO, confianza=7)
    assert not r["ok"] and "veredicto · confianza" in r["errores"][0]
    assert gestor.almacen.sala(sala_id).estado is EstadoSala.VERIFICACION

    assert gestor.veredicto(sala_id, VEREDICTO, confianza=0.5)["ok"]


def test_verificador_es_un_agente_valido():
    v = cargar_verificador()
    assert v.id == "verificador" and v.familia == "sistema"
    assert v.formato_salida == "veredicto"


def test_maquina_de_estados_del_panel():
    p = Panel()
    p.validar_transicion(EstadoSala.ABIERTA, EstadoSala.PROPUESTAS)
    with pytest.raises(TransicionInvalida):
        p.validar_transicion(EstadoSala.ABIERTA, EstadoSala.CERRADA)
    with pytest.raises(TransicionInvalida):
        p.validar_transicion(EstadoSala.PROPUESTAS, EstadoSala.CRITICA)


# --- abrir_sala ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("argumentos", "mensaje"),
    [
        ({"agentes": ["ingeniero-industrial", "astronauta"]}, "astronauta' no está en el catálogo"),
        ({"agentes": ["periodista"]}, "al menos 2"),
        ({"protocolo": "debate"}, "todavía no está disponible"),
        ({"protocolo": "asamblea"}, "Protocolo desconocido"),
        ({"posturas": {"economista-ortodoxo": "x"}}, "no está en la sala"),
        ({"objetivo": "  "}, "objetivo"),
    ],
)
def test_abrir_sala_con_errores_claros(gestor: GestorSalas, argumentos: dict, mensaje: str):
    datos = {"objetivo": OBJETIVO, "agentes": AGENTES[:1] + AGENTES[2:]} | argumentos
    with pytest.raises(ErrorSala, match=mensaje):
        gestor.abrir_sala(**datos)
    assert gestor.almacen.listar_salas() == []


# --- ver_sala ------------------------------------------------------------------


def test_ver_sala(gestor: GestorSalas):
    assert "Todavía no hay salas" in gestor.ver_sala()
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES)["sala_id"]
    assert "La mesa está vacía" in gestor.ver_sala(sala_id)
    jugar_turnos(gestor, sala_id)
    gestor.veredicto(sala_id)
    gestor.veredicto(sala_id, VEREDICTO, acuerdos=["Medir primero"], confianza=0.6)

    lista = gestor.ver_sala()
    assert sala_id in lista and "cerrada" in lista and "panel" in lista
    mesa = gestor.ver_sala(sala_id, "mesa")
    assert "### Periodista · ronda 1 · propuesta · confianza 0.70" in mesa
    assert "Idea de periodista" in mesa and "Paradas de línea" in mesa
    hilo = gestor.ver_sala(sala_id, "hilo", "periodista")
    assert "## Hilo de Periodista" in hilo and "## Lo que se afirma" in hilo
    assert "Hilo de Ingeniero" not in hilo
    assert gestor.ver_sala(sala_id, "hilo").count("## Hilo de") == 3
    veredicto = gestor.ver_sala(sala_id, "veredicto")
    assert "**Confianza:** 0.60" in veredicto and "Medir primero" in veredicto
    with pytest.raises(ErrorSala, match="no participa"):
        gestor.ver_sala(sala_id, "hilo", "astronauta")
    with pytest.raises(ErrorSala, match="Vista desconocida"):
        gestor.ver_sala(sala_id, "todo")
    with pytest.raises(ErrorSala, match="No existe una sala"):
        gestor.ver_sala("nada")


# --- No funcionales ------------------------------------------------------------


def test_contexto_de_cada_turno_cabe_en_3000_palabras(tmp_path: Path, bd: Path):
    """RNF-02 / CA-04: 6 agentes, textos al límite, verificador incluido."""
    raiz = tmp_path / "raiz"
    shutil.copytree(RAIZ_PROYECTO / "skills", raiz / "skills")
    shutil.copytree(RAIZ_PROYECTO / "agentes", raiz / "agentes")
    for original in AGENTES:  # 3 agentes más, copias de los reales con otro nombre
        origen = next((raiz / "agentes").rglob(f"{original}/agente.md"))
        copia = origen.parent.parent / f"{original}-bis" / "agente.md"
        copia.parent.mkdir()
        copia.write_text(origen.read_text(encoding="utf-8").replace(f"name: {original}", f"name: {original}-bis"),
                         encoding="utf-8")
    gestor = GestorSalas(Catalogo(raiz), Almacen(bd))
    assert len(gestor.catalogo.agentes) == 6
    sala_id = gestor.abrir_sala(OBJETIVO, sorted(gestor.catalogo.agentes), max_palabras=400)["sala_id"]
    while (t := gestor.siguiente_turno(sala_id)).get("estado") != LISTO_PARA_VEREDICTO:
        assert t["palabras_contexto"] <= 3000, t["agente"]
        relleno = "palabra " * (400 // len(t["formato_salida"]["secciones"]) - 3)
        r = gestor.publicar_turno(sala_id, t["turno_id"], texto_valido(t, relleno), artefacto(resumen="r" * 600))
        assert r["ok"], r
    assert gestor.veredicto(sala_id)["palabras_contexto"] <= 3000


def test_lectura_en_paralelo_con_wal(gestor: GestorSalas, bd: Path):
    """RNF-10: el visor lee (solo lectura) mientras el servidor tiene una escritura abierta."""
    sala_id = gestor.abrir_sala(OBJETIVO, AGENTES[:2])["sala_id"]
    lector = Almacen(bd, solo_lectura=True)
    with gestor.almacen.transaccion() as con:
        con.execute("UPDATE salas SET objetivo='cambiando' WHERE id=?", (sala_id,))
        assert lector.sala(sala_id).objetivo == OBJETIVO  # lee lo último confirmado, sin bloquearse
    assert lector.sala(sala_id).objetivo == "cambiando"
    with pytest.raises(sqlite3.OperationalError):
        with lector.transaccion() as con:
            con.execute("DELETE FROM salas")
    con = sqlite3.connect(bd)
    try:
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    finally:
        con.close()
