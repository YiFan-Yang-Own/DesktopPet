"""Reminder scheduling and do-not-disturb checks."""

from __future__ import annotations

import ctypes
import logging
import platform
from datetime import datetime, time
from typing import Dict, Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication

from core.config_manager import ConfigManager
from core.pet_window import PetWindow
from core.word_manager import WordManager


LOGGER = logging.getLogger(__name__)


class Scheduler(QObject):
    """Drive periodic word reminders through a Qt timer."""

    daily_goal_reached = pyqtSignal()

    def __init__(
        self,
        config_manager: ConfigManager,
        word_manager: WordManager,
        pet_window: PetWindow,
    ) -> None:
        """Create scheduler dependencies and timer."""
        super().__init__()
        self.config_manager = config_manager
        self.word_manager = word_manager
        self.pet_window = pet_window
        self.paused = False
        self._goal_notified_today: Optional[str] = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.trigger_reminder)

    def start(self) -> None:
        """Start the reminder timer and send an initial gentle reminder."""
        self.update_interval()
        if bool(self.config_manager.get("startup_reminder", True)):
            QTimer.singleShot(1500, self.trigger_reminder)

    def stop(self) -> None:
        """Stop the reminder timer."""
        self.timer.stop()

    def pause(self) -> None:
        """Pause reminder popups."""
        self.paused = True
        LOGGER.info("Scheduler paused")

    def resume(self) -> None:
        """Resume reminder popups."""
        self.paused = False
        LOGGER.info("Scheduler resumed")

    def update_interval(self) -> None:
        """Apply the reminder interval from configuration."""
        seconds = int(
            self.config_manager.get(
                "reminder_interval_seconds",
                int(self.config_manager.get("reminder_interval_minutes", 30)) * 60,
            )
        )
        interval_ms = max(seconds, 1) * 1000
        self.timer.start(interval_ms)
        LOGGER.info("Reminder interval set to %s seconds", seconds)

    def trigger_reminder(self) -> None:
        """Fetch and display the next word when reminders are allowed."""
        self.show_next_word(force=False)

    def show_next_word(self, force: bool = False) -> None:
        """Fetch and display the next word."""
        if self.paused:
            return
        if not force and self._is_quiet_time():
            LOGGER.info("Skipping reminder during quiet hours")
            return
        if not force and self._is_foreground_fullscreen():
            LOGGER.info("Skipping reminder because foreground window is fullscreen")
            word = self.word_manager.get_next_word()
            if word is not None:
                self.word_manager.defer_word(int(word["id"]))
            return

        word = self.word_manager.get_next_word()
        if word is None:
            return
        self._attach_progress(word)
        self.pet_window.show_bubble(word)

    def handle_bubble_result(self, word_info: Dict[str, object], result: str) -> None:
        """Persist a bubble action and emit daily-goal notification when reached."""
        word_id = int(word_info["id"])
        self.word_manager.record_result(word_id, result)

        stats = self.word_manager.get_today_stats()
        daily_goal = int(self.config_manager.get("daily_goal", 20))
        today_key = datetime.now().date().isoformat()
        completed = stats["new_words"] + stats["reviews"]
        if completed >= daily_goal and self._goal_notified_today != today_key:
            self._goal_notified_today = today_key
            self.daily_goal_reached.emit()

    def _attach_progress(self, word: Dict[str, object]) -> None:
        """Attach daily progress metadata to a word before displaying it."""
        stats = self.word_manager.get_today_stats()
        daily_goal = max(int(self.config_manager.get("daily_goal", 20)), 1)
        completed = int(stats["total"])
        percent = min(int(completed / daily_goal * 100), 100)
        word["progress_percent"] = percent
        word["progress_text"] = f"今日 {completed}/{daily_goal}"

    def _is_quiet_time(self) -> bool:
        """Return True when current local time is inside configured quiet hours."""
        quiet_enabled = bool(self.config_manager.get("quiet_hours.enabled", True))
        if not quiet_enabled:
            return False

        start_value = str(self.config_manager.get("quiet_hours.start", "22:00"))
        end_value = str(self.config_manager.get("quiet_hours.end", "08:00"))
        try:
            start = time.fromisoformat(start_value)
            end = time.fromisoformat(end_value)
        except ValueError:
            LOGGER.warning("Invalid quiet hours config: %s - %s", start_value, end_value)
            return False

        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    def _is_foreground_fullscreen(self) -> bool:
        """Detect fullscreen foreground windows on Windows."""
        if platform.system() != "Windows":
            return False

        screen = QApplication.primaryScreen()
        if screen is None:
            return False
        geometry = screen.geometry()

        class Rect(ctypes.Structure):
            """Win32 RECT structure."""

            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False

        rect = Rect()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False

        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return width >= geometry.width() and height >= geometry.height()
