"""Lo común a todos los protocolos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .. import textos
from ..modelos import Artefacto, EstadoSala, PosturaArtefacto, Protocolo, Sala, Turno


class TransicionInvalida(Exception):
    """Se intentó pasar a un estado que el protocolo no permite."""


@dataclass(frozen=True)
class PasoPlan:
    """Un turno previsto: quién habla y en qué ronda."""

    orden: int
    agente_id: str
    ronda: int

    def como_dict(self) -> dict[str, int | str]:
        return {"orden": self.orden, "agente": self.agente_id, "ronda": self.ronda}


class ProtocoloSala(ABC):
    """Máquina de estados de un protocolo."""

    protocolo: Protocolo
    # Estado actual -> estados a los que se puede pasar.
    transiciones: dict[EstadoSala, frozenset[EstadoSala]]

    @abstractmethod
    def plan(self, sala: Sala) -> list[PasoPlan]:
        """Orden de turnos previsto al abrir la sala."""

    @abstractmethod
    def siguiente(self, sala: Sala, turnos: list[Turno]) -> PasoPlan | None:
        """Siguiente turno a crear, o ``None`` si ya no quedan (toca veredicto).

        ``turnos`` son los ya creados (publicados o no), en orden.
        """

    @abstractmethod
    def ve_mesa(self, sala: Sala, ronda: int) -> bool:
        """Si el agente de esa ronda recibe el resumen de la mesa."""

    @abstractmethod
    def posturas_permitidas(self, ronda: int) -> frozenset[PosturaArtefacto]:
        """Posturas de artefacto válidas en esa ronda."""

    def cierre(self, sala: Sala, turnos: list[Turno]) -> str | None:
        """Por qué terminó la discusión (p. ej. ``consenso``), o ``None`` si sigue."""
        if turnos and all(t.artefacto is not None for t in turnos) and self.siguiente(sala, turnos) is None:
            return "limite"
        return None

    def errores_artefacto(self, ronda: int, artefacto: Artefacto) -> list[str]:
        """Reglas propias del protocolo sobre el artefacto de un turno."""
        return []

    def estado_de_ronda(self, ronda: int) -> EstadoSala:
        """Estado en que está la sala mientras se juega esa ronda."""
        return EstadoSala.PROPUESTAS

    def validar_transicion(self, desde: EstadoSala, hasta: EstadoSala) -> None:
        if desde == hasta:
            return
        if hasta not in self.transiciones.get(desde, frozenset()):
            raise TransicionInvalida(
                textos.TRANSICION_INVALIDA.format(desde=desde.value, hasta=hasta.value)
            )
