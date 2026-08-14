"""
data.py — Persistence layer for Velvet Browser
  - load / save JSON data store
  - history, bookmarks, pinned sites, window geometry
  - Chromium discovery (Linux · Windows · macOS)
  - search URL routing
"""
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────
APP_DIR     = Path.home() / ".velvet_browser"
PROFILE_DIR = APP_DIR / "chrome_profile"
INC_DIR     = APP_DIR / "incognito_profile"
DATA_FILE   = APP_DIR / "data.json"

HISTORY_MAX = 500

_SYS = platform.system()
_IS_WIN = _SYS == "Windows"

# ── Search engines ────────────────────────────────────────
SEARCH_ENGINES: dict[str, str] = {
    "♥ Velvet (DuckDuckGo)": "https://duckduckgo.com/?q={}",
    "Google":                 "https://www.google.com/search?q={}",
    "Bing":                   "https://www.bing.com/search?q={}",
    "Brave Search":           "https://search.brave.com/search?q={}",
    "Ecosia":                 "https://www.ecosia.org/search?q={}",
    "Kagi":                   "https://kagi.com/search?q={}",
}

# ── Default pinned sites ──────────────────────────────────
DEFAULT_PINS: list[dict] = [
    {"label": "GitHub",    "url": "https://github.com"},
    {"label": "Mail",      "url": "https://mail.google.com"},
    {"label": "YouTube",   "url": "https://youtube.com"},
    {"label": "Wikipedia", "url": "https://wikipedia.org"},
]


def ensure_dirs() -> None:
    """Create all required app directories."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    INC_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> dict:
    """Load persisted data, migrating old schemas forward."""
    if DATA_FILE.exists():
        try:
            d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            # Forward migrations
            d.setdefault("pinned",        DEFAULT_PINS)
            d.setdefault("session_count", 0)
            d.setdefault("incognito",     False)
            d.setdefault("history",       [])
            d.setdefault("bookmarks",     [])
            d.setdefault("last_url",      "")
            d.setdefault("search_engine", "♥ Velvet (DuckDuckGo)")
            d.setdefault("window_geometry", None)
            return d
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "history": [], "bookmarks": [], "pinned": DEFAULT_PINS,
        "last_url": "", "search_engine": "♥ Velvet (DuckDuckGo)",
        "window_geometry": None, "session_count": 0, "incognito": False,
    }


def save_data(data: dict) -> None:
    """Atomically persist data to disk."""
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA_FILE)


def dir_size_mb(path: Path) -> float:
    """Return total size of a directory tree in MB."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total / (1024 * 1024)


# ── Chromium discovery ────────────────────────────────────
_WIN_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Chromium\Application\chromium.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
]

_UNIX_CHROME_NAMES = [
    "chromium-browser", "chromium", "google-chrome",
    "google-chrome-stable", "chromium-browser-stable",
    "/usr/bin/chromium-browser", "/usr/bin/chromium",
    "/usr/bin/google-chrome", "/snap/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


def find_chromium() -> str:
    """Return path to Chrome/Chromium binary, or empty string if not found."""
    candidates = (_WIN_CHROME_PATHS if _IS_WIN else []) + _UNIX_CHROME_NAMES
    for c in candidates:
        found = shutil.which(c) or (Path(c).exists() and str(c))
        if found:
            return str(found)
    return ""


def launch_chromium(url: str, chromium: str, incognito: bool = False) -> tuple[bool, str]:
    """
    Launch Chromium/Chrome with isolated profile.
    Returns (success, error_message).
    """
    if not chromium:
        chromium = find_chromium()
    if not chromium:
        return False, (
            "Chromium / Chrome not found.\n\n"
            "Install one of:\n"
            "  Linux:   sudo apt install chromium-browser\n"
            "  macOS:   brew install --cask chromium\n"
            "  Windows: https://www.google.com/chrome"
        )

    profile = INC_DIR if incognito else PROFILE_DIR
    flags = [
        chromium,
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--restore-last-session",
        "--disable-translate",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-features=TranslateUI",
    ]
    if incognito:
        flags.append("--incognito")
    flags.append(url)

    try:
        kwargs: dict = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if _IS_WIN:
            kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        subprocess.Popen(flags, **kwargs)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def build_search_url(query: str, engine: str) -> str:
    """
    Route query to search engine URL.
    If query looks like a URL, open it directly.
    """
    q = query.strip()
    if re.match(r"^(https?://|www\.)", q):
        return q if q.startswith("http") else "https://" + q
    template = SEARCH_ENGINES.get(engine, list(SEARCH_ENGINES.values())[0])
    return template.format(q.replace(" ", "+"))
