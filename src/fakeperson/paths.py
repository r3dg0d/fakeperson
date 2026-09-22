"""XDG-ish paths for identities and model cache."""

from __future__ import annotations

import os
from pathlib import Path


def data_home() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "fakeperson"
    return Path.home() / ".local" / "share" / "fakeperson"


def cache_home() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        return Path(base) / "fakeperson"
    return Path.home() / ".cache" / "fakeperson"


def config_home() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "fakeperson"
    return Path.home() / ".config" / "fakeperson"


def identities_dir() -> Path:
    return data_home() / "identities"


def models_dir() -> Path:
    return cache_home() / "models"


def ensure_dirs() -> None:
    identities_dir().mkdir(parents=True, exist_ok=True)
    models_dir().mkdir(parents=True, exist_ok=True)
    config_home().mkdir(parents=True, exist_ok=True)
