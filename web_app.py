"""
RAG Master 1 -- Web application entry point.

Usage:
    python web_app.py
"""

import logging
import os

from core.constants import FLASK_HOST, FLASK_PORT
from api import create_app

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    separator = "=" * 55
    print(separator)
    print("  RAG Master 1 - Interface Web")
    print(f"  http://localhost:{FLASK_PORT}")
    if debug:
        print("  WARNING: Debug mode is ON — do not use in production")
    print(separator)
    app.run(debug=debug, host=FLASK_HOST, port=FLASK_PORT)
