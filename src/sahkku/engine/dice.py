"""All randomness goes through an injected ``Dice``. The engine never touches ``random`` itself."""

from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from typing import Any, Protocol

from ..rules import Face


class Dice(Protocol):
    def roll(self, faces: Sequence[Face]) -> Face:
        """Throw one die with the given faces (each equally likely)."""

    def coin(self) -> bool:
        """A fair coin (who throws first)."""


class SeededDice:
    """Reproducible dice. ``snapshot``/``restore`` let the UI undo without changing later throws."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def roll(self, faces: Sequence[Face]) -> Face:
        return faces[self._rng.randrange(len(faces))]

    def coin(self) -> bool:
        return self._rng.random() < 0.5

    def snapshot(self) -> Any:
        return self._rng.getstate()

    def restore(self, state: Any) -> None:
        self._rng.setstate(state)


class ScriptedDice:
    """Dice that return a fixed list of throws (for tests). Raises when the script runs out."""

    def __init__(self, rolls: Iterable[Face] = (), coins: Iterable[bool] = ()) -> None:
        self._rolls = list(rolls)
        self._coins = list(coins)
        self.rolls_used = 0

    def roll(self, faces: Sequence[Face]) -> Face:
        if not self._rolls:
            raise IndexError("ScriptedDice ran out of rolls")
        face = self._rolls.pop(0)
        if face not in faces:
            raise ValueError(f"scripted face {face!r} is not on the die {tuple(faces)}")
        self.rolls_used += 1
        return face

    def coin(self) -> bool:
        if not self._coins:
            raise IndexError("ScriptedDice ran out of coins")
        return self._coins.pop(0)
