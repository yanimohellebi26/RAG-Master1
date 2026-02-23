"""
Google Drive Blueprint -- /api/gdrive/* routes.

Endpoints :
    GET  /api/gdrive/status            -- Statut du service Google Drive
    POST /api/gdrive/connect           -- Connecter avec service account
    GET  /api/gdrive/files             -- Lister les fichiers d'un dossier
    GET  /api/gdrive/file/<id>/preview -- Apercu du contenu d'un fichier
    POST /api/gdrive/sync              -- Synchroniser vers ChromaDB
"""

import asyncio
import logging

from flask import Blueprint, jsonify, request

from api.services.google_drive import gdrive_service

logger = logging.getLogger(__name__)
gdrive_bp = Blueprint("gdrive", __name__)


def _run_async(coro):
    """Helper pour executer une coroutine async depuis Flask (sync)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Status & connect
# ---------------------------------------------------------------------------

@gdrive_bp.route("/gdrive/status", methods=["GET"])
def gdrive_status():
    """Check Google Drive service availability and connection status."""
    from core.config import CONFIG
    mcp_cfg = CONFIG.get("mcp", {}).get("google-drive", {})

    return jsonify({
        "available": gdrive_service.available,
        "connected": gdrive_service.connected,
        "enabled": mcp_cfg.get("enabled", False),
        "default_folder_id": mcp_cfg.get("default_folder_id", ""),
        "message": (
            "Google Drive connecte et pret"
            if gdrive_service.connected
            else (
                "google-api-python-client non installe. "
                "Run: pip install google-api-python-client google-auth"
                if not gdrive_service.available
                else (
                    "Service non active dans config.yaml"
                    if not mcp_cfg.get("enabled", False)
                    else "Non connecte — cliquez Connecter"
                )
            )
        ),
    })


@gdrive_bp.route("/gdrive/connect", methods=["POST"])
def connect_gdrive():
    """Connect to Google Drive using service account credentials."""
    if not gdrive_service.available:
        return jsonify({
            "error": (
                "google-api-python-client non installe. "
                "Run: pip install google-api-python-client google-auth"
            ),
        }), 400

    success = _run_async(gdrive_service.connect())

    return jsonify({
        "connected": success,
        "message": (
            "Connecte a Google Drive"
            if success
            else "Connexion echouee — verifiez le fichier service account"
        ),
    })


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

@gdrive_bp.route("/gdrive/files", methods=["GET"])
def list_files():
    """List files in a Drive folder."""
    if not gdrive_service.connected:
        return jsonify({"error": "Google Drive non connecte"}), 400

    folder_id = request.args.get("folder_id", "")
    query = request.args.get("query", "")

    try:
        result = gdrive_service.list_files(folder_id=folder_id, query=query)
        return jsonify(result)
    except Exception as exc:
        logger.error("Google Drive list_files failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gdrive_bp.route("/gdrive/file/<file_id>/preview", methods=["GET"])
def preview_file(file_id: str):
    """Preview the text content of a file."""
    if not gdrive_service.connected:
        return jsonify({"error": "Google Drive non connecte"}), 400

    try:
        result = gdrive_service.get_file_content(file_id)
        # Truncate preview to first 2000 chars
        content = result.get("content", "")
        result["preview"] = content[:2000]
        result["truncated"] = len(content) > 2000
        return jsonify(result)
    except Exception as exc:
        logger.error("Google Drive preview failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

@gdrive_bp.route("/gdrive/sync", methods=["POST"])
def sync_files():
    """Sync Drive files into ChromaDB."""
    if not gdrive_service.connected:
        return jsonify({"error": "Google Drive non connecte"}), 400

    data = request.get_json() or {}
    folder_id = data.get("folder_id", "")
    subject = data.get("subject", "")
    file_ids = data.get("file_ids", [])

    if not folder_id and not file_ids:
        return jsonify({"error": "folder_id ou file_ids requis"}), 400

    try:
        if file_ids:
            result = gdrive_service.sync_selected_files(
                file_ids=file_ids, subject=subject
            )
        else:
            result = gdrive_service.sync_folder(
                folder_id=folder_id, subject=subject
            )
        return jsonify(result)
    except Exception as exc:
        logger.error("Google Drive sync failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
