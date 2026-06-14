"""Application settings window."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
)

from core.config_manager import ConfigManager
from core.interval_dialog import IntervalDialog


class SettingsWindow(QDialog):
    """A unified settings dialog for reminder and pet behavior."""

    def __init__(
        self,
        config_manager: ConfigManager,
        on_apply: Callable[[], None],
        base_dir: Path,
    ) -> None:
        """Create a settings window."""
        super().__init__()
        self.config_manager = config_manager
        self.on_apply = on_apply
        self.base_dir = base_dir
        self.setWindowTitle("DesktopPet 设置")
        self.setMinimumWidth(460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.interval_seconds = int(
            self.config_manager.get(
                "reminder_interval_seconds",
                int(self.config_manager.get("reminder_interval_minutes", 30)) * 60,
            )
        )
        self.interval_label = QLabel()
        self.daily_goal_spin = self._spin(1, 999, int(self.config_manager.get("daily_goal", 20)))
        self.bubble_duration_spin = self._spin(
            1,
            60,
            int(self.config_manager.get("bubble_duration_seconds", 5)),
        )
        self.pet_size_spin = self._spin(120, 880, int(self.config_manager.get("pet.size", 200)))
        self.pet_opacity_spin = self._spin(
            20,
            100,
            int(self.config_manager.get("pet.opacity", 100)),
        )
        self.pet_asset_label = QLabel()
        self.pet_asset_label.setWordWrap(True)
        self.pet_always_on_top_check = QCheckBox("桌宠始终置顶")
        self.pet_always_on_top_check.setChecked(
            bool(self.config_manager.get("pet.always_on_top", True))
        )
        self.pet_click_to_review_check = QCheckBox("点击桌宠立即复习")
        self.pet_click_to_review_check.setChecked(
            bool(self.config_manager.get("pet.click_to_review", True))
        )
        self.startup_reminder_check = QCheckBox("启动后自动弹出一个单词")
        self.startup_reminder_check.setChecked(
            bool(self.config_manager.get("startup_reminder", True))
        )
        self.quiet_enabled_check = QCheckBox("启用夜间免打扰")
        self.quiet_enabled_check.setChecked(
            bool(self.config_manager.get("quiet_hours.enabled", True))
        )
        self.quiet_start_edit = self._time_edit(str(self.config_manager.get("quiet_hours.start", "22:00")))
        self.quiet_end_edit = self._time_edit(str(self.config_manager.get("quiet_hours.end", "08:00")))
        self._build_ui()
        self._update_interval_label()

    def _build_ui(self) -> None:
        """Build settings controls."""
        self.setStyleSheet(
            """
            QDialog {
                background: #f8fafc;
                color: #111827;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QSpinBox, QTimeEdit {
                min-height: 30px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 3px 8px;
                background: #ffffff;
            }
            QPushButton {
                border: none;
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: 700;
            }
            QPushButton#Primary {
                background: #2563eb;
                color: #ffffff;
            }
            QPushButton#Secondary {
                background: #e5e7eb;
                color: #111827;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        reminder_group = QGroupBox("提醒")
        reminder_form = QFormLayout(reminder_group)
        interval_row = QHBoxLayout()
        interval_button = QPushButton("调整...")
        interval_button.setObjectName("Secondary")
        interval_button.clicked.connect(self._edit_interval)
        interval_row.addWidget(self.interval_label, 1)
        interval_row.addWidget(interval_button)
        reminder_form.addRow("提醒间隔", interval_row)
        reminder_form.addRow("每日目标", self.daily_goal_spin)
        reminder_form.addRow("气泡停留秒数", self.bubble_duration_spin)
        reminder_form.addRow("", self.startup_reminder_check)
        root.addWidget(reminder_group)

        pet_group = QGroupBox("桌宠")
        pet_form = QFormLayout(pet_group)
        pet_form.addRow("桌宠大小", self.pet_size_spin)
        pet_form.addRow("透明度", self.pet_opacity_spin)
        pet_form.addRow("", self.pet_always_on_top_check)
        pet_form.addRow("", self.pet_click_to_review_check)
        pet_asset_row = QHBoxLayout()
        choose_pet_button = QPushButton("选择图片...")
        choose_pet_button.setObjectName("Secondary")
        choose_pet_button.clicked.connect(self._choose_pet_asset)
        reset_pet_button = QPushButton("恢复默认")
        reset_pet_button.setObjectName("Secondary")
        reset_pet_button.clicked.connect(self._reset_pet_asset)
        pet_asset_row.addWidget(self.pet_asset_label, 1)
        pet_asset_row.addWidget(choose_pet_button)
        pet_asset_row.addWidget(reset_pet_button)
        pet_form.addRow("桌宠图片", pet_asset_row)
        root.addWidget(pet_group)

        quiet_group = QGroupBox("免打扰")
        quiet_form = QFormLayout(quiet_group)
        quiet_form.addRow("", self.quiet_enabled_check)
        quiet_form.addRow("开始时间", self.quiet_start_edit)
        quiet_form.addRow("结束时间", self.quiet_end_edit)
        root.addWidget(quiet_group)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("Secondary")
        cancel_button.clicked.connect(self.reject)
        ok_button = QPushButton("确定")
        ok_button.setObjectName("Primary")
        ok_button.clicked.connect(self._save)
        buttons.addWidget(cancel_button)
        buttons.addWidget(ok_button)
        root.addLayout(buttons)
        self._update_pet_asset_label()

    def _choose_pet_asset(self) -> None:
        """Copy a selected pet image into the project resource directory."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择桌宠图片",
            str(Path.home()),
            "Images (*.gif *.png *.jpg *.jpeg)",
        )
        if not file_name:
            return

        source = Path(file_name)
        suffix = source.suffix.lower()
        if suffix not in {".gif", ".png", ".jpg", ".jpeg"}:
            QMessageBox.warning(self, "DesktopPet", "只支持 GIF、PNG 或 JPG 图片。")
            return

        pet_dir = self.base_dir / "resources" / "pets"
        pet_dir.mkdir(parents=True, exist_ok=True)
        target = pet_dir / f"local_pet{suffix}"
        try:
            for old_name in (
                "local_pet.gif",
                "local_pet.png",
                "local_pet.jpg",
                "local_pet.jpeg",
            ):
                old_path = pet_dir / old_name
                if old_path.exists() and old_path != target:
                    old_path.unlink()
            shutil.copy2(source, target)
        except OSError as exc:
            QMessageBox.critical(self, "DesktopPet", f"复制图片失败：{exc}")
            return

        self._update_pet_asset_label()
        self.on_apply()

    def _reset_pet_asset(self) -> None:
        """Remove local override pet assets while keeping the committed default."""
        pet_dir = self.base_dir / "resources" / "pets"
        removed = False
        for old_name in (
            "local_pet.gif",
            "local_pet.png",
            "local_pet.jpg",
            "local_pet.jpeg",
        ):
            old_path = pet_dir / old_name
            if old_path.exists():
                old_path.unlink()
                removed = True
        if removed:
            self._update_pet_asset_label()
            self.on_apply()

    def _edit_interval(self) -> None:
        """Open the wheel-style interval dialog."""
        dialog = IntervalDialog(self.interval_seconds)
        if dialog.exec_() == QDialog.Accepted:
            self.interval_seconds = dialog.total_seconds()
            self._update_interval_label()

    def _save(self) -> None:
        """Save settings and notify the application."""
        self.config_manager.set("reminder_interval_seconds", self.interval_seconds)
        self.config_manager.set("reminder_interval_minutes", max(self.interval_seconds // 60, 1))
        self.config_manager.set("daily_goal", self.daily_goal_spin.value())
        self.config_manager.set("bubble_duration_seconds", self.bubble_duration_spin.value())
        self.config_manager.set("pet.size", self.pet_size_spin.value())
        self.config_manager.set("pet.opacity", self.pet_opacity_spin.value())
        self.config_manager.set("pet.always_on_top", self.pet_always_on_top_check.isChecked())
        self.config_manager.set("pet.click_to_review", self.pet_click_to_review_check.isChecked())
        self.config_manager.set("startup_reminder", self.startup_reminder_check.isChecked())
        self.config_manager.set("quiet_hours.enabled", self.quiet_enabled_check.isChecked())
        self.config_manager.set("quiet_hours.start", self.quiet_start_edit.time().toString("HH:mm"))
        self.config_manager.set("quiet_hours.end", self.quiet_end_edit.time().toString("HH:mm"))
        self.on_apply()
        self.accept()

    def _update_interval_label(self) -> None:
        """Refresh the human-readable interval label."""
        hours = self.interval_seconds // 3600
        minutes = (self.interval_seconds % 3600) // 60
        seconds = self.interval_seconds % 60
        self.interval_label.setText(f"{hours:02d} 小时 {minutes:02d} 分钟 {seconds:02d} 秒")

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        """Create a numeric spin box."""
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignCenter)
        return spin

    @staticmethod
    def _time_edit(value: str) -> QTimeEdit:
        """Create a time edit from HH:mm text."""
        time_value = QTime.fromString(value, "HH:mm")
        if not time_value.isValid():
            time_value = QTime(0, 0)
        edit = QTimeEdit(time_value)
        edit.setDisplayFormat("HH:mm")
        return edit

    def _update_pet_asset_label(self) -> None:
        """Show the active pet asset file name."""
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
            if (pet_dir / image_name).exists():
                self.pet_asset_label.setText(image_name)
                return
        self.pet_asset_label.setText("内置兜底")
