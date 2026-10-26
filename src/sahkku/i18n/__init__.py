"""Tiny i18n layer: one JSON file per language (``en.json`` is the reference).

To add a language, copy ``en.json`` to e.g. ``nb.json`` and translate the values. Keys that are
missing fall back to English. Sámi UI strings beyond the glossary terms are deliberately not
provided (see CULTURAL_NOTES.md).
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

_DIR = Path(__file__).parent
_current = "en"


def available_languages() -> list[str]:
    return sorted(p.stem for p in _DIR.glob("*.json"))


@cache
def _load(lang: str) -> dict[str, str]:
    path = _DIR / f"{lang}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def set_language(lang: str) -> None:
    global _current
    _current = lang if lang in available_languages() else "en"


def t(key: str, **vars: object) -> str:
    """Translate ``key``; ``{name}`` placeholders are filled from ``vars``."""
    s = _load(_current).get(key) or _load("en").get(key) or key
    for k, v in vars.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def has(key: str) -> bool:
    return key in _load("en")
