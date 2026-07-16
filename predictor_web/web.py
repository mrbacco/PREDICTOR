# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

import json
from socketserver import ThreadingMixIn
from typing import Callable, Iterable
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from predictor_web.config import AppConfig, load_config
from predictor_web.logging_utils import bac_log
from predictor_web.services import LotteryService

ResponseIterable = Iterable[bytes]
StartResponse = Callable[[str, list[tuple[str, str]]], None]


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class PredictorWebApp:
    def __init__(self, config: AppConfig, service: LotteryService) -> None:
        self.config = config
        self.service = service
        self.static_routes = {
            "/static/styles.css": (
                self.config.static_dir / "styles.css",
                "text/css; charset=utf-8",
            ),
            "/static/app.js": (
                self.config.static_dir / "app.js",
                "application/javascript; charset=utf-8",
            ),
        }

    def __call__(self, environ: dict, start_response: StartResponse) -> ResponseIterable:
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/")) or "/"

        try:
            if method == "GET" and path == "/":
                return self._serve_file(
                    start_response,
                    self.config.template_dir / "index.html",
                    "text/html; charset=utf-8",
                )

            if method == "GET" and path in self.static_routes:
                file_path, content_type = self.static_routes[path]
                return self._serve_file(start_response, file_path, content_type)

            if method == "GET" and path == "/api/health":
                return self._json_response(
                    start_response,
                    {
                        "status": "ok",
                        "service": self.config.project_name,
                        "version": self.config.release_version,
                    },
                )

            if method == "GET" and path == "/api/summary":
                return self._json_response(start_response, self.service.get_summary())

            if method == "GET" and path == "/api/draws":
                params = self._query_params(environ)
                limit = self._parse_integer(
                    params.get("limit"),
                    default=12,
                    minimum=1,
                    maximum=50,
                    label="limit",
                )
                return self._json_response(
                    start_response,
                    {"items": self.service.get_recent_draws(limit=limit)},
                )

            if method == "GET" and path == "/api/predictions":
                params = self._query_params(environ)
                top_k = self._parse_optional_integer(
                    params.get("top_k"),
                    minimum=1,
                    maximum=self.config.max_top_k,
                    label="top_k",
                )
                iterations = self._parse_optional_integer(
                    params.get("iterations"),
                    minimum=1,
                    maximum=self.config.max_iterations,
                    label="iterations",
                )
                random_seed = self._parse_optional_integer(
                    params.get("seed"),
                    minimum=0,
                    maximum=999999999,
                    label="seed",
                )
                return self._json_response(
                    start_response,
                    self.service.generate_predictions(
                        top_k=top_k,
                        iterations=iterations,
                        random_seed=random_seed,
                    ),
                )

            if method == "POST" and path == "/api/refresh-data":
                return self._json_response(start_response, self.service.refresh_data())

            if path.startswith("/api/"):
                return self._json_response(
                    start_response,
                    {"error": "API route not found."},
                    status="404 Not Found",
                )

            return self._json_response(
                start_response,
                {"error": "Page not found."},
                status="404 Not Found",
            )
        except ValueError as error:
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="400 Bad Request",
            )
        except FileNotFoundError as error:
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="503 Service Unavailable",
            )
        except RuntimeError as error:
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="500 Internal Server Error",
            )
        except Exception as error:  # pragma: no cover - safety net
            bac_log(f"Unhandled web error on {method} {path}: {error}")
            return self._json_response(
                start_response,
                {"error": "Unexpected server error."},
                status="500 Internal Server Error",
            )

    @staticmethod
    def _query_params(environ: dict) -> dict[str, str]:
        parsed = parse_qs(str(environ.get("QUERY_STRING", "")), keep_blank_values=False)
        return {key: values[0] for key, values in parsed.items() if values}

    @staticmethod
    def _parse_integer(
        raw_value: str | None,
        *,
        default: int,
        minimum: int,
        maximum: int,
        label: str,
    ) -> int:
        if raw_value is None:
            return default
        value = int(raw_value)
        if value < minimum or value > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return value

    @staticmethod
    def _parse_optional_integer(
        raw_value: str | None,
        *,
        minimum: int,
        maximum: int,
        label: str,
    ) -> int | None:
        if raw_value is None:
            return None
        value = int(raw_value)
        if value < minimum or value > maximum:
            raise ValueError(f"{label} must be between {minimum} and {maximum}.")
        return value

    @staticmethod
    def _serve_file(
        start_response: StartResponse,
        file_path,
        content_type: str,
    ) -> ResponseIterable:
        body = file_path.read_bytes()
        start_response(
            "200 OK",
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    @staticmethod
    def _json_response(
        start_response: StartResponse,
        payload: dict,
        *,
        status: str = "200 OK",
    ) -> ResponseIterable:
        body = json.dumps(payload).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]


def create_app(
    config: AppConfig | None = None,
    service: LotteryService | None = None,
) -> PredictorWebApp:
    resolved_config = config or load_config()
    resolved_service = service or LotteryService(resolved_config)
    return PredictorWebApp(resolved_config, resolved_service)


def run_dev_server(config: AppConfig | None = None) -> None:
    resolved_config = config or load_config()
    app = create_app(resolved_config)

    bac_log(
        f"Starting {resolved_config.project_name} v{resolved_config.release_version} "
        f"on http://{resolved_config.host}:{resolved_config.port}"
    )

    with make_server(
        resolved_config.host,
        resolved_config.port,
        app,
        server_class=ThreadingWSGIServer,
        handler_class=WSGIRequestHandler,
    ) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            bac_log("Server stopped by user.")
