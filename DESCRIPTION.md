# Description du projet RAG Master 1

RAG Master 1 est un assistant pedagogique base sur RAG pour repondre aux questions des etudiants a partir des cours du Master 1 Informatique.

## Objectif

- Faciliter la revision des cours
- Donner des reponses structurees en s'appuyant sur les sources
- Permettre la recherche par matiere

## Fonctionnement

1. Indexation des documents (PDF, TXT, CSV) dans ChromaDB
2. Recherche des passages pertinents a chaque question
3. Generation de reponse par GPT-4o-mini avec sources affichees

## Stack technique

- Streamlit (interface web)
- LangChain (pipeline RAG)
- ChromaDB (base vectorielle)
- OpenAI (embeddings + LLM)

## Utilisation rapide

```bash
python indexer.py
streamlit run app.py
```

