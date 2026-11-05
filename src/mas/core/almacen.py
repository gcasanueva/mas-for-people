"""Guardado local de salas, turnos y veredictos en SQLite (RF-10).

Un solo archivo, sin instalar nada. Se abre en modo WAL para que el visor
pueda leer mientras el servidor escribe (RNF-10). Cada operación abre y
cierra su propia conexión: así el servidor no deja bloqueos colgados si
Claude Desktop lo detiene a mitad de una sala.

El resto del programa no escribe SQL: usa esta clase (RNF-11).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .modelos import Artefacto, EstadoSala, Protocolo, Sala, Turno, Veredicto

VERSION_ESQUEMA = 1

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS salas (
    id           TEXT PRIMARY KEY,
    objetivo     TEXT NOT NULL,
    agentes      TEXT NOT NULL,          -- lista JSON de ids, en orden
    posturas     TEXT NOT NULL,          -- objeto JSON id -> postura
    protocolo    TEXT NOT NULL,
    max_rondas   INTEGER NOT NULL,
    max_palabras INTEGER NOT NULL,
    estado       TEXT NOT NULL,
    creada       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS turnos (
    id         TEXT PRIMARY KEY,
    sala_id    TEXT NOT NULL REFERENCES salas(id) ON DELETE CASCADE,
    agente_id  TEXT NOT NULL,
    ronda      INTEGER NOT NULL,
    orden      INTEGER NOT NULL,         -- posición en el plan de la sala
    contenido  TEXT NOT NULL DEFAULT '',
    artefacto  TEXT,                     -- JSON; NULL mientras está pendiente
    palabras   INTEGER NOT NULL DEFAULT 0,
    fecha      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS turnos_sala ON turnos(sala_id, orden);
CREATE TABLE IF NOT EXISTS veredictos (
    sala_id     TEXT PRIMARY KEY REFERENCES salas(id) ON DELETE CASCADE,
    acuerdos    TEXT NOT NULL,
    desacuerdos TEXT NOT NULL,
    confianza   REAL NOT NULL,
    plan        TEXT NOT NULL,
    contenido   TEXT NOT NULL,
    fecha       TEXT NOT NULL
);
"""


def _json(valor: object) -> str:
    return json.dumps(valor, ensure_ascii=False)


class Almacen:
    """Base de datos SQLite de las salas."""

    def __init__(self, ruta: Path | str, solo_lectura: bool = False) -> None:
        self.ruta = Path(ruta)
        self.solo_lectura = solo_lectura
        if not solo_lectura:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with self._conectar() as con:
                con.execute("PRAGMA journal_mode=WAL")
                con.executescript(_ESQUEMA)
                con.execute(f"PRAGMA user_version={VERSION_ESQUEMA}")

    # Conexión ----------------------------------------------------------------

    @contextmanager
    def _conectar(self, inmediata: bool = False) -> Iterator[sqlite3.Connection]:
        if self.solo_lectura:
            con = sqlite3.connect(f"{self.ruta.resolve().as_uri()}?mode=ro", uri=True, timeout=10)
        else:
            con = sqlite3.connect(self.ruta, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            if inmediata:
                # Reserva la escritura desde el inicio: dos llamadas a la vez no
                # pueden crear el mismo turno dos veces.
                con.execute("BEGIN IMMEDIATE")
                try:
                    yield con
                    con.execute("COMMIT")
                except BaseException:
                    con.execute("ROLLBACK")
                    raise
            else:
                yield con
        finally:
            con.close()

    @contextmanager
    def transaccion(self) -> Iterator[sqlite3.Connection]:
        """Conexión con escritura reservada; todo o nada."""
        with self._conectar(inmediata=True) as con:
            yield con

    # Salas -------------------------------------------------------------------

    def crear_sala(self, sala: Sala) -> None:
        with self.transaccion() as con:
            con.execute(
                "INSERT INTO salas VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    sala.id,
                    sala.objetivo,
                    _json(sala.agentes),
                    _json(sala.posturas),
                    sala.protocolo.value,
                    sala.max_rondas,
                    sala.max_palabras,
                    sala.estado.value,
                    sala.creada.isoformat(),
                ),
            )

    @staticmethod
    def _sala(fila: sqlite3.Row) -> Sala:
        return Sala(
            id=fila["id"],
            objetivo=fila["objetivo"],
            agentes=json.loads(fila["agentes"]),
            posturas=json.loads(fila["posturas"]),
            protocolo=Protocolo(fila["protocolo"]),
            max_rondas=fila["max_rondas"],
            max_palabras=fila["max_palabras"],
            estado=EstadoSala(fila["estado"]),
            creada=datetime.fromisoformat(fila["creada"]),
        )

    def sala(self, sala_id: str, con: sqlite3.Connection | None = None) -> Sala | None:
        if con is None:
            with self._conectar() as con:
                return self.sala(sala_id, con)
        fila = con.execute("SELECT * FROM salas WHERE id=?", (sala_id,)).fetchone()
        return self._sala(fila) if fila else None

    def listar_salas(self, texto: str | None = None, limite: int = 50) -> list[Sala]:
        """Salas de la más nueva a la más antigua; ``texto`` filtra por objetivo."""
        consulta = "SELECT * FROM salas"
        parametros: list[object] = []
        if texto:
            consulta += " WHERE objetivo LIKE ?"
            parametros.append(f"%{texto}%")
        consulta += " ORDER BY creada DESC LIMIT ?"
        parametros.append(limite)
        with self._conectar() as con:
            return [self._sala(f) for f in con.execute(consulta, parametros)]

    def cambiar_estado(self, con: sqlite3.Connection, sala_id: str, estado: EstadoSala) -> None:
        con.execute("UPDATE salas SET estado=? WHERE id=?", (estado.value, sala_id))

    # Turnos ------------------------------------------------------------------

    @staticmethod
    def _turno(fila: sqlite3.Row) -> Turno:
        return Turno(
            id=fila["id"],
            sala_id=fila["sala_id"],
            agente_id=fila["agente_id"],
            ronda=fila["ronda"],
            contenido=fila["contenido"],
            artefacto=Artefacto.model_validate_json(fila["artefacto"]) if fila["artefacto"] else None,
            fecha=datetime.fromisoformat(fila["fecha"]),
        )

    def turnos(self, sala_id: str, con: sqlite3.Connection | None = None) -> list[Turno]:
        """Todos los turnos de una sala (publicados y pendientes) en orden de plan."""
        if con is None:
            with self._conectar() as con:
                return self.turnos(sala_id, con)
        filas = con.execute("SELECT * FROM turnos WHERE sala_id=? ORDER BY orden", (sala_id,))
        return [self._turno(f) for f in filas]

    def crear_turno(self, con: sqlite3.Connection, turno: Turno, orden: int) -> None:
        con.execute(
            "INSERT INTO turnos (id, sala_id, agente_id, ronda, orden, fecha) VALUES (?,?,?,?,?,?)",
            (turno.id, turno.sala_id, turno.agente_id, turno.ronda, orden, turno.fecha.isoformat()),
        )

    def publicar_turno(self, con: sqlite3.Connection, turno: Turno) -> None:
        assert turno.artefacto is not None
        con.execute(
            "UPDATE turnos SET contenido=?, artefacto=?, palabras=?, fecha=? WHERE id=?",
            (
                turno.contenido,
                turno.artefacto.model_dump_json(),
                turno.palabras,
                turno.fecha.isoformat(),
                turno.id,
            ),
        )

    # Veredictos --------------------------------------------------------------

    def guardar_veredicto(self, con: sqlite3.Connection, v: Veredicto) -> None:
        con.execute(
            "INSERT INTO veredictos VALUES (?,?,?,?,?,?,?)",
            (
                v.sala_id,
                _json(v.acuerdos),
                _json(v.desacuerdos),
                v.confianza,
                _json(v.plan),
                v.contenido,
                v.fecha.isoformat(),
            ),
        )

    def veredicto(self, sala_id: str, con: sqlite3.Connection | None = None) -> Veredicto | None:
        if con is None:
            with self._conectar() as con:
                return self.veredicto(sala_id, con)
        fila = con.execute("SELECT * FROM veredictos WHERE sala_id=?", (sala_id,)).fetchone()
        if not fila:
            return None
        return Veredicto(
            sala_id=fila["sala_id"],
            acuerdos=json.loads(fila["acuerdos"]),
            desacuerdos=json.loads(fila["desacuerdos"]),
            confianza=fila["confianza"],
            plan=json.loads(fila["plan"]),
            contenido=fila["contenido"],
            fecha=datetime.fromisoformat(fila["fecha"]),
        )
