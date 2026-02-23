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

## Avantage cle : GitHub Copilot SDK

Ce projet utilise le **SDK GitHub Copilot** comme couche d'integration
supplementaire. C'est un **avantage majeur** qui permet :

- **Acces direct aux outils Copilot** depuis l'interface web (completions,
  suggestions, generation de code)
- **Bridge entre le LLM et les MCP** -- le Copilot SDK orchestre les appels
  aux serveurs MCP et gere le contexte de facon transparente
- **Extensibilite** -- on peut enregistrer nos MCP comme des "tools" Copilot
  et les invoquer depuis n'importe quel contexte (chat, editor, terminal)
- **Integration native avec GitHub** -- issues, PRs, repos, code search
  sans configuration supplementaire
- **Agent mode** -- possibilite de deleguer des taches complexes a un agent
  Copilot qui utilise nos MCP en autonomie

Le Copilot SDK est le "chef d'orchestre" qui connecte le LLM, les MCP natifs,
les automations Rube/Composio, et les APIs directes dans un pipeline unifie.

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
│  (OpenAI)   │         │  (GitHub)        │
└──────┬──────┘         └────────┬─────────┘
       │                         │
       └─────────┬───────────────┘
                 v
┌──────────────────────────────────────────┐
│         Couche d'integration MCP         │
├──────────────────────────────────────────┤
│  - Acquisition de contenu                │
│  - Recherche externe                     │
│  - Traitement de documents (docx, pdf...)│
│  - Traitement d'images / Canva           │
│  - Execution de code / Terminal          │
│  - Organisation / Productivite           │
│  - Communication (mail, discord, social) │
│  - Memoire persistante                   │
│  - Rube/Composio (78+ apps SaaS)        │
│  - Skills (awesome-claude-skills)        │
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

- [X] **youtube-transcript** -- ingestion des cours video
       - [X] recuperation des transcripts + nettoyage
       - [X] indexation dans ChromaDB
- [X] **notion** -- connexion des notes personnelles
       - [X] auth + sync des pages
       - [X] mapping titres/tags -> cours
       - [X] ajouter un bouton dans outils copilot pour demander d'enregistrer une synthese en notion de ce chat avec les ressources pour reprendre
- [X]**google-drive** -- synchronisation des documents partages
       - [X] import des PDF/Slides
       - [X] extraction texte + indexation

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

---

# Etape 2 -- Integration Rube MCP (Composio) : Automatisations SaaS

## Contexte

Le repo [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
recense des skills d'automatisation pour 78+ apps SaaS via **Rube MCP (Composio)**.
Chaque skill fournit des sequences d'outils pretes, des guides de parametres,
et des references aux vrais slugs de l'API Composio.

L'idee est d'integrer ces automatisations dans notre couche MCP existante pour
connecter l'assistant a des services reels (Gmail, Google Calendar, Drive, etc.)
sans reinventer la roue.

Notre usage du **GitHub Copilot SDK** est un avantage cle : il sert de couche
d'orchestration qui peut invoquer les MCP natifs ET les automations Rube de
facon transparente, avec gestion du contexte et des outils.

---

## Catalogue complet des Skills disponibles (awesome-claude-skills)

Voici le catalogue exhaustif des skills que l'on peut integrer, classes par
categorie. Chaque skill peut etre adapte en MCP serveur ou utilise directement
via le Copilot SDK.

### Document Processing

| Skill | Description | Application pour nous |
|---|---|---|
| **docx** | Creer, editer, analyser des docs Word avec suivi des modifications | Generer des fiches de revision en .docx, rapports de projet |
| **pdf** | Extraire texte, tableaux, metadata, fusionner et annoter des PDFs | Indexer les cours PDF dans ChromaDB, annoter les annales |
| **pptx** | Lire, generer, ajuster des slides et templates | Creer des presentations de revision, importer les slides profs |
| **xlsx** | Manipulation de spreadsheets : formules, graphiques, transformations | Analyser les donnees de progression, exporter les stats |
| **Markdown to EPUB** | Convertir du markdown en ebook EPUB professionnel | Transformer les fiches de revision en ebook portable |

### Development & Code Tools

| Skill | Description | Application pour nous |
|---|---|---|
| **artifacts-builder** | Creer des artefacts HTML avec React, Tailwind, shadcn/ui | Ameliorer les composants de notre interface web |
| **Changelog Generator** | Generer des changelogs user-facing depuis les commits git | Documenter automatiquement les evolutions du projet |
| **D3.js Visualization** | Produire des graphiques D3 et visualisations interactives | Visualiser la progression, les stats de quiz |
| **MCP Builder** | Guide de creation de serveurs MCP de qualite (Python/TypeScript) | Accelerer la creation de nos propres serveurs MCP |
| **Playwright Browser Automation** | Automatiser les tests web avec Playwright | Tester notre interface frontend automatiquement |
| **prompt-engineering** | Techniques de prompt engineering et bonnes pratiques | Ameliorer les prompts du RAG pour des reponses plus precises |
| **software-architecture** | Clean Architecture, SOLID, design patterns | Structurer le code du projet proprement |
| **test-driven-development** | TDD : ecrire les tests avant le code | Maintenir la qualite du code a mesure qu'on ajoute des features |
| **Webapp Testing** | Tester les apps web locales avec Playwright | Verifier le frontend, debugger le UI, screenshots |
| **Connect** | Connecter a n'importe quelle app (Gmail, Slack, GitHub, Notion, 1000+) | Point d'entree universel pour toutes les integrations |
| **LangSmith Fetch** | Debugger les agents LangChain/LangGraph via LangSmith | Observer et debugger notre pipeline RAG |
| **using-git-worktrees** | Git worktrees isoles avec selection intelligente | Developper en parallele sur plusieurs features |
| **subagent-driven-development** | Dispatcher des sous-agents independants | Paralleliser le dev avec des checkpoints de review |

### Data & Analysis

| Skill | Description | Application pour nous |
|---|---|---|
| **CSV Data Summarizer** | Analyser des fichiers CSV avec visualisations auto | Analyser `eval_results/*.csv`, stats de progression |
| **deep-research** | Recherche multi-etapes autonome (Gemini Deep Research) | Approfondir un sujet quand le cours ne suffit pas |
| **postgres** | Requetes SQL read-only sur PostgreSQL | Analyser l'historique des interactions, stats avancees |
| **root-cause-tracing** | Tracer la cause racine d'erreurs profondes | Debugger les problemes dans le pipeline RAG |

### Communication & Writing

| Skill | Description | Application pour nous |
|---|---|---|
| **article-extractor** | Extraire le texte complet d'articles web | Enrichir la base de connaissances avec des articles |
| **brainstorming** | Transformer des idees brutes en designs structures | Planifier les features, explorer les alternatives |
| **Content Research Writer** | Rediger du contenu avec recherche et citations | Aide a la redaction de rapports/memoires |
| **Meeting Insights Analyzer** | Analyser des transcripts de reunions | Analyser les reunions de groupe de projet |
| **NotebookLM Integration** | Chat avec NotebookLM pour des reponses source-grounded | Completer le RAG avec des reponses basees sur les docs |
| **Twitter Algorithm Optimizer** | Optimiser les tweets pour maximiser la portee | Publier des contenus engageants sur les reseaux |

### Creative & Media

| Skill | Description | Application pour nous |
|---|---|---|
| **Canvas Design** | Creer des visuels en PNG/PDF avec design esthetique | Posters, affiches, visuels de revision |
| **imagen** | Generer des images via Google Gemini | Mockups UI, icones, illustrations |
| **Image Enhancer** | Ameliorer la qualite des images et screenshots | Presentations et documentation pro |
| **Theme Factory** | Appliquer des themes pro (fonts, couleurs) aux artefacts | Themer notre interface, slides, rapports |
| **Video Downloader** | Telecharger des videos YouTube et autres plateformes | Sauvegarder les cours video en local |
| **youtube-transcript** | Recuperer et resumer les transcripts YouTube | Deja implemente -- notre premier MCP |

### Productivity & Organization

| Skill | Description | Application pour nous |
|---|---|---|
| **File Organizer** | Organiser fichiers/dossiers intelligemment, trouver les doublons | Ranger le dossier `Master1/` automatiquement |
| **Invoice Organizer** | Organiser factures et recus pour les impots | Gestion administrative personnelle |
| **Tailored Resume Generator** | CV adapte a partir d'une offre d'emploi | Creer des CV pour les stages M2 |
| **tapestry** | Relier et resumer des documents en reseaux de connaissances | Creer des cartes mentales entre les cours |
| **kaizen** | Amelioration continue (philosophie Kaizen/Lean) | Ameliorer le projet de facon iterative |
| **n8n-skills** | Comprendre et operer des workflows n8n | Automatiser des pipelines complexes |

### Collaboration & Project Management

| Skill | Description | Application pour nous |
|---|---|---|
| **git-pushing** | Automatiser les operations git | Simplifier le workflow git du projet |
| **google-workspace-skills** | Suite Google Workspace (Gmail, Calendar, Docs, Sheets, Drive) | Integration complete Google en un package |
| **review-implementing** | Evaluer les plans d'implementation et aligner aux specs | Review de code avant merge |
| **test-fixing** | Detecter les tests echoues et proposer des correctifs | Maintenir la suite de tests fonctionnelle |

### Security & Systems

| Skill | Description | Application pour nous |
|---|---|---|
| **metadata-extraction** | Extraire et analyser les metadonnees de fichiers | Indexer les metadonnees des documents |
| **computer-forensics** | Analyse forensique numerique | Securite et analyse de fichiers |

---

## Catalogue complet des Automations Rube MCP (Composio)

Skills pre-built pour 78+ apps SaaS. Chaque skill contient des sequences
d'outils, des guides de parametres, et des references aux vrais slugs API.

### CRM & Sales

| Automation | Description |
|---|---|
| **Close** | Leads, contacts, opportunites, activites, pipelines |
| **HubSpot** | Contacts, deals, companies, tickets, email engagement |
| **Pipedrive** | Deals, contacts, organisations, activites, pipelines |
| **Salesforce** | Objects, records, SOQL queries, operations bulk |
| **Zoho CRM** | Leads, contacts, deals, comptes, modules |

### Project Management

| Automation | Description |
|---|---|
| **Asana** | Taches, projets, sections, assignations, workspaces |
| **Basecamp** | To-do lists, messages, personnes, groupes, projets |
| **ClickUp** | Taches, listes, espaces, objectifs, time tracking |
| **Jira** | Issues, projets, boards, sprints, JQL queries |
| **Linear** | Issues, projets, cycles, equipes, workflows |
| **Monday.com** | Boards, items, colonnes, groupes, workspaces |
| **Notion** | Pages, databases, blocs, commentaires, recherche |
| **Todoist** | Taches, projets, sections, labels, filtres |
| **Trello** | Boards, cartes, listes, membres, checklists |
| **Wrike** | Taches, dossiers, projets, commentaires, workflows |

### Communication

| Automation | Description |
|---|---|
| **Discord** | Messages, channels, serveurs, roles, reactions |
| **Intercom** | Conversations, contacts, companies, tickets, articles |
| **Microsoft Teams** | Messages, channels, equipes, chats, meetings |
| **Slack** | Messages, channels, recherche, reactions, threads, scheduling |
| **Telegram** | Messages, chats, media, groupes, bots |
| **WhatsApp** | Messages, media, templates, groupes, profils business |

### Email

| Automation | Description |
|---|---|
| **Gmail** | Envoyer/repondre, rechercher, labels, brouillons, pieces jointes |
| **Outlook** | Emails, dossiers, contacts, integration calendrier |
| **Postmark** | Emails transactionnels, templates, serveurs, stats de livraison |
| **SendGrid** | Emails, templates, contacts, listes, stats campagnes |

### Code & DevOps

| Automation | Description |
|---|---|
| **Bitbucket** | Repos, PRs, branches, issues, workspaces |
| **CircleCI** | Pipelines, workflows, jobs, configuration projet |
| **Datadog** | Monitors, dashboards, metriques, incidents, alertes |
| **GitHub** | Issues, PRs, repos, branches, actions, code search |
| **GitLab** | Issues, MRs, projets, pipelines, branches |
| **PagerDuty** | Incidents, services, schedules, escalation, on-call |
| **Render** | Services, deploys, gestion de projets |
| **Sentry** | Issues, events, projets, releases, alertes |
| **Supabase** | SQL queries, schemas de tables, edge functions, storage |
| **Vercel** | Deployments, projets, domaines, env variables, logs |

### Storage & Files

| Automation | Description |
|---|---|
| **Box** | Fichiers, dossiers, recherche, partage, collaborations, signature |
| **Dropbox** | Fichiers, dossiers, recherche, partage, operations batch |
| **Google Drive** | Upload, download, recherche, partage, organisation |
| **OneDrive** | Fichiers, dossiers, recherche, partage, permissions, versioning |

### Spreadsheets & Databases

| Automation | Description |
|---|---|
| **Airtable** | Records, tables, bases, vues, gestion de champs |
| **Coda** | Docs, tables, lignes, formules, automations |
| **Google Sheets** | Lecture/ecriture cellules, formatage, formules, operations batch |

### Calendar & Scheduling

| Automation | Description |
|---|---|
| **Cal.com** | Types d'evenements, reservations, disponibilite, planning |
| **Calendly** | Evenements, invites, types, liens de planning, disponibilite |
| **Google Calendar** | Evenements, participants, libre/occupe, recurrence |
| **Outlook Calendar** | Evenements, participants, rappels, recurrence |

### Social Media

| Automation | Description |
|---|---|
| **Instagram** | Posts, stories, commentaires, media, insights business |
| **LinkedIn** | Posts, profils, entreprises, images, commentaires |
| **Reddit** | Posts, commentaires, subreddits, vote, moderation |
| **TikTok** | Upload videos, requetes, gestion createur |
| **Twitter/X** | Tweets, recherche, utilisateurs, listes, engagement |
| **YouTube** | Videos, chaines, playlists, commentaires, abonnements |

### Marketing & Email Marketing

| Automation | Description |
|---|---|
| **ActiveCampaign** | Contacts, deals, campagnes, listes, automations |
| **Brevo** | Contacts, campagnes email, emails transactionnels, listes |
| **ConvertKit** | Abonnes, tags, sequences, broadcasts, formulaires |
| **Klaviyo** | Profils, listes, segments, campagnes, evenements |
| **Mailchimp** | Audiences, campagnes, templates, segments, rapports |

### Support & Helpdesk

| Automation | Description |
|---|---|
| **Freshdesk** | Tickets, contacts, agents, groupes, reponses types |
| **Freshservice** | Tickets, assets, changes, problemes, catalogue de services |
| **Help Scout** | Conversations, clients, mailboxes, tags |
| **Zendesk** | Tickets, utilisateurs, organisations, recherche, macros |

### E-commerce & Payments

| Automation | Description |
|---|---|
| **Shopify** | Produits, commandes, clients, inventaire, GraphQL |
| **Square** | Paiements, clients, catalogue, commandes, locations |
| **Stripe** | Charges, clients, produits, abonnements, remboursements |

### Design & Collaboration

| Automation | Description |
|---|---|
| **Canva** | Designs, templates, assets, dossiers, brand kits |
| **Confluence** | Pages, espaces, recherche, CQL, labels, versions |
| **DocuSign** | Enveloppes, templates, signature, gestion de documents |
| **Figma** | Fichiers, composants, commentaires, projets, equipes |
| **Miro** | Boards, sticky notes, formes, connecteurs, items |
| **Webflow** | Collections CMS, items, sites, publication, assets |

### Analytics & Data

| Automation | Description |
|---|---|
| **Amplitude** | Events, cohortes, proprietes utilisateur, requetes |
| **Google Analytics** | Rapports, dimensions, metriques, gestion de proprietes |
| **Mixpanel** | Events, funnels, cohortes, annotations, JQL |
| **PostHog** | Events, personnes, feature flags, insights, annotations |
| **Segment** | Sources, destinations, tracking, connexions warehouse |

### HR & People

| Automation | Description |
|---|---|
| **BambooHR** | Employes, conges, rapports, annuaire |

### Automation Platforms

| Automation | Description |
|---|---|
| **Make (Integromat)** | Scenarios, connexions, gestion d'execution |

### Zoom & Meetings

| Automation | Description |
|---|---|
| **Zoom** | Meetings, enregistrements, participants, webinars, rapports |

---

## Integrations Rube prioritaires pour l'assistant etudiant

### Priorite 1 -- Impact direct sur les revisions

| Skill Rube/Composio | Stub existant | Valeur ajoutee |
|---|---|---|
| **Gmail Automation** | `personal/gmail.py` | Lire les mails de la fac, resumer les annonces, envoyer des fiches par mail |
| **Google Calendar Automation** | `organization/google_calendar.py` | Planifier les sessions de revision, rappels avant examens |
| **Google Drive Automation** | `content/google_drive.py` | Importer slides/PDFs partages par les profs, indexer dans ChromaDB |
| **Notion Automation** | `content/notion.py` | Sync des notes perso, sauvegarder les syntheses de chat |
| **GitHub Automation** | `git/github.py` | Indexer les repos de TPs, recuperer du code de cours |

### Priorite 2 -- Enrichir les capacites

| Skill Rube/Composio | Stub existant | Valeur ajoutee |
|---|---|---|
| **Google Sheets Automation** | a creer | Suivi notes/scores de quiz, courbes de progression |
| **Todoist Automation** | `organization/todoist.py` | Checklists de revision par matiere, suivi des taches |
| **Discord Automation** | `communication/discord.py` | Partager fiches/quiz dans un canal d'etude |
| **Telegram Automation** | a creer | Rappels de revision sur telephone |

### Priorite 3 -- Skills non-Composio pertinents

| Skill (awesome-claude-skills) | Application |
|---|---|
| **CSV Data Summarizer** | Analyse auto des fichiers `eval_results/*.csv` |
| **File Organizer** | Ranger/restructurer le dossier `Master1/` automatiquement |
| **Video Downloader** | Sauvegarder les cours video YouTube en local |
| **Content Research Writer** | Aide a la redaction de rapports/memoires avec sources |
| **Deep Research** | Approfondir un sujet quand le cours ne suffit pas |
| **Tailored Resume Generator** | Creer un CV pour les stages M2 |
| **Webapp Testing (Playwright)** | Tester le frontend de l'assistant automatiquement |

---

## Plan d'implementation Rube

### Etape 2.1 -- Setup Composio
- [ ] Creer un compte sur [platform.composio.dev](https://platform.composio.dev)
- [ ] Obtenir la cle API Composio
- [ ] Ajouter `composio-core` aux dependances (`requirements.txt`)
- [ ] Configurer l'auth dans `config.yaml` sous `mcp: composio:`
- [ ] Tester la connexion de base

### Etape 2.2 -- Gmail via Rube
- [ ] Connecter le compte Gmail via OAuth Composio
- [ ] Implementer `personal/gmail.py` : lire, resumer, envoyer
- [ ] Ajouter endpoint `/api/mcp/gmail` dans l'API
- [ ] Ajouter une section "Mails" dans le frontend
- [ ] Tests d'integration

### Etape 2.3 -- Google Calendar via Rube
- [ ] Connecter Google Calendar via OAuth
- [ ] Implementer `organization/google_calendar.py` : creer, lister, rappels
- [ ] Ajouter section "Planning" dans le frontend
- [ ] Generer automatiquement un planning de revision

### Etape 2.4 -- Google Drive via Rube
- [ ] Connecter Google Drive via OAuth
- [ ] Implementer `content/google_drive.py` : lister, telecharger, indexer
- [ ] Pipeline auto : Drive -> extraction texte -> ChromaDB
- [ ] Ajouter section "Documents" dans le frontend

### Etape 2.5 -- Notion via Rube
- [ ] Connecter Notion via integration API
- [ ] Implementer `content/notion.py` : lire, creer, sync pages
- [ ] Bouton "Sauvegarder cette synthese dans Notion" dans le chat
- [ ] Sync bidirectionnel notes Notion <-> RAG

### Etape 2.6 -- Discord & Collaboration via Rube
- [ ] Connecter bot Discord
- [ ] Implementer `communication/discord.py` : envoyer, ecouter, reagir
- [ ] Partage de fiches/quiz dans un canal de groupe

### Etape 2.7 -- Todoist via Rube
- [ ] Connecter Todoist via API
- [ ] Implementer `organization/todoist.py` : creer taches, lister, completer
- [ ] Generer des checklists de revision automatiquement

---

## Architecture Rube dans le projet

```
┌──────────────────────────────────────────┐
│         Interface Web (frontend)         │
│  Mails │ Planning │ Docs │ Chat │ ...    │
└────────────────┬─────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │    API Flask (blueprints)│
    │  /chat  /mcp  /eval ... │
    └────────────┬────────────┘
                 │
    ┌────────────┴────────────┐
    │    MCPRegistry          │
    │  (base.py + registry)   │
    ├─────────────────────────┤
    │  Serveurs natifs        │  Serveurs Rube/Composio
    │  - youtube-transcript   │  - gmail (OAuth)
    │  - filesystem           │  - google-calendar (OAuth)
    │  - code-interpreter     │  - google-drive (OAuth)
    │  - ...                  │  - notion (API)
    │                         │  - discord (bot)
    │                         │  - todoist (API)
    └─────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │   Composio SDK (Rube)   │
    │   Auth + Tool Execution │
    └─────────────────────────┘
```

---

# Etape 3 -- Evolution vers un assistant personnel complet

## Vision : Au-dela des revisions

L'assistant n'est plus seulement un outil de revision. Il devient un **vrai
assistant personnel complet** qui gere **tous les aspects de la vie** :
vie sociale, reservations, finances, sante, voyages, divertissement, etc.

Le RAG Master 1 reste le noyau central, mais l'assistant evolue en un
**compagnon de vie numerique** capable de tout gerer depuis une seule interface.

---

## Nouveaux domaines couverts

### 3.1 -- Vie sociale & Communication

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Gestion des contacts** | Google Contacts, Notion | Carnet d'adresses intelligent, rappels d'anniversaires |
| **WhatsApp / Telegram** | WhatsApp API, Telegram Bot | Envoyer/recevoir des messages, resumer les conversations |
| **Reseaux sociaux** | Instagram, LinkedIn, Twitter/X | Publier, programmer des posts, veille sur le fil d'actu |
| **Evenements sociaux** | Google Calendar, Eventbrite | Planifier des sorties, soirees, retrouvailles avec les potes |
| **Invitations** | Gmail, WhatsApp | Envoyer des invitations groupees, gerer les RSVP |

### 3.2 -- Reservations & Booking

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Restaurants** | Google Maps API, OpenTable | Chercher, comparer et reserver des restos |
| **Voyages** | Skyscanner API, Booking.com | Trouver les meilleurs vols et hotels |
| **Transports** | SNCF API, BlaBlaCar, Uber | Reserver des trajets, comparer les prix |
| **Activites** | Eventbrite, Google Maps | Trouver et reserver des activites (cinema, sport, concerts) |
| **Rendez-vous** | Cal.com, Calendly, Doctolib | Prendre des RDV (medecin, administratif, etc.) |

### 3.3 -- Finances & Budget

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Suivi des depenses** | Google Sheets, Notion | Tracker les depenses par categorie |
| **Factures** | Gmail + OCR | Extraire auto les montants des factures recues par mail |
| **Budget mensuel** | Google Sheets | Generer et suivre le budget du mois |
| **Rappels de paiement** | Google Calendar, Todoist | Rappeler les echeances (loyer, abonnements, etc.) |
| **Comparateur de prix** | Brave Search, web scraping | Trouver les meilleures offres avant d'acheter |

### 3.4 -- Sante & Bien-etre

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Rendez-vous medicaux** | Doctolib API, Google Calendar | Prendre et gerer les RDV medicaux |
| **Rappels medicaments** | Todoist, notifications | Rappels de prise de medicaments |
| **Suivi sport** | Google Sheets, Notion | Logger les seances, plans d'entrainement |
| **Recettes & nutrition** | Web search, Notion | Suggestions de repas equilibres, liste de courses |
| **Sommeil** | Google Calendar analytics | Analyser les habitudes de sommeil |

### 3.5 -- Productivite quotidienne

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Morning briefing** | Gmail, Calendar, Todoist, Meteo | Resume matinal : mails, agenda, taches, meteo |
| **Gestion de taches** | Todoist, Notion, Linear | Taches perso + pro au meme endroit |
| **Notes vocales** | TTS + STT | Dicter des notes, recevoir des resumes audio |
| **Rappels intelligents** | Tous les services | Rappels contextuels bases sur l'heure, le lieu, les habitudes |
| **Automatisations** | Make, n8n, IFTTT | "Si je recois un mail de X, creer une tache dans Todoist" |

### 3.6 -- Divertissement & Culture

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Recommendations** | Brave Search, YouTube, Spotify | "Quoi regarder ce soir ?", suggestions de films/series/musique |
| **Playlists** | Spotify API | Creer et gerer des playlists selon l'humeur |
| **Actualites** | RSS, Brave Search, Reddit | Resume quotidien de l'actu (tech, sport, general) |
| **Podcasts** | Spotify, YouTube transcript | Resumer les derniers episodes de podcasts suivis |
| **Lectures** | Notion, Kindle highlights | Tracker les livres lus, extraire les passages cles |

### 3.7 -- Administratif & Documents

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Stockage organise** | Google Drive, Dropbox | Classer auto les documents (factures, ID, cerfa...) |
| **Remplissage de formulaires** | OCR + LLM | Aider a remplir les formulaires administratifs |
| **Suivi des demarches** | Todoist, Notion | Tracker l'avancement des demarches (CAF, impots, mutuelle) |
| **Scan & OCR** | OCR (tesseract) | Scanner des documents papier et les indexer |
| **Modeles de courrier** | LLM + templates | Generer des lettres types (resiliation, reclamation, etc.) |

### 3.8 -- Logement & Maison

| Fonctionnalite | Services integres | Description |
|---|---|---|
| **Recherche logement** | LeBonCoin API, web scraping | Alertes sur les nouvelles annonces selon criteres |
| **Gestion colocataires** | Google Sheets, Todoist | Partage des depenses, planning menage |
| **Courses** | Todoist, Google Keep | Liste de courses intelligente basee sur les recettes |
| **Domotique** | Home Assistant API | Controle des appareils connectes (lumieres, chauffage) |

---

## Architecture cible -- Assistant complet

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Interface Web Unifiee                            │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐     │
│  │  Chat   │ │ Planning │ │ Mails  │ │Finance │ │  Social  │ ... │
│  │ (RAG)   │ │& Booking │ │        │ │        │ │          │     │
│  └─────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘     │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐     │
│  │ Sante  │ │  Admin   │ │Maison  │ │Culture │ │ Morning  │ ... │
│  │        │ │  & Docs  │ │        │ │& Loisir│ │ Briefing │     │
│  └─────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘     │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │        Moteur IA           │
              │   LLM + RAG + Memoire     │
              │   (contexte persistant)    │
              └─────────────┬─────────────┘
                            │
   ┌────────────────────────┼────────────────────────┐
   │                        │                        │
   v                        v                        v
┌──────────┐         ┌──────────────┐         ┌───────────┐
│ MCP Natifs│         │ Rube/Composio│         │  APIs     │
│ (custom) │         │ (78+ apps)   │         │ directes  │
├──────────┤         ├──────────────┤         ├───────────┤
│ youtube  │         │ gmail        │         │ meteo     │
│ filesystem│        │ calendar     │         │ SNCF      │
│ code     │         │ drive        │         │ doctolib  │
│ memory   │         │ notion       │         │ leboncoin │
│ OCR/TTS  │         │ discord      │         │ spotify   │
│ ...      │         │ todoist      │         │ ...       │
└──────────┘         │ sheets       │         └───────────┘
                     │ linkedin     │
                     │ whatsapp     │
                     │ ...          │
                     └──────────────┘
                            │
              ┌─────────────┴─────────────┐
              │   Base de connaissances    │
              │  ChromaDB + SQLite + Memory│
              │  (cours + perso + habitudes)│
              └───────────────────────────┘
```

---

## Plan d'implementation -- Etape 3

### Phase 3.A -- Fondations de l'assistant complet
- [ ] Systeme de memoire persistante (preferences, habitudes, historique)
- [ ] Morning briefing automatique (mails + agenda + taches + meteo)
- [ ] Dashboard unifie avec tous les modules
- [ ] Systeme de notifications cross-module
- [ ] Profil utilisateur configurable (centres d'interet, horaires, preferences)

### Phase 3.B -- Vie sociale
- [ ] Integration WhatsApp (envoi/reception de messages)
- [ ] Integration Telegram (bot de notifications + commandes)
- [ ] Gestion des contacts intelligente (rappels anniversaires, etc.)
- [ ] Planification d'evenements sociaux (proposer, inviter, confirmer)
- [ ] Resume hebdo des interactions sociales

### Phase 3.C -- Booking & Reservations
- [ ] Recherche et reservation de restaurants (Google Maps / OpenTable)
- [ ] Recherche de vols et hotels (Skyscanner / Booking)
- [ ] Reservation de transports (SNCF, BlaBlaCar)
- [ ] Prise de RDV medicaux (Doctolib)
- [ ] Integration Cal.com / Calendly pour les RDV pro

### Phase 3.D -- Finances
- [ ] Suivi des depenses automatique (extraction depuis mails/factures)
- [ ] Budget mensuel interactif (Google Sheets)
- [ ] Alertes de paiement et echeances
- [ ] Comparateur de prix intelligent
- [ ] Bilan financier mensuel automatique

### Phase 3.E -- Sante & Quotidien
- [ ] Rappels de medicaments et RDV medicaux
- [ ] Plans d'entrainement et suivi sport
- [ ] Suggestions de repas + liste de courses auto
- [ ] Suivi des habitudes (sommeil, sport, alimentation)

### Phase 3.F -- Admin & Documents
- [ ] Classification automatique des documents (Drive/local)
- [ ] OCR + indexation des documents papier scannes
- [ ] Assistant de remplissage de formulaires
- [ ] Generateur de courriers administratifs
- [ ] Suivi des demarches en cours

### Phase 3.G -- Divertissement
- [ ] Recommandations films/series/musique personnalisees
- [ ] Gestion des playlists Spotify
- [ ] Resume d'actu quotidien personnalise
- [ ] Suivi des podcasts et livres

### Phase 3.H -- Logement
- [ ] Alertes annonces logement (LeBonCoin, SeLoger)
- [ ] Gestion des depenses colocation
- [ ] Liste de courses intelligente
- [ ] Integration domotique (si appareils connectes)

---

## Checklist des nouvelles integrations (Etape 3)

**Vie sociale :**
- [ ] WhatsApp API
- [ ] Telegram Bot
- [ ] Google Contacts
- [ ] Eventbrite

**Booking :**
- [ ] Google Maps / Places API
- [ ] Skyscanner / Amadeus API
- [ ] SNCF Open Data API
- [ ] Doctolib (scraping ou API)
- [ ] Cal.com

**Finances :**
- [ ] Google Sheets (suivi budget)
- [ ] OCR factures (automatise)
- [ ] Alertes paiement

**Sante :**
- [ ] Doctolib integration
- [ ] Rappels meds (Todoist/notifs)
- [ ] Suivi sport (Notion/Sheets)

**Divertissement :**
- [ ] Spotify API
- [ ] RSS feeds
- [ ] Reddit API

**Admin :**
- [ ] OCR avance (tesseract + LLM)
- [ ] Templates courriers
- [ ] Google Drive classement auto

**Logement :**
- [ ] LeBonCoin scraper
- [ ] Home Assistant API

---

## Principes directeurs

1. **Un seul point d'entree** -- Tout passe par la meme interface web et le meme chat
2. **Contextuel** -- L'assistant sait qui tu es, ce que tu fais, et s'adapte
3. **Proactif** -- Il ne se contente pas de repondre, il anticipe (rappels, suggestions)
4. **Modulaire** -- Chaque domaine est un module independant, activable/desactivable
5. **Prive** -- Toutes les donnees restent locales ou sous ton controle (pas de cloud tiers non consenti)
6. **Progressif** -- On ajoute les modules un par un, sans casser l'existant

---

## Ressources

- [MCP Documentation](https://modelcontextprotocol.io)
- [GitHub Copilot SDK](https://github.com/github/copilot-sdk)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [LangChain Integrations](https://python.langchain.com/docs/integrations)
- [Composio Platform](https://platform.composio.dev)
- [Awesome Claude Skills](https://github.com/ComposioHQ/awesome-claude-skills)
- [Spotify Web API](https://developer.spotify.com/documentation/web-api)
- [SNCF Open Data](https://data.sncf.com)
- [Google APIs](https://console.cloud.google.com/apis)

---

**Note :** Le code d'implementation sera ajoute au fur et a mesure de la
creation de chaque MCP. Ce document sert de roadmap et de vision globale.

**Etape 1** = Module revision (RAG Master 1) + GitHub Copilot SDK -- FAIT
**Etape 2** = Integrations Rube/Composio + Skills (78+ apps SaaS, document processing, code tools, data analysis...) -- EN COURS
**Etape 3** = Assistant personnel complet (vie sociale, booking, finances, sante, admin, loisirs)
 idée ++ =  dans mes cours que j ai indexé ou les pdf , video que je voudrai indexé en plus parfois ya  du code je veux qu il's soit extrait ,dans la oage file avec filtre code + filtre module ça mfiche ce code dans un notebook executable

