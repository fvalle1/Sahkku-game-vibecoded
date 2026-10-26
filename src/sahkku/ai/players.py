"""Easy, Medium and Hard players.

* Easy: random legal moves with a slight preference for captures.
* Medium: one-ply greedy on the static evaluation.
* Hard: expectimax with chance nodes for the dice, a beam, a depth limit and a time budget.
"""

from __future__ import annotations

import itertools
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal

from ..engine import (
    Action,
    Die,
    GameState,
    MoveAction,
    Rethrow,
    RethrowAll,
    Side,
    apply_action,
    legal_actions,
    legal_moves,
    state_key,
    throw_with,
)
from ..rules import Face
from .evaluate import evaluate

Level = Literal["easy", "medium", "hard"]
LEVELS: tuple[Level, ...] = ("easy", "medium", "hard")


def _easy(s: GameState, acts: list[Action], rng: random.Random) -> Action:
    captures = {
        (m.die, m.piece_id, m.to, m.fate): len(m.cand.out.captures) > 0 for m in legal_moves(s)
    }
    weights = []
    for a in acts:
        if isinstance(a, MoveAction):
            weights.append(4.0 if captures.get((a.die, a.piece_id, a.to, a.fate)) else 1.0)
        else:
            weights.append(0.4)  # re-throws are rarely interesting
    return rng.choices(acts, weights=weights, k=1)[0]


def _medium(s: GameState, acts: list[Action], rng: random.Random) -> Action:
    me = s.current
    base = evaluate(s, me)
    best = acts[0]
    best_v = float("-inf")
    for a in acts:
        if isinstance(a, Rethrow):
            v = base + 1
        elif isinstance(a, RethrowAll):
            v = base + 3
        else:
            v = evaluate(apply_action(s, a), me)
        v += rng.random() * 0.01
        if v > best_v:
            best_v, best = v, a
    return best


# ------------------------------------------------------------------ hard


@dataclass(frozen=True, slots=True)
class _Outcome:
    faces: tuple[Face, ...]
    weight: float


def _dice_outcomes(s: GameState) -> list[_Outcome]:
    o = s.options
    total = len(o.faces) ** o.dice_count
    counts: dict[tuple[Face, ...], int] = {}
    for combo in itertools.product(o.faces, repeat=o.dice_count):
        key = tuple(sorted(combo))
        counts[key] = counts.get(key, 0) + 1
    return [_Outcome(k, c / total) for k, c in counts.items()]


def _set_dice(s: GameState, faces: tuple[Face, ...]) -> GameState:
    o = s.options
    return replace(s, dice=tuple(Die(f, f == "blank" and o.blank_value == 0) for f in faces))


class _Search:
    def __init__(
        self,
        root: Side,
        budget_ms: float,
        s: GameState,
        own_beam: int,
        opp_beam: int,
        cancelled: Callable[[], bool] | None,
    ) -> None:
        self.root = root
        self.deadline = time.monotonic() + budget_ms / 1000.0
        self.own_beam = own_beam
        self.opp_beam = opp_beam
        self.cancelled = cancelled
        self.nodes = 0
        self.memo: dict[str, float] = {}
        self.outcomes = _dice_outcomes(s)

    def out_of_time(self) -> bool:
        """Checked on every node: one node (legal moves plus scoring each) can already be slow."""
        self.nodes += 1
        return time.monotonic() > self.deadline or bool(self.cancelled and self.cancelled())

    def after_rethrow(self, s: GameState, die: int, depth: int) -> float:
        o = s.options
        faces = [f for f in o.faces if f != "X"]
        total = 0.0
        for f in faces:
            dice = tuple(
                Die(f, f == "blank" and o.blank_value == 0) if i == die else d
                for i, d in enumerate(s.dice)
            )
            total += self.value(replace(s, dice=dice), depth)
        return total / len(faces)

    def after_rethrow_all(self, s: GameState, depth: int) -> float:
        """Condition on not getting all X again (the player could simply repeat)."""
        total = w = 0.0
        for out in self.outcomes:
            if all(f == "X" for f in out.faces):
                continue
            total += out.weight * self.value(_set_dice(s, out.faces), depth)
            w += out.weight
        return total / w if w else evaluate(s, self.root)

    def value(self, s: GameState, depth: int) -> float:
        if s.phase == "over" or self.out_of_time():
            return evaluate(s, self.root)
        key = f"{depth}|{state_key(s)}"
        hit = self.memo.get(key)
        if hit is not None:
            return hit
        if s.phase == "throw":
            if depth <= 0:
                result = evaluate(s, self.root)
            else:
                result = sum(
                    out.weight * self.value(throw_with(s, out.faces), depth - 1)
                    for out in self.outcomes
                )
        else:
            maximizing = s.current == self.root
            beam = self.own_beam if maximizing else self.opp_beam
            base = evaluate(s, self.root)
            scored: list[tuple[float, Action, GameState | None]] = []
            nxt: GameState | None
            for a in legal_actions(s):
                if time.monotonic() > self.deadline:
                    break  # out of time: judge by what has been scored so far
                if isinstance(a, (Rethrow, RethrowAll)):
                    scored.append((base + (1 if maximizing else -1), a, None))
                else:
                    nxt = apply_action(s, a)
                    scored.append((evaluate(nxt, self.root), a, nxt))
            if not scored:
                return evaluate(s, self.root)
            scored.sort(key=lambda t: t[0], reverse=maximizing)
            best = float("-inf") if maximizing else float("inf")
            for _, a, nxt in scored[:beam]:
                if nxt is not None:
                    v = self.value(nxt, depth)
                elif isinstance(a, Rethrow):
                    v = self.after_rethrow(s, a.die, depth)
                else:
                    v = self.after_rethrow_all(s, depth)
                best = max(best, v) if maximizing else min(best, v)
            result = best
        self.memo[key] = result
        return result


def _hard(
    s: GameState,
    acts: list[Action],
    rng: random.Random,
    budget_ms: float,
    cancelled: Callable[[], bool] | None,
) -> Action:
    search = _Search(s.current, budget_ms, s, 4, 2, cancelled)
    best = _medium(s, acts, rng)  # fallback if the clock runs out
    best_v = float("-inf")
    for a in acts:
        if isinstance(a, Rethrow):
            v = search.after_rethrow(s, a.die, 1)
        elif isinstance(a, RethrowAll):
            v = search.after_rethrow_all(s, 1)
        else:
            v = search.value(apply_action(s, a), 1)
        if time.monotonic() > search.deadline or (cancelled and cancelled()):
            break
        if v > best_v or (v == best_v and a == best):
            best_v, best = v, a
    return best


def choose_action(
    s: GameState,
    level: Level,
    rng: random.Random,
    budget_ms: float = 900.0,
    cancelled: Callable[[], bool] | None = None,
) -> Action:
    """Pick the next action for the player to move. Hard honours ``budget_ms`` and ``cancelled``."""
    acts = legal_actions(s)
    if not acts:
        raise ValueError("No legal actions")
    if len(acts) == 1 or s.phase == "throw":
        return acts[0]
    if level == "easy":
        return _easy(s, acts, rng)
    if level == "medium":
        return _medium(s, acts, rng)
    return _hard(s, acts, rng, budget_ms, cancelled)


def choose_action_job(s: GameState, level: Level, seed: int, budget_ms: float) -> Action:
    """Picklable entry point for running the AI in a worker process."""
    return choose_action(s, level, random.Random(seed), budget_ms)
