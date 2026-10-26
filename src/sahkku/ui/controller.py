"""Game session logic for the UI, free of any NiceGUI import (so it can be tested directly).

The controller owns the current state, undo history, the log, the die/piece selection and the
messages shown to the player. The NiceGUI layer only draws it and forwards clicks.
"""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..ai import Level, choose_action
from ..engine import (
    Action,
    Cand,
    GameState,
    MoveAction,
    Rethrow,
    RethrowAll,
    SeededDice,
    Throw,
    apply_action,
    candidates_for,
    die_status,
    legal_actions,
    legal_moves,
    playable_dice_indices,
    start_game,
)
from ..engine.types import LegalMove
from ..i18n import t
from ..i18n.glossary import TERMS
from ..rules import RuleSet
from .format import describe_event, describe_position, face_text, side_name, win_text
from .scene import DestKind

Opponent = str  # "human" | "easy" | "medium" | "hard"


@dataclass(slots=True)
class _Snapshot:
    state: GameState
    dice_state: Any
    log_len: int
    record_len: int


@dataclass(slots=True)
class GameController:
    rules: RuleSet
    state: GameState
    dice: SeededDice
    seed: int
    opponent: Opponent = "human"
    human_side: int = 0
    explain: bool = True
    hint: str | None = None
    log: list[str] = field(default_factory=list)
    record: list[str] = field(default_factory=list)
    history: list[_Snapshot] = field(default_factory=list)
    sel_die: int | None = None
    sel_piece: int | None = None
    message: str = ""
    fate_prompt: list[Cand] | None = None
    thinking: bool = False
    cancel_requested: bool = False
    _ai_rng: random.Random = field(default_factory=random.Random)
    _cache_key: int = -1
    _cache: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ construction
    @classmethod
    def new(
        cls,
        rules: RuleSet,
        *,
        seed: int,
        opponent: Opponent = "human",
        human_side: int = 0,
        equal_odds: bool = False,
        miedut: bool = False,
        explain: bool = True,
    ) -> GameController:
        dice = SeededDice(seed)
        options, _ = rules.options.normalized()
        state = start_game(options, dice, miedut=miedut, equal_odds=equal_odds)
        return cls.from_state(
            rules, state, dice, seed, opponent, human_side, explain=explain, header=True
        )

    @classmethod
    def from_state(
        cls,
        rules: RuleSet,
        state: GameState,
        dice: SeededDice,
        seed: int,
        opponent: Opponent = "human",
        human_side: int = 0,
        *,
        explain: bool = True,
        hint: str | None = None,
        header: bool = False,
    ) -> GameController:
        c = cls(rules, state, dice, seed, opponent, human_side, explain, hint)
        c._ai_rng = random.Random(seed ^ 0x9E3779B9)
        c._log_events(state)
        if header:
            c.record.extend(c._record_header())
        return c

    def _record_header(self) -> list[str]:
        o = self.state.options
        lines = [
            f"{t('game.recordTitle')} - sahkku {self.rules.name}",
            f"rule set: {self.rules.id} ({self.rules.name})",
            f"seed: {self.seed}   mieđut: {self.state.miedut}   equal odds: {self.state.equal_odds}",
            f"options: {json.dumps(o.to_dict(), ensure_ascii=False, sort_keys=True)}",
            f"opponent: {self.opponent}   human seat: {self.human_side}",
        ]
        for th in self.state.start_log:
            lines.append(
                f"start throw {t(f'side.{th.side}')}: {' '.join(map(face_text, th.faces))}"
            )
        lines.append(f"{side_name(self.state.current)} starts")
        return lines

    def _log_events(self, s: GameState) -> None:
        for e in s.events:
            text = describe_event(s.options, e)
            if text:
                self.log.append(text)
                self.record.append(f"T{s.turn_number}: {text}")

    # ------------------------------------------------------------------ derived values
    @property
    def is_ai(self) -> bool:
        return self.opponent != "human"

    @property
    def over(self) -> bool:
        return self.state.phase == "over"

    @property
    def human_turn(self) -> bool:
        return not self.over and (not self.is_ai or self.state.current == self.human_side)

    @property
    def ai_turn(self) -> bool:
        return not self.over and self.is_ai and self.state.current != self.human_side

    def _cached(self, name: str, fn: Callable[[], Any]) -> Any:
        if self._cache_key != id(self.state):
            self._cache_key = id(self.state)
            self._cache = {}
        if name not in self._cache:
            self._cache[name] = fn()
        return self._cache[name]

    @property
    def actions(self) -> list[Action]:
        return list(
            self._cached("actions", lambda: legal_actions(self.state) if self.human_turn else [])
        )

    @property
    def moves(self) -> list[LegalMove]:
        return list(
            self._cached("moves", lambda: legal_moves(self.state) if self.human_turn else [])
        )

    @property
    def playable(self) -> list[int]:
        return list(
            self._cached(
                "playable",
                lambda: playable_dice_indices(self.state) if self.state.phase == "move" else [],
            )
        )

    @property
    def die(self) -> int | None:
        """The die in use: the selected one, or the only playable face."""
        s = self.state
        if not self.human_turn or s.phase != "move":
            return None
        playable = self.playable
        sel = self.sel_die
        if (
            sel is not None
            and sel < len(s.dice)
            and not s.dice[sel].used
            and any(s.dice[i].face == s.dice[sel].face for i in playable)
        ):
            return sel
        faces = {s.dice[i].face for i in playable}
        return playable[0] if len(faces) == 1 else None

    @property
    def face(self) -> Any:
        d = self.die
        return None if d is None else self.state.dice[d].face

    @property
    def movable(self) -> set[int]:
        f = self.face
        return {m.piece_id for m in self.moves if m.face == f} if f else set()

    @property
    def cands(self) -> list[Cand]:
        f = self.face
        if not self.human_turn or self.sel_piece is None or f is None:
            return []
        return candidates_for(self.state, self.sel_piece, f)

    @property
    def dests(self) -> dict[int, DestKind]:
        out: dict[int, DestKind] = {}
        for c in self.cands:
            if c.ok:
                out[c.to] = "capture" if c.out.captures else "ok"
            else:
                out.setdefault(c.to, "blocked")
        return out

    def status_text(self) -> str:
        s = self.state
        if s.phase == "over":
            return win_text(s)
        if self.thinking:
            return t("game.aiThinking")
        if s.phase == "throw":
            return f"{t('game.yourTurn')} · {side_name(s.current)}" if self.human_turn else ""
        return t("game.turn", side=side_name(s.current))

    def guide_text(self) -> str:
        if self.message:
            return self.message
        if self.hint:
            return f"{t('tutorial.try')} {self.hint}"
        if not self.human_turn or self.state.phase != "move":
            return ""
        if self.die is None:
            return t("game.pickDie")
        if self.sel_piece is None:
            return t("game.pickPiece")
        return t("game.pickDest")

    def king_text(self) -> str:
        k = next((p for p in self.state.pieces if p.kind == "king"), None)
        if k is None:
            return t("king.removed")
        key = "king.owner.none" if k.side is None else f"king.owner.{k.side}"
        return f"{t(key)} ({TERMS['king']})"

    def die_status(self, i: int) -> str:
        return die_status(self.state, i)

    def can_rethrow(self, i: int) -> bool:
        return any(isinstance(a, Rethrow) and a.die == i for a in self.actions)

    @property
    def can_rethrow_all(self) -> bool:
        return any(isinstance(a, RethrowAll) for a in self.actions)

    @property
    def can_undo(self) -> bool:
        return self.opponent == "human" and bool(self.history)

    def stake_remaining(self) -> int:
        w = self.state.winner
        if w is None:
            return 0
        return sum(1 for p in self.state.pieces if p.kind == "soldier" and p.side == w)

    def position_text(self) -> str:
        return describe_position(self.state)

    def game_record(self) -> str:
        lines = list(self.record)
        if self.over:
            lines.append(win_text(self.state))
        lines.append("")
        lines.append(self.position_text())
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------ actions
    def _commit(self, nxt: GameState, dice_before: Any) -> None:
        self.history.append(_Snapshot(self.state, dice_before, len(self.log), len(self.record)))
        self.state = nxt
        self._log_events(nxt)
        self.sel_die = None
        self.sel_piece = None
        self.fate_prompt = None
        self.message = ""

    def do_action(self, a: Action) -> None:
        dice_before = self.dice.snapshot()  # taken BEFORE the action, so undo cannot re-roll
        try:
            nxt = apply_action(self.state, a, self.dice)
        except ValueError as e:
            self.message = str(e)
            return
        self._commit(nxt, dice_before)

    def throw(self) -> None:
        if self.human_turn and self.state.phase == "throw":
            self.do_action(Throw())

    def rethrow(self, die: int) -> None:
        if self.can_rethrow(die):
            self.do_action(Rethrow(die))

    def rethrow_all(self) -> None:
        if self.can_rethrow_all:
            self.do_action(RethrowAll())

    def select_die(self, i: int) -> None:
        self.sel_die = i
        self.sel_piece = None
        self.fate_prompt = None
        self.message = ""

    def choose_fate(self, fate: str) -> None:
        die = self.die
        if die is None or not self.fate_prompt:
            return
        c = next(x for x in self.fate_prompt if x.fate == fate)
        self.do_action(MoveAction(die, c.piece_id, c.to, c.fate))

    def explain_click(self, pt: int) -> str:
        """Why clicking ``pt`` did nothing: the "explain why this move is illegal" message."""
        f = self.face
        if f is None:
            return t("reason.pick-die")
        s = self.state
        mine = [p for p in s.pieces if p.pt == pt and p.side == s.current]
        if self.sel_piece is None:
            if not mine:
                return t("game.pickPiece")
            p = mine[0]
            if not p.active and f != "X":
                return t("reason.only-x-wakes")
            bad = next((c for c in candidates_for(s, p.id, f) if c.reason), None)
            return t(f"reason.{bad.reason}") if bad and bad.reason else t("reason.no-moves-piece")
        bad_c = next((c for c in self.cands if c.to == pt and not c.ok), None)
        if bad_c and bad_c.reason:
            return t(f"reason.{bad_c.reason}")
        return t("reason.not-reachable")

    def click_point(self, pt: int) -> None:
        if not self.human_turn:
            return
        s = self.state
        if s.phase != "move":
            self.message = t("game.throw")
            return
        die = self.die
        if self.sel_piece is not None and die is not None:
            ok = [c for c in self.cands if c.to == pt and c.ok]
            if len(ok) == 1:
                self.do_action(MoveAction(die, self.sel_piece, pt, ok[0].fate))
                return
            if len(ok) > 1:
                self.fate_prompt = ok
                return
        here = [p for p in s.pieces if p.pt == pt and p.id in self.movable]
        if here:
            ids = [p.id for p in here]
            i = ids.index(self.sel_piece) if self.sel_piece in ids else -1
            self.sel_piece = ids[(i + 1) % len(ids)]
            self.fate_prompt = None
            self.message = t("game.pickDest")
            return
        self.message = self.explain_click(pt) if self.explain else ""

    def undo(self) -> None:
        if not self.can_undo:
            return
        snap = self.history.pop()
        self.state = snap.state
        self.dice.restore(snap.dice_state)  # the same dice come up again: undo cannot reroll
        del self.log[snap.log_len :]
        del self.record[snap.record_len :]
        self.sel_die = None
        self.sel_piece = None
        self.fate_prompt = None
        self.message = ""

    # ------------------------------------------------------------------ computer player
    def ai_choice(self, level: Level, budget_ms: float) -> Action:
        return choose_action(
            self.state, level, self._ai_rng, budget_ms, lambda: self.cancel_requested
        )

    def apply_ai(self, a: Action) -> None:
        self.thinking = False
        self.cancel_requested = False
        if not self.ai_turn:
            return
        self.do_action(a)
