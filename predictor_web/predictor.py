# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Deterministic weighted prediction engine for main and bonus numbers."""

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
    """Generate, filter, score, and rank weighted Lotto candidate lines."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        bac_log(
            "Predictor engine initialized",
            component="predictor",
            picks_per_line=self.config.picks_per_line,
        )

    def generate(
        self,
        draws: list[LottoDraw],
        *,
        top_k: int | None = None,
        iterations: int | None = None,
        random_seed: int | None = None,
    ) -> PredictionReport:
        """Run one reproducible prediction search against historical draws."""
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

        bac_log(
            "Prediction run started",
            component="predictor",
            draw_count=len(draws),
            iterations=resolved_iterations,
            random_seed=resolved_seed,
            top_k=resolved_top_k,
        )

        # The analysis phase builds reusable weights before candidate generation begins.
        frequency = build_frequency(draws)
        bonus_frequency = Counter(
            draw.bonus for draw in draws if draw.bonus is not None
        )
        pair_frequency = build_pair_frequency(draws)
        overdue = build_overdue(draws, self.config.number_min, self.config.number_max)
        scores = calculate_number_scores(
            frequency,
            overdue,
            number_min=self.config.number_min,
            number_max=self.config.number_max,
        )
        bac_log(
            "Prediction analysis completed",
            component="predictor",
            bonus_numbers_seen=len(bonus_frequency),
            pair_count=len(pair_frequency),
        )

        rng = random.Random(resolved_seed)
        candidates: list[tuple[float, tuple[int, ...], int]] = []
        progress_interval = max(1, min(10000, resolved_iterations // 5 or 1))

        # Generate weighted lines, then keep only lines matching the shape filters.
        for index in range(resolved_iterations):
            ticket = self._weighted_pick(rng, scores)

            if self._is_valid_ticket(ticket):
                bonus = self._weighted_bonus_pick(
                    rng,
                    scores,
                    bonus_frequency,
                    excluded=ticket,
                )
                score = self._score_ticket(ticket, scores, pair_frequency)
                candidates.append((score, ticket, bonus))

            completed_iterations = index + 1
            if (
                completed_iterations % progress_interval == 0
                or completed_iterations == resolved_iterations
            ):
                bac_log(
                    "Prediction generation progress",
                    component="predictor",
                    accepted_candidates=len(candidates),
                    completed_iterations=completed_iterations,
                    progress_percent=round(
                        completed_iterations / resolved_iterations * 100,
                        1,
                    ),
                )

        if not candidates:
            bac_log(
                "Prediction run produced no valid candidates",
                level="ERROR",
                component="predictor",
                iterations=resolved_iterations,
            )
            raise RuntimeError("No valid candidates generated. Relax filters or increase iterations.")

        # Highest score wins; duplicate six-number lines are removed after sorting.
        candidates.sort(key=lambda item: item[0], reverse=True)
        lines = self._deduplicate_candidates(candidates, limit=resolved_top_k)
        bac_log(
            "Top prediction line selected",
            level="DEBUG",
            component="predictor",
            bonus=lines[0].bonus if lines else None,
            numbers=lines[0].numbers if lines else None,
            score=lines[0].score if lines else None,
        )

        bac_log(
            "Prediction run completed",
            component="predictor",
            acceptance_rate=round(len(candidates) / resolved_iterations, 4),
            accepted_candidates=len(candidates),
            returned_lines=len(lines),
        )
        return PredictionReport(
            lines=lines,
            iterations=resolved_iterations,
            top_k=resolved_top_k,
            random_seed=resolved_seed,
            candidate_count=len(candidates),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _validate_history(self, draws: list[LottoDraw]) -> None:
        """Reject prediction requests that do not have enough history."""
        if len(draws) < self.config.min_history_required:
            bac_log(
                "Prediction history requirement not met",
                level="ERROR",
                component="predictor",
                available_draws=len(draws),
                required_draws=self.config.min_history_required,
            )
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
        """Resolve an optional positive setting while enforcing its upper bound."""
        resolved = default if value is None else int(value)
        if resolved < 1:
            bac_log(
                "Prediction setting is below its minimum",
                level="WARNING",
                component="predictor",
                label=label,
                value=resolved,
            )
            raise ValueError(f"{label} must be at least 1.")
        if resolved > maximum:
            bac_log(
                "Prediction setting exceeds its maximum",
                level="WARNING",
                component="predictor",
                label=label,
                maximum=maximum,
                value=resolved,
            )
            raise ValueError(f"{label} must be less than or equal to {maximum}.")
        return resolved

    def _weighted_pick(self, rng: random.Random, scores: dict[int, float]) -> tuple[int, ...]:
        """Select six unique main numbers using the calculated number weights."""
        population = list(scores.keys())
        selected: list[int] = []

        # Remove each selected number so a ticket can never contain duplicates.
        while len(selected) < self.config.picks_per_line:
            weights = [scores[number] for number in population]
            pick = rng.choices(population, weights=weights, k=1)[0]
            selected.append(pick)
            population.remove(pick)

        return tuple(sorted(selected))

    @staticmethod
    def _weighted_bonus_pick(
        rng: random.Random,
        scores: dict[int, float],
        bonus_frequency: Counter[int],
        *,
        excluded: tuple[int, ...],
    ) -> int:
        """Select one weighted bonus from numbers not present in the main line."""
        population = [number for number in scores if number not in excluded]
        weights = [
            scores[number] + bonus_frequency[number] * 0.25
            for number in population
        ]
        return rng.choices(population, weights=weights, k=1)[0]

    def _is_valid_ticket(self, ticket: tuple[int, ...]) -> bool:
        """Apply lightweight distribution filters to a generated main line."""
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
        """Combine individual weights with historical pair co-occurrence strength."""
        total = sum(scores[number] for number in ticket)
        for pair in combinations(ticket, 2):
            total += pair_frequency[pair] * 2
        return total

    @staticmethod
    def _deduplicate_candidates(
        candidates: list[tuple[float, tuple[int, ...], int]],
        *,
        limit: int,
    ) -> list[PredictionLine]:
        """Return the highest-scoring unique lines up to the requested limit."""
        seen: set[tuple[int, ...]] = set()
        lines: list[PredictionLine] = []

        for score, ticket, bonus in candidates:
            if ticket in seen:
                continue

            seen.add(ticket)
            lines.append(
                PredictionLine(
                    rank=len(lines) + 1,
                    numbers=ticket,
                    bonus=bonus,
                    score=round(score, 2),
                )
            )

            if len(lines) == limit:
                break

        return lines
