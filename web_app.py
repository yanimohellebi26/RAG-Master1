"""
RAG Master 1 -- Flask web application.

Complete web interface for querying Master 1 course materials
with RAG pipeline, Copilot tools, and evaluation dashboard.
"""

import time
import json
import uuid
import os
from datetime import datetime
from typing import Any

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from core.config import OPENAI_API_KEY, CHROMA_DIR
from core.retrieval import BM25Index, enhanced_retrieve, rewrite_query
from tools.copilot import (
    copilot_generate,
    is_copilot_ready,
    get_available_models,
    TOOL_LABELS,
    COPILOT_SDK_AVAILABLE,
)
from evaluation.evaluator import (
    run_evaluation,
    save_results,
    load_results,
    list_eval_history,
    EVAL_DATASET,
)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

DIST_DIR = os.path.join(os.path.dirname(__file__), "web", "dist")

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static",
)
app.secret_key = "rag-m1-secret-key-" + str(uuid.uuid4())[:8]

# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

ALL_SUBJECTS: list[str] = [
    "Algorithmique",
    "Analyse Exploratoire de Donnees",
    "Cloud & Reseaux",
    "Conception Web Avancee",
    "Genie Logiciel",
    "Intelligence Artificielle",
    "Logique & Prolog",
    "Systemes Distribues",
    "Systemes de Gestion de Donnees",
]

# ---------------------------------------------------------------------------
# Global resources (lazy-loaded)
# ---------------------------------------------------------------------------

_vectorstore = None
_llm = None
_bm25_index = None
_chat_history: list = []


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=OPENAI_API_KEY,
        )
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
        )
    return _vectorstore


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=OPENAI_API_KEY,
        )
    return _llm


def get_bm25_index() -> BM25Index | None:
    global _bm25_index
    if _bm25_index is None:
        try:
            vs = get_vectorstore()
            all_docs = vs.get(include=["documents", "metadatas"])
            if all_docs and all_docs.get("documents"):
                from langchain_core.documents import Document as LCDoc
                docs = []
                for content, meta in zip(all_docs["documents"], all_docs["metadatas"]):
                    docs.append(LCDoc(page_content=content, metadata=meta or {}))
                _bm25_index = BM25Index(docs)
        except Exception:
            pass
    return _bm25_index


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
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

PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def format_docs(docs: list) -> str:
    parts: list[str] = []
    for doc in docs:
        matiere = doc.metadata.get("matiere", "Inconnu")
        doc_type = doc.metadata.get("doc_type", "Document")
        filename = doc.metadata.get("filename", "")
        parts.append(f"[{matiere} -- {doc_type} -- {filename}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def deduplicate_sources(docs: list) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    for doc in docs:
        key = doc.metadata.get("filename", "")
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "matiere": doc.metadata.get("matiere", "Inconnu"),
            "doc_type": doc.metadata.get("doc_type", "Document"),
            "filename": key,
        })
    return sources


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the main page."""
    copilot_ready = COPILOT_SDK_AVAILABLE and is_copilot_ready()
    models = get_available_models() or ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "o3-mini"]
    return render_template(
        "index.html",
        subjects=sorted(ALL_SUBJECTS),
        copilot_available=COPILOT_SDK_AVAILABLE,
        copilot_ready=copilot_ready,
        copilot_models=models,
        tool_labels=TOOL_LABELS,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle a chat message and return a streamed response."""
    global _chat_history
    data = request.json
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question vide"}), 400

    subjects = data.get("subjects", [])
    nb_sources = data.get("nb_sources", 10)
    enable_rewrite = data.get("enable_rewrite", True)
    enable_hybrid = data.get("enable_hybrid", True)
    enable_rerank = data.get("enable_rerank", False)
    enable_compress = data.get("enable_compress", False)

    def generate():
        global _chat_history
        start_time = time.time()

        vectorstore = get_vectorstore()
        llm = get_llm()
        bm25 = get_bm25_index()

        filter_dict = None
        if subjects:
            filter_dict = {"matiere": {"$in": subjects}}

        chat_ctx = ""
        if _chat_history:
            last_msgs = _chat_history[-4:]
            chat_ctx = "\n".join(m.content[:200] for m in last_msgs)

        retrieval_result = enhanced_retrieve(
            question=question,
            vectorstore=vectorstore,
            llm=llm,
            bm25_index=bm25,
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

        context = format_docs(relevant_docs)
        retrieval_time = time.time() - start_time

        sources = deduplicate_sources(relevant_docs)

        # Send metadata first
        meta = {
            "type": "meta",
            "sources": sources,
            "retrieval_time": round(retrieval_time, 2),
            "rewritten_query": rewritten_query,
            "steps": steps_applied,
            "num_docs": len(relevant_docs),
            "context": context[:5000],
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        messages = PROMPT_TEMPLATE.invoke({
            "context": context,
            "chat_history": _chat_history,
            "question": question,
        })

        full_response = ""
        for chunk in llm.stream(messages):
            if chunk.content:
                full_response += chunk.content
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"

        total_time = time.time() - start_time
        yield f"data: {json.dumps({'type': 'done', 'total_time': round(total_time, 2)}, ensure_ascii=False)}\n\n"

        _chat_history.extend([
            HumanMessage(content=question),
            AIMessage(content=full_response),
        ])

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Clear conversation history."""
    global _chat_history
    _chat_history = []
    return jsonify({"status": "ok"})


@app.route("/api/copilot", methods=["POST"])
def copilot_tool():
    """Generate Copilot tool content."""
    data = request.json
    tool_type = data.get("tool_type", "")
    content = data.get("content", "")
    model = data.get("model", "gpt-4o")
    sources = data.get("sources", [])

    if not COPILOT_SDK_AVAILABLE:
        return jsonify({"error": "SDK Copilot non installe"}), 400

    result = copilot_generate(tool_type, content, model=model, sources=sources)
    return jsonify(result)


@app.route("/api/eval/run", methods=["POST"])
def run_eval():
    """Run the evaluation pipeline."""
    vectorstore = get_vectorstore()
    llm = get_llm()
    bm25 = get_bm25_index()

    summary = run_evaluation(
        vectorstore=vectorstore,
        llm=llm,
        nb_sources=10,
        bm25_index=bm25,
        enable_enhanced=True,
    )
    save_results(summary)

    from dataclasses import asdict
    return jsonify(asdict(summary))


@app.route("/api/eval/latest", methods=["GET"])
def get_eval_latest():
    """Get the latest evaluation results."""
    results = load_results()
    if results is None:
        return jsonify({"error": "Aucune evaluation disponible"}), 404
    from dataclasses import asdict
    return jsonify(asdict(results))


@app.route("/api/eval/history", methods=["GET"])
def get_eval_history():
    """Get evaluation history."""
    history = list_eval_history()
    return jsonify(history)


@app.route("/api/config", methods=["GET"])
def get_config():
    """Return frontend configuration."""
    copilot_ready = COPILOT_SDK_AVAILABLE and is_copilot_ready()
    models = get_available_models() or ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "o3-mini"]
    return jsonify({
        "subjects": sorted(ALL_SUBJECTS),
        "copilot_available": COPILOT_SDK_AVAILABLE,
        "copilot_ready": copilot_ready,
        "copilot_models": models,
        "tool_labels": TOOL_LABELS,
    })


# ---------------------------------------------------------------------------
# Serve React SPA (production build)
# ---------------------------------------------------------------------------

@app.route("/assets/<path:path>")
def serve_assets(path):
    """Serve Vite build assets."""
    return send_from_directory(os.path.join(DIST_DIR, "assets"), path)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    """Serve the React SPA for all non-API routes."""
    # If a file exists in the dist folder, serve it
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    # Otherwise serve index.html (React Router handles routing)
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(DIST_DIR, "index.html")
    # Fallback to old template
    copilot_ready = COPILOT_SDK_AVAILABLE and is_copilot_ready()
    models = get_available_models() or ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "o3-mini"]
    return render_template(
        "index.html",
        subjects=sorted(ALL_SUBJECTS),
        copilot_available=COPILOT_SDK_AVAILABLE,
        copilot_ready=copilot_ready,
        copilot_models=models,
        tool_labels=TOOL_LABELS,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  RAG Master 1 - Interface Web")
    print("  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
