<!--
Author: mrbacco04@gmail.com
Month: July 2026
Release Version: 1.0.0
License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
-->
# Irish Lotto Predictor

This repository is now structured as a modular web application instead of a single prediction script.

It includes:

- a browser dashboard for recent draws, dataset refreshes, and prediction runs
- a service layer that coordinates scraping, repository access, and prediction logic
- separate modules for configuration, models, analytics, persistence, web routing, and CLI entrypoints
- automated tests for the repository, predictor, and HTTP endpoints

## Architecture

The application is split into focused modules so it can grow cleanly:

- `app.py`: WSGI entrypoint and local development server launcher
- `generate_predictions.py`: CLI command for ranked prediction output
- `scrape_irish_lotto.py`: CLI command that refreshes the CSV dataset
- `predictor_web/config.py`: environment-aware configuration
- `predictor_web/models.py`: typed draw and report models
- `predictor_web/repository.py`: CSV loading and persistence
- `predictor_web/scraper.py`: Irish Lotto source scraping and parsing
- `predictor_web/analytics.py`: frequency, pair, and overdue analysis
- `predictor_web/predictor.py`: Monte Carlo ticket generation engine
- `predictor_web/services.py`: orchestration layer for the web app and CLI tools
- `predictor_web/web.py`: HTTP routes and WSGI app
- `predictor_web/templates/index.html`: dashboard shell
- `predictor_web/static/styles.css`: responsive UI styling
- `predictor_web/static/app.js`: browser-side dashboard behavior
- `tests/`: regression coverage for the refactor

## Features

- Historical Irish Lotto CSV repository with validation and logging
- Weighted prediction engine with modular analysis steps
- JSON API endpoints for health, summary, recent draws, and predictions
- Browser UI for operating the predictor without changing code
- Thin CLI entrypoints so automation scripts can stay simple
- File headers added to every new source file with author, month, version, and license details

## How To Run

From the project root:

1. Refresh the CSV dataset:

```powershell
python scrape_irish_lotto.py
```

2. Start the web application:

```powershell
python app.py
```

3. Open the dashboard in your browser:

```text
http://127.0.0.1:8080
```

4. Optional CLI prediction run:

```powershell
python generate_predictions.py
```

## API Endpoints

- `GET /api/health`
- `GET /api/summary`
- `GET /api/draws?limit=12`
- `GET /api/predictions?top_k=5&iterations=50000&seed=20260712`
- `POST /api/refresh-data`

## Testing

Run the automated checks with:

```powershell
python -m unittest discover -s tests -v
```

## Terminal Logging

All backend layers use the shared `bac_log` utility. Each line includes a timestamp,
severity, component, message, and structured context so requests can be followed from
the web route through repository and predictor operations.

The default level is `INFO`. Set `BAC_LOG_LEVEL` before starting the app to change
terminal verbosity:

```powershell
$env:BAC_LOG_LEVEL = "DEBUG"
python app.py
```

Supported levels are `DEBUG`, `INFO`, `WARNING`, and `ERROR`.

## Scalability Notes

This codebase is now organized around layers that can scale independently:

- the UI is isolated from the prediction engine behind HTTP endpoints
- the service layer keeps orchestration separate from storage and analytics
- the repository layer can later move from CSV to a database without rewriting the predictor
- the WSGI app can be hosted behind a production web server when you are ready to deploy

## Licensing

This repository supports multiple licensing paths:

1. Apache License 2.0: see `LICENSE-APACHE`
2. GNU AGPL v3: see `LICENSE-AGPL`
3. Commercial license: see `COMMERCIAL-LICENSE.md`

For commercial licensing requests, contact `mrbacco04@gmail.com`.
