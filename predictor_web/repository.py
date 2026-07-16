# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""CSV persistence boundary for validated historical Lotto draws."""

import csv
from datetime import date
from pathlib import Path

from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw

DEFAULT_NUMBER_COLUMNS = ("n1", "n2", "n3", "n4", "n5", "n6")


class LottoRepository:
    """Load and save draw history without leaking CSV details to other layers."""

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
        bac_log(
            "Repository initialized",
            component="repository",
            data_file=self.csv_path.name,
            number_range=f"{self.number_min}-{self.number_max}",
        )

    def load_draws(self) -> list[LottoDraw]:
        """Load, validate, sort, and return all usable draw rows."""
        bac_log(
            "Loading draw history",
            component="repository",
            data_file=self.csv_path.name,
        )
        if not self.csv_path.exists():
            bac_log(
                "Draw history file is missing",
                level="ERROR",
                component="repository",
                data_file=self.csv_path.name,
            )
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
                    bac_log(
                        "Skipping malformed CSV row",
                        level="WARNING",
                        component="repository",
                        row=row_index,
                    )
                    continue

                if len(numbers) != self.picks_per_line or len(set(numbers)) != self.picks_per_line:
                    skipped_rows += 1
                    bac_log(
                        "Skipping row with duplicate main numbers",
                        level="WARNING",
                        component="repository",
                        numbers=numbers,
                        row=row_index,
                    )
                    continue

                if any(number < self.number_min or number > self.number_max for number in numbers):
                    skipped_rows += 1
                    bac_log(
                        "Skipping row with out-of-range number",
                        level="WARNING",
                        component="repository",
                        numbers=numbers,
                        row=row_index,
                    )
                    continue

                draws.append(LottoDraw(draw_date=draw_date, numbers=numbers, bonus=bonus))

        draws.sort(key=lambda item: item.draw_date)
        bac_log(
            "Draw history loaded",
            component="repository",
            earliest_date=draws[0].draw_date.isoformat() if draws else None,
            latest_date=draws[-1].draw_date.isoformat() if draws else None,
            loaded_rows=len(draws),
            skipped_rows=skipped_rows,
        )

        return draws

    def save_draws(self, draws: list[LottoDraw]) -> None:
        """Replace the CSV contents with an ordered validated draw collection."""
        bac_log(
            "Saving draw history",
            component="repository",
            data_file=self.csv_path.name,
            row_count=len(draws),
        )
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ("draw_date", *self.number_columns, "bonus")

        # Write the complete file in one pass so the schema stays consistent.
        with self.csv_path.open("w", newline="", encoding="utf-8") as file_pointer:
            writer = csv.DictWriter(file_pointer, fieldnames=fieldnames)
            writer.writeheader()
            for draw in draws:
                writer.writerow(draw.to_csv_row())

        bac_log(
            "Draw history saved",
            component="repository",
            data_file=self.csv_path.name,
            row_count=len(draws),
        )

    @staticmethod
    def _parse_optional_int(value: object) -> int | None:
        """Convert a blank optional CSV field to None, otherwise to an integer."""
        normalized = str(value).strip()
        if not normalized:
            return None
        return int(normalized)
