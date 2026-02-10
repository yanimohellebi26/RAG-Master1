"""
Configuration -- Centralized config loading from config.yaml.

All path computations relative to the project root are done here
so that every module can ``from core.config import ...`` without
worrying about ``__file__`` gymnastics.
"""

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root (two levels up from core/config.py → project root)
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = PROJECT_ROOT / "config.yaml"

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# YAML config
# ---------------------------------------------------------------------------


def load_config() -> dict:
    """Load and return the full config dict from *config.yaml*."""
    if not CONFIG_PATH.exists():
        raise ConfigurationError(
            f"Fichier de configuration introuvable : {CONFIG_PATH}"
        )
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigurationError("config.yaml is empty or malformed")
    return data


CONFIG: dict = load_config()

# ---------------------------------------------------------------------------
# Derived paths and values (used across modules)
# ---------------------------------------------------------------------------

COURSES_DIR: Path = PROJECT_ROOT / CONFIG["courses_dir"]
CHROMA_DIR: Path = PROJECT_ROOT / CONFIG["chroma_dir"]
EVAL_RESULTS_DIR: Path = PROJECT_ROOT / "eval_results"

CHUNK_SIZE: int = CONFIG["chunk_size"]
CHUNK_OVERLAP: int = CONFIG["chunk_overlap"]
BATCH_SIZE: int = CONFIG["batch_size"]
MAX_RETRIES: int = CONFIG["max_retries"]
MIN_PAGE_LENGTH: int = CONFIG["min_page_length"]
MIN_LINE_LENGTH: int = CONFIG["min_line_length"]
SUPPORTED_EXTENSIONS: set[str] = set(CONFIG["supported_extensions"])
EXCLUDED_PATTERNS: list[str] = CONFIG["excluded_patterns"]
SUBJECT_NAMES: dict[str, str] = CONFIG["subject_names"]
