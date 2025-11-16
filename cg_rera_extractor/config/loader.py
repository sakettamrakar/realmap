"""Configuration loading utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import AppConfig


def load_config(path: str) -> AppConfig:
    """Load YAML configuration data into an :class:`AppConfig`."""

    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config_data: Any = yaml.safe_load(handle) or {}

    return AppConfig.model_validate(config_data)


__all__ = ["load_config"]
