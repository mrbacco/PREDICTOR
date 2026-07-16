# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Command-line entrypoint for refreshing the local Lotto history CSV."""

from predictor_web.logging_utils import bac_log
from predictor_web.services import LotteryService


def main() -> None:
    """Fetch remote history and replace the configured local repository file."""
    bac_log("Dataset refresh CLI started", component="cli")
    service = LotteryService()
    result = service.refresh_data()
    bac_log(
        "Dataset refresh CLI completed",
        component="cli",
        latest_draw_date=result["latest_draw_date"],
        rows_written=result["rows_written"],
    )


if __name__ == "__main__":
    main()
