"""
Chat Blueprint -- /api/chat and /api/clear routes.
"""

import json
import logging
import re
import time
from typing import Any

from flask import Blueprint, Response, jsonify, request, stream_with_context
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from api.services.rag import rag_service
from core.constants import (
    ALL_SUBJECTS,
    CHAT_CONTEXT_MAX_CHARS,
    CHAT_CONTEXT_TRAILING_MESSAGES,
    DEFAULT_NB_SOURCES,
    META_MATIERE,
    SYSTEM_PROMPT,
)
from core.retrieval import enhanced_retrieve
from core.validators import validate_nb_sources, validate_question, validate_subjects

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])

# ---------------------------------------------------------------------------
# Video intent detection
# ---------------------------------------------------------------------------

_VIDEO_PATTERNS = [
    re.compile(
        r"(?:trouve|cherche|montre|donne|suggere|recommande|propose)"
        r"[- ]?(?:moi|nous)?\s+"
        r"(?:une?|des|la|les)?\s*"
        r"(?:vid[eé]os?|tutos?|tutoriels?)\s+"
        r"(?:explicati[fv]e?s?|sur|de|pour|qui|en rapport|a propos)"
        r"\s+(.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:vid[eé]os?\s+(?:sur|de|pour|explicati))\s+(.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:je\s+(?:veux|voudrais|cherche|aimerais)\s+)"
        r"(?:une?|des)?\s*"
        r"(?:vid[eé]os?|tutos?)\s+(?:sur|de|pour|qui|explicati)\s+(.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:y\s*a[- ]?t[- ]?il|est[- ]ce\s+qu.il\s+y\s+a|as[- ]tu)\s+"
        r"(?:une?|des)?\s*"
        r"(?:vid[eé]os?|tutos?)\s+(?:sur|de|pour)\s+(.+)",
        re.IGNORECASE,
    ),
]


def detect_video_intent(question: str) -> str | None:
    """Return the concept if the question asks for a video, else None."""
    for pat in _VIDEO_PATTERNS:
        m = pat.search(question)
        if m:
            concept = m.group(1).strip().rstrip("?!. ")
            if len(concept) > 3:
                return concept
    return None


@chat_bp.route("/chat", methods=["POST"])
def chat() -> Response:
    """Stream a RAG-augmented chat response via SSE."""
    data: dict[str, Any] | None = request.json
    if not data:
        return jsonify({"error": "Requete invalide"}), 400

    question = data.get("question", "").strip()
    is_valid, error_msg = validate_question(question)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    subjects: list[str] = data.get("subjects", [])
    is_valid, error_msg = validate_subjects(subjects, sorted(ALL_SUBJECTS))
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    nb_sources: int = data.get("nb_sources", DEFAULT_NB_SOURCES)
    is_valid, error_msg = validate_nb_sources(nb_sources)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    nb_sources = int(nb_sources)

    enable_rewrite: bool = data.get("enable_rewrite", True)
    enable_hybrid: bool = data.get("enable_hybrid", True)
    enable_rerank: bool = data.get("enable_rerank", False)
    enable_compress: bool = data.get("enable_compress", False)

    svc = rag_service

    # ------------------------------------------------------------------
    # Short-circuit: if the user just wants a video, skip RAG + LLM
    # ------------------------------------------------------------------
    video_concept = detect_video_intent(question)
    if video_concept:
        def generate_video_only():
            start_time = time.time()
            try:
                from api.services.youtube import youtube_service
                video_results = youtube_service.search_videos(
                    concept=video_concept,
                    max_results=5,
                )
                # Send an empty meta so the frontend doesn't break
                yield f"data: {json.dumps({'type': 'meta', 'sources': [], 'retrieval_time': 0, 'rewritten_query': question, 'steps': ['video_search'], 'num_docs': 0, 'context': ''}, ensure_ascii=False)}\n\n"

                # Build a short text response listing the videos
                lines = [f"🎥 **Vidéos trouvées pour : {video_concept}**\n"]
                for i, v in enumerate(video_results.get("videos", []), 1):
                    lines.append(f"{i}. [{v['title']}]({v['url']}) — *{v['channel']}* ({v.get('duration', '')})")
                if video_results.get("recommended_channels"):
                    lines.append("\n📺 **Chaînes recommandées** : " + ", ".join(video_results["recommended_channels"]))

                text_response = "\n".join(lines)
                yield f"data: {json.dumps({'type': 'token', 'content': text_response}, ensure_ascii=False)}\n\n"

                total_time = time.time() - start_time
                yield f"data: {json.dumps({'type': 'done', 'total_time': round(total_time, 2)}, ensure_ascii=False)}\n\n"

                # Send structured video data for rich rendering
                yield f"data: {json.dumps({'type': 'videos', 'concept': video_concept, 'videos': video_results.get('videos', []), 'queries': video_results.get('queries', []), 'recommended_channels': video_results.get('recommended_channels', []), 'tips': video_results.get('tips', '')}, ensure_ascii=False)}\n\n"

                svc.append_exchange(question, text_response)
            except Exception as exc:
                logger.error("Video-only search failed: %s", exc)
                yield f"data: {json.dumps({'type': 'meta', 'sources': [], 'retrieval_time': 0, 'rewritten_query': question, 'steps': [], 'num_docs': 0, 'context': ''}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'content': f'Erreur lors de la recherche de vidéos : {exc}'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'total_time': round(time.time() - start_time, 2)}, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate_video_only()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ------------------------------------------------------------------
    # Normal RAG pipeline
    # ------------------------------------------------------------------

    def generate():
        start_time = time.time()

        filter_dict = None
        if subjects:
            filter_dict = {META_MATIERE: {"$in": subjects}}

        chat_ctx = ""
        if svc.chat_history:
            last_msgs = svc.chat_history[-CHAT_CONTEXT_TRAILING_MESSAGES:]
            chat_ctx = "\n".join(
                m.content[:CHAT_CONTEXT_MAX_CHARS] for m in last_msgs
            )

        retrieval_result = enhanced_retrieve(
            question=question,
            vectorstore=svc.vectorstore,
            llm=svc.llm,
            bm25_index=svc.bm25_index,
            nb_sources=nb_sources,
            filter_dict=filter_dict,
            chat_context=chat_ctx,
            enable_rewrite=enable_rewrite,
            enable_hybrid=enable_hybrid,
            enable_rerank=enable_rerank,
            enable_compress=enable_compress,
        )

        relevant_docs = retrieval_result["documents"]
        rewritten_query = retrieval_result["rewritten_query"]
        steps_applied = retrieval_result["steps_applied"]

        context = svc.format_docs(relevant_docs)
        retrieval_time = time.time() - start_time
        sources = svc.deduplicate_sources(relevant_docs)

        meta_payload = {
            "type": "meta",
            "sources": sources,
            "retrieval_time": round(retrieval_time, 2),
            "rewritten_query": rewritten_query,
            "steps": steps_applied,
            "num_docs": len(relevant_docs),
            "context": context[:3000],
        }
        yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

        messages = PROMPT_TEMPLATE.invoke({
            "context": context,
            "chat_history": svc.chat_history,
            "question": question,
        })

        full_response = ""
        for chunk in svc.llm.stream(messages):
            if chunk.content:
                full_response += chunk.content
                token_payload = {"type": "token", "content": chunk.content}
                yield f"data: {json.dumps(token_payload, ensure_ascii=False)}\n\n"

        total_time = time.time() - start_time
        done_payload = {"type": "done", "total_time": round(total_time, 2)}
        yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

        svc.append_exchange(question, full_response)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@chat_bp.route("/clear", methods=["POST"])
def clear_chat():
    """Clear conversation history."""
    rag_service.clear_history()
    return jsonify({"status": "ok"})
