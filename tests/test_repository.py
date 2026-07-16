# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import csv
import tempfile
import unittest
from pathlib import Path

from predictor_web.repository import LottoRepository
from tests.test_support import SAMPLE_DRAWS, build_test_config, write_sample_csv


class LottoRepositoryTests(unittest.TestCase):
    def test_load_draws_skips_invalid_rows_and_sorts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = build_test_config(root)
            write_sample_csv(config.csv_path)

            with config.csv_path.open("a", newline="", encoding="utf-8") as file_pointer:
                writer = csv.writer(file_pointer)
                writer.writerow(["bad-date", 1, 2, 3, 4, 5, 6, ""])
                writer.writerow(["2026-02-13", 1, 1, 2, 3, 4, 5, ""])

            repository = LottoRepository(
                config.csv_path,
                number_min=config.number_min,
                number_max=config.number_max,
                picks_per_line=config.picks_per_line,
            )

            draws = repository.load_draws()

            self.assertEqual(len(draws), len(SAMPLE_DRAWS))
            self.assertEqual(draws[0].draw_date.isoformat(), SAMPLE_DRAWS[0][0])
            self.assertEqual(draws[-1].draw_date.isoformat(), SAMPLE_DRAWS[-1][0])


if __name__ == "__main__":
    unittest.main()
