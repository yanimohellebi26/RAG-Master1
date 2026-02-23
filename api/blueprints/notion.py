"""
Notion Blueprint -- /api/notion/* routes.

Endpoints :
    GET  /api/notion/status              -- Statut du service Notion
    GET  /api/notion/oauth/authorize     -- Lancer le flux OAuth Notion
    GET  /api/notion/oauth/callback      -- Callback OAuth (recoit le token)
    POST /api/notion/connect             -- Connecter au service Notion
    POST /api/notion/search              -- Rechercher des pages
    GET  /api/notion/pages/<page_id>     -- Recuperer une page
    POST /api/notion/save-synthesis      -- Sauvegarder une synthese de chat
    POST /api/notion/sync                -- Synchroniser les pages vers ChromaDB
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import httpx
from flask import Blueprint, jsonify, redirect, request

from api.services.notion import notion_service

logger = logging.getLogger(__name__)
notion_bp = Blueprint("notion", __name__)

# Path to persist the OAuth token between restarts
_TOKEN_PATH = Path(__file__).resolve().parent.parent.parent / "credentials" / "notion_token.json"


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


def _load_saved_token() -> str | None:
    """Load a previously saved OAuth access token."""
    if _TOKEN_PATH.exists():
        try:
            data = json.loads(_TOKEN_PATH.read_text())
            return data.get("access_token")
        except Exception:
            pass
    return None


def _save_token(token_data: dict) -> None:
    """Persist the OAuth token to disk."""
    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    logger.info("Notion OAuth token saved to %s", _TOKEN_PATH)


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------

@notion_bp.route("/notion/oauth/authorize", methods=["GET"])
def oauth_authorize():
    """Redirect the user to Notion's OAuth authorization page."""
    client_id = os.getenv("NOTION_CLIENT_ID", "")
    redirect_uri = os.getenv("NOTION_REDIRECT_URI", "http://localhost:5000/api/notion/oauth/callback")

    if not client_id:
        return jsonify({"error": "NOTION_CLIENT_ID not configured"}), 400

    auth_url = (
        f"https://api.notion.com/v1/oauth/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&owner=user"
        f"&redirect_uri={redirect_uri}"
    )
    return redirect(auth_url)


@notion_bp.route("/notion/oauth/callback", methods=["GET"])
def oauth_callback():
    """Handle the OAuth callback from Notion, exchange code for access token."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>Connexion Notion echouee</h2>
        <p>Erreur : {error}</p>
        <a href="/">Retour</a>
        </body></html>
        """, 400

    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    client_id = os.getenv("NOTION_CLIENT_ID", "")
    client_secret = os.getenv("NOTION_CLIENT_SECRET", "")
    redirect_uri = os.getenv("NOTION_REDIRECT_URI", "http://localhost:5000/api/notion/oauth/callback")

    if not client_id or not client_secret:
        return jsonify({"error": "NOTION_CLIENT_ID or NOTION_CLIENT_SECRET not configured"}), 500

    # Exchange the authorization code for an access token
    try:
        resp = httpx.post(
            "https://api.notion.com/v1/oauth/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(client_id, client_secret),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        token_data = resp.json()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text
        logger.error("Notion OAuth token exchange failed: %s", body)
        return f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px">
        <h2>Echange de token echoue</h2>
        <p>{body}</p>
        <a href="/">Retour</a>
        </body></html>
        """, 400
    except Exception as exc:
        logger.error("Notion OAuth error: %s", exc)
        return jsonify({"error": str(exc)}), 500

    access_token = token_data.get("access_token", "")
    workspace_name = token_data.get("workspace_name", "")

    if not access_token:
        return jsonify({"error": "No access_token in response", "details": token_data}), 500

    # Save the token
    _save_token(token_data)

    # Connect the service with the new token
    notion_service.set_access_token(access_token)
    success = _run_async(notion_service.connect())

    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px">
    <h2>Notion connecte !</h2>
    <p>Workspace : <strong>{workspace_name}</strong></p>
    <p>{"Connexion active" if success else "Token recu mais connexion echouee"}</p>
    <a href="/" style="display:inline-block;margin-top:20px;padding:10px 20px;background:#667eea;color:#fff;border-radius:8px;text-decoration:none">
      Retour a l'application
    </a>
    </body></html>
    """


# ---------------------------------------------------------------------------
# Status & connect
# ---------------------------------------------------------------------------

@notion_bp.route("/notion/status", methods=["GET"])
def notion_status():
    """Check Notion service availability and connection status."""
    has_token = bool(_load_saved_token())
    return jsonify({
        "available": notion_service.available,
        "connected": notion_service.connected,
        "has_token": has_token,
        "oauth_url": "/api/notion/oauth/authorize",
        "message": (
            "Notion connecte et pret"
            if notion_service.connected
            else (
                "notion-client non installe. Run: pip install notion-client"
                if not notion_service.available
                else (
                    "Token OAuth disponible — cliquez Connecter"
                    if has_token
                    else "Non connecte — cliquez pour autoriser via Notion"
                )
            )
        ),
    })


@notion_bp.route("/notion/connect", methods=["POST"])
def connect_notion():
    """Connect to Notion API using saved OAuth token."""
    if not notion_service.available:
        return jsonify({
            "error": "notion-client non installe. Run: pip install notion-client",
        }), 400

    # Try to load saved token
    token = _load_saved_token()
    if token:
        notion_service.set_access_token(token)

    success = _run_async(notion_service.connect())

    if not success and not token:
        return jsonify({
            "connected": False,
            "needs_oauth": True,
            "oauth_url": "/api/notion/oauth/authorize",
            "message": "Aucun token. Autorisez via OAuth d'abord.",
        })

    return jsonify({
        "connected": success,
        "message": "Connecte a Notion" if success else "Token invalide — re-autorisez via OAuth",
    })


# ---------------------------------------------------------------------------
# Page operations
# ---------------------------------------------------------------------------

@notion_bp.route("/notion/search", methods=["POST"])
def search_pages():
    """Search Notion pages."""
    data = request.get_json()
    if not data or not data.get("query"):
        return jsonify({"error": "query is required"}), 400

    if not notion_service.connected:
        return jsonify({"error": "Notion non connecte"}), 400

    try:
        result = notion_service.search_pages(data["query"])
        return jsonify(result)
    except Exception as exc:
        logger.error("Notion search failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@notion_bp.route("/notion/pages/<page_id>", methods=["GET"])
def get_page(page_id: str):
    """Get a Notion page content."""
    if not notion_service.connected:
        return jsonify({"error": "Notion non connecte"}), 400

    try:
        result = notion_service.get_page(page_id)
        return jsonify(result)
    except Exception as exc:
        logger.error("Notion get_page failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@notion_bp.route("/notion/save-synthesis", methods=["POST"])
def save_synthesis():
    """Save a chat synthesis to Notion."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Requete invalide"}), 400

    title = data.get("title", "")
    messages = data.get("messages", [])
    sources = data.get("sources", [])
    subjects = data.get("subjects", [])

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not messages:
        return jsonify({"error": "messages is required"}), 400

    if not notion_service.connected:
        # Try to auto-connect with saved token
        token = _load_saved_token()
        if token:
            notion_service.set_access_token(token)
            success = _run_async(notion_service.connect())
            if not success:
                return jsonify({"error": "Notion non connecte", "needs_oauth": True}), 400
        else:
            return jsonify({"error": "Notion non connecte", "needs_oauth": True}), 400

    try:
        result = notion_service.save_synthesis(
            title=title,
            messages=messages,
            sources=sources,
            subjects=subjects,
        )
        return jsonify(result)
    except Exception as exc:
        logger.error("Notion save_synthesis failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@notion_bp.route("/notion/pages", methods=["GET"])
def list_pages():
    """List available Notion pages for selective indexation."""
    if not notion_service.connected:
        # Try auto-connect
        token = _load_saved_token()
        if token:
            notion_service.set_access_token(token)
            _run_async(notion_service.connect())
        if not notion_service.connected:
            return jsonify({"error": "Notion non connecte"}), 400

    try:
        pages = notion_service.list_pages()
        return jsonify({"pages": pages, "total": len(pages)})
    except Exception as exc:
        logger.error("Notion list pages failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@notion_bp.route("/notion/sync", methods=["POST"])
def sync_pages():
    """Sync Notion pages into ChromaDB. Send page_ids to sync selectively."""
    if not notion_service.connected:
        return jsonify({"error": "Notion non connecte"}), 400

    data = request.get_json() or {}
    page_ids = data.get("page_ids", [])

    try:
        if page_ids:
            result = notion_service.sync_selected_pages(page_ids)
        else:
            database_id = data.get("database_id", "")
            result = notion_service.sync_pages(database_id)
        return jsonify(result)
    except Exception as exc:
        logger.error("Notion sync failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
