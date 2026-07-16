# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

from predictor_web.logging_utils import bac_log
from predictor_web.services import LotteryService


def main() -> None:
    service = LotteryService()
    report = service.generate_predictions()

    print(f"\nTop {report['top_k']} Optimized Lines:\n")
    for line in report["lines"]:
        print(
            f"{line['rank']:02d}. {line['numbers']} + bonus {line['bonus']}   "
            f"score={line['score']:.2f}"
        )

    bac_log(
        "Generated "
        f"{len(report['lines'])} ranked lines from {report['candidate_count']} valid candidates."
    )


if __name__ == "__main__":
    main()
