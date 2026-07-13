"""Learning statistics window."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
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
        self.setMinimumSize(560, 660)
        self.setWindowFlags(Qt.Window)
        self._cards: Dict[str, QLabel] = {}
        self._today_progress = QProgressBar()
        self._today_progress_label = QLabel()
        self._search_edit = QLineEdit()
        self._recent_title = QLabel()
        self._weak_title = QLabel()
        self._weak_words_container = QWidget()
        self._weak_words_layout = QVBoxLayout(self._weak_words_container)
        self._weak_words_layout.setContentsMargins(0, 0, 0, 0)
        self._weak_words_layout.setSpacing(8)
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
                background: #f4f6fa;
                color: #111827;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#Title {
                font-size: 22px;
                font-weight: 700;
                color: #1f2937;
            }
            QLabel#Subtitle {
                color: #64748b;
            }
            QFrame#Card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QLabel#CardValue {
                font-size: 24px;
                font-weight: 700;
                color: #1d4ed8;
            }
            QLabel#CardLabel {
                color: #64748b;
            }
            QFrame#ProgressPanel {
                background: #ffffff;
                border: 1px solid #dbeafe;
                border-radius: 8px;
            }
            QFrame#WeakPanel {
                background: #fffaf3;
                border: 1px solid #fed7aa;
                border-radius: 8px;
            }
            QLabel#ProgressTitle {
                color: #1e3a8a;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#ProgressText {
                color: #475569;
                font-weight: 600;
            }
            QProgressBar {
                background: #e5e7eb;
                border: none;
                border-radius: 5px;
                height: 10px;
            }
            QProgressBar::chunk {
                background: #2563eb;
                border-radius: 5px;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
            QFrame#RecordItem {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#Primary {
                background: #2563eb;
                color: #ffffff;
            }
            QPushButton#Primary:hover {
                background: #1d4ed8;
            }
            QPushButton#Secondary {
                background: #e5e7eb;
                color: #111827;
            }
            QPushButton#Secondary:hover {
                background: #d1d5db;
            }
            QPushButton#Danger {
                background: #fee2e2;
                color: #b91c1c;
            }
            QPushButton#Danger:hover {
                background: #fecaca;
            }
            QScrollArea {
                background: transparent;
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
        refresh_button.setObjectName("Primary")
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)
        export_button = QPushButton("导出 CSV")
        export_button.setObjectName("Secondary")
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.clicked.connect(self._export_csv)
        reset_button = QPushButton("重置记录")
        reset_button.setObjectName("Danger")
        reset_button.setCursor(Qt.PointingHandCursor)
        reset_button.clicked.connect(self._reset_records)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(export_button)
        header.addWidget(reset_button)
        header.addWidget(refresh_button)
        root.addLayout(header)

        search_row = QHBoxLayout()
        search_label = QLabel("搜索")
        search_label.setObjectName("ProgressTitle")
        self._search_edit.setPlaceholderText("搜索单词、释义、例句、日期或结果")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self.refresh)
        search_row.addWidget(search_label)
        search_row.addWidget(self._search_edit, 1)
        root.addLayout(search_row)

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
                ("weak_words", "错词数量"),
            ]
        ):
            row, column = divmod(index, 3)
            cards.addWidget(self._create_stat_card(key, label), row, column)
        root.addLayout(cards)

        progress_panel = QFrame()
        progress_panel.setObjectName("ProgressPanel")
        progress_layout = QVBoxLayout(progress_panel)
        progress_layout.setContentsMargins(14, 12, 14, 12)
        progress_layout.setSpacing(8)
        progress_header = QHBoxLayout()
        progress_title = QLabel("今日目标")
        progress_title.setObjectName("ProgressTitle")
        self._today_progress_label.setObjectName("ProgressText")
        progress_header.addWidget(progress_title)
        progress_header.addStretch(1)
        progress_header.addWidget(self._today_progress_label)
        self._today_progress.setRange(0, 100)
        self._today_progress.setTextVisible(False)
        progress_layout.addLayout(progress_header)
        progress_layout.addWidget(self._today_progress)
        root.addWidget(progress_panel)

        weak_panel = QFrame()
        weak_panel.setObjectName("WeakPanel")
        weak_layout = QVBoxLayout(weak_panel)
        weak_layout.setContentsMargins(14, 12, 14, 12)
        weak_layout.setSpacing(8)
        weak_header = QHBoxLayout()
        self._weak_title.setText("错词本")
        self._weak_title.setObjectName("ProgressTitle")
        self._weak_words_label = QLabel("0 个")
        self._weak_words_label.setObjectName("ProgressText")
        weak_header.addWidget(self._weak_title)
        weak_header.addStretch(1)
        weak_header.addWidget(self._weak_words_label)
        weak_layout.addLayout(weak_header)
        weak_layout.addWidget(self._weak_words_container)
        root.addWidget(weak_panel)

        self._recent_title.setText("最近记录")
        recent_title_font = QFont()
        recent_title_font.setPointSize(15)
        recent_title_font.setBold(True)
        self._recent_title.setFont(recent_title_font)
        root.addWidget(self._recent_title)

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
        query = self._search_edit.text().strip()
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
        weak_words = self.word_manager.get_weak_words(limit=5, query=query)
        weak_count = self.word_manager.get_weak_word_count(query=query)
        self._cards["weak_words"].setText(str(weak_count))
        percent = min(int(today["total"] / max(daily_goal, 1) * 100), 100)
        self._today_progress.setValue(percent)
        self._today_progress_label.setText(f"{today['total']} / {daily_goal}")
        self._weak_words_label.setText(f"{weak_count} 个")
        self._weak_title.setText("错词本" if not query else f"错词本 · {weak_count} 个")
        records = self.word_manager.get_recent_records(query=query)
        self._recent_title.setText("最近记录" if not query else f"最近记录 · {len(records)} 条")
        self._render_weak_words(
            weak_words,
            empty_message="暂无错词，继续保持！" if not query else "没有匹配的错词。",
        )
        self._render_records(
            records,
            empty_message=(
                "还没有学习记录。完成一次气泡操作后，这里会显示历史。"
                if not query
                else "没有匹配的学习记录。"
            ),
        )

    def _render_weak_words(
        self,
        words: List[Dict[str, object]],
        empty_message: str,
    ) -> None:
        """Render the currently weak words."""
        while self._weak_words_layout.count():
            item = self._weak_words_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not words:
            empty = QLabel(empty_message)
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "background: #ffffff; border: 1px solid #fde68a; "
                "border-radius: 8px; color: #92400e; padding: 18px;"
            )
            self._weak_words_layout.addWidget(empty)
            self._weak_words_layout.addStretch(1)
            return

        for word in words:
            self._weak_words_layout.addWidget(self._create_weak_word_item(word))
        self._weak_words_layout.addStretch(1)

    def _create_weak_word_item(self, word: Dict[str, object]) -> QFrame:
        """Create one weak-word summary row."""
        item = QFrame()
        item.setObjectName("RecordItem")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        word_box = QVBoxLayout()
        title_row = QHBoxLayout()
        title = QLabel(str(word["word"]))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        badge = QLabel("错词")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "background: #fee2e2; border-radius: 6px; color: #b91c1c; "
            "font-weight: 700; padding: 4px 8px;"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch(1)

        meaning = QLabel(str(word["meaning"]))
        meaning.setWordWrap(True)
        meaning.setStyleSheet("color: #4b5563;")
        meta = QLabel(
            f"错 {int(word['again_count'])} 次 · 记住 {int(word['remembered_count'])} 次"
        )
        meta.setStyleSheet("color: #b45309; font-weight: 600;")
        last_reviewed_at = str(word.get("last_reviewed_at", "")).replace("T", " ")
        time_label = QLabel(f"最近出现: {last_reviewed_at}")
        time_label.setStyleSheet("color: #6b7280;")

        word_box.addLayout(title_row)
        word_box.addWidget(meaning)
        word_box.addWidget(meta)
        word_box.addWidget(time_label)

        layout.addLayout(word_box, 1)
        return item

    def _render_records(
        self,
        records: List[Dict[str, object]],
        empty_message: str,
    ) -> None:
        """Render recent learning record rows."""
        while self._records_layout.count():
            item = self._records_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not records:
            empty = QLabel(empty_message)
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                "background: #ffffff; border: 1px solid #e5e7eb; "
                "border-radius: 8px; color: #64748b; padding: 24px;"
            )
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
            "background: #dcfce7; border-radius: 6px; color: #15803d; "
            "font-weight: 700; padding: 5px 8px;"
            if record["result"] == "remembered"
            else "background: #fee2e2; border-radius: 6px; color: #b91c1c; "
            "font-weight: 700; padding: 5px 8px;"
        )
        time_label = QLabel(str(record["reviewed_at"]).replace("T", " "))
        time_label.setStyleSheet("color: #6b7280;")
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addLayout(word_box, 1)
        layout.addWidget(result)
        layout.addWidget(time_label)
        return item

    def _export_csv(self) -> None:
        """Export learning records to a user-selected CSV file."""
        default_name = f"desktoppet-records-{datetime.now():%Y%m%d-%H%M%S}.csv"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "导出学习记录",
            str(Path.home() / default_name),
            "CSV Files (*.csv)",
        )
        if not file_name:
            return
        try:
            count = self.word_manager.export_records_csv(Path(file_name))
        except OSError as exc:
            QMessageBox.critical(self, "DesktopPet", f"导出失败：{exc}")
            return
        QMessageBox.information(self, "DesktopPet", f"已导出 {count} 条学习记录。")

    def _reset_records(self) -> None:
        """Reset local learning records after confirmation."""
        result = QMessageBox.question(
            self,
            "DesktopPet",
            "确定要清空本地学习记录吗？词库不会被删除。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return
        self.word_manager.reset_learning_records()
        self.refresh()
        QMessageBox.information(self, "DesktopPet", "本地学习记录已清空。")

    def show_and_refresh(self) -> None:
        """Refresh and show the window."""
        self.refresh()
        self.show()
        self.raise_()
        self.activateWindow()
