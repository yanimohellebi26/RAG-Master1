# Guide d'utilisation - RAG Master 1

## Nouvelles fonctionnalités (Phase 1)

### 1. Configuration externalisée

La configuration est maintenant centralisée dans `config.yaml` :

```yaml
courses_dir: ./Master1
chroma_dir: ./chroma_db
chunk_size: 3000
chunk_overlap: 400
```

Modifiez ce fichier pour adapter les chemins et paramètres sans toucher au code.

---

### 2. Réindexation incrémentale

**Problème résolu :** Avant, réindexer = tout reconstruire (lent).

**Solution :** Détection des modifications par hash MD5.

#### Utilisation

```bash
# Indexation complète (première fois)
python indexer.py

# Réindexation incrémentale (seulement fichiers modifiés)
python indexer.py --incremental

# Force la reconstruction complète
python indexer.py --force
```

**Avantages :**
- ⚡ Jusqu'à 10x plus rapide
-  Économie d'API calls OpenAI
-  Détecte automatiquement les fichiers ajoutés/modifiés/supprimés

---

### 3. Mode surveillance (Watch Mode)

**Réindexation automatique** quand vous modifiez un cours.

#### Activation

1. Activez dans `config.yaml` :
   ```yaml
   watch_mode:
     enabled: true
     check_interval_seconds: 60
     auto_reindex: true
   ```

2. Lancez la surveillance :
   ```bash
   python indexer.py --watch
   ```

Le système vérifie les changements toutes les 60 secondes et réindexe automatiquement.

---

### 4. Tests automatisés

Suite de tests complète pour garantir la qualité.

#### Lancer les tests

```bash
# Tous les tests
pytest test_rag.py -v

# Tests rapides uniquement (sans évaluation complète)
pytest test_rag.py -v -m "not slow"

# Test spécifique
pytest test_rag.py::TestRetrieval::test_similarity_search -v
```

#### Tests couverts

-  Indexation et stockage
-  Retrieval (similarité, MMR, filtres)
-  Améliorations RAG (rewrite, BM25, hybrid, compress)
-  Pipeline complet end-to-end
-  Système d'évaluation
-  Utilitaires (hash MD5, exclusions)

---

## Exemples d'utilisation

### Workflow typique

```bash
# 1. Première indexation
python indexer.py

# 2. Lancer l'interface
streamlit run app.py

# 3. Après modification d'un cours
python indexer.py --incremental

# Ou activer la surveillance automatique
python indexer.py --watch
```

### Vérifier l'état de l'index

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vs = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# Nombre total de chunks
all_docs = vs.get(include=["metadatas"])
print(f"Total chunks: {len(all_docs['ids'])}")

# Fichiers indexés
files = {meta.get("filename") for meta in all_docs["metadatas"] if meta}
print(f"Fichiers: {len(files)}")
```

---

## Architecture des nouveautés

```
config.yaml                # Configuration centralisée
├── courses_dir
├── chroma_dir
├── chunk_size
└── excluded_patterns

indexer.py                 # Indexation avec support incrémental
├── compute_file_hash()    # Hash MD5 des fichiers
├── get_existing_hashes()  # Récupère les hash de l'index
├── load_all_documents()   # Charge seulement les modifiés
└── main()                 # --incremental, --force, --watch

indexer_watch.py           # Mode surveillance
├── get_directory_hash()   # Snapshot du dossier
└── watch_and_reindex()    # Boucle de surveillance

test_rag.py                # Suite de tests complète
├── TestIndexation
├── TestRetrieval
├── TestRAGImprovements
├── TestFullPipeline
└── TestEvaluation
```

---

## Dépannage

### Erreur "config.yaml introuvable"

```bash
# Vérifiez que config.yaml existe à la racine du projet
ls -la config.yaml

# Si absent, copiez config.yaml.example
cp config.yaml.example config.yaml
```

### L'indexation incrémentale ne détecte pas les changements

```bash
# Forcez une réindexation complète
python indexer.py --force

# Vérifiez les patterns d'exclusion dans config.yaml
# Assurez-vous que vos fichiers ne sont pas exclus
```

### Tests échouent

```bash
# Vérifiez que la clé API OpenAI est configurée
echo $OPENAI_api_key

# Ou dans .env
cat .env | grep OPENAI_api_key

# Installez les dépendances
pip install -r requirements.txt
```

---

## Prochaines étapes (Phase 1 - suite)

- [ ] **API REST** optionnelle (Flask/FastAPI)
- [ ] **Interface de gestion** de l'index (Streamlit sidebar)
- [ ] **Logs structurés** (fichier + rotation)
- [ ] **Monitoring** (métriques d'indexation)

---

## Commandes rapides

```bash
# Indexation
python indexer.py                    # Complète
python indexer.py -i                 # Incrémentale
python indexer.py -f                 # Force rebuild
python indexer.py -w                 # Watch mode

# Tests
pytest test_rag.py -v                # Tous
pytest test_rag.py -v -m "not slow"  # Rapides
pytest test_rag.py -k "retrieval"    # Pattern

# Application
streamlit run app.py                 # Interface

# Évaluation
python evaluation.py                 # Évaluation complète
```

---

**Documentation complète :** [MCP_INTEGRATION.md](MCP_INTEGRATION.md)
