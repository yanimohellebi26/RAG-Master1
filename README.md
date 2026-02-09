# RAG Master 1

Assistant pedagogique base sur RAG pour repondre aux questions sur les
cours du Master 1 Informatique -- Universite de Bourgogne.

## Fonctionnalites

- **RAG (OpenAI)** -- Chat conversationnel avec historique, filtrage par
  matiere, sources affichees.
- **Copilot Tools (GitHub Copilot SDK)** -- Panneau d'outils complementaires :
  - **Quiz** -- Generation de QCM interactifs
  - **Tableau** -- Tableaux recapitulatifs / comparatifs
  - **Graphique** -- Visualisation en barres, lignes, aires
  - **Concepts cles** -- Extraction avec niveaux d'importance
  - **Flashcards** -- Cartes de revision recto-verso
  - **Mind Map** -- Carte mentale structuree

## Architecture

```
OpenAI (gpt-4o-mini)          GitHub Copilot SDK
       |                            |
   RAG principal              Outils visuels
   (reponses)             (quiz, tableaux, graphs)
       |                            |
       +------------+---------------+
               Streamlit UI
```

OpenAI est le LLM principal pour les reponses RAG. Le SDK Copilot fournit
des outils complementaires pour enrichir visuellement les reponses.

## Installation

Prerequis : Python 3.10+, cle API OpenAI, GitHub Copilot (CLI).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Creer le fichier `.env` :

```ini
OPENAI_api_key=sk-xxxxxxxxxxxxxxxxxxxx
```

> Le SDK Copilot utilise le CLI GitHub Copilot integre a VS Code.
> Assurez-vous que GitHub Copilot est active dans votre editeur.

## Utilisation

Indexer les documents :

```bash
python indexer.py
```

Lancer l'application :

```bash
streamlit run app.py
```

## Structure du projet

```
RAG-M1/
  app.py              Interface Streamlit + panneau Copilot Tools
  copilot_client.py   Integration SDK GitHub Copilot
  indexer.py          Indexation des documents dans ChromaDB
  requirements.txt    Dependances Python
  .env                Cle API (non versionne)
  chroma_db/          Base vectorielle generee par indexer.py
  Master1/            Dossier contenant les cours par matiere
```

## Notes

- Les cours doivent etre ranges dans le dossier `Master1/` (voir `indexer.py`).
- Les sources utilisees sont affichees a la fin de chaque reponse.
- Le panneau Copilot Tools apparait sous chaque reponse de l'assistant.
- Les resultats des outils Copilot sont conserves dans l'historique.

## Licence

MIT
