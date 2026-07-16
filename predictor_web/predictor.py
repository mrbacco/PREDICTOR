# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import random
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations

from predictor_web.analytics import (
    build_frequency,
    build_overdue,
    build_pair_frequency,
    calculate_number_scores,
)
from predictor_web.config import AppConfig
from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw, PredictionLine, PredictionReport


class PredictorEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def generate(
        self,
        draws: list[LottoDraw],
        *,
        top_k: int | None = None,
        iterations: int | None = None,
        random_seed: int | None = None,
    ) -> PredictionReport:
        self._validate_history(draws)

        resolved_top_k = self._resolve_positive_integer(
            top_k,
            default=self.config.default_top_k,
            maximum=self.config.max_top_k,
            label="top_k",
        )
        resolved_iterations = self._resolve_positive_integer(
            iterations,
            default=self.config.default_iterations,
            maximum=self.config.max_iterations,
            label="iterations",
        )
        resolved_seed = self.config.default_random_seed if random_seed is None else int(random_seed)

        bac_log("Starting predictor analysis")
        frequency = build_frequency(draws)
        pair_frequency = build_pair_frequency(draws)
        overdue = build_overdue(draws, self.config.number_min, self.config.number_max)
        scores = calculate_number_scores(
            frequency,
            overdue,
            number_min=self.config.number_min,
            number_max=self.config.number_max,
        )

        rng = random.Random(resolved_seed)
        candidates: list[tuple[float, tuple[int, ...]]] = []

        for index in range(resolved_iterations):
            ticket = self._weighted_pick(rng, scores)

            if self._is_valid_ticket(ticket):
                score = self._score_ticket(ticket, scores, pair_frequency)
                candidates.append((score, ticket))

            if (index + 1) % 10000 == 0:
                bac_log(f"Prediction progress: {index + 1}/{resolved_iterations}")

        if not candidates:
            raise RuntimeError("No valid candidates generated. Relax filters or increase iterations.")

        candidates.sort(key=lambda item: item[0], reverse=True)
        lines = self._deduplicate_candidates(candidates, limit=resolved_top_k)

        bac_log(f"Prepared {len(lines)} ranked prediction lines")
        return PredictionReport(
            lines=lines,
            iterations=resolved_iterations,
            top_k=resolved_top_k,
            random_seed=resolved_seed,
            candidate_count=len(candidates),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _validate_history(self, draws: list[LottoDraw]) -> None:
        if len(draws) < self.config.min_history_required:
            raise RuntimeError(
                f"Not enough valid historical draws to generate output. Need at least "
                f"{self.config.min_history_required} rows."
            )

    @staticmethod
    def _resolve_positive_integer(
        value: int | None,
        *,
        default: int,
        maximum: int,
        label: str,
    ) -> int:
        resolved = default if value is None else int(value)
        if resolved < 1:
            raise ValueError(f"{label} must be at least 1.")
        if resolved > maximum:
            raise ValueError(f"{label} must be less than or equal to {maximum}.")
        return resolved

    def _weighted_pick(self, rng: random.Random, scores: dict[int, float]) -> tuple[int, ...]:
        population = list(scores.keys())
        selected: list[int] = []

        while len(selected) < self.config.picks_per_line:
            weights = [scores[number] for number in population]
            pick = rng.choices(population, weights=weights, k=1)[0]
            selected.append(pick)
            population.remove(pick)

        return tuple(sorted(selected))

    def _is_valid_ticket(self, ticket: tuple[int, ...]) -> bool:
        low_count = sum(1 for number in ticket if number <= 31)
        if low_count > 4:
            return False

        odd_count = sum(1 for number in ticket if number % 2 == 1)
        if odd_count < 2 or odd_count > 4:
            return False

        consecutive_pairs = 0
        for index in range(len(ticket) - 1):
            if ticket[index + 1] - ticket[index] == 1:
                consecutive_pairs += 1

        return consecutive_pairs < 2

    @staticmethod
    def _score_ticket(
        ticket: tuple[int, ...],
        scores: dict[int, float],
        pair_frequency: Counter[tuple[int, int]],
    ) -> float:
        total = sum(scores[number] for number in ticket)
        for pair in combinations(ticket, 2):
            total += pair_frequency[pair] * 2
        return total

    @staticmethod
    def _deduplicate_candidates(
        candidates: list[tuple[float, tuple[int, ...]]],
        *,
        limit: int,
    ) -> list[PredictionLine]:
        seen: set[tuple[int, ...]] = set()
        lines: list[PredictionLine] = []

        for score, ticket in candidates:
            if ticket in seen:
                continue

            seen.add(ticket)
            lines.append(
                PredictionLine(rank=len(lines) + 1, numbers=ticket, score=round(score, 2))
            )

            if len(lines) == limit:
                break

        return lines
