# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Remote Irish Lotto history fetcher and Next.js payload parser."""

import json
import re
from datetime import datetime
from urllib.request import Request, urlopen

from predictor_web.logging_utils import bac_log
from predictor_web.models import LottoDraw


class LottoScraper:
    """Fetch and translate the public history page into typed draw records."""

    def __init__(self, source_url: str, timeout_seconds: int = 30) -> None:
        self.source_url = source_url
        self.timeout_seconds = timeout_seconds
        bac_log(
            "Scraper initialized",
            component="scraper",
            timeout_seconds=self.timeout_seconds,
        )

    def fetch_draws(self) -> list[LottoDraw]:
        """Run the full remote fetch, extraction, parsing, and validation flow."""
        bac_log(
            "Fetching remote Lotto history",
            component="scraper",
            source_url=self.source_url,
        )
        raw_html = self.fetch_html(self.source_url)
        next_data = self.extract_next_data_json(raw_html)
        draws = self.parse_draws_from_next_data(next_data)

        if not draws:
            bac_log(
                "Remote payload produced no draw rows",
                level="ERROR",
                component="scraper",
            )
            raise RuntimeError(
                "No Lotto rows parsed from the source payload. The website structure may have changed."
            )

        bac_log(
            "Remote Lotto history parsed",
            component="scraper",
            earliest_date=draws[0].draw_date.isoformat(),
            latest_date=draws[-1].draw_date.isoformat(),
            row_count=len(draws),
        )
        return draws

    def fetch_html(self, url: str) -> str:
        """Download the source HTML with a browser-like user agent."""
        bac_log(
            "Opening remote history page",
            component="scraper",
            timeout_seconds=self.timeout_seconds,
        )
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
                bac_log(
                    "Remote history request failed",
                    level="ERROR",
                    component="scraper",
                    http_status=status,
                )
                raise RuntimeError(f"Unexpected HTTP status: {status}")
            response_body = response.read()
            bac_log(
                "Remote history page downloaded",
                component="scraper",
                bytes_received=len(response_body),
                http_status=status,
            )
            return response_body.decode("utf-8", errors="replace")

    @staticmethod
    def extract_next_data_json(raw_html: str) -> dict:
        """Extract the embedded Next.js JSON payload from the downloaded page."""
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">([\s\S]*?)</script>',
            raw_html,
            flags=re.IGNORECASE,
        )
        if not match:
            bac_log(
                "Next.js data payload was not found",
                level="ERROR",
                component="scraper",
                html_characters=len(raw_html),
            )
            raise RuntimeError("Could not locate __NEXT_DATA__ payload in the source HTML.")
        payload = json.loads(match.group(1))
        bac_log(
            "Next.js data payload extracted",
            component="scraper",
            payload_characters=len(match.group(1)),
        )
        return payload

    @staticmethod
    def parse_draws_from_next_data(next_data: dict) -> list[LottoDraw]:
        """Translate supported payload entries and remove duplicate draw dates."""
        page_props = next_data.get("props", {}).get("pageProps", {})
        entries = page_props.get("list", [])
        draws: list[LottoDraw] = []
        skipped_entries = 0

        bac_log(
            "Parsing remote draw entries",
            component="scraper",
            entry_count=len(entries),
        )

        for entry in entries:
            standard = entry.get("standard", {})
            grids = standard.get("grids", [])
            draw_dates = standard.get("drawDates", [])

            if not grids or not draw_dates:
                skipped_entries += 1
                continue

            first_grid = grids[0]
            standard_lines = first_grid.get("standard", [])
            additional_lines = first_grid.get("additional", [])

            if not standard_lines or len(standard_lines[0]) != 6:
                skipped_entries += 1
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

        parsed_draws = sorted(deduplicated.values(), key=lambda item: item.draw_date)
        bac_log(
            "Remote draw entries parsed",
            component="scraper",
            duplicate_rows=len(draws) - len(parsed_draws),
            parsed_rows=len(parsed_draws),
            skipped_entries=skipped_entries,
        )
        return parsed_draws
