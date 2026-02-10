"""
RAG Improvements -- Enhanced retrieval pipeline components.

Provides:
- Query rewriting / expansion for better retrieval
- Contextual compression to filter irrelevant passages
- BM25 keyword search for hybrid retrieval
- Cross-encoder-style LLM re-ranking of retrieved documents
"""

import re
import math
import json
from collections import Counter
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from core.constants import (
    BM25_K1,
    BM25_B,
    RRF_CONSTANT,
    SEMANTIC_WEIGHT,
    BM25_WEIGHT,
    FETCH_K_MULTIPLIER,
    SEARCH_TYPE_MMR,
    COMPRESS_MIN_LENGTH,
    COMPRESS_MAX_CONTENT,
    COMPRESS_NON_PERTINENT,
    COMPRESS_MIN_RESULT_LENGTH,
    RERANK_MAX_PASSAGE_LENGTH,
    REWRITE_MAX_CONTEXT,
    META_FILENAME,
    META_COMPRESSED,
    STOP_WORDS_FR,
)

# ---------------------------------------------------------------------------
# 1. Query Rewriting / Expansion
# ---------------------------------------------------------------------------

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un expert en reformulation de requetes pour un systeme RAG "
        "universitaire (Master 1 Informatique). "
        "Ton role est de reformuler la question de l'utilisateur pour ameliorer "
        "la recherche dans une base de cours.\n\n"
        "Regles :\n"
        "1. Garde le sens original de la question\n"
        "2. Ajoute des synonymes et termes techniques pertinents\n"
        "3. Developpe les acronymes si necessaire\n"
        "4. Si la question est vague, precise-la\n"
        "5. Genere une version enrichie de la requete\n\n"
        "Reponds UNIQUEMENT avec un JSON :\n"
        "{{\"rewritten\": \"question reformulee\", "
        "\"keywords\": [\"mot1\", \"mot2\", ...]}}"
    )),
    ("human", (
        "Question originale : {question}\n\n"
        "Contexte de la conversation (si disponible) :\n{chat_context}\n\n"
        "Reformule cette question pour optimiser la recherche."
    )),
])


def rewrite_query(
    question: str,
    llm: ChatOpenAI,
    chat_context: str = "",
) -> dict[str, Any]:
    """Rewrite a user question for better retrieval.

    Returns a dict with 'rewritten' (enriched query) and 'keywords' (list).
    Falls back to original question on any error.
    """
    fallback = {"rewritten": question, "keywords": [], "original": question}
    try:
        msgs = REWRITE_PROMPT.invoke({
            "question": question,
            "chat_context": chat_context[:REWRITE_MAX_CONTEXT],
        })
        response = llm.invoke(msgs)
        text = response.content.strip()

        parsed = _extract_json(text)
        if parsed is not None:
            return {
                "rewritten": parsed.get("rewritten", question),
                "keywords": parsed.get("keywords", []),
                "original": question,
            }
    except Exception:
        pass

    return fallback


# ---------------------------------------------------------------------------
# 2. BM25 Keyword Search (lightweight, no external deps)
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Simple French-friendly tokeniser."""
    text = text.lower()
    tokens = re.findall(r"[a-zàâäéèêëïîôùûüÿçœæ0-9]+", text)
    return [t for t in tokens if t not in STOP_WORDS_FR and len(t) > 1]


class BM25Index:
    """Minimal BM25 index over a list of LangChain documents."""

    def __init__(
        self,
        documents: list[Document],
        k1: float = BM25_K1,
        b: float = BM25_B,
    ) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b

        self._doc_tokens: list[list[str]] = []
        self._doc_freqs: list[Counter] = []
        self._idf: dict[str, float] = {}

        n = len(documents)
        df: Counter = Counter()
        total_len = 0

        for doc in documents:
            tokens = _tokenize(doc.page_content)
            self._doc_tokens.append(tokens)
            freq = Counter(tokens)
            self._doc_freqs.append(freq)
            df.update(freq.keys())
            total_len += len(tokens)

        self._avgdl = total_len / n if n else 1.0

        for term, doc_count in df.items():
            self._idf[term] = math.log(
                (n - doc_count + 0.5) / (doc_count + 0.5) + 1.0
            )

    def query(self, text: str, k: int = 10) -> list[tuple[Document, float]]:
        """Return the top-*k* documents with BM25 scores for *text*."""
        query_tokens = _tokenize(text)
        scores: list[float] = []

        for idx, freq in enumerate(self._doc_freqs):
            doc_len = len(self._doc_tokens[idx])
            score = 0.0
            for qt in query_tokens:
                if qt not in freq:
                    continue
                tf = freq[qt]
                idf = self._idf.get(qt, 0.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * doc_len / self._avgdl
                )
                score += idf * numerator / denominator
            scores.append(score)

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [
            (self.documents[i], scores[i])
            for i in ranked[:k]
            if scores[i] > 0
        ]


# ---------------------------------------------------------------------------
# 3. Hybrid Search (combine semantic + BM25)
# ---------------------------------------------------------------------------


def hybrid_search(
    query: str,
    vectorstore: Any,
    bm25_index: BM25Index | None,
    k: int = 10,
    semantic_weight: float = SEMANTIC_WEIGHT,
    bm25_weight: float = BM25_WEIGHT,
    fetch_k: int | None = None,
    filter_dict: dict | None = None,
) -> list[Document]:
    """Combine semantic (vector) and BM25 keyword search results via RRF."""
    if fetch_k is None:
        fetch_k = k * FETCH_K_MULTIPLIER

    search_kwargs: dict[str, Any] = {"k": k, "fetch_k": fetch_k}
    if filter_dict:
        search_kwargs["filter"] = filter_dict

    retriever = vectorstore.as_retriever(
        search_type=SEARCH_TYPE_MMR,
        search_kwargs=search_kwargs,
    )
    semantic_docs = retriever.invoke(query)

    if bm25_index is None:
        return semantic_docs

    bm25_results = bm25_index.query(query, k=k)
    bm25_docs = [doc for doc, _ in bm25_results]

    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for rank, doc in enumerate(semantic_docs):
        doc_id = _doc_identity(doc)
        rrf_score = semantic_weight / (RRF_CONSTANT + rank + 1)
        scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
        doc_map[doc_id] = doc

    for rank, doc in enumerate(bm25_docs):
        doc_id = _doc_identity(doc)
        rrf_score = bm25_weight / (RRF_CONSTANT + rank + 1)
        scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score
        doc_map[doc_id] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[doc_id] for doc_id, _ in ranked[:k]]


# ---------------------------------------------------------------------------
# 4. Contextual Compression
# ---------------------------------------------------------------------------

COMPRESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un assistant qui filtre et compresse des extraits de cours. "
        "Etant donne une question et un extrait de document, extrais UNIQUEMENT "
        "les passages directement pertinents pour repondre a la question.\n\n"
        "Regles :\n"
        "1. Garde le contenu factuel tel quel (ne reformule pas)\n"
        "2. Supprime les parties non pertinentes\n"
        "3. Si l'extrait est completement hors sujet, reponds 'NON_PERTINENT'\n"
        "4. Garde les formules, definitions, et exemples lies a la question\n"
    )),
    ("human", (
        "Question : {question}\n\n"
        "Extrait du document :\n{content}\n\n"
        "Extrais les passages pertinents :"
    )),
])


def compress_documents(
    question: str,
    docs: list[Document],
    llm: ChatOpenAI,
    max_docs: int = 8,
) -> list[Document]:
    """Filter and compress documents to keep only relevant passages."""
    compressed: list[Document] = []

    for doc in docs[:max_docs]:
        if len(doc.page_content) < COMPRESS_MIN_LENGTH:
            compressed.append(doc)
            continue

        try:
            msgs = COMPRESS_PROMPT.invoke({
                "question": question,
                "content": doc.page_content[:COMPRESS_MAX_CONTENT],
            })
            response = llm.invoke(msgs)
            result = response.content.strip()

            if (
                result
                and result != COMPRESS_NON_PERTINENT
                and len(result) > COMPRESS_MIN_RESULT_LENGTH
            ):
                new_doc = Document(
                    page_content=result,
                    metadata={**doc.metadata, META_COMPRESSED: True},
                )
                compressed.append(new_doc)
        except Exception:
            compressed.append(doc)

    compressed.extend(docs[max_docs:])
    return compressed


# ---------------------------------------------------------------------------
# 5. LLM Re-Ranking
# ---------------------------------------------------------------------------

RERANK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un evaluateur de pertinence. Donne un score de 0 a 10 "
        "pour indiquer si le passage est pertinent pour repondre a la question.\n\n"
        "Reponds UNIQUEMENT avec un JSON : {{\"score\": N}}"
    )),
    ("human", (
        "Question : {question}\n\n"
        "Passage :\n{passage}\n\n"
        "Score de pertinence (0-10) :"
    )),
])

_DEFAULT_RERANK_SCORE: float = 5.0


def rerank_documents(
    question: str,
    docs: list[Document],
    llm: ChatOpenAI,
    top_k: int = 8,
) -> list[Document]:
    """Re-rank documents by relevance using LLM scoring."""
    scored: list[tuple[Document, float]] = []

    for doc in docs:
        try:
            msgs = RERANK_PROMPT.invoke({
                "question": question,
                "passage": doc.page_content[:RERANK_MAX_PASSAGE_LENGTH],
            })
            response = llm.invoke(msgs)
            text = response.content.strip()

            parsed = _extract_json(text)
            if parsed is not None:
                score = float(parsed.get("score", _DEFAULT_RERANK_SCORE))
            else:
                match = re.search(r"(\d+\.?\d*)", text)
                score = float(match.group(1)) if match else _DEFAULT_RERANK_SCORE

            scored.append((doc, score))
        except Exception:
            scored.append((doc, _DEFAULT_RERANK_SCORE))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scored[:top_k]]


# ---------------------------------------------------------------------------
# 6. Enhanced RAG Pipeline (combines all improvements)
# ---------------------------------------------------------------------------


def enhanced_retrieve(
    question: str,
    vectorstore: Any,
    llm: ChatOpenAI,
    bm25_index: BM25Index | None = None,
    nb_sources: int = 10,
    filter_dict: dict | None = None,
    chat_context: str = "",
    enable_rewrite: bool = True,
    enable_hybrid: bool = True,
    enable_rerank: bool = True,
    enable_compress: bool = True,
) -> dict[str, Any]:
    """Full enhanced retrieval pipeline."""
    steps: list[str] = []
    query_for_search = question

    if enable_rewrite:
        rewrite_result = rewrite_query(question, llm, chat_context)
        query_for_search = rewrite_result["rewritten"]
        steps.append("query_rewrite")

    if enable_hybrid and bm25_index is not None:
        docs = hybrid_search(
            query_for_search,
            vectorstore,
            bm25_index,
            k=nb_sources,
            filter_dict=filter_dict,
        )
        steps.append("hybrid_search")
    else:
        search_kwargs: dict[str, Any] = {
            "k": nb_sources,
            "fetch_k": nb_sources * FETCH_K_MULTIPLIER,
        }
        if filter_dict:
            search_kwargs["filter"] = filter_dict

        retriever = vectorstore.as_retriever(
            search_type=SEARCH_TYPE_MMR,
            search_kwargs=search_kwargs,
        )
        docs = retriever.invoke(query_for_search)
        steps.append("semantic_search")

    if enable_rerank and len(docs) > 3:
        docs = rerank_documents(question, docs, llm, top_k=nb_sources)
        steps.append("rerank")

    if enable_compress:
        docs = compress_documents(question, docs, llm, max_docs=6)
        steps.append("compress")

    return {
        "documents": docs,
        "rewritten_query": query_for_search,
        "original_query": question,
        "steps_applied": steps,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict | None:
    """Try to parse a JSON object from *text*. Returns None on failure."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _doc_identity(doc: Document) -> str:
    """Build a simple identity key for RRF deduplication."""
    return doc.metadata.get(META_FILENAME, "") + ":" + doc.page_content[:100]
