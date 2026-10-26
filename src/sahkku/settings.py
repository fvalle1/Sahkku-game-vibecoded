"""User settings, stored as a small JSON file in the user's config directory."""

from __future__ import annotations

import contextlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


def config_dir() -> Path:
    override = os.environ.get("SAHKKU_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "sahkku"
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "sahkku"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "sahkku"


@dataclass(slots=True)
class Settings:
    variant_id: str = "lagesvuotna"
    opponent: str = "medium"  # human | easy | medium | hard
    human_side: int = 0
    equal_odds: bool = False
    dice_anim: bool = True
    sound: bool = False
    colorblind: bool = False
    large_touch: bool = False
    explain: bool = True
    seen_notice: bool = False
    language: str = "en"
    custom_options: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def _path() -> Path:
    return config_dir() / "settings.json"


def load_settings() -> Settings:
    """Load settings; a missing or damaged file silently gives the defaults."""
    try:
        raw = json.loads(_path().read_text(encoding="utf-8"))
        known = {f.name for f in fields(Settings)}
        return Settings(**{k: v for k, v in raw.items() if k in known})
    except (OSError, ValueError, TypeError):
        return Settings()


def save_settings(s: Settings) -> None:
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(s.to_json(), encoding="utf-8")
        tmp.replace(p)
    except OSError:
        pass  # settings are a convenience; never crash the game over them


def reset_settings() -> Settings:
    with contextlib.suppress(OSError):
        _path().unlink(missing_ok=True)
    return Settings()
