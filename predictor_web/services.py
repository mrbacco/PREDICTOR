# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

from predictor_web.analytics import build_frequency
from predictor_web.config import AppConfig, load_config
from predictor_web.models import DatasetSummary
from predictor_web.predictor import PredictorEngine
from predictor_web.repository import DEFAULT_NUMBER_COLUMNS, LottoRepository
from predictor_web.scraper import LottoScraper


class LotteryService:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self.repository = LottoRepository(
            self.config.csv_path,
            number_columns=DEFAULT_NUMBER_COLUMNS,
            number_min=self.config.number_min,
            number_max=self.config.number_max,
            picks_per_line=self.config.picks_per_line,
        )
        self.scraper = LottoScraper(
            self.config.source_url,
            timeout_seconds=self.config.request_timeout_seconds,
        )
        self.predictor = PredictorEngine(self.config)

    def get_summary(self) -> dict:
        draws = self.repository.load_draws()
        if not draws:
            summary = DatasetSummary(
                total_draws=0,
                earliest_draw_date=None,
                latest_draw_date=None,
                latest_draw_numbers=(),
                hottest_numbers=[],
                unique_numbers_seen=0,
            )
            return summary.to_dict()

        frequency = build_frequency(draws)
        latest_draw = draws[-1]
        summary = DatasetSummary(
            total_draws=len(draws),
            earliest_draw_date=draws[0].draw_date.isoformat(),
            latest_draw_date=latest_draw.draw_date.isoformat(),
            latest_draw_numbers=latest_draw.numbers,
            hottest_numbers=[number for number, _ in frequency.most_common(6)],
            unique_numbers_seen=len(frequency),
        )
        return summary.to_dict()

    def get_recent_draws(self, limit: int = 12) -> list[dict]:
        resolved_limit = max(1, min(limit, 50))
        draws = self.repository.load_draws()
        recent_draws = list(reversed(draws[-resolved_limit:]))
        return [draw.to_dict() for draw in recent_draws]

    def generate_predictions(
        self,
        *,
        top_k: int | None = None,
        iterations: int | None = None,
        random_seed: int | None = None,
    ) -> dict:
        draws = self.repository.load_draws()
        report = self.predictor.generate(
            draws,
            top_k=top_k,
            iterations=iterations,
            random_seed=random_seed,
        )
        return report.to_dict()

    def refresh_data(self) -> dict:
        draws = self.scraper.fetch_draws()
        self.repository.save_draws(draws)
        return {
            "rows_written": len(draws),
            "latest_draw_date": draws[-1].draw_date.isoformat(),
            "source_url": self.config.source_url,
        }
