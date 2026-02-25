import time
import threading
from pynput import mouse
from core.script import ClickEntry

DOUBLE_CLICK_THRESHOLD = 0.25   # seconds between clicks to count as double
MOVE_MIN_INTERVAL = 0.05        # minimum seconds between recorded move samples
MOVE_MIN_DISTANCE = 5           # minimum pixels between recorded move samples


class Recorder:
    def __init__(self):
        self._listener: mouse.Listener | None = None
        self._recording = False
        self._lock = threading.Lock()
        self._entries: list[ClickEntry] = []
        self._last_time: float = 0.0
        self._is_first_event = True
        self._record_movements = False

        # for double-click detection
        self._pending_click: dict | None = None
        self._pending_timer: threading.Timer | None = None

        # for movement sampling
        self._last_move_time: float = 0.0
        self._last_move_x: int = 0
        self._last_move_y: int = 0

        self.on_click_captured = None   # called with (ClickEntry,) for live UI updates

    @property
    def is_recording(self):
        return self._recording

    @property
    def entries(self):
        with self._lock:
            return list(self._entries)

    def start(self, record_movements: bool = False):
        if self._recording:
            return

        self._record_movements = record_movements

        with self._lock:
            self._entries.clear()
        self._last_time = time.monotonic()
        self._is_first_event = True
        self._pending_click = None
        self._last_move_time = 0.0
        self._last_move_x = 0
        self._last_move_y = 0
        self._recording = True

        kwargs = {"on_click": self._on_click}
        if record_movements:
            kwargs["on_move"] = self._on_move
        self._listener = mouse.Listener(**kwargs)
        self._listener.start()

    def stop(self) -> list[ClickEntry]:
        if not self._recording:
            return []

        self._recording = False

        # discard the pending click — it's the Stop button press
        if self._pending_timer:
            self._pending_timer.cancel()
        self._pending_click = None

        if self._listener:
            self._listener.stop()
            self._listener = None

        with self._lock:
            captured = list(self._entries)
            self._entries.clear()
        return captured

    def _on_move(self, x, y):
        if not self._recording or not self._record_movements:
            return

        now = time.monotonic()
        ix, iy = int(x), int(y)

        # throttle: skip if too soon or too close
        dt = now - self._last_move_time
        dx = abs(ix - self._last_move_x)
        dy = abs(iy - self._last_move_y)

        if dt < MOVE_MIN_INTERVAL or (dx < MOVE_MIN_DISTANCE and dy < MOVE_MIN_DISTANCE):
            return

        if self._is_first_event:
            delay = 0.0
            self._is_first_event = False
        else:
            delay = round(now - self._last_time, 3)
        self._last_time = now

        self._last_move_time = now
        self._last_move_x = ix
        self._last_move_y = iy

        self._commit_entry({"x": ix, "y": iy, "delay": delay}, "move")

    def _on_click(self, x, y, button, pressed):
        if not pressed or not self._recording:
            return

        now = time.monotonic()

        # first event gets delay=0 so playback doesn't stall on startup wait
        if self._is_first_event:
            delay = 0.0
            self._is_first_event = False
        else:
            delay = round(now - self._last_time, 3)
        self._last_time = now

        # update move tracking so next move delay is correct
        self._last_move_time = now
        self._last_move_x = int(x)
        self._last_move_y = int(y)

        if button == mouse.Button.left:
            self._handle_left_click(x, y, delay)
        elif button == mouse.Button.right:
            # flush pending left click before recording right click
            self._flush_pending()
            self._commit_entry({"x": int(x), "y": int(y), "delay": delay}, "right")

    def _handle_left_click(self, x, y, delay):
        if self._pending_click:
            # second left click came in quickly — it's a double click
            self._pending_timer.cancel()
            # use the first click's delay (time since the action before it)
            self._commit_entry(self._pending_click, "double")
            self._pending_click = None
        else:
            # hold this click and wait briefly to see if another follows
            self._pending_click = {"x": int(x), "y": int(y), "delay": delay}
            self._pending_timer = threading.Timer(
                DOUBLE_CLICK_THRESHOLD, self._flush_pending
            )
            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _flush_pending(self):
        if self._pending_click:
            self._commit_entry(self._pending_click, "left")
            self._pending_click = None

    def _commit_entry(self, data: dict, click_type: str):
        entry = ClickEntry(
            x=data["x"],
            y=data["y"],
            click_type=click_type,
            delay_before=data["delay"],
            return_cursor=False,
        )

        with self._lock:
            self._entries.append(entry)
        if self.on_click_captured:
            self.on_click_captured(entry)
