"""
heart.py — Heart rendering for Velvet Browser

  draw_heart()     — core parametric cardioid painter function
  PulsingHeart     — animated header logo widget
  GhostHeartBG     — breathing blurred ghost watermark behind desktop content
"""
import math

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath,
)
from PyQt5.QtWidgets import QWidget


# ─────────────────────────────────────────────────────────
# CORE DRAW FUNCTION
# Parametric cardioid:  x = 16 sin³t
#                       y = -(13cost − 5cos2t − 2cos3t − cos4t)
# ─────────────────────────────────────────────────────────
def draw_heart(
    painter: QPainter,
    cx: float,
    cy: float,
    s: float,
    alpha: int = 255,
    glow: bool = True,
    blur_mode: bool = False,
) -> None:
    """
    Draw a heart centered at (cx, cy) with scale s.

    Args:
        painter:    active QPainter (caller manages begin/end)
        cx, cy:     center coordinates
        s:          scale (approx. half-height in pixels)
        alpha:      0-255 opacity
        glow:       paint outer radial glow halo
        blur_mode:  flat single-colour fill (for ghost watermark layers)
    """
    p = painter
    p.setRenderHint(QPainter.Antialiasing)

    # Outer glow halo
    if glow and not blur_mode:
        halo = QRadialGradient(cx, cy + s * 0.15, s * 2.0)
        halo.setColorAt(0,   QColor(240, 140, 160, max(0, min(70, alpha // 2))))
        halo.setColorAt(0.5, QColor(220,  80, 100, max(0, min(30, alpha // 4))))
        halo.setColorAt(1.0, QColor(220,  80, 100, 0))
        p.setBrush(QBrush(halo))
        p.setPen(Qt.NoPen)
        p.drawEllipse(
            int(cx - s * 2.0), int(cy - s * 1.8),
            int(s * 4.0),      int(s * 4.0)
        )

    # Build parametric heart path
    path = QPainterPath()
    steps = 300
    pts = []
    for i in range(steps + 1):
        t  = (2 * math.pi * i / steps) - math.pi / 2
        hx = 16 * (math.sin(t) ** 3)
        hy = -(13 * math.cos(t)
               - 5 * math.cos(2 * t)
               - 2 * math.cos(3 * t)
               -     math.cos(4 * t))
        sc = s / 16.0
        pts.append((cx + hx * sc, cy + hy * sc * 0.96))

    path.moveTo(pts[0][0], pts[0][1])
    for px, py in pts[1:]:
        path.lineTo(px, py)
    path.closeSubpath()

    if blur_mode:
        # Ghost watermark — flat pink, no gradient
        p.setBrush(QBrush(QColor(232, 96, 122, max(0, min(255, alpha)))))
        p.setPen(Qt.NoPen)
        p.drawPath(path)
        return

    # Full gradient fill
    grad = QLinearGradient(cx - s, cy - s * 1.1, cx + s, cy + s * 1.1)
    a = max(0, min(255, alpha))
    grad.setColorAt(0.00, QColor(240, 100, 130, a))
    grad.setColorAt(0.25, QColor(220,  70, 100, a))
    grad.setColorAt(0.60, QColor(192,  57,  75, a))
    grad.setColorAt(0.85, QColor(139,  26,  42, a))
    grad.setColorAt(1.00, QColor( 80,  10,  20, a))
    p.setBrush(QBrush(grad))

    border = QPen(QColor(92, 61, 46, a))
    border.setWidthF(max(0.8, s / 22.0))
    p.setPen(border)
    p.drawPath(path)

    # Specular highlight — top-left inner shine
    shine = QPainterPath()
    shine.addEllipse(cx - s * 0.40, cy - s * 0.60, s * 0.40, s * 0.32)
    sg = QLinearGradient(cx - s * 0.40, cy - s * 0.60,
                         cx - s * 0.12, cy - s * 0.38)
    sg.setColorAt(0, QColor(255, 255, 255, min(90, a // 2 + 30)))
    sg.setColorAt(1, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(sg))
    p.setPen(Qt.NoPen)
    p.drawPath(shine)


# ─────────────────────────────────────────────────────────
# PULSING HEART — header logo widget
# Heartbeat animation: expand → slight dip → small bounce → settle
# ─────────────────────────────────────────────────────────
class PulsingHeart(QWidget):
    """Header heart that pulses like a real heartbeat (lub-dub rhythm)."""

    def __init__(self, base_size: int = 52, parent=None):
        super().__init__(parent)
        self._base  = base_size
        self._scale = 1.0
        self.setFixedSize(base_size + 28, base_size + 28)
        self.setAttribute(Qt.WA_TranslucentBackground)

        anim = QPropertyAnimation(self, b"heartScale")
        anim.setDuration(900)
        anim.setStartValue(1.0)
        anim.setKeyValueAt(0.30, 1.09)   # lub — first beat
        anim.setKeyValueAt(0.50, 0.97)   # dip
        anim.setKeyValueAt(0.68, 1.05)   # dub — second beat
        anim.setKeyValueAt(0.85, 0.99)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.InOutSine)
        anim.setLoopCount(-1)
        anim.start()
        self._anim = anim  # keep reference

    # pyqtProperty for QPropertyAnimation
    def _get_scale(self) -> float:
        return self._scale

    def _set_scale(self, v: float) -> None:
        self._scale = v
        self.update()

    heartScale = pyqtProperty(float, _get_scale, _set_scale)

    def paintEvent(self, event):
        p = QPainter(self)
        cx = self.width()  / 2
        cy = self.height() / 2
        s  = (self._base * 0.44) * self._scale
        draw_heart(p, cx, cy, s, alpha=255, glow=True)
        p.end()


# ─────────────────────────────────────────────────────────
# GHOST HEART BACKGROUND
# Sits behind all content. Multi-layer alpha pass = blur illusion.
# Breathing animation cycles opacity 22 ↔ 34 over ~4.2 s.
# ─────────────────────────────────────────────────────────
class GhostHeartBG(QWidget):
    """
    Full-size transparent background widget.

    Renders a large, softly glowing ghost heart in the center
    of the desktop content area using layered alpha passes to
    simulate a blur effect. A slow breathing QPropertyAnimation
    makes the opacity gently pulse.

    Always add this widget first and call .lower() so it stays
    behind all other content widgets.
    """

    _BASE_ALPHA = 28   # center opacity value
    _BREATH_AMP = 6    # ± around base

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._phase = 0.0

        breath = QPropertyAnimation(self, b"breathPhase")
        breath.setDuration(4200)
        breath.setStartValue(0.0)
        breath.setEndValue(1.0)
        breath.setLoopCount(-1)
        breath.start()
        self._breath = breath

    def _get_phase(self) -> float:
        return self._phase

    def _set_phase(self, v: float) -> None:
        self._phase = v
        self.update()

    breathPhase = pyqtProperty(float, _get_phase, _set_phase)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx   = w / 2
        cy   = h / 2 + 30   # pushed slightly below visual center

        # Breathing opacity
        alpha = int(self._BASE_ALPHA
                    + self._BREATH_AMP * math.sin(self._phase * 2 * math.pi))
        alpha = max(0, min(255, alpha))

        # Outer pink aura radial
        r = min(w, h) * 0.52
        aura = QRadialGradient(cx, cy, r)
        aura.setColorAt(0,   QColor(240, 150, 170, max(0, alpha - 4)))
        aura.setColorAt(0.4, QColor(230, 100, 130, max(0, alpha // 2)))
        aura.setColorAt(0.7, QColor(220,  80, 110, max(0, alpha // 4)))
        aura.setColorAt(1.0, QColor(220,  80, 110, 0))
        p.setBrush(QBrush(aura))
        p.setPen(Qt.NoPen)
        p.drawEllipse(
            int(cx - r), int(cy - r * 0.9),
            int(r * 2),  int(r * 1.8)
        )

        # Layered ghost heart passes: outermost blurriest, innermost sharpest
        s_base = min(w, h) * 0.28
        layers = [
            (s_base * 1.12, 6),
            (s_base * 1.06, 5),
            (s_base * 1.02, 4),
            (s_base,        3),
        ]
        for extra_s, a_div in layers:
            draw_heart(
                p, cx, cy, extra_s,
                alpha=max(0, alpha // a_div),
                glow=False, blur_mode=True,
            )

        p.end()
