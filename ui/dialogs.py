import customtkinter as ctk
from ui.theme import (
    BG_BASE, BG_SURFACE, BG_ELEVATED, BORDER,
    ACCENT, ACCENT_HOVER, RED, RED_HOVER, AMBER,
    NEUTRAL, NEUTRAL_HOVER,
    TEXT, TEXT_SEC, TEXT_DIM, FAMILY,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)


class _ThemedDialog(ctk.CTkToplevel):
    """Base class for themed modal dialogs."""

    def __init__(self, parent, title: str, message: str, icon_char: str,
                 icon_color: str, buttons: list[dict]):
        super().__init__(parent)

        self.title(title)
        self.configure(fg_color=BG_BASE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        # center on parent
        self.update_idletasks()
        w, h = 400, 200
        self.geometry(f"{w}x{h}")
        self._center_on_parent(parent, w, h)

        # outer padding frame
        outer = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        # icon + message area
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(20, 12))

        # icon circle
        icon_frame = ctk.CTkFrame(body, fg_color=icon_color, width=36, height=36,
                                  corner_radius=18)
        icon_frame.pack_propagate(False)
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.grid_columnconfigure(0, weight=1)
        icon_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            icon_frame, text=icon_char,
            font=ctk.CTkFont(family=FAMILY, size=16, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0)

        # text
        text_frame = ctk.CTkFrame(body, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            text_frame, text=title,
            font=ctk.CTkFont(family=FAMILY, size=14, weight="bold"),
            text_color=TEXT, anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            text_frame, text=message,
            font=ctk.CTkFont(family=FAMILY, size=12),
            text_color=TEXT_SEC, anchor="w", justify="left",
            wraplength=280,
        ).pack(fill="x", pady=(4, 0))

        # button row
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        # right-align buttons
        spacer = ctk.CTkFrame(btn_row, fg_color="transparent")
        spacer.pack(side="left", expand=True)

        for btn_def in buttons:
            btn = ctk.CTkButton(
                btn_row,
                text=btn_def["text"],
                width=btn_def.get("width", 80),
                height=34,
                fg_color=btn_def.get("fg", NEUTRAL),
                hover_color=btn_def.get("hover", NEUTRAL_HOVER),
                text_color=btn_def.get("text_color", TEXT_SEC),
                font=ctk.CTkFont(family=FAMILY, size=12,
                                 weight="bold" if btn_def.get("primary") else "normal"),
                corner_radius=RADIUS_MD,
                command=lambda v=btn_def.get("value"): self._on_button(v),
            )
            btn.pack(side="left", padx=(6, 0))

        # handle close via X button
        self.protocol("WM_DELETE_WINDOW", lambda: self._on_button(None))

        # focus and wait
        self.focus_force()
        self.wait_window()

    def _center_on_parent(self, parent, w, h):
        try:
            px = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
            py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
            self.geometry(f"{w}x{h}+{px}+{py}")
        except Exception:
            pass

    def _on_button(self, value):
        self.result = value
        self.grab_release()
        self.destroy()


def show_info(parent, title: str, message: str):
    """Themed info dialog with an OK button."""
    _ThemedDialog(
        parent, title, message,
        icon_char="i", icon_color=ACCENT,
        buttons=[
            {"text": "OK", "fg": ACCENT, "hover": ACCENT_HOVER,
             "text_color": "#0f1117", "primary": True, "value": True},
        ],
    )


def show_warning(parent, title: str, message: str):
    """Themed warning dialog with an OK button."""
    _ThemedDialog(
        parent, title, message,
        icon_char="!", icon_color=AMBER,
        buttons=[
            {"text": "OK", "fg": ACCENT, "hover": ACCENT_HOVER,
             "text_color": "#0f1117", "primary": True, "value": True},
        ],
    )


def show_error(parent, title: str, message: str):
    """Themed error dialog with an OK button."""
    _ThemedDialog(
        parent, title, message,
        icon_char="✕", icon_color=RED,
        buttons=[
            {"text": "OK", "fg": ACCENT, "hover": ACCENT_HOVER,
             "text_color": "#0f1117", "primary": True, "value": True},
        ],
    )


def ask_yes_no(parent, title: str, message: str) -> bool:
    """Themed yes/no dialog. Returns True for Yes, False for No or close."""
    dlg = _ThemedDialog(
        parent, title, message,
        icon_char="?", icon_color=ACCENT,
        buttons=[
            {"text": "No", "fg": NEUTRAL, "hover": NEUTRAL_HOVER,
             "text_color": TEXT_SEC, "value": False},
            {"text": "Yes", "fg": ACCENT, "hover": ACCENT_HOVER,
             "text_color": "#0f1117", "primary": True, "value": True, "width": 80},
        ],
    )
    return dlg.result is True
