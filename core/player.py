import time
import threading
import pyautogui
from core.script import Script, ClickEntry

# keep pyautogui's failsafe on — moving to top-left corner aborts
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


class Player:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_step = -1
        self._running = False
        self.speed_multiplier = 1.0
        self.repeat_delay = 0.0

        # callbacks the UI can hook into
        self.on_step_change = None     # called with (step_index,)
        self.on_playback_done = None   # called with no args when finished
        self.on_error = None           # called with (error_message,)

    @property
    def is_running(self):
        return self._running

    @property
    def current_step(self):
        return self._current_step

    def start(self, script: Script, dry_run: bool = False):
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._current_step = -1

        self._thread = threading.Thread(
            target=self._run_loop,
            args=(script, dry_run),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run_loop(self, script: Script, dry_run: bool):
        try:
            repeat = script.repeat_count
            infinite = repeat == 0
            iteration = 0

            while infinite or iteration < repeat:
                if self._stop_event.is_set():
                    break

                for i, step in enumerate(script.steps):
                    if self._stop_event.is_set():
                        break

                    self._current_step = i
                    if self.on_step_change:
                        self.on_step_change(i)

                    delay = step.delay_before / self.speed_multiplier
                    if delay > 0:
                        # sleep in small chunks so we can respond to stop quickly
                        self._interruptible_sleep(delay)

                    if self._stop_event.is_set():
                        break

                    if not dry_run:
                        self._execute_click(step)

                iteration += 1

                # pause between loops (skip after the final iteration)
                if self.repeat_delay > 0 and (infinite or iteration < repeat):
                    if not self._stop_event.is_set():
                        self._interruptible_sleep(self.repeat_delay)

        except pyautogui.FailSafeException:
            if self.on_error:
                self.on_error("Failsafe triggered — mouse was moved to corner.")
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
        finally:
            self._running = False
            self._current_step = -1
            if self.on_playback_done:
                self.on_playback_done()

    def _execute_click(self, step: ClickEntry):
        original_x, original_y = pyautogui.position()

        if step.move_to:
            pyautogui.moveTo(step.x, step.y, duration=0.05)

        if step.click_type == "move":
            pyautogui.moveTo(step.x, step.y, duration=0)
        elif step.click_type == "left":
            pyautogui.click(step.x, step.y)
        elif step.click_type == "right":
            pyautogui.rightClick(step.x, step.y)
        elif step.click_type == "double":
            pyautogui.doubleClick(step.x, step.y)

        if step.return_cursor:
            pyautogui.moveTo(original_x, original_y, duration=0.05)

    def _interruptible_sleep(self, seconds: float):
        """Sleep in 50ms chunks so stop requests aren't delayed."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._stop_event.is_set():
                return
            remaining = end - time.monotonic()
            time.sleep(min(0.05, max(0, remaining)))
