from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Never touch the real settings file; start every test as a first run, hot-seat."""
    monkeypatch.setenv("SAHKKU_CONFIG_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(
        json.dumps({"opponent": "human", "seen_notice": False}), encoding="utf-8"
    )
    yield tmp_path
