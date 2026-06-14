"""Configuration loading and saving for DesktopPet."""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any, Dict

import yaml


LOGGER = logging.getLogger(__name__)


DEFAULT_CONFIG: Dict[str, Any] = {
    "reminder_interval_minutes": 30,
    "reminder_interval_seconds": 1800,
    "word_lib": "cet4.json",
    "daily_goal": 20,
    "startup_reminder": True,
    "bubble_duration_seconds": 5,
    "pet": {
        "size": 200,
        "opacity": 100,
        "always_on_top": True,
        "click_to_review": True,
        "x": None,
        "y": None,
    },
    "quiet_hours": {
        "enabled": True,
        "start": "22:00",
        "end": "08:00",
    },
}


class ConfigManager:
    """Read default config and persist user overrides separately."""

    def __init__(self, config_path: Path) -> None:
        """Load configuration from disk, creating it when missing."""
        self.config_path = config_path
        self.local_config_path = config_path.with_name(f"{config_path.stem}.local{config_path.suffix}")
        self.config: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration and fill missing fields with defaults."""
        loaded: Dict[str, Any] = {}
        if not self.config_path.exists():
            LOGGER.info("Config file missing; creating default config")
            self._write_yaml(self.config_path, self.config)
        else:
            loaded = self._read_yaml(self.config_path)

        local_loaded = self._read_yaml(self.local_config_path)
        merged = self._merge_defaults(copy.deepcopy(DEFAULT_CONFIG), loaded)
        self.config = self._merge_defaults(merged, local_loaded)

        self.save()
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value using dot notation for nested keys."""
        current: Any = self.config
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a config value using dot notation and save the file."""
        current = self.config
        parts = key.split(".")
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self.save()

    def save(self) -> None:
        """Persist user changes to the ignored local config file."""
        self._write_yaml(self.local_config_path, self.config)

    def _read_yaml(self, path: Path) -> Dict[str, Any]:
        """Read a YAML mapping from disk."""
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as file:
                loaded = yaml.safe_load(file) or {}
        except yaml.YAMLError:
            LOGGER.exception("Invalid YAML config: %s", path)
            return {}
        if not isinstance(loaded, dict):
            LOGGER.warning("Config file is not a mapping: %s", path)
            return {}
        return loaded

    @staticmethod
    def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
        """Write a YAML mapping to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                data,
                file,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

    @staticmethod
    def _merge_defaults(defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user settings into defaults without dropping new default keys."""
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(defaults.get(key), dict):
                defaults[key] = ConfigManager._merge_defaults(defaults[key], value)
            else:
                defaults[key] = value
        return defaults
