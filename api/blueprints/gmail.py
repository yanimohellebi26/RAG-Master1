"""
Gmail Blueprint -- /api/gmail/* routes.

Endpoints :
    GET  /api/gmail/status     -- Statut du service Gmail
    POST /api/gmail/connect    -- Tester la connexion IMAP
    GET  /api/gmail/unread     -- Lister les mails non lus (auto-classifies)
    GET  /api/gmail/email/<uid> -- Lire un mail complet
    GET  /api/gmail/email/<uid>/attachment/<int:part_index> -- Telecharger PJ
    POST /api/gmail/summarize  -- Resumer les non-lus (LLM)
    POST /api/gmail/draft      -- Redaction assistee (LLM)
    POST /api/gmail/send       -- Envoyer un mail (JSON ou multipart/form-data)
    GET  /api/gmail/categories -- Categories et mapping
    POST /api/gmail/categorize -- Assigner une categorie
    DELETE /api/gmail/categorize/<uid> -- Retirer une categorie
    POST /api/gmail/email-status -- Changer le statut d'un mail
"""

import io
import logging
import time

from flask import Blueprint, jsonify, request, send_file

from api.services.gmail import gmail_service

logger = logging.getLogger(__name__)
gmail_bp = Blueprint("gmail", __name__)

# Simple in-memory rate limiter for LLM endpoints
_llm_last_call: dict[str, float] = {}
_LLM_COOLDOWN = 5  # seconds between LLM calls per endpoint


def _check_llm_rate_limit(endpoint: str) -> str | None:
    """Return error message if rate limited, None otherwise."""
    now = time.time()
    last = _llm_last_call.get(endpoint, 0)
    if now - last < _LLM_COOLDOWN:
        remaining = int(_LLM_COOLDOWN - (now - last)) + 1
        return f"Veuillez patienter {remaining}s avant de relancer cette action."
    _llm_last_call[endpoint] = now
    return None


# ---------------------------------------------------------------------------
# Status & connect
# ---------------------------------------------------------------------------

@gmail_bp.route("/gmail/status", methods=["GET"])
def gmail_status():
    """Check Gmail service availability and connection status."""
    from core.config import CONFIG
    mcp_cfg = CONFIG.get("mcp", {}).get("gmail", {})

    return jsonify({
        "available": gmail_service.available,
        "connected": gmail_service.connected,
        "enabled": mcp_cfg.get("enabled", False),
        "address": gmail_service.address,
        "message": (
            "Gmail connecte et pret"
            if gmail_service.connected
            else (
                "Variables GMAIL_ADDRESS / GMAIL_APP_PASSWORD manquantes dans .env"
                if not gmail_service.available
                else (
                    "Service non active dans config.yaml"
                    if not mcp_cfg.get("enabled", False)
                    else "Non connecte — cliquez Connecter"
                )
            )
        ),
    })


@gmail_bp.route("/gmail/connect", methods=["POST"])
def connect_gmail():
    """Test IMAP connection with App Password."""
    if not gmail_service.available:
        return jsonify({
            "error": "Variables GMAIL_ADDRESS / GMAIL_APP_PASSWORD manquantes dans .env",
        }), 400

    success = gmail_service.connect()

    return jsonify({
        "connected": success,
        "message": (
            "Connecte a Gmail"
            if success
            else "Connexion echouee — verifiez l'App Password"
        ),
    })


# ---------------------------------------------------------------------------
# Read emails
# ---------------------------------------------------------------------------

@gmail_bp.route("/gmail/unread", methods=["GET"])
def list_unread():
    """List emails with auto-classification and pagination."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    date_filter = request.args.get("filter", "month")
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    try:
        result = gmail_service.fetch_emails(
            date_filter=date_filter, page=page, page_size=page_size,
        )
        # Auto-classify fetched emails
        enriched = gmail_service.auto_classify_emails(result["emails"])

        # Compute global category counts from all stored emails
        cat_data = gmail_service.get_categories()
        global_counts: dict[str, int] = {}
        for info in cat_data.get("emails", {}).values():
            cat = info.get("category", "Personnel")
            global_counts[cat] = global_counts.get(cat, 0) + 1

        return jsonify({
            "emails": enriched,
            "count": len(enriched),
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"],
            "category_counts": global_counts,
        })
    except Exception as exc:
        logger.error("Gmail fetch_emails failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/email/<uid>", methods=["GET"])
def read_email(uid: str):
    """Read a single email by UID."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    try:
        result = gmail_service.fetch_email(uid)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail fetch_email failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/email/<uid>/attachment/<int:part_index>", methods=["GET"])
def download_attachment(uid: str, part_index: int):
    """Download an attachment from an email."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    if part_index < 0:
        return jsonify({"error": "part_index invalide"}), 400

    try:
        result = gmail_service.download_attachment(uid, part_index)
        if "error" in result:
            return jsonify(result), 404
        return send_file(
            io.BytesIO(result["data"]),
            mimetype=result["content_type"],
            as_attachment=True,
            download_name=result["filename"],
        )
    except Exception as exc:
        logger.error("Gmail download_attachment failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

@gmail_bp.route("/gmail/summarize", methods=["POST"])
def summarize_unread():
    """Summarize emails using LLM. Optionally pass uids to summarize specific emails."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    rate_err = _check_llm_rate_limit("summarize")
    if rate_err:
        return jsonify({"error": rate_err}), 429

    data = request.get_json() or {}
    max_results = min(data.get("max_results", 20), 50)
    uids = data.get("uids")

    # Validate uids: must be a list of strings, max 30
    if uids is not None:
        if not isinstance(uids, list):
            return jsonify({"error": "uids doit etre une liste"}), 400
        uids = [str(u) for u in uids[:30]]
        if not uids:
            uids = None

    try:
        result = gmail_service.summarize_unread(max_results=max_results, uids=uids)
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail summarize failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/classify-ai", methods=["POST"])
def classify_ai():
    """Force LLM reclassification of emails stuck in 'Personnel'."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    rate_err = _check_llm_rate_limit("classify-ai")
    if rate_err:
        return jsonify({"error": rate_err}), 429

    try:
        result = gmail_service.classify_ai_fallback()
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail classify-ai failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/draft", methods=["POST"])
def draft_reply():
    """Generate a draft reply for an email."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    rate_err = _check_llm_rate_limit("draft")
    if rate_err:
        return jsonify({"error": rate_err}), 429

    data = request.get_json() or {}
    uid = data.get("uid")
    instructions = data.get("instructions", "")

    if not instructions:
        return jsonify({"error": "instructions requis"}), 400

    try:
        if uid:
            result = gmail_service.draft_reply(uid=uid, instructions=instructions)
        else:
            result = gmail_service.improve_text(text=instructions)
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail draft failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@gmail_bp.route("/gmail/categories", methods=["GET"])
def get_categories():
    """Return categories definitions and email-category mapping."""
    try:
        result = gmail_service.get_categories()
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail get_categories failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/categorize", methods=["POST"])
def categorize_email():
    """Assign a category to an email."""
    data = request.get_json() or {}
    uid = data.get("uid")
    category = data.get("category")

    if not uid or not category:
        return jsonify({"error": "uid et category requis"}), 400

    try:
        result = gmail_service.set_email_category(uid=uid, category=category)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail categorize failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


@gmail_bp.route("/gmail/categorize/<uid>", methods=["DELETE"])
def uncategorize_email(uid: str):
    """Remove category from an email."""
    try:
        result = gmail_service.remove_email_category(uid=uid)
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail uncategorize failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Email status
# ---------------------------------------------------------------------------

@gmail_bp.route("/gmail/email-status", methods=["POST"])
def set_email_status():
    """Set email status (Nouveau / En cours / Traite)."""
    data = request.get_json() or {}
    uid = data.get("uid")
    status = data.get("status")

    if not uid or not status:
        return jsonify({"error": "uid et status requis"}), 400

    try:
        result = gmail_service.set_email_status(uid=uid, status=status)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:
        logger.error("Gmail set_email_status failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------

BLOCKED_EXTENSIONS = {".exe", ".bat", ".sh", ".cmd"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES = 5


@gmail_bp.route("/gmail/send", methods=["POST"])
def send_email():
    """Send an email (JSON or multipart/form-data with attachments)."""
    if not gmail_service.connected:
        return jsonify({"error": "Gmail non connecte"}), 400

    # Detect multipart/form-data vs JSON
    if request.content_type and "multipart/form-data" in request.content_type:
        to = (request.form.get("to") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        body = (request.form.get("body") or "").strip()
        files = request.files.getlist("attachments")

        # Validate file constraints
        if len(files) > MAX_FILES:
            return jsonify({"error": f"Maximum {MAX_FILES} fichiers autorises"}), 400

        attachments = []
        for f in files:
            ext = ("." + f.filename.rsplit(".", 1)[-1]).lower() if "." in (f.filename or "") else ""
            if ext in BLOCKED_EXTENSIONS:
                return jsonify({"error": f"Type de fichier interdit: {ext}"}), 400
            data = f.read()
            if len(data) > MAX_FILE_SIZE:
                return jsonify({"error": f"Fichier trop volumineux: {f.filename} (max 10 MB)"}), 400
            attachments.append((f.filename, f.content_type or "application/octet-stream", data))
    else:
        data = request.get_json() or {}
        to = data.get("to", "").strip()
        subject = data.get("subject", "").strip()
        body = data.get("body", "").strip()
        attachments = None

    if not to or not subject or not body:
        return jsonify({"error": "to, subject et body requis"}), 400

    try:
        result = gmail_service.send_email(
            to=to, subject=subject, body=body,
            attachments=attachments if attachments else None,
        )
        if result.get("success"):
            return jsonify(result)
        return jsonify(result), 500
    except Exception as exc:
        logger.error("Gmail send failed: %s", exc)
        return jsonify({"error": str(exc)}), 500
