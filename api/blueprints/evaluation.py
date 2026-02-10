"""
Evaluation Blueprint -- /api/eval/* routes.
"""

from dataclasses import asdict

from flask import Blueprint, jsonify

from api.services.rag import rag_service
from core.constants import DEFAULT_NB_SOURCES
from evaluation.evaluator import (
    list_eval_history,
    load_results,
    run_evaluation,
    save_results,
)

eval_bp = Blueprint("evaluation", __name__)


@eval_bp.route("/eval/run", methods=["POST"])
def run_eval():
    """Run the full evaluation pipeline."""
    svc = rag_service
    summary = run_evaluation(
        vectorstore=svc.vectorstore,
        llm=svc.llm,
        nb_sources=DEFAULT_NB_SOURCES,
        bm25_index=svc.bm25_index,
        enable_enhanced=True,
    )
    save_results(summary)
    return jsonify(asdict(summary))


@eval_bp.route("/eval/latest", methods=["GET"])
def get_eval_latest():
    """Get the latest evaluation results."""
    results = load_results()
    if results is None:
        return jsonify({"error": "Aucune evaluation disponible"}), 404
    return jsonify(asdict(results))


@eval_bp.route("/eval/history", methods=["GET"])
def get_eval_history():
    """Get evaluation history."""
    return jsonify(list_eval_history())
