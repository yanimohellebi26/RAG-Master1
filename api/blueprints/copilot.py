"""
Copilot Blueprint -- /api/copilot routes.
"""

import logging
from typing import Any

from flask import Blueprint, jsonify, request

from core.constants import COPILOT_MAX_CONTENT_LENGTH, TOOL_LABELS
from core.validators import validate_question
from tools.copilot import (
    COPILOT_SDK_AVAILABLE,
    copilot_generate,
)

logger = logging.getLogger(__name__)
copilot_bp = Blueprint("copilot", __name__)

_VALID_TOOL_TYPES: frozenset[str] = frozenset(TOOL_LABELS.keys())


@copilot_bp.route("/copilot", methods=["POST"])
def copilot_tool():
    """Generate Copilot tool content (quiz, table, chart, etc.)."""
    data: dict[str, Any] | None = request.json
    if not data:
        return jsonify({"error": "Requete invalide"}), 400

    tool_type: str = data.get("tool_type", "")
    content: str = data.get("content", "")
    model: str = data.get("model", "gpt-4o")
    sources: list[dict[str, str]] = data.get("sources", [])

    if not tool_type or tool_type not in _VALID_TOOL_TYPES:
        return jsonify({"error": f"Type d'outil invalide. Valides: {sorted(_VALID_TOOL_TYPES)}"}), 400
    if not content:
        return jsonify({"error": "Contenu requis"}), 400
    if len(content) > COPILOT_MAX_CONTENT_LENGTH * 2:
        return jsonify({"error": "Contenu trop long"}), 400
    if not COPILOT_SDK_AVAILABLE:
        return jsonify({"error": "SDK Copilot non installe"}), 400

    result = copilot_generate(tool_type, content, model=model, sources=sources)
    return jsonify(result)
