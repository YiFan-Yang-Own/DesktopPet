"""Application settings window."""

from __future__ import annotations

import shutil
import zipfile
from datetime import datetime
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
from core import startup_manager


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
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.interval_seconds = int(
            self.config_manager.get(
                "reminder_interval_seconds",
                int(self.config_manager.get("reminder_interval_minutes", 30)) * 60,
            )
        )
        self.interval_label = QLabel()
        self.daily_goal_spin = self._spin(1, 999, int(self.config_manager.get("daily_goal", 20)))
        self.daily_goal_spin.setFixedWidth(150)
        self.bubble_duration_spin = self._spin(
            1,
            60,
            int(self.config_manager.get("bubble_duration_seconds", 5)),
        )
        self.bubble_duration_spin.setFixedWidth(150)
        self.pet_size_spin = self._spin(120, 880, int(self.config_manager.get("pet.size", 200)))
        self.pet_size_spin.setFixedWidth(150)
        self.pet_opacity_spin = self._spin(
            20,
            100,
            int(self.config_manager.get("pet.opacity", 100)),
        )
        self.pet_opacity_spin.setFixedWidth(150)
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
        self.launch_at_login_check = QCheckBox("开机自动启动")
        self.launch_at_login_check.setChecked(startup_manager.is_enabled())
        self.launch_at_login_check.setEnabled(startup_manager.is_supported())
        self.quiet_enabled_check = QCheckBox("启用夜间免打扰")
        self.quiet_enabled_check.setChecked(
            bool(self.config_manager.get("quiet_hours.enabled", True))
        )
        self.quiet_start_edit = self._time_edit(str(self.config_manager.get("quiet_hours.start", "22:00")))
        self.quiet_end_edit = self._time_edit(str(self.config_manager.get("quiet_hours.end", "08:00")))
        self.quiet_start_edit.setFixedWidth(150)
        self.quiet_end_edit.setFixedWidth(150)
        self.backup_hint_label = QLabel(
            "备份会包含本地配置、学习记录、导入词库和本地桌宠图片。"
        )
        self.backup_hint_label.setWordWrap(True)
        self._build_ui()
        self._update_interval_label()

    def _build_ui(self) -> None:
        """Build settings controls."""
        self.setStyleSheet(
            """
            QDialog {
                background: #f4f6fa;
                color: #111827;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 14px;
                padding: 14px 12px 12px 12px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #374151;
            }
            QSpinBox, QTimeEdit {
                min-height: 30px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 3px 8px;
                background: #ffffff;
            }
            QSpinBox:focus, QTimeEdit:focus {
                border-color: #2563eb;
            }
            QCheckBox {
                spacing: 8px;
                color: #374151;
            }
            QLabel#BackupHint {
                color: #64748b;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
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
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        reminder_group = QGroupBox("提醒")
        reminder_form = QFormLayout(reminder_group)
        reminder_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        reminder_form.setHorizontalSpacing(14)
        reminder_form.setVerticalSpacing(10)
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
        reminder_form.addRow("", self.launch_at_login_check)
        root.addWidget(reminder_group)

        pet_group = QGroupBox("桌宠")
        pet_form = QFormLayout(pet_group)
        pet_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pet_form.setHorizontalSpacing(14)
        pet_form.setVerticalSpacing(10)
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
        quiet_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        quiet_form.setHorizontalSpacing(14)
        quiet_form.setVerticalSpacing(10)
        quiet_form.addRow("", self.quiet_enabled_check)
        quiet_form.addRow("开始时间", self.quiet_start_edit)
        quiet_form.addRow("结束时间", self.quiet_end_edit)
        root.addWidget(quiet_group)

        data_group = QGroupBox("数据")
        data_form = QFormLayout(data_group)
        data_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        data_form.setHorizontalSpacing(14)
        data_form.setVerticalSpacing(10)
        self.backup_hint_label.setObjectName("BackupHint")
        backup_row = QHBoxLayout()
        backup_button = QPushButton("备份数据")
        backup_button.setObjectName("Secondary")
        backup_button.clicked.connect(self._backup_data)
        restore_button = QPushButton("恢复数据")
        restore_button.setObjectName("Secondary")
        restore_button.clicked.connect(self._restore_data)
        backup_row.addWidget(backup_button)
        backup_row.addWidget(restore_button)
        backup_row.addStretch(1)
        data_form.addRow("", self.backup_hint_label)
        data_form.addRow("数据备份", backup_row)
        root.addWidget(data_group)

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

    def _backup_data(self) -> None:
        """Export local configuration, learning data, and custom assets into a zip file."""
        default_name = f"desktoppet-backup-{datetime.now():%Y%m%d-%H%M%S}.zip"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "备份数据",
            str(Path.home() / default_name),
            "Zip Files (*.zip)",
        )
        if not file_name:
            return

        backup_path = Path(file_name)
        if backup_path.suffix.lower() != ".zip":
            backup_path = backup_path.with_suffix(".zip")

        try:
            count = self._write_backup_archive(backup_path)
        except OSError as exc:
            QMessageBox.critical(self, "DesktopPet", f"备份失败：{exc}")
            return

        QMessageBox.information(
            self,
            "DesktopPet",
            f"已备份 {count} 个文件到：{backup_path}",
        )

    def _restore_data(self) -> None:
        """Import local configuration, learning data, and custom assets from a zip file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "恢复数据",
            str(Path.home()),
            "Zip Files (*.zip)",
        )
        if not file_name:
            return

        archive_path = Path(file_name)
        try:
            restored_count = self._restore_backup_archive(archive_path)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            QMessageBox.critical(self, "DesktopPet", f"恢复失败：{exc}")
            return

        QMessageBox.information(
            self,
            "DesktopPet",
            "已恢复 "
            f"{restored_count} 个文件。请重启程序以重新加载配置和学习记录。",
        )

    def _write_backup_archive(self, backup_path: Path) -> int:
        """Write a zip archive with all local user data files."""
        entries = self._backup_entries()
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for source, arcname in entries:
                if source.exists():
                    archive.write(source, arcname)
                    written += 1
        return written

    def _restore_backup_archive(self, archive_path: Path) -> int:
        """Restore a zip archive into the project workspace."""
        restored = 0
        allowed_roots = {
            "config.local.yaml",
            "data/user_data.db",
            "data/wordlib/",
            "resources/pets/",
        }

        with zipfile.ZipFile(archive_path, "r") as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                member_name = Path(member.filename).as_posix()
                if not self._is_allowed_backup_member(member_name, allowed_roots):
                    continue

                target = self.base_dir / Path(member_name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member, "r") as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
                restored += 1

        if restored == 0:
            raise ValueError("备份包里没有可恢复的数据文件")
        return restored

    def _backup_entries(self) -> list[tuple[Path, str]]:
        """Return the files that should be included in a backup archive."""
        entries: list[tuple[Path, str]] = [
            (self.base_dir / "config.local.yaml", "config.local.yaml"),
            (self.base_dir / "data" / "user_data.db", "data/user_data.db"),
        ]

        wordlib_dir = self.base_dir / "data" / "wordlib"
        for path in sorted(wordlib_dir.glob("custom_*.json")):
            entries.append((path, f"data/wordlib/{path.name}"))

        pet_dir = self.base_dir / "resources" / "pets"
        for image_name in (
            "local_pet.gif",
            "local_pet.png",
            "local_pet.jpg",
            "local_pet.jpeg",
        ):
            path = pet_dir / image_name
            entries.append((path, f"resources/pets/{image_name}"))

        return entries

    @staticmethod
    def _is_allowed_backup_member(member_name: str, allowed_roots: set[str]) -> bool:
        """Limit restore extraction to the known user-data paths."""
        path = Path(member_name)
        if path.is_absolute() or ".." in path.parts:
            return False
        normalized = path.as_posix()
        if normalized in allowed_roots:
            return True
        return any(normalized.startswith(prefix) for prefix in allowed_roots if prefix.endswith("/"))

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
        startup_manager.set_enabled(self.launch_at_login_check.isChecked(), self.base_dir)
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
