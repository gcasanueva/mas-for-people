"""Modelos de datos del núcleo.

Ocho entidades (ver la ERS, "Modelo de dominio"):

- ``Skill`` y ``Agente`` viven como archivos (``SKILL.md`` y ``agente.md``).
- ``Sala``, ``Hilo``, ``Turno``, ``Artefacto`` y ``Veredicto`` se guardarán en
  SQLite (paso 3).
- ``Mesa`` no es una tabla: es la vista de todos los artefactos de una sala.

Los atributos de Python están en español. En ``agente.md`` los campos van
en inglés (``name``, ``description``, ``stance``...) porque el formato es un
superconjunto del de subagentes de Claude Code; cada campo declara su alias.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from . import textos
from .formatos import FORMATOS

# --- Tipos comunes -----------------------------------------------------------

_PATRON_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PATRON_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def _validar_id(valor: str) -> str:
    if not _PATRON_ID.match(valor):
        raise ValueError(textos.ID_INVALIDO.format(valor=valor))
    return valor


def _lista_desde_texto(valor: Any) -> Any:
    """Acepta 'a, b' además de [a, b], como hace Claude Code con ``tools``."""
    if isinstance(valor, str):
        return [p.strip() for p in valor.split(",") if p.strip()]
    if valor is None:
        return []
    return valor


Id = Annotated[str, AfterValidator(_validar_id)]
"""Identificador en minúsculas con guiones, p. ej. ``ingeniero-industrial``."""

TextoCorto = Annotated[str, Field(min_length=1, max_length=120)]


def contar_palabras(texto: str) -> int:
    """Número aproximado de palabras de un texto (RF-14)."""
    return len(texto.split())


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _nuevo_id() -> str:
    return uuid.uuid4().hex[:12]


# --- Skill -------------------------------------------------------------------


class Skill(BaseModel):
    """Conocimiento reutilizable en formato estándar ``SKILL.md``.

    Solo exigimos ``name`` y ``description``; el resto de campos del estándar
    (``license``, ``allowed-tools``, ``metadata``...) se conservan tal cual.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, str_strip_whitespace=True)

    id: Id = Field(alias="name")
    descripcion: str = Field(alias="description", min_length=1, max_length=1024)
    instrucciones: str = Field(alias="instructions", min_length=1)
    ruta: Path | None = Field(default=None, exclude=True)


# --- Agente ------------------------------------------------------------------


class PreferenciaModelo(BaseModel):
    """Modelo preferido y alternativas (para diversidad en la app propia)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preferido: str | None = Field(default=None, alias="preferred")
    alternativas: list[str] = Field(default_factory=list, alias="alternatives")


class Limites(BaseModel):
    """Límites del agente dentro de una sala."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    max_turnos: int = Field(default=6, ge=1, le=20, alias="max_turns")
    max_palabras_turno: int = Field(default=400, ge=50, le=2000, alias="max_words_per_turn")


class Agente(BaseModel):
    """Un agente especializado: rol + criterios + skills + formato de salida.

    Se lee de un archivo ``agente.md``: encabezado YAML con los campos y,
    debajo, las instrucciones en Markdown.
    """

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, str_strip_whitespace=True
    )

    # Campos compartidos con los subagentes de Claude Code.
    id: Id = Field(alias="name")
    descripcion: str = Field(alias="description", min_length=1, max_length=400)
    herramientas: Annotated[list[str], BeforeValidator(_lista_desde_texto)] = Field(
        default_factory=list, alias="tools"
    )
    modelo: str | PreferenciaModelo | None = Field(default=None, alias="model")
    skills: Annotated[list[Id], BeforeValidator(_lista_desde_texto)] = Field(
        default_factory=list
    )

    # Campos propios de MAS for People.
    nombre: str | None = Field(default=None, alias="title", max_length=80)
    version: str = "0.1.0"
    familia: Id = Field(alias="family")
    postura: TextoCorto = Field(alias="stance")
    formato_salida: str = Field(alias="output_contract")
    limites: Limites = Field(default_factory=Limites, alias="limits")
    sensible: bool = Field(default=False, alias="sensitive")
    aviso: str | None = Field(default=None, alias="disclaimer", max_length=600)

    # Cuerpo del archivo y ubicación (no van en el encabezado).
    instrucciones: str = Field(alias="instructions", min_length=1)
    ruta: Path | None = Field(default=None, exclude=True)

    @field_validator("version")
    @classmethod
    def _version_valida(cls, valor: str) -> str:
        if not _PATRON_VERSION.match(valor):
            raise ValueError(textos.VERSION_INVALIDA.format(valor=valor))
        return valor

    @field_validator("formato_salida")
    @classmethod
    def _formato_existe(cls, valor: str) -> str:
        if valor not in FORMATOS:
            raise ValueError(
                textos.FORMATO_DESCONOCIDO.format(valor=valor, validos=", ".join(FORMATOS))
            )
        return valor

    @field_validator("skills")
    @classmethod
    def _skills_sin_repetir(cls, valor: list[str]) -> list[str]:
        vistos: set[str] = set()
        for s in valor:
            if s in vistos:
                raise ValueError(textos.SKILLS_REPETIDAS.format(valor=s))
            vistos.add(s)
        return valor

    @model_validator(mode="after")
    def _aviso_si_sensible(self) -> Agente:
        # RNF-09: los agentes de temas sensibles deben traer un aviso.
        if self.sensible and not (self.aviso and self.aviso.strip()):
            raise ValueError(textos.AVISO_OBLIGATORIO)
        if self.nombre is None:
            self.nombre = self.id.replace("-", " ").capitalize()
        return self

    def ficha(self) -> dict[str, str]:
        """Resumen corto para listados (salida de ``listar_agentes``)."""
        return {
            "id": self.id,
            "nombre": self.nombre or self.id,
            "familia": self.familia,
            "postura": self.postura,
            "descripcion": self.descripcion,
        }

    def a_agente_md(self) -> str:
        """Devuelve el contenido del archivo ``agente.md`` de este agente."""
        datos = self.model_dump(
            by_alias=True, exclude={"instrucciones", "ruta"}, exclude_none=True
        )
        if not self.sensible:
            datos.pop("sensitive", None)
        if not self.herramientas:
            datos.pop("tools", None)
        encabezado = yaml.safe_dump(
            datos, allow_unicode=True, sort_keys=False, default_flow_style=None
        )
        return f"---\n{encabezado}---\n\n{self.instrucciones.strip()}\n"


# --- Sala, hilo, turno, artefacto, mesa y veredicto --------------------------


class Protocolo(str, Enum):
    DEBATE = "debate"
    PANEL = "panel"


class EstadoSala(str, Enum):
    """Estados de la máquina de estados de una sala (ver ERS, protocolo)."""

    ABIERTA = "abierta"
    PROPUESTAS = "propuestas"
    CRITICA = "critica"  # solo en debate
    VERIFICACION = "verificacion"
    CERRADA = "cerrada"


class PosturaArtefacto(str, Enum):
    PROPUESTA = "propuesta"
    APOYO = "apoyo"
    OBJECION = "objecion"
    CORRECCION = "correccion"


class Artefacto(BaseModel):
    """Salida estructurada de un turno; se publica en la mesa."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    postura: PosturaArtefacto
    resumen: str = Field(min_length=1, max_length=600)
    supuestos: list[str] = Field(default_factory=list)
    riesgos: list[str] = Field(default_factory=list)
    responde_a: list[str] = Field(default_factory=list)
    confianza: float = Field(ge=0.0, le=1.0)
    cambiaria_de_opinion_si: str = ""


class Sala(BaseModel):
    """Una sala: objetivo + equipo + protocolo."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(default_factory=_nuevo_id)
    objetivo: str = Field(min_length=1, max_length=2000)
    agentes: list[Id] = Field(min_length=2, max_length=6)
    # Postura distinta a la por defecto para algún agente (id -> postura).
    posturas: dict[str, TextoCorto] = Field(default_factory=dict)
    protocolo: Protocolo = Protocolo.DEBATE
    max_rondas: int = Field(default=2, ge=1, le=4)
    max_palabras: int = Field(default=400, ge=50, le=2000)
    estado: EstadoSala = EstadoSala.ABIERTA
    creada: datetime = Field(default_factory=_ahora)

    @field_validator("agentes")
    @classmethod
    def _agentes_sin_repetir(cls, valor: list[str]) -> list[str]:
        vistos: set[str] = set()
        for a in valor:
            if a in vistos:
                raise ValueError(textos.AGENTES_REPETIDOS.format(valor=a))
            vistos.add(a)
        return valor


class Turno(BaseModel):
    """Una intervención de un agente en una sala."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_nuevo_id)
    sala_id: str
    agente_id: Id
    ronda: int = Field(ge=1)
    contenido: str = ""
    artefacto: Artefacto | None = None
    fecha: datetime = Field(default_factory=_ahora)

    @property
    def palabras(self) -> int:
        return contar_palabras(self.contenido)


class Hilo(BaseModel):
    """Lo que un agente ha dicho y recibido en una sala (uno por agente)."""

    sala_id: str
    agente_id: Id
    turnos: list[Turno] = Field(default_factory=list)


class EntradaMesa(BaseModel):
    turno_id: str
    agente_id: str
    ronda: int
    artefacto: Artefacto


class Mesa(BaseModel):
    """Vista de todos los artefactos publicados en una sala."""

    sala_id: str
    entradas: list[EntradaMesa] = Field(default_factory=list)

    @classmethod
    def desde_turnos(cls, sala_id: str, turnos: list[Turno]) -> Mesa:
        return cls(
            sala_id=sala_id,
            entradas=[
                EntradaMesa(
                    turno_id=t.id, agente_id=t.agente_id, ronda=t.ronda, artefacto=t.artefacto
                )
                for t in turnos
                if t.artefacto is not None
            ],
        )

    def resumen(self, excluir: str | None = None) -> list[dict[str, Any]]:
        """Resumen corto para un turno: postura, resumen y confianza de los demás.

        No incluye los textos completos para que el contexto sea pequeño (RNF-02).
        """
        return [
            {
                "turno_id": e.turno_id,
                "agente": e.agente_id,
                "ronda": e.ronda,
                "postura": e.artefacto.postura.value,
                "resumen": e.artefacto.resumen,
                "confianza": e.artefacto.confianza,
            }
            for e in self.entradas
            if e.agente_id != excluir
        ]


class Veredicto(BaseModel):
    """Cierre de una sala, escrito por el verificador."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    sala_id: str
    acuerdos: list[str] = Field(default_factory=list)
    desacuerdos: list[str] = Field(default_factory=list)
    confianza: float = Field(ge=0.0, le=1.0)
    plan: list[str] = Field(default_factory=list)
    contenido: str = ""
    fecha: datetime = Field(default_factory=_ahora)


# --- Errores de validación legibles -----------------------------------------


class ErrorValidacion(BaseModel):
    """Un problema concreto: en qué archivo, en qué campo y qué corregir."""

    archivo: str
    campo: str | None = None
    mensaje: str

    def __str__(self) -> str:
        if self.campo:
            return textos.LINEA_ERROR.format(
                archivo=self.archivo, campo=self.campo, mensaje=self.mensaje
            )
        return textos.LINEA_ERROR_SIN_CAMPO.format(archivo=self.archivo, mensaje=self.mensaje)


def traducir_errores(exc: ValidationError, archivo: str) -> list[ErrorValidacion]:
    """Convierte los errores de Pydantic en mensajes en español (RNF-07)."""
    errores: list[ErrorValidacion] = []
    for err in exc.errors(include_url=False):
        campo = ".".join(str(p) for p in err["loc"]) or None
        tipo = err["type"]
        if tipo == "value_error":
            # Nuestros propios validadores: el mensaje ya está en español.
            mensaje = str(err["ctx"]["error"]) if "ctx" in err else err["msg"]
        else:
            plantilla = textos.ERRORES_PYDANTIC.get(tipo, textos.ERROR_GENERICO)
            try:
                mensaje = plantilla.format(**err.get("ctx", {}))
            except (KeyError, IndexError):
                mensaje = plantilla
        if campo == "instructions":
            campo, mensaje = None, textos.CUERPO_VACIO
        errores.append(ErrorValidacion(archivo=archivo, campo=campo, mensaje=mensaje))
    return errores
