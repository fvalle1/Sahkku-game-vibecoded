"""Computer opponents. No UI imports are allowed in this package."""

from .evaluate import evaluate
from .players import LEVELS, Level, choose_action, choose_action_job

__all__ = ["LEVELS", "Level", "choose_action", "choose_action_job", "evaluate"]
