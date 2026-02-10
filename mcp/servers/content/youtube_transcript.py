"""
MCP Server -- YouTube Transcript.

Deux modes :
  1. **Enrichissement** : indexer la transcription dans ChromaDB pour enrichir
     la base de connaissances quand les cours sont insuffisants.
  2. **Analyse standalone** : page dediee ou l'utilisateur colle un lien
     et obtient transcription + resume + concepts cles + analyse IA.
"""

from __future__ import annotations

import re
import logging
from typing import Any

from mcp.base import BaseMCPServer, MCPToolDefinition, MCPStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency — graceful fallback
# ---------------------------------------------------------------------------

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YT_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YT_TRANSCRIPT_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_YT_URL_PATTERNS = [
    re.compile(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:embed/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:shorts/)([a-zA-Z0-9_-]{11})"),
]


def extract_video_id(url: str) -> str | None:
    """Extract the 11-char video ID from any common YouTube URL format."""
    for pat in _YT_URL_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    # Maybe the user passed a bare ID
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url.strip()):
        return url.strip()
    return None


# Shared API instance (youtube-transcript-api v1.x requires instantiation)
_yt_api: "YouTubeTranscriptApi | None" = None


def _get_api() -> "YouTubeTranscriptApi":
    global _yt_api
    if _yt_api is None:
        _yt_api = YouTubeTranscriptApi()
    return _yt_api


def fetch_transcript(
    video_id: str,
    languages: list[str] | None = None,
) -> dict[str, Any]:
    """
    Fetch transcript for a video.

    Returns dict with keys: segments, full_text, language, duration_seconds.

    Compatible with youtube-transcript-api >= 1.0.
    """
    if not YT_TRANSCRIPT_AVAILABLE:
        raise RuntimeError(
            "youtube-transcript-api not installed. "
            "Run: pip install youtube-transcript-api"
        )

    api = _get_api()
    langs = languages or ["fr", "en"]
    transcript_list = api.list(video_id)

    # Try to find a manually created transcript first, then generated
    transcript = None
    for lang in langs:
        try:
            transcript = transcript_list.find_manually_created_transcript([lang])
            break
        except Exception:
            pass
    if transcript is None:
        for lang in langs:
            try:
                transcript = transcript_list.find_generated_transcript([lang])
                break
            except Exception:
                pass
    if transcript is None:
        # Fallback: grab whatever is available
        transcript = transcript_list.find_transcript(langs)

    fetched = transcript.fetch()
    # v1.x returns FetchedTranscript with .snippets of named-tuple-like objects
    snippets = list(fetched.snippets)
    segments = [
        {"text": s.text, "start": s.start, "duration": s.duration}
        for s in snippets
    ]
    full_text = " ".join(s.text for s in snippets)
    duration = (snippets[-1].start + snippets[-1].duration) if snippets else 0

    return {
        "video_id": video_id,
        "segments": segments,
        "full_text": full_text,
        "language": fetched.language_code,
        "duration_seconds": round(duration),
    }


def clean_transcript(text: str) -> str:
    """Basic cleaning of transcript text for indexation."""
    # Remove multiple spaces / newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove common filler patterns
    text = re.sub(r"\[musique\]|\[applaudissements\]|\[rires\]", "", text, flags=re.IGNORECASE)
    return text.strip()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------


class YouTubeTranscriptServer(BaseMCPServer):
    SERVER_ID = "youtube-transcript"
    SERVER_NAME = "YouTube Transcript"
    CATEGORY = "content"
    DESCRIPTION = (
        "Transcrire les cours video YouTube, les indexer dans ChromaDB, "
        "ou les analyser avec l'IA (resume, concepts cles, clarification)"
    )

    def tools(self) -> list[MCPToolDefinition]:
        return [
            MCPToolDefinition(
                name="get_transcript",
                description="Recuperer la transcription brute d'une video YouTube",
                parameters={
                    "video_url": "str  — URL ou ID de la video",
                    "languages": "list[str]  — ordre de preference (defaut: fr, en)",
                },
                required_params=["video_url"],
            ),
            MCPToolDefinition(
                name="index_transcript",
                description=(
                    "Indexer la transcription dans ChromaDB pour enrichir "
                    "la base de connaissances RAG"
                ),
                parameters={
                    "video_url": "str",
                    "subject": "str  — matiere associee",
                    "doc_type": "str  — CM, TD, TP, etc.",
                },
                required_params=["video_url", "subject"],
            ),
            MCPToolDefinition(
                name="analyze_video",
                description=(
                    "Analyse complete : transcription + resume + concepts cles "
                    "+ points importants via OpenAI"
                ),
                parameters={
                    "video_url": "str",
                    "analysis_type": "str  — summary | concepts | detailed | all",
                },
                required_params=["video_url"],
            ),
        ]

    async def connect(self) -> bool:
        if not YT_TRANSCRIPT_AVAILABLE:
            self.logger.warning(
                "youtube-transcript-api not installed — "
                "run: pip install youtube-transcript-api"
            )
            return False
        self._status = MCPStatus.CONNECTED
        self.logger.info("YouTube Transcript server connected")
        return True

    async def disconnect(self) -> None:
        self._status = MCPStatus.DISCONNECTED

    async def health(self) -> bool:
        return YT_TRANSCRIPT_AVAILABLE

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        if tool_name == "get_transcript":
            return self._get_transcript(**kwargs)
        elif tool_name == "index_transcript":
            return self._index_transcript(**kwargs)
        elif tool_name == "analyze_video":
            return self._analyze_video(**kwargs)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # -- Tool implementations -----------------------------------------------

    def _get_transcript(
        self,
        video_url: str,
        languages: list[str] | None = None,
    ) -> dict[str, Any]:
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"URL YouTube invalide : {video_url}")
        data = fetch_transcript(video_id, languages or self._default_languages)
        data["full_text"] = clean_transcript(data["full_text"])
        return data

    def _index_transcript(
        self,
        video_url: str,
        subject: str,
        doc_type: str = "Video",
    ) -> dict[str, Any]:
        """Fetch, chunk, and index a transcript into ChromaDB."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document as LCDoc
        from api.services.rag import rag_service
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP
        from core.constants import (
            META_MATIERE, META_DOC_TYPE, META_FILENAME, META_FILEPATH,
        )

        transcript = self._get_transcript(video_url)
        video_id = transcript["video_id"]
        text = transcript["full_text"]

        if not text or len(text) < 50:
            return {"indexed": 0, "message": "Transcription trop courte ou vide"}

        # Build a LangChain document
        filename = f"youtube_{video_id}.txt"
        doc = LCDoc(
            page_content=text,
            metadata={
                META_MATIERE: subject,
                META_DOC_TYPE: doc_type,
                META_FILENAME: filename,
                META_FILEPATH: f"https://youtube.com/watch?v={video_id}",
                "source_type": "youtube",
                "video_id": video_id,
                "language": transcript["language"],
                "duration_seconds": transcript["duration_seconds"],
            },
        )

        # Split
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents([doc])

        # Add to vectorstore
        rag_service.vectorstore.add_documents(chunks)
        # Invalidate BM25 cache so it rebuilds with new docs
        rag_service._bm25_index = None

        return {
            "indexed": len(chunks),
            "video_id": video_id,
            "subject": subject,
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "text_length": len(text),
        }

    def _analyze_video(
        self,
        video_url: str,
        analysis_type: str = "all",
    ) -> dict[str, Any]:
        """Fetch transcript and run OpenAI analysis."""
        from api.services.rag import rag_service

        transcript = self._get_transcript(video_url)
        text = transcript["full_text"]

        if not text:
            return {"error": "Transcription vide"}

        # Truncate for LLM context window
        max_chars = 12_000
        truncated = text[:max_chars]
        is_truncated = len(text) > max_chars

        prompts = {
            "summary": (
                "Tu es un assistant pedagogique expert. "
                "Fais un resume structure et clair de cette transcription de video YouTube. "
                "Utilise des titres (##), des listes a puces, et mets en avant les points cles.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "concepts": (
                "Tu es un assistant pedagogique expert. "
                "Extrais les concepts cles de cette transcription de video YouTube. "
                "Pour chaque concept, donne une definition courte et un exemple si possible. "
                "Organise par themes.\n\n"
                f"Transcription :\n{truncated}"
            ),
            "detailed": (
                "Tu es un assistant pedagogique expert. "
                "Fais une analyse detaillee de cette transcription de video YouTube :\n"
                "1. Resume en 3-5 phrases\n"
                "2. Concepts cles avec definitions\n"
                "3. Points importants a retenir\n"
                "4. Questions de revision possibles\n"
                "5. Liens avec d'autres sujets\n\n"
                f"Transcription :\n{truncated}"
            ),
        }

        results = {
            "video_id": transcript["video_id"],
            "language": transcript["language"],
            "duration_seconds": transcript["duration_seconds"],
            "transcript_length": len(text),
            "is_truncated": is_truncated,
            "transcript": text,
        }

        if analysis_type == "all":
            types_to_run = ["summary", "concepts", "detailed"]
        else:
            types_to_run = [analysis_type] if analysis_type in prompts else ["summary"]

        llm = rag_service.llm
        for atype in types_to_run:
            try:
                response = llm.invoke(prompts[atype])
                results[atype] = response.content
            except Exception as exc:
                logger.error("Analysis %s failed: %s", atype, exc)
                results[atype] = f"Erreur lors de l'analyse : {exc}"

        return results

    # -- Internal helpers ---------------------------------------------------

    @property
    def _default_languages(self) -> list[str]:
        lang = self.config.get("default_language", "fr")
        if lang == "fr":
            return ["fr", "en"]
        return [lang, "fr", "en"]
