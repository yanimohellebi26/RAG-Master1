"""Core RAG engine -- indexation, retrieval, configuration."""

"""Core RAG engine -- indexation, retrieval, config, watcher."""

from core.config import (
    PROJECT_ROOT,
    CONFIG,
    COURSES_DIR,
    CHROMA_DIR,
    EVAL_RESULTS_DIR,
    OPENAI_API_KEY,
    load_config,
)
from core.retrieval import (
    BM25Index,
    enhanced_retrieve,
    rewrite_query,
    hybrid_search,
)
from core.indexer import compute_file_hash, should_exclude_path
