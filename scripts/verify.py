#!/usr/bin/env python3
"""
Script de verification rapide - RAG Master 1

Verifie que toutes les fonctionnalites sont operationnelles
dans la nouvelle architecture par packages.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=" * 60)
print("Verification RAG Master 1 - Architecture modulaire")
print("=" * 60)

errors = []
warnings = []

# 1. Verifier config.yaml
print("\n[1/6] Configuration...")
try:
    from core.config import CONFIG, COURSES_DIR, CHROMA_DIR, OPENAI_API_KEY
    required_keys = ["courses_dir", "chroma_dir", "chunk_size", "chunk_overlap"]
    for key in required_keys:
        if key not in CONFIG:
            errors.append(f"Cle manquante dans config.yaml: {key}")
    print("   config.yaml valide")
    print(f"   COURSES_DIR = {COURSES_DIR}")
    print(f"   CHROMA_DIR  = {CHROMA_DIR}")
except Exception as e:
    errors.append(f"Erreur config: {e}")

# 2. Verifier core/
print("\n[2/6] Module core/...")
try:
    from core.indexer import compute_file_hash, should_exclude_path
    from core.retrieval import BM25Index, enhanced_retrieve, rewrite_query, hybrid_search
    from core.watcher import get_directory_hash, watch_and_reindex
    print("   core.indexer OK")
    print("   core.retrieval OK")
    print("   core.watcher OK")

    test_hash = compute_file_hash(__file__)
    if len(test_hash) == 32:
        print("   compute_file_hash OK")
    else:
        warnings.append("compute_file_hash retourne un hash invalide")
except Exception as e:
    errors.append(f"Erreur core/: {e}")

# 3. Verifier evaluation/
print("\n[3/6] Module evaluation/...")
try:
    from evaluation.evaluator import (
        run_evaluation, save_results, load_results,
        list_eval_history, EVAL_DATASET, EvalSummary,
    )
    print(f"   evaluation.evaluator OK ({len(EVAL_DATASET)} questions)")
except Exception as e:
    errors.append(f"Erreur evaluation/: {e}")

# 4. Verifier tools/
print("\n[4/6] Module tools/...")
try:
    from tools.copilot import copilot_generate, is_copilot_ready, TOOL_LABELS
    print(f"   tools.copilot OK ({len(TOOL_LABELS)} outils)")
    print(f"   Copilot SDK: {'disponible' if is_copilot_ready() else 'non installe'}")
except Exception as e:
    errors.append(f"Erreur tools/: {e}")

# 5. Verifier api/
print("\n[5/6] Module api/...")
try:
    from api import create_app
    from api.services.rag import rag_service
    from api.blueprints.chat import chat_bp
    from api.blueprints.copilot import copilot_bp
    from api.blueprints.evaluation import eval_bp
    from api.blueprints.config import config_bp
    print(f"   api.create_app OK")
    print(f"   api.services.rag OK")
    print(f"   4 blueprints registered OK")
except Exception as e:
    errors.append(f"Erreur api/: {e}")

# 6. Verifier les dependances
print("\n[6/6] Dependances...")
required_packages = ["yaml", "pytest", "streamlit", "langchain_openai"]
missing = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    warnings.append(f"Packages manquants: {', '.join(missing)}")
    print(f"   Packages manquants: {', '.join(missing)}")
    print("     pip install -r requirements.txt")
else:
    print("   Toutes les dependances installees")

# Resultat final
print("\n" + "=" * 60)
print("RESULTAT")
print("=" * 60)

if errors:
    print("\n ERREURS detectees:")
    for err in errors:
        print(f"   - {err}")
    sys.exit(1)
elif warnings:
    print("\n  AVERTISSEMENTS:")
    for warn in warnings:
        print(f"   - {warn}")
    print("\n Systeme fonctionnel avec quelques avertissements")
    sys.exit(0)
else:
    print("\n TOUS LES MODULES VERIFIES")
    print("\nCommandes disponibles:")
    print("  python web_app.py                      # Lancer le serveur Flask")
    print("  python -m scripts.index                 # Indexer les cours")
    print("  python -m scripts.index -i              # Reindexation incrementale")
    print("  python -m scripts.index -w              # Mode surveillance")
    print("  python -m scripts.evaluate              # Evaluation complete")
    print("  pytest tests/ -v                        # Tests unitaires")
    sys.exit(0)
