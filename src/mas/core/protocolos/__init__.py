"""Protocolos de sala: cada uno es una máquina de estados (ver la ERS).

El gestor de salas pregunta al protocolo qué turno sigue, si el agente ve
la mesa y qué cambios de estado se permiten; el servidor nunca deja saltar
un estado.
"""

from __future__ import annotations

from ..modelos import Protocolo
from .base import PasoPlan, ProtocoloSala, TransicionInvalida
from .debate import Debate
from .panel import Panel

_PROTOCOLOS: dict[Protocolo, ProtocoloSala] = {Protocolo.DEBATE: Debate(), Protocolo.PANEL: Panel()}


def disponibles() -> list[Protocolo]:
    return list(_PROTOCOLOS)


def obtener(protocolo: Protocolo) -> ProtocoloSala | None:
    """El protocolo pedido, o ``None`` si todavía no está implementado."""
    return _PROTOCOLOS.get(protocolo)


__all__ = ["PasoPlan", "ProtocoloSala", "TransicionInvalida", "Debate", "Panel", "disponibles", "obtener"]
