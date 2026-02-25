import customtkinter as ctk
import keyboard
import pyautogui
from ui.theme import (
    BG_BASE, BG_SURFACE, BG_INPUT, BG_ELEVATED, BORDER, ACCENT, ACCENT_HOVER,
    NEUTRAL, NEUTRAL_HOVER, AMBER,
    TEXT, TEXT_SEC, TEXT_DIM, FAMILY,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)


class _SectionLabel(ctk.CTkLabel):
    """Uppercase section header used to group related controls."""
    def __init__(self, master, text, **kw):
        super().__init__(
            master, text=text.upper(),
            font=ctk.CTkFont(family=FAMILY, size=11, weight="bold"),
            text_color=TEXT_SEC,
            **kw,
        )


class _HotkeyPicker(ctk.CTkFrame):
    """Shows the current key and a Change button. Captures the next keypress on click."""

    def __init__(self, master, label: str, hint: str, default: str,
                 on_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._var = ctk.StringVar(value=default)
        self._on_change = on_change
        self._listening = False
        self._hook = None

        ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
        ).grid(row=0, column=0, sticky="w")

        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._key_label = ctk.CTkLabel(
            row_frame, text=default, width=60, height=30,
            fg_color=BG_INPUT, corner_radius=RADIUS_SM,
            font=ctk.CTkFont(family=FAMILY, size=12, weight="bold"),
            text_color=TEXT,
        )
        self._key_label.pack(side="left", padx=(0, 6))

        self._change_btn = ctk.CTkButton(
            row_frame, text="Change", width=64, height=28,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=11),
            corner_radius=RADIUS_SM,
            command=self._start_listening,
        )
        self._change_btn.pack(side="left")

        ctk.CTkLabel(
            self, text=hint,
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM,
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

    @property
    def value(self) -> str:
        return self._var.get().strip() or "F6"

    def _start_listening(self):
        if self._listening:
            return
        self._listening = True
        self._key_label.configure(text="...", fg_color=AMBER, text_color="#1a1a1a")
        self._change_btn.configure(text="Press key", state="disabled")
        self._hook = keyboard.on_press(self._on_key_press, suppress=False)

    def _on_key_press(self, event):
        key_name = event.name
        if not key_name:
            return
        self.after(0, lambda: self._finish_listening(key_name))

    def _finish_listening(self, key_name: str):
        if not self._listening:
            return
        self._listening = False

        if self._hook is not None:
            try:
                keyboard.unhook(self._hook)
            except Exception:
                pass
            self._hook = None

        self._var.set(key_name)
        self._key_label.configure(text=key_name, fg_color=BG_INPUT, text_color=TEXT)
        self._change_btn.configure(text="Change", state="normal")

        if self._on_change:
            self._on_change()


class _HotkeyDialog(ctk.CTkToplevel):
    """Modal dialog for configuring all hotkeys."""

    def __init__(self, parent, current_values: dict, on_save):
        super().__init__(parent)
        self.title("Hotkeys")
        self.configure(fg_color=BG_BASE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._on_save = on_save

        w, h = 340, 430
        self.geometry(f"{w}x{h}")
        try:
            px = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
            py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
            self.geometry(f"{w}x{h}+{px}+{py}")
        except Exception:
            pass

        outer = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            outer, text="Hotkeys",
            font=ctk.CTkFont(family=FAMILY, size=15, weight="bold"),
            text_color=TEXT,
        ).pack(padx=20, pady=(16, 4), anchor="w")

        ctk.CTkLabel(
            outer, text="Click Change, then press a key to rebind",
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM,
        ).pack(padx=20, pady=(0, 14), anchor="w")

        # create fresh pickers inside this dialog
        self._capture = _HotkeyPicker(
            outer, label="Capture Position", hint="Fills X / Y from cursor",
            default=current_values.get("capture", "F6"),
        )
        self._capture.pack(fill="x", padx=20, pady=(0, 10))

        self._quick_add = _HotkeyPicker(
            outer, label="Quick-Add Step", hint="Adds step at cursor position",
            default=current_values.get("quick_add", "F7"),
        )
        self._quick_add.pack(fill="x", padx=20, pady=(0, 10))

        self._play_stop = _HotkeyPicker(
            outer, label="Start / Stop Playback", hint="Toggles script playback",
            default=current_values.get("play_stop", "F8"),
        )
        self._play_stop.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkButton(
            outer, text="Done", width=80, height=32,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#0f1117",
            font=ctk.CTkFont(family=FAMILY, size=12, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._close,
        ).pack(pady=(0, 16))

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.focus_force()
        self.wait_window()

    def _close(self):
        result = {
            "capture": self._capture.value,
            "quick_add": self._quick_add.value,
            "play_stop": self._play_stop.value,
        }
        self.grab_release()
        self.destroy()
        if self._on_save:
            self._on_save(result)


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BG_SURFACE, corner_radius=RADIUS_LG, **kwargs)

        self.on_hotkey_change = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # scrollable inner container
        inner = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_DIM,
        )
        inner.grid(row=0, column=0, sticky="nsew")
        inner.grid_columnconfigure(0, weight=1)
        inner._parent_canvas.bind("<Configure>", lambda e: self.after_idle(self._auto_scrollbar))

        self._inner = inner
        row = 0

        # ── panel title ──
        title = ctk.CTkLabel(
            inner, text="Settings",
            font=ctk.CTkFont(family=FAMILY, size=16, weight="bold"),
            text_color=TEXT,
        )
        title.grid(row=row, column=0, padx=16, pady=(12, 4), sticky="w")
        row += 1

        ctk.CTkFrame(inner, fg_color=BORDER, height=1).grid(
            row=row, column=0, padx=16, pady=(0, 8), sticky="ew"
        )
        row += 1

        # ── playback section ──
        _SectionLabel(inner, text="Playback").grid(
            row=row, column=0, padx=16, pady=(0, 5), sticky="w"
        )
        row += 1

        ctk.CTkLabel(
            inner, text="Repeat Count",
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
        ).grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        row += 1

        self.repeat_var = ctk.StringVar(value="1")
        self.repeat_entry = ctk.CTkEntry(
            inner, textvariable=self.repeat_var, width=76, height=32,
            placeholder_text="1",
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_SM,
        )
        self.repeat_entry.grid(row=row, column=0, padx=16, pady=(0, 3), sticky="w")
        row += 1

        ctk.CTkLabel(
            inner, text="0 = run forever",
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM,
        ).grid(row=row, column=0, padx=16, pady=(0, 8), sticky="w")
        row += 1

        # repeat delay
        ctk.CTkLabel(
            inner, text="Repeat Delay (s)",
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
        ).grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        row += 1

        self.repeat_delay_var = ctk.StringVar(value="0")
        self.repeat_delay_entry = ctk.CTkEntry(
            inner, textvariable=self.repeat_delay_var, width=76, height=32,
            placeholder_text="0",
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_SM,
        )
        self.repeat_delay_entry.grid(row=row, column=0, padx=16, pady=(0, 3), sticky="w")
        row += 1

        ctk.CTkLabel(
            inner, text="Pause between loops",
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM,
        ).grid(row=row, column=0, padx=16, pady=(0, 8), sticky="w")
        row += 1

        # speed multiplier
        self._speed_val = ctk.DoubleVar(value=1.0)
        self.speed_label = ctk.CTkLabel(
            inner, text="Speed  1.00x",
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
        )
        self.speed_label.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="w")
        row += 1

        self.speed_slider = ctk.CTkSlider(
            inner,
            from_=0.25, to=4.0,
            number_of_steps=15,
            variable=self._speed_val,
            command=self._on_speed_change,
            button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT,
            fg_color=BORDER,
            height=14,
        )
        self.speed_slider.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="ew")
        row += 1

        speed_range = ctk.CTkFrame(inner, fg_color="transparent")
        speed_range.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="ew")
        speed_range.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            speed_range, text="0.25x",
            font=ctk.CTkFont(family=FAMILY, size=10), text_color=TEXT_DIM,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            speed_range, text="4.0x",
            font=ctk.CTkFont(family=FAMILY, size=10), text_color=TEXT_DIM,
        ).grid(row=0, column=2, sticky="e")
        row += 1

        # divider
        ctk.CTkFrame(inner, fg_color=BORDER, height=1).grid(
            row=row, column=0, padx=16, pady=(0, 8), sticky="ew"
        )
        row += 1

        # ── options section ──
        _SectionLabel(inner, text="Options").grid(
            row=row, column=0, padx=16, pady=(0, 5), sticky="w"
        )
        row += 1

        self.record_moves_var = ctk.BooleanVar(value=False)
        self.record_moves_check = ctk.CTkCheckBox(
            inner, text="Record mouse movements",
            variable=self.record_moves_var,
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
            fg_color=ACCENT, hover_color=ACCENT,
            border_color=BORDER, border_width=2,
            checkbox_height=18, checkbox_width=18,
        )
        self.record_moves_check.grid(row=row, column=0, padx=16, pady=(0, 6), sticky="w")
        row += 1

        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_check = ctk.CTkCheckBox(
            inner, text="Dry run (preview only)",
            variable=self.dry_run_var,
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
            fg_color=ACCENT, hover_color=ACCENT,
            border_color=BORDER, border_width=2,
            checkbox_height=18, checkbox_width=18,
        )
        self.dry_run_check.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="w")
        row += 1

        # divider
        ctk.CTkFrame(inner, fg_color=BORDER, height=1).grid(
            row=row, column=0, padx=16, pady=(0, 8), sticky="ew"
        )
        row += 1

        # ── hotkeys — compact button to open dialog ──
        hk_row = ctk.CTkFrame(inner, fg_color="transparent")
        hk_row.grid(row=row, column=0, padx=16, pady=(0, 3), sticky="ew")

        ctk.CTkLabel(
            hk_row, text="HOTKEYS",
            font=ctk.CTkFont(family=FAMILY, size=11, weight="bold"),
            text_color=TEXT_SEC,
        ).pack(side="left")

        # show current keys as a summary
        self._hotkey_summary = ctk.CTkLabel(
            hk_row,
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM, text="",
        )
        self._hotkey_summary.pack(side="left", padx=(8, 0))

        row += 1

        self.hotkey_btn = ctk.CTkButton(
            inner, text="Configure Hotkeys", width=180, height=30,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=11),
            corner_radius=RADIUS_SM,
            command=self._open_hotkey_dialog,
        )
        self.hotkey_btn.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="w")
        row += 1

        # divider
        ctk.CTkFrame(inner, fg_color=BORDER, height=1).grid(
            row=row, column=0, padx=16, pady=(0, 8), sticky="ew"
        )
        row += 1

        # ── system section ──
        self.assoc_btn = ctk.CTkButton(
            inner, text="Set as default for .ghostclick",
            width=190, height=30,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=11),
            corner_radius=RADIUS_SM,
        )
        self.assoc_btn.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="w")
        row += 1

        # divider
        ctk.CTkFrame(inner, fg_color=BORDER, height=1).grid(
            row=row, column=0, padx=16, pady=(0, 8), sticky="ew"
        )
        row += 1

        # ── cursor position ──
        _SectionLabel(inner, text="Cursor").grid(
            row=row, column=0, padx=16, pady=(0, 4), sticky="w"
        )
        row += 1

        self._cursor_label = ctk.CTkLabel(
            inner, text="X: \u2014   Y: \u2014",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            text_color=TEXT,
        )
        self._cursor_label.grid(row=row, column=0, padx=16, pady=(0, 10), sticky="w")
        row += 1

        self._poll_cursor()

        # hotkey values (strings, no widgets needed in sidebar)
        self._hotkey_capture = "F6"
        self._hotkey_quick_add = "F7"
        self._hotkey_play_stop = "F8"

        self._update_hotkey_summary()

    def _open_hotkey_dialog(self):
        _HotkeyDialog(
            self.winfo_toplevel(),
            current_values={
                "capture": self._hotkey_capture,
                "quick_add": self._hotkey_quick_add,
                "play_stop": self._hotkey_play_stop,
            },
            on_save=self._on_hotkeys_saved,
        )

    def _on_hotkeys_saved(self, values: dict):
        self._hotkey_capture = values["capture"]
        self._hotkey_quick_add = values["quick_add"]
        self._hotkey_play_stop = values["play_stop"]
        self._update_hotkey_summary()
        self._notify_hotkey_change()

    def _update_hotkey_summary(self):
        self._hotkey_summary.configure(
            text=f"{self._hotkey_capture} / {self._hotkey_quick_add} / {self._hotkey_play_stop}"
        )

    def _auto_scrollbar(self):
        """Hide scrollbar when settings content fits, show when it overflows."""
        try:
            canvas = self._inner._parent_canvas
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if not bbox:
                self._inner._scrollbar.grid_remove()
                return
            content_h = bbox[3] - bbox[1]
            visible_h = canvas.winfo_height()
            if content_h <= visible_h:
                self._inner._scrollbar.grid_remove()
            else:
                self._inner._scrollbar.grid()
        except Exception:
            pass

    def _poll_cursor(self):
        try:
            x, y = pyautogui.position()
            self._cursor_label.configure(text=f"X: {x}   Y: {y}")
        except Exception:
            pass
        self.after(100, self._poll_cursor)

    def _on_speed_change(self, value):
        self.speed_label.configure(text=f"Speed  {value:.2f}x")

    def _notify_hotkey_change(self):
        self._update_hotkey_summary()
        if self.on_hotkey_change:
            self.on_hotkey_change()

    @property
    def speed_multiplier(self) -> float:
        return self._speed_val.get()

    @property
    def repeat_count(self) -> int:
        try:
            val = int(self.repeat_var.get())
            return max(0, val)
        except ValueError:
            return 1

    @property
    def repeat_delay(self) -> float:
        try:
            val = float(self.repeat_delay_var.get())
            return max(0.0, val)
        except ValueError:
            return 0.0

    @property
    def capture_hotkey(self) -> str:
        return self._hotkey_capture

    @property
    def record_movements(self) -> bool:
        return self.record_moves_var.get()

    @property
    def dry_run(self) -> bool:
        return self.dry_run_var.get()

    @property
    def quick_add_hotkey(self) -> str:
        return self._hotkey_quick_add

    @property
    def play_stop_hotkey(self) -> str:
        return self._hotkey_play_stop
