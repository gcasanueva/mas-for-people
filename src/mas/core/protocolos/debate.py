"""Protocolo debate por rondas (CU-03).

Ronda 1: cada agente propone sin ver a los demás (así nadie se ancla en la
primera idea). Rondas 2 en adelante: cada agente lee el resumen de la mesa y
apoya, objeta o corrige. El moderador (este protocolo) cierra el debate:

- por **consenso**, cuando en una ronda de crítica ningún artefacto trae
  postura ``objecion`` o ``correccion``;
- por **límite**, al terminar la ronda ``max_rondas``.

    abierta -> propuestas -> critica (rondas 2..max) -> verificacion -> cerrada

Con ``max_rondas = 1`` no hay crítica: pasa de propuestas a verificación,
igual que el panel.
"""

from __future__ import annotations

from .. import textos
from ..modelos import Artefacto, EstadoSala, PosturaArtefacto, Protocolo, Sala, Turno
from .base import PasoPlan, ProtocoloSala

E = EstadoSala
P = PosturaArtefacto

POSTURAS_CRITICA = frozenset({P.APOYO, P.OBJECION, P.CORRECCION})
POSTURAS_QUE_SIGUEN = frozenset({P.OBJECION, P.CORRECCION})

CONSENSO = "consenso"
LIMITE = "limite"


class Debate(ProtocoloSala):
    protocolo = Protocolo.DEBATE
    transiciones = {
        E.ABIERTA: frozenset({E.PROPUESTAS}),
        E.PROPUESTAS: frozenset({E.CRITICA, E.VERIFICACION}),
        E.CRITICA: frozenset({E.VERIFICACION}),
        E.VERIFICACION: frozenset({E.CERRADA}),
    }

    def plan(self, sala: Sala) -> list[PasoPlan]:
        """Plan máximo: todas las rondas. Puede acabar antes por consenso."""
        n = len(sala.agentes)
        return [
            PasoPlan(orden=r * n + i, agente_id=a, ronda=r + 1)
            for r in range(sala.max_rondas)
            for i, a in enumerate(sala.agentes)
        ]

    def siguiente(self, sala: Sala, turnos: list[Turno]) -> PasoPlan | None:
        if self.cierre(sala, turnos) is not None:
            return None
        plan = self.plan(sala)
        return plan[len(turnos)] if len(turnos) < len(plan) else None

    def cierre(self, sala: Sala, turnos: list[Turno]) -> str | None:
        """Motivo de cierre (``consenso`` o ``limite``) si el debate ya terminó.

        Solo mira rondas completas y publicadas; ``None`` si debe seguir.
        """
        n = len(sala.agentes)
        if not turnos or len(turnos) % n != 0 or any(t.artefacto is None for t in turnos):
            return None
        ronda = len(turnos) // n
        if ronda >= 2:
            de_la_ronda = [t for t in turnos if t.ronda == ronda]
            if not any(t.artefacto.postura in POSTURAS_QUE_SIGUEN for t in de_la_ronda if t.artefacto):
                return CONSENSO
        if ronda >= sala.max_rondas:
            return LIMITE
        return None

    def ve_mesa(self, sala: Sala, ronda: int) -> bool:
        return ronda >= 2

    def posturas_permitidas(self, ronda: int) -> frozenset[PosturaArtefacto]:
        return frozenset({P.PROPUESTA}) if ronda == 1 else POSTURAS_CRITICA

    def estado_de_ronda(self, ronda: int) -> EstadoSala:
        return E.PROPUESTAS if ronda == 1 else E.CRITICA

    def errores_artefacto(self, ronda: int, artefacto: Artefacto) -> list[str]:
        # Una objeción o corrección debe decir a qué turno responde.
        if ronda >= 2 and artefacto.postura in POSTURAS_QUE_SIGUEN and not artefacto.responde_a:
            return [textos.DEBATE_FALTA_RESPONDE_A.format(postura=artefacto.postura.value)]
        return []
