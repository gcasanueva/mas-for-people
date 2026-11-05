"""Pantalla Salas: buscador, tabla de salas y detalle de la elegida (RF-17 a RF-19)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mas.core import textos
from mas.core.consulta import ConsultaSalas
from mas.core.modelos import EstadoSala, Sala

from .sala_detalle import VistaDetalleSala


class VistaSalas(QWidget):
    exportada = Signal(str)

    def __init__(self, consulta: ConsultaSalas, segundos_refresco: int) -> None:
        super().__init__()
        self.consulta = consulta
        self.salas: list[Sala] = []

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText(textos.VISOR_BUSCAR)
        self.buscador.setClearButtonEnabled(True)
        self.buscador.textChanged.connect(lambda _t: self.actualizar())

        self.boton_exportar = QPushButton(textos.VISOR_EXPORTAR)
        self.boton_exportar.setEnabled(False)
        self.boton_exportar.clicked.connect(self.exportar)

        self.tabla = QTableWidget(0, len(textos.VISOR_COLUMNAS_SALAS))
        self.tabla.setHorizontalHeaderLabels(list(textos.VISOR_COLUMNAS_SALAS))
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setWordWrap(False)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.itemSelectionChanged.connect(self._elegida)

        self.vacio = QLabel()
        self.vacio.setWordWrap(True)
        self.vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.detalle = VistaDetalleSala(segundos_refresco)

        arriba = QWidget()
        capa_arriba = QVBoxLayout(arriba)
        capa_arriba.setContentsMargins(0, 0, 0, 0)
        fila = QHBoxLayout()
        fila.addWidget(self.buscador, 1)
        fila.addWidget(self.boton_exportar)
        capa_arriba.addLayout(fila)
        capa_arriba.addWidget(self.tabla)
        capa_arriba.addWidget(self.vacio)

        division = QSplitter(Qt.Orientation.Vertical)
        division.addWidget(arriba)
        division.addWidget(self.detalle)
        division.setStretchFactor(1, 1)
        division.setSizes([220, 500])

        capa = QVBoxLayout(self)
        capa.addWidget(division)
        self.actualizar()

    # Datos ---------------------------------------------------------------------

    def sala_elegida(self) -> str | None:
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return None
        return self.tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def actualizar(self) -> None:
        """Relee la lista y la sala elegida. Lo llama el reloj cada pocos segundos (RF-18)."""
        texto = self.buscador.text()
        salas = self.consulta.listar(texto)
        elegida = self.sala_elegida()
        if [(s.id, s.estado) for s in salas] != [(s.id, s.estado) for s in self.salas]:
            self._llenar_tabla(salas, elegida)
        else:
            self._actualizar_turnos(salas)
        self.salas = salas

        if not salas:
            self.vacio.setText(
                textos.VISOR_SIN_RESULTADOS.format(texto=texto.strip()) if texto.strip() else textos.VISOR_SIN_SALAS
            )
        self.vacio.setVisible(not salas)
        self.tabla.setVisible(bool(salas))
        self._mostrar_detalle()

    def _fila(self, sala: Sala) -> list[str]:
        return [
            sala.creada.astimezone().strftime("%Y-%m-%d %H:%M"),
            " ".join(sala.objetivo.split()),
            sala.protocolo.value,
            sala.estado.value,
            "",
        ]

    def _llenar_tabla(self, salas: list[Sala], elegida: str | None) -> None:
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(salas))
        for fila, sala in enumerate(salas):
            for col, valor in enumerate(self._fila(sala)):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, sala.id)
                if col == 1:
                    item.setToolTip(sala.objetivo)
                self.tabla.setItem(fila, col, item)
            if sala.id == elegida:
                self.tabla.selectRow(fila)
        self.tabla.blockSignals(False)
        self._actualizar_turnos(salas)

    def _actualizar_turnos(self, salas: list[Sala]) -> None:
        # La cuenta de turnos solo se pide para salas en curso (las cerradas no cambian).
        for fila, sala in enumerate(salas):
            item = self.tabla.item(fila, 4)
            if item is None or (item.text() and sala.estado == EstadoSala.CERRADA):
                continue
            detalle = self.consulta.detalle(sala.id)
            if detalle:
                item.setText(str(len(detalle.turnos)))

    def _elegida(self) -> None:
        self._mostrar_detalle()

    def _mostrar_detalle(self) -> None:
        sala_id = self.sala_elegida()
        if sala_id is None:
            self.detalle.limpiar()
            self.boton_exportar.setEnabled(False)
            return
        detalle = self.consulta.detalle(sala_id)
        if detalle is None:
            self.detalle.limpiar(textos.VISOR_SALA_DESAPARECIDA)
            self.boton_exportar.setEnabled(False)
            return
        self.detalle.mostrar(detalle)
        self.boton_exportar.setEnabled(True)

    # Exportar ------------------------------------------------------------------

    def exportar(self, ruta: str | Path | None = None) -> Path | None:
        """Guarda la sala elegida completa (mesa, hilos y veredicto) en Markdown (RF-19)."""
        detalle = self.detalle.detalle
        if detalle is None:
            return None
        if not ruta:
            sugerida = str(Path.home() / f"sala-{detalle.sala.id}.md")
            ruta, _filtro = QFileDialog.getSaveFileName(
                self, textos.VISOR_EXPORTAR_TITULO, sugerida, "Markdown (*.md)"
            )
            if not ruta:
                return None
        destino = Path(ruta)
        try:
            destino.write_text(detalle.completo_md(), encoding="utf-8")
        except OSError as e:
            QMessageBox.warning(self, textos.VISOR_EXPORTAR_TITULO, textos.VISOR_EXPORTAR_ERROR.format(detalle=e))
            return None
        self.exportada.emit(str(destino))
        return destino
