"""
Config Blueprint -- /api/config routes.
"""

from flask import Blueprint, jsonify

from core.constants import ALL_SUBJECTS, COPILOT_AVAILABLE_MODELS, TOOL_LABELS
from tools.copilot import (
    COPILOT_SDK_AVAILABLE,
    get_available_models,
    is_copilot_ready,
)

config_bp = Blueprint("config", __name__)


@config_bp.route("/config", methods=["GET"])
def get_config():
    """Return frontend configuration (subjects, copilot status, etc.)."""
    copilot_ready = COPILOT_SDK_AVAILABLE and is_copilot_ready()
    models = get_available_models() or list(COPILOT_AVAILABLE_MODELS)
    return jsonify({
        "subjects": sorted(ALL_SUBJECTS),
        "copilot_available": COPILOT_SDK_AVAILABLE,
        "copilot_ready": copilot_ready,
        "copilot_models": models,
        "tool_labels": TOOL_LABELS,
    })
