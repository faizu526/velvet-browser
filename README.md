<div align="center">

# ♥ Velvet Browser

**A premium personal Chromium launcher.**  
Persistent sessions · Ghost heart desktop · Incognito mode · One Python file per module.

![Python](https://img.shields.io/badge/Python-3.9%2B-brown?style=flat-square&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-C0394B?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Linux%20·%20Windows%20·%20macOS-E8607A?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-A6795C?style=flat-square)
![CI](https://img.shields.io/github/actions/workflow/status/faizu526/velvet-browser/ci.yml?style=flat-square&label=CI)

</div>

---

## What is Velvet?

Velvet is a **persistent-profile Chromium launcher** — a small PyQt5 app that opens Chrome/Chromium with your own isolated profile so logins, cookies, extensions, and sessions **survive every relaunch**. It's not a browser engine. It's your personal front door to Chromium.

---

## Features

| | Feature | Detail |
|---|---|---|
| ♥ | **Persistent sessions** | Isolated `~/.velvet_browser/chrome_profile` — logins never lost |
| 🕵 | **Incognito mode** | Separate profile, purple UI, `Ctrl+I` toggle |
| 💨 | **Ghost heart background** | Breathing blurred heart watermark in the content area |
| 💓 | **Animated logo** | Parametric cardioid heart with lub-dub heartbeat pulse |
| 🔍 | **6 search engines** | DuckDuckGo · Google · Bing · Brave · Ecosia · Kagi |
| 📌 | **Quick-pin strip** | One-click launch for your most-used sites |
| 📜 | **History + Bookmarks** | Deduped, timestamped, persisted to JSON |
| 💾 | **Storage indicator** | Live profile disk usage in MB |
| ⌨️ | **Keyboard shortcuts** | `Ctrl+L` focus · `Ctrl+B` bookmark · `Ctrl+I` incognito |
| 🪟 | **Window memory** | Position and size restored every launch |
| 🎨 | **Premium UI** | Cream · Brown borders · Red-pink shadow glows |

---

## Install

```bash
# Clone
git clone https://github.com/faizu526/velvet-browser.git
cd velvet-browser

# Linux (auto-detects apt / dnf / pacman)
bash scripts/install.sh

# macOS
brew install pyqt@5 && brew install --cask chromium

# Windows / pip fallback
pip install PyQt5

# Run
python main.py
```

---

## Project structure

```
velvet-browser/
│
├── main.py                  ← entry point (QApplication bootstrap)
│
├── velvet/                  ← core package
│   ├── __init__.py
│   ├── palette.py           ← design tokens (colors · fonts)
│   ├── data.py              ← persistence layer (JSON · Chromium launcher)
│   ├── heart.py             ← heart drawing (draw_heart · PulsingHeart · GhostHeartBG)
│   ├── widgets.py           ← reusable UI chips (URLPill · PinBtn)
│   └── window.py            ← main VelvetBrowser QWidget
│
├── tests/
│   └── test_data.py         ← pytest unit tests (data layer, no GUI needed)
│
├── scripts/
│   ├── install.sh           ← platform installer
│   └── velvet.desktop       ← Linux .desktop entry
│
├── assets/                  ← icons, screenshots (add your own)
│
├── .github/
│   └── workflows/ci.yml     ← GitHub Actions (multi-Python matrix)
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## How it works

The key flag passed to Chromium:

```
--user-data-dir=~/.velvet_browser/chrome_profile
```

This makes Chromium store its entire profile (cookies, localStorage, sessions, extensions, saved passwords) at that path. Every relaunch of Velvet picks up exactly where it left off.

```
~/.velvet_browser/
  chrome_profile/       ← normal session  (logins, history, extensions)
  incognito_profile/    ← incognito session (separate, no cross-contamination)
  data.json             ← velvet's own data (history pills, bookmarks, pins, geometry)
```

---

## Architecture

```
main.py
  └── VelvetBrowser (window.py)
        ├── GhostHeartBG (heart.py)    ← painted first, z-order lowest
        ├── PulsingHeart (heart.py)    ← header logo, QPropertyAnimation
        ├── URLPill × N (widgets.py)   ← history / bookmark chips
        ├── PinBtn × N  (widgets.py)   ← quick-pin strip
        └── data.py calls:
              find_chromium()           ← OS-aware Chrome detection
              launch_chromium()         ← Popen with --user-data-dir
              build_search_url()        ← URL vs search routing
              save_data() / load_data() ← atomic JSON persist
```

---

## Ghost heart — how the blur effect works

Qt's `QGraphicsBlurEffect` can't be applied to custom-painted widgets in all versions. Instead, Velvet renders **4 layered alpha passes** of the heart at slightly different scales:

```
Layer 1: scale ×1.12, alpha ÷ 6  ← outermost, most transparent
Layer 2: scale ×1.06, alpha ÷ 5
Layer 3: scale ×1.02, alpha ÷ 4
Layer 4: scale ×1.00, alpha ÷ 3  ← innermost, most opaque
```

The result is a soft-focus glow that reads as blurred without any filter API.  
A `QPropertyAnimation` on a custom `breathPhase` pyqtProperty cycles the opacity 22 ↔ 34 over 4.2 seconds.

---

## Customise

Edit `velvet/palette.py` to change any color:

```python
class P:
    BG      = "#F5EBD8"   # cream base
    R_VIVID = "#C0394B"   # primary accent
    B_DARK  = "#5C3D2E"   # border / structure
```

Add/change pinned sites in `velvet/data.py`:

```python
DEFAULT_PINS = [
    {"label": "Work",  "url": "https://yourcompany.com"},
    {"label": "Docs",  "url": "https://docs.python.org"},
]
```

Add a search engine:

```python
SEARCH_ENGINES["Perplexity"] = "https://www.perplexity.ai/search?q={}"
```

---

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests cover: URL routing, data persistence, schema migration, disk size, Chromium detection. No display or GUI required.

---

## Push to GitHub

```bash
git init
git add .
git commit -m "feat: Velvet Browser v2.0 — structured package"
git remote add origin https://github.com/faizu526/velvet-browser.git
git branch -M main
git push -u origin main

# Tag release
git tag -a v2.0 -m "v2.0"
git push origin v2.0
```

---

## License

MIT — use it, fork it, make it yours.

---

<div align="center">
Made with ♥ · Cream · Brown · Red-pink · Zero bloat
</div>
