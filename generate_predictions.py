# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Command-line entrypoint for generating and printing ranked predictions."""

from predictor_web.logging_utils import bac_log
from predictor_web.services import LotteryService


def main() -> None:
    """Generate the configured default report and print readable ticket lines."""
    bac_log("Prediction CLI started", component="cli")
    service = LotteryService()
    report = service.generate_predictions()

    bac_log(
        "Printing prediction report",
        component="cli",
        line_count=len(report["lines"]),
    )
    print(f"\nTop {report['top_k']} Optimized Lines:\n")
    for line in report["lines"]:
        print(
            f"{line['rank']:02d}. {line['numbers']} + bonus {line['bonus']}   "
            f"score={line['score']:.2f}"
        )

    bac_log(
        "Prediction CLI completed",
        component="cli",
        candidate_count=report["candidate_count"],
        returned_lines=len(report["lines"]),
    )


if __name__ == "__main__":
    main()
