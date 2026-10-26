"""Self-play harness: ``python -m sahkku.ai.selfplay [--games 1000] [--hard-games 6]``.

Plays AI-vs-AI games for every variant and reports crashes, non-terminating games, illegal
states, and the first-seat versus second-seat win rate. Games run in parallel processes.
"""

from __future__ import annotations

import argparse
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

from ..engine import SeededDice, apply_action, check_invariants, start_game
from ..rules import VARIANTS, RuleSet, get_variant
from .players import Level, choose_action

MAX_ACTIONS = 6000


@dataclass(slots=True)
class GameResult:
    finished: bool
    winner: int | None
    starter: int
    actions: int
    violations: list[str] = field(default_factory=list)
    crashed: str | None = None


def play_one(
    variant_id: str, seed: int, levels: tuple[Level, Level], budget_ms: float = 0.0
) -> GameResult:
    rs = get_variant(variant_id)
    dice = SeededDice(seed)
    rng = random.Random(seed * 7919)
    s = start_game(rs.options, dice, miedut=seed % 2 == 0, equal_odds=seed % 5 == 0)
    starter = s.current
    n = 0
    try:
        while s.phase != "over" and n < MAX_ACTIONS:
            a = choose_action(s, levels[s.current], rng, budget_ms)
            s = apply_action(s, a, dice)
            bad = check_invariants(s)
            if bad:
                return GameResult(False, None, starter, n, bad)
            n += 1
    except Exception as e:
        return GameResult(False, None, starter, n, [], f"{type(e).__name__}: {e}")
    return GameResult(s.phase == "over", s.winner, starter, n)


_Job = tuple[str, int, tuple[Level, Level], float]


def _job(args: _Job) -> GameResult:
    return play_one(*args)


def _run(jobs: list[_Job], pool: ProcessPoolExecutor | None) -> list[GameResult]:
    if pool is None:
        return [_job(j) for j in jobs]
    return list(pool.map(_job, jobs, chunksize=4))


@dataclass(slots=True)
class Report:
    name: str
    games: int
    finished: int = 0
    unfinished: int = 0
    crashes: int = 0
    violations: int = 0
    seat_wins: tuple[int, int] = (0, 0)
    starter_wins: int = 0
    avg_actions: float = 0.0
    hard_ok: int = 0
    hard_games: int = 0

    @property
    def seat0_share(self) -> float:
        total = sum(self.seat_wins)
        return self.seat_wins[0] / total if total else 0.5

    @property
    def starter_share(self) -> float:
        return self.starter_wins / self.finished if self.finished else 0.5

    @property
    def one_sided(self) -> bool:
        return not 0.35 <= self.seat0_share <= 0.65

    @property
    def clean(self) -> bool:
        return (
            not (self.unfinished or self.crashes or self.violations)
            and self.hard_ok == self.hard_games
        )

    def line(self) -> str:
        return (
            f"{self.name:<28} games {self.games}  finished {self.finished}  "
            f"unfinished {self.unfinished}  crashes {self.crashes}  violations {self.violations}  "
            f"seat0 win {self.seat0_share:.1%}  starter win {self.starter_share:.1%}  "
            f"avg actions {self.avg_actions:.0f}  hard {self.hard_ok}/{self.hard_games}"
            + ("  WARNING one-sided" if self.one_sided else "")
        )


def run_variant(
    rs: RuleSet, games: int, hard_games: int, pool: ProcessPoolExecutor | None
) -> Report:
    pairs: list[tuple[Level, Level]] = [
        ("easy", "easy"),
        ("medium", "medium"),
        ("easy", "medium"),
        ("medium", "easy"),
    ]
    jobs: list[_Job] = [(rs.id, i + 1, pairs[i % 4], 0.0) for i in range(games)]
    hard_jobs: list[_Job] = [
        (rs.id, 90000 + i, ("hard", "medium") if i % 2 else ("medium", "hard"), 60.0)
        for i in range(hard_games)
    ]
    results = _run(jobs, pool)
    hard = _run(hard_jobs, pool)
    rep = Report(rs.name, games, hard_games=hard_games)
    wins = [0, 0]
    actions = 0
    for r in results:
        if r.crashed:
            rep.crashes += 1
        elif r.violations:
            rep.violations += 1
        elif r.finished:
            rep.finished += 1
            actions += r.actions
            if r.winner is not None:
                wins[r.winner] += 1
                rep.starter_wins += r.winner == r.starter
        else:
            rep.unfinished += 1
    rep.seat_wins = (wins[0], wins[1])
    rep.avg_actions = actions / rep.finished if rep.finished else 0.0
    rep.hard_ok = sum(1 for r in hard if r.finished and not r.violations and not r.crashed)
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--games", type=int, default=1000)
    ap.add_argument("--hard-games", type=int, default=6)
    ap.add_argument("--variant", default=None, help="only this variant id")
    ap.add_argument("--workers", type=int, default=0, help="0 = all cores, 1 = no processes")
    args = ap.parse_args(argv)
    variants = [v for v in VARIANTS if args.variant in (None, v.id)]
    ok = True
    pool = None if args.workers == 1 else ProcessPoolExecutor(args.workers or None)
    try:
        for rs in variants:
            rep = run_variant(rs, args.games, args.hard_games, pool)
            print(rep.line(), flush=True)
            ok &= rep.clean
    finally:
        if pool:
            pool.shutdown()
    if not ok:
        print("Self-play found problems.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
