"""Application entry point for DesktopPet."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Type

from PyQt5.QtWidgets import QApplication, QMessageBox

from core.config_manager import ConfigManager
from core.pet_window import PetWindow
from core.scheduler import Scheduler
from core.tray_manager import TrayManager
from core.word_manager import WordManager
from utils.logger import setup_logging


BASE_DIR = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)


class SingleInstanceGuard:
    """Prevent multiple DesktopPet processes from running at the same time."""

    def __init__(self, lock_path: Path) -> None:
        """Create a file lock guard with a stable application lock file."""
        self.lock_path = lock_path
        self._lock_file: Optional[object] = None

    def acquire(self) -> bool:
        """Return True when this process acquired the single-instance lock."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = self.lock_path.open("a+b")
        lock_file.seek(0)
        if not lock_file.read(1):
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock_file.close()
            return False

        self._lock_file = lock_file
        return True

    def release(self) -> None:
        """Release the single-instance lock if this process owns it."""
        if self._lock_file is not None:
            self._lock_file.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None


def install_exception_hook() -> None:
    """Install a global exception hook that logs uncaught exceptions."""

    def handle_exception(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[object],
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        LOGGER.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception


def main() -> int:
    """Initialize and run the Qt application."""
    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    setup_logging(BASE_DIR / "logs")
    install_exception_hook()

    guard = SingleInstanceGuard(BASE_DIR / "logs" / "desktop_pet.lock")
    if not guard.acquire():
        LOGGER.info("DesktopPet is already running; duplicate process exits")
        return 0

    config_manager = ConfigManager(BASE_DIR / "config.yaml")
    word_manager = WordManager(
        config_manager=config_manager,
        database_path=BASE_DIR / "data" / "user_data.db",
        wordlib_dir=BASE_DIR / "data" / "wordlib",
    )
    pet_window = PetWindow(BASE_DIR, config_manager)
    scheduler = Scheduler(config_manager, word_manager, pet_window)
    tray_manager = TrayManager(config_manager, scheduler, word_manager, pet_window)

    pet_window.bubble_result.connect(scheduler.handle_bubble_result)
    pet_window.pet_clicked.connect(lambda: scheduler.show_next_word(force=True))
    scheduler.daily_goal_reached.connect(tray_manager.show_daily_goal_notification)

    def graceful_shutdown() -> None:
        """Close windows and persist pending application state."""
        LOGGER.info("DesktopPet is shutting down")
        scheduler.stop()
        pet_window.close_all_bubbles()
        word_manager.close()
        tray_manager.hide()
        guard.release()

    app.aboutToQuit.connect(graceful_shutdown)

    pet_window.show()
    scheduler.start()
    tray_manager.show()

    LOGGER.info("DesktopPet started successfully")
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
