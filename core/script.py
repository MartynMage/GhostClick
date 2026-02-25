from dataclasses import dataclass, asdict
import copy

MAX_UNDO_HISTORY = 50


@dataclass
class ClickEntry:
    x: int = 0
    y: int = 0
    click_type: str = "left"          # "left", "right", "double", "move"
    delay_before: float = 0.5
    return_cursor: bool = False
    label: str = ""
    move_to: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    def describe(self):
        """One-liner summary for display in the step list."""
        tag = f"[{self.label}] " if self.label else ""
        action = {
            "left": "L-Click", "right": "R-Click",
            "double": "Dbl-Click", "move": "Move",
        }.get(self.click_type, self.click_type)
        ret = " (return)" if self.return_cursor else ""
        return f"{tag}{action} @ ({self.x}, {self.y}) — {self.delay_before:.2f}s{ret}"


class Script:
    def __init__(self, name: str = "Untitled"):
        self.name = name
        self.version = "1.0"
        self.repeat_count = 1          # 0 = infinite
        self.steps: list[ClickEntry] = []
        self._undo_stack: list[list[ClickEntry]] = []
        self._redo_stack: list[list[ClickEntry]] = []

    # --- undo/redo helpers ---

    def _snapshot(self):
        self._undo_stack.append([copy.deepcopy(s) for s in self.steps])
        if len(self._undo_stack) > MAX_UNDO_HISTORY:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append([copy.deepcopy(s) for s in self.steps])
        self.steps = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append([copy.deepcopy(s) for s in self.steps])
        self.steps = self._redo_stack.pop()
        return True

    # --- step manipulation ---

    def add_step(self, entry: ClickEntry, index: int | None = None):
        self._snapshot()
        if index is not None:
            self.steps.insert(index, entry)
        else:
            self.steps.append(entry)

    def edit_step(self, index: int, entry: ClickEntry):
        if 0 <= index < len(self.steps):
            self._snapshot()
            self.steps[index] = entry

    def delete_step(self, index: int):
        if 0 <= index < len(self.steps):
            self._snapshot()
            self.steps.pop(index)

    def move_step(self, index: int, direction: int):
        """Move a step up (direction=-1) or down (direction=1)."""
        target = index + direction
        if 0 <= index < len(self.steps) and 0 <= target < len(self.steps):
            self._snapshot()
            self.steps[index], self.steps[target] = self.steps[target], self.steps[index]
            return target
        return index

    def clear(self):
        self._snapshot()
        self.steps.clear()

    # --- serialization ---

    def to_dict(self):
        return {
            "version": self.version,
            "name": self.name,
            "repeat_count": self.repeat_count,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict):
        script = cls(name=data.get("name", "Untitled"))
        script.version = data.get("version", "1.0")
        script.repeat_count = data.get("repeat_count", 1)
        script.steps = [ClickEntry.from_dict(s) for s in data.get("steps", [])]
        return script
