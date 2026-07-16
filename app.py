# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""WSGI export and local development entrypoint."""

from predictor_web import create_app, run_dev_server
from predictor_web.logging_utils import bac_log

# Production WSGI servers import this object without starting the dev server.
bac_log("Creating exported WSGI application", component="entrypoint")
application = create_app()


if __name__ == "__main__":
    bac_log("Starting application from app.py", component="entrypoint")
    run_dev_server(app=application)
