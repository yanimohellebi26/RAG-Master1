"""
RAG Chat – Interface Streamlit pour interroger les cours du Master 1.
Utilise ChromaDB comme base vectorielle et GPT-4o-mini comme LLM.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ── Configuration ──────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_api_key")
CHROMA_DIR = Path(__file__).parent / "chroma_db"

# ── Page Streamlit ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Master 1",
    page_icon="M1",
    layout="wide",
)

# ── Styles CSS ─────────────────────────────────────────────────────────────
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">Assistant RAG - Master 1 Informatique</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Posez vos questions sur vos cours : Algo, IA, Logique, Systèmes Distribués, etc.</p>', unsafe_allow_html=True)


# ── Vérifications ──────────────────────────────────────────────────────────
if not OPENAI_API_KEY:
    st.error("Cle API OpenAI introuvable. Verifiez votre fichier .env.")
    st.stop()

if not CHROMA_DIR.exists():
    st.error("Base vectorielle introuvable. Lancez d'abord : python indexer.py")
    st.stop()


# ── Chargement de la base vectorielle (cached) ────────────────────────────
@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )


@st.cache_resource
def load_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=OPENAI_API_KEY,
    )


vectorstore = load_vectorstore()
llm = load_llm()
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 12},
)

# ── Prompt système ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un assistant pédagogique expert pour un étudiant en Master 1 Informatique.
Tu réponds en français de manière claire, structurée et pédagogique.

Règles :
1. Base tes réponses UNIQUEMENT sur le contexte fourni (extraits de cours).
2. Si le contexte ne contient pas assez d'informations, dis-le clairement.
3. Cite les sources (matière, type de document) quand c'est pertinent.
4. Utilise des exemples et des explications simples.
5. Structure tes réponses avec des titres, listes à puces, etc.
6. Si on te demande un exercice, guide l'étudiant étape par étape.

Contexte des cours :
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])


def format_docs(docs):
    """Formate les documents récupérés en texte."""
    formatted = []
    for doc in docs:
        matiere = doc.metadata.get("matiere", "Inconnu")
        doc_type = doc.metadata.get("doc_type", "Document")
        filename = doc.metadata.get("filename", "")
        formatted.append(
            f"[{matiere} – {doc_type} – {filename}]\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(formatted)


# ── Session State ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Parametres")

    # Liste des matieres (statique pour eviter de charger 60k docs)
    all_matieres = sorted([
        "Algorithmique",
        "Analyse Exploratoire de Donnees",
        "Cloud & Reseaux",
        "Conception Web Avancee",
        "Genie Logiciel",
        "Intelligence Artificielle",
        "Logique & Prolog",
        "Systemes Distribues",
        "Systemes de Gestion de Donnees",
    ])

    selected_matieres = st.multiselect(
        "Filtrer par matiere",
        options=all_matieres,
        default=[],
        help="Laissez vide pour chercher dans toutes les matieres.",
    )

    st.markdown("---")

    nb_sources = st.slider("Nombre de sources", 2, 30, 10)

    st.markdown("---")

    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("### Matieres indexees")
    for mat in all_matieres:
        st.markdown(f"- {mat}")

    st.markdown("---")
    st.markdown(
        "<small>LangChain + ChromaDB + OpenAI</small>",
        unsafe_allow_html=True,
    )

# ── Affichage de l'historique ──────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources utilisees"):
                for src in message["sources"]:
                    st.markdown(
                        f'<div class="source-box">'
                        f'<span class="matiere-tag">{src["matiere"]}</span> '
                        f'**{src["doc_type"]}** – _{src["filename"]}_'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

# ── Input utilisateur ─────────────────────────────────────────────────────
if user_input := st.chat_input("Posez votre question sur vos cours..."):
    # Afficher la question
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Récupérer les documents pertinents
    with st.chat_message("assistant"):
        with st.spinner("Recherche dans vos cours..."):
            # Appliquer le filtre par matiere si selectionne
            if selected_matieres:
                search_kwargs = {
                    "k": nb_sources,
                    "fetch_k": nb_sources * 3,
                    "filter": {"matiere": {"$in": selected_matieres}},
                }
            else:
                search_kwargs = {
                    "k": nb_sources,
                    "fetch_k": nb_sources * 3,
                }

            filtered_retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs,
            )

            relevant_docs = filtered_retriever.invoke(user_input)

            # Construire le contexte
            context = format_docs(relevant_docs)

            # Construire les messages
            messages = prompt.invoke({
                "context": context,
                "chat_history": st.session_state.chat_history,
                "question": user_input,
            })

            # Streaming de la réponse
            response_placeholder = st.empty()
            full_response = ""

            for chunk in llm.stream(messages):
                if chunk.content:
                    full_response += chunk.content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

            # Sources
            sources = []
            seen = set()
            for doc in relevant_docs:
                key = doc.metadata.get("filename", "")
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "matiere": doc.metadata.get("matiere", "Inconnu"),
                        "doc_type": doc.metadata.get("doc_type", "Document"),
                        "filename": doc.metadata.get("filename", ""),
                    })

            # Afficher les sources directement à la fin
            if sources:
                st.markdown("---")
                st.markdown("### Ressources utilisées")
                for src in sources:
                    st.markdown(
                        f'<div class="source-box">'
                        f'<span class="matiere-tag">{src["matiere"]}</span> '
                        f'**{src["doc_type"]}** – _{src["filename"]}_'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # Sauvegarder dans l'historique
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
    })
    st.session_state.chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=full_response),
    ])
