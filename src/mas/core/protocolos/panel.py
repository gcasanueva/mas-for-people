"""Protocolo panel en paralelo (CU-04).

Una sola ronda: cada agente propone sin ver lo que dijeron los demás y
luego el verificador revisa todo contra el objetivo.

    abierta -> propuestas -> verificacion -> cerrada
"""

from __future__ import annotations

from ..modelos import EstadoSala, PosturaArtefacto, Protocolo, Sala, Turno
from .base import PasoPlan, ProtocoloSala

E = EstadoSala


class Panel(ProtocoloSala):
    protocolo = Protocolo.PANEL
    transiciones = {
        E.ABIERTA: frozenset({E.PROPUESTAS}),
        E.PROPUESTAS: frozenset({E.VERIFICACION}),
        E.VERIFICACION: frozenset({E.CERRADA}),
    }

    def plan(self, sala: Sala) -> list[PasoPlan]:
        return [PasoPlan(orden=i, agente_id=a, ronda=1) for i, a in enumerate(sala.agentes)]

    def siguiente(self, sala: Sala, turnos: list[Turno]) -> PasoPlan | None:
        plan = self.plan(sala)
        return plan[len(turnos)] if len(turnos) < len(plan) else None

    def ve_mesa(self, sala: Sala, ronda: int) -> bool:
        return False  # en el panel nadie ve las respuestas de los demás

    def posturas_permitidas(self, ronda: int) -> frozenset[PosturaArtefacto]:
        return frozenset({PosturaArtefacto.PROPUESTA})
