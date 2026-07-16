# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import csv
from datetime import date
from pathlib import Path

from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw

DEFAULT_NUMBER_COLUMNS = ("n1", "n2", "n3", "n4", "n5", "n6")


class LottoRepository:
    def __init__(
        self,
        csv_path: Path,
        *,
        number_columns: tuple[str, ...] = DEFAULT_NUMBER_COLUMNS,
        number_min: int = 1,
        number_max: int = 47,
        picks_per_line: int = 6,
    ) -> None:
        self.csv_path = csv_path
        self.number_columns = number_columns
        self.number_min = number_min
        self.number_max = number_max
        self.picks_per_line = picks_per_line

    def load_draws(self) -> list[LottoDraw]:
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {self.csv_path.name}. Run scrape_irish_lotto.py first."
            )

        draws: list[LottoDraw] = []
        skipped_rows = 0

        with self.csv_path.open("r", newline="", encoding="utf-8") as file_pointer:
            reader = csv.DictReader(file_pointer)
            for row_index, row in enumerate(reader, start=2):
                try:
                    draw_date = date.fromisoformat(str(row["draw_date"]))
                    numbers = tuple(
                        sorted(int(str(row[column_name])) for column_name in self.number_columns)
                    )
                    bonus = self._parse_optional_int(row.get("bonus", ""))
                except (KeyError, TypeError, ValueError):
                    skipped_rows += 1
                    bac_log(f"Skipping malformed row {row_index}")
                    continue

                if len(numbers) != self.picks_per_line or len(set(numbers)) != self.picks_per_line:
                    skipped_rows += 1
                    bac_log(f"Skipping duplicate-number row {row_index}: {numbers}")
                    continue

                if any(number < self.number_min or number > self.number_max for number in numbers):
                    skipped_rows += 1
                    bac_log(f"Skipping out-of-range row {row_index}: {numbers}")
                    continue

                draws.append(LottoDraw(draw_date=draw_date, numbers=numbers, bonus=bonus))

        draws.sort(key=lambda item: item.draw_date)
        bac_log(f"Loaded {len(draws)} valid draw rows from {self.csv_path.name}")
        if skipped_rows:
            bac_log(f"Skipped {skipped_rows} malformed or invalid rows")

        return draws

    def save_draws(self, draws: list[LottoDraw]) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ("draw_date", *self.number_columns, "bonus")

        with self.csv_path.open("w", newline="", encoding="utf-8") as file_pointer:
            writer = csv.DictWriter(file_pointer, fieldnames=fieldnames)
            writer.writeheader()
            for draw in draws:
                writer.writerow(draw.to_csv_row())

        bac_log(f"Wrote {len(draws)} rows to {self.csv_path.name}")

    @staticmethod
    def _parse_optional_int(value: object) -> int | None:
        normalized = str(value).strip()
        if not normalized:
            return None
        return int(normalized)
