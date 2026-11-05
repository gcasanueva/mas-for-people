"""Ventana principal del visor. Comando: ``uv run mas-visor``.

Muestra el catálogo de agentes y las salas que guarda el servidor MCP en
``datos/mas.db``. No conversa ni escribe en la base: para eso está Claude
Desktop. Mientras está abierta, relee la base cada pocos segundos, así que
una sala en curso se ve avanzar sola (RF-18).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from mas.core import textos

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QTabWidget
except ImportError:  # pragma: no cover - depende de la instalación
    print(textos.VISOR_SIN_PYSIDE, file=sys.stderr)
    raise SystemExit(1) from None

from mas import __version__
from mas.core.catalogo import Catalogo
from mas.core.consulta import ConsultaSalas
from mas.core.raiz import ubicar_bd, ubicar_raiz

from .vistas.catalogo import VistaCatalogo
from .vistas.salas import VistaSalas

SEGUNDOS_REFRESCO = 3


class VentanaPrincipal(QMainWindow):
    def __init__(self, catalogo: Catalogo, consulta: ConsultaSalas, segundos: int = SEGUNDOS_REFRESCO) -> None:
        super().__init__()
        self.consulta = consulta
        self.setWindowTitle(f"{textos.VISOR_TITULO} {__version__}")
        self.resize(1200, 800)

        self.catalogo = VistaCatalogo(catalogo)
        self.salas = VistaSalas(consulta, segundos)
        self.pestanas = QTabWidget()
        self.pestanas.addTab(self.salas, textos.VISOR_PESTANA_SALAS)
        self.pestanas.addTab(self.catalogo, textos.VISOR_PESTANA_CATALOGO)
        self.setCentralWidget(self.pestanas)

        self.estado_bd = QLabel()
        self.hora = QLabel()
        self.statusBar().addWidget(self.estado_bd, 1)
        self.statusBar().addPermanentWidget(self.hora)
        self.salas.exportada.connect(
            lambda ruta: self.statusBar().showMessage(textos.VISOR_EXPORTADA.format(ruta=ruta), 8000)
        )

        # Solo lecturas cortas en modo lectura: no bloquean al servidor (RNF-10).
        self.reloj = QTimer(self)
        self.reloj.setInterval(segundos * 1000)
        self.reloj.timeout.connect(self.refrescar)
        self.reloj.start()
        self.refrescar()

    def refrescar(self) -> None:
        self.salas.actualizar()
        plantilla = textos.VISOR_ESTADO_BD if self.consulta.hay_base else textos.VISOR_ESTADO_SIN_BD
        self.estado_bd.setText(plantilla.format(ruta=self.consulta.ruta_bd))
        self.hora.setText(textos.VISOR_ACTUALIZADO.format(hora=datetime.now().strftime("%H:%M:%S")))


def crear_ventana(raiz: Path | None = None, ruta_bd: Path | None = None) -> VentanaPrincipal:
    """Arma la ventana con el catálogo y la base de datos del proyecto."""
    raiz = raiz or ubicar_raiz()
    catalogo = Catalogo(raiz)
    consulta = ConsultaSalas(ruta_bd or ubicar_bd(raiz), catalogo)
    return VentanaPrincipal(catalogo, consulta)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(textos.VISOR_TITULO)
    try:
        ventana = crear_ventana()
    except FileNotFoundError as e:
        QMessageBox.critical(None, textos.VISOR_SIN_RAIZ, str(e))
        return 1
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
