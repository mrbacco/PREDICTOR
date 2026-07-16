# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Shared deterministic fixtures for repository, predictor, and web tests."""

import csv
from pathlib import Path

from predictor_web.config import AppConfig

# Twelve valid rows satisfy the predictor's minimum-history requirement.
SAMPLE_DRAWS = [
    ("2026-01-04", (2, 9, 14, 21, 28, 35), 42),
    ("2026-01-08", (5, 11, 17, 23, 29, 41), 7),
    ("2026-01-11", (3, 12, 18, 26, 33, 45), 9),
    ("2026-01-15", (1, 7, 19, 24, 32, 44), 16),
    ("2026-01-18", (4, 10, 22, 27, 34, 46), 13),
    ("2026-01-22", (6, 8, 15, 25, 38, 47), 3),
    ("2026-01-25", (5, 14, 20, 31, 39, 43), 18),
    ("2026-01-29", (2, 13, 16, 28, 36, 40), 12),
    ("2026-02-01", (9, 11, 24, 30, 35, 42), 5),
    ("2026-02-05", (7, 18, 21, 29, 37, 45), 14),
    ("2026-02-08", (1, 10, 17, 26, 34, 41), 22),
    ("2026-02-12", (4, 12, 19, 27, 33, 46), 15),
]


def build_test_config(root: Path) -> AppConfig:
    """Create an isolated configuration while reusing real static assets."""
    package_root = Path(__file__).resolve().parent.parent / "predictor_web"

    return AppConfig(
        base_dir=root,
        csv_path=root / "irish_lotto_results.csv",
        static_dir=package_root / "static",
        template_dir=package_root / "templates",
        source_url="https://example.com/lotto",
        project_name="Irish Lotto Predictor",
        release_version="1.0.0",
        number_min=1,
        number_max=47,
        picks_per_line=6,
        default_top_k=5,
        default_iterations=5000,
        default_random_seed=20260712,
        min_history_required=10,
        max_top_k=50,
        max_iterations=200000,
        request_timeout_seconds=30,
        host="127.0.0.1",
        port=8080,
    )


def write_sample_csv(csv_path: Path) -> None:
    """Write the deterministic sample history using the production CSV schema."""
    fieldnames = ["draw_date", "n1", "n2", "n3", "n4", "n5", "n6", "bonus"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as file_pointer:
        writer = csv.DictWriter(file_pointer, fieldnames=fieldnames)
        writer.writeheader()
        # Keep fixture construction explicit so schema regressions are easy to diagnose.
        for draw_date, numbers, bonus in SAMPLE_DRAWS:
            writer.writerow(
                {
                    "draw_date": draw_date,
                    "n1": numbers[0],
                    "n2": numbers[1],
                    "n3": numbers[2],
                    "n4": numbers[3],
                    "n5": numbers[4],
                    "n6": numbers[5],
                    "bonus": bonus,
                }
            )
