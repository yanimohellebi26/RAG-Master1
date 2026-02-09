"""
Script d'indexation des cours du Master 1 dans ChromaDB.
Optimisé pour gérer un grand volume de PDFs avec rate limiting.
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

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_api_key")
if not OPENAI_API_KEY:
    sys.exit("Cle API OpenAI introuvable dans .env")

BASE_DIR = Path(__file__).parent
COURSES_DIR = BASE_DIR / "Master1"
CHROMA_DIR = BASE_DIR / "chroma_db"

MATIERE_NAMES = {
    "Algo": "Algorithmique",
    "AnalyseExplo": "Analyse Exploratoire de Données",
    "Cloud": "Cloud & Réseaux",
    "CWA": "Conception Web Avancée",
    "GenieLog": "Génie Logiciel",
    "IA": "Intelligence Artificielle",
    "Logique": "Logique & Prolog",
    "SGBDGraphes": "SGBD Graphes",
    "SGD": "Systèmes de Gestion de Données",
    "SystDistri": "Systèmes Distribués",
}


def get_matiere(filepath):
    rel = os.path.relpath(filepath, COURSES_DIR)
    folder = rel.split(os.sep)[0]
    return MATIERE_NAMES.get(folder, folder)


def get_doc_type(filename):
    n = filename.lower()
    if any(k in n for k in ("cm", "cours", "slide", "ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7")):
        return "CM"
    if "td" in n:
        return "TD"
    if "tp" in n:
        return "TP"
    if any(k in n for k in ("exam", "ct ", "ct_", "cc_", "annale")):
        return "Examen"
    if any(k in n for k in ("corr", "cor", "solution")):
        return "Corrigé"
    return "Document"


def load_all_documents():
    """Charge tous les PDF et TXT du dossier Master1."""
    docs = []
    for root, _, files in os.walk(COURSES_DIR):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in (".pdf", ".txt", ".csv"):
                continue
            fp = os.path.join(root, f)
            matiere = get_matiere(fp)
            dtype = get_doc_type(f)
            print(f"  [{matiere}] {f}")
            try:
                if ext == ".pdf":
                    loaded = PyPDFLoader(fp).load()
                else:
                    loaded = TextLoader(fp, encoding="utf-8").load()
                for d in loaded:
                    # Nettoyer: enlever lignes quasi-vides
                    lines = [l for l in d.page_content.split("\n") if len(l.strip()) > 3]
                    d.page_content = "\n".join(lines)
                    d.metadata.update(matiere=matiere, doc_type=dtype, filename=f)
                docs.extend(d for d in loaded if len(d.page_content.strip()) > 50)
            except Exception as e:
                print(f"  [ERREUR] {f}: {e}")
    return docs


def main():
    print("=" * 55)
    print("Indexation RAG - Master 1 Informatique")
    print("=" * 55)

    # 1) Charger
    print("\nChargement des documents...")
    documents = load_all_documents()
    print(f"→ {len(documents)} pages chargées")
    if not documents:
        sys.exit("Aucun document trouvé.")

    # 2) Découper
    print("\nDecoupage en chunks (3 000 car.)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000, chunk_overlap=400,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"→ {len(chunks)} chunks")

    # 3) Indexer par batches
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=OPENAI_API_KEY,
    )

    BATCH = 400
    total_b = (len(chunks) + BATCH - 1) // BATCH
    print(f"\nIndexation ({total_b} batches de {BATCH})...")

    vs = None
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        bn = i // BATCH + 1
        for attempt in range(6):
            try:
                if vs is None:
                    vs = Chroma.from_documents(batch, embeddings,
                                               persist_directory=str(CHROMA_DIR))
                else:
                    vs.add_documents(batch)
                print(f"   [OK] batch {bn}/{total_b}")
                break
            except Exception as e:
                w = min(2 ** attempt * 5, 120)
                print(f"   [WAIT] rate-limit batch {bn}, retry in {w}s")
                time.sleep(w)
        else:
            print(f"   [FAIL] batch {bn}")
        time.sleep(1)

    # 4) Stats
    print("\nPar matiere :")
    for m, c in sorted(Counter(ch.metadata["matiere"] for ch in chunks).items()):
        print(f"   • {m}: {c}")

    print(f"\nBase vectorielle prete dans {CHROMA_DIR}/")
    print("   → streamlit run app.py")


if __name__ == "__main__":
    main()
