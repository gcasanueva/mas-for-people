"""Piezas compartidas por las pantallas."""

from __future__ import annotations

from PySide6.QtWidgets import QTextBrowser


class TextoMarkdown(QTextBrowser):
    """Muestra Markdown; al actualizar conserva la posición de lectura."""

    def __init__(self, texto: str = "") -> None:
        super().__init__()
        self.setOpenExternalLinks(True)
        self._actual: str | None = None
        if texto:
            self.mostrar(texto)

    def mostrar(self, markdown: str, al_final_si_crece: bool = False) -> None:
        if markdown == self._actual:
            return
        barra = self.verticalScrollBar()
        estaba_al_final = barra.value() >= barra.maximum() - 4
        posicion = barra.value()
        primera_vez = self._actual is None
        self._actual = markdown
        self.setMarkdown(markdown)
        if primera_vez:
            barra.setValue(0)
        elif al_final_si_crece and estaba_al_final:
            barra.setValue(barra.maximum())
        else:
            barra.setValue(posicion)

    def markdown_actual(self) -> str:
        return self._actual or ""
