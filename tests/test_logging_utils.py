# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Structured BAC logger regression tests."""

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from predictor_web.logging_utils import bac_log


class BacLogTests(unittest.TestCase):
    """Verify the stable fields relied on during terminal diagnostics."""

    def test_bac_log_includes_level_component_message_and_context(self) -> None:
        """One event is emitted as a complete structured terminal line."""
        output = io.StringIO()

        # Redirecting stdout keeps the test deterministic without changing logger code.
        with patch.dict(os.environ, {"BAC_LOG_LEVEL": "INFO"}):
            with redirect_stdout(output):
                bac_log(
                    "Test event",
                    level="WARNING",
                    component="tests",
                    row_count=3,
                )

        log_line = output.getvalue()
        self.assertIn("BAC_LOG |", log_line)
        self.assertIn("| WARNING | tests | Test event", log_line)
        self.assertIn("row_count=3", log_line)
