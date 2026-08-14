#!/usr/bin/env python3
"""
Velvet Browser — entry point
Run:  python main.py
"""
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from velvet.palette import P
from velvet.window  import VelvetBrowser


def _build_palette() -> QPalette:
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(P.BG))
    pal.setColor(QPalette.WindowText,      QColor(P.T_BODY))
    pal.setColor(QPalette.Base,            QColor(P.INPUT))
    pal.setColor(QPalette.AlternateBase,   QColor(P.CARD))
    pal.setColor(QPalette.Text,            QColor(P.T_HEAD))
    pal.setColor(QPalette.Button,          QColor(P.CARD))
    pal.setColor(QPalette.ButtonText,      QColor(P.T_BODY))
    pal.setColor(QPalette.Highlight,       QColor(P.PK_ULTRA))
    pal.setColor(QPalette.HighlightedText, QColor(P.R_DEEP))
    return pal


def main() -> None:
    # High-DPI — must be set before QApplication()
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    app.setApplicationName("Velvet Browser")
    app.setOrganizationName("Velvet")
    app.setApplicationVersion("2.0.0")
    app.setPalette(_build_palette())

    win = VelvetBrowser()
    win.show()
    win.url_bar.setFocus()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
