"""
Shared pytest fixtures for the RAG Master 1 test suite.
"""

import os
import tempfile
import shutil
from pathlib import Path

import pytest
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for ChromaDB during tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def embeddings():
    """Create embeddings instance for tests."""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )


@pytest.fixture
def llm():
    """Create LLM instance for tests."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=OPENAI_API_KEY,
    )


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            page_content="Le tri fusion est un algorithme de tri avec une complexite O(n log n).",
            metadata={"matiere": "Algorithmique", "doc_type": "CM", "filename": "algo.txt"},
        ),
        Document(
            page_content="L'apprentissage supervise utilise des donnees etiquetees pour entrainer un modele.",
            metadata={"matiere": "Intelligence Artificielle", "doc_type": "CM", "filename": "ia.txt"},
        ),
        Document(
            page_content="Prolog utilise l'unification pour rendre deux termes identiques.",
            metadata={"matiere": "Logique & Prolog", "doc_type": "CM", "filename": "prolog.txt"},
        ),
    ]


@pytest.fixture
def vectorstore(temp_chroma_dir, embeddings, sample_documents):
    """Create a test vectorstore with sample documents."""
    return Chroma.from_documents(
        sample_documents,
        embeddings,
        persist_directory=str(temp_chroma_dir),
    )
