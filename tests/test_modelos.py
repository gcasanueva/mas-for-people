from __future__ import annotations

import pytest
from pydantic import ValidationError

from mas.core.modelos import (
    Agente,
    Artefacto,
    Mesa,
    PosturaArtefacto,
    Sala,
    Turno,
    contar_palabras,
    traducir_errores,
)

BASE = {
    "name": "ingeniero-x",
    "description": "Un ingeniero.",
    "family": "ingenieria",
    "stance": "pragmático",
    "output_contract": "propuesta-tecnica",
    "instructions": "Eres un ingeniero.",
}


def errores_de(datos: dict) -> dict[str, str]:
    with pytest.raises(ValidationError) as exc:
        Agente.model_validate(datos)
    return {e.campo or "": e.mensaje for e in traducir_errores(exc.value, "agente.md")}


def test_agente_valido_con_valores_por_defecto():
    agente = Agente.model_validate(BASE)
    assert agente.id == "ingeniero-x"
    assert agente.nombre == "Ingeniero x"
    assert agente.limites.max_palabras_turno == 400
    assert agente.skills == []


def test_tools_acepta_texto_separado_por_comas_como_claude_code():
    agente = Agente.model_validate({**BASE, "tools": "Read, Grep"})
    assert agente.herramientas == ["Read", "Grep"]


def test_model_acepta_texto_u_objeto():
    assert Agente.model_validate({**BASE, "model": "sonnet"}).modelo == "sonnet"
    agente = Agente.model_validate({**BASE, "model": {"preferred": "claude", "alternatives": ["gpt"]}})
    assert agente.modelo.alternativas == ["gpt"]


@pytest.mark.parametrize("nombre", ["Ingeniero", "ingeniero_x", "ingeniería", "-x", ""])
def test_id_invalido(nombre):
    errores = errores_de({**BASE, "name": nombre})
    assert "name" in errores


def test_campo_obligatorio_en_espanol():
    datos = dict(BASE)
    del datos["stance"]
    assert errores_de(datos) == {"stance": "Falta el campo obligatorio."}


def test_formato_de_salida_desconocido():
    errores = errores_de({**BASE, "output_contract": "poema"})
    assert "poema" in errores["output_contract"]
    assert "propuesta-tecnica" in errores["output_contract"]


def test_campo_desconocido_rechazado():
    assert "stanse" in errores_de({**BASE, "stanse": "x"})


def test_agente_sensible_exige_aviso():
    errores = errores_de({**BASE, "sensitive": True})
    assert "disclaimer" in next(iter(errores.values()))
    Agente.model_validate({**BASE, "sensitive": True, "disclaimer": "No es consejo médico."})


def test_skills_repetidas():
    errores = errores_de({**BASE, "skills": ["a", "a"]})
    assert "más de una vez" in errores["skills"]


def test_limites_fuera_de_rango():
    errores = errores_de({**BASE, "limits": {"max_words_per_turn": 10}})
    assert errores["limits.max_words_per_turn"] == "Debe ser mayor o igual que 50."


def test_ida_y_vuelta_a_agente_md():
    from mas.core.catalogo import parsear_agente

    original = Agente.model_validate({**BASE, "skills": ["a-b"], "title": "Ingeniero X"})
    texto = original.a_agente_md()
    assert texto.startswith("---\nname: ingeniero-x\n")
    copia = parsear_agente(texto, "agente.md")
    assert isinstance(copia, Agente)
    assert copia.model_dump() == original.model_dump()


def test_sala_valida_limites():
    sala = Sala(objetivo="Reducir consumo", agentes=["a", "b"])
    assert sala.estado.value == "abierta"
    assert sala.max_rondas == 2
    with pytest.raises(ValidationError):
        Sala(objetivo="x", agentes=["a"])
    with pytest.raises(ValidationError):
        Sala(objetivo="x", agentes=list("abcdefg"))
    with pytest.raises(ValidationError):
        Sala(objetivo="x", agentes=["a", "b"], max_rondas=5)
    with pytest.raises(ValidationError):
        Sala(objetivo="x", agentes=["a", "a"])


def test_artefacto_estandar():
    art = Artefacto(postura="objecion", resumen="No cuadra.", confianza=0.6)
    assert art.postura is PosturaArtefacto.OBJECION
    with pytest.raises(ValidationError):
        Artefacto(postura="opinion", resumen="x", confianza=0.5)
    with pytest.raises(ValidationError):
        Artefacto(postura="apoyo", resumen="x", confianza=1.5)


def test_mesa_resume_sin_textos_completos_y_excluye_al_propio_agente():
    turnos = [
        Turno(sala_id="s", agente_id="a", ronda=1, contenido="largo " * 300,
              artefacto=Artefacto(postura="propuesta", resumen="Plan A", confianza=0.7)),
        Turno(sala_id="s", agente_id="b", ronda=1, contenido="otro texto",
              artefacto=Artefacto(postura="objecion", resumen="Falla X", confianza=0.5)),
        Turno(sala_id="s", agente_id="c", ronda=1, contenido="sin artefacto"),
    ]
    assert turnos[0].palabras == 300
    resumen = Mesa.desde_turnos("s", turnos).resumen(excluir="a")
    assert resumen == [
        {"turno_id": turnos[1].id, "agente": "b", "ronda": 1,
         "postura": "objecion", "resumen": "Falla X", "confianza": 0.5}
    ]


def test_contar_palabras():
    assert contar_palabras("  uno dos\ntres ") == 3
