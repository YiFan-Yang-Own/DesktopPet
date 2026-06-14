"""System tray icon and menu management."""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path

from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QDialog,
    QFileDialog,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from core.config_manager import ConfigManager
from core.interval_dialog import IntervalDialog
from core.pet_window import PetWindow
from core.scheduler import Scheduler
from core.settings_window import SettingsWindow
from core.stats_window import StatsWindow
from core.word_manager import WordManager


LOGGER = logging.getLogger(__name__)


class TrayManager:
    """Create and coordinate the DesktopPet tray icon and menu."""

    def __init__(
        self,
        config_manager: ConfigManager,
        scheduler: Scheduler,
        word_manager: WordManager,
        pet_window: PetWindow,
    ) -> None:
        """Initialize tray icon, menus, and actions."""
        self.config_manager = config_manager
        self.scheduler = scheduler
        self.word_manager = word_manager
        self.pet_window = pet_window
        self.stats_window = StatsWindow(config_manager, word_manager)
        self.settings_window = SettingsWindow(
            config_manager,
            self._apply_settings,
            Path(__file__).resolve().parents[1],
        )

        self.tray_icon = QSystemTrayIcon(self._load_icon())
        self.tray_icon.setToolTip("DesktopPet")
        self.menu = QMenu()

        self.pause_action = QAction("暂停提醒", self.menu)
        self.pause_action.triggered.connect(self._toggle_pause)

        self.review_now_action = QAction("立即复习", self.menu)
        self.review_now_action.triggered.connect(self.scheduler.trigger_reminder)

        self.stats_action = QAction("学习记录", self.menu)
        self.stats_action.triggered.connect(self.stats_window.show_and_refresh)

        self.settings_action = QAction("设置", self.menu)
        self.settings_action.triggered.connect(self.settings_window.show)

        self.reset_position_action = QAction("重置桌宠位置", self.menu)
        self.reset_position_action.triggered.connect(self._reset_pet_position)

        self.quit_action_top = QAction("退出程序", self.menu)
        self.quit_action_top.triggered.connect(self._quit_application)

        self.quit_action_bottom = QAction("退出程序", self.menu)
        self.quit_action_bottom.triggered.connect(self._quit_application)

        self.word_group = QActionGroup(self.menu)
        self.word_group.setExclusive(True)
        self.interval_group = QActionGroup(self.menu)
        self.interval_group.setExclusive(True)

        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._handle_activation)
        self.pet_window.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pet_window.customContextMenuRequested.connect(self._show_pet_context_menu)

    def show(self) -> None:
        """Show the tray icon."""
        self.tray_icon.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        self.tray_icon.hide()

    def show_daily_goal_notification(self) -> None:
        """Display a tray notification for completing the daily target."""
        self.tray_icon.showMessage(
            "DesktopPet",
            "今日目标已完成！",
            QSystemTrayIcon.Information,
            3000,
        )

    def _build_menu(self) -> None:
        """Build all tray menu entries."""
        self.menu.clear()
        self.menu.addAction(self.quit_action_top)
        self.menu.addSeparator()
        self.menu.addAction(self.pause_action)
        self.menu.addAction(self.review_now_action)
        self.menu.addAction(self.stats_action)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.reset_position_action)
        self.menu.addSeparator()

        word_menu = self.menu.addMenu("词库选择")
        for label, file_name in self._word_library_actions().items():
            action = QAction(label, word_menu)
            action.setCheckable(True)
            action.setData(file_name)
            action.setChecked(self.config_manager.get("word_lib") == file_name)
            action.triggered.connect(
                lambda checked, name=file_name: self._set_word_lib(name)
            )
            self.word_group.addAction(action)
            word_menu.addAction(action)
        word_menu.addSeparator()
        import_word_lib_action = QAction("导入词库...", word_menu)
        import_word_lib_action.triggered.connect(self._import_word_library)
        word_menu.addAction(import_word_lib_action)

        interval_menu = self.menu.addMenu("设置提醒间隔")
        for label, minutes in {
            "15分钟": 15,
            "30分钟": 30,
            "1小时": 60,
            "2小时": 120,
        }.items():
            action = QAction(label, interval_menu)
            action.setCheckable(True)
            action.setData(minutes)
            action.setChecked(
                int(self.config_manager.get("reminder_interval_minutes", 30)) == minutes
            )
            action.triggered.connect(
                lambda checked, value=minutes: self._set_interval(value)
            )
            self.interval_group.addAction(action)
            interval_menu.addAction(action)
        interval_menu.addSeparator()
        custom_action = QAction("自定义...", interval_menu)
        custom_action.triggered.connect(self._set_custom_interval)
        interval_menu.addAction(custom_action)

        self.menu.addSeparator()
        self.menu.addAction(self.quit_action_bottom)

    def _load_icon(self) -> QIcon:
        """Load tray icon or generate a fallback icon."""
        icon_path = Path(__file__).resolve().parents[1] / "resources" / "icons" / "icon.png"
        if icon_path.exists():
            return QIcon(str(icon_path))

        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#ffffff"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor("#4f8cff"))
        painter.setPen(QColor("#1f3b73"))
        painter.drawEllipse(8, 8, 48, 48)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(24, 24, 6, 6)
        painter.drawEllipse(36, 24, 6, 6)
        painter.end()
        LOGGER.warning("icon.png not found; using built-in fallback tray icon")
        return QIcon(pixmap)

    def _toggle_pause(self) -> None:
        """Pause or resume reminders from the tray menu."""
        if self.scheduler.paused:
            self.scheduler.resume()
            self.pause_action.setText("暂停提醒")
        else:
            self.scheduler.pause()
            self.pause_action.setText("恢复提醒")

    def _set_word_lib(self, file_name: str) -> None:
        """Update selected word library and refresh word storage."""
        self.config_manager.set("word_lib", file_name)
        self.word_manager.refresh_word_library()
        self._build_menu()
        LOGGER.info("Word library changed to %s", file_name)

    def _import_word_library(self) -> None:
        """Import a JSON word library into the local wordlib directory."""
        file_name, _ = QFileDialog.getOpenFileName(
            None,
            "导入词库",
            str(Path.home()),
            "JSON Files (*.json)",
        )
        if not file_name:
            return

        source = Path(file_name)
        try:
            words = json.loads(source.read_text(encoding="utf-8"))
            self._validate_word_library(words)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            QMessageBox.critical(None, "DesktopPet", f"词库格式无效：{exc}")
            return

        wordlib_dir = Path(__file__).resolve().parents[1] / "data" / "wordlib"
        wordlib_dir.mkdir(parents=True, exist_ok=True)
        safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", source.stem).strip("_") or "wordlib"
        target = wordlib_dir / f"custom_{safe_stem}.json"
        index = 1
        while target.exists():
            target = wordlib_dir / f"custom_{safe_stem}_{index}.json"
            index += 1

        try:
            shutil.copy2(source, target)
        except OSError as exc:
            QMessageBox.critical(None, "DesktopPet", f"复制词库失败：{exc}")
            return

        self._set_word_lib(target.name)
        QMessageBox.information(None, "DesktopPet", f"已导入词库：{target.name}")

    @staticmethod
    def _validate_word_library(words: object) -> None:
        """Validate the minimal JSON schema for a word library."""
        if not isinstance(words, list):
            raise ValueError("顶层必须是 JSON 数组")
        if not words:
            raise ValueError("词库不能为空")
        for index, item in enumerate(words, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"第 {index} 项不是对象")
            if not str(item.get("word", "")).strip():
                raise ValueError(f"第 {index} 项缺少 word")
            if not str(item.get("meaning", "")).strip():
                raise ValueError(f"第 {index} 项缺少 meaning")

    @staticmethod
    def _word_library_actions() -> dict[str, str]:
        """Return built-in and local word libraries for the menu."""
        wordlib_dir = Path(__file__).resolve().parents[1] / "data" / "wordlib"
        actions = {
            "CET4": "cet4.json",
            "CET6": "cet6.json",
            "考研": "postgraduate.json",
        }
        for path in sorted(wordlib_dir.glob("custom_*.json")):
            actions[path.stem.replace("custom_", "", 1)] = path.name
        return actions

    def _set_interval(self, minutes: int) -> None:
        """Update reminder interval and restart scheduler timer."""
        self.config_manager.set("reminder_interval_minutes", minutes)
        self.config_manager.set("reminder_interval_seconds", minutes * 60)
        self.scheduler.update_interval()
        LOGGER.info("Reminder interval changed to %s minutes", minutes)

    def _set_custom_interval(self) -> None:
        """Show a custom hours/minutes/seconds interval dialog."""
        current_seconds = int(
            self.config_manager.get(
                "reminder_interval_seconds",
                int(self.config_manager.get("reminder_interval_minutes", 30)) * 60,
            )
        )
        dialog = IntervalDialog(current_seconds)
        if dialog.exec_() != QDialog.Accepted:
            return
        seconds = dialog.total_seconds()
        self.config_manager.set("reminder_interval_seconds", seconds)
        self.config_manager.set("reminder_interval_minutes", max(seconds // 60, 1))
        self.scheduler.update_interval()
        LOGGER.info("Custom reminder interval changed to %s seconds", seconds)

    def _apply_settings(self) -> None:
        """Apply settings changed from the settings window."""
        self.scheduler.update_interval()
        self.pet_window.apply_settings()

    def _reset_pet_position(self) -> None:
        """Reset the pet position to the lower-right corner."""
        self.config_manager.set("pet.x", None)
        self.config_manager.set("pet.y", None)
        self.pet_window._move_to_bottom_right()

    def _show_pet_context_menu(self, position: object) -> None:
        """Show the tray menu when right-clicking the pet."""
        self.menu.popup(self.pet_window.mapToGlobal(position))

    def _handle_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Toggle pet visibility when the tray icon is clicked."""
        if reason == QSystemTrayIcon.Trigger:
            if self.pet_window.isVisible():
                self.pet_window.hide()
            else:
                self.pet_window.show()

    @staticmethod
    def _quit_application() -> None:
        """Quit the current Qt application."""
        QApplication.quit()
