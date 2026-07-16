# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Application service layer coordinating storage, scraping, and prediction."""

from predictor_web.analytics import build_frequency
from predictor_web.config import AppConfig, load_config
from predictor_web.logging_utils import bac_log
from predictor_web.models import DatasetSummary
from predictor_web.predictor import PredictorEngine
from predictor_web.repository import DEFAULT_NUMBER_COLUMNS, LottoRepository
from predictor_web.scraper import LottoScraper


class LotteryService:
    """Expose cohesive operations for both HTTP routes and CLI commands."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        bac_log(
            "Initializing lottery service",
            component="service",
            data_file=self.config.csv_path.name,
        )
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
        bac_log("Lottery service ready", component="service")

    def get_summary(self) -> dict:
        """Build dashboard-level statistics from the current repository data."""
        bac_log("Building dataset summary", component="service")
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
            bac_log(
                "Dataset summary ready for empty history",
                component="service",
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
        bac_log(
            "Dataset summary ready",
            component="service",
            latest_date=summary.latest_draw_date,
            total_draws=summary.total_draws,
            unique_numbers=summary.unique_numbers_seen,
        )
        return summary.to_dict()

    def get_recent_draws(self, limit: int = 12) -> list[dict]:
        """Return the newest validated draws in reverse chronological order."""
        resolved_limit = max(1, min(limit, 50))
        bac_log(
            "Loading recent draws",
            component="service",
            requested_limit=limit,
            resolved_limit=resolved_limit,
        )
        draws = self.repository.load_draws()
        recent_draws = list(reversed(draws[-resolved_limit:]))
        bac_log(
            "Recent draws ready",
            component="service",
            returned_rows=len(recent_draws),
        )
        return [draw.to_dict() for draw in recent_draws]

    def generate_predictions(
        self,
        *,
        top_k: int | None = None,
        iterations: int | None = None,
        random_seed: int | None = None,
    ) -> dict:
        """Generate a ranked prediction report from the current draw history."""
        bac_log(
            "Prediction request received",
            component="service",
            iterations=iterations,
            random_seed=random_seed,
            top_k=top_k,
        )
        draws = self.repository.load_draws()
        report = self.predictor.generate(
            draws,
            top_k=top_k,
            iterations=iterations,
            random_seed=random_seed,
        )
        bac_log(
            "Prediction report ready",
            component="service",
            candidate_count=report.candidate_count,
            returned_lines=len(report.lines),
        )
        return report.to_dict()

    def refresh_data(self) -> dict:
        """Refresh remote history and persist it as the local source of truth."""
        bac_log("Dataset refresh started", component="service")
        draws = self.scraper.fetch_draws()
        self.repository.save_draws(draws)
        result = {
            "rows_written": len(draws),
            "latest_draw_date": draws[-1].draw_date.isoformat(),
            "source_url": self.config.source_url,
        }
        bac_log(
            "Dataset refresh completed",
            component="service",
            latest_draw_date=result["latest_draw_date"],
            rows_written=result["rows_written"],
        )
        return result
