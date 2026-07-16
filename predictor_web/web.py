# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Threaded WSGI application, API routes, static serving, and request logging."""

import json
from socketserver import ThreadingMixIn
from time import perf_counter
from typing import Callable, Iterable
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from predictor_web.config import AppConfig, load_config
from predictor_web.logging_utils import bac_log
from predictor_web.services import LotteryService

ResponseIterable = Iterable[bytes]
StartResponse = Callable[[str, list[tuple[str, str]]], None]


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Allow independent browser requests to execute concurrently."""

    daemon_threads = True


class BacLogRequestHandler(WSGIRequestHandler):
    """Route the standard WSGI access line through the shared BAC logger."""

    def log_message(self, format_string: str, *args) -> None:
        bac_log(
            format_string % args,
            component="wsgi",
            client=self.client_address[0],
        )


class PredictorWebApp:
    """Dispatch WSGI requests to dashboard files or JSON service operations."""

    def __init__(self, config: AppConfig, service: LotteryService) -> None:
        self.config = config
        self.service = service
        # Explicit static routes keep the standard-library server small and predictable.
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
        bac_log(
            "Web application initialized",
            component="web",
            static_routes=len(self.static_routes),
        )

    def __call__(self, environ: dict, start_response: StartResponse) -> ResponseIterable:
        """Handle one WSGI request and emit a duration-aware access event."""
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/")) or "/"
        query_string = str(environ.get("QUERY_STRING", ""))
        client = str(environ.get("REMOTE_ADDR", "unknown"))
        request_started = perf_counter()
        response_status = "500 Internal Server Error"
        original_start_response = start_response

        # Capture status without changing route response construction.
        def tracked_start_response(
            status: str,
            headers: list[tuple[str, str]],
        ) -> None:
            nonlocal response_status
            response_status = status
            original_start_response(status, headers)

        start_response = tracked_start_response
        bac_log(
            "HTTP request received",
            component="web",
            client=client,
            method=method,
            path=path,
            query=query_string or None,
        )

        try:
            # Dashboard document and its two local static assets.
            if method == "GET" and path == "/":
                return self._serve_file(
                    start_response,
                    self.config.template_dir / "index.html",
                    "text/html; charset=utf-8",
                )

            if method == "GET" and path in self.static_routes:
                file_path, content_type = self.static_routes[path]
                return self._serve_file(start_response, file_path, content_type)

            # JSON API routes are kept thin and delegate business work to the service.
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
            bac_log(
                "HTTP request validation failed",
                level="WARNING",
                component="web",
                error=str(error),
                method=method,
                path=path,
            )
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="400 Bad Request",
            )
        except FileNotFoundError as error:
            bac_log(
                "HTTP request could not find required data",
                level="ERROR",
                component="web",
                error=str(error),
                method=method,
                path=path,
            )
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="503 Service Unavailable",
            )
        except RuntimeError as error:
            bac_log(
                "HTTP operation failed",
                level="ERROR",
                component="web",
                error=str(error),
                method=method,
                path=path,
            )
            return self._json_response(
                start_response,
                {"error": str(error)},
                status="500 Internal Server Error",
            )
        except Exception as error:  # pragma: no cover - safety net
            bac_log(
                "Unhandled HTTP error",
                level="ERROR",
                component="web",
                error=repr(error),
                method=method,
                path=path,
            )
            return self._json_response(
                start_response,
                {"error": "Unexpected server error."},
                status="500 Internal Server Error",
            )
        finally:
            bac_log(
                "HTTP request completed",
                component="web",
                duration_ms=round((perf_counter() - request_started) * 1000, 2),
                method=method,
                path=path,
                status=response_status.split(" ", 1)[0],
            )

    @staticmethod
    def _query_params(environ: dict) -> dict[str, str]:
        """Flatten the first value for each URL query parameter."""
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
        """Parse a required-or-default bounded integer query parameter."""
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
        """Parse a bounded optional integer query parameter."""
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
        """Read and return one trusted local dashboard asset."""
        body = file_path.read_bytes()
        bac_log(
            "Serving local web asset",
            level="DEBUG",
            component="web",
            bytes_sent=len(body),
            file_name=file_path.name,
        )
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
        """Encode a dictionary as a UTF-8 JSON WSGI response."""
        body = json.dumps(payload).encode("utf-8")
        bac_log(
            "Encoding JSON response",
            level="DEBUG",
            component="web",
            bytes_sent=len(body),
            payload_keys=sorted(payload),
            status=status.split(" ", 1)[0],
        )
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
    """Create a web application with injectable dependencies for testing."""
    resolved_config = config or load_config()
    resolved_service = service or LotteryService(resolved_config)
    app = PredictorWebApp(resolved_config, resolved_service)
    bac_log(
        "WSGI application created",
        component="web",
        injected_service=service is not None,
    )
    return app


def run_dev_server(
    config: AppConfig | None = None,
    app: PredictorWebApp | None = None,
) -> None:
    """Run the local threaded development server until interrupted."""
    # Reuse an exported WSGI instance when app.py has already created one.
    resolved_config = config or (app.config if app is not None else load_config())
    resolved_app = app or create_app(resolved_config)

    bac_log(
        "Development server starting",
        component="server",
        host=resolved_config.host,
        port=resolved_config.port,
        project=resolved_config.project_name,
        version=resolved_config.release_version,
    )

    with make_server(
        resolved_config.host,
        resolved_config.port,
        resolved_app,
        server_class=ThreadingWSGIServer,
        handler_class=BacLogRequestHandler,
    ) as server:
        bac_log(
            "Development server ready",
            component="server",
            url=f"http://{resolved_config.host}:{resolved_config.port}",
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            bac_log("Server stopped by user", component="server")
