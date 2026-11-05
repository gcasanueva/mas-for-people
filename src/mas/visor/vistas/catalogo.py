"""Pantalla Catálogo: familias a la izquierda, ficha del agente a la derecha (RF-16)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mas.core import textos
from mas.core.catalogo import Catalogo
from mas.core.vistas import vista_agente

from .comun import TextoMarkdown

_ERRORES = "__errores__"


class VistaCatalogo(QWidget):
    def __init__(self, catalogo: Catalogo) -> None:
        super().__init__()
        self.catalogo = catalogo

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels([textos.VISOR_COL_AGENTE, textos.VISOR_COL_POSTURA])
        self.arbol.setColumnWidth(0, 220)
        self.arbol.currentItemChanged.connect(self._elegido)

        self.boton_recargar = QPushButton(textos.VISOR_RECARGAR)
        self.boton_recargar.setShortcut("F5")
        self.boton_recargar.clicked.connect(self.recargar)

        izquierda = QWidget()
        capa_izq = QVBoxLayout(izquierda)
        capa_izq.setContentsMargins(0, 0, 0, 0)
        capa_izq.addWidget(self.arbol)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(self.boton_recargar)
        capa_izq.addLayout(fila)

        self.ficha = TextoMarkdown(textos.VISOR_ELIGE_AGENTE)

        division = QSplitter(Qt.Orientation.Horizontal)
        division.addWidget(izquierda)
        division.addWidget(self.ficha)
        division.setStretchFactor(1, 1)
        division.setSizes([320, 700])

        capa = QVBoxLayout(self)
        capa.addWidget(division)
        self._llenar()

    def recargar(self) -> None:
        """Relee los archivos del catálogo (un agente.md editado a mano)."""
        actual = self.arbol.currentItem()
        elegido = actual.data(0, Qt.ItemDataRole.UserRole) if actual else None
        self.catalogo.recargar()
        self._llenar(elegido)

    def _llenar(self, elegido: str | None = None) -> None:
        self.arbol.clear()
        for familia, agentes in sorted(self.catalogo.familias().items()):
            nodo = QTreeWidgetItem([familia.replace("-", " ").capitalize()])
            nodo.setFlags(nodo.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.arbol.addTopLevelItem(nodo)
            for agente in agentes:
                hoja = QTreeWidgetItem([agente.nombre or agente.id, agente.postura])
                hoja.setData(0, Qt.ItemDataRole.UserRole, agente.id)
                hoja.setToolTip(0, agente.descripcion)
                nodo.addChild(hoja)
                if agente.id == elegido:
                    self.arbol.setCurrentItem(hoja)
            nodo.setExpanded(True)
        if self.catalogo.errores:
            nodo = QTreeWidgetItem([textos.VISOR_ERRORES_CATALOGO.format(n=len(self.catalogo.errores))])
            nodo.setData(0, Qt.ItemDataRole.UserRole, _ERRORES)
            self.arbol.addTopLevelItem(nodo)
        if elegido is None or self.arbol.currentItem() is None:
            self.ficha.mostrar(textos.VISOR_ELIGE_AGENTE)

    def _elegido(self, item: QTreeWidgetItem | None, _anterior: object = None) -> None:
        id_ = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if id_ == _ERRORES:
            lineas = [f"- {e}" for e in self.catalogo.errores]
            self.ficha.mostrar(textos.VISOR_ERRORES_TITULO + "\n\n" + "\n".join(lineas))
        elif id_ in self.catalogo.agentes:
            agente = self.catalogo.agentes[id_]
            self.ficha.mostrar(vista_agente(agente, self.catalogo.skills_de(agente)))
