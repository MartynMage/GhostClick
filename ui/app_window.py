import os
import sys
from tkinter import filedialog
from datetime import datetime

import customtkinter as ctk
import keyboard
import pyautogui

from core.script import Script, ClickEntry
from core.player import Player
from core.recorder import Recorder
from core.scheduler import ScriptScheduler
from ui.click_list import ClickList
from ui.dialogs import show_info, show_warning, show_error, ask_yes_no
from ui.settings_panel import SettingsPanel
from ui.theme import (
    BG_BASE, BG_SURFACE, BG_ELEVATED, BG_INPUT, BORDER, BORDER_FOCUS,
    ACCENT, ACCENT_HOVER, ACCENT_MUTED,
    GREEN, GREEN_HOVER, RED, RED_HOVER, AMBER, AMBER_HOVER,
    NEUTRAL, NEUTRAL_HOVER,
    TEXT, TEXT_SEC, TEXT_DIM, FAMILY,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)
from utils.file_io import save_script, load_script, GHOSTCLICK_EXT


class GhostClickApp(ctk.CTk):
    def __init__(self, script_path: str | None = None):
        super().__init__()

        self.title("GhostClick")
        self.geometry("980x700")
        self.minsize(820, 580)
        self.configure(fg_color=BG_BASE)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # core objects
        self.script = Script()
        self.player = Player()
        self.recorder = Recorder()
        self.scheduler = ScriptScheduler()
        self._current_file: str | None = None
        self._hotkey_hook = None
        self._quick_add_hook = None
        self._play_stop_hook = None
        self._editing_index: int | None = None

        screen_w, screen_h = pyautogui.size()
        self._screen_w = screen_w
        self._screen_h = screen_h

        self.player.on_step_change = self._on_step_change
        self.player.on_playback_done = self._on_playback_done
        self.player.on_error = self._on_playback_error

        self._build_layout()
        self._bind_shortcuts()
        self._register_hotkey()

        # wire file association button from settings panel
        self.settings.assoc_btn.configure(command=self._register_association)
        self.settings.on_hotkey_change = self._register_hotkey

        if script_path and os.path.isfile(script_path):
            self._load_from_path(script_path)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════════════════════
    #  LAYOUT
    # ═══════════════════════════════════════════════════════════

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── top toolbar ──
        self._build_toolbar()

        # ── left sidebar ──
        self.settings = SettingsPanel(self, width=230)
        self.settings.grid(row=1, column=0, rowspan=2, padx=(10, 0), pady=(0, 10), sticky="ns")

        # sidebar divider
        divider = ctk.CTkFrame(self, fg_color=BORDER, width=1)
        divider.grid(row=1, column=0, rowspan=2, padx=(240, 0), pady=(8, 18), sticky="ns")

        # ── center area ──
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=1, column=1, padx=(6, 10), pady=(0, 10), sticky="nsew")
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(0, weight=1)

        # step list
        self.click_list = ClickList(center)
        self.click_list.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.click_list.on_selection_change = self._on_list_select
        self.click_list.on_edit_request = self._start_edit
        self.click_list.on_record_click = self._toggle_recording
        self.click_list.on_add_click = self._focus_add_form

        # step editing bar
        self._build_step_bar(center)

        # input form
        self._build_input_form(center)

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0, height=56)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.grid_propagate(False)

        # ── left: playback controls ──
        left = ctk.CTkFrame(toolbar, fg_color="transparent")
        left.pack(side="left", padx=14, pady=10)

        self.start_btn = ctk.CTkButton(
            left, text="Start", width=92, height=36,
            fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#ffffff",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._start_playback,
        )
        self.start_btn.pack(side="left", padx=(0, 6))

        self.stop_btn = ctk.CTkButton(
            left, text="Stop", width=80, height=36,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=13),
            corner_radius=RADIUS_MD,
            command=self._stop_playback,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 6))

        self.record_btn = ctk.CTkButton(
            left, text="Record", width=92, height=36,
            fg_color=AMBER, hover_color=AMBER_HOVER, text_color="#1a1a1a",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._toggle_recording,
        )
        self.record_btn.pack(side="left", padx=(0, 18))

        # separator
        self._toolbar_sep(left)

        # ── file operations ──
        self._toolbar_btn("New", self._new_script, left)
        self._toolbar_btn("Open", self._open_script, left)

        # save is slightly more prominent — filled background
        save_btn = ctk.CTkButton(
            left, text="Save", width=60, height=34,
            fg_color=ACCENT_MUTED, hover_color=BG_ELEVATED,
            text_color=TEXT, border_color=BORDER, border_width=1,
            font=ctk.CTkFont(family=FAMILY, size=12, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._save_script,
        )
        save_btn.pack(side="left", padx=(0, 5))

        self._toolbar_btn("Save As", self._save_script_as, left, width=66)

        self._toolbar_sep(left)

        # schedule
        self._toolbar_btn("Schedule", self._schedule_dialog, left, width=76)

        # ── right: step count + status ──
        right = ctk.CTkFrame(toolbar, fg_color="transparent")
        right.pack(side="right", padx=14, pady=10)

        self.status_label = ctk.CTkLabel(
            right, text="Ready",
            font=ctk.CTkFont(family=FAMILY, size=12),
            text_color=TEXT_DIM,
        )
        self.status_label.pack(side="right")

        sep_r = ctk.CTkFrame(right, fg_color=BORDER, width=1, height=18)
        sep_r.pack(side="right", padx=10)

        self.step_count_label = ctk.CTkLabel(
            right, text="0 steps",
            font=ctk.CTkFont(family=FAMILY, size=12),
            text_color=TEXT_SEC,
        )
        self.step_count_label.pack(side="right")

    def _toolbar_btn(self, text, command, parent, width=56):
        btn = ctk.CTkButton(
            parent, text=text, width=width, height=34,
            fg_color="transparent", hover_color=BG_ELEVATED,
            text_color=TEXT_SEC, border_color=BORDER, border_width=1,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_MD,
            command=command,
        )
        btn.pack(side="left", padx=(0, 5))
        return btn

    def _toolbar_sep(self, parent):
        sep = ctk.CTkFrame(parent, fg_color=BORDER, width=1, height=26)
        sep.pack(side="left", padx=(6, 14))

    def _build_step_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=RADIUS_MD, height=44)
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        bar.grid_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=6)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")

        self.delete_btn = self._bar_btn(left, "Delete", RED, RED_HOVER, "#ffffff", self._delete_step)
        self.delete_all_btn = self._bar_btn(left, "Delete All", RED, RED_HOVER, "#ffffff", self._delete_all_steps)
        self.up_btn = self._bar_btn(left, "Up", NEUTRAL, NEUTRAL_HOVER, TEXT_SEC, lambda: self._move_step(-1))
        self.down_btn = self._bar_btn(left, "Down", NEUTRAL, NEUTRAL_HOVER, TEXT_SEC, lambda: self._move_step(1))

        sep = ctk.CTkFrame(left, fg_color=BORDER, width=1, height=20)
        sep.pack(side="left", padx=8)

        self.undo_btn = self._bar_btn(left, "Undo", NEUTRAL, NEUTRAL_HOVER, TEXT_SEC, self._undo)
        self.redo_btn = self._bar_btn(left, "Redo", NEUTRAL, NEUTRAL_HOVER, TEXT_SEC, self._redo)

        # selection-dependent buttons start disabled
        self._selection_buttons = [self.delete_btn, self.up_btn, self.down_btn]
        for btn in self._selection_buttons:
            btn.configure(state="disabled")

        self._edit_buttons = [
            self.delete_btn, self.delete_all_btn, self.up_btn, self.down_btn,
            self.undo_btn, self.redo_btn,
        ]

    def _bar_btn(self, parent, text, fg, hover, text_color, command):
        btn = ctk.CTkButton(
            parent, text=text, width=58, height=30,
            fg_color=fg, hover_color=hover, text_color=text_color,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_SM,
            command=command,
        )
        btn.pack(side="left", padx=(0, 4))
        return btn

    def _build_input_form(self, parent):
        form = ctk.CTkFrame(parent, fg_color=BG_SURFACE, corner_radius=RADIUS_LG)
        form.grid(row=2, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=16, pady=(12, 14))

        # row 1: title + action type, coordinates, delay
        r1 = ctk.CTkFrame(fields, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 8))

        self.form_title = ctk.CTkLabel(
            r1, text="Add Step",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            text_color=TEXT,
        )
        self.form_title.pack(side="left", padx=(0, 14))

        self._form_label(r1, "Action")
        self.click_type_var = ctk.StringVar(value="Left Click")
        self.click_type_menu = ctk.CTkOptionMenu(
            r1, values=["Left Click", "Right Click", "Double Click", "Move"],
            variable=self.click_type_var, width=130, height=34,
            fg_color=BG_INPUT, button_color=BORDER, button_hover_color=BG_ELEVATED,
            text_color=TEXT, dropdown_fg_color=BG_ELEVATED,
            dropdown_hover_color=ACCENT_MUTED, dropdown_text_color=TEXT,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_SM,
        )
        self.click_type_menu.pack(side="left", padx=(0, 16))

        self._form_label(r1, "X")
        self.x_entry = self._form_input(r1, 72, "0")

        self._form_label(r1, "Y")
        self.y_entry = self._form_input(r1, 72, "0")

        self._form_label(r1, "Delay (s)")
        self.delay_entry = self._form_input(r1, 68, "0.5")
        self.delay_entry.insert(0, "0.5")

        # row 2: label, return cursor, action buttons
        r2 = ctk.CTkFrame(fields, fg_color="transparent")
        r2.pack(fill="x")

        self._form_label(r2, "Label")
        self.label_entry = self._form_input(r2, 190, "optional note", pad_right=16)

        self.return_var = ctk.BooleanVar(value=False)
        self.return_check = ctk.CTkCheckBox(
            r2, text="Return cursor", variable=self.return_var,
            font=ctk.CTkFont(family=FAMILY, size=12), text_color=TEXT_SEC,
            fg_color=ACCENT, hover_color=ACCENT,
            border_color=BORDER, border_width=2,
            checkbox_height=18, checkbox_width=18,
        )
        self.return_check.pack(side="left", padx=(0, 16))

        self.add_btn = ctk.CTkButton(
            r2, text="Add Step", width=96, height=34,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#0f1117",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._add_step,
        )
        self.add_btn.pack(side="left", padx=(0, 5))

        self.update_btn = ctk.CTkButton(
            r2, text="Update", width=86, height=34,
            fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#ffffff",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            corner_radius=RADIUS_MD,
            command=self._update_step,
        )

        self.cancel_edit_btn = ctk.CTkButton(
            r2, text="Cancel", width=72, height=34,
            fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_MD,
            command=self._cancel_edit,
        )

        self._edit_buttons.extend([self.add_btn, self.update_btn, self.cancel_edit_btn])

    def _form_label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(family=FAMILY, size=12),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(0, 5))

    def _form_input(self, parent, width, placeholder, pad_right=10):
        entry = ctk.CTkEntry(
            parent, width=width, height=34,
            placeholder_text=placeholder,
            fg_color=BG_INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family=FAMILY, size=12),
            corner_radius=RADIUS_SM,
        )
        entry.pack(side="left", padx=(0, pad_right))
        return entry

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self._new_script())
        self.bind_all("<Control-o>", lambda e: self._open_script())
        self.bind_all("<Control-s>", lambda e: self._save_script())
        self.bind_all("<Control-Shift-S>", lambda e: self._save_script_as())
        self.bind_all("<Control-z>", lambda e: self._undo())
        self.bind_all("<Control-y>", lambda e: self._redo())

    # ═══════════════════════════════════════════════════════════
    #  STATE HELPERS
    # ═══════════════════════════════════════════════════════════

    def _set_editing_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in self._edit_buttons:
            btn.configure(state=state)

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _update_step_count(self):
        n = len(self.script.steps)
        self.step_count_label.configure(text=f"{n} step{'s' if n != 1 else ''}")
        # sync selection-dependent buttons
        has_sel = self.click_list.selected_index >= 0
        state = "normal" if has_sel else "disabled"
        for btn in self._selection_buttons:
            btn.configure(state=state)

    # ═══════════════════════════════════════════════════════════
    #  FORM
    # ═══════════════════════════════════════════════════════════

    _ACTION_TO_INTERNAL = {
        "Left Click": "left", "Right Click": "right",
        "Double Click": "double", "Move": "move",
    }
    _INTERNAL_TO_ACTION = {v: k for k, v in _ACTION_TO_INTERNAL.items()}

    def _entry_from_form(self) -> ClickEntry | None:
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
        except ValueError:
            show_warning(self, "Invalid Input", "X and Y must be integers.")
            return None

        if not (0 <= x < self._screen_w and 0 <= y < self._screen_h):
            proceed = ask_yes_no(
                self, "Out of Bounds",
                f"Coordinates ({x}, {y}) are outside your screen "
                f"({self._screen_w}x{self._screen_h}).\n\nAdd anyway?",
            )
            if not proceed:
                return None

        try:
            delay = float(self.delay_entry.get())
        except ValueError:
            delay = 0.5

        action_display = self.click_type_var.get()
        click_type = self._ACTION_TO_INTERNAL.get(action_display, "left")

        return ClickEntry(
            x=x, y=y,
            click_type=click_type,
            delay_before=max(0.0, delay),
            return_cursor=self.return_var.get(),
            label=self.label_entry.get().strip(),
        )

    def _populate_form(self, entry: ClickEntry):
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(entry.x))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(entry.y))

        display = self._INTERNAL_TO_ACTION.get(entry.click_type, "Left Click")
        self.click_type_var.set(display)

        self.delay_entry.delete(0, "end")
        self.delay_entry.insert(0, str(entry.delay_before))
        self.return_var.set(entry.return_cursor)
        self.label_entry.delete(0, "end")
        self.label_entry.insert(0, entry.label)

    def _clear_form(self):
        self.x_entry.delete(0, "end")
        self.y_entry.delete(0, "end")
        self.delay_entry.delete(0, "end")
        self.delay_entry.insert(0, "0.5")
        self.click_type_var.set("Left Click")
        self.return_var.set(False)
        self.label_entry.delete(0, "end")

    # ═══════════════════════════════════════════════════════════
    #  STEP OPERATIONS
    # ═══════════════════════════════════════════════════════════

    def _add_step(self):
        entry = self._entry_from_form()
        if entry:
            self.script.add_step(entry)
            self.click_list.refresh(self.script.steps)
            self._update_title()
            self._update_step_count()

    def _start_edit(self, index: int):
        if self.player.is_running:
            return
        if 0 <= index < len(self.script.steps):
            self._editing_index = index
            self._populate_form(self.script.steps[index])
            self.form_title.configure(text=f"Editing Step {index + 1}")
            self.add_btn.pack_forget()
            self.update_btn.pack(side="left", padx=(0, 5))
            self.cancel_edit_btn.pack(side="left", padx=(0, 5))

    def _update_step(self):
        if self._editing_index is not None:
            entry = self._entry_from_form()
            if entry:
                self.script.edit_step(self._editing_index, entry)
                self.click_list.refresh(self.script.steps)
                self._cancel_edit()
                self._update_title()

    def _cancel_edit(self):
        self._editing_index = None
        self.form_title.configure(text="Add Step")
        self.update_btn.pack_forget()
        self.cancel_edit_btn.pack_forget()
        self.add_btn.pack(side="left", padx=(0, 5))
        self._clear_form()

    def _delete_step(self):
        idx = self.click_list.selected_index
        if idx >= 0:
            self.script.delete_step(idx)
            self.click_list.refresh(self.script.steps)
            self._update_title()
            self._update_step_count()

    def _delete_all_steps(self):
        if not self.script.steps:
            return
        if not ask_yes_no(self, "Delete All", f"Delete all {len(self.script.steps)} steps?"):
            return
        self.script.clear()
        self.click_list.refresh(self.script.steps)
        self._update_title()
        self._update_step_count()

    def _move_step(self, direction: int):
        idx = self.click_list.selected_index
        if idx >= 0:
            new_idx = self.script.move_step(idx, direction)
            self.click_list.refresh(self.script.steps)
            self.click_list.select(new_idx)
            self._update_title()

    def _undo(self):
        if self.player.is_running:
            return
        if self.script.undo():
            self.click_list.refresh(self.script.steps)
            self._update_title()
            self._update_step_count()

    def _redo(self):
        if self.player.is_running:
            return
        if self.script.redo():
            self.click_list.refresh(self.script.steps)
            self._update_title()
            self._update_step_count()

    def _on_list_select(self, index: int):
        has_sel = index >= 0
        state = "normal" if has_sel else "disabled"
        for btn in self._selection_buttons:
            btn.configure(state=state)

    def _focus_add_form(self):
        """Scroll down and focus the X entry so the user can start typing."""
        self.x_entry.focus_set()

    # ═══════════════════════════════════════════════════════════
    #  PLAYBACK
    # ═══════════════════════════════════════════════════════════

    def _start_playback(self):
        if not self.script.steps:
            show_info(self, "Nothing to Play", "Add some steps first.")
            return

        if self._editing_index is not None:
            self._cancel_edit()

        self.script.repeat_count = self.settings.repeat_count
        self.player.speed_multiplier = self.settings.speed_multiplier
        self.player.repeat_delay = self.settings.repeat_delay

        self.start_btn.configure(state="disabled", fg_color=NEUTRAL, text_color=TEXT_DIM)
        self.stop_btn.configure(state="normal", fg_color=RED, hover_color=RED_HOVER, text_color="#ffffff")
        self.record_btn.configure(state="disabled", fg_color=NEUTRAL, text_color=TEXT_DIM)
        self._set_editing_enabled(False)
        self._set_status("Playing...")

        self.player.start(self.script, dry_run=self.settings.dry_run)

    def _stop_playback(self):
        self.player.stop()

    def _on_step_change(self, index: int):
        self.after(0, lambda: self.click_list.refresh_with_highlight(self.script.steps, index))
        self.after(0, lambda: self._set_status(f"Step {index + 1} / {len(self.script.steps)}"))

    def _on_playback_done(self):
        def _reset():
            self.start_btn.configure(
                state="normal", fg_color=GREEN, hover_color=GREEN_HOVER, text_color="#ffffff",
            )
            self.stop_btn.configure(
                state="disabled",
                fg_color=NEUTRAL, hover_color=NEUTRAL_HOVER, text_color=TEXT_SEC,
            )
            self.record_btn.configure(
                state="normal", fg_color=AMBER, hover_color=AMBER_HOVER, text_color="#1a1a1a",
            )
            self._set_editing_enabled(True)
            self.click_list.refresh(self.script.steps)
            self._set_status("Ready")
        self.after(0, _reset)

    def _on_playback_error(self, msg: str):
        self.after(0, lambda: show_error(self, "Playback Error", msg))
        self.after(0, lambda: self._set_status("Error"))

    # ═══════════════════════════════════════════════════════════
    #  RECORDING
    # ═══════════════════════════════════════════════════════════

    def _toggle_recording(self):
        if self.recorder.is_recording:
            entries = self.recorder.stop()
            self.record_btn.configure(
                text="Record", fg_color=AMBER, hover_color=AMBER_HOVER,
                text_color="#1a1a1a",
            )
            self.start_btn.configure(
                state="normal", fg_color=GREEN, text_color="#ffffff",
            )
            self.stop_btn.configure(
                state="disabled", fg_color=NEUTRAL, text_color=TEXT_SEC,
            )
            self._set_editing_enabled(True)
            self._set_status("Ready")

            self.click_list.hide_recording()
            if entries:
                for e in entries:
                    self.script.add_step(e)
                self.click_list.refresh(self.script.steps)
                self._update_title()
                self._update_step_count()
                self._set_status(f"Recorded {len(entries)} steps")
            else:
                self.click_list.refresh(self.script.steps)
        else:
            if self._editing_index is not None:
                self._cancel_edit()

            self.recorder.on_click_captured = self._on_click_captured
            self.recorder.start(record_movements=self.settings.record_movements)
            self.record_btn.configure(
                text="Stop Rec", fg_color=RED, hover_color=RED_HOVER,
                text_color="#ffffff",
            )
            self.start_btn.configure(
                state="disabled", fg_color=NEUTRAL, text_color=TEXT_DIM,
            )
            self.stop_btn.configure(
                state="disabled", fg_color=NEUTRAL, text_color=TEXT_DIM,
            )
            self._set_editing_enabled(False)
            self._set_status("Recording...")
            self.click_list.show_recording()

    def _on_click_captured(self, entry: ClickEntry):
        """Called from recorder thread — schedule UI update on main thread."""
        self.after(0, lambda: self.click_list.add_recording_step(entry))

    # ═══════════════════════════════════════════════════════════
    #  HOTKEY
    # ═══════════════════════════════════════════════════════════

    def _register_hotkey(self):
        self._unregister_hotkey()

        # F6 — fill X/Y from cursor
        try:
            key = self.settings.capture_hotkey
            self._hotkey_hook = keyboard.add_hotkey(key, self._capture_cursor_pos)
        except Exception:
            pass

        # F7 — quick-add step at cursor position
        try:
            key = self.settings.quick_add_hotkey
            self._quick_add_hook = keyboard.add_hotkey(key, self._quick_add_step)
        except Exception:
            pass

        # F8 — toggle playback
        try:
            key = self.settings.play_stop_hotkey
            self._play_stop_hook = keyboard.add_hotkey(key, self._toggle_playback_hotkey)
        except Exception:
            pass

    def _unregister_hotkey(self):
        for attr in ("_hotkey_hook", "_quick_add_hook", "_play_stop_hook"):
            hook = getattr(self, attr, None)
            if hook is not None:
                try:
                    keyboard.remove_hotkey(hook)
                except Exception:
                    pass
                setattr(self, attr, None)

    def _capture_cursor_pos(self):
        try:
            x, y = pyautogui.position()
            self.after(0, lambda: self._fill_coords(x, y))
        except Exception:
            pass

    def _fill_coords(self, x: int, y: int):
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(x))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(y))

    def _quick_add_step(self):
        """Capture cursor position and immediately add a left-click step."""
        if self.player.is_running or self.recorder.is_recording:
            return
        try:
            x, y = pyautogui.position()
        except Exception:
            return

        entry = ClickEntry(
            x=x, y=y,
            click_type="left",
            delay_before=0.5,
        )
        self.after(0, lambda: self._append_quick_step(entry))

    def _append_quick_step(self, entry: ClickEntry):
        self.script.add_step(entry)
        self.click_list.refresh(self.script.steps)
        self._update_title()
        self._update_step_count()
        self._set_status(f"Added step at ({entry.x}, {entry.y})")

    def _toggle_playback_hotkey(self):
        """Start playback if idle, stop if running."""
        if self.player.is_running:
            self.after(0, self._stop_playback)
        else:
            self.after(0, self._start_playback)

    # ═══════════════════════════════════════════════════════════
    #  FILE OPS
    # ═══════════════════════════════════════════════════════════

    def _new_script(self):
        if self._editing_index is not None:
            self._cancel_edit()
        self.script = Script()
        self._current_file = None
        self.click_list.refresh(self.script.steps)
        self._clear_form()
        self._update_title()
        self._update_step_count()

    def _open_script(self):
        path = filedialog.askopenfilename(
            title="Open Script",
            filetypes=[("GhostClick Scripts", f"*{GHOSTCLICK_EXT}"), ("All Files", "*.*")],
        )
        if path:
            self._load_from_path(path)

    def _load_from_path(self, path: str):
        try:
            self.script = load_script(path)
            self._current_file = path

            if self._editing_index is not None:
                self._cancel_edit()

            self.click_list.refresh(self.script.steps)
            self.settings.repeat_var.set(str(self.script.repeat_count))
            self._update_title()
            self._update_step_count()
        except Exception as e:
            show_error(self, "Load Error", f"Failed to load script:\n{e}")

    def _save_script(self):
        if self._current_file:
            self.script.repeat_count = self.settings.repeat_count
            save_script(self.script, self._current_file)
            self._update_title()
            self._set_status("Saved")
        else:
            self._save_script_as()

    def _save_script_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Script",
            defaultextension=GHOSTCLICK_EXT,
            filetypes=[("GhostClick Scripts", f"*{GHOSTCLICK_EXT}")],
        )
        if path:
            self.script.repeat_count = self.settings.repeat_count
            self._current_file = save_script(self.script, path)
            self._update_title()
            self._set_status("Saved")

    def _register_association(self):
        from utils.file_io import register_file_association
        if register_file_association():
            show_info(self, "File Association", ".ghostclick files are now associated with GhostClick.")
        else:
            show_warning(self, "File Association", "Could not register file association. Try running as admin.")

    # ═══════════════════════════════════════════════════════════
    #  SCHEDULING
    # ═══════════════════════════════════════════════════════════

    def _schedule_dialog(self):
        if not self.script.steps:
            show_info(self, "Nothing to Schedule", "Add some steps first.")
            return

        dialog = ctk.CTkInputDialog(
            text="Run at (YYYY-MM-DD HH:MM:SS):",
            title="Schedule Script",
        )
        result = dialog.get_input()
        if not result:
            return

        try:
            run_at = datetime.strptime(result.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            show_warning(self, "Invalid Format", "Use YYYY-MM-DD HH:MM:SS format.")
            return

        if run_at <= datetime.now():
            show_warning(self, "Past Time", "Scheduled time must be in the future.")
            return

        self.script.repeat_count = self.settings.repeat_count
        self.player.speed_multiplier = self.settings.speed_multiplier

        self.scheduler.schedule(
            "main_schedule", run_at,
            lambda: self.after(0, self._start_playback),
        )
        show_info(self, "Scheduled", f"Script will run at {run_at}.")

    def _cancel_schedule(self):
        self.scheduler.cancel_all()
        show_info(self, "Cancelled", "All scheduled runs have been cancelled.")

    # ═══════════════════════════════════════════════════════════
    #  WINDOW
    # ═══════════════════════════════════════════════════════════

    def _update_title(self):
        name = self.script.name
        path = self._current_file
        if path:
            display = os.path.basename(path)
        elif name != "Untitled":
            display = name
        else:
            display = "Untitled"
        self.title(f"GhostClick — {display}")

    def _on_close(self):
        self.player.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
        self._unregister_hotkey()
        self.scheduler.shutdown()
        self.destroy()
