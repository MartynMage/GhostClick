# GhostClick design system
# Warm dark palette with green accent — inspired by modern Reddit-style modals.

# ── backgrounds ──
BG_BASE = "#121317"           # deepest background (window)
BG_SURFACE = "#1c1e26"        # cards, panels, containers
BG_ELEVATED = "#272a35"       # raised elements, hover states
BG_INPUT = "#20232c"          # form input fields

# ── borders / dividers ──
BORDER = "#313545"
BORDER_FOCUS = "#4caf7d"

# ── accent palette ──
ACCENT = "#4caf7d"            # primary actions, links, highlights
ACCENT_HOVER = "#3d9b6b"
ACCENT_MUTED = "#1e3329"      # tinted backgrounds for selected states

# ── semantic colors ──
GREEN = "#4caf7d"             # play, success, confirm (same as accent)
GREEN_HOVER = "#3d9b6b"
RED = "#ef4444"               # stop, delete, destructive
RED_HOVER = "#dc2626"
AMBER = "#f59e0b"             # record, warning
AMBER_HOVER = "#d97706"
NEUTRAL = "#2e3242"           # secondary buttons (move, undo)
NEUTRAL_HOVER = "#3a3f54"

# ── text ──
TEXT = "#eaecf0"              # primary text
TEXT_SEC = "#a0a5b8"          # secondary / labels
TEXT_DIM = "#6c7190"          # placeholders, disabled

# ── list rows ──
ROW_BG = "#1c1e26"
ROW_BG_ALT = "#20232c"
ROW_SELECTED = "#1e3329"
ROW_ACTIVE = "#1a3d2e"
ROW_HOVER = "#272a35"

# ── corner radius ──
RADIUS_SM = 6                 # inputs, small elements
RADIUS_MD = 8                 # buttons, cards
RADIUS_LG = 12                # panels, containers

# ── font family ──
# Segoe UI Variable is the Windows 11 system font — it renders sharper than
# plain "Segoe UI" at small sizes because it's a variable-weight font with
# optical size axis. Falls back to Segoe UI on Win10.
FAMILY = "Segoe UI Variable"

FONT_SM = (FAMILY, 12)
FONT_MD = (FAMILY, 13)
FONT_LG = (FAMILY, 15)
FONT_SECTION = (FAMILY, 11, "bold")
FONT_HEADING = (FAMILY, 14, "bold")
