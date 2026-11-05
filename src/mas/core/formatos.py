"""Formatos de salida (``output_contract``) que puede usar un agente.

Cada formato dice qué secciones debe traer el texto de un turno. Además,
todo turno entrega el artefacto estándar (ver ``modelos.Artefacto``), así
que las secciones de aquí son las del texto libre, no las del artefacto.
La comprobación de las secciones se hace al publicar un turno
(``secciones_faltantes``).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class FormatoSalida:
    id: str
    nombre: str
    secciones: tuple[str, ...]


FORMATOS: dict[str, FormatoSalida] = {
    f.id: f
    for f in (
        FormatoSalida(
            "propuesta-tecnica",
            "Propuesta técnica",
            ("Propuesta", "Supuestos", "Riesgos", "Confianza", "Qué cambiaría mi opinión"),
        ),
        FormatoSalida(
            "analisis-economico",
            "Análisis económico",
            ("Diagnóstico", "Costos y beneficios", "Supuestos", "Riesgos", "Confianza"),
        ),
        FormatoSalida(
            "plan-de-mercado",
            "Plan de mercado",
            ("Segmento", "Propuesta de valor", "Canales", "Métricas", "Riesgos"),
        ),
        FormatoSalida(
            "nota-critica",
            "Nota o preguntas críticas",
            ("Lo que se afirma", "Lo que falta verificar", "Preguntas críticas", "Fuentes"),
        ),
        FormatoSalida(
            "informe-con-fuentes",
            "Informe con fuentes",
            ("Pregunta", "Evidencia", "Calidad de la evidencia", "Conclusión", "Fuentes"),
        ),
        FormatoSalida(
            "objeciones-priorizadas",
            "Objeciones priorizadas",
            ("Objeciones", "Severidad", "Qué las resolvería"),
        ),
        FormatoSalida(
            "resumen-mesa",
            "Resumen de mesa y decisión de cierre",
            ("Resumen", "Acuerdos", "Desacuerdos", "Decisión"),
        ),
        FormatoSalida(
            "veredicto",
            "Veredicto",
            ("Acuerdos", "Desacuerdos", "Confianza", "Plan de acción"),
        ),
    )
}


def formato(id_formato: str) -> FormatoSalida | None:
    """Devuelve el formato con ese id, o ``None`` si no existe."""
    return FORMATOS.get(id_formato)


# --- Comprobar que un texto siga el formato (RF-07, CA-05) ------------------


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold()


# Lo que puede ir antes del nombre de una sección: "## ", "**", "- ", "1. ", "> ".
_PREFIJO_SECCION = re.compile(r"^[\s#>*_\-•·\d.)]*")


def _inicios_de_linea(contenido: str) -> list[str]:
    return [_PREFIJO_SECCION.sub("", _normalizar(linea)) for linea in contenido.splitlines()]


def secciones_faltantes(contenido: str, fmt: FormatoSalida) -> list[str]:
    """Secciones del formato que no aparecen como encabezado en ``contenido``.

    Una sección cuenta si alguna línea empieza con su nombre, con o sin
    Markdown delante y sin importar tildes ni mayúsculas: "## Riesgos",
    "**Riesgos:**", "- Riesgos —" y "riesgos:" valen igual.
    """
    lineas = _inicios_de_linea(contenido)
    return [s for s in fmt.secciones if not any(l.startswith(_normalizar(s)) for l in lineas)]
