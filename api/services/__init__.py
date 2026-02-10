"""
RAG Service -- Singleton managing shared resources (vectorstore, LLM, BM25).

All blueprints share these resources through ``rag_service``.
"""

import logging
from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document as LCDoc
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.config import CHROMA_DIR, OPENAI_API_KEY
from core.constants import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    LLM_TEMPERATURE,
    MAX_CHAT_HISTORY_LENGTH,
    META_DOC_TYPE,
    META_FILENAME,
    META_MATIERE,
)
from core.retrieval import BM25Index

logger = logging.getLogger(__name__)


class RAGService:
    """Lazy-initialised singleton holding vectorstore, LLM, and BM25 index."""

    def __init__(self) -> None:
        self._vectorstore: Chroma | None = None
        self._llm: ChatOpenAI | None = None
        self._bm25_index: BM25Index | None = None
        self._chat_history: list[HumanMessage | AIMessage] = []

    # -- Flask integration --------------------------------------------------

    def init_app(self, app: Any) -> None:
        """Attach the service to a Flask app (called by the factory)."""
        app.extensions["rag_service"] = self

    # -- Lazy accessors -----------------------------------------------------

    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY,
            )
            self._vectorstore = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=embeddings,
            )
        return self._vectorstore

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                openai_api_key=OPENAI_API_KEY,
            )
        return self._llm

    @property
    def bm25_index(self) -> BM25Index | None:
        if self._bm25_index is None:
            try:
                all_docs = self.vectorstore.get(
                    include=["documents", "metadatas"],
                )
                if all_docs and all_docs.get("documents"):
                    docs = [
                        LCDoc(page_content=content, metadata=meta or {})
                        for content, meta in zip(
                            all_docs["documents"], all_docs["metadatas"]
                        )
                    ]
                    self._bm25_index = BM25Index(docs)
            except Exception:
                logger.exception("Failed to build BM25 index")
        return self._bm25_index

    # -- Chat history -------------------------------------------------------

    @property
    def chat_history(self) -> list[HumanMessage | AIMessage]:
        return self._chat_history

    def append_exchange(self, question: str, answer: str) -> None:
        """Append a user question + assistant answer to the history."""
        self._chat_history.extend([
            HumanMessage(content=question),
            AIMessage(content=answer),
        ])
        if len(self._chat_history) > MAX_CHAT_HISTORY_LENGTH:
            self._chat_history = self._chat_history[-MAX_CHAT_HISTORY_LENGTH:]

    def clear_history(self) -> None:
        self._chat_history = []

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def format_docs(docs: list) -> str:
        """Concatenate retrieved documents into a context string."""
        parts: list[str] = []
        for doc in docs:
            matiere = doc.metadata.get(META_MATIERE, "Inconnu")
            doc_type = doc.metadata.get(META_DOC_TYPE, "Document")
            filename = doc.metadata.get(META_FILENAME, "")
            parts.append(
                f"[{matiere} -- {doc_type} -- {filename}]\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def deduplicate_sources(docs: list) -> list[dict[str, str]]:
        """Build a deduplicated list of source metadata."""
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        for doc in docs:
            key = doc.metadata.get(META_FILENAME, "")
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                META_MATIERE: doc.metadata.get(META_MATIERE, "Inconnu"),
                META_DOC_TYPE: doc.metadata.get(META_DOC_TYPE, "Document"),
                META_FILENAME: key,
            })
        return sources


# Module-level singleton — import this everywhere.
rag_service = RAGService()
