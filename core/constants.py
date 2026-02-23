"""
Constants -- Single source of truth for all magic strings and values.

Import from here instead of scattering literals across modules.
"""

# ---------------------------------------------------------------------------
# OpenAI Models & Embeddings
# ---------------------------------------------------------------------------

LLM_MODEL: str = "gpt-4o-mini"
LLM_TEMPERATURE: float = 0.1
LLM_JUDGE_TEMPERATURE: float = 0.0

EMBEDDING_MODEL: str = "text-embedding-3-small"

# ---------------------------------------------------------------------------
# Copilot Models
# ---------------------------------------------------------------------------

COPILOT_DEFAULT_MODEL: str = "gpt-4o"
COPILOT_AVAILABLE_MODELS: list[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-sonnet-4",
    "o3-mini",
]
COPILOT_MAX_CONTENT_LENGTH: int = 6000
COPILOT_SESSION_TIMEOUT: float = 60.0

# ---------------------------------------------------------------------------
# Metadata Keys (used in Document.metadata across the project)
# ---------------------------------------------------------------------------

META_MATIERE: str = "matiere"
META_DOC_TYPE: str = "doc_type"
META_FILENAME: str = "filename"
META_FILEPATH: str = "filepath"
META_FILE_HASH: str = "file_hash"
META_COMPRESSED: str = "compressed"

# ---------------------------------------------------------------------------
# Default Metadata Values
# ---------------------------------------------------------------------------

DEFAULT_MATIERE: str = "Inconnu"
DEFAULT_DOC_TYPE: str = "Document"

# ---------------------------------------------------------------------------
# Document Type Classification
# ---------------------------------------------------------------------------

DOC_TYPE_CM: str = "CM"
DOC_TYPE_TD: str = "TD"
DOC_TYPE_TP: str = "TP"
DOC_TYPE_EXAM: str = "Examen"
DOC_TYPE_CORRECTION: str = "Corrige"

CM_KEYWORDS: tuple[str, ...] = (
    "cm", "cours", "slide",
    "ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7",
)
EXAM_KEYWORDS: tuple[str, ...] = ("exam", "ct ", "ct_", "cc_", "annale")
CORRECTION_KEYWORDS: tuple[str, ...] = ("corr", "cor", "solution")

# ---------------------------------------------------------------------------
# Retrieval Pipeline
# ---------------------------------------------------------------------------

BM25_K1: float = 1.5
BM25_B: float = 0.75
RRF_CONSTANT: int = 60

SEMANTIC_WEIGHT: float = 0.6
BM25_WEIGHT: float = 0.4

FETCH_K_MULTIPLIER: int = 3
SEARCH_TYPE_MMR: str = "mmr"

COMPRESS_MIN_LENGTH: int = 200
COMPRESS_MAX_CONTENT: int = 3000
COMPRESS_NON_PERTINENT: str = "NON_PERTINENT"
COMPRESS_MIN_RESULT_LENGTH: int = 30
RERANK_MAX_PASSAGE_LENGTH: int = 1500
REWRITE_MAX_CONTEXT: int = 1000

DEFAULT_NB_SOURCES: int = 10
MIN_NB_SOURCES: int = 1
MAX_NB_SOURCES: int = 50

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MAX_QUESTION_LENGTH: int = 2000
MIN_QUESTION_LENGTH: int = 3

SUSPICIOUS_PATTERNS: list[str] = [
    r"<script",
    r"javascript:",
    r"onerror=",
    r"onload=",
]

# ---------------------------------------------------------------------------
# Flask / Server
# ---------------------------------------------------------------------------

FLASK_HOST: str = "0.0.0.0"
FLASK_PORT: int = 5000
MAX_CHAT_HISTORY_LENGTH: int = 20
CHAT_CONTEXT_TRAILING_MESSAGES: int = 4
CHAT_CONTEXT_MAX_CHARS: int = 200

# ---------------------------------------------------------------------------
# Evaluation Weights (overall_score composite)
# ---------------------------------------------------------------------------

EVAL_WEIGHT_FAITHFULNESS: float = 0.18
EVAL_WEIGHT_RELEVANCE: float = 0.20
EVAL_WEIGHT_COMPLETENESS: float = 0.20
EVAL_WEIGHT_SEMANTIC_SIM: float = 0.15
EVAL_WEIGHT_KEYWORD_COV: float = 0.12
EVAL_WEIGHT_SUBJECT_MATCH: float = 0.10
EVAL_WEIGHT_KEYWORD_HIT: float = 0.05

EVAL_LATEST_FILENAME: str = "eval_latest.json"
EVAL_HISTORY_GLOB: str = "eval_2*.json"
EVAL_MAX_CONTEXT_LENGTH: int = 10_000
EVAL_MAX_ANSWER_LENGTH: int = 3_000
EVAL_MAX_ANSWER_JUDGE: int = 2_000
EVAL_MAX_EMBED_LENGTH: int = 2_000

# ---------------------------------------------------------------------------
# Indexer
# ---------------------------------------------------------------------------

FILE_HASH_CHUNK_SIZE: int = 8192

# ---------------------------------------------------------------------------
# Subjects (derived from config at import time — canonical list)
# ---------------------------------------------------------------------------

ALL_SUBJECTS: list[str] = [
    "Algorithmique",
    "Analyse Exploratoire de Donnees",
    "Cloud & Reseaux",
    "Conception Web Avancee",
    "Genie Logiciel",
    "Intelligence Artificielle",
    "Logique & Prolog",
    "SGBD Graphes",
    "Systemes Distribues",
    "Systemes de Gestion de Donnees",
]

# ---------------------------------------------------------------------------
# MCP (Model Context Protocol)
# ---------------------------------------------------------------------------

MCP_CONNECT_TIMEOUT: float = 30.0
MCP_EXECUTE_TIMEOUT: float = 60.0
MCP_HEALTH_CHECK_INTERVAL: int = 300  # seconds

MCP_CATEGORIES: dict[str, str] = {
    "personal": "Outils personnels",
    "content": "Acquisition de contenu",
    "search": "Recherche et veille",
    "media": "Images et media",
    "code": "Code et execution",
    "organization": "Organisation",
    "communication": "Communication",
    "memory": "Memoire et donnees",
    "git": "Git",
}

# ---------------------------------------------------------------------------
# Copilot Tool Labels
# ---------------------------------------------------------------------------

TOOL_LABELS: dict[str, str] = {
    "quiz": "Quiz",
    "table": "Tableau",
    "chart": "Graphique",
    "concepts": "Concepts",
    "flashcards": "Flashcards",
    "mindmap": "Mind Map",
    "video": "\ud83c\udfa5 Vid\u00e9o",
    "notion": "\ud83d\udcdd Notion",
}

# ---------------------------------------------------------------------------
# System Prompt (shared between app.py, web_app.py, evaluation)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """\
Tu es un assistant pedagogique expert pour un etudiant en Master 1 Informatique
a l'Universite de Bourgogne. Tu reponds en francais de maniere claire,
structuree et pedagogique.

Regles :
1. Base tes reponses PRINCIPALEMENT sur le contexte fourni (extraits de cours).
   Quand tu utilises une information du contexte, cite la source (matiere, type).
2. Tu peux completer avec des connaissances generales en informatique si elles
   sont coherentes avec le contexte et necessaires pour une reponse pedagogique.
   Dans ce cas precise : "De maniere generale en informatique, ..."
3. Si le contexte ne contient PAS d'information sur le sujet, dis-le clairement
   puis donne une reponse generale en le signalant.
4. Structure tes reponses avec des titres (##), listes a puces, et code si pertinent.
5. Utilise des exemples concrets et des explications progressives.
6. Pour les exercices : guide etape par etape (methode socratique).
7. Fais des liens entre matieres quand c'est pertinent.
8. Termine par 1-2 questions pour approfondir.

Contexte des cours (extraits indexes) :
{context}
"""

# ---------------------------------------------------------------------------
# French Stop Words (for BM25 tokenisation)
# ---------------------------------------------------------------------------

STOP_WORDS_FR: frozenset[str] = frozenset({
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "est",
    "en", "que", "qui", "dans", "pour", "par", "sur", "au", "aux",
    "ce", "ces", "son", "sa", "ses", "il", "elle", "nous", "vous",
    "ils", "elles", "ne", "pas", "plus", "se", "ou", "mais", "avec",
    "sont", "ont", "etre", "avoir", "a", "d", "l", "qu", "n", "c",
    "je", "tu", "me", "te", "on", "leur", "entre", "soit", "cette",
    "tout", "tous", "peut", "comme", "aussi", "alors", "si", "bien",
    "fait", "faire", "dit", "donc", "tres", "meme", "sans", "car",
    "apres", "avant", "ici", "encore", "deux", "autre", "autres",
})
