"""
widgets.py — Reusable UI components for Velvet Browser

  URLPill   — history / bookmark chip with click + remove signals
  PinBtn    — quick-access pinned site button
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QCursor
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect,
)

from .palette import P, FONT_BODY as FB


class URLPill(QFrame):
    """
    A pill-shaped chip displaying a URL / title.
    Emits clicked(url) on left-click and removed(url) on × press.
    Supports both normal and incognito colour schemes.
    """

    clicked = pyqtSignal(str)
    removed = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        label: str = "",
        timestamp: str = "",
        incognito: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.url = url

        disp = (label or url)
        if len(disp) > 50:
            disp = disp[:47] + "…"

        # Colour scheme
        if incognito:
            bg, bd, txt, hbg, hbd = (
                P.INC_CARD, P.INC_ACC, P.INC_TEXT, "#3A2A5E", P.INC_ACC
            )
        else:
            bg, bd, txt, hbg, hbd = (
                P.CARD, P.B_LIGHT, P.T_BODY, P.PK_ULTRA, P.R_VIVID
            )

        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {bd};
                border-radius: 18px;
            }}
            QFrame:hover {{
                background: {hbg};
                border-color: {hbd};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(192, 57, 75, 35))
        self.setGraphicsEffect(shadow)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 6, 0)
        lay.setSpacing(4)

        lbl = QLabel(disp)
        lbl.setFont(QFont(FB, 9))
        lbl.setStyleSheet(f"color:{txt};border:none;background:transparent;")
        lay.addWidget(lbl, 1)

        if timestamp:
            ts_lbl = QLabel(timestamp[:10])
            ts_lbl.setFont(QFont(FB, 7))
            ts_lbl.setStyleSheet(
                f"color:{P.T_MUTED};border:none;background:transparent;"
            )
            lay.addWidget(ts_lbl)

        btn_rm = QPushButton("×")
        btn_rm.setFixedSize(20, 20)
        btn_rm.setStyleSheet(f"""
            QPushButton {{
                color: {P.T_MUTED};
                background: transparent;
                border: none;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                color: {P.R_VIVID};
                background: {P.PK_ULTRA};
            }}
        """)
        btn_rm.clicked.connect(lambda: self.removed.emit(self.url))
        lay.addWidget(btn_rm)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.url)


class PinBtn(QFrame):
    """
    Quick-access pinned site button for the top strip.
    Emits triggered(url) on click.
    """

    triggered = pyqtSignal(str)

    def __init__(self, label: str, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFixedHeight(32)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(url)
        self.setStyleSheet(f"""
            QFrame {{
                background: {P.CARD};
                border: 1px solid {P.RULE};
                border-radius: 16px;
            }}
            QFrame:hover {{
                background: {P.PK_ULTRA};
                border-color: {P.PK_BRT};
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)

        lbl = QLabel(label)
        lbl.setFont(QFont(FB, 9))
        lbl.setStyleSheet(
            f"color:{P.T_BODY};border:none;background:transparent;"
        )
        lay.addWidget(lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.triggered.emit(self.url)
