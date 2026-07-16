# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import json
import re
from datetime import datetime
from urllib.request import Request, urlopen

from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw


class LottoScraper:
    def __init__(self, source_url: str, timeout_seconds: int = 30) -> None:
        self.source_url = source_url
        self.timeout_seconds = timeout_seconds

    def fetch_draws(self) -> list[LottoDraw]:
        bac_log(f"Fetching lotto history from {self.source_url}")
        raw_html = self.fetch_html(self.source_url)
        next_data = self.extract_next_data_json(raw_html)
        draws = self.parse_draws_from_next_data(next_data)

        if not draws:
            raise RuntimeError(
                "No Lotto rows parsed from the source payload. The website structure may have changed."
            )

        bac_log(f"Fetched {len(draws)} draw rows from source")
        return draws

    def fetch_html(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                )
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"Unexpected HTTP status: {status}")
            return response.read().decode("utf-8", errors="replace")

    @staticmethod
    def extract_next_data_json(raw_html: str) -> dict:
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">([\s\S]*?)</script>',
            raw_html,
            flags=re.IGNORECASE,
        )
        if not match:
            raise RuntimeError("Could not locate __NEXT_DATA__ payload in the source HTML.")
        return json.loads(match.group(1))

    @staticmethod
    def parse_draws_from_next_data(next_data: dict) -> list[LottoDraw]:
        page_props = next_data.get("props", {}).get("pageProps", {})
        entries = page_props.get("list", [])
        draws: list[LottoDraw] = []

        for entry in entries:
            standard = entry.get("standard", {})
            grids = standard.get("grids", [])
            draw_dates = standard.get("drawDates", [])

            if not grids or not draw_dates:
                continue

            first_grid = grids[0]
            standard_lines = first_grid.get("standard", [])
            additional_lines = first_grid.get("additional", [])

            if not standard_lines or len(standard_lines[0]) != 6:
                continue

            numbers = tuple(sorted(int(value) for value in standard_lines[0]))
            bonus = None
            if additional_lines and additional_lines[0]:
                raw_bonus = str(additional_lines[0][0]).strip()
                if raw_bonus:
                    bonus = int(raw_bonus)

            draw_date = datetime.fromisoformat(draw_dates[0].replace("Z", "+00:00")).date()
            draws.append(LottoDraw(draw_date=draw_date, numbers=numbers, bonus=bonus))

        deduplicated: dict[str, LottoDraw] = {}
        for draw in draws:
            deduplicated.setdefault(draw.draw_date.isoformat(), draw)

        return sorted(deduplicated.values(), key=lambda item: item.draw_date)
