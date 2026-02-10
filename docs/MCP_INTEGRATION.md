# Integration MCP -- Assistant Personnel Yani

Ce document recense les serveurs MCP (Model Context Protocol) prevus pour
construire un assistant personnel complet, multi-sources et multi-capacites.

Le module **Revision / RAG Master 1** est une des facettes de cet assistant.
D'autres modules viendront s'ajouter (productivite, communication, creation, etc.)
au travers d'une interface web interactive et modulaire.

---

## Vision globale

L'objectif final est un **bot personnel unique** qui centralise :

- Les revisions et l'aide aux cours (RAG Master 1 -- module actuel)
- La gestion des mails et communications
- Le controle du terminal et de l'environnement de dev
- La creation visuelle (Canva, diagrammes, schemas)
- L'organisation quotidienne (calendrier, taches, notes)
- La recherche et la veille (web, arxiv, wikipedia)
- L'execution de code et les TPs interactifs
- La memoire persistante et la personnalisation

Chaque module sera accessible via une **interface web interactive** avec des
sections dediees selon le besoin du moment.

---

## Architecture proposee

```
┌─────────────────────────────────────────────────────────────────┐
│              Interface Web Interactive (modules)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Revision │ │  Mails   │ │ Terminal │ │  Canva   │  ...      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    v                           v
┌─────────────┐         ┌──────────────────┐
│   LLM API   │         │  Copilot SDK     │
│  (OpenAI)   │         │  (outils visuels)│
└──────┬──────┘         └────────┬─────────┘
       │                         │
       v                         v
┌──────────────────────────────────────────┐
│         Couche d'integration MCP         │
├──────────────────────────────────────────┤
│  - Acquisition de contenu                │
│  - Recherche externe                     │
│  - Traitement d'images / Canva           │
│  - Execution de code / Terminal          │
│  - Organisation / Productivite           │
│  - Communication (mail, discord)         │
│  - Memoire persistante                   │
└──────────────────────────────────────────┘
       │
       v
┌──────────────────────────────────────────┐
│     Base vectorielle ChromaDB            │
│  (cours indexes + sources externes)      │
└──────────────────────────────────────────┘
```


---

## Modules de l'assistant

### Module 1 : Revision (actuel)

Le RAG Master 1 actuel. Recherche dans les cours indexes, generation de quiz,
fiches de revision, explications de concepts.

**MCP associes :** youtube-transcript, notion, google-drive, browser, filesystem

---

### Module 2 : Mail

Acces complet aux mails : lire, envoyer, trier, resumer, repondre automatiquement.

**MCP associes :** gmail / email

**Fonctionnalites prevues :**
- Lire et resumer les mails non lus
- Rediger des reponses assistees par l'IA
- Trier et classifier automatiquement
- Envoyer des fiches de revision ou rappels par mail
- Rechercher dans l'historique des mails

---

### Module 3 : Terminal

Controle du terminal local : executer des commandes, gerer l'environnement de dev,
automatiser des taches systeme.

**MCP associes :** terminal, code-interpreter, docker

**Fonctionnalites prevues :**
- Executer des commandes shell via le bot
- Lancer et surveiller des processus
- Automatiser des taches repetitives (build, deploy, backup)
- Debugger en interactif
- Gerer les conteneurs Docker

---

### Module 4 : Canva / Creation visuelle

Creation et edition de visuels, schemas, diagrammes, presentations.

**MCP associes :** canva, dalle / image-generation, vision / gpt-4-vision

**Fonctionnalites prevues :**
- Generer des schemas explicatifs et diagrammes
- Creer des presentations et visuels
- Analyser et decrire des images/schemas existants
- Editer des designs Canva via MCP

---

### Module 5 : Recherche & Veille

Recherche web, articles academiques, definitions, veille technologique.

**MCP associes :** brave-search / tavily, exa, arxiv, semantic-scholar, wikipedia

**Fonctionnalites prevues :**
- Completer les reponses quand le cours ne suffit pas
- Trouver des articles de recherche recents
- Definitions rapides via Wikipedia
- Recherche semantique sur le web
- Veille sur des sujets specifiques

---

### Module 6 : Code & Execution

Executer du code, generer des notebooks, tester des solutions.

**MCP associes :** code-interpreter, jupyter, docker

**Fonctionnalites prevues :**
- Executer du code Python/Java/C++ directement
- Generer des notebooks Jupyter interactifs
- Tester les solutions aux exercices
- Execution securisee dans des conteneurs Docker

---

### Module 7 : Organisation & Productivite

Calendrier, taches, planning de revision, rappels.

**MCP associes :** google-calendar, todoist / linear

**Fonctionnalites prevues :**
- Planifier des sessions de revision
- Generer des checklists de revision
- Recevoir des rappels avant les examens
- Suivre la progression par matiere

---

### Module 8 : Communication & Collaboration

Partage avec le groupe d'etude, notifications, collaboration.

**MCP associes :** discord, slack

**Fonctionnalites prevues :**
- Partager des reponses dans un canal de groupe
- Creer une base de connaissances partagee
- Notifications et alertes

---

### Module 9 : Memoire & Personnalisation

Retenir les preferences, l'historique, la progression entre les sessions.

**MCP associes :** memory, sqlite / postgres

**Fonctionnalites prevues :**
- Adapter le niveau de detail selon l'utilisateur
- Retenir les sujets deja maitrises
- Suivre les scores aux quiz et identifier les points faibles
- Historique complet des interactions

---

### Module 10 : Media & OCR

Traitement d'images, OCR, text-to-speech.

**MCP associes :** vision / gpt-4-vision, ocr (tesseract), tts

**Fonctionnalites prevues :**
- Lire et decrire des diagrammes UML, graphes, schemas
- Extraire du texte depuis des photos de tableau ou notes manuscrites
- Convertir les reponses en audio pour reviser en ecoutant

---

## Serveurs MCP detailles

### 1. Acquisition de contenu

| MCP | Utilite |
|-----|---------|
| **youtube-transcript** | Transcrire les cours video YouTube et les indexer |
| **notion** | Connecter les notes personnelles Notion comme source |
| **google-drive / onedrive** | Acceder aux documents partages (slides, annales) |
| **browser / puppeteer** | Scraper les pages de cours en ligne (Moodle, sites de profs) |
| **filesystem** | Indexer des fichiers locaux hors du dossier Master1/ |

### 2. Recherche et veille

| MCP | Utilite |
|-----|---------|
| **brave-search / tavily** | Completer les reponses RAG avec des sources web |
| **exa** | Recherche semantique sur le web (articles par sens) |
| **arxiv** | Articles de recherche (IA, algo, systemes distribues) |
| **semantic-scholar** | Citations et resumes structures de papers |
| **wikipedia** | Definitions et concepts fondamentaux |

### 3. Images et media

| MCP | Utilite |
|-----|---------|
| **vision / gpt-4-vision** | Lire et decrire schemas, diagrammes, graphes |
| **ocr (tesseract)** | Extraire du texte depuis images/notes manuscrites |
| **dalle / image-generation** | Generer des schemas explicatifs et diagrammes |
| **tts** | Convertir les reponses en audio |
| **canva** | Creation et edition de visuels |

### 4. Code et execution

| MCP | Utilite |
|-----|---------|
| **code-interpreter** | Executer du code Python/Java directement |
| **docker** | Execution dans un environnement isole |
| **jupyter** | Notebooks interactifs pour les TPs |
| **terminal** | Acces direct au shell |

### 5. Organisation

| MCP | Utilite |
|-----|---------|
| **google-calendar** | Planning de revision et rappels |
| **todoist / linear** | Taches et checklists |

### 6. Communication

| MCP | Utilite |
|-----|---------|
| **gmail / email** | Gestion complete des mails |
| **discord** | Partage collaboratif avec le groupe |
| **slack** | Communication d'equipe |

### 7. Memoire et donnees

| MCP | Utilite |
|-----|---------|
| **memory** | Preferences et personnalisation persistantes |
| **sqlite / postgres** | Historique, scores, progression |
| **qdrant / pinecone** | Alternative/complement vectoriel a ChromaDB |

### 8. Git et versioning

| MCP | Utilite |
|-----|---------|
| **github** | Acces aux repos de code (TPs, projets) |
| **gitkraken** | Gestion Git avancee (deja installe) |

---

## Plan d'implementation progressif (checklist detaillee)

### Phase 1 -- Fondations (en cours)
- [x] **RAG Master 1** -- module de revision stable et utilisable
       - [x] API/serveur fonctionnel (demarrage, config, erreurs gerees)
       - [x] pipeline RAG complet (index -> retrieval -> generation)
       - [x] interface minimale (questions, fiches, quiz)
       - [x] evaluation basique (jeu de questions + score)
- [x] **filesystem** -- indexation locale fiable
       - [x] scan des dossiers cibles + exclusions (build, cache)
       - [x] decoupage en chunks + embeddings + stockage
       - [x] reindexation et mise a jour des sources
       - [x] configuration simple des chemins
       - [x] Configuration externalisee (config.yaml)
       - [x] Reindexation incrementale avec hachage MD5
       - [x] Detection automatique des modifications/suppressions
       - [x] Mode surveillance (watch mode) pour reindexation auto
       - [x] Suite de tests complete (unitaires + integration)

---

### Phase 2 -- Acquisition de contenu
- [ ] **youtube-transcript** -- ingestion des cours video
       - [ ] recuperation des transcripts + nettoyage
       - [ ] indexation dans ChromaDB
- [ ] **notion** -- connexion des notes personnelles
       - [ ] auth + sync des pages
       - [ ] mapping titres/tags -> cours
- [ ] **google-drive** -- synchronisation des documents partages
       - [ ] import des PDF/Slides
       - [ ] extraction texte + indexation

**Impact :** Doubler la base de connaissances

---

### Phase 3 -- Outils personnels
- [ ] **gmail** -- gestion des mails
       - [ ] lecture/summary des non lus
       - [ ] redaction assistee
- [ ] **terminal** -- controle du shell
       - [ ] execution securisee de commandes
       - [ ] suivi des processus longs
- [ ] **canva** -- creation visuelle
       - [ ] generation de visuels simples
       - [ ] export et stockage des assets

**Impact :** L'assistant devient un vrai compagnon quotidien

---

### Phase 4 -- Recherche externe
- [ ] **brave-search / tavily** -- enrichissement web
       - [ ] sources citees dans les reponses
- [ ] **arxiv** -- references academiques
       - [ ] recuperation des abstracts + meta
- [ ] **wikipedia** -- definitions rapides
       - [ ] resume court + liens utiles

**Impact :** Repondre aux questions hors programme

---

### Phase 5 -- Vision et media
- [ ] **vision** -- analyse d'images et schemas
       - [ ] description + extraction d'elements cles
- [ ] **ocr** -- indexation de notes manuscrites
       - [ ] extraction texte + nettoyage
- [ ] **dalle** -- generation de schemas
       - [ ] templates d'explication reutilisables
- [ ] **tts** -- audio pour revision
       - [ ] export mp3 des fiches

**Impact :** Exploiter le contenu visuel et audio

---

### Phase 6 -- Code et execution
- [ ] **code-interpreter** -- execution d'exemples
       - [ ] sandbox securisee
- [ ] **jupyter** -- notebooks interactifs
       - [ ] generation de notebooks a partir d'exos
- [ ] **docker** -- isolation
       - [ ] images de base pretes

**Impact :** Rendre les exemples interactifs

---

### Phase 7 -- Organisation
- [ ] **google-calendar** -- planning
       - [ ] creation de sessions de revision
- [ ] **todoist** -- taches et suivi
       - [ ] checklists par matiere
- [ ] **sqlite** -- analytics et progression
       - [ ] suivi des scores + courbes simples

**Impact :** Suivi de progression et personnalisation

---

### Phase 8 -- Communaute (optionnel)
- [ ] **discord** -- partage collaboratif
       - [ ] publication de fiches/quiz
- [ ] **github** -- indexer les repos de code
       - [ ] ingestion README + code
- [ ] **slack** -- communication d'equipe
       - [ ] notifications et resumes

**Impact :** Collaboration et partage

---

### Phase 9 -- Interface web interactive
- [ ] design modulaire (sections par module)
- [ ] dashboard principal (acces rapide)
- [ ] personnalisation par contexte (revision, dev, veille)

**Impact :** Experience utilisateur complete et fluide

---

## Checklist de creation des MCP

**Outils personnels (priorite haute) :**
- [ ] gmail / email
- [ ] terminal
- [ ] canva

**Acquisition de contenu :**
- [ ] youtube-transcript
- [ ] notion
- [ ] google-drive
- [ ] browser / puppeteer
- [ ] filesystem

**Recherche et veille :**
- [ ] brave-search ou tavily
- [ ] exa
- [ ] arxiv
- [ ] semantic-scholar
- [ ] wikipedia

**Images et media :**
- [ ] vision / gpt-4-vision
- [ ] ocr
- [ ] dalle
- [ ] tts

**Code et execution :**
- [ ] code-interpreter
- [ ] docker
- [ ] jupyter

**Organisation :**
- [ ] google-calendar
- [ ] todoist

**Communication :**
- [ ] discord
- [ ] slack

**Memoire et donnees :**
- [ ] memory
- [ ] sqlite
- [ ] qdrant

**Git :**
- [ ] github

**Interface :**
- [X] Interface web modulaire

---

## Ressources

- [MCP Documentation](https://modelcontextprotocol.io)
- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [LangChain Integrations](https://python.langchain.com/docs/integrations)

---

**Note :** Le code d'implementation sera ajoute au fur et a mesure de la
creation de chaque MCP. Ce document sert de roadmap et de vision globale.
Commencer par les outils personnels (gmail, terminal, canva) en parallele
du module revision deja en place.


