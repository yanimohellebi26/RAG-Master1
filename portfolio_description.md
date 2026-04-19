# Assistant Pédagogique RAG — Master 1 Informatique

## En une phrase
Une application web full-stack qui transforme des documents de cours en assistant intelligent : l'étudiant pose une question en langage naturel, le système retrouve les passages pertinents dans ses propres cours et génère une réponse sourcée, en temps réel.

---

## Le problème résolu
Les étudiants en Master 1 Informatique (Université de Bourgogne) jonglent avec des dizaines de documents sur 10+ matières (Algo, IA, Cloud, SGBD, Systèmes Distribués, Génie Logiciel…). Trouver une notion précise dans cette masse est long. Ce projet offre un moteur de Q&R directement ancré dans leurs supports officiels — sans hallucination, sources citées.

---

## Fonctionnalités

### Chat RAG avancé
- **Streaming SSE** — les tokens arrivent en temps réel dans l'interface, comme ChatGPT
- **Réécriture de requête automatique** — le LLM reformule et enrichit la question avant la recherche (synonymes, acronymes, termes techniques)
- **Recherche hybride** — fusion BM25 (keyword) + sémantique avec algorithme **RRF** (Reciprocal Rank Fusion)
- **Re-ranking** — l'LLM re-juge la pertinence des passages récupérés
- **Compression contextuelle** — filtre les passages hors sujet avant génération
- **MMR (Maximal Marginal Relevance)** — diversifie les sources pour éviter la redondance
- **Filtrage par matière** — recherche ciblée sur un ou plusieurs cours
- **Historique conversationnel** — contexte maintenu côté serveur sur toute la session
- **Détection d'intention vidéo** — si l'utilisateur demande une vidéo, le pipeline RAG est court-circuité vers la recherche YouTube

### Outils visuels (GitHub Copilot SDK)
Depuis n'importe quelle réponse, panneau latéral pour générer en un clic :
- Quiz QCM interactifs
- Tableaux récapitulatifs / comparatifs
- Graphiques (barres, lignes, aires)
- Extraction de concepts clés avec niveaux d'importance
- Flashcards recto-verso
- Mind maps structurées

### Page YouTube
- Coller un lien → extraction de la transcription + **résumé / analyse IA en streaming**
- **Indexation dans ChromaDB** — le contenu d'une vidéo devient interrogeable dans le chat
- Historique des vidéos indexées avec suppression

### Page Gmail
- Lecture des mails non lus avec **résumé LLM automatique**
- **Auto-classification** des mails par catégories personnalisables (JSON)
- **Rédaction assistée** — l'LLM propose un brouillon de réponse contextuelle
- Envoi directement depuis l'interface

### Page Google Drive
- Acquisition et indexation de documents Drive dans la base vectorielle

### Dashboard d'évaluation
- **Auto-évaluation** sur un dataset de 50+ questions/réponses de référence (ground truth par matière)
- **7 métriques** : Faithfulness, Relevance, Completeness, Semantic Similarity, Keyword Coverage, Subject Match, Keyword Hit
- Score global pondéré configurable
- **LLM-as-judge** pour les métriques qualitatives
- Historique des évaluations avec comparaison dans le temps

---

## Architecture

```
React + Vite (SPA multi-pages)
        │  SSE streaming
        ▼
Flask API REST (blueprints par domaine)
        │
   ┌────┴──────────────┐
   │                   │
OpenAI             GitHub Copilot SDK
gpt-4o-mini         (outils visuels)
   │
LangChain
(query rewriting → hybrid BM25+semantic → RRF → re-rank → compress → MMR)
   │
ChromaDB (vector store persistant)
   │
APIs tierces + Serveurs MCP
(YouTube, Gmail, Google Drive, Notion, Brave Search, Arxiv…)
```

---

## Stack technique

| Couche | Technologies |
|---|---|
| **Frontend** | React 18, Vite, CSS modules, marked + DOMPurify |
| **Backend** | Python 3.10, Flask, Flask Blueprints, SSE streaming |
| **LLM & Embeddings** | OpenAI GPT-4o-mini, text-embedding-3-small |
| **Orchestration RAG** | LangChain — query rewriting, BM25, recherche sémantique, RRF, re-ranking, MMR, compression |
| **Base vectorielle** | ChromaDB (persistance locale) |
| **Outils visuels** | GitHub Copilot SDK |
| **Intégrations** | Gmail API, Google Drive API, YouTube Transcript API |
| **Extensions** | Serveurs MCP configurables (YouTube, Gmail, Drive, Notion, Brave Search, Arxiv, Wikipedia) |
| **Évaluation** | Pipeline custom, LLM-as-judge, 7 métriques pondérées |
| **Tests** | pytest + coverage |

---

## Ce qui le distingue d'un chatbot classique

| Chatbot classique | Ce projet |
|---|---|
| Répond depuis la connaissance du LLM | Répond **uniquement** depuis les cours indexés |
| Peut halluciner | Sources citées, traçabilité complète |
| Recherche vectorielle simple | Hybride BM25 + sémantique + RRF + re-ranking + MMR |
| Interface basique | SPA React avec 5 pages fonctionnelles |
| Pas d'évaluation | Pipeline de 7 métriques avec historique |
| Non extensible | Architecture MCP — nouvelles sources sans toucher au cœur |

---

## Compétences démontrées
- Pipeline RAG avancé de A à Z (pas juste un wrapper LangChain)
- Streaming SSE Flask → React (tokens en temps réel)
- Intégration APIs tierces : OpenAI, Gmail, Google Drive, YouTube
- Architecture modulaire : Flask Blueprints + React pages + MCP servers
- LLM-as-judge et évaluation quantitative de systèmes LLM
- Frontend React complet (Context API, hooks, routing, markdown sécurisé)
