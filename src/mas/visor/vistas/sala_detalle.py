"""Detalle de una sala: pestañas Mesa, Hilos (una columna por agente) y Veredicto (RF-17)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QTabWidget, QVBoxLayout, QWidget

from mas.core import textos
from mas.core.consulta import DetalleSala

from .comun import TextoMarkdown


class ColumnaHilo(TextoMarkdown):
    """Hilo de un agente: su nombre y sus turnos completos."""


class VistaDetalleSala(QWidget):
    def __init__(self, segundos_refresco: int) -> None:
        super().__init__()
        self.segundos = segundos_refresco
        self.detalle: DetalleSala | None = None
        self._firma: tuple | None = None

        self.aviso = QLabel(textos.VISOR_ELIGE_SALA)
        self.aviso.setWordWrap(True)

        self.mesa = TextoMarkdown()
        self.hilos = QSplitter(Qt.Orientation.Horizontal)
        self.hilos.setChildrenCollapsible(False)
        self.columnas: dict[str, ColumnaHilo] = {}
        self.veredicto = TextoMarkdown()

        self.pestanas = QTabWidget()
        self.pestanas.addTab(self.mesa, textos.VISOR_PESTANA_MESA)
        self.pestanas.addTab(self.hilos, textos.VISOR_PESTANA_HILOS)
        self.pestanas.addTab(self.veredicto, textos.VISOR_PESTANA_VEREDICTO)
        self.pestanas.setVisible(False)

        capa = QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.addWidget(self.aviso)
        capa.addWidget(self.pestanas, 1)

    def limpiar(self, mensaje: str = textos.VISOR_ELIGE_SALA) -> None:
        self.detalle, self._firma = None, None
        self.aviso.setText(mensaje)
        self.pestanas.setVisible(False)

    def mostrar(self, detalle: DetalleSala) -> None:
        """Muestra la sala; si es la misma y no cambió nada, no toca la pantalla."""
        misma = self.detalle is not None and self.detalle.sala.id == detalle.sala.id
        firma = detalle.firma()
        if misma and firma == self._firma:
            return
        if not misma:
            self._armar_columnas(detalle)
            self.pestanas.setCurrentIndex(2 if detalle.veredicto else 0)
        self.detalle, self._firma = detalle, firma

        if detalle.en_curso:
            self.aviso.setText(
                textos.VISOR_EN_CURSO.format(segundos=self.segundos, pendientes=detalle.pendientes)
            )
        else:
            self.aviso.setText(textos.VISOR_CERRADA)
        self.pestanas.setVisible(True)
        self.mesa.mostrar(detalle.mesa_md(), al_final_si_crece=True)
        for agente_id, columna in self.columnas.items():
            columna.mostrar(detalle.hilo_md(agente_id), al_final_si_crece=True)
        self.veredicto.mostrar(detalle.veredicto_md())

    def _armar_columnas(self, detalle: DetalleSala) -> None:
        for columna in self.columnas.values():
            columna.setParent(None)
            columna.deleteLater()
        self.columnas = {}
        for agente_id in detalle.sala.agentes:
            columna = ColumnaHilo()
            self.columnas[agente_id] = columna
            self.hilos.addWidget(columna)
        ancho = max(1, self.hilos.width() // max(1, len(self.columnas)))
        self.hilos.setSizes([ancho] * len(self.columnas))
