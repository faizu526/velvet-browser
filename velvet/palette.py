"""
palette.py — Design tokens for Velvet Browser
Cream · Brown · Red-Pink premium theme + Incognito dark variant
"""
import platform

_SYS = platform.system()


class P:
    # ── Creamy base ───────────────────────────────
    BG         = "#F5EBD8"    # page background
    CARD       = "#FAF3E8"    # card / panel background
    INPUT      = "#FEFAF3"    # input field background
    RULE       = "#E8D5B8"    # subtle hairline / rule

    # ── Brown — borders · structure ───────────────
    B_DARK     = "#5C3D2E"    # heavy border / primary text
    B_MID      = "#7D5A47"    # secondary border
    B_LIGHT    = "#A6795C"    # tertiary / muted border
    B_ULTRA    = "#3B2218"    # logo / heading text

    # ── Red-Pink — glow · accent · premium ────────
    R_VIVID    = "#C0394B"    # primary accent
    R_DEEP     = "#8B1A2A"    # deep shadow / pressed
    PK_BRT     = "#E8607A"    # hover / bright
    PK_SOFT    = "#F0A0B0"    # rim glow
    PK_ULTRA   = "#FDD8DF"    # tint background

    # ── Text ──────────────────────────────────────
    T_HEAD     = "#2C1810"    # headings
    T_BODY     = "#4A3020"    # body
    T_MUTED    = "#8C6A50"    # placeholder / meta

    # ── Incognito dark variant ────────────────────
    INC_BG     = "#1E1E2E"
    INC_CARD   = "#2A2A3E"
    INC_TEXT   = "#E0D8F0"
    INC_ACC    = "#9F7AEA"


# Platform-safe font stack
FONT_HEAD = "Georgia"
FONT_BODY = "Segoe UI"   if _SYS == "Windows" else \
            "SF Pro Display" if _SYS == "Darwin" else "Ubuntu"
FONT_MONO = "Consolas"   if _SYS == "Windows" else \
            "Menlo"      if _SYS == "Darwin"  else "DejaVu Sans Mono"
