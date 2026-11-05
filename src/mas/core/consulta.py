"""Lectura de salas para el visor (CU-07, RNF-10, RNF-11).

Solo lee: abre la base de datos en modo lectura, así que nunca bloquea al
servidor MCP que escribe (SQLite en modo WAL deja leer mientras se escribe).
El visor usa esta clase y no escribe SQL propio.

No importa nada de Qt: se prueba sin ventana.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .almacen import Almacen
from .catalogo import Catalogo
from .modelos import EstadoSala, Sala, Turno, Veredicto
from .vistas import _seccion_hilos, vista_completa, vista_mesa, vista_veredicto


@dataclass
class DetalleSala:
    """Todo lo que el visor muestra de una sala."""

    sala: Sala
    turnos: list[Turno]  # solo los publicados, en orden
    pendientes: int  # turnos repartidos que aún no se publican
    veredicto: Veredicto | None
    nombres: dict[str, str] = field(default_factory=dict)

    @property
    def en_curso(self) -> bool:
        return self.sala.estado != EstadoSala.CERRADA

    def firma(self) -> tuple:
        """Cambia cuando hay algo nuevo que mostrar (para refrescar sin parpadeos)."""
        return (
            self.sala.estado,
            tuple(t.id for t in self.turnos),
            self.pendientes,
            self.veredicto.fecha if self.veredicto else None,
        )

    def mesa_md(self) -> str:
        return vista_mesa(self.sala, self.turnos, self.nombres)

    def hilo_md(self, agente_id: str) -> str:
        """Turnos completos de un agente, sin el encabezado de la sala."""
        return _seccion_hilos(self.turnos, self.nombres, [agente_id]).strip() + "\n"

    def veredicto_md(self) -> str:
        return vista_veredicto(self.sala, self.veredicto)

    def completo_md(self) -> str:
        return vista_completa(self.sala, self.turnos, self.nombres, self.veredicto)


class ConsultaSalas:
    """Lectura de salas guardadas, tolerante a que la base aún no exista."""

    def __init__(self, ruta_bd: Path | str, catalogo: Catalogo | None = None) -> None:
        self.ruta_bd = Path(ruta_bd)
        self.catalogo = catalogo
        self._almacen = Almacen(self.ruta_bd, solo_lectura=True)

    @property
    def hay_base(self) -> bool:
        return self.ruta_bd.is_file()

    def listar(self, texto: str | None = None, limite: int = 200) -> list[Sala]:
        """Salas de la más nueva a la más antigua; ``texto`` busca en el objetivo."""
        if not self.hay_base:
            return []
        try:
            return self._almacen.listar_salas(texto=(texto or "").strip() or None, limite=limite)
        except sqlite3.OperationalError:
            # Base recién creada por el servidor y aún sin tablas.
            return []

    def _nombres(self, sala: Sala) -> dict[str, str]:
        agentes = self.catalogo.agentes if self.catalogo else {}
        return {a: (agentes[a].nombre or a) if a in agentes else a for a in sala.agentes}

    def detalle(self, sala_id: str) -> DetalleSala | None:
        if not self.hay_base:
            return None
        try:
            sala = self._almacen.sala(sala_id)
            if sala is None:
                return None
            turnos = self._almacen.turnos(sala_id)
            veredicto = self._almacen.veredicto(sala_id)
        except sqlite3.OperationalError:
            return None
        publicados = [t for t in turnos if t.artefacto is not None]
        return DetalleSala(
            sala=sala,
            turnos=publicados,
            pendientes=len(turnos) - len(publicados),
            veredicto=veredicto,
            nombres=self._nombres(sala),
        )
