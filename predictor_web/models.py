# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Typed records used at repository, service, predictor, and API boundaries."""

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class LottoDraw:
    """One validated historical draw, including its optional recorded bonus."""

    draw_date: date
    numbers: tuple[int, ...]
    bonus: int | None = None

    def to_csv_row(self) -> dict[str, Any]:
        """Convert the typed draw into the repository's flat CSV schema."""
        row: dict[str, Any] = {"draw_date": self.draw_date.isoformat()}
        for index, number in enumerate(self.numbers, start=1):
            row[f"n{index}"] = number
        row["bonus"] = "" if self.bonus is None else self.bonus
        return row

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation for API responses."""
        return {
            "draw_date": self.draw_date.isoformat(),
            "numbers": list(self.numbers),
            "bonus": self.bonus,
        }


@dataclass(frozen=True, slots=True)
class PredictionLine:
    """One ranked six-number prediction with a distinct bonus number."""

    rank: int
    numbers: tuple[int, ...]
    bonus: int
    score: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready prediction line."""
        return {
            "rank": self.rank,
            "numbers": list(self.numbers),
            "bonus": self.bonus,
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class PredictionReport:
    """Metadata and ranked output from one deterministic prediction run."""

    lines: list[PredictionLine]
    iterations: int
    top_k: int
    random_seed: int
    candidate_count: int
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete prediction run for the CLI or API."""
        return {
            "lines": [line.to_dict() for line in self.lines],
            "iterations": self.iterations,
            "top_k": self.top_k,
            "random_seed": self.random_seed,
            "candidate_count": self.candidate_count,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    """Compact statistics displayed in the dashboard overview."""

    total_draws: int
    earliest_draw_date: str | None
    latest_draw_date: str | None
    latest_draw_numbers: tuple[int, ...]
    hottest_numbers: list[int]
    unique_numbers_seen: int

    def to_dict(self) -> dict[str, Any]:
        """Return dashboard summary values in JSON-compatible form."""
        return {
            "total_draws": self.total_draws,
            "earliest_draw_date": self.earliest_draw_date,
            "latest_draw_date": self.latest_draw_date,
            "latest_draw_numbers": list(self.latest_draw_numbers),
            "hottest_numbers": self.hottest_numbers,
            "unique_numbers_seen": self.unique_numbers_seen,
        }
