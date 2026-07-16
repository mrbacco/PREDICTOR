# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

from collections import Counter
from itertools import combinations

from predictor_web.models import LottoDraw


def build_frequency(draws: list[LottoDraw]) -> Counter[int]:
    frequency: Counter[int] = Counter()
    for draw in draws:
        frequency.update(draw.numbers)
    return frequency


def build_pair_frequency(draws: list[LottoDraw]) -> Counter[tuple[int, int]]:
    pair_frequency: Counter[tuple[int, int]] = Counter()
    for draw in draws:
        for pair in combinations(draw.numbers, 2):
            pair_frequency[pair] += 1
    return pair_frequency


def build_overdue(draws: list[LottoDraw], number_min: int, number_max: int) -> dict[int, int]:
    unseen_distance = len(draws)
    overdue = {number: unseen_distance for number in range(number_min, number_max + 1)}

    for index, draw in enumerate(reversed(draws)):
        for number in draw.numbers:
            if overdue[number] == unseen_distance:
                overdue[number] = index

    return overdue


def calculate_number_scores(
    frequency: Counter[int],
    overdue: dict[int, int],
    *,
    number_min: int,
    number_max: int,
) -> dict[int, float]:
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

    return scores


def _minmax(value: int, values: list[int]) -> float:
    low = min(values)
    high = max(values)
    if low == high:
        return 0.0
    return (value - low) / (high - low)
