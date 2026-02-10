# RAG Master 1

Assistant pédagogique basé sur RAG pour répondre aux questions sur les
cours du Master 1 Informatique -- Université de Bourgogne.

## Fonctionnalités

### RAG Principal (OpenAI)
- **Chat conversationnel** avec historique de session sécurisé
- **Filtrage par matière** pour cibler les recherches
- **Pipeline avancé** : query rewriting, hybrid search (BM25 + semantic), re-ranking
- **Sources affichées** avec traçabilité complète
- **Évaluation automatique** avec métriques détaillées

### Copilot Tools (GitHub Copilot SDK)
Panneau d'outils complémentaires pour enrichir visuellement les réponses :
- **Quiz** -- Génération de QCM interactifs
- **Tableau** -- Tableaux récapitulatifs / comparatifs
- **Graphique** -- Visualisation en barres, lignes, aires
- **Concepts clés** -- Extraction avec niveaux d'importance
- **Flashcards** -- Cartes de révision recto-verso
- **Mind Map** -- Carte mentale structurée

##  Architecture

```
OpenAI (gpt-4o-mini)          GitHub Copilot SDK
       |                            |
   RAG principal              Outils visuels
   (reponses)             (quiz, tableaux, graphs)
       |                            |
       +------------+---------------+
            Streamlit / Flask
                    |
              ChromaDB (Vector Store)
```

OpenAI est le LLM principal pour les réponses RAG. Le SDK Copilot fournit
des outils complémentaires pour enrichir visuellement les réponses.

##  Prérequis

- Python 3.10+
- Clé API OpenAI ([obtenir une clé](https://platform.openai.com/api-keys))
- GitHub Copilot (CLI) - optionnel pour les outils visuels
- 2GB+ RAM (pour ChromaDB et embeddings)

##  Installation

### 1. Cloner et configurer l'environnement

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configuration

Copier le fichier d'exemple et configurer vos clés :

```bash
cp .env.example .env
```

Éditer `.env` et ajouter votre clé API :
# Indexation complète (première fois)
python core/indexer.py

# Indexation incrémentale (détecte les changements)
python core/indexer.py --incremental

# Forcer une réindexation complète
python core/indexer.py --force
```

### 4. Lancer l'application

**Interface Streamlit (recommandé pour démo):**

```bash
streamlit run app.py
```

Ouvrir http://localhost:8501

**API Flask + Frontend React:**

```bash
# Terminal 1: Backend Flask
python web_app.py

# Terminal 2: Frontend React (si développement)
├── core/                   # Modules principaux
│   ├── config.py          # Configuration centralisée
│   ├── indexer.py         # Indexation documents → ChromaDB
│   ├── retrieval.py       # Pipeline RAG amélioré
│   ├── validators.py      # Validation des entrées (NEW)
│   └── exceptions.py      # Exceptions personnalisées (NEW)
├── evaluation/            # Système d'évaluation automatique
│   └── evaluator.py       # Métriques et évaluation
├── tools/                 # Intégrations externes
│   └── copilot.py         # GitHub Copilot SDK
├── tests/                 # Tests unitaires et intégration
│   ├── conftest.py        # Fixtures pytest
│   └── test_rag.py        # Suite de tests
├── frontend/              # Interface React (optionnel)
├── app.py                 # Interface Streamlit
├── web_app.py             # API Flask + serveur
├── config.yaml            # Configuration indexation
├── requirements.txt       # Dépendances Python
├── .env.example           # Template configuration (NEW)
├── CODE_REVIEW.md         # Rapport d'audit (NEW)
├── chroma_db/             # Base vectorielle (généré)
├── eval_results/          # Résultats évaluations (généré)
└── Master1/               # Vos cours ici

##  Tests

Lancer la suite de tests :

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=core --cov=evaluation --cov=tools

# Tests spécifiques
pytest tests/test_rag.py::TestRetrieval -v
```

##  Évaluation
Évaluer la qualité du système RAG :

```bash
python -m scripts.evaluate
```

Ou depuis l'interface Streamlit : section "Évaluation du système RAG"

**Métriques calculées:**
- Faithfulness (fidélité aux sources)
- Relevance (pertinence de la réponse)
- Completeness (complétude)
- Semantic similarity (similarité sémantique)
- Keyword coverage (couverture mots-clés)

##  Configuration Avancée

### Ajuster les paramètres RAG

Éditer `config.yaml` :

```yaml
# Taille des chunks
chunk_size: 3000
chunk_overlap: 400

# Modèle d'embeddings
embedding_model: text-embedding-3-small

# Extensions supportées
supported_extensions:
  - .pdf
  - .txt
  - .csv
```

### Variables d'environnement

| Variable | Description | Requis | Défaut |
|----------|-------------|---------|---------|
| `OPENAI_API_KEY` | Clé API OpenAI | ✅ Oui | - |
| `FLASK_SECRET_KEY` | Secret Flask sessions | ⚪ Non | Auto-généré |
| `FLASK_ENV` | Environment | ⚪ Non | development |

##  Dépannage

### Erreur: "Clé API OpenAI introuvable"
 Vérifier que `.env` existe et contient `OPENAI_API_KEY`

### Erreur: "Base vectorielle introuvable"
 Lancer d'abord: `python core/indexer.py`

### Erreur: "SDK Copilot non installé"
 Optionnel. Pour l'activer: `pip install github-copilot-sdk`

### Performance lente
 Réduire `nb_sources` dans l'interface (par défaut: 10)  
 Désactiver les options avancées (rerank, compress)

##  Contribution

1. Fork le projet
2. Créer une branche: `git checkout -b feature/nouvelle-fonctionnalite`
3. Commiter: `git commit -am 'Ajout nouvelle fonctionnalité'`
4. Push: `git push origin feature/nouvelle-fonctionnalite`
5. Créer une Pull Request

**Standards:**
- Type hints obligatoires
- Docstrings pour fonctions publiques
- Tests pour nouvelles fonctionnalités
- Validation des entrées utilisateur


## Licence

MIT License - Voir [LICENSE](LICENSE) pour détails

---
## Notes

- Les cours doivent etre ranges dans le dossier `Master1/` (voir `indexer.py`).
- Les sources utilisees sont affichees a la fin de chaque reponse.
- Le panneau Copilot Tools apparait sous chaque reponse de l'assistant.
- Les resultats des outils Copilot sont conserves dans l'historique.
