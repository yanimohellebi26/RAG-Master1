"""
Indexer -- Ingest Master 1 course documents into a ChromaDB vector store.

Supports PDF, TXT and CSV files.  Handles large volumes through batch
embedding with automatic retry on rate-limit errors.
"""

import os
import sys
import time
import shutil
from pathlib import Path
from collections import Counter

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_api_key")
if not OPENAI_API_KEY:
    sys.exit("Cle API OpenAI introuvable dans .env")

BASE_DIR: Path = Path(__file__).parent
COURSES_DIR: Path = BASE_DIR / "Master1"
CHROMA_DIR: Path = BASE_DIR / "chroma_db"

CHUNK_SIZE: int = 3000
CHUNK_OVERLAP: int = 400
BATCH_SIZE: int = 400
MAX_RETRIES: int = 6
MIN_PAGE_LENGTH: int = 50
MIN_LINE_LENGTH: int = 3
SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".txt", ".csv"}

# Folder name -> human-readable subject label
SUBJECT_NAMES: dict[str, str] = {
    "Algo": "Algorithmique",
    "AnalyseExplo": "Analyse Exploratoire de Donnees",
    "Cloud": "Cloud & Reseaux",
    "CWA": "Conception Web Avancee",
    "GenieLog": "Genie Logiciel",
    "IA": "Intelligence Artificielle",
    "Logique": "Logique & Prolog",
    "SGBDGraphes": "SGBD Graphes",
    "SGD": "Systemes de Gestion de Donnees",
    "SystDistri": "Systemes Distribues",
}

# Filename keywords -> document type classification
_CM_KEYWORDS: tuple[str, ...] = (
    "cm", "cours", "slide",
    "ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7",
)
_EXAM_KEYWORDS: tuple[str, ...] = ("exam", "ct ", "ct_", "cc_", "annale")
_CORRECTION_KEYWORDS: tuple[str, ...] = ("corr", "cor", "solution")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_subject(filepath: str) -> str:
    """Derive the subject label from the file's position under COURSES_DIR."""
    rel = os.path.relpath(filepath, COURSES_DIR)
    folder = rel.split(os.sep)[0]
    return SUBJECT_NAMES.get(folder, folder)


def get_doc_type(filename: str) -> str:
    """Classify a document by its filename into CM, TD, TP, Examen, etc."""
    lower = filename.lower()
    if any(kw in lower for kw in _CM_KEYWORDS):
        return "CM"
    if "td" in lower:
        return "TD"
    if "tp" in lower:
        return "TP"
    if any(kw in lower for kw in _EXAM_KEYWORDS):
        return "Examen"
    if any(kw in lower for kw in _CORRECTION_KEYWORDS):
        return "Corrige"
    return "Document"


def load_all_documents() -> list:
    """Walk COURSES_DIR and load every supported file into LangChain documents."""
    docs: list = []
    for root, _, files in os.walk(COURSES_DIR):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(root, filename)
            subject = get_subject(filepath)
            doc_type = get_doc_type(filename)
            print(f"  [{subject}] {filename}")

            try:
                if ext == ".pdf":
                    loaded = PyPDFLoader(filepath).load()
                else:
                    loaded = TextLoader(filepath, encoding="utf-8").load()

                for doc in loaded:
                    # Strip near-empty lines to reduce noise
                    lines = [
                        line
                        for line in doc.page_content.split("\n")
                        if len(line.strip()) > MIN_LINE_LENGTH
                    ]
                    doc.page_content = "\n".join(lines)
                    doc.metadata.update(
                        matiere=subject,
                        doc_type=doc_type,
                        filename=filename,
                    )

                docs.extend(
                    doc for doc in loaded
                    if len(doc.page_content.strip()) > MIN_PAGE_LENGTH
                )
            except Exception as exc:
                print(f"  [ERREUR] {filename}: {exc}")

    return docs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full indexation pipeline."""
    print("=" * 55)
    print("Indexation RAG - Master 1 Informatique")
    print("=" * 55)

    # 1. Load raw documents
    print("\nChargement des documents...")
    documents = load_all_documents()
    print(f"  {len(documents)} pages chargees")
    if not documents:
        sys.exit("Aucun document trouve.")

    # 2. Split into chunks
    print(f"\nDecoupage en chunks ({CHUNK_SIZE} car.)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"  {len(chunks)} chunks")

    # 3. Embed and index in batches
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )

    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nIndexation ({total_batches} batches de {BATCH_SIZE})...")

    vectorstore = None
    for offset in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[offset : offset + BATCH_SIZE]
        batch_num = offset // BATCH_SIZE + 1

        for attempt in range(MAX_RETRIES):
            try:
                if vectorstore is None:
                    vectorstore = Chroma.from_documents(
                        batch,
                        embeddings,
                        persist_directory=str(CHROMA_DIR),
                    )
                else:
                    vectorstore.add_documents(batch)
                print(f"   [OK] batch {batch_num}/{total_batches}")
                break
            except Exception:
                wait = min(2 ** attempt * 5, 120)
                print(f"   [WAIT] rate-limit batch {batch_num}, retry in {wait}s")
                time.sleep(wait)
        else:
            print(f"   [FAIL] batch {batch_num}")

        time.sleep(1)

    # 4. Summary
    print("\nPar matiere :")
    subject_counts = Counter(ch.metadata["matiere"] for ch in chunks)
    for subject, count in sorted(subject_counts.items()):
        print(f"   - {subject}: {count}")

    print(f"\nBase vectorielle prete dans {CHROMA_DIR}/")
    print("   streamlit run app.py")


if __name__ == "__main__":
    main()
