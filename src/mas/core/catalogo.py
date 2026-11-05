"""Catálogo de agentes y skills.

Lee ``agentes/**/agente.md`` y ``skills/*/SKILL.md`` (RF-01), valida cada
archivo (RF-02) y permite listar y buscar agentes (RF-03). Un archivo
inválido no se carga: queda en ``Catalogo.errores`` con el archivo, el campo
y qué corregir (RNF-07). ``recargar()`` vuelve a leer todo sin reiniciar el
programa (RF-04, CA-02).
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import frontmatter
import yaml
from pydantic import ValidationError

from . import textos
from .modelos import Agente, ErrorValidacion, Skill, traducir_errores

NOMBRE_ARCHIVO_AGENTE = "agente.md"
CARPETA_AGENTES = "agentes"
# Agentes creados por el usuario: solo en este equipo, fuera de git (no se
# comparten con nadie en el MVP).
CARPETA_PROPIOS = "mis-agentes"
NOMBRE_ARCHIVO_SKILL = "SKILL.md"


class NoEncontrado(LookupError):
    """Se pidió un agente o una skill que no está en el catálogo."""


# --- Lectura de archivos -----------------------------------------------------


def _separar(texto: str, archivo: str) -> tuple[dict[str, Any], str] | list[ErrorValidacion]:
    """Separa el encabezado YAML del cuerpo Markdown."""
    try:
        post = frontmatter.loads(texto)
    except yaml.YAMLError as exc:
        detalle = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
        return [ErrorValidacion(archivo=archivo, mensaje=textos.FRONTMATTER_INVALIDO.format(detalle=detalle))]
    if not isinstance(post.metadata, dict) or not post.metadata:
        return [ErrorValidacion(archivo=archivo, mensaje=textos.FRONTMATTER_VACIO)]
    return dict(post.metadata), post.content


def parsear_agente(
    texto: str, archivo: str, familia_carpeta: str | None = None
) -> Agente | list[ErrorValidacion]:
    """Valida el texto de un ``agente.md``.

    Devuelve el ``Agente`` o la lista de errores. Si el archivo está dentro de
    una carpeta de familia (``agentes/<familia>/...``) y no declara ``family``,
    se toma de la carpeta; si la declara, debe coincidir.
    """
    separado = _separar(texto, archivo)
    if isinstance(separado, list):
        return separado
    datos, cuerpo = separado

    if "instructions" in datos:
        return [ErrorValidacion(archivo=archivo, campo="instructions", mensaje=textos.CAMPO_DESCONOCIDO.format(validos=", ".join(_campos_agente())))]

    if familia_carpeta is not None:
        familia = datos.get("family")
        if familia is None:
            datos["family"] = familia_carpeta
        elif familia != familia_carpeta:
            return [
                ErrorValidacion(
                    archivo=archivo,
                    campo="family",
                    mensaje=textos.FAMILIA_NO_COINCIDE.format(familia=familia, carpeta=familia_carpeta),
                )
            ]

    datos["instructions"] = cuerpo
    try:
        return Agente.model_validate(datos)
    except ValidationError as exc:
        errores = traducir_errores(exc, archivo)
        for e in errores:
            if e.mensaje == textos.ERRORES_PYDANTIC["extra_forbidden"]:
                e.mensaje = textos.CAMPO_DESCONOCIDO.format(validos=", ".join(_campos_agente()))
        return errores


def parsear_skill(texto: str, archivo: str) -> Skill | list[ErrorValidacion]:
    """Valida el texto de un ``SKILL.md``."""
    separado = _separar(texto, archivo)
    if isinstance(separado, list):
        return separado
    datos, cuerpo = separado
    datos["instructions"] = cuerpo
    try:
        return Skill.model_validate(datos)
    except ValidationError as exc:
        errores = traducir_errores(exc, archivo)
        for e in errores:
            if e.mensaje == textos.CUERPO_VACIO:
                e.mensaje = textos.SKILL_CUERPO_VACIO
        return errores


def _campos_agente() -> list[str]:
    return [
        f.alias or nombre
        for nombre, f in Agente.model_fields.items()
        if nombre not in ("instrucciones", "ruta")
    ]


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para buscar 'ingenieria' o 'Ingeniería' igual."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold()


# --- Catálogo ----------------------------------------------------------------


class Catalogo:
    """Agentes y skills de una carpeta raíz con ``agentes/`` y ``skills/``."""

    def __init__(self, raiz: Path | str) -> None:
        self.raiz = Path(raiz)
        self.carpeta_agentes = self.raiz / CARPETA_AGENTES
        self.carpeta_propios = self.raiz / CARPETA_PROPIOS
        self.carpeta_skills = self.raiz / "skills"
        self.agentes: dict[str, Agente] = {}
        self.skills: dict[str, Skill] = {}
        self.errores: list[ErrorValidacion] = []
        self.recargar()

    # Carga -------------------------------------------------------------------

    def recargar(self) -> list[ErrorValidacion]:
        """Vuelve a leer todos los archivos. Devuelve los errores encontrados."""
        self.agentes, self.skills, self.errores = {}, {}, []
        self._cargar_skills()
        self._cargar_agentes()
        return self.errores

    def _relativa(self, ruta: Path) -> str:
        try:
            return ruta.relative_to(self.raiz).as_posix()
        except ValueError:
            return ruta.as_posix()

    def _leer(self, ruta: Path) -> str | None:
        try:
            return ruta.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            self.errores.append(
                ErrorValidacion(archivo=self._relativa(ruta), mensaje=textos.ARCHIVO_ILEGIBLE.format(detalle=exc))
            )
            return None

    def _cargar_skills(self) -> None:
        if not self.carpeta_skills.is_dir():
            return
        for ruta in sorted(self.carpeta_skills.glob(f"*/{NOMBRE_ARCHIVO_SKILL}")):
            archivo = self._relativa(ruta)
            texto = self._leer(ruta)
            if texto is None:
                continue
            resultado = parsear_skill(texto, archivo)
            if isinstance(resultado, list):
                self.errores.extend(resultado)
                continue
            carpeta = ruta.parent.name
            if resultado.id != carpeta:
                self.errores.append(
                    ErrorValidacion(
                        archivo=archivo,
                        campo="name",
                        mensaje=textos.NOMBRE_NO_COINCIDE_CARPETA.format(nombre=resultado.id, carpeta=carpeta),
                    )
                )
                continue
            resultado.ruta = ruta
            self.skills[resultado.id] = resultado

    def _cargar_agentes(self) -> None:
        if not self.carpeta_agentes.is_dir():
            self.errores.append(
                ErrorValidacion(
                    archivo=self._relativa(self.carpeta_agentes),
                    mensaje=textos.CATALOGO_SIN_CARPETA.format(ruta=self.carpeta_agentes),
                )
            )
            return
        rutas = [(self.carpeta_agentes, r) for r in sorted(self.carpeta_agentes.rglob(NOMBRE_ARCHIVO_AGENTE))]
        if self.carpeta_propios.is_dir():
            rutas += [(self.carpeta_propios, r) for r in sorted(self.carpeta_propios.rglob(NOMBRE_ARCHIVO_AGENTE))]
        for base, ruta in rutas:
            archivo = self._relativa(ruta)
            texto = self._leer(ruta)
            if texto is None:
                continue
            partes = ruta.relative_to(base).parts
            familia_carpeta = partes[0] if len(partes) > 1 else None
            resultado = parsear_agente(texto, archivo, familia_carpeta)
            if isinstance(resultado, list):
                self.errores.extend(resultado)
                continue
            errores = self.errores_de_referencias(resultado, archivo)
            if errores:
                self.errores.extend(errores)
                continue
            resultado.ruta = ruta
            self.agentes[resultado.id] = resultado

    def errores_de_referencias(self, agente: Agente, archivo: str) -> list[ErrorValidacion]:
        """Skills inexistentes e id repetido (lo que el modelo solo no puede ver)."""
        errores = [
            ErrorValidacion(
                archivo=archivo,
                campo=f"skills.{i}",
                mensaje=textos.SKILL_INEXISTENTE.format(valor=s),
            )
            for i, s in enumerate(agente.skills)
            if s not in self.skills
        ]
        if agente.id in self.agentes:
            otro = self.agentes[agente.id].ruta
            errores.append(
                ErrorValidacion(
                    archivo=archivo,
                    campo="name",
                    mensaje=textos.ID_DUPLICADO.format(
                        id=agente.id, otra_ruta=self._relativa(otro) if otro else "?"
                    ),
                )
            )
        return errores

    # Consultas ---------------------------------------------------------------

    def es_propio(self, agente: Agente | str) -> bool:
        """Si el agente lo creó el usuario (vive en ``mis-agentes/``)."""
        if isinstance(agente, str):
            agente = self.agente(agente)
        return agente.ruta is not None and agente.ruta.is_relative_to(self.carpeta_propios)

    def ficha(self, agente: Agente) -> dict[str, Any]:
        """Ficha corta con la marca de agente propio."""
        return {**agente.ficha(), "propio": self.es_propio(agente)}

    def listar(self, familia: str | None = None, texto: str | None = None) -> list[Agente]:
        """Agentes ordenados por familia y nombre, filtrando por familia o texto (RF-03)."""
        resultado = list(self.agentes.values())
        if familia:
            buscada = _normalizar(familia)
            resultado = [a for a in resultado if _normalizar(a.familia) == buscada]
        if texto:
            palabras = _normalizar(texto).split()
            resultado = [
                a
                for a in resultado
                if all(p in self._texto_buscable(a) for p in palabras)
            ]
        return sorted(resultado, key=lambda a: (a.familia, a.nombre or a.id))

    @staticmethod
    def _texto_buscable(agente: Agente) -> str:
        return _normalizar(
            " ".join(
                [
                    agente.id,
                    agente.nombre or "",
                    agente.familia,
                    agente.postura,
                    agente.descripcion,
                    " ".join(agente.skills),
                ]
            )
        )

    def familias(self) -> dict[str, list[Agente]]:
        """Agentes agrupados por familia (para el visor y el CU-01)."""
        grupos: dict[str, list[Agente]] = {}
        for agente in self.listar():
            grupos.setdefault(agente.familia, []).append(agente)
        return grupos

    def agente(self, id_agente: str) -> Agente:
        try:
            return self.agentes[id_agente]
        except KeyError:
            raise NoEncontrado(textos.AGENTE_NO_ENCONTRADO.format(id=id_agente)) from None

    def skill(self, id_skill: str) -> Skill:
        try:
            return self.skills[id_skill]
        except KeyError:
            raise NoEncontrado(textos.SKILL_NO_ENCONTRADA.format(id=id_skill)) from None

    def skills_de(self, agente: Agente | str) -> list[Skill]:
        """Skills que usa un agente, en el orden en que las declara."""
        if isinstance(agente, str):
            agente = self.agente(agente)
        return [self.skills[s] for s in agente.skills if s in self.skills]
