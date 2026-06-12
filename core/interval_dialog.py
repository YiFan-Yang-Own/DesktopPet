"""Custom reminder interval dialog."""

from __future__ import annotations

from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class IntervalDialog(QDialog):
    """A wheel-style dialog for setting hours, minutes, and seconds."""

    def __init__(self, total_seconds: int) -> None:
        """Create the dialog with the current interval preselected."""
        super().__init__()
        self.setWindowTitle("设置提醒间隔")
        self.setFixedWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        hours, minutes, seconds = self._split_seconds(total_seconds)
        self.hours_spin = self._create_spin(0, 23, hours)
        self.minutes_spin = self._create_spin(0, 59, minutes)
        self.seconds_spin = self._create_spin(0, 59, seconds)
        self._build_ui()

    def total_seconds(self) -> int:
        """Return the selected interval in seconds."""
        value = (
            self.hours_spin.value() * 3600
            + self.minutes_spin.value() * 60
            + self.seconds_spin.value()
        )
        return max(value, 1)

    def _build_ui(self) -> None:
        """Build the dialog widgets."""
        self.setStyleSheet(
            """
            QDialog {
                background: #f8fafc;
                color: #111827;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            QLabel#Title {
                font-size: 18px;
                font-weight: 700;
            }
            QSpinBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px;
                font-size: 18px;
                min-height: 42px;
            }
            QPushButton {
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-weight: 700;
            }
            QPushButton#OkButton {
                background: #2563eb;
                color: #ffffff;
            }
            QPushButton#CancelButton {
                background: #e5e7eb;
                color: #111827;
            }
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        title = QLabel("提醒间隔")
        title.setObjectName("Title")
        root.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        for column, (label, spin) in enumerate(
            [
                ("小时", self.hours_spin),
                ("分钟", self.minutes_spin),
                ("秒", self.seconds_spin),
            ]
        ):
            text = QLabel(label)
            text.setAlignment(Qt.AlignCenter)
            grid.addWidget(spin, 0, column)
            grid.addWidget(text, 1, column)
        root.addLayout(grid)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("CancelButton")
        cancel_button.clicked.connect(self.reject)
        ok_button = QPushButton("确定")
        ok_button.setObjectName("OkButton")
        ok_button.clicked.connect(self.accept)
        buttons.addWidget(cancel_button)
        buttons.addWidget(ok_button)
        root.addLayout(buttons)

    @staticmethod
    def _create_spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        """Create one wheel-enabled spin box."""
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignCenter)
        spin.setButtonSymbols(QSpinBox.PlusMinus)
        spin.setAccelerated(True)
        return spin

    @staticmethod
    def _split_seconds(total_seconds: int) -> Tuple[int, int, int]:
        """Split seconds into hours, minutes, and seconds."""
        total_seconds = max(int(total_seconds), 1)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return min(hours, 23), minutes, seconds
