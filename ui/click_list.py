import customtkinter as ctk
from core.script import ClickEntry
from ui.theme import (
    BG_SURFACE, BG_ELEVATED, ROW_BG, ROW_BG_ALT, ROW_SELECTED, ROW_ACTIVE,
    BORDER, ACCENT, ACCENT_HOVER, AMBER, AMBER_HOVER, RED, RED_HOVER,
    TEXT, TEXT_SEC, TEXT_DIM, FAMILY,
    RADIUS_SM, RADIUS_MD, RADIUS_LG,
)


class ClickListRow(ctk.CTkFrame):
    """Single row representing one script step."""

    def __init__(self, master, index: int, entry: ClickEntry, selected=False,
                 active=False, on_select=None, **kwargs):
        if active:
            bg = ROW_ACTIVE
        elif selected:
            bg = ROW_SELECTED
        else:
            bg = ROW_BG_ALT if index % 2 else ROW_BG

        super().__init__(master, fg_color=bg, corner_radius=RADIUS_SM, height=40, **kwargs)
        self.grid_propagate(False)

        self.index = index
        self.entry = entry
        self._on_select = on_select

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # step number badge
        num_frame = ctk.CTkFrame(self, fg_color=BORDER if not active else "#2a5e3e",
                                 corner_radius=4, width=28, height=22)
        num_frame.grid(row=0, column=0, padx=(10, 6), pady=9)
        num_frame.grid_propagate(False)
        num_frame.grid_columnconfigure(0, weight=1)
        num_frame.grid_rowconfigure(0, weight=1)

        num_label = ctk.CTkLabel(
            num_frame, text=str(index + 1),
            font=ctk.CTkFont(family=FAMILY, size=11, weight="bold"),
            text_color=TEXT if active else TEXT_DIM,
        )
        num_label.grid(row=0, column=0)

        # click type indicator
        type_map = {"left": "L", "right": "R", "double": "D", "move": "M"}
        type_colors = {
            "left": ACCENT,
            "right": "#c084fc",   # soft purple
            "double": "#f59e0b",  # amber
            "move": "#60a5fa",    # sky blue
        }
        type_char = type_map.get(entry.click_type, "?")
        type_color = type_colors.get(entry.click_type, TEXT_DIM)

        type_label = ctk.CTkLabel(
            self, text=type_char, width=22,
            font=ctk.CTkFont(family=FAMILY, size=12, weight="bold"),
            text_color=type_color,
        )
        type_label.grid(row=0, column=1, padx=(0, 6), pady=9)

        # main description
        label_text = entry.label if entry.label else ""
        coord_text = f"({entry.x}, {entry.y})"
        delay_text = f"{entry.delay_before:.2f}s"
        ret_text = "  [return]" if entry.return_cursor else ""

        if label_text:
            display = f"{label_text}   {coord_text}   {delay_text}{ret_text}"
        else:
            action = {"left": "Left Click", "right": "Right Click", "double": "Double Click", "move": "Move To"}.get(
                entry.click_type, entry.click_type
            )
            display = f"{action}   {coord_text}   {delay_text}{ret_text}"

        desc_label = ctk.CTkLabel(
            self, text=display, anchor="w",
            text_color=TEXT if (selected or active) else TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=12),
        )
        desc_label.grid(row=0, column=2, padx=(0, 14), pady=9, sticky="ew")

        # make the whole row clickable
        for widget in [self, num_frame, num_label, type_label, desc_label]:
            widget.bind("<Button-1>", self._clicked)
            widget.bind("<Double-Button-1>", self._double_clicked)

    def _clicked(self, event=None):
        if self._on_select:
            self._on_select(self.index)

    def _double_clicked(self, event=None):
        if self._on_select:
            self._on_select(self.index, edit=True)


class MoveGroupRow(ctk.CTkFrame):
    """Collapsed row representing a group of consecutive mouse move steps."""

    def __init__(self, master, first_index: int, entries: list[ClickEntry],
                 selected=False, active=False, on_select=None, **kwargs):
        if active:
            bg = ROW_ACTIVE
        elif selected:
            bg = ROW_SELECTED
        else:
            bg = ROW_BG_ALT if first_index % 2 else ROW_BG

        super().__init__(master, fg_color=bg, corner_radius=RADIUS_SM, height=40, **kwargs)
        self.grid_propagate(False)

        self.index = first_index
        self.group_size = len(entries)
        self._entries = list(entries)
        self._on_select = on_select

        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # step range badge
        badge_text = self._badge_text()
        badge_w = max(28, len(badge_text) * 7 + 12)
        self._num_frame = ctk.CTkFrame(
            self, fg_color=BORDER if not active else "#2a5e3e",
            corner_radius=4, width=badge_w, height=22,
        )
        self._num_frame.grid(row=0, column=0, padx=(10, 6), pady=9)
        self._num_frame.grid_propagate(False)
        self._num_frame.grid_columnconfigure(0, weight=1)
        self._num_frame.grid_rowconfigure(0, weight=1)

        self._num_label = ctk.CTkLabel(
            self._num_frame, text=badge_text,
            font=ctk.CTkFont(family=FAMILY, size=10, weight="bold"),
            text_color=TEXT if active else TEXT_DIM,
        )
        self._num_label.grid(row=0, column=0)

        # path indicator (wavy ≈ to distinguish from single "M")
        type_label = ctk.CTkLabel(
            self, text="\u2248", width=22,
            font=ctk.CTkFont(family=FAMILY, size=14, weight="bold"),
            text_color="#60a5fa",
        )
        type_label.grid(row=0, column=1, padx=(0, 6), pady=9)

        # description
        self._desc_label = ctk.CTkLabel(
            self, text=self._desc_text(), anchor="w",
            text_color=TEXT if (selected or active) else TEXT_SEC,
            font=ctk.CTkFont(family=FAMILY, size=12),
        )
        self._desc_label.grid(row=0, column=2, padx=(0, 14), pady=9, sticky="ew")

        # clickable
        for widget in [self, self._num_frame, self._num_label, type_label, self._desc_label]:
            widget.bind("<Button-1>", self._clicked)

    def _badge_text(self):
        if self.group_size > 1:
            return f"{self.index + 1}\u2013{self.index + self.group_size}"
        return str(self.index + 1)

    def _desc_text(self):
        count = len(self._entries)
        total_time = sum(e.delay_before for e in self._entries)
        end = self._entries[-1]
        moves = "move" if count == 1 else "moves"
        return f"Mouse path   {count} {moves}   {total_time:.2f}s   \u2192 ({end.x}, {end.y})"

    def update_group(self, entries: list[ClickEntry]):
        """Update with new entries (used during live recording)."""
        self._entries = list(entries)
        self.group_size = len(entries)
        self._desc_label.configure(text=self._desc_text())
        new_badge = self._badge_text()
        self._num_label.configure(text=new_badge)
        badge_w = max(28, len(new_badge) * 7 + 12)
        self._num_frame.configure(width=badge_w)

    def _clicked(self, event=None):
        if self._on_select:
            self._on_select(self.index)


class ClickList(ctk.CTkScrollableFrame):
    """Scrollable list of all script steps with selection support."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=BG_SURFACE, corner_radius=RADIUS_LG,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=TEXT_DIM,
            **kwargs,
        )

        self._rows: list[ClickListRow | MoveGroupRow] = []
        self._current_steps: list[ClickEntry] = []
        self._selected_index = -1
        self._active_index = -1
        self._empty_frame: ctk.CTkFrame | None = None
        self._recording_frame: ctk.CTkFrame | None = None
        self._rec_dot_visible = True
        self._rec_move_group: MoveGroupRow | None = None
        self._rec_move_entries: list[ClickEntry] = []

        self.on_selection_change = None
        self.on_edit_request = None
        self.on_record_click = None
        self.on_add_click = None

        # auto-hide scrollbar when content fits
        self._parent_canvas.bind("<Configure>", lambda e: self.after_idle(self._auto_scrollbar))

        # show empty state by default
        self.after(50, self._show_empty)

    @property
    def selected_index(self):
        return self._selected_index

    def set_active_step(self, index: int):
        self._active_index = index

    @staticmethod
    def _group_steps(steps: list[ClickEntry]):
        """Group consecutive move entries. Returns list of (start_index, [entries])."""
        groups = []
        i = 0
        while i < len(steps):
            if steps[i].click_type == "move":
                start = i
                while i < len(steps) and steps[i].click_type == "move":
                    i += 1
                groups.append((start, steps[start:i]))
            else:
                groups.append((i, [steps[i]]))
                i += 1
        return groups

    def load_steps(self, steps: list[ClickEntry], preserve_selection: bool = False):
        old_sel = self._selected_index if preserve_selection else -1
        self._clear_rows()
        self._active_index = -1
        self._selected_index = old_sel
        self._current_steps = list(steps)

        if not steps:
            self._show_empty()
            self._selected_index = -1
            return

        self._hide_empty()
        for start_idx, entries in self._group_steps(steps):
            if len(entries) >= 2 and entries[0].click_type == "move":
                selected = (
                    old_sel >= 0
                    and start_idx <= old_sel < start_idx + len(entries)
                )
                row = MoveGroupRow(
                    self, start_idx, entries,
                    selected=selected, active=False,
                    on_select=self._handle_row_select,
                )
            else:
                row = ClickListRow(
                    self, start_idx, entries[0],
                    selected=(start_idx == old_sel), active=False,
                    on_select=self._handle_row_select,
                )
            row.pack(fill="x", padx=8, pady=(3, 0))
            self._rows.append(row)

        if not preserve_selection:
            self._selected_index = -1
        self.after_idle(self._auto_scrollbar)

    def refresh(self, steps: list[ClickEntry]):
        old_sel = self._selected_index
        self.load_steps(steps, preserve_selection=True)
        if 0 <= old_sel < len(steps):
            self._selected_index = old_sel
        elif steps:
            self._selected_index = len(steps) - 1
        else:
            self._selected_index = -1

    def refresh_with_highlight(self, steps: list[ClickEntry], active_index: int):
        old_sel = self._selected_index
        self._active_index = active_index
        self._clear_rows()
        self._selected_index = old_sel
        self._current_steps = list(steps)
        self._hide_empty()

        for start_idx, entries in self._group_steps(steps):
            if len(entries) >= 2 and entries[0].click_type == "move":
                is_active = (
                    active_index >= 0
                    and start_idx <= active_index < start_idx + len(entries)
                )
                is_selected = (
                    old_sel >= 0
                    and start_idx <= old_sel < start_idx + len(entries)
                )
                row = MoveGroupRow(
                    self, start_idx, entries,
                    selected=is_selected, active=is_active,
                    on_select=self._handle_row_select,
                )
            else:
                row = ClickListRow(
                    self, start_idx, entries[0],
                    selected=(start_idx == old_sel),
                    active=(start_idx == active_index),
                    on_select=self._handle_row_select,
                )
            row.pack(fill="x", padx=8, pady=(3, 0))
            self._rows.append(row)
        self.after_idle(self._auto_scrollbar)

    def select(self, index: int):
        self._selected_index = index
        if self.on_selection_change:
            self.on_selection_change(index)

    def _auto_scrollbar(self):
        """Hide scrollbar when content fits, show when it overflows."""
        try:
            canvas = self._parent_canvas
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if not bbox:
                self._scrollbar.grid_remove()
                return
            content_h = bbox[3] - bbox[1]
            visible_h = canvas.winfo_height()
            if content_h <= visible_h:
                self._scrollbar.grid_remove()
            else:
                self._scrollbar.grid()
        except Exception:
            pass

    def _clear_rows(self):
        for row in self._rows:
            row.destroy()
        self._rows.clear()

    def _show_empty(self):
        if self._empty_frame:
            return

        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(expand=True, fill="both")

        # center everything vertically
        spacer_top = ctk.CTkFrame(wrap, fg_color="transparent")
        spacer_top.pack(expand=True)

        content = ctk.CTkFrame(wrap, fg_color="transparent")
        content.pack()

        ctk.CTkLabel(
            content, text="No steps yet",
            font=ctk.CTkFont(family=FAMILY, size=15, weight="bold"),
            text_color=TEXT_SEC,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            content,
            text="Record mouse clicks, add steps manually,\nor press F7 to quick-add at your cursor.",
            font=ctk.CTkFont(family=FAMILY, size=12),
            text_color=TEXT_DIM,
            justify="center",
        ).pack(pady=(0, 18))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row, text="Record Clicks", width=130, height=36,
            fg_color=AMBER, hover_color=AMBER_HOVER, text_color="#1a1a1a",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            corner_radius=RADIUS_MD,
            command=lambda: self.on_record_click and self.on_record_click(),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Add Step", width=110, height=36,
            fg_color="transparent", hover_color=BG_ELEVATED,
            text_color=TEXT_SEC, border_color=BORDER, border_width=1,
            font=ctk.CTkFont(family=FAMILY, size=13),
            corner_radius=RADIUS_MD,
            command=lambda: self.on_add_click and self.on_add_click(),
        ).pack(side="left")

        spacer_bot = ctk.CTkFrame(wrap, fg_color="transparent")
        spacer_bot.pack(expand=True)

        self._empty_frame = wrap
        self.after_idle(self._auto_scrollbar)

    def _hide_empty(self):
        if self._empty_frame:
            self._empty_frame.destroy()
            self._empty_frame = None

    def show_recording(self):
        """Show a recording banner at the top with live step rows below."""
        self._hide_empty()
        self._clear_rows()
        self._rec_step_count = 0
        self._rec_move_group = None
        self._rec_move_entries = []

        if self._recording_frame:
            return

        # compact banner
        banner = ctk.CTkFrame(self, fg_color="#2a1215", corner_radius=RADIUS_MD)
        banner.pack(fill="x", padx=8, pady=(6, 4))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        self._rec_dot = ctk.CTkFrame(inner, fg_color=RED, width=10, height=10,
                                      corner_radius=5)
        self._rec_dot.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            inner, text="Recording",
            font=ctk.CTkFont(family=FAMILY, size=13, weight="bold"),
            text_color=RED,
        ).pack(side="left")

        self._rec_count_label = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(family=FAMILY, size=11),
            text_color=TEXT_DIM,
        )
        self._rec_count_label.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            inner, text="Stop", width=60, height=26,
            fg_color=RED, hover_color=RED_HOVER, text_color="#ffffff",
            font=ctk.CTkFont(family=FAMILY, size=11, weight="bold"),
            corner_radius=RADIUS_SM,
            command=lambda: self.on_record_click and self.on_record_click(),
        ).pack(side="right")

        self._recording_frame = banner
        self._rec_dot_visible = True
        self._pulse_dot()
        self.after_idle(self._auto_scrollbar)

    def add_recording_step(self, entry: ClickEntry):
        """Add a live step row during recording, grouping consecutive moves."""
        self._rec_step_count += 1

        if entry.click_type == "move":
            if self._rec_move_group is not None:
                # extend existing move group
                self._rec_move_entries.append(entry)
                self._rec_move_group.update_group(self._rec_move_entries)
            else:
                # start a new move group
                self._rec_move_entries = [entry]
                row = MoveGroupRow(
                    self, self._rec_step_count - 1, self._rec_move_entries,
                )
                row.pack(fill="x", padx=8, pady=(3, 0))
                self._rows.append(row)
                self._rec_move_group = row
        else:
            # end any active move group
            self._rec_move_group = None
            self._rec_move_entries = []
            row = ClickListRow(
                self, self._rec_step_count - 1, entry,
                selected=False, active=False,
            )
            row.pack(fill="x", padx=8, pady=(3, 0))
            self._rows.append(row)

        # update count in banner
        n = self._rec_step_count
        self._rec_count_label.configure(
            text=f"{n} step{'s' if n != 1 else ''} captured"
        )

        # auto-scroll to bottom
        self._parent_canvas.yview_moveto(1.0)
        self.after_idle(self._auto_scrollbar)

    def hide_recording(self):
        """Remove the recording banner."""
        if self._recording_frame:
            self._recording_frame.destroy()
            self._recording_frame = None
        self._rec_move_group = None
        self._rec_move_entries = []
        self._clear_rows()
        self.after_idle(self._auto_scrollbar)

    def _pulse_dot(self):
        """Blink the recording dot."""
        if not self._recording_frame:
            return
        self._rec_dot_visible = not self._rec_dot_visible
        try:
            self._rec_dot.configure(fg_color=RED if self._rec_dot_visible else "#2a1215")
        except Exception:
            return
        self.after(500, self._pulse_dot)

    def _handle_row_select(self, index: int, edit: bool = False):
        self._selected_index = index
        self.load_steps(self._current_steps, preserve_selection=True)
        self._selected_index = index

        if self.on_selection_change:
            self.on_selection_change(index)
        if edit and self.on_edit_request:
            self.on_edit_request(index)
