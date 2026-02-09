# RAG Master 1

Assistant pedagogique base sur RAG pour repondre aux questions sur les cours du Master 1 Informatique université de Bourgogne (j'ai pas pu recupérer toutes les ressources pédagogique ).

## Fonctionnalites

- Chat conversationnel avec historique
- Filtrage par matiere
- Sources affichees a la fin de chaque reponse
- Indexation locale des documents (PDF, TXT, CSV)

## Installation rapide

Prerequis : Python 3.10+ et une cle API OpenAI.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Creer le fichier .env :

```ini
OPENAI_api_key=sk-xxxxxxxxxxxxxxxxxxxx
```

## Utilisation

Indexer les documents :

```bash
python indexer.py
```

Lancer l'application :

```bash
streamlit run app.py
```

## Structure

```
RAG-M1/
├── app.py
├── indexer.py
├── requirements.txt
├── .env
└── chroma_db/
```

## Notes

- Les cours doivent etre ranges dans le dossier Master1/ (voir indexer.py).
- Les sources utilisees sont affichees a la fin de chaque reponse.

## Licence

MIT
