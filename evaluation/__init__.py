"""Evaluation package -- automated RAG quality evaluation."""

from evaluation.evaluator import (
    run_evaluation,
    save_results,
    load_results,
    list_eval_history,
    EVAL_DATASET,
    EvalSummary,
    RetrievalMetrics,
    AnswerMetrics,
    SingleEvalResult,
    evaluate_retrieval,
    evaluate_answer,
    compute_keyword_ratio,
)
