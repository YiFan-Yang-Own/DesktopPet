"""Transparent draggable desktop pet window."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QLinearGradient, QMovie, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

from core.bubble_window import BubbleWindow
from core.config_manager import ConfigManager


LOGGER = logging.getLogger(__name__)


class PetWindow(QMainWindow):
    """A frameless always-on-top pet window with drag support."""

    bubble_result = pyqtSignal(dict, str)
    pet_clicked = pyqtSignal()

    def __init__(self, base_dir: Path, config_manager: ConfigManager) -> None:
        """Create the pet window and load animation resources."""
        super().__init__()
        self.base_dir = base_dir
        self.config_manager = config_manager
        self.drag_position: Optional[QPoint] = None
        self.press_position: Optional[QPoint] = None
        self.current_bubble: Optional[BubbleWindow] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pet_size = int(self.config_manager.get("pet.size", 200))
        self.setFixedSize(self.pet_size, self.pet_size)

        self.pet_label = QLabel(self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setGeometry(0, 0, self.pet_size, self.pet_size)
        self._load_pet_animation()
        self._restore_position()

    def _load_pet_animation(self) -> None:
        """Load a pet asset when present, otherwise render a friendly fallback."""
        pet_dir = self.base_dir / "resources" / "pets"
        for image_name in (
            "local_pet.gif",
            "local_pet.png",
            "local_pet.jpg",
            "local_pet.jpeg",
            "pet.gif",
            "pet.png",
            "pet.jpg",
            "pet.jpeg",
        ):
            image_path = pet_dir / image_name
            if not image_path.exists():
                continue
            if image_path.suffix.lower() == ".gif":
                movie = QMovie(str(image_path))
                movie.setScaledSize(self.size())
                self.pet_label.setMovie(movie)
                movie.start()
                LOGGER.info("Loaded pet animation from %s", image_path)
                return
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                canvas = QPixmap(self.size())
                canvas.fill(Qt.transparent)
                painter = QPainter(canvas)
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
                painter.end()
                self.pet_label.setPixmap(canvas)
                LOGGER.info("Loaded pet image from %s", image_path)
                return

        fallback = QPixmap(self.size())
        fallback.fill(Qt.transparent)
        painter = QPainter(fallback)
        painter.setRenderHint(QPainter.Antialiasing, True)

        shadow = QColor(15, 23, 42, 45)
        painter.setBrush(shadow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(48, 152, 104, 20)

        body_gradient = QLinearGradient(55, 35, 145, 160)
        body_gradient.setColorAt(0, QColor("#fde68a"))
        body_gradient.setColorAt(1, QColor("#fb923c"))
        painter.setBrush(body_gradient)
        painter.setPen(QPen(QColor("#92400e"), 2))
        painter.drawEllipse(42, 38, 116, 122)

        painter.setBrush(QColor("#fef3c7"))
        painter.setPen(QPen(QColor("#92400e"), 2))
        painter.drawEllipse(63, 90, 74, 58)

        painter.setBrush(QColor("#111827"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(75, 78, 12, 15)
        painter.drawEllipse(113, 78, 12, 15)

        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(79, 81, 4, 5)
        painter.drawEllipse(117, 81, 4, 5)

        painter.setPen(QPen(QColor("#7c2d12"), 3))
        painter.drawArc(QRect(82, 96, 36, 26), 200 * 16, 140 * 16)

        painter.setBrush(QColor("#fed7aa"))
        painter.setPen(QPen(QColor("#92400e"), 2))
        painter.drawEllipse(31, 86, 28, 36)
        painter.drawEllipse(141, 86, 28, 36)

        painter.setBrush(QColor("#f97316"))
        painter.setPen(QPen(QColor("#92400e"), 2))
        painter.drawEllipse(57, 31, 28, 28)
        painter.drawEllipse(115, 31, 28, 28)
        painter.end()
        self.pet_label.setPixmap(fallback)
        LOGGER.warning("pet.gif not found; using built-in fallback image")

    def apply_settings(self) -> None:
        """Apply size and positioning settings after config changes."""
        new_size = int(self.config_manager.get("pet.size", self.pet_size))
        if new_size != self.pet_size:
            self.pet_size = new_size
            self.setFixedSize(self.pet_size, self.pet_size)
            self.pet_label.setGeometry(0, 0, self.pet_size, self.pet_size)
            self._load_pet_animation()
            self._reposition_current_bubble()

    def _restore_position(self) -> None:
        """Restore saved position or move to the lower-right corner."""
        x = self.config_manager.get("pet.x")
        y = self.config_manager.get("pet.y")
        if isinstance(x, int) and isinstance(y, int):
            self.move(x, y)
            return
        self._move_to_bottom_right()

    def _move_to_bottom_right(self) -> None:
        """Move the pet to the lower-right corner of the primary screen."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        x = available.right() - self.width() - 20
        y = available.bottom() - self.height() - 20
        self.move(x, y)

    def show_bubble(self, word_info: Dict[str, object]) -> None:
        """Show a word bubble near the pet window."""
        self.close_all_bubbles()
        self.current_bubble = BubbleWindow(
            word_info,
            self.geometry(),
            int(self.config_manager.get("bubble_duration_seconds", 5)),
        )
        self.current_bubble.result_selected.connect(self.bubble_result.emit)
        self.current_bubble.show()

    def close_all_bubbles(self) -> None:
        """Close the currently visible bubble, if any."""
        if self.current_bubble is not None:
            self.current_bubble.close()
            self.current_bubble = None

    def mousePressEvent(self, event: object) -> None:
        """Start dragging when the left mouse button is pressed."""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.press_position = event.globalPos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            event.accept()

    def mouseMoveEvent(self, event: object) -> None:
        """Move the pet while dragging."""
        if event.buttons() & Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            self._reposition_current_bubble()
            event.accept()

    def mouseReleaseEvent(self, event: object) -> None:
        """Finish dragging and restore the cursor."""
        if event.button() == Qt.LeftButton:
            was_click = (
                self.press_position is not None
                and (event.globalPos() - self.press_position).manhattanLength() <= 5
            )
            self.drag_position = None
            self.press_position = None
            self.setCursor(QCursor(Qt.ArrowCursor))
            self._reposition_current_bubble()
            self._save_position()
            if was_click:
                self.pet_clicked.emit()
            event.accept()

    def _reposition_current_bubble(self) -> None:
        """Keep the visible word bubble attached to the pet while moving."""
        if self.current_bubble is not None:
            self.current_bubble.reposition(self.geometry())

    def _save_position(self) -> None:
        """Persist the current pet position."""
        self.config_manager.set("pet.x", self.x())
        self.config_manager.set("pet.y", self.y())
