# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""In-process WSGI tests for health, summary, prediction, and validation routes."""

import io
import json
import tempfile
import unittest
from pathlib import Path

from predictor_web.services import LotteryService
from predictor_web.web import create_app
from tests.test_support import build_test_config, write_sample_csv


class PredictorWebAppTests(unittest.TestCase):
    """Call the WSGI application directly without opening a network socket."""

    def test_health_and_summary_endpoints(self) -> None:
        """Health and dashboard summary endpoints return successful JSON payloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = build_test_config(root)
            write_sample_csv(config.csv_path)

            app = create_app(config, LotteryService(config))

            health_status, _, health_body = self._request(app, "/api/health")
            summary_status, _, summary_body = self._request(app, "/api/summary")

            self.assertEqual(health_status, "200 OK")
            self.assertEqual(summary_status, "200 OK")
            self.assertEqual(json.loads(health_body)["status"], "ok")
            self.assertEqual(json.loads(summary_body)["total_draws"], 12)

    def test_predictions_endpoint_returns_payload(self) -> None:
        """Prediction responses include ranked lines and distinct bonus values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = build_test_config(root)
            write_sample_csv(config.csv_path)

            app = create_app(config, LotteryService(config))
            status, _, body = self._request(
                app,
                "/api/predictions?top_k=3&iterations=500&seed=99",
            )

            payload = json.loads(body)
            self.assertEqual(status, "200 OK")
            self.assertEqual(len(payload["lines"]), 3)
            self.assertEqual(payload["top_k"], 3)
            for line in payload["lines"]:
                self.assertIn("bonus", line)
                self.assertNotIn(line["bonus"], line["numbers"])

    def test_predictions_endpoint_validates_limits(self) -> None:
        """Out-of-range query parameters return a descriptive client error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = build_test_config(root)
            write_sample_csv(config.csv_path)

            app = create_app(config, LotteryService(config))
            status, _, body = self._request(app, "/api/predictions?top_k=999")

            self.assertEqual(status, "400 Bad Request")
            self.assertIn("top_k", json.loads(body)["error"])

    @staticmethod
    def _request(app, path: str, method: str = "GET") -> tuple[str, dict[str, str], str]:
        """Build a minimal WSGI environment and capture the complete response."""
        query_string = ""
        path_info = path
        if "?" in path:
            path_info, query_string = path.split("?", 1)

        captured: dict[str, object] = {}

        # WSGI communicates status and headers through this callback.
        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path_info,
            "QUERY_STRING": query_string,
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(b""),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        body = b"".join(app(environ, start_response)).decode("utf-8")
        return (
            str(captured["status"]),
            dict(captured["headers"]),
            body,
        )


if __name__ == "__main__":
    unittest.main()
