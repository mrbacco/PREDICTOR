# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class LottoDraw:
    draw_date: date
    numbers: tuple[int, ...]
    bonus: int | None = None

    def to_csv_row(self) -> dict[str, Any]:
        row = {"draw_date": self.draw_date.isoformat()}
        for index, number in enumerate(self.numbers, start=1):
            row[f"n{index}"] = number
        row["bonus"] = "" if self.bonus is None else self.bonus
        return row

    def to_dict(self) -> dict[str, Any]:
        return {
            "draw_date": self.draw_date.isoformat(),
            "numbers": list(self.numbers),
            "bonus": self.bonus,
        }


@dataclass(frozen=True, slots=True)
class PredictionLine:
    rank: int
    numbers: tuple[int, ...]
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "numbers": list(self.numbers),
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class PredictionReport:
    lines: list[PredictionLine]
    iterations: int
    top_k: int
    random_seed: int
    candidate_count: int
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
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
    total_draws: int
    earliest_draw_date: str | None
    latest_draw_date: str | None
    latest_draw_numbers: tuple[int, ...]
    hottest_numbers: list[int]
    unique_numbers_seen: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_draws": self.total_draws,
            "earliest_draw_date": self.earliest_draw_date,
            "latest_draw_date": self.latest_draw_date,
            "latest_draw_numbers": list(self.latest_draw_numbers),
            "hottest_numbers": self.hottest_numbers,
            "unique_numbers_seen": self.unique_numbers_seen,
        }
