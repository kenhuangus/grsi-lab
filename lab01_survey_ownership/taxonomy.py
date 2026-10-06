"""Two-axis taxonomy for RSI survey: mutable/locked × evaluable/not."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mutability(str, Enum):
    MUTABLE = "mutable"
    LOCKED = "locked"


class Evaluability(str, Enum):
    EVALUABLE = "evaluable"
    NOT_EVALUABLE = "not_evaluable"


@dataclass(frozen=True)
class TaxonomyCell:
    """Classification cell for a surveyed component."""

    mutability: Mutability
    evaluability: Evaluability

    @property
    def is_rsi_target(self) -> bool:
        """True only if independently mutable and evaluable."""
        return (
            self.mutability is Mutability.MUTABLE
            and self.evaluability is Evaluability.EVALUABLE
        )


def classify(
    *,
    is_locked: bool,
    has_eval_hook: bool,
) -> TaxonomyCell:
    """Classify a component on the two ownership axes.

    Parameters
    ----------
    is_locked:
        True if the path sits in the Last Frozen Layer / ownership locked list.
    has_eval_hook:
        True if an external or declared evaluation hook exists.
    """
    mutability = Mutability.LOCKED if is_locked else Mutability.MUTABLE
    evaluability = (
        Evaluability.EVALUABLE if has_eval_hook else Evaluability.NOT_EVALUABLE
    )
    return TaxonomyCell(mutability=mutability, evaluability=evaluability)
