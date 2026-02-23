# RAG Master 1

Assistant pedagogique base sur RAG pour repondre aux questions sur les
cours du Master 1 Informatique -- Universite de Bourgogne.

## Fonctionnalites

### RAG Principal (OpenAI)
- **Chat conversationnel** avec historique de session securise
- **Filtrage par matiere** pour cibler les recherches
- **Pipeline avance** : query rewriting, hybrid search (BM25 + semantic), re-ranking
- **Sources affichees** avec tracabilite complete
- **Evaluation automatique** avec metriques detaillees

### Copilot Tools (GitHub Copilot SDK)
Panneau d'outils complementaires pour enrichir visuellement les reponses :
- **Quiz** -- Generation de QCM interactifs
- **Tableau** -- Tableaux recapitulatifs / comparatifs
- **Graphique** -- Visualisation en barres, lignes, aires
- **Concepts cles** -- Extraction avec niveaux d'importance
- **Flashcards** -- Cartes de revision recto-verso
- **Mind Map** -- Carte mentale structuree

### Serveurs MCP
Integration de serveurs MCP (Model Context Protocol) pour etendre les capacites :
- **YouTube Transcript** -- Indexation de cours video YouTube
- **Gmail, Google Drive, Notion** -- Acquisition de contenu (prevu)
- **Brave Search, Arxiv, Wikipedia** -- Recherche externe (prevu)
- Voir `docs/MCP_INTEGRATION.md` pour la roadmap complete

## Architecture

```
OpenAI (gpt-4o-mini)          GitHub Copilot SDK
       |                            |
   RAG principal              Outils visuels
   (reponses)             (quiz, tableaux, graphs)
       |                            |
       +------------+---------------+
                    |
          Flask API + React Frontend
                    |
        +----------+----------+
        |                     |
   ChromaDB              Serveurs MCP
  (Vector Store)      (YouTube, Gmail, ...)
```

## Prerequis

- Python 3.10+
- Node.js 18+ (pour le frontend React)
- Cle API OpenAI ([obtenir une cle](https://platform.openai.com/api-keys))
- GitHub Copilot (CLI) -- optionnel pour les outils visuels
- 2GB+ RAM (pour ChromaDB et embeddings)

## Installation

### 1. Cloner et configurer l'environnement

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
```

Editer `.env` et ajouter votre cle API :

```
OPENAI_API_KEY=sk-...
```

### 3. Indexer les cours

Placer vos documents (PDF, TXT, CSV) dans `Master1/` en sous-dossiers par matiere.

```bash
# Indexation complete (premiere fois)
python core/indexer.py

# Indexation incrementale (detecte les changements)
python core/indexer.py --incremental

# Forcer une reindexation complete
python core/indexer.py --force
```

### 4. Lancer l'application

**API Flask + Frontend React :**

```bash
# Terminal 1 : Backend Flask
python web_app.py

# Terminal 2 : Frontend React
cd frontend && npm install && npm run dev
```

Ouvrir http://localhost:5173

**Interface Streamlit (demo) :**

```bash
streamlit run app.py
```

Ouvrir http://localhost:8501

## Structure du projet

```
core/                  # Modules principaux
├── config.py          # Configuration centralisee
├── indexer.py         # Indexation documents -> ChromaDB
├── retrieval.py       # Pipeline RAG ameliore
├── validators.py      # Validation des entrees
└── exceptions.py      # Exceptions personnalisees
api/                   # Endpoints Flask (blueprints)
evaluation/            # Systeme d'evaluation automatique
├── evaluator.py       # Metriques et evaluation
tools/                 # Integrations externes
├── copilot.py         # GitHub Copilot SDK
mcp/                   # Serveurs MCP
├── base.py            # Classe de base MCP
├── registry.py        # Registre des serveurs
└── discovery.py       # Decouverte automatique
tests/                 # Tests unitaires et integration
frontend/              # Interface React (Vite)
scripts/               # Scripts utilitaires
docs/                  # Documentation du projet
config.yaml            # Configuration indexation & MCP
web_app.py             # Serveur Flask
app.py                 # Interface Streamlit
```

## Tests

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=core --cov=evaluation --cov=tools

# Tests specifiques
pytest tests/test_rag.py::TestRetrieval -v
```

## Evaluation

```bash
python -m scripts.evaluate
```

Ou depuis l'interface Streamlit : section "Evaluation du systeme RAG"

**Metriques calculees :**
- Faithfulness (fidelite aux sources)
- Relevance (pertinence de la reponse)
- Completeness (completude)
- Semantic similarity (similarite semantique)
- Keyword coverage (couverture mots-cles)

## Configuration avancee

### Parametres RAG (`config.yaml`)

```yaml
chunk_size: 3000
chunk_overlap: 400
embedding_model: text-embedding-3-small
supported_extensions: [.pdf, .txt, .csv]
```

### Serveurs MCP (`config.yaml`)

```yaml
mcp:
  youtube-transcript:
    enabled: true
    default_language: fr
  brave-search:
    enabled: false
    # api_key: ""
```

### Variables d'environnement

| Variable | Description | Requis | Defaut |
|----------|-------------|--------|--------|
| `OPENAI_API_KEY` | Cle API OpenAI | Oui | - |
| `FLASK_SECRET_KEY` | Secret Flask sessions | Non | Auto-genere |
| `FLASK_ENV` | Environnement | Non | development |

## Depannage

| Erreur | Solution |
|--------|----------|
| "Cle API OpenAI introuvable" | Verifier que `.env` contient `OPENAI_API_KEY` |
| "Base vectorielle introuvable" | Lancer `python core/indexer.py` |
| "SDK Copilot non installe" | Optionnel : `pip install github-copilot-sdk` |
| Performance lente | Reduire `nb_sources`, desactiver rerank/compress |

## Documentation

- `docs/DESCRIPTION.md` -- Description detaillee du projet et du pipeline
- `docs/MCP_INTEGRATION.md` -- Roadmap des integrations MCP et vision globale
- `docs/USAGE_GUIDE.md` -- Guide d'utilisation

## Licence

MIT License -- Voir [LICENSE](LICENSE) pour details
