"""
Evaluation -- Automated evaluation framework for the RAG system.

Measures retrieval quality, answer faithfulness, answer relevance,
and provides detailed per-question diagnostics.  Can be run standalone
(CLI) or imported by the Streamlit UI for interactive evaluation.
"""

import json
import logging
import time
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict

import numpy as np

logger = logging.getLogger(__name__)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

from core.config import OPENAI_API_KEY, CHROMA_DIR, EVAL_RESULTS_DIR
from core.constants import (
    LLM_MODEL,
    LLM_JUDGE_TEMPERATURE,
    EMBEDDING_MODEL,
    META_MATIERE,
    META_DOC_TYPE,
    META_FILENAME,
    DEFAULT_MATIERE,
    DEFAULT_DOC_TYPE,
    DEFAULT_NB_SOURCES,
    FETCH_K_MULTIPLIER,
    SEARCH_TYPE_MMR,
    SYSTEM_PROMPT,
    EVAL_WEIGHT_FAITHFULNESS,
    EVAL_WEIGHT_RELEVANCE,
    EVAL_WEIGHT_COMPLETENESS,
    EVAL_WEIGHT_SEMANTIC_SIM,
    EVAL_WEIGHT_KEYWORD_COV,
    EVAL_WEIGHT_SUBJECT_MATCH,
    EVAL_WEIGHT_KEYWORD_HIT,
    EVAL_LATEST_FILENAME,
    EVAL_HISTORY_GLOB,
    EVAL_MAX_CONTEXT_LENGTH,
    EVAL_MAX_ANSWER_LENGTH,
    EVAL_MAX_ANSWER_JUDGE,
    EVAL_MAX_EMBED_LENGTH,
)

# ---------------------------------------------------------------------------
# Evaluation dataset -- ground-truth Q&A pairs per subject
# ---------------------------------------------------------------------------

EVAL_DATASET: list[dict[str, Any]] = [
    # -- Algorithmique --
    {
        "question": "Quelle est la complexite temporelle du tri par fusion (merge sort) ?",
        "expected_answer": "O(n log n) dans tous les cas (meilleur, moyen, pire).",
        "subject": "Algorithmique",
        "keywords": ["O(n log n)", "merge sort", "tri fusion", "diviser pour regner"],
    },
    {
        "question": "Qu'est-ce qu'un algorithme glouton et donner un exemple ?",
        "expected_answer": "Un algorithme glouton fait a chaque etape le choix localement optimal. Exemple : algorithme de Kruskal pour l'arbre couvrant minimum.",
        "subject": "Algorithmique",
        "keywords": ["glouton", "greedy", "optimal local", "Kruskal", "Dijkstra"],
    },
    # -- Intelligence Artificielle --
    {
        "question": "Quelle est la difference entre l'apprentissage supervise et non supervise ?",
        "expected_answer": "L'apprentissage supervise utilise des donnees etiquetees pour entrainer le modele, tandis que le non supervise decouvre des structures dans des donnees non etiquetees.",
        "subject": "Intelligence Artificielle",
        "keywords": ["supervise", "non supervise", "etiquetees", "labels", "clustering", "classification"],
    },
    {
        "question": "Qu'est-ce que la descente de gradient ?",
        "expected_answer": "La descente de gradient est un algorithme d'optimisation qui ajuste iterativement les parametres d'un modele en suivant le gradient negatif de la fonction de cout.",
        "subject": "Intelligence Artificielle",
        "keywords": ["gradient", "optimisation", "fonction de cout", "learning rate", "parametres"],
    },
    # -- Logique & Prolog --
    {
        "question": "Qu'est-ce que l'unification en Prolog ?",
        "expected_answer": "L'unification est le mecanisme par lequel Prolog tente de rendre deux termes identiques en trouvant une substitution de variables appropriee.",
        "subject": "Logique & Prolog",
        "keywords": ["unification", "substitution", "variable", "termes", "Prolog"],
    },
    {
        "question": "Expliquer le principe de resolution en logique des predicats.",
        "expected_answer": "La resolution est une regle d'inference qui, a partir de deux clauses contenant des litteraux complementaires, derive une nouvelle clause (resolvante). C'est la base du moteur d'inference de Prolog.",
        "subject": "Logique & Prolog",
        "keywords": ["resolution", "clause", "litteral", "inference", "resolvante"],
    },
    # -- Systemes Distribues --
    {
        "question": "Qu'est-ce que le paradigme MapReduce et comment fonctionne-t-il ?",
        "expected_answer": "MapReduce est un modele de programmation pour le traitement distribue de grandes quantites de donnees. Il se compose de deux phases : Map (applique une fonction a chaque element pour produire des paires cle-valeur) et Reduce (aggrege les valeurs par cle).",
        "subject": "Systemes Distribues",
        "keywords": ["MapReduce", "Map", "Reduce", "cle", "valeur", "distribue"],
    },
    {
        "question": "Expliquer le consensus dans les systemes distribues.",
        "expected_answer": "Le consensus est un probleme fondamental ou un ensemble de processus doivent se mettre d'accord sur une valeur commune, meme en presence de pannes. Algorithmes : Paxos, Raft.",
        "subject": "Systemes Distribues",
        "keywords": ["consensus", "Paxos", "Raft", "accord", "pannes", "processus"],
    },
    # -- Cloud & Reseaux --
    {
        "question": "Quelles sont les couches du modele OSI et a quoi servent-elles ?",
        "expected_answer": "Le modele OSI comporte 7 couches : Physique, Liaison, Reseau, Transport, Session, Presentation, Application. Chaque couche fournit des services a la couche superieure et utilise les services de la couche inferieure.",
        "subject": "Cloud & Reseaux",
        "keywords": ["OSI", "couche", "transport", "reseau", "application", "physique", "liaison"],
    },
    # -- Genie Logiciel --
    {
        "question": "Quels sont les principes SOLID en genie logiciel ?",
        "expected_answer": "SOLID : Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.",
        "subject": "Genie Logiciel",
        "keywords": ["SOLID", "Single Responsibility", "Open/Closed", "Liskov", "Interface Segregation", "Dependency Inversion"],
    },
    # -- Conception Web Avancee --
    {
        "question": "Qu'est-ce que le pattern MVC ?",
        "expected_answer": "MVC (Modele-Vue-Controleur) est un patron d'architecture qui separe l'application en trois composants : le Modele (donnees), la Vue (interface) et le Controleur (logique).",
        "subject": "Conception Web Avancee",
        "keywords": ["MVC", "Modele", "Vue", "Controleur", "separation", "architecture"],
    },
    # -- Analyse Exploratoire de Donnees --
    {
        "question": "Qu'est-ce que l'ACP (Analyse en Composantes Principales) ?",
        "expected_answer": "L'ACP est une methode de reduction de dimensionnalite qui projette les donnees sur les axes de variance maximale (composantes principales).",
        "subject": "Analyse Exploratoire de Donnees",
        "keywords": ["ACP", "composantes principales", "variance", "dimensionnalite", "projection"],
    },
    # -- SGD --
    {
        "question": "Qu'est-ce que la normalisation dans les bases de donnees relationnelles ?",
        "expected_answer": "La normalisation est un processus de structuration des tables pour eliminer la redondance et les anomalies. Formes normales : 1NF, 2NF, 3NF, BCNF.",
        "subject": "Systemes de Gestion de Donnees",
        "keywords": ["normalisation", "1NF", "2NF", "3NF", "BCNF", "redondance", "anomalie"],
    },
]

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RetrievalMetrics:
    """Metrics about the quality of retrieved documents."""
    num_docs_retrieved: int = 0
    subject_match_ratio: float = 0.0
    keyword_hit_ratio: float = 0.0
    avg_doc_length: float = 0.0
    unique_sources: int = 0


@dataclass
class AnswerMetrics:
    """Metrics about the generated answer quality."""
    faithfulness_score: float = 0.0
    relevance_score: float = 0.0
    completeness_score: float = 0.0
    keyword_coverage: float = 0.0
    semantic_similarity: float = 0.0
    answer_length: int = 0


@dataclass
class SingleEvalResult:
    """Full evaluation result for a single question."""
    question: str = ""
    expected_answer: str = ""
    generated_answer: str = ""
    subject: str = ""
    retrieval: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    answer: AnswerMetrics = field(default_factory=AnswerMetrics)
    latency_seconds: float = 0.0
    retrieved_sources: list[str] = field(default_factory=list)


@dataclass
class EvalSummary:
    """Aggregated summary over all evaluation questions."""
    total_questions: int = 0
    avg_faithfulness: float = 0.0
    avg_relevance: float = 0.0
    avg_completeness: float = 0.0
    avg_keyword_coverage: float = 0.0
    avg_semantic_similarity: float = 0.0
    avg_subject_match: float = 0.0
    avg_keyword_hit: float = 0.0
    avg_latency: float = 0.0
    overall_score: float = 0.0
    timestamp: str = ""
    results: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LLM-as-Judge prompts
# ---------------------------------------------------------------------------

FAITHFULNESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un evaluateur de fidelite pour un systeme RAG universitaire.\n"
        "Tu dois juger si la reponse generee est coherente avec le contexte fourni.\n\n"
        "GUIDE DE SCORING :\n"
        "- 1.0 : La reponse est entierement fondee sur le contexte\n"
        "- 0.8 : Essentiel correct, quelques elaborations pedagogiques mineures\n"
        "- 0.7 : Majoritairement fidele, ajouts de connaissance generale acceptables\n"
        "- 0.5 : Mix de contenu source et d'ajouts significatifs non fondes\n"
        "- 0.3 : Beaucoup d'informations inventees\n"
        "- 0.0 : Completement hallucine, rien ne vient du contexte\n\n"
        "REGLES IMPORTANTES :\n"
        "- Les explications pedagogiques qui CLARIFIENT le contexte sont acceptables\n"
        "- Les definitions standards en informatique coherentes avec le contexte sont OK\n"
        "- Seules les CONTRADICTIONS ou INVENTIONS factuelles = hallucination\n"
        "- Si la reponse dit que les documents ne couvrent pas le sujet, score >= 0.7\n\n"
        "Reponds UNIQUEMENT avec un JSON : {{\"score\": X, \"justification\": \"...\"}}"
    )),
    ("human", (
        "Question : {question}\n\n"
        "Contexte (documents recuperes) :\n{context}\n\n"
        "Reponse generee :\n{answer}\n\n"
        "Evalue la fidelite de la reponse par rapport au contexte."
    )),
])

RELEVANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un evaluateur strict. Tu dois juger si la reponse repond bien "
        "a la question posee.\n"
        "Donne un score entre 0 et 1 :\n"
        "- 1.0 : Repond parfaitement a la question\n"
        "- 0.7 : Repond correctement mais manque de precision\n"
        "- 0.5 : Repond partiellement\n"
        "- 0.3 : Repond vaguement ou hors sujet en partie\n"
        "- 0.0 : Ne repond pas du tout a la question\n"
        "Reponds UNIQUEMENT avec un JSON : {{\"score\": X, \"justification\": \"...\"}}"
    )),
    ("human", (
        "Question : {question}\n\n"
        "Reponse generee :\n{answer}\n\n"
        "Evalue la pertinence de la reponse."
    )),
])

COMPLETENESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "Tu es un evaluateur strict. Tu dois juger si la reponse generee "
        "couvre les memes informations que la reponse attendue.\n"
        "Donne un score entre 0 et 1 :\n"
        "- 1.0 : Couvre toutes les informations attendues\n"
        "- 0.7 : Couvre la majorite des points\n"
        "- 0.5 : Couvre environ la moitie\n"
        "- 0.3 : Couvre peu de points\n"
        "- 0.0 : Ne couvre aucun point attendu\n"
        "Reponds UNIQUEMENT avec un JSON : {{\"score\": X, \"justification\": \"...\"}}"
    )),
    ("human", (
        "Question : {question}\n\n"
        "Reponse attendue :\n{expected}\n\n"
        "Reponse generee :\n{answer}\n\n"
        "Evalue la completude de la reponse."
    )),
])


# ---------------------------------------------------------------------------
# Evaluation functions
# ---------------------------------------------------------------------------

def _parse_llm_score(response_text: str) -> tuple[float, str]:
    """Extract score and justification from LLM judge response."""
    try:
        text = response_text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(text[start:end + 1])
            return float(data.get("score", 0.0)), data.get("justification", "")
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"(\d+\.?\d*)", response_text)
    if match:
        score = float(match.group(1))
        if score > 1.0:
            score = score / 10.0 if score <= 10 else score / 100.0
        return min(score, 1.0), "Score extrait automatiquement"

    return 0.0, "Impossible d'extraire le score"


def _normalize_text(text: str) -> str:
    """Normalize text: lowercase, strip accents, collapse whitespace."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def compute_keyword_ratio(text: str, keywords: list[str]) -> float:
    """Compute the fraction of *keywords* found in *text*."""
    if not keywords:
        return 1.0
    text_norm = _normalize_text(text)
    hits = 0
    for kw in keywords:
        kw_norm = _normalize_text(kw)
        if kw_norm in text_norm:
            hits += 1
            continue
        if len(kw_norm) >= 5 and kw_norm[:4] in text_norm:
            hits += 0.5
    return hits / len(keywords)


def compute_semantic_similarity(
    text_a: str,
    text_b: str,
    embeddings: OpenAIEmbeddings,
) -> float:
    """Compute cosine similarity between two texts using embeddings."""
    try:
        vecs = embeddings.embed_documents([text_a[:EVAL_MAX_EMBED_LENGTH], text_b[:EVAL_MAX_EMBED_LENGTH]])
        a = np.array(vecs[0])
        b = np.array(vecs[1])
        cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
        return max(0.0, cos_sim)
    except Exception:
        return 0.0


def evaluate_retrieval(
    docs: list,
    expected_subject: str,
    expected_keywords: list[str],
) -> RetrievalMetrics:
    """Compute retrieval-quality metrics from a list of LangChain documents."""
    if not docs:
        return RetrievalMetrics()

    subject_matches = sum(
        1 for d in docs
        if d.metadata.get(META_MATIERE, "").lower() == expected_subject.lower()
    )

    all_text = " ".join(d.page_content for d in docs)
    keyword_hits = compute_keyword_ratio(all_text, expected_keywords)

    unique_files = {d.metadata.get(META_FILENAME, "") for d in docs}

    return RetrievalMetrics(
        num_docs_retrieved=len(docs),
        subject_match_ratio=subject_matches / len(docs) if docs else 0.0,
        keyword_hit_ratio=keyword_hits,
        avg_doc_length=sum(len(d.page_content) for d in docs) / len(docs),
        unique_sources=len(unique_files),
    )


def evaluate_answer(
    question: str,
    expected_answer: str,
    generated_answer: str,
    context: str,
    keywords: list[str],
    llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings | None = None,
) -> AnswerMetrics:
    """Compute answer-quality metrics using LLM-as-judge, keywords, and semantic similarity."""
    metrics = AnswerMetrics(answer_length=len(generated_answer))

    metrics.keyword_coverage = compute_keyword_ratio(generated_answer, keywords)

    if embeddings is not None:
        metrics.semantic_similarity = compute_semantic_similarity(
            expected_answer, generated_answer, embeddings,
        )

    try:
        faith_msgs = FAITHFULNESS_PROMPT.invoke({
            "question": question,
            "context": context[:EVAL_MAX_CONTEXT_LENGTH],
            "answer": generated_answer[:EVAL_MAX_ANSWER_LENGTH],
        })
        faith_resp = llm.invoke(faith_msgs)
        metrics.faithfulness_score, _ = _parse_llm_score(faith_resp.content)
    except Exception:
        metrics.faithfulness_score = 0.0

    try:
        rel_msgs = RELEVANCE_PROMPT.invoke({
            "question": question,
            "answer": generated_answer[:EVAL_MAX_ANSWER_JUDGE],
        })
        rel_resp = llm.invoke(rel_msgs)
        metrics.relevance_score, _ = _parse_llm_score(rel_resp.content)
    except Exception:
        metrics.relevance_score = 0.0

    try:
        comp_msgs = COMPLETENESS_PROMPT.invoke({
            "question": question,
            "expected": expected_answer,
            "answer": generated_answer[:EVAL_MAX_ANSWER_JUDGE],
        })
        comp_resp = llm.invoke(comp_msgs)
        metrics.completeness_score, _ = _parse_llm_score(comp_resp.content)
    except Exception:
        metrics.completeness_score = 0.0

    return metrics


# ---------------------------------------------------------------------------
# Main evaluation pipeline
# ---------------------------------------------------------------------------

def run_evaluation(
    vectorstore: Chroma,
    llm: ChatOpenAI,
    dataset: list[dict[str, Any]] | None = None,
    nb_sources: int = 10,
    progress_callback=None,
    bm25_index=None,
    enable_enhanced: bool = True,
) -> EvalSummary:
    """Run the full evaluation pipeline on the given dataset."""
    from langchain_core.prompts import ChatPromptTemplate as CPT

    if dataset is None:
        dataset = EVAL_DATASET

    enhanced_retrieve = None
    if enable_enhanced:
        try:
            from core.retrieval import enhanced_retrieve as _er
            enhanced_retrieve = _er
        except ImportError:
            pass

    judge_llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_JUDGE_TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
    )

    eval_embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    eval_prompt = CPT.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

    results: list[SingleEvalResult] = []

    for idx, item in enumerate(dataset):
        question = item["question"]
        expected = item["expected_answer"]
        subject = item.get("subject", "")
        keywords = item.get("keywords", [])

        if progress_callback:
            progress_callback(idx, len(dataset), question)

        start = time.time()

        if enhanced_retrieve is not None:
            retrieval_result = enhanced_retrieve(
                question=question,
                vectorstore=vectorstore,
                llm=llm,
                bm25_index=bm25_index,
                nb_sources=nb_sources,
                enable_rewrite=True,
                enable_hybrid=(bm25_index is not None),
                enable_rerank=False,
                enable_compress=False,
            )
            docs = retrieval_result["documents"]
        else:
            search_kwargs = {"k": nb_sources, "fetch_k": nb_sources * FETCH_K_MULTIPLIER}
            retriever = vectorstore.as_retriever(
                search_type=SEARCH_TYPE_MMR,
                search_kwargs=search_kwargs,
            )
            docs = retriever.invoke(question)

        context_parts = []
        for doc in docs:
            matiere = doc.metadata.get(META_MATIERE, DEFAULT_MATIERE)
            doc_type = doc.metadata.get(META_DOC_TYPE, DEFAULT_DOC_TYPE)
            filename = doc.metadata.get(META_FILENAME, "")
            context_parts.append(
                f"[{matiere} -- {doc_type} -- {filename}]\n{doc.page_content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        messages = eval_prompt.invoke({
            "context": context,
            "question": question,
        })
        response = llm.invoke(messages)
        generated = response.content

        elapsed = time.time() - start

        ret_metrics = evaluate_retrieval(docs, subject, keywords)

        ans_metrics = evaluate_answer(
            question, expected, generated, context, keywords, judge_llm,
            embeddings=eval_embeddings,
        )

        source_names = list({
            doc.metadata.get(META_FILENAME, "") for doc in docs
        })

        result = SingleEvalResult(
            question=question,
            expected_answer=expected,
            generated_answer=generated,
            subject=subject,
            retrieval=ret_metrics,
            answer=ans_metrics,
            latency_seconds=round(elapsed, 2),
            retrieved_sources=source_names,
        )
        results.append(result)

    n = len(results)
    summary = EvalSummary(
        total_questions=n,
        avg_faithfulness=sum(r.answer.faithfulness_score for r in results) / n if n else 0,
        avg_relevance=sum(r.answer.relevance_score for r in results) / n if n else 0,
        avg_completeness=sum(r.answer.completeness_score for r in results) / n if n else 0,
        avg_keyword_coverage=sum(r.answer.keyword_coverage for r in results) / n if n else 0,
        avg_semantic_similarity=sum(r.answer.semantic_similarity for r in results) / n if n else 0,
        avg_subject_match=sum(r.retrieval.subject_match_ratio for r in results) / n if n else 0,
        avg_keyword_hit=sum(r.retrieval.keyword_hit_ratio for r in results) / n if n else 0,
        avg_latency=sum(r.latency_seconds for r in results) / n if n else 0,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        results=[asdict(r) for r in results],
    )

    summary.overall_score = round(
        EVAL_WEIGHT_FAITHFULNESS * summary.avg_faithfulness
        + EVAL_WEIGHT_RELEVANCE * summary.avg_relevance
        + EVAL_WEIGHT_COMPLETENESS * summary.avg_completeness
        + EVAL_WEIGHT_SEMANTIC_SIM * summary.avg_semantic_similarity
        + EVAL_WEIGHT_KEYWORD_COV * summary.avg_keyword_coverage
        + EVAL_WEIGHT_SUBJECT_MATCH * summary.avg_subject_match
        + EVAL_WEIGHT_KEYWORD_HIT * summary.avg_keyword_hit,
        4,
    )

    return summary


def save_results(summary: EvalSummary, filename: str = EVAL_LATEST_FILENAME) -> Path:
    """Persist evaluation results to a JSON file + timestamped copy."""
    EVAL_RESULTS_DIR.mkdir(exist_ok=True)
    filepath = EVAL_RESULTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(asdict(summary), fh, ensure_ascii=False, indent=2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_path = EVAL_RESULTS_DIR / f"eval_{ts}.json"
    with open(history_path, "w", encoding="utf-8") as fh:
        json.dump(asdict(summary), fh, ensure_ascii=False, indent=2)
    return filepath


def list_eval_history() -> list[dict]:
    """List all past evaluation runs with their scores, sorted newest first."""
    if not EVAL_RESULTS_DIR.exists():
        return []
    history = []
    for fp in sorted(EVAL_RESULTS_DIR.glob(EVAL_HISTORY_GLOB), reverse=True):
        try:
            with open(fp, encoding="utf-8") as fh:
                data = json.load(fh)
            history.append({
                "filename": fp.name,
                "timestamp": data.get("timestamp", fp.stem.replace("eval_", "")),
                "overall_score": data.get("overall_score", 0),
                "avg_faithfulness": data.get("avg_faithfulness", 0),
                "avg_relevance": data.get("avg_relevance", 0),
                "avg_completeness": data.get("avg_completeness", 0),
                "avg_semantic_similarity": data.get("avg_semantic_similarity", 0),
                "avg_keyword_coverage": data.get("avg_keyword_coverage", 0),
                "total_questions": data.get("total_questions", 0),
            })
        except Exception:
            continue
    return history


def load_results(filename: str = EVAL_LATEST_FILENAME) -> EvalSummary | None:
    """Load previously saved evaluation results."""
    filepath = EVAL_RESULTS_DIR / filename
    if not filepath.exists():
        return None
    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)
    return EvalSummary(**{k: v for k, v in data.items()})


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run evaluation from the command line and print results."""
    print("=" * 55)
    print("Evaluation du systeme RAG - Master 1")
    print("=" * 55)

    if not OPENAI_API_KEY:
        print("ERREUR: Cle API OpenAI introuvable dans .env")
        return

    if not CHROMA_DIR.exists():
        print("ERREUR: Base vectorielle introuvable. Lancez: python -m scripts.index")
        return

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )
    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )
    judge_llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_JUDGE_TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
    )

    from core.retrieval import BM25Index
    from langchain_core.documents import Document as LCDoc

    print("Construction de l'index BM25...")
    bm25_index = None
    all_docs = vectorstore.get(include=["documents", "metadatas"])
    if all_docs and all_docs.get("documents"):
        docs = [
            LCDoc(page_content=content, metadata=meta or {})
            for content, meta in zip(
                all_docs["documents"], all_docs["metadatas"]
            )
        ]
        bm25_index = BM25Index(docs)
        print(f"  Index BM25: {len(docs)} documents indexes")

    def progress(idx, total, q):
        print(f"\n  [{idx + 1}/{total}] {q[:70]}...")

    summary = run_evaluation(
        vectorstore, judge_llm, progress_callback=progress,
        bm25_index=bm25_index, enable_enhanced=True,
    )

    print("\n" + "=" * 55)
    print("RESULTATS GLOBAUX")
    print("=" * 55)
    print(f"  Questions evaluees   : {summary.total_questions}")
    print(f"  Score global         : {summary.overall_score:.2%}")
    print(f"  Fidelite (faithf.)   : {summary.avg_faithfulness:.2%}")
    print(f"  Pertinence (relev.)  : {summary.avg_relevance:.2%}")
    print(f"  Completude           : {summary.avg_completeness:.2%}")
    print(f"  Couverture mots-cles : {summary.avg_keyword_coverage:.2%}")
    print(f"  Match matiere        : {summary.avg_subject_match:.2%}")
    print(f"  Keywords retrieval   : {summary.avg_keyword_hit:.2%}")
    print(f"  Latence moyenne      : {summary.avg_latency:.1f}s")

    filepath = save_results(summary)
    print(f"\nResultats sauvegardes dans {filepath}")


if __name__ == "__main__":
    main()
