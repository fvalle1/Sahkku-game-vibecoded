from __future__ import annotations

import json
from pathlib import Path

import pytest

from sahkku.settings import Settings, load_settings, reset_settings, save_settings


@pytest.fixture(autouse=True)
def cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SAHKKU_CONFIG_DIR", str(tmp_path))
    return tmp_path


def test_defaults_when_missing() -> None:
    s = load_settings()
    assert s.opponent == "medium" and s.sound is False and s.explain is True


def test_roundtrip(cfg: Path) -> None:
    s = Settings(
        variant_id="unjarga", colorblind=True, large_touch=True, custom_options={"cols": 13}
    )
    save_settings(s)
    again = load_settings()
    assert again == s
    assert (
        json.loads((cfg / "settings.json").read_text(encoding="utf-8"))["variant_id"] == "unjarga"
    )


def test_damaged_file_gives_defaults(cfg: Path) -> None:
    (cfg / "settings.json").write_text("{not json", encoding="utf-8")
    assert load_settings() == Settings()


def test_unknown_keys_are_ignored(cfg: Path) -> None:
    (cfg / "settings.json").write_text(
        json.dumps({"opponent": "hard", "future": 1}), encoding="utf-8"
    )
    assert load_settings().opponent == "hard"


def test_reset_removes_file(cfg: Path) -> None:
    save_settings(Settings(sound=True))
    assert reset_settings() == Settings()
    assert not (cfg / "settings.json").exists()
