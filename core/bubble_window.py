"""Word reminder bubble widget."""

from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygon
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BubbleWindow(QWidget):
    """A rounded word card with action buttons and a pointer triangle."""

    result_selected = pyqtSignal(dict, str)

    def __init__(
        self,
        word_info: Dict[str, object],
        pet_rect: QRect,
        auto_close_seconds: int = 5,
        scale: float = 1.0,
    ) -> None:
        """Create a bubble for a single word and position it near the pet."""
        super().__init__()
        self.word_info = word_info
        self.pet_rect = pet_rect
        self.auto_close_seconds = max(int(auto_close_seconds), 1)
        self.scale = max(0.75, min(float(scale), 1.6))
        self._fade_animation: Optional[QPropertyAnimation] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.min_width = self._scaled(280)
        self.max_width = self._scaled(380)
        self.setMaximumWidth(self.max_width)

        self._build_ui()
        self.adjustSize()
        self._smart_position()

        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.close)

    def _build_ui(self) -> None:
        """Build labels and buttons inside the custom-painted bubble."""
        container = QVBoxLayout(self)
        container.setContentsMargins(
            self._scaled(20),
            self._scaled(16),
            self._scaled(20),
            self._scaled(26),
        )
        container.setSpacing(self._scaled(8))

        header_layout = QHBoxLayout()
        tag_label = QLabel(str(self.word_info.get("level", "CET4")))
        tag_label.setAlignment(Qt.AlignCenter)
        tag_label.setStyleSheet(
            f"""
            QLabel {
                background: #e0f2fe;
                color: #0369a1;
                border-radius: 5px;
                padding: {self._scaled(3)}px {self._scaled(8)}px;
                font-size: {self._scaled(11)}px;
                font-weight: 700;
            }
            """
        )
        status_label = QLabel(str(self.word_info.get("progress_text", "今日继续加油")))
        status_label.setStyleSheet(f"color: #64748b; font-size: {self._scaled(12)}px;")
        header_layout.addWidget(tag_label)
        header_layout.addStretch(1)
        header_layout.addWidget(status_label)

        word_label = QLabel(str(self.word_info.get("word", "")))
        word_font = QFont()
        word_font.setPointSize(self._scaled(20))
        word_font.setBold(True)
        word_label.setFont(word_font)
        word_label.setStyleSheet("color: #111827;")

        phonetic_label = QLabel(str(self.word_info.get("phonetic", "")))
        phonetic_label.setStyleSheet(f"color: #2563eb; font-size: {self._scaled(13)}px;")

        meaning_label = QLabel(str(self.word_info.get("meaning", "")))
        meaning_label.setWordWrap(True)
        meaning_label.setStyleSheet(
            f"color: #1f2937; font-size: {self._scaled(14)}px; font-weight: 600;"
        )

        example_label = QLabel(str(self.word_info.get("example", "")))
        example_label.setWordWrap(True)
        example_label.setStyleSheet(
            f"""
            QLabel {
                color: #64748b;
                font-size: {self._scaled(12)}px;
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: {self._scaled(8)}px;
            }
            """
        )

        progress_bar = QProgressBar()
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(self._scaled(7))
        progress_bar.setRange(0, 100)
        progress_bar.setValue(int(self.word_info.get("progress_percent", 0)))
        progress_bar.setStyleSheet(
            """
            QProgressBar {
                background: #e5e7eb;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: #22c55e;
                border-radius: 3px;
            }
            """
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(self._scaled(8))
        remember_button = QPushButton("记住了")
        again_button = QPushButton("再记一次")
        for button in (remember_button, again_button):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(self._scaled(28))
            button.setStyleSheet(
                f"""
                QPushButton {
                    background: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                    padding: {self._scaled(6)}px {self._scaled(14)}px;
                    color: #111827;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #f3f4f6;
                }
                """
            )
        remember_button.setStyleSheet(
            f"""
            QPushButton {
                background: #2563eb;
                border: 1px solid #2563eb;
                border-radius: 6px;
                padding: {self._scaled(6)}px {self._scaled(14)}px;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #1d4ed8;
                border-color: #1d4ed8;
            }
            """
        )

        remember_button.clicked.connect(lambda: self._finish("remembered"))
        again_button.clicked.connect(lambda: self._finish("again"))
        button_layout.addStretch(1)
        button_layout.addWidget(again_button)
        button_layout.addWidget(remember_button)

        container.addLayout(header_layout)
        container.addWidget(word_label)
        container.addWidget(phonetic_label)
        container.addWidget(meaning_label)
        container.addWidget(example_label)
        container.addWidget(progress_bar)
        container.addSpacing(self._scaled(4))
        container.addLayout(button_layout)

    def paintEvent(self, event: object) -> None:
        """Paint the rounded bubble body and its lower pointer triangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#cbd5e1"), 1))

        width = self.width()
        height = self.height()
        triangle_height = self._scaled(10)
        body_rect = QRect(1, 1, width - 2, height - triangle_height - 2)

        gradient = QLinearGradient(0, 0, 0, body_rect.height())
        gradient.setColorAt(0, QColor("#ffffff"))
        gradient.setColorAt(1, QColor("#f8fafc"))
        painter.setBrush(gradient)

        path = QPainterPath()
        radius = self._scaled(12)
        path.addRoundedRect(QRectF(body_rect), radius, radius)
        painter.drawPath(path)

        triangle_center = min(max(self._scaled(28), width // 2), width - self._scaled(28))
        triangle = QPolygon(
            [
                QPoint(triangle_center - self._scaled(9), height - triangle_height - 1),
                QPoint(triangle_center + self._scaled(9), height - triangle_height - 1),
                QPoint(triangle_center, height - 1),
            ]
        )
        painter.drawPolygon(triangle)
        super().paintEvent(event)

    def showEvent(self, event: object) -> None:
        """Start fade-in animation and auto-close timer when shown."""
        self.setWindowOpacity(0.0)
        self._fade_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_animation.setDuration(300)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_animation.start()
        self.auto_close_timer.start(self.auto_close_seconds * 1000)
        super().showEvent(event)

    def _finish(self, result: str) -> None:
        """Emit the selected result and close the bubble."""
        self.auto_close_timer.stop()
        self.result_selected.emit(self.word_info, result)
        self.close()

    def _smart_position(self) -> None:
        """Place the bubble beside the pet while keeping it on screen."""
        self.reposition(self.pet_rect)

    def reposition(self, pet_rect: QRect) -> None:
        """Reposition the bubble beside a new pet window rectangle."""
        self.pet_rect = pet_rect
        screen = QApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        margin = self._scaled(8)
        bubble_width = min(max(self.sizeHint().width(), self.min_width), self.max_width)
        bubble_height = self.sizeHint().height()
        self.resize(bubble_width, bubble_height)

        x = self.pet_rect.right() + margin
        y = self.pet_rect.top() + self._scaled(10)

        if x + bubble_width > available.right():
            x = self.pet_rect.left() - bubble_width - margin
        if y + bubble_height > available.bottom():
            y = available.bottom() - bubble_height - margin
        if y < available.top():
            y = available.top() + margin
        if x < available.left():
            x = available.left() + margin

        self.move(x, y)

    def _scaled(self, value: int) -> int:
        """Scale a pixel or font value according to pet size."""
        return max(1, int(round(value * self.scale)))
