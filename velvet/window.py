"""
window.py — VelvetBrowser main window

Assembles all UI sections:
  Header   (animated heart logo + chrome status + incognito toggle)
  PinStrip (quick-access sites + storage indicator)
  Search   (engine selector + URL bar + Open / Bookmark buttons)
  Panels   (History · Bookmarks side-by-side)
  StatusBar

All state lives in self.data (dict) persisted by data.py.
"""
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import (
    QColor, QFont, QIcon, QPainter, QBrush, QRadialGradient,
    QCursor, QPalette, QKeySequence, QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QMessageBox, QComboBox, QShortcut,
)

from .palette import P, FONT_HEAD as FH, FONT_BODY as FB, FONT_MONO as FM
from .heart   import draw_heart, PulsingHeart, GhostHeartBG
from .widgets import URLPill, PinBtn
from .data    import (
    APP_DIR, PROFILE_DIR, DATA_FILE,
    HISTORY_MAX, SEARCH_ENGINES, DEFAULT_PINS,
    ensure_dirs, load_data, save_data, dir_size_mb,
    find_chromium, launch_chromium, build_search_url,
)


class VelvetBrowser(QWidget):
    """Main launcher window for Velvet Browser."""

    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.data   = load_data()
        self.chrome = find_chromium()
        self._inc   = self.data.get("incognito", False)
        self._opened = 0   # URLs opened this session

        self._build_ui()
        self._apply_styles()
        self._restore_geometry()
        self._populate_history()
        self._populate_bookmarks()
        self._install_shortcuts()

    # ══════════════════════════════════════════════════════
    # STYLES
    # ══════════════════════════════════════════════════════
    def _apply_styles(self):
        inc = self._inc
        if inc:
            bg = P.INC_BG; body = P.INC_TEXT; base = P.INC_CARD
            cb_bg = "#3A2A5E"; cb_bd = P.INC_ACC
            cb_sel_bg = "#4A3A6E"; cb_sel_txt = P.INC_TEXT
        else:
            bg = P.BG; body = P.T_BODY; base = P.INPUT
            cb_bg = P.INPUT; cb_bd = P.B_MID
            cb_sel_bg = P.PK_ULTRA; cb_sel_txt = P.R_DEEP

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                color: {body};
                font-family: '{FB}';
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {P.RULE}; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {P.B_LIGHT}; border-radius: 2px; min-height: 16px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QComboBox {{
                background: {cb_bg}; border: 1.5px solid {cb_bd};
                border-radius: 10px; padding: 4px 12px;
                color: {body}; font-size: 10px; min-height: 26px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {cb_bg}; border: 1px solid {cb_bd};
                selection-background-color: {cb_sel_bg};
                selection-color: {cb_sel_txt};
            }}
            QToolTip {{
                background: {P.CARD}; border: 1px solid {P.B_LIGHT};
                color: {P.T_BODY}; padding: 4px 8px;
                border-radius: 6px; font-size: 10px;
            }}
        """)

    # ══════════════════════════════════════════════════════
    # BUILD UI
    # ══════════════════════════════════════════════════════
    def _build_ui(self):
        self.setWindowTitle("Velvet Browser  ♥")
        self.setMinimumSize(820, 660)
        self.resize(980, 740)
        self._make_icon()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Ghost heart — added first, pushed behind via .lower()
        self._ghost = GhostHeartBG(self)
        self._ghost.setGeometry(self.rect())
        self._ghost.lower()

        root.addWidget(self._build_header())
        root.addWidget(self._build_pin_strip())
        root.addWidget(self._build_search())
        root.addWidget(self._build_rule())

        content = QHBoxLayout()
        content.setContentsMargins(24, 16, 24, 16)
        content.setSpacing(20)
        content.addWidget(self._build_panel("History",   "history"),   1)
        content.addWidget(self._build_panel("Bookmarks", "bookmarks"), 1)
        root.addLayout(content, 1)

        root.addWidget(self._build_status_bar())

    def _make_icon(self):
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        draw_heart(p, 32, 32, 14, alpha=255, glow=False)
        p.end()
        self.setWindowIcon(QIcon(pix))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ghost.setGeometry(self.rect())

    # ── Gradient rule between search and panels ───────────
    def _build_rule(self) -> QFrame:
        r = QFrame()
        r.setFixedHeight(2)
        r.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.2 {P.B_LIGHT},
                stop:0.5 {P.PK_SOFT},
                stop:0.8 {P.B_LIGHT},
                stop:1   transparent);
        """)
        return r

    # ══════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════
    def _build_header(self) -> QFrame:
        inc = self._inc
        bg0 = P.INC_BG  if inc else P.CARD
        bg1 = "#2A2A3E" if inc else "#F8EDE0"
        bg2 = P.INC_BG  if inc else P.BG
        bd  = P.INC_ACC if inc else P.B_MID

        h = QFrame()
        h.setFixedHeight(90)
        h.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg0}, stop:0.6 {bg1}, stop:1 {bg2});
                border-bottom: 1.5px solid {bd};
            }}
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(28)
        sh.setOffset(0, 7)
        sh.setColor(QColor(192, 57, 75, 55))
        h.setGraphicsEffect(sh)

        lay = QHBoxLayout(h)
        lay.setContentsMargins(24, 10, 24, 10)
        lay.setSpacing(16)

        self.logo = PulsingHeart(50)
        lay.addWidget(self.logo)

        vb = QVBoxLayout(); vb.setSpacing(1)
        title_txt = "Velvet" + ("  🕵" if inc else "")
        t = QLabel(title_txt)
        t.setFont(QFont(FH, 24, QFont.Bold))
        t.setStyleSheet(
            f"color: {'#C5B0F0' if inc else P.B_ULTRA};"
            "background: transparent; border: none;"
        )
        vb.addWidget(t)
        sub_txt = "Incognito Session" if inc else "Private Browser  ·  Your data stays yours"
        s = QLabel(sub_txt)
        s.setFont(QFont(FB, 8))
        s.setStyleSheet(
            f"color: {'#9F7AEA' if inc else P.T_MUTED};"
            "background: transparent; border: none;"
        )
        vb.addWidget(s)
        lay.addLayout(vb)
        lay.addStretch()

        # Session badge
        self._session_badge = QLabel()
        self._refresh_session_badge()
        lay.addWidget(self._session_badge)

        # Chrome status
        self._chrome_pill = QLabel()
        self._refresh_chrome_pill()
        lay.addWidget(self._chrome_pill)

        # Incognito toggle
        self._inc_btn = self._pill_btn(
            "🕵 Incognito" if not inc else "🌞 Normal",
            tip="Toggle incognito (Ctrl+I)",
        )
        self._inc_btn.clicked.connect(self._toggle_incognito)
        lay.addWidget(self._inc_btn)

        # Close
        bx = self._icon_btn("✕", danger=True)
        bx.clicked.connect(self._quit)
        lay.addWidget(bx)

        return h

    def _refresh_session_badge(self):
        self._session_badge.setText(f"  {self._opened} opened  ")
        self._session_badge.setFont(QFont(FB, 8))
        self._session_badge.setStyleSheet(f"""
            color: {P.R_DEEP}; background: {P.PK_ULTRA};
            border: 1px solid {P.PK_SOFT}; border-radius: 10px;
            padding: 3px 8px;
        """)

    def _refresh_chrome_pill(self):
        from pathlib import Path
        if self.chrome:
            self._chrome_pill.setText(f"● {Path(self.chrome).stem}")
            self._chrome_pill.setStyleSheet("""
                color: #2E7D32; background: #E8F5E9;
                border: 1px solid #A5D6A7; border-radius: 10px;
                padding: 3px 10px; font-size: 10px;
            """)
        else:
            self._chrome_pill.setText("⚠ Chrome not found")
            self._chrome_pill.setStyleSheet(f"""
                color: {P.R_VIVID}; background: {P.PK_ULTRA};
                border: 1px solid {P.PK_SOFT}; border-radius: 10px;
                padding: 3px 10px; font-size: 10px;
            """)

    # ══════════════════════════════════════════════════════
    # PIN STRIP
    # ══════════════════════════════════════════════════════
    def _build_pin_strip(self) -> QFrame:
        f = QFrame()
        f.setFixedHeight(48)
        f.setStyleSheet(f"""
            QFrame {{
                background: {P.INPUT};
                border-bottom: 1px solid {P.RULE};
            }}
        """)
        lay = QHBoxLayout(f)
        lay.setContentsMargins(24, 6, 24, 6)
        lay.setSpacing(8)

        lbl = QLabel("Quick:")
        lbl.setFont(QFont(FB, 8))
        lbl.setStyleSheet(f"color: {P.T_MUTED}; background: transparent; border: none;")
        lay.addWidget(lbl)

        for pin in self.data.get("pinned", DEFAULT_PINS):
            btn = PinBtn(pin["label"], pin["url"])
            btn.triggered.connect(self._load_url)
            lay.addWidget(btn)

        lay.addStretch()

        sz = dir_size_mb(PROFILE_DIR)
        sz_lbl = QLabel(f"💾 {sz:.1f} MB")
        sz_lbl.setFont(QFont(FM, 8))
        sz_lbl.setToolTip(f"Profile: {PROFILE_DIR}")
        sz_lbl.setStyleSheet(f"color: {P.T_MUTED}; background: transparent; border: none;")
        lay.addWidget(sz_lbl)

        return f

    # ══════════════════════════════════════════════════════
    # SEARCH SECTION
    # ══════════════════════════════════════════════════════
    def _build_search(self) -> QFrame:
        inc = self._inc
        bg  = P.INC_CARD if inc else P.INPUT
        bd  = P.INC_BG   if inc else P.RULE

        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{ background: {bg}; border-bottom: 1px solid {bd}; }}
        """)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(36, 20, 36, 20)
        lay.setSpacing(12)

        # Engine selector row
        er = QHBoxLayout(); er.setSpacing(8)
        el = QLabel("Search via")
        el.setFont(QFont(FB, 9))
        el.setStyleSheet(f"color: {P.T_MUTED}; background: transparent; border: none;")
        er.addWidget(el)

        self.engine_sel = QComboBox()
        for name in SEARCH_ENGINES:
            self.engine_sel.addItem(name)
        idx = self.engine_sel.findText(
            self.data.get("search_engine", "♥ Velvet (DuckDuckGo)")
        )
        if idx >= 0:
            self.engine_sel.setCurrentIndex(idx)
        self.engine_sel.currentTextChanged.connect(self._on_engine_change)
        er.addWidget(self.engine_sel)
        er.addStretch()

        hint = QLabel("Ctrl+L  ·  Ctrl+B  ·  Ctrl+I")
        hint.setFont(QFont(FM, 7))
        hint.setStyleSheet(f"color: {P.T_MUTED}; background: transparent; border: none;")
        er.addWidget(hint)
        lay.addLayout(er)

        # URL bar row
        sr = QHBoxLayout(); sr.setSpacing(10)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search anything or paste a URL  ↩")
        self.url_bar.setFixedHeight(50)
        last = self.data.get("last_url", "")
        if last:
            self.url_bar.setText(last)
        self.url_bar.returnPressed.connect(self._on_launch)
        self.url_bar.setFont(QFont(FB, 12))

        bar_bd  = P.INC_ACC  if inc else P.B_MID
        bar_bg  = P.INC_CARD if inc else P.CARD
        bar_foc = P.INC_ACC  if inc else P.R_VIVID
        bar_txt = P.INC_TEXT if inc else P.T_HEAD

        self.url_bar.setStyleSheet(f"""
            QLineEdit {{
                background: {bar_bg}; border: 2px solid {bar_bd};
                border-radius: 25px; padding: 0 22px;
                color: {bar_txt};
                selection-background-color: {P.PK_ULTRA};
            }}
            QLineEdit:focus {{
                border: 2px solid {bar_foc};
                background: {P.INPUT};
            }}
            QLineEdit:hover {{ border-color: {P.B_DARK}; }}
        """)
        bar_sh = QGraphicsDropShadowEffect()
        bar_sh.setBlurRadius(22)
        bar_sh.setOffset(0, 5)
        bar_sh.setColor(QColor(192, 57, 75, 50))
        self.url_bar.setGraphicsEffect(bar_sh)
        sr.addWidget(self.url_bar, 1)

        self.btn_go = self._launch_btn()
        self.btn_go.clicked.connect(self._on_launch)
        sr.addWidget(self.btn_go)

        bm_btn = self._icon_btn("♥", tip="Bookmark (Ctrl+B)")
        bm_btn.clicked.connect(self._bookmark_current)
        sr.addWidget(bm_btn)

        lay.addLayout(sr)
        return f

    # ══════════════════════════════════════════════════════
    # PANELS — history / bookmarks
    # ══════════════════════════════════════════════════════
    def _build_panel(self, title: str, kind: str) -> QFrame:
        inc    = self._inc
        card_bg = P.INC_CARD if inc else P.CARD
        bd      = P.INC_ACC  if inc else P.B_LIGHT
        hd_col  = "#C5B0F0"  if inc else P.B_ULTRA

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {card_bg};
                border: 1.5px solid {bd};
                border-radius: 18px;
            }}
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(22)
        sh.setOffset(2, 7)
        sh.setColor(QColor(192, 57, 75, 40))
        card.setGraphicsEffect(sh)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(8)

        # Header row
        hrow = QHBoxLayout()
        ttl = QLabel(title)
        ttl.setFont(QFont(FH, 13, QFont.Bold))
        ttl.setStyleSheet(f"color: {hd_col}; background: transparent; border: none;")
        hrow.addWidget(ttl)
        hrow.addStretch()

        # Count badge
        cnt = len(self.data.get("history" if kind == "history" else "bookmarks", []))
        cnt_lbl = QLabel(str(cnt))
        cnt_lbl.setFont(QFont(FB, 8))
        cnt_lbl.setStyleSheet(f"""
            color: {P.R_DEEP}; background: {P.PK_ULTRA};
            border: 1px solid {P.PK_SOFT}; border-radius: 9px;
            padding: 1px 7px;
        """)
        hrow.addWidget(cnt_lbl)
        if kind == "history":
            self._hist_cnt = cnt_lbl
        else:
            self._bm_cnt = cnt_lbl

        clr = QPushButton("Clear")
        clr.setFixedHeight(22)
        clr.setCursor(QCursor(Qt.PointingHandCursor))
        clr.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {P.RULE};
                border-radius: 11px; color: {P.T_MUTED};
                font-size: 8px; padding: 0 9px;
            }}
            QPushButton:hover {{ border-color: {P.R_VIVID}; color: {P.R_VIVID}; }}
        """)
        clr.clicked.connect(
            self._clear_history if kind == "history" else self._clear_bookmarks
        )
        hrow.addWidget(clr)
        lay.addLayout(hrow)

        # Divider
        dv = QFrame(); dv.setFixedHeight(1)
        dv.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {P.B_LIGHT}, stop:0.6 {P.PK_SOFT}, stop:1 transparent);
        """)
        lay.addWidget(dv)

        # Scroll area
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sc.setStyleSheet("background: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(0, 4, 0, 4)
        fl.setSpacing(5)
        fl.setAlignment(Qt.AlignTop)

        if kind == "history":
            self._hist_lay = fl
        else:
            self._bm_lay = fl

        sc.setWidget(inner)
        lay.addWidget(sc)
        return card

    # ══════════════════════════════════════════════════════
    # STATUS BAR
    # ══════════════════════════════════════════════════════
    def _build_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {P.RULE}, stop:0.5 {P.CARD}, stop:1 {P.RULE});
                border-top: 1px solid {P.B_LIGHT};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(18, 0, 18, 0)

        self.status_lbl = QLabel(f"♥  {PROFILE_DIR}  ·  sessions auto-saved")
        self.status_lbl.setFont(QFont(FB, 7))
        self.status_lbl.setStyleSheet(
            f"color: {P.T_MUTED}; background: transparent; border: none;"
        )
        lay.addWidget(self.status_lbl)
        lay.addStretch()

        ver = QLabel("Velvet v2.0  ·  github.com/youruser/velvet-browser")
        ver.setFont(QFont(FB, 7))
        ver.setStyleSheet(f"color: {P.B_LIGHT}; background: transparent; border: none;")
        lay.addWidget(ver)
        return bar

    # ══════════════════════════════════════════════════════
    # POPULATE LISTS
    # ══════════════════════════════════════════════════════
    def _populate_history(self):
        self._clear_lay(self._hist_lay)
        items = self.data.get("history", [])[:60]
        for e in items:
            pill = URLPill(
                e["url"], e.get("title", ""),
                e.get("time", "")[:10], self._inc,
            )
            pill.clicked.connect(self._load_url)
            pill.removed.connect(self._remove_history)
            self._hist_lay.addWidget(pill)
        if not items:
            self._hist_lay.addWidget(self._empty("No history yet — go explore ♥"))
        self._hist_cnt.setText(str(len(items)))

    def _populate_bookmarks(self):
        self._clear_lay(self._bm_lay)
        items = self.data.get("bookmarks", [])
        for e in items:
            pill = URLPill(e["url"], e.get("title", ""), "", self._inc)
            pill.clicked.connect(self._load_url)
            pill.removed.connect(self._remove_bookmark)
            self._bm_lay.addWidget(pill)
        if not items:
            self._bm_lay.addWidget(self._empty("Press ♥ to save bookmarks"))
        self._bm_cnt.setText(str(len(items)))

    def _empty(self, txt: str) -> QLabel:
        l = QLabel(txt)
        l.setAlignment(Qt.AlignCenter)
        l.setStyleSheet(
            f"color: {P.T_MUTED}; font-size: 11px;"
            "background: transparent; border: none; padding: 24px;"
        )
        return l

    @staticmethod
    def _clear_lay(lay):
        while lay.count():
            it = lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    # ══════════════════════════════════════════════════════
    # KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════
    def _install_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self._focus_bar)
        QShortcut(QKeySequence("Ctrl+B"), self, self._bookmark_current)
        QShortcut(QKeySequence("Ctrl+I"), self, self._toggle_incognito)

    def _focus_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    # ══════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════
    def _on_engine_change(self, name: str):
        self.data["search_engine"] = name
        save_data(self.data)

    def _on_launch(self):
        raw = self.url_bar.text().strip()
        if not raw:
            return
        url = build_search_url(raw, self.engine_sel.currentText())

        ok, err = launch_chromium(url, self.chrome, self._inc)
        if not ok:
            self._show_error(err)
            return

        self._opened += 1
        self.data["session_count"] = self.data.get("session_count", 0) + 1
        self.data["last_url"] = url

        if not self._inc:
            hist = self.data.setdefault("history", [])
            hist = [h for h in hist if h["url"] != url]
            hist.insert(0, {
                "url":   url,
                "title": raw[:57] + "…" if len(raw) > 60 else raw,
                "time":  datetime.now().isoformat(timespec="seconds"),
            })
            self.data["history"] = hist[:HISTORY_MAX]

        save_data(self.data)
        self._refresh_session_badge()
        if not self._inc:
            self._populate_history()
        self._set_status(
            f"Opened: {url[:80]}…" if len(url) > 80 else f"Opened: {url}"
        )

    def _load_url(self, url: str):
        self.url_bar.setText(url)
        self._on_launch()

    def _bookmark_current(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        bms = self.data.setdefault("bookmarks", [])
        if any(b["url"] == url for b in bms):
            self._set_status("Already bookmarked.")
            return
        bms.append({
            "url":   url,
            "title": url,
            "time":  datetime.now().isoformat(timespec="seconds"),
        })
        save_data(self.data)
        self._populate_bookmarks()
        self._set_status("Bookmarked ♥")

    def _remove_history(self, url: str):
        self.data["history"] = [
            h for h in self.data.get("history", []) if h["url"] != url
        ]
        save_data(self.data)
        self._populate_history()

    def _remove_bookmark(self, url: str):
        self.data["bookmarks"] = [
            b for b in self.data.get("bookmarks", []) if b["url"] != url
        ]
        save_data(self.data)
        self._populate_bookmarks()

    def _clear_history(self):
        self.data["history"] = []
        save_data(self.data)
        self._populate_history()
        self._set_status("History cleared.")

    def _clear_bookmarks(self):
        self.data["bookmarks"] = []
        save_data(self.data)
        self._populate_bookmarks()
        self._set_status("Bookmarks cleared.")

    def _toggle_incognito(self):
        self._inc = not self._inc
        self.data["incognito"] = self._inc
        save_data(self.data)
        # Rebuild full UI with new colour scheme
        old = self.layout()
        QWidget().setLayout(old)
        self._build_ui()
        self._apply_styles()
        self._populate_history()
        self._populate_bookmarks()
        self._install_shortcuts()

    def _show_error(self, msg: str):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Velvet — Error")
        dlg.setText(msg)
        dlg.setIcon(QMessageBox.Warning)
        dlg.setStyleSheet(f"""
            QMessageBox {{ background: {P.CARD}; }}
            QLabel {{ color: {P.T_HEAD}; }}
            QPushButton {{
                background: {P.R_VIVID}; color: white;
                border-radius: 8px; padding: 6px 18px;
            }}
        """)
        dlg.exec_()

    def _set_status(self, msg: str):
        self.status_lbl.setText(msg)
        QTimer.singleShot(
            5000,
            lambda: self.status_lbl.setText(
                f"♥  {PROFILE_DIR}  ·  sessions auto-saved"
            ),
        )

    def _quit(self):
        self._save_geo()
        save_data(self.data)
        QApplication.quit()

    # ══════════════════════════════════════════════════════
    # GEOMETRY PERSISTENCE
    # ══════════════════════════════════════════════════════
    def _save_geo(self):
        g = self.geometry()
        self.data["window_geometry"] = [g.x(), g.y(), g.width(), g.height()]

    def _restore_geometry(self):
        g = self.data.get("window_geometry")
        if g and len(g) == 4:
            self.setGeometry(*g)

    def closeEvent(self, event):
        self._save_geo()
        save_data(self.data)
        event.accept()

    # ══════════════════════════════════════════════════════
    # BACKGROUND PAINT — cream vignette (ghost lives on top)
    # ══════════════════════════════════════════════════════
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        vgn = QRadialGradient(w / 2, h / 2, max(w, h) * 0.78)
        vgn.setColorAt(0,   QColor(255, 252, 246, 0))
        vgn.setColorAt(0.65, QColor(245, 228, 210, 0))
        vgn.setColorAt(1.0,  QColor(210, 178, 148, 25))
        p.fillRect(self.rect(), QBrush(vgn))
        p.end()

    # ══════════════════════════════════════════════════════
    # BUTTON FACTORY HELPERS
    # ══════════════════════════════════════════════════════
    def _launch_btn(self) -> QPushButton:
        btn = QPushButton("  Open  ")
        btn.setFixedHeight(50)
        btn.setMinimumWidth(110)
        btn.setFont(QFont(FB, 12, QFont.Medium))
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {P.PK_BRT}, stop:0.45 {P.R_VIVID}, stop:1 {P.R_DEEP});
                color: #FFF5F7;
                border: 1.5px solid {P.B_DARK};
                border-radius: 25px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F07090, stop:0.5 {P.PK_BRT}, stop:1 {P.R_VIVID});
            }}
            QPushButton:pressed {{
                background: {P.R_DEEP}; padding-top: 2px;
            }}
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(20)
        sh.setOffset(0, 6)
        sh.setColor(QColor(139, 26, 42, 100))
        btn.setGraphicsEffect(sh)
        return btn

    def _icon_btn(self, sym: str, tip: str = "", danger: bool = False) -> QPushButton:
        btn = QPushButton(sym)
        btn.setFixedSize(44, 44)
        if tip:
            btn.setToolTip(tip)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        hbg  = "#FDECEA" if danger else P.PK_ULTRA
        hcol = "#B71C1C" if danger else P.R_VIVID
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {P.CARD};
                border: 1.5px solid {P.B_LIGHT};
                border-radius: 22px;
                color: {P.B_MID};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {hbg}; border-color: {hcol}; color: {hcol};
            }}
            QPushButton:pressed {{ background: {P.BG}; }}
        """)
        return btn

    def _pill_btn(self, text: str, tip: str = "") -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(30)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        if tip:
            btn.setToolTip(tip)
        inc = self._inc
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {"#3A2A5E" if inc else P.CARD};
                border: 1.5px solid {"#9F7AEA" if inc else P.B_LIGHT};
                border-radius: 15px;
                color: {"#C5B0F0" if inc else P.T_BODY};
                font-size: 10px; padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {"#4A3A6E" if inc else P.PK_ULTRA};
                border-color: {P.PK_BRT};
            }}
        """)
        return btn
