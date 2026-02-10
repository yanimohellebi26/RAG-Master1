"""
RAG Chat -- Streamlit interface for querying Master 1 course materials.

Uses ChromaDB as the vector store, GPT-4o-mini as the primary LLM,
and the GitHub Copilot SDK for complementary visual tools.
"""

import time
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from core.config import OPENAI_API_KEY, CHROMA_DIR

from tools.copilot import (
    copilot_generate,
    is_copilot_ready,
    get_available_models,
    TOOL_LABELS,
    COPILOT_SDK_AVAILABLE,
)
from core.retrieval import (
    BM25Index,
    enhanced_retrieve,
    rewrite_query,
)
from evaluation.evaluator import (
    run_evaluation,
    save_results,
    load_results,
    list_eval_history,
    EVAL_DATASET,
    EvalSummary,
)

# ---------------------------------------------------------------------------
# Configuration
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
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="RAG Master 1",
    page_icon="M1",
    layout="wide",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

_CSS = """
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

st.markdown(_CSS, unsafe_allow_html=True)

st.markdown(
    '<p class="main-title">Assistant RAG - Master 1 Informatique</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subtitle">'
    "Posez vos questions sur vos cours : Algo, IA, Logique, Systemes Distribues, etc."
    "</p>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Startup checks
# ---------------------------------------------------------------------------

if not OPENAI_API_KEY:
    st.error("Cle API OpenAI introuvable. Verifiez votre fichier .env.")
    st.stop()

if not CHROMA_DIR.exists():
    st.error("Base vectorielle introuvable. Lancez d'abord : python -m scripts.index")
    st.stop()

# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------
@st.cache_resource
def load_vectorstore() -> Chroma:
    """Initialise and cache the ChromaDB vector store."""
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )


@st.cache_resource
def load_llm() -> ChatOpenAI:
    """Initialise and cache the primary LLM."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=OPENAI_API_KEY,
    )


@st.cache_resource
def load_bm25_index() -> BM25Index | None:
    """Build a BM25 index over all documents in the vector store."""
    try:
        vs = load_vectorstore()
        all_docs = vs.get(include=["documents", "metadatas"])
        if not all_docs or not all_docs.get("documents"):
            return None
        from langchain_core.documents import Document as LCDoc
        docs = []
        for content, meta in zip(all_docs["documents"], all_docs["metadatas"]):
            docs.append(LCDoc(page_content=content, metadata=meta or {}))
        return BM25Index(docs)
    except Exception:
        return None


vectorstore = load_vectorstore()
llm = load_llm()
bm25_index = load_bm25_index()

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
# Session state
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "copilot_results" not in st.session_state:
    st.session_state.copilot_results = {}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## Parametres")

    selected_subjects = st.multiselect(
        "Filtrer par matiere",
        options=sorted(ALL_SUBJECTS),
        default=[],
        help="Laissez vide pour chercher dans toutes les matieres.",
    )

    st.markdown("---")

    nb_sources = st.slider("Nombre de sources", 2, 30, 10)

    st.markdown("---")

    st.markdown("### Pipeline RAG avance")
    enable_rewrite = st.toggle(
        "Reformulation de requete",
        value=True,
        help="Enrichit la question avec des synonymes et termes techniques.",
    )
    enable_hybrid = st.toggle(
        "Recherche hybride (BM25 + semantique)",
        value=True,
        help="Combine recherche par mots-cles et recherche vectorielle.",
    )
    enable_rerank = st.toggle(
        "Re-ranking LLM",
        value=False,
        help="Re-classe les documents par pertinence via LLM (plus lent).",
    )
    enable_compress = st.toggle(
        "Compression contextuelle",
        value=False,
        help="Filtre les passages non pertinents dans les documents (plus lent).",
    )

    st.markdown("---")

    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("### Matieres indexees")
    for subject in sorted(ALL_SUBJECTS):
        st.markdown(f"- {subject}")

    st.markdown("---")
    st.markdown("### Copilot Tools")
    if COPILOT_SDK_AVAILABLE:
        copilot_ok = is_copilot_ready()
        if copilot_ok:
            st.success("Connecte")
        else:
            st.warning("SDK installe -- client non connecte")
        models = get_available_models() or [
            "gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "o3-mini",
        ]
        st.selectbox("Modele Copilot", models, key="copilot_model")
    else:
        st.info("SDK non installe.")
        st.caption("`pip install github-copilot-sdk`")

    st.markdown("---")
    st.markdown(
        "<small>LangChain + ChromaDB + OpenAI + GitHub Copilot SDK</small>",
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


# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------

for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message.get("sources"):
            show_sources(message["sources"], expanded=False)

        if message["role"] == "assistant":
            cached = st.session_state.copilot_results.get(str(msg_idx), {})
            if cached:
                with st.expander("Resultats Copilot", expanded=False):
                    for tool_type, result in cached.items():
                        renderer = RENDERERS.get(tool_type)
                        if "error" not in result and renderer:
                            renderer(result, f"hist_{msg_idx}_{tool_type}")

# ---------------------------------------------------------------------------
# User input handling
# ---------------------------------------------------------------------------

if user_input := st.chat_input("Posez votre question sur vos cours..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans vos cours..."):
            start_time = time.time()

            # Build filter
            filter_dict = None
            if selected_subjects:
                filter_dict = {"matiere": {"$in": selected_subjects}}

            # Build chat context for query rewriting
            chat_ctx = ""
            if st.session_state.chat_history:
                last_msgs = st.session_state.chat_history[-4:]
                chat_ctx = "\n".join(
                    m.content[:200] for m in last_msgs
                )

            # Enhanced retrieval pipeline
            retrieval_result = enhanced_retrieve(
                question=user_input,
                vectorstore=vectorstore,
                llm=llm,
                bm25_index=bm25_index,
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

            messages = PROMPT_TEMPLATE.invoke({
                "context": context,
                "chat_history": st.session_state.chat_history,
                "question": user_input,
            })

            # Stream the response token by token
            response_placeholder = st.empty()
            full_response = ""

            for chunk in llm.stream(messages):
                if chunk.content:
                    full_response += chunk.content
                    response_placeholder.markdown(full_response + " |")

            response_placeholder.markdown(full_response)
            total_time = time.time() - start_time

            # Deduplicate and display sources
            sources = deduplicate_sources(relevant_docs)

            if sources:
                show_sources(sources, expanded=True)
            else:
                st.info("Aucune source pertinente trouvee dans la base de cours.")

            # Show pipeline info
            with st.expander("Pipeline RAG", expanded=False):
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Retrieval", f"{retrieval_time:.1f}s")
                col_b.metric("Total", f"{total_time:.1f}s")
                col_c.metric("Documents", len(relevant_docs))
                if rewritten_query != user_input:
                    st.caption(f"Requete enrichie : _{rewritten_query}_")
                st.caption(f"Etapes : {' → '.join(steps_applied)}")

    # Persist to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
        "rag_context": context,
    })
    st.session_state.chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=full_response),
    ])

# ---------------------------------------------------------------------------
# Copilot Tools panel
# ---------------------------------------------------------------------------

if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "assistant"
    and COPILOT_SDK_AVAILABLE
):
    last_idx = len(st.session_state.messages) - 1
    last_msg = st.session_state.messages[-1]

    # Find the most recent user question
    last_question = ""
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            last_question = msg["content"]
            break

    copilot_content = (
        f"Question de l'etudiant : {last_question}\n\n"
        f"Reponse du cours :\n{last_msg['content']}"
    )
    rag_context = last_msg.get("rag_context", "")
    if rag_context:
        copilot_content += f"\n\nExtraits des cours :\n{rag_context[:3000]}"

    st.divider()
    st.markdown(
        '<p class="copilot-header">Outils Copilot</p>',
        unsafe_allow_html=True,
    )
    st.caption("Generez du contenu visuel complementaire a partir de la reponse.")

    # One button per tool type
    cols = st.columns(len(TOOL_LABELS))
    for col, (tool_type, label) in zip(cols, TOOL_LABELS.items()):
        if col.button(label, key=f"gen_{tool_type}", use_container_width=True):
            model = st.session_state.get("copilot_model", "gpt-4o")
            with st.spinner(f"Copilot genere : {label}..."):
                result = copilot_generate(
                    tool_type,
                    copilot_content,
                    model=model,
                    sources=last_msg.get("sources", []),
                )
            st.session_state.copilot_results.setdefault(
                str(last_idx), {},
            )[tool_type] = result

    # Display cached results for the current answer
    cached_results = st.session_state.copilot_results.get(str(last_idx), {})
    for tool_type, result in cached_results.items():
        if "error" in result:
            st.error(f"{TOOL_LABELS.get(tool_type, tool_type)} -- {result['error']}")
            if result.get("raw"):
                with st.expander("Reponse brute du modele"):
                    st.code(result["raw"][:1000])
            with st.expander("Diagnostic"):
                if "exception" in result:
                    st.caption(f"**Exception:** {result['exception']}")
                if "exception_type" in result:
                    st.caption(f"**Type:** {result['exception_type']}")
                if "traceback" in result:
                    st.code(result["traceback"], language="python")
        else:
            renderer = RENDERERS.get(tool_type)
            if renderer:
                renderer(result, f"active_{last_idx}_{tool_type}")

            if result.get("sources"):
                with st.expander("Sources utilisees"):
                    for src in result["sources"]:
                        if isinstance(src, dict):
                            st.markdown(
                                f"**{src.get('matiere', 'Inconnu')}** -- "
                                f"{src.get('doc_type', 'Doc')} "
                                f"_{src.get('filename', '')}_ "
                            )
                        else:
                            st.markdown(f"- {src}")

# ---------------------------------------------------------------------------
# Evaluation tab
# ---------------------------------------------------------------------------

st.divider()
with st.expander("Evaluation du systeme RAG", expanded=False):
    st.markdown("### Evaluation automatique")
    st.caption(
        "Lance une evaluation complete du systeme RAG sur un jeu de test "
        "couvrant toutes les matieres. Utilise des metriques de fidelite, "
        "pertinence, completude et couverture de mots-cles."
    )

    eval_col1, eval_col2 = st.columns([2, 1])
    with eval_col1:
        st.markdown(f"**{len(EVAL_DATASET)} questions** couvrant {len(set(q['subject'] for q in EVAL_DATASET))} matieres")
    with eval_col2:
        run_eval = st.button("Lancer l'evaluation", type="primary", use_container_width=True)

    # Show previous results if they exist
    prev_results = load_results()

    if run_eval:
        progress_bar = st.progress(0, text="Demarrage de l'evaluation...")
        status_text = st.empty()

        def eval_progress(idx, total, q_text):
            progress_bar.progress(
                (idx + 1) / total,
                text=f"Question {idx + 1}/{total}",
            )
            status_text.caption(f"_{q_text[:80]}..._" if len(q_text) > 80 else f"_{q_text}_")

        with st.spinner("Evaluation en cours (cela peut prendre quelques minutes)..."):
            summary = run_evaluation(
                vectorstore=vectorstore,
                llm=llm,
                nb_sources=nb_sources,
                progress_callback=eval_progress,
                bm25_index=bm25_index,
                enable_enhanced=True,
            )
            save_results(summary)

        progress_bar.progress(1.0, text="Evaluation terminee !")
        status_text.empty()
        prev_results = summary

    if prev_results:
        st.markdown("---")
        st.markdown("### Resultats")

        # Main score
        score_col1, score_col2, score_col3, score_col4 = st.columns(4)
        score_col1.metric(
            "Score global",
            f"{prev_results.overall_score:.1%}",
            help="Score composite pondere",
        )
        score_col2.metric(
            "Fidelite",
            f"{prev_results.avg_faithfulness:.1%}",
            help="Reponse fidele au contexte (pas d'hallucination)",
        )
        score_col3.metric(
            "Pertinence",
            f"{prev_results.avg_relevance:.1%}",
            help="Reponse qui adresse la question",
        )
        score_col4.metric(
            "Completude",
            f"{prev_results.avg_completeness:.1%}",
            help="Couverture des points attendus",
        )

        # Secondary metrics
        sec_col1, sec_col2, sec_col3, sec_col4, sec_col5 = st.columns(5)
        sec_col1.metric(
            "Similarite semantique",
            f"{getattr(prev_results, 'avg_semantic_similarity', 0):.1%}",
            help="Cosine similarity entre reponse attendue et generee",
        )
        sec_col2.metric("Mots-cles (reponse)", f"{prev_results.avg_keyword_coverage:.1%}")
        sec_col3.metric("Match matiere", f"{prev_results.avg_subject_match:.1%}")
        sec_col4.metric("Mots-cles (retrieval)", f"{prev_results.avg_keyword_hit:.1%}")
        sec_col5.metric("Latence moy.", f"{prev_results.avg_latency:.1f}s")

        # Per-question details
        if prev_results.results:
            st.markdown("### Detail par question")
            for i, r in enumerate(prev_results.results):
                label = f"Q{i+1}. {r['question'][:60]}..."
                faith = r['answer']['faithfulness_score']
                relev = r['answer']['relevance_score']
                compl = r['answer']['completeness_score']
                avg_q = (faith + relev + compl) / 3

                # Color code
                if avg_q >= 0.7:
                    icon = "✅"
                elif avg_q >= 0.4:
                    icon = "⚠️"
                else:
                    icon = "❌"

                with st.expander(f"{icon} {label} — {avg_q:.0%}"):
                    qcol1, qcol2, qcol3, qcol4, qcol5 = st.columns(5)
                    qcol1.metric("Fidelite", f"{faith:.0%}")
                    qcol2.metric("Pertinence", f"{relev:.0%}")
                    qcol3.metric("Completude", f"{compl:.0%}")
                    sem_sim = r['answer'].get('semantic_similarity', 0)
                    qcol4.metric("Sim. semantique", f"{sem_sim:.0%}")
                    qcol5.metric("Latence", f"{r['latency_seconds']:.1f}s")

                    st.markdown("**Reponse attendue :**")
                    st.info(r['expected_answer'])
                    st.markdown("**Reponse generee :**")
                    st.success(r['generated_answer'][:500])
                    if r.get('retrieved_sources'):
                        st.markdown("**Sources recuperees :**")
                        st.caption(", ".join(r['retrieved_sources'][:5]))

            # Summary table
            st.markdown("### Tableau recapitulatif")
            table_data = []
            for i, r in enumerate(prev_results.results):
                table_data.append({
                    "#": i + 1,
                    "Matiere": r['subject'],
                    "Fidelite": f"{r['answer']['faithfulness_score']:.0%}",
                    "Pertinence": f"{r['answer']['relevance_score']:.0%}",
                    "Completude": f"{r['answer']['completeness_score']:.0%}",
                    "Sim. semantique": f"{r['answer'].get('semantic_similarity', 0):.0%}",
                    "Mots-cles": f"{r['answer']['keyword_coverage']:.0%}",
                    "Latence": f"{r['latency_seconds']:.1f}s",
                })
            st.dataframe(
                pd.DataFrame(table_data),
                use_container_width=True,
                hide_index=True,
            )

            # CSV export
            csv_rows = []
            for i, r in enumerate(prev_results.results):
                csv_rows.append({
                    "#": i + 1,
                    "Matiere": r["subject"],
                    "Fidelite": f"{r['answer']['faithfulness_score']:.0%}",
                    "Pertinence": f"{r['answer']['relevance_score']:.0%}",
                    "Completude": f"{r['answer']['completeness_score']:.0%}",
                    "Sim_semantique": f"{r['answer'].get('semantic_similarity', 0):.0%}",
                    "Mots-cles": f"{r['answer']['keyword_coverage']:.0%}",
                    "Latence": f"{r['latency_seconds']:.1f}s",
                })
            csv_df = pd.DataFrame(csv_rows)
            st.download_button(
                "Telecharger les resultats (CSV)",
                data=csv_df.to_csv(index=False),
                file_name=f"eval_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

        # Eval history comparison
        history = list_eval_history()
        if len(history) >= 2:
            st.markdown("### Historique des evaluations")
            hist_data = []
            for h in history[:10]:  # last 10 runs
                hist_data.append({
                    "Date": h["timestamp"][:19],
                    "Score global": f"{h['overall_score']:.1%}",
                    "Fidelite": f"{h['avg_faithfulness']:.1%}",
                    "Pertinence": f"{h['avg_relevance']:.1%}",
                    "Completude": f"{h['avg_completeness']:.1%}",
                    "Sim. semantique": f"{h.get('avg_semantic_similarity', 0):.1%}",
                    "Questions": h["total_questions"],
                })
            st.dataframe(
                pd.DataFrame(hist_data),
                use_container_width=True,
                hide_index=True,
            )

            # Delta vs previous run
            if len(history) >= 2:
                curr, prev = history[0], history[1]
                delta = curr["overall_score"] - prev["overall_score"]
                delta_faith = curr["avg_faithfulness"] - prev["avg_faithfulness"]
                if delta >= 0:
                    st.success(
                        f"Evolution vs run precedent : score global **{delta:+.1%}**, "
                        f"fidelite **{delta_faith:+.1%}**"
                    )
                else:
                    st.warning(
                        f"Evolution vs run precedent : score global **{delta:+.1%}**, "
                        f"fidelite **{delta_faith:+.1%}**"
                    )
