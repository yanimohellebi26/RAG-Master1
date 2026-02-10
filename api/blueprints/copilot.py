"""
Copilot Blueprint -- /api/copilot routes.
"""

from typing import Any

from flask import Blueprint, jsonify, request

from tools.copilot import (
    COPILOT_SDK_AVAILABLE,
    copilot_generate,
)

copilot_bp = Blueprint("copilot", __name__)


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

    if not tool_type:
        return jsonify({"error": "Type d'outil requis"}), 400
    if not content:
        return jsonify({"error": "Contenu requis"}), 400
    if not COPILOT_SDK_AVAILABLE:
        return jsonify({"error": "SDK Copilot non installe"}), 400

    result = copilot_generate(tool_type, content, model=model, sources=sources)
    return jsonify(result)
