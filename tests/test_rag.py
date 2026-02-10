"""
Tests unitaires et d'integration pour le systeme RAG Master 1.

Tests couverts:
- Indexation et retrieval
- Pipeline RAG complet
- Ameliorations (rewrite, hybrid, rerank, compress)
- Evaluation
"""

import os
import pytest
from pathlib import Path

from langchain_core.documents import Document

OPENAI_API_KEY = os.getenv("OPENAI_api_key")

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not OPENAI_API_KEY,
    reason="OPENAI_api_key not found in environment",
)


# ---------------------------------------------------------------------------
# Unit Tests - Indexation
# ---------------------------------------------------------------------------

class TestIndexation:
    """Tests for document indexation."""

    def test_create_vectorstore(self, temp_chroma_dir, embeddings, sample_documents):
        from langchain_community.vectorstores import Chroma

        vs = Chroma.from_documents(
            sample_documents,
            embeddings,
            persist_directory=str(temp_chroma_dir),
        )
        results = vs.similarity_search("tri fusion", k=1)
        assert len(results) > 0
        assert "tri fusion" in results[0].page_content.lower()

    def test_add_documents(self, vectorstore):
        new_doc = Document(
            page_content="MapReduce permet le traitement distribue de donnees.",
            metadata={"matiere": "Systemes Distribues", "doc_type": "CM", "filename": "distrib.txt"},
        )
        initial_count = len(vectorstore.get()["ids"])
        vectorstore.add_documents([new_doc])
        final_count = len(vectorstore.get()["ids"])
        assert final_count > initial_count

    def test_metadata_preservation(self, vectorstore):
        results = vectorstore.similarity_search("apprentissage supervise", k=1)
        assert results[0].metadata["matiere"] == "Intelligence Artificielle"
        assert results[0].metadata["doc_type"] == "CM"


# ---------------------------------------------------------------------------
# Unit Tests - Retrieval
# ---------------------------------------------------------------------------

class TestRetrieval:
    """Tests for document retrieval."""

    def test_similarity_search(self, vectorstore):
        results = vectorstore.similarity_search("algorithme de tri", k=2)
        assert len(results) > 0
        assert any("tri" in r.page_content.lower() for r in results)

    def test_mmr_search(self, vectorstore):
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 2, "fetch_k": 3},
        )
        results = retriever.invoke("intelligence artificielle")
        assert len(results) > 0

    def test_filter_by_subject(self, vectorstore):
        results = vectorstore.similarity_search(
            "algorithme",
            k=5,
            filter={"matiere": "Algorithmique"},
        )
        assert all(r.metadata["matiere"] == "Algorithmique" for r in results)


# ---------------------------------------------------------------------------
# Unit Tests - RAG Improvements
# ---------------------------------------------------------------------------

class TestRAGImprovements:
    """Tests for RAG improvement components."""

    def test_query_rewrite(self, llm):
        from core.retrieval import rewrite_query

        result = rewrite_query("Qu'est-ce que le tri fusion ?", llm)
        assert "rewritten" in result
        assert "keywords" in result
        assert len(result["rewritten"]) > 0

    def test_bm25_index(self, sample_documents):
        from core.retrieval import BM25Index

        bm25 = BM25Index(sample_documents)
        results = bm25.query("tri fusion algorithme", k=2)
        assert len(results) > 0
        assert results[0][1] > 0

    def test_hybrid_search(self, vectorstore, sample_documents):
        from core.retrieval import BM25Index, hybrid_search

        bm25 = BM25Index(sample_documents)
        results = hybrid_search("algorithme de tri", vectorstore, bm25, k=2)
        assert len(results) > 0
        assert all(isinstance(doc, Document) for doc in results)

    def test_compress_documents(self, llm, sample_documents):
        from core.retrieval import compress_documents

        compressed = compress_documents(
            "Quelle est la complexite du tri fusion ?",
            sample_documents,
            llm,
            max_docs=3,
        )
        assert len(compressed) > 0
        assert all(isinstance(doc, Document) for doc in compressed)


# ---------------------------------------------------------------------------
# Integration Tests - Full RAG Pipeline
# ---------------------------------------------------------------------------

class TestFullPipeline:
    """Integration tests for the complete RAG pipeline."""

    def test_basic_rag_query(self, vectorstore, llm):
        from langchain_core.prompts import ChatPromptTemplate

        docs = vectorstore.similarity_search("tri fusion", k=2)
        assert len(docs) > 0

        context = "\n\n".join(doc.page_content for doc in docs)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Tu es un assistant pedagogique. Reponds en te basant sur: {context}"),
            ("human", "{question}"),
        ])

        messages = prompt.invoke({
            "context": context,
            "question": "Quelle est la complexite du tri fusion ?",
        })

        response = llm.invoke(messages)
        assert response.content
        assert len(response.content) > 20

    def test_enhanced_retrieve(self, vectorstore, llm, sample_documents):
        from core.retrieval import BM25Index, enhanced_retrieve

        bm25 = BM25Index(sample_documents)

        result = enhanced_retrieve(
            question="Comment fonctionne l'apprentissage supervise ?",
            vectorstore=vectorstore,
            llm=llm,
            bm25_index=bm25,
            nb_sources=3,
            enable_rewrite=True,
            enable_hybrid=True,
            enable_rerank=False,
            enable_compress=False,
        )
        assert "documents" in result
        assert "rewritten_query" in result
        assert "steps_applied" in result
        assert len(result["documents"]) > 0
        assert len(result["steps_applied"]) > 0


# ---------------------------------------------------------------------------
# Integration Tests - Evaluation
# ---------------------------------------------------------------------------

class TestEvaluation:
    """Tests for the evaluation system."""

    def test_evaluation_metrics_computation(self, llm, embeddings):
        from evaluation.evaluator import evaluate_answer

        metrics = evaluate_answer(
            question="Qu'est-ce que le tri fusion ?",
            expected_answer="Le tri fusion est un algorithme de tri avec complexite O(n log n).",
            generated_answer="Le tri fusion est un algorithme efficace de complexite O(n log n).",
            context="Le tri fusion divise le tableau en deux et fusionne les resultats.",
            keywords=["tri fusion", "O(n log n)", "algorithme"],
            llm=llm,
            embeddings=embeddings,
        )
        assert 0 <= metrics.faithfulness_score <= 1
        assert 0 <= metrics.relevance_score <= 1
        assert 0 <= metrics.completeness_score <= 1
        assert 0 <= metrics.keyword_coverage <= 1
        assert 0 <= metrics.semantic_similarity <= 1

    def test_retrieval_metrics(self, sample_documents):
        from evaluation.evaluator import evaluate_retrieval

        metrics = evaluate_retrieval(
            docs=sample_documents[:2],
            expected_subject="Algorithmique",
            expected_keywords=["tri", "algorithme", "complexite"],
        )
        assert metrics.num_docs_retrieved == 2
        assert 0 <= metrics.subject_match_ratio <= 1
        assert 0 <= metrics.keyword_hit_ratio <= 1

    @pytest.mark.slow
    def test_full_evaluation_run(self, vectorstore, llm):
        from evaluation.evaluator import run_evaluation, EVAL_DATASET

        mini_dataset = EVAL_DATASET[:2]

        summary = run_evaluation(
            vectorstore=vectorstore,
            llm=llm,
            dataset=mini_dataset,
            nb_sources=3,
            enable_enhanced=False,
        )
        assert summary.total_questions == 2
        assert 0 <= summary.overall_score <= 1
        assert len(summary.results) == 2


# ---------------------------------------------------------------------------
# Unit Tests - Indexer Utils
# ---------------------------------------------------------------------------

class TestIndexerUtils:
    """Tests for indexer utility functions."""

    def test_compute_file_hash(self, tmp_path):
        from core.indexer import compute_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        hash1 = compute_file_hash(str(test_file))
        assert len(hash1) == 32

        hash2 = compute_file_hash(str(test_file))
        assert hash1 == hash2

        test_file.write_text("Hello World!")
        hash3 = compute_file_hash(str(test_file))
        assert hash3 != hash1

    def test_should_exclude_path(self, tmp_path):
        from core.indexer import should_exclude_path

        base = tmp_path
        assert should_exclude_path(str(base / "__pycache__" / "file.pyc"), base)
        assert should_exclude_path(str(base / ".git" / "config"), base)
        assert not should_exclude_path(str(base / "docs" / "file.pdf"), base)


# ---------------------------------------------------------------------------
# Run Tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
