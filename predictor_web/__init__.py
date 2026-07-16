# Author: mrbacco04@gmail.com
# Month: July 2026
# Release Version: 1.0.0
# License: Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Public package exports for application factories and local server startup."""

from predictor_web.web import create_app, run_dev_server

# Keep the supported package surface explicit for WSGI and external callers.
__all__ = ["create_app", "run_dev_server"]
