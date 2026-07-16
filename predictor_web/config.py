# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import os
from dataclasses import dataclass
from pathlib import Path

LICENSE_NAME = "Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial"


@dataclass(frozen=True, slots=True)
class AppConfig:
    base_dir: Path
    csv_path: Path
    static_dir: Path
    template_dir: Path
    source_url: str
    project_name: str
    release_version: str
    number_min: int
    number_max: int
    picks_per_line: int
    default_top_k: int
    default_iterations: int
    default_random_seed: int
    min_history_required: int
    max_top_k: int
    max_iterations: int
    request_timeout_seconds: int
    host: str
    port: int


def load_config() -> AppConfig:
    base_dir = Path(__file__).resolve().parent.parent

    return AppConfig(
        base_dir=base_dir,
        csv_path=base_dir / os.getenv("PREDICTOR_DATA_FILE", "irish_lotto_results.csv"),
        static_dir=base_dir / "predictor_web" / "static",
        template_dir=base_dir / "predictor_web" / "templates",
        source_url=os.getenv("PREDICTOR_SOURCE_URL", "https://www.lottery.ie/results/lotto/history"),
        project_name="Irish Lotto Predictor",
        release_version=os.getenv("PREDICTOR_RELEASE_VERSION", "1.0.0"),
        number_min=1,
        number_max=47,
        picks_per_line=6,
        default_top_k=int(os.getenv("PREDICTOR_DEFAULT_TOP_K", "5")),
        default_iterations=int(os.getenv("PREDICTOR_DEFAULT_ITERATIONS", "50000")),
        default_random_seed=int(os.getenv("PREDICTOR_RANDOM_SEED", "20260712")),
        min_history_required=int(os.getenv("PREDICTOR_MIN_HISTORY", "10")),
        max_top_k=int(os.getenv("PREDICTOR_MAX_TOP_K", "50")),
        max_iterations=int(os.getenv("PREDICTOR_MAX_ITERATIONS", "200000")),
        request_timeout_seconds=int(os.getenv("PREDICTOR_HTTP_TIMEOUT", "30")),
        host=os.getenv("PREDICTOR_HOST", "127.0.0.1"),
        port=int(os.getenv("PREDICTOR_PORT", "8080")),
    )
