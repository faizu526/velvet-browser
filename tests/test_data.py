"""
tests/test_data.py
Unit tests for velvet.data — no GUI, no Chromium needed.
Run:  python -m pytest tests/ -v
"""
import json
import sys
from pathlib import Path

import pytest

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from velvet.data import (
    build_search_url, load_data, save_data,
    find_chromium, dir_size_mb, SEARCH_ENGINES,
)


# ── build_search_url ─────────────────────────────────────
class TestBuildSearchUrl:
    def test_plain_query_routes_to_engine(self):
        url = build_search_url("hello world", "♥ Velvet (DuckDuckGo)")
        assert "duckduckgo.com" in url
        assert "hello+world" in url

    def test_google_engine(self):
        url = build_search_url("python docs", "Google")
        assert "google.com" in url
        assert "python+docs" in url

    def test_http_url_passthrough(self):
        assert build_search_url("https://github.com", "Google") == "https://github.com"

    def test_www_prefix_gets_https(self):
        assert build_search_url("www.youtube.com", "Google") == "https://www.youtube.com"

    def test_http_prefix_passthrough(self):
        assert build_search_url("http://localhost:8000", "Google") == "http://localhost:8000"

    def test_unknown_engine_falls_back(self):
        url = build_search_url("test", "Nonexistent Engine")
        # Falls back to first engine (DuckDuckGo)
        assert "duckduckgo.com" in url

    def test_spaces_encoded(self):
        url = build_search_url("open source software", "♥ Velvet (DuckDuckGo)")
        assert "open+source+software" in url

    def test_all_engines_have_placeholder(self):
        for name, tpl in SEARCH_ENGINES.items():
            assert "{}" in tpl, f"Engine '{name}' missing {{}} placeholder"


# ── load_data / save_data ────────────────────────────────
class TestPersistence:
    def test_load_data_returns_defaults_when_no_file(self, tmp_path, monkeypatch):
        import velvet.data as d
        monkeypatch.setattr(d, "DATA_FILE", tmp_path / "nonexistent.json")
        data = d.load_data()
        assert data["history"] == []
        assert data["bookmarks"] == []
        assert data["incognito"] is False

    def test_save_and_reload(self, tmp_path, monkeypatch):
        import velvet.data as d
        f = tmp_path / "data.json"
        monkeypatch.setattr(d, "DATA_FILE", f)

        payload = {
            "history": [{"url": "https://example.com", "title": "Example", "time": "2025-01-01"}],
            "bookmarks": [],
            "pinned": [],
            "last_url": "https://example.com",
            "search_engine": "Google",
            "window_geometry": [100, 100, 900, 700],
            "session_count": 3,
            "incognito": False,
        }
        d.save_data(payload)
        loaded = d.load_data()
        assert loaded["history"][0]["url"] == "https://example.com"
        assert loaded["session_count"] == 3

    def test_corrupt_json_returns_defaults(self, tmp_path, monkeypatch):
        import velvet.data as d
        f = tmp_path / "data.json"
        f.write_text("THIS IS NOT JSON", encoding="utf-8")
        monkeypatch.setattr(d, "DATA_FILE", f)
        data = d.load_data()
        assert isinstance(data, dict)
        assert "history" in data

    def test_schema_migration_adds_missing_keys(self, tmp_path, monkeypatch):
        import velvet.data as d
        f = tmp_path / "data.json"
        # Old schema without new keys
        f.write_text(json.dumps({"history": [], "bookmarks": []}), encoding="utf-8")
        monkeypatch.setattr(d, "DATA_FILE", f)
        data = d.load_data()
        assert "incognito" in data
        assert "session_count" in data
        assert "pinned" in data


# ── dir_size_mb ───────────────────────────────────────────
class TestDirSizeMb:
    def test_empty_dir_returns_zero(self, tmp_path):
        assert dir_size_mb(tmp_path) == 0.0

    def test_counts_file_sizes(self, tmp_path):
        (tmp_path / "a.bin").write_bytes(b"x" * 1024 * 1024)   # 1 MB
        sz = dir_size_mb(tmp_path)
        assert 0.9 < sz < 1.1

    def test_nonexistent_dir_returns_zero(self, tmp_path):
        assert dir_size_mb(tmp_path / "ghost") == 0.0


# ── find_chromium ─────────────────────────────────────────
class TestFindChromium:
    def test_returns_string(self):
        result = find_chromium()
        assert isinstance(result, str)

    def test_path_exists_if_found(self):
        result = find_chromium()
        if result:
            assert Path(result).exists()
