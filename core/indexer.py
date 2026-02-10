"""
Indexer -- Ingest Master 1 course documents into a ChromaDB vector store.

Supports PDF, TXT and CSV files.  Handles large volumes through batch
embedding with automatic retry on rate-limit errors.
Incremental reindexing with MD5 hash tracking.
"""

import os
import sys
import time
import shutil
import hashlib
import fnmatch
from pathlib import Path
from collections import Counter

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from core.config import (
    OPENAI_API_KEY,
    CONFIG,
    COURSES_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    BATCH_SIZE,
    MAX_RETRIES,
    MIN_PAGE_LENGTH,
    MIN_LINE_LENGTH,
    SUPPORTED_EXTENSIONS,
    EXCLUDED_PATTERNS,
    SUBJECT_NAMES,
    EMBEDDING_MODEL,
)
from core.constants import (
    META_MATIERE,
    META_DOC_TYPE,
    META_FILENAME,
    META_FILEPATH,
    META_FILE_HASH,
    DOC_TYPE_CM,
    DOC_TYPE_TD,
    DOC_TYPE_TP,
    DOC_TYPE_EXAM,
    DOC_TYPE_CORRECTION,
    CM_KEYWORDS,
    EXAM_KEYWORDS,
    CORRECTION_KEYWORDS,
    DEFAULT_DOC_TYPE,
    FILE_HASH_CHUNK_SIZE,
)

# ---------------------------------------------------------------------------
# Startup check
# ---------------------------------------------------------------------------

if not OPENAI_API_KEY:
    sys.exit("Cle API OpenAI introuvable dans .env")

# Filename keywords -> document type classification (from constants)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_file_hash(filepath: str) -> str:
    """Compute MD5 hash of a file for change detection."""
    md5_hash = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(FILE_HASH_CHUNK_SIZE), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception:
        return ""


def should_exclude_path(filepath: str, base_dir: Path) -> bool:
    """Check if a file path matches any excluded pattern."""
    rel_path = os.path.relpath(filepath, base_dir)
    for pattern in EXCLUDED_PATTERNS:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(filepath), pattern):
            return True
    return False


def get_existing_file_hashes(vectorstore) -> dict[str, str]:
    """Retrieve all file hashes from existing ChromaDB metadata.

    Returns a dict mapping filepath -> md5_hash.
    """
    try:
        all_docs = vectorstore.get(include=["metadatas"])
        if not all_docs or not all_docs.get("metadatas"):
            return {}

        file_hashes = {}
        for meta in all_docs["metadatas"]:
            if meta and META_FILEPATH in meta and META_FILE_HASH in meta:
                file_hashes[meta[META_FILEPATH]] = meta[META_FILE_HASH]

        return file_hashes
    except Exception:
        return {}


def get_subject(filepath: str) -> str:
    """Derive the subject label from the file's position under COURSES_DIR."""
    rel = os.path.relpath(filepath, COURSES_DIR)
    folder = rel.split(os.sep)[0]
    return SUBJECT_NAMES.get(folder, folder)


def get_doc_type(filename: str) -> str:
    """Classify a document by its filename into CM, TD, TP, Examen, etc."""
    lower = filename.lower()
    if any(kw in lower for kw in CM_KEYWORDS):
        return DOC_TYPE_CM
    if "td" in lower:
        return DOC_TYPE_TD
    if "tp" in lower:
        return DOC_TYPE_TP
    if any(kw in lower for kw in EXAM_KEYWORDS):
        return DOC_TYPE_EXAM
    if any(kw in lower for kw in CORRECTION_KEYWORDS):
        return DOC_TYPE_CORRECTION
    return DEFAULT_DOC_TYPE


def load_all_documents(
    incremental: bool = False,
    existing_hashes: dict | None = None,
) -> tuple[list, set[str], set[str]]:
    """Walk COURSES_DIR and load every supported file into LangChain documents.

    Args:
        incremental: If True, only load modified/new files.
        existing_hashes: Dict mapping filepath -> md5_hash from existing index.

    Returns:
        Tuple of (documents, filepaths_processed, filepaths_all_current)
    """
    if existing_hashes is None:
        existing_hashes = {}

    docs: list = []
    filepaths_processed: set[str] = set()
    filepaths_all_current: set[str] = set()
    
    total_files = 0
    skipped_files = 0

    for root, _, files in os.walk(COURSES_DIR):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            total_files += 1
            filepath = os.path.join(root, filename)

            if should_exclude_path(filepath, COURSES_DIR):
                skipped_files += 1
                continue

            filepaths_all_current.add(filepath)

            current_hash = compute_file_hash(filepath)
            if not current_hash:
                continue

            if incremental and filepath in existing_hashes:
                if existing_hashes[filepath] == current_hash:
                    continue
                else:
                    print(f"  [MODIFIE] {filename}")

            subject = get_subject(filepath)
            doc_type = get_doc_type(filename)

            if not incremental:
                print(f"  [{subject}] {filename}")
            elif filepath not in existing_hashes:
                print(f"  [NOUVEAU] {filename}")

            try:
                if ext == ".pdf":
                    loaded = PyPDFLoader(filepath).load()
                else:
                    loaded = TextLoader(filepath, encoding="utf-8").load()

                for doc in loaded:
                    lines = [
                        line
                        for line in doc.page_content.split("\n")
                        if len(line.strip()) > MIN_LINE_LENGTH
                    ]
                    doc.page_content = "\n".join(lines)
                    doc.metadata.update({
                        META_MATIERE: subject,
                        META_DOC_TYPE: doc_type,
                        META_FILENAME: filename,
                        META_FILEPATH: filepath,
                        META_FILE_HASH: current_hash,
                    })

                docs.extend(
                    doc for doc in loaded
                    if len(doc.page_content.strip()) > MIN_PAGE_LENGTH
                )
                filepaths_processed.add(filepath)
            except Exception as exc:
                print(f"  [ERREUR] {filename}: {exc}")

    if total_files > 0:
        print(f"  Total de fichiers trouves: {total_files}, Exclus: {skipped_files}, Charges: {len(filepaths_processed)}")
    
    return docs, filepaths_processed, filepaths_all_current


# ---------------------------------------------------------------------------
# Delete helpers
# ---------------------------------------------------------------------------


def delete_documents_by_filepath(vectorstore, filepaths: set[str]) -> int:
    """Delete all documents matching the given filepaths from ChromaDB."""
    if not filepaths:
        return 0
    try:
        all_docs = vectorstore.get(include=["metadatas"])
        if not all_docs or not all_docs.get("ids"):
            return 0

        ids_to_delete = []
        for doc_id, meta in zip(all_docs["ids"], all_docs["metadatas"]):
            if meta and meta.get(META_FILEPATH) in filepaths:
                ids_to_delete.append(doc_id)

        if ids_to_delete:
            vectorstore.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        return 0
    except Exception as exc:
        print(f"  [ERREUR] Suppression: {exc}")
        return 0


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def main(incremental: bool = False, force_full: bool = False) -> None:
    """Run the full indexation pipeline."""
    print("=" * 55)
    print("Indexation RAG - Master 1 Informatique")
    print("=" * 55)

    index_exists = CHROMA_DIR.exists()

    if force_full and index_exists:
        print("\nSuppression de l'index existant (mode --force)...")
        shutil.rmtree(CHROMA_DIR)
        index_exists = False
        incremental = False

    if incremental and not index_exists:
        print("\nPas d'index existant, indexation complete...")
        incremental = False

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    existing_hashes = {}
    vectorstore = None

    if incremental:
        print("\nChargement de l'index existant...")
        try:
            vectorstore = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=embeddings,
            )
            existing_hashes = get_existing_file_hashes(vectorstore)
            print(f"  {len(existing_hashes)} fichiers indexes actuellement")
        except Exception as exc:
            print(f"  [ERREUR] Impossible de charger l'index: {exc}")
            print("  Indexation complete forcee...")
            incremental = False

    print("\nChargement des documents...")
    documents, processed_paths, current_paths = load_all_documents(
        incremental=incremental,
        existing_hashes=existing_hashes,
    )
    print(f"  {len(documents)} pages chargees")

    if not documents and not incremental:
        sys.exit("Aucun document trouve.")

    if incremental and existing_hashes:
        deleted_paths = set(existing_hashes.keys()) - current_paths
        if deleted_paths:
            print(f"\n{len(deleted_paths)} fichiers supprimes detectes:")
            for path in sorted(deleted_paths):
                print(f"  - {os.path.basename(path)}")
            deleted_count = delete_documents_by_filepath(vectorstore, deleted_paths)
            print(f"  {deleted_count} chunks supprimes")

    if incremental and not documents:
        print("\nAucune modification detectee. Index a jour.")
        return

    print(f"\nDecoupage en chunks ({CHUNK_SIZE} car.)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"  {len(chunks)} chunks")

    if incremental and processed_paths:
        print(f"\nSuppression des anciens chunks pour {len(processed_paths)} fichiers modifies...")
        deleted_count = delete_documents_by_filepath(vectorstore, processed_paths)
        print(f"  {deleted_count} chunks supprimes")

    if not incremental or not index_exists:
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR)
        vectorstore = None

    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nIndexation ({total_batches} batches de {BATCH_SIZE})...")

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

    print("\nPar matiere :")
    try:
        all_docs = vectorstore.get(include=["metadatas"])
        if all_docs and all_docs.get("metadatas"):
            subject_counts = Counter(
                meta.get(META_MATIERE, DEFAULT_DOC_TYPE)
                for meta in all_docs["metadatas"]
                if meta
            )
            for subject, count in sorted(subject_counts.items()):
                print(f"   - {subject}: {count}")
    except Exception:
        subject_counts = Counter(ch.metadata[META_MATIERE] for ch in chunks)
        for subject, count in sorted(subject_counts.items()):
            print(f"   - {subject}: {count}")

    mode_str = "incrementale" if incremental else "complete"
    print(f"\nIndexation {mode_str} terminee dans {CHROMA_DIR}/")
    print("   streamlit run app.py")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Indexation RAG Master 1")
    parser.add_argument("--incremental", "-i", action="store_true")
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--watch", "-w", action="store_true")
    args = parser.parse_args()

    if args.watch:
        from core.watcher import watch_and_reindex
        watch_and_reindex()
    else:
        main(incremental=args.incremental, force_full=args.force)
