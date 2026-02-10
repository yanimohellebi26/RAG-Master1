"""
API package -- Flask application factory.

Usage:
    from api import create_app
    app = create_app()
"""

import logging
import os
import secrets

from flask import Flask

from api.services.rag import rag_service
from api.blueprints.chat import chat_bp
from api.blueprints.copilot import copilot_bp
from api.blueprints.evaluation import eval_bp
from api.blueprints.config import config_bp

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory -- creates and configures the Flask instance."""
    dist_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
    )

    app = Flask(
        __name__,
        template_folder=dist_dir,
        static_folder=os.path.join(dist_dir, "assets"),
    )
    app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

    if not os.getenv("FLASK_SECRET_KEY"):
        logger.warning(
            "FLASK_SECRET_KEY not set — using random key. "
            "Sessions will not survive restarts."
        )

    # -- CORS headers for development --------------------------------------
    @app.after_request
    def add_cors_headers(response):
        origin = os.getenv("CORS_ORIGIN", "")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    # -- Initialise shared services -----------------------------------------
    rag_service.init_app(app)

    # -- Register blueprints ------------------------------------------------
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(copilot_bp, url_prefix="/api")
    app.register_blueprint(eval_bp, url_prefix="/api")
    app.register_blueprint(config_bp, url_prefix="/api")

    # -- SPA catch-all routes -----------------------------------------------
    _register_spa_routes(app, dist_dir)

    return app


def _register_spa_routes(app: Flask, dist_dir: str) -> None:
    """Register routes that serve the React single-page application."""
    from flask import send_from_directory

    @app.route("/")
    def serve_index():
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        return "Frontend not built. Run: cd frontend && npm run build", 500

    @app.route("/assets/<path:path>")
    def serve_assets(path: str):
        assets_dir = os.path.join(dist_dir, "assets")
        if os.path.exists(assets_dir):
            return send_from_directory(assets_dir, path)
        return "Asset not found", 404

    # Catch-all for client-side routing (React Router)
    @app.route("/<path:path>")
    def spa_fallback(path: str):
        """Forward unknown paths to React Router."""
        # Don't catch API routes or actual static files
        if path.startswith("api/") or path.startswith("assets/"):
            return "Not found", 404
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        return "Frontend not built. Run: cd frontend && npm run build", 500
