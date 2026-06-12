"""Learning statistics window."""

from __future__ import annotations

from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import ConfigManager
from core.word_manager import WordManager


class StatsWindow(QWidget):
    """Display learning progress and recent records."""

    def __init__(self, config_manager: ConfigManager, word_manager: WordManager) -> None:
        """Create the statistics window."""
        super().__init__()
        self.config_manager = config_manager
        self.word_manager = word_manager
        self.setWindowTitle("DesktopPet 学习记录")
        self.setMinimumSize(560, 520)
        self.setWindowFlags(Qt.Window)
        self._cards: Dict[str, QLabel] = {}
        self._records_container = QWidget()
        self._records_layout = QVBoxLayout(self._records_container)
        self._records_layout.setContentsMargins(0, 0, 0, 0)
        self._records_layout.setSpacing(8)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the statistics layout."""
        self.setStyleSheet(
            """
            QWidget {
                background: #f6f7fb;
                color: #202124;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#Title {
                font-size: 22px;
                font-weight: 700;
                color: #1f2937;
            }
            QLabel#Subtitle {
                color: #6b7280;
            }
            QFrame#Card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QLabel#CardValue {
                font-size: 24px;
                font-weight: 700;
                color: #2563eb;
            }
            QLabel#CardLabel {
                color: #6b7280;
            }
            QFrame#RecordItem {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("学习记录")
        title.setObjectName("Title")
        subtitle = QLabel("查看今日进度、累计学习情况和最近复习记录")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        refresh_button = QPushButton("刷新")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(refresh_button)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        for index, (key, label) in enumerate(
            [
                ("today_total", "今日完成"),
                ("today_new", "今日新词"),
                ("today_reviews", "今日复习"),
                ("streak", "连续天数"),
                ("learned", "已学单词"),
                ("due", "待复习"),
            ]
        ):
            row, column = divmod(index, 3)
            cards.addWidget(self._create_stat_card(key, label), row, column)
        root.addLayout(cards)

        recent_title = QLabel("最近记录")
        recent_title_font = QFont()
        recent_title_font.setPointSize(15)
        recent_title_font.setBold(True)
        recent_title.setFont(recent_title_font)
        root.addWidget(recent_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self._records_container)
        root.addWidget(scroll, 1)

    def _create_stat_card(self, key: str, label: str) -> QFrame:
        """Create one statistic card."""
        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumHeight(86)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        value_label = QLabel("0")
        value_label.setObjectName("CardValue")
        text_label = QLabel(label)
        text_label.setObjectName("CardLabel")
        layout.addWidget(value_label)
        layout.addStretch(1)
        layout.addWidget(text_label)
        self._cards[key] = value_label
        return card

    def refresh(self) -> None:
        """Refresh all statistics and recent records."""
        today = self.word_manager.get_today_stats()
        overall = self.word_manager.get_overall_stats()
        daily_goal = int(self.config_manager.get("daily_goal", 20))
        due_count = self.word_manager.get_due_count()
        streak = self.word_manager.get_streak_days()

        self._cards["today_total"].setText(f"{today['total']} / {daily_goal}")
        self._cards["today_new"].setText(str(today["new_words"]))
        self._cards["today_reviews"].setText(str(today["reviews"]))
        self._cards["streak"].setText(f"{streak} 天")
        self._cards["learned"].setText(
            f"{overall['learned_words']} / {overall['total_words']}"
        )
        self._cards["due"].setText(str(due_count))
        self._render_records(self.word_manager.get_recent_records())

    def _render_records(self, records: List[Dict[str, object]]) -> None:
        """Render recent learning record rows."""
        while self._records_layout.count():
            item = self._records_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not records:
            empty = QLabel("还没有学习记录。完成一次气泡操作后，这里会显示历史。")
            empty.setStyleSheet("color: #6b7280; padding: 16px;")
            self._records_layout.addWidget(empty)
            self._records_layout.addStretch(1)
            return

        for record in records:
            self._records_layout.addWidget(self._create_record_item(record))
        self._records_layout.addStretch(1)

    def _create_record_item(self, record: Dict[str, object]) -> QFrame:
        """Create one recent record row."""
        item = QFrame()
        item.setObjectName("RecordItem")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        word_box = QVBoxLayout()
        word = QLabel(str(record["word"]))
        word_font = QFont()
        word_font.setPointSize(14)
        word_font.setBold(True)
        word.setFont(word_font)
        meaning = QLabel(str(record["meaning"]))
        meaning.setWordWrap(True)
        meaning.setStyleSheet("color: #4b5563;")
        word_box.addWidget(word)
        word_box.addWidget(meaning)

        result_text = "记住了" if record["result"] == "remembered" else "再记一次"
        result = QLabel(result_text)
        result.setAlignment(Qt.AlignCenter)
        result.setMinimumWidth(72)
        result.setStyleSheet(
            "color: #16a34a; font-weight: 700;"
            if record["result"] == "remembered"
            else "color: #dc2626; font-weight: 700;"
        )
        time_label = QLabel(str(record["reviewed_at"]).replace("T", " "))
        time_label.setStyleSheet("color: #6b7280;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(word_box, 1)
        layout.addWidget(result)
        layout.addWidget(time_label)
        return item

    def show_and_refresh(self) -> None:
        """Refresh and show the window."""
        self.refresh()
        self.show()
        self.raise_()
        self.activateWindow()
