# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Small structured terminal logger shared by every application layer."""

import json
import os
from datetime import datetime
from threading import Lock
from typing import Any

# Numeric priorities make the environment-controlled minimum level inexpensive.
_LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}
_PRINT_LOCK = Lock()


def bac_log(
    message: str,
    *,
    level: str = "INFO",
    component: str = "application",
    **context: Any,
) -> None:
    """Write one timestamped BAC_LOG event to the active terminal."""
    normalized_level = level.upper()
    if normalized_level not in _LOG_LEVELS:
        normalized_level = "INFO"

    configured_level = os.getenv("BAC_LOG_LEVEL", "INFO").upper()
    minimum_priority = _LOG_LEVELS.get(configured_level, _LOG_LEVELS["INFO"])
    if _LOG_LEVELS[normalized_level] < minimum_priority:
        return

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    context_text = " ".join(
        f"{key}={_format_context_value(value)}"
        for key, value in sorted(context.items())
    )
    suffix = f" | {context_text}" if context_text else ""
    output = (
        f"BAC_LOG | {timestamp} | {normalized_level:<7} | "
        f"{component} | {message}{suffix}"
    )

    # Requests may run on different WSGI threads, so print complete lines atomically.
    with _PRINT_LOCK:
        print(output, flush=True)


def _format_context_value(value: Any) -> str:
    """Keep structured values compact and unambiguous in plain terminal output."""
    if isinstance(value, (bool, int, float)) or value is None:
        return json.dumps(value)
    return json.dumps(str(value), ensure_ascii=True)
