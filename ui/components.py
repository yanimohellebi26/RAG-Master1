"""
UI Components -- Reusable Streamlit renderers and helpers.

Extracted from app.py to keep the main entry point focused on
orchestration while all rendering logic lives here.
"""

from typing import Any

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

APP_CSS = """
<style>
    .main-title {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px;
        margin: 5px 0;
        border-left: 4px solid #667eea;
    }
    .matiere-tag {
        display: inline-block;
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .copilot-header {
        background: linear-gradient(90deg, #1a7f37 0%, #2ea043 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .concept-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        border-left: 3px solid;
    }
    .concept-haute  { border-color: #ef4444; }
    .concept-moyenne { border-color: #f59e0b; }
    .concept-basse  { border-color: #22c55e; }
</style>
"""

# ---------------------------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------------------------


def format_docs(docs: list) -> str:
    """Concatenate retrieved documents into a single context string."""
    parts: list[str] = []
    for doc in docs:
        matiere = doc.metadata.get("matiere", "Inconnu")
        doc_type = doc.metadata.get("doc_type", "Document")
        filename = doc.metadata.get("filename", "")
        parts.append(
            f"[{matiere} -- {doc_type} -- {filename}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def deduplicate_sources(docs: list) -> list[dict[str, str]]:
    """Build a deduplicated list of source metadata from retrieved documents."""
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


def show_sources(sources: list[dict[str, str]], *, expanded: bool = True) -> None:
    """Render RAG source cards inside a Streamlit expander."""
    if not sources:
        return
    label = f"Sources RAG utilisees ({len(sources)} documents)"
    with st.expander(label, expanded=expanded):
        for src in sources:
            st.markdown(
                f'<div class="source-box">'
                f'<span class="matiere-tag">{src["matiere"]}</span> '
                f'**{src["doc_type"]}** -- _{src["filename"]}_'
                f"</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Copilot tool renderers
# ---------------------------------------------------------------------------


def render_quiz(data: dict[str, Any], key_prefix: str) -> None:
    """Render an interactive multiple-choice quiz."""
    st.markdown(f"#### {data.get('title', 'Quiz')}")
    for idx, question in enumerate(data.get("questions", [])):
        st.markdown(f"**Q{idx + 1}.** {question['question']}")
        answer = st.radio(
            "Votre reponse :",
            question["options"],
            key=f"{key_prefix}_q{idx}",
            index=None,
        )
        if answer is not None:
            correct_idx = question.get("correct", 0)
            if question["options"].index(answer) == correct_idx:
                st.success(f"Correct. {question.get('explanation', '')}")
            else:
                st.error(f"Bonne reponse : {question['options'][correct_idx]}")
                st.info(question.get("explanation", ""))
        st.markdown("---")


def render_table(data: dict[str, Any], key_prefix: str) -> None:
    """Render a summary table as a Streamlit dataframe."""
    st.markdown(f"#### {data.get('title', 'Tableau')}")
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    if headers and rows:
        df = pd.DataFrame(rows, columns=headers)
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_chart(data: dict[str, Any], key_prefix: str) -> None:
    """Render a bar, line, or area chart."""
    st.markdown(f"#### {data.get('title', 'Graphique')}")
    labels = data.get("labels", [])
    values = data.get("values", [])
    if labels and values:
        df = pd.DataFrame({"Valeur": values}, index=labels)
        chart_type = data.get("chart_type", "bar")
        if chart_type == "line":
            st.line_chart(df)
        elif chart_type == "area":
            st.area_chart(df)
        else:
            st.bar_chart(df)


def render_concepts(data: dict[str, Any], key_prefix: str) -> None:
    """Render key concepts with importance-based colour coding."""
    st.markdown(f"#### {data.get('title', 'Concepts cles')}")
    for concept in data.get("concepts", []):
        importance = concept.get("importance", "moyenne")
        st.markdown(
            f'<div class="concept-card concept-{importance}">'
            f"<strong>{concept['name']}</strong><br>{concept['definition']}</div>",
            unsafe_allow_html=True,
        )


def render_flashcards(data: dict[str, Any], key_prefix: str) -> None:
    """Render revision flashcards as expandable front/back pairs."""
    st.markdown(f"#### {data.get('title', 'Flashcards')}")
    for idx, card in enumerate(data.get("cards", [])):
        with st.expander(card["front"]):
            st.markdown(card["back"])


def render_mindmap(data: dict[str, Any], key_prefix: str) -> None:
    """Render a text-based mind map with branches and children."""
    st.markdown(f"#### {data.get('title', 'Mind Map')}")
    central = data.get("central", "")
    st.markdown(f"**{central}**")
    for branch in data.get("branches", []):
        st.markdown(f"--- **{branch['name']}**")
        for child in branch.get("children", []):
            st.markdown(f"&emsp; {child}")


RENDERERS: dict[str, Any] = {
    "quiz": render_quiz,
    "table": render_table,
    "chart": render_chart,
    "concepts": render_concepts,
    "flashcards": render_flashcards,
    "mindmap": render_mindmap,
}
