"""Transparent draggable desktop pet window."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QLinearGradient, QMovie, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow

from core.bubble_window import BubbleWindow
from core.config_manager import ConfigManager
from core.pet_assets import (
    DEFAULT_PET_SKIN,
    PET_ASSET_EXTENSIONS,
    normalize_pet_skin,
)


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
        self.pet_movie: Optional[QMovie] = None
        self.pet_state = "happy"
        self._state_generation = 0

        self._apply_window_flags()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.pet_size = int(self.config_manager.get("pet.size", 200))
        self.setFixedSize(self.pet_size, self.pet_size)
        self._apply_opacity()

        self.pet_label = QLabel(self)
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setGeometry(0, 0, self.pet_size, self.pet_size)
        self._load_pet_animation(self.pet_state)
        self._restore_position()

    def _load_pet_animation(self, state: Optional[str] = None) -> None:
        """Load a pet asset when present, otherwise render a friendly fallback."""
        pet_dir = self.base_dir / "resources" / "pets"
        for image_path in self._pet_asset_candidates(pet_dir, state):
            if image_path.exists() and self._apply_pet_asset(image_path):
                return

        self._draw_fallback_pet()

    def _pet_asset_candidates(self, pet_dir: Path, state: Optional[str]) -> tuple[Path, ...]:
        """Return pet asset paths in display priority order."""
        candidates = []
        for extension in PET_ASSET_EXTENSIONS:
            candidates.append(pet_dir / f"local_pet.{extension}")

        skin = normalize_pet_skin(self.config_manager.get("pet.skin", DEFAULT_PET_SKIN))
        skin_dirs = [pet_dir / "skins" / skin]
        if skin != DEFAULT_PET_SKIN:
            skin_dirs.append(pet_dir / "skins" / DEFAULT_PET_SKIN)

        if state:
            for skin_dir in skin_dirs:
                for extension in PET_ASSET_EXTENSIONS:
                    candidates.append(skin_dir / f"pet_{state}.{extension}")
            for extension in PET_ASSET_EXTENSIONS:
                candidates.append(pet_dir / f"pet_{state}.{extension}")

        for extension in PET_ASSET_EXTENSIONS:
            candidates.append(pet_dir / f"pet.{extension}")

        return tuple(candidates)

    def _apply_pet_asset(self, image_path: Path) -> bool:
        """Apply an image or GIF pet asset to the label."""
        if image_path.suffix.lower() == ".gif":
            movie = QMovie(str(image_path))
            movie.setScaledSize(self.size())
            self.pet_label.clear()
            self.pet_label.setMovie(movie)
            self.pet_movie = movie
            movie.start()
            LOGGER.info("Loaded pet animation from %s", image_path)
            return True

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            return False

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
        self.pet_movie = None
        self.pet_label.clear()
        self.pet_label.setPixmap(canvas)
        LOGGER.info("Loaded pet image from %s", image_path)
        return True

    def _draw_fallback_pet(self) -> None:
        """Draw a fallback pet when no image resources are available."""
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
        self.pet_movie = None
        self.pet_label.clear()
        self.pet_label.setPixmap(fallback)
        LOGGER.warning("pet.gif not found; using built-in fallback image")

    def show_state(self, state: str, duration_ms: int = 0) -> None:
        """Show a named default pet state, then optionally return to happy."""
        self._state_generation += 1
        generation = self._state_generation
        self.pet_state = state
        self._load_pet_animation(self.pet_state)
        if duration_ms <= 0:
            return

        def restore_default() -> None:
            if generation != self._state_generation:
                return
            self.pet_state = "happy"
            self._load_pet_animation(self.pet_state)

        QTimer.singleShot(duration_ms, restore_default)

    def apply_settings(self) -> None:
        """Apply size and positioning settings after config changes."""
        was_visible = self.isVisible()
        self._apply_window_flags()
        if was_visible:
            self.show()
        self._apply_opacity()
        new_size = int(self.config_manager.get("pet.size", self.pet_size))
        if new_size != self.pet_size:
            self.pet_size = new_size
            self.setFixedSize(self.pet_size, self.pet_size)
            self.pet_label.setGeometry(0, 0, self.pet_size, self.pet_size)
        self._load_pet_animation(self.pet_state)
        self._reposition_current_bubble()

    def _apply_window_flags(self) -> None:
        """Apply frameless/tool/always-on-top flags from configuration."""
        flags = Qt.FramelessWindowHint | Qt.Tool
        if bool(self.config_manager.get("pet.always_on_top", True)):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _apply_opacity(self) -> None:
        """Apply pet window opacity from configuration."""
        opacity = int(self.config_manager.get("pet.opacity", 100))
        self.setWindowOpacity(max(20, min(opacity, 100)) / 100)

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
        duration_seconds = int(self.config_manager.get("bubble_duration_seconds", 5))
        self.show_state("eat", duration_ms=max(duration_seconds, 1) * 1000)
        self.close_all_bubbles()
        self.current_bubble = BubbleWindow(
            word_info,
            self.geometry(),
            duration_seconds,
            scale=self._bubble_scale(),
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
            self.show_state("walk")
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
            self.show_state("happy")
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

    def _bubble_scale(self) -> float:
        """Return the bubble scale derived from the configured pet size."""
        return max(0.75, min(self.pet_size / 200, 1.6))
