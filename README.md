# 🪷 Grantha PG-OCR — PostgreSQL-Native Manuscript Pipeline

<p align="center">
  <a href="https://colab.research.google.com/github/Ashvathram/grantha-pg-ocr/blob/main/grantha_ocr.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
  </a>
</p>

An ancient Grantha manuscript OCR and search engine where **all application logic** runs entirely inside PostgreSQL via PL/Python stored procedures. 

Built for **Stack Unknown — The Obscure Tech Hackathon** by GDG on Campus SASTRA.

> "The Database IS the Application."

## ⚡ Fastest Path to a Running Demo

```bash
git clone https://github.com/Ashvathram/grantha-pg-ocr && cd grantha-pg-ocr
python client.py demo
```

> **Requires:** Python ≥ 3.10 — the local demo uses only the standard library, no `pip install` needed.

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

### Run the CLI tool
```bash
# Full end-to-end demo (recommended for first run)
python client.py demo

# Or run individual commands:
python client.py ingest-dir samples/
python client.py search dharma
python client.py fuzzy dharma
python client.py similar "righteousness"
python client.py translate 1
python client.py list
python client.py stats
python client.py reset
```

> **Note:** `client.py` uses `local_demo_engine.py` (SQLite) under the hood to simulate the PL/Python PostgreSQL environment. The true production code is in the Colab notebook.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

### About the Developer
Ashvathram B — Final-year B.Tech CSE student at SASTRA University.

