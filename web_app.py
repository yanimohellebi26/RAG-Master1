"""
RAG Master 1 -- Web application entry point.

Usage:
    python web_app.py
"""

from core.constants import FLASK_HOST, FLASK_PORT
from api import create_app

app = create_app()

if __name__ == "__main__":
    separator = "=" * 55
    print(separator)
    print("  RAG Master 1 - Interface Web")
    print(f"  http://localhost:{FLASK_PORT}")
    print(separator)
    app.run(debug=True, host=FLASK_HOST, port=FLASK_PORT)
