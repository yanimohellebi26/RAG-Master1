# RAG Master 1 -- Description du projet

## Presentation

RAG Master 1 est un assistant pedagogique concu pour les etudiants du
Master 1 Informatique de l'Universite de Bourgogne. Il s'appuie sur le
paradigme **Retrieval-Augmented Generation (RAG)** : chaque reponse est
fondee sur les documents de cours reellement indexes, puis generee par un
modele de langage.

Le systeme combine deux moteurs complementaires :

- **OpenAI (gpt-4o-mini)** -- moteur principal pour les reponses textuelles,
  avec affichage des sources utilisees.
- **GitHub Copilot SDK** -- moteur secondaire pour la generation d'outils
  visuels de revision (quiz, tableaux, graphiques, concepts cles, flashcards,
  mind map).

## Pipeline

1. **Indexation** -- Les documents du dossier `Master1/` (PDF, TXT, CSV) sont
   decoupes en chunks puis vectorises dans ChromaDB via `text-embedding-3-small`.
2. **Recherche** -- A chaque question, les passages les plus pertinents sont
   retrouves par recherche MMR (Maximal Marginal Relevance).
3. **Generation** -- Le LLM produit une reponse structuree en francais, en
   s'appuyant uniquement sur le contexte recupere.
4. **Outils visuels** -- L'etudiant peut, en un clic, generer du contenu
   complementaire (quiz interactif, tableau comparatif, graphique, etc.) via
   le SDK Copilot.

## Stack technique

| Composant            | Role                                |
|----------------------|-------------------------------------|
| Streamlit            | Interface web                       |
| LangChain            | Orchestration du pipeline RAG       |
| ChromaDB             | Base vectorielle                    |
| OpenAI               | Embeddings + LLM principal          |
| GitHub Copilot SDK   | Outils visuels complementaires      |

## Utilisation rapide

```bash
python indexer.py        # indexer les cours
streamlit run app.py     # lancer l'interface
```
