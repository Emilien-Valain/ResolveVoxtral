"""Plaintext local settings file (see docs/adr/0003-plaintext-api-key-storage.md)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import ConfigError

SCHEMA_VERSION = 1


def get_config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise ConfigError(
            "Couldn't find your Windows AppData folder. "
            "This script is only supported on Windows."
        )
    return Path(appdata) / "ResolveVoxtral"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def get_log_path() -> Path:
    return get_config_dir() / "log.txt"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(data: dict) -> None:
    config_dir = get_config_dir()
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        data = {**data, "schema_version": SCHEMA_VERSION}
        with get_config_path().open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        raise ConfigError(
            "Couldn't save your settings. Check that ResolveVoxtral has "
            "permission to write to your AppData folder."
        ) from e


def get_api_key() -> str | None:
    return load_config().get("mistral_api_key") or None


def set_api_key(key: str) -> None:
    cfg = load_config()
    cfg["mistral_api_key"] = key
    save_config(cfg)
