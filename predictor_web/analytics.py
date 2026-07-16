# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Pure historical analysis functions used to weight prediction candidates."""

from collections import Counter
from itertools import combinations

from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw


def build_frequency(draws: list[LottoDraw]) -> Counter[int]:
    """Count how often each main number appears in the supplied history."""
    bac_log(
        "Building number frequency table",
        component="analytics",
        draw_count=len(draws),
    )
    frequency: Counter[int] = Counter()
    for draw in draws:
        frequency.update(draw.numbers)
    bac_log(
        "Number frequency table ready",
        component="analytics",
        unique_numbers=len(frequency),
    )
    return frequency


def build_pair_frequency(draws: list[LottoDraw]) -> Counter[tuple[int, int]]:
    """Count historical co-occurrences for every two-number combination."""
    bac_log(
        "Building pair frequency table",
        component="analytics",
        draw_count=len(draws),
    )
    pair_frequency: Counter[tuple[int, int]] = Counter()
    for draw in draws:
        for pair in combinations(draw.numbers, 2):
            pair_frequency[pair] += 1
    bac_log(
        "Pair frequency table ready",
        component="analytics",
        unique_pairs=len(pair_frequency),
    )
    return pair_frequency


def build_overdue(draws: list[LottoDraw], number_min: int, number_max: int) -> dict[int, int]:
    """Measure draws elapsed since each number most recently appeared."""
    bac_log(
        "Calculating overdue distances",
        component="analytics",
        number_max=number_max,
        number_min=number_min,
    )
    unseen_distance = len(draws)
    overdue = {number: unseen_distance for number in range(number_min, number_max + 1)}

    # Reverse traversal lets the first match represent the latest appearance.
    for index, draw in enumerate(reversed(draws)):
        for number in draw.numbers:
            if overdue[number] == unseen_distance:
                overdue[number] = index

    bac_log(
        "Overdue distances ready",
        component="analytics",
        maximum_distance=max(overdue.values(), default=0),
    )
    return overdue


def calculate_number_scores(
    frequency: Counter[int],
    overdue: dict[int, int],
    *,
    number_min: int,
    number_max: int,
) -> dict[int, float]:
    """Blend normalized hot and overdue signals into positive pick weights."""
    bac_log(
        "Calculating number weights",
        component="analytics",
        number_count=number_max - number_min + 1,
    )
    frequency_values = [frequency[number] for number in range(number_min, number_max + 1)]
    overdue_values = [overdue[number] for number in range(number_min, number_max + 1)]
    scores: dict[int, float] = {}

    for number in range(number_min, number_max + 1):
        hot_score = _minmax(frequency[number], frequency_values)
        cold_score = _minmax(overdue[number], overdue_values)
        score = hot_score * 0.6 + cold_score * 0.4

        if number > 31:
            score *= 1.05

        scores[number] = score + 0.01

    highest_numbers = sorted(scores, key=scores.get, reverse=True)[:6]
    bac_log(
        "Number weights ready",
        component="analytics",
        highest_weighted=highest_numbers,
    )
    return scores


def _minmax(value: int, values: list[int]) -> float:
    """Normalize one integer onto a zero-to-one range."""
    low = min(values)
    high = max(values)
    if low == high:
        return 0.0
    return (value - low) / (high - low)
