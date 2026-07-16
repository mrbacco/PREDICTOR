# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import tempfile
import unittest
from pathlib import Path

from predictor_web.predictor import PredictorEngine
from predictor_web.repository import LottoRepository
from tests.test_support import build_test_config, write_sample_csv


class PredictorEngineTests(unittest.TestCase):
    def test_generate_returns_ranked_unique_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = build_test_config(root)
            write_sample_csv(config.csv_path)

            repository = LottoRepository(
                config.csv_path,
                number_min=config.number_min,
                number_max=config.number_max,
                picks_per_line=config.picks_per_line,
            )
            draws = repository.load_draws()

            engine = PredictorEngine(config)
            report = engine.generate(draws, top_k=5, iterations=800, random_seed=101)

            self.assertEqual(report.top_k, 5)
            self.assertEqual(len(report.lines), 5)
            self.assertEqual([line.rank for line in report.lines], [1, 2, 3, 4, 5])
            self.assertGreater(report.candidate_count, 0)

            seen_tickets = set()
            for line in report.lines:
                self.assertEqual(tuple(sorted(line.numbers)), line.numbers)
                self.assertEqual(len(line.numbers), 6)
                self.assertEqual(len(set(line.numbers)), 6)
                self.assertNotIn(line.numbers, seen_tickets)
                seen_tickets.add(line.numbers)


if __name__ == "__main__":
    unittest.main()
