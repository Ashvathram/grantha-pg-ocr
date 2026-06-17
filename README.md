# 🪷 Grantha PG-OCR — PostgreSQL-Native Manuscript Pipeline

<p align="center">
  <a href="https://colab.research.google.com/github/Ashvathram/grantha-pg-ocr/blob/main/grantha_ocr.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
  </a>
</p>

An ancient Grantha manuscript OCR and search engine where **all application logic** runs entirely inside PostgreSQL via PL/Python stored procedures. 

Built for **Stack Unknown — The Obscure Tech Hackathon** by GDG on Campus SASTRA.

> "The Database IS the Application."

## The Obscure Stack

Instead of building a typical web backend (Flask/FastAPI/Node) that connects to a database, this project flips the architecture: the database *is* the backend.

| Concept | Technology |
|---|---|
| **Application Runtime** | PostgreSQL 14 |
| **Logic Layer** | PL/Python (`plpython3u`) Stored Procedures |
| **Vector Search** | pgvector — 768-d cosine similarity (`<=>`) |
| **Fuzzy Search** | pg_trgm — Trigram similarity (`%`) |
| **OCR Engine** | Kraken CRNN+CTC — called from inside Postgres |
| **AI Translation** | Gemini 2.0 Flash — called from inside Postgres |
| **Frontend** | `psql` (or any PostgreSQL client) |

## The Primary Deliverable: `grantha_ocr.ipynb`

The production version of this pipeline is designed to run on Google Colab (fulfilling the Google Technology requirement). 

Open `grantha_ocr.ipynb` to see the complete implementation:
- 6 PL/Python stored procedures
- `pgvector` and `pg_trgm` integration
- Kraken OCR and Gemini API integration inside PostgreSQL
- Sophisticated Gemini Prompting Strategy

### Architecture — SQL Is The API

```text
psql (the "frontend")
  |
  |-- SELECT * FROM ingest_manuscript('/path/to/image.jpg');
  |-- SELECT * FROM search_manuscripts('dharma');
  |-- SELECT * FROM fuzzy_search('karma', 0.1);
  |-- SELECT * FROM similar_manuscripts(1, 3);
  |-- SELECT * FROM translate_manuscript(1);
  |-- SELECT * FROM search_and_translate('dharma');
  |
  +-- PostgreSQL 14 [PL/Python + pgvector + pg_trgm]
       |-- Kraken OCR (subprocess from PL/Python)
       |-- Gemini 2.0 Flash (HTTP API from PL/Python)
       +-- pgvector (768-d cosine distance embeddings)
```

### Prompting Strategy

The Gemini API is integrated directly into the `translate_manuscript` stored procedure. We use a highly specific prompt designed for ancient Grantha manuscripts:
- **Context:** Instructs the model about OCR extraction from palm-leaf manuscripts.
- **Error Awareness:** Explicitly tells the model to look out for common Grantha OCR glyph confusions (ta/na, pa/ya).
- **Multi-task Extraction:** Returns structured JSON containing IAST transliteration, Devanagari conversion, scholarly English translation, source identification, and paleographic notes.

---

## Local Demo Mode

If you don't have PostgreSQL or WSL installed locally, a simulated mock backend is provided for easy testing on Windows.

### 1. Install local dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run the CLI tool
```bash
# Ingest sample manuscripts
python client.py ingest-dir samples/

# Full-text exact search
python client.py search dharma

# Fuzzy search (simulating pg_trgm)
python client.py fuzzy dharma

# Vector similarity search (simulating pgvector)
python client.py similar "righteousness"

# View all records
python client.py list
```

> **Note:** `client.py` uses `local_demo_engine.py` (SQLite) under the hood to simulate the PL/Python PostgreSQL environment. The true production code is in the Colab notebook.

---

### About the Developer
Ashvathram B — Final-year B.Tech CSE student at SASTRA University.
Inspired by the TATTVA project (Grantha manuscript OCR under JSPS/ICSSR funding with the University of Tokyo).
