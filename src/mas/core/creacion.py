"""Crear y editar agentes desde la conversación (CU-02, RF-04).

``guardar_agente`` arma el ``agente.md`` con los campos que da el usuario,
lo valida igual que el catálogo (esquema, skills existentes, id único) y
solo entonces lo escribe. Con ``solo_validar`` devuelve el borrador sin
tocar el disco, para mostrárselo al usuario antes de confirmar.

Los agentes nuevos van a ``mis-agentes/<familia>/<id>/agente.md``: una
carpeta local, fuera de git, que no se comparte con nadie (decisión del
MVP; compartir agentes queda para una fase siguiente).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from . import textos
from .catalogo import NOMBRE_ARCHIVO_AGENTE, Catalogo
from .formatos import FORMATOS
from .modelos import Agente, ErrorValidacion, traducir_errores

# Ids que usan los agentes de sistema: un agente de usuario no puede tomarlos.
IDS_RESERVADOS = frozenset({"verificador", "moderador"})


def a_id(texto: str) -> str:
    """'Ingeniera de Datos' -> 'ingeniera-de-datos' (minúsculas, sin tildes, con guiones)."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    ascii_ = "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_).strip("-")


def guardar_agente(
    catalogo: Catalogo,
    nombre: str,
    especialidad: str,
    familia: str,
    postura: str,
    skills: list[str] | None,
    formato_salida: str,
    instrucciones: str,
    id: str | None = None,
    sensible: bool = False,
    aviso: str | None = None,
    reemplazar: bool = False,
    solo_validar: bool = False,
) -> dict[str, Any]:
    """Valida y guarda un agente. Devuelve ``{ok, id, ruta, agente_md}`` o ``{ok: False, errores}``."""
    catalogo.recargar()
    id_agente = (id or "").strip() or a_id(nombre or "")
    familia_id = a_id(familia or "")
    archivo = f"mis-agentes/{familia_id or '?'}/{id_agente or '?'}/{NOMBRE_ARCHIVO_AGENTE}"

    datos: dict[str, Any] = {
        "name": id_agente,
        "title": (nombre or "").strip() or None,
        "description": especialidad,
        "family": familia_id,
        "stance": postura,
        "skills": [s.strip() for s in (skills or []) if s and s.strip()],
        "output_contract": (formato_salida or "").strip(),
        "instructions": instrucciones or "",
    }
    if sensible:
        datos["sensitive"] = True
        datos["disclaimer"] = aviso
    try:
        agente = Agente.model_validate(datos)
    except ValidationError as exc:
        return _error(traducir_errores(exc, archivo), catalogo)

    errores: list[ErrorValidacion] = []
    existente = catalogo.agentes.get(agente.id)
    if agente.id in IDS_RESERVADOS:
        errores.append(ErrorValidacion(archivo=archivo, campo="name", mensaje=textos.CREAR_ID_RESERVADO.format(id=agente.id)))
    elif existente is not None and not reemplazar:
        errores.append(
            ErrorValidacion(
                archivo=archivo,
                campo="name",
                mensaje=textos.CREAR_YA_EXISTE.format(id=agente.id, ruta=catalogo._relativa(existente.ruta) if existente.ruta else "?"),
            )
        )
    errores += [
        e for e in catalogo.errores_de_referencias(agente, archivo) if e.campo != "name"  # el id ya se revisó arriba
    ]
    if errores:
        return _error(errores, catalogo)

    destino = _destino(catalogo, agente, existente)
    texto = agente.a_agente_md()
    relativa = catalogo._relativa(destino)
    resultado: dict[str, Any] = {
        "ok": True,
        "id": agente.id,
        "ruta": relativa,
        "agente_md": texto,
        "reemplaza": existente is not None,
    }
    if solo_validar:
        resultado["guardado"] = False
        resultado["indicacion"] = textos.CREAR_BORRADOR_OK
        return resultado

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    if existente is not None and existente.ruta and existente.ruta.resolve() != destino.resolve():
        _borrar_anterior(existente.ruta)
    catalogo.recargar()
    if agente.id not in catalogo.agentes:  # pragma: no cover - ya se validó todo antes
        return _error(catalogo.errores, catalogo)
    resultado["guardado"] = True
    resultado["indicacion"] = textos.CREAR_GUARDADO.format(nombre=agente.nombre, ruta=relativa)
    return resultado


def _destino(catalogo: Catalogo, agente: Agente, existente: Agente | None) -> Path:
    """Dónde va el archivo: junto al original si se edita; si no, en mis-agentes/."""
    base = catalogo.carpeta_propios
    if existente is not None and existente.ruta is not None and not catalogo.es_propio(existente):
        base = catalogo.carpeta_agentes  # se edita un agente base en su sitio
    return base / agente.familia / agente.id / NOMBRE_ARCHIVO_AGENTE


def _borrar_anterior(ruta: Path) -> None:
    """Al cambiar de familia, quita el archivo viejo (y su carpeta si quedó vacía)."""
    ruta.unlink(missing_ok=True)
    try:
        ruta.parent.rmdir()
    except OSError:
        pass


def _error(errores: list[ErrorValidacion], catalogo: Catalogo) -> dict[str, Any]:
    return {
        "ok": False,
        "errores": [str(e) for e in errores],
        "formatos_validos": sorted(FORMATOS),
        "skills_disponibles": sorted(catalogo.skills),
        "indicacion": textos.CREAR_CORREGIR,
    }


def opciones_creacion(catalogo: Catalogo) -> dict[str, Any]:
    """Lo que hace falta saber para proponer un agente: familias, formatos y skills."""
    catalogo.recargar()
    return {
        "familias": sorted(catalogo.familias()),
        "formatos": [
            {"id": f.id, "nombre": f.nombre, "secciones": list(f.secciones)}
            for f in FORMATOS.values()
            if f.id not in ("veredicto", "resumen-mesa")
        ],
        "skills": [{"id": s.id, "descripcion": s.descripcion} for s in sorted(catalogo.skills.values(), key=lambda s: s.id)],
    }
