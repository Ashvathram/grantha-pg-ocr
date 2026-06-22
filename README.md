# 🪷 Grantha PG-OCR

### *What if the database wasn't just where you keep stuff… but the entire app?*

<p align="center">
  <a href="https://colab.research.google.com/github/Ashvathram/grantha-pg-ocr/blob/main/grantha_ocr.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
  </a>
</p>

> Built for **Stack Unknown — The Obscure Tech Hackathon** by GDG on Campus SASTRA.

---

## 🧒 Explain Like I'm 5

Imagine you found a **really old book** written in a secret script that nobody can read anymore. It's on crumbly old leaves, not even paper.

Now imagine you took a photo of it and asked a really smart robot to:

1. 📸 **Look at the picture** and figure out what the squiggly letters say *(that's the OCR part — a robot called Kraken)*
2. 🤖 **Translate it** into English so you can actually understand it *(that's Gemini — Google's AI)*
3. 🧠 **Remember what it learned** so that when you ask "find me something about yoga," it can say "Oh! This old leaf talks about that!" *(that's vector search — pgvector)*
4. 🔍 **Still find it** even if you spell it wrong, like "yoaga" instead of "yoga" *(that's fuzzy search — pg_trgm)*

**The twist?** Most apps use a website server (like a waiter) to talk to the database (the kitchen). We **fired the waiter.** The kitchen takes your order directly. The database *is* the app.

You talk to it with SQL. That's it. No Flask. No FastAPI. No Node.js. Just SQL.

```sql
-- That's not pseudocode. That's the actual API.
SELECT * FROM ingest_manuscript('/path/to/ancient_leaf.jpg');
SELECT * FROM search_manuscripts('dharma');
SELECT * FROM fuzzy_search('yoaga', 0.1);
SELECT * FROM similar_manuscripts(1, 3);
SELECT * FROM translate_manuscript(1);
SELECT * FROM search_and_translate('karma');
```

---

## 🏗️ How It Actually Works (The Grown-Up Version)

```
                        ┌──────────────────────────────────┐
   psql / Any SQL       │       PostgreSQL 14               │
   Client               │  ┌──────────────────────────┐    │
        │                │  │  PL/Python (plpython3u)   │    │
        │  SQL call      │  │                          │    │
        ├───────────────►│  │  ┌─ Kraken OCR ──────┐   │    │
        │                │  │  │  CRNN+CTC on image │   │    │
        │                │  │  └───────┬───────────┘   │    │
        │                │  │          ▼               │    │
        │                │  │  ┌─ Gemini 2.0 Flash ┐   │    │
        │                │  │  │  Transliterate +   │   │    │
        │                │  │  │  Translate + JSON  │   │    │
        │                │  │  └───────┬───────────┘   │    │
        │                │  │          ▼               │    │
        │                │  │  ┌─ pgvector ────────┐   │    │
        │                │  │  │  768-d embedding   │   │    │
        │                │  │  │  cosine distance   │   │    │
        │                │  │  └───────────────────┘   │    │
        │                │  └──────────────────────────┘    │
        │                │                                  │
        │◄───────────────│  + pg_trgm (fuzzy/trigram)       │
       results           └──────────────────────────────────┘
```

Everything — OCR, AI translation, vector math, fuzzy matching — runs **inside a single SQL transaction.** If Gemini's API hiccups, the whole thing rolls back atomically. No half-processed data. No orphan records.

### The Obscure Stack

| Layer | Technology | Why It's Cool |
|---|---|---|
| **Runtime** | PostgreSQL 14 | It's not just storage. It's the *application server.* |
| **Logic** | PL/Python (`plpython3u`) | Full Python 3 interpreter running *inside* Postgres. Most devs don't even know this exists. |
| **OCR** | Kraken (CRNN+CTC) | Built specifically for historical scripts. Not Tesseract. |
| **AI** | Gemini 2.0 Flash | Called via HTTP *from inside a stored procedure.* The DB makes API calls. |
| **Semantic Search** | pgvector (768-d, `<=>`) | Cosine similarity over embeddings, natively in SQL. |
| **Fuzzy Search** | pg_trgm (`%`) | Handles OCR typos gracefully with trigram similarity. |
| **Frontend** | `psql` | Your terminal is the UI. No React required. |
| **Deployment** | Google Colab | Full PostgreSQL server running in the cloud for free. |

---

## ⚡ Try It Right Now

```bash
git clone https://github.com/Ashvathram/grantha-pg-ocr && cd grantha-pg-ocr
python client.py demo
```

> **That's it.** Python ≥ 3.10 + standard library only. No `pip install`. No Docker. No config files.

The demo runs through the full pipeline:

```
Step 1/6 → Ingest 4 sample manuscripts
Step 2/6 → Full-text search ("gamaya")
Step 3/6 → Fuzzy search with pg_trgm ("yoga")
Step 4/6 → Vector similarity search with pgvector ("righteousness")
Step 5/6 → Gemini AI transliteration
Step 6/6 → Database statistics
```

Want to poke around yourself?

```bash
python client.py ingest-dir samples/    # Feed it images
python client.py search dharma          # Exact search
python client.py fuzzy dharma           # Typo-tolerant search
python client.py similar "righteousness" # Semantic similarity
python client.py translate 1            # AI transliteration
python client.py list                   # See everything
python client.py stats                  # DB statistics
python client.py reset                  # Start fresh
```

> **Note:** `client.py` uses a local SQLite mock engine to simulate the PL/Python PostgreSQL environment. The real production pipeline lives in `grantha_ocr.ipynb` on Colab with a live PostgreSQL server.

---

## 🧠 The Gemini Prompting Strategy

We don't just throw text at Gemini and hope for the best. The prompt is **hand-engineered for ancient manuscript OCR:**

- **Context Injection** — Tells the model it's reading OCR output from a palm-leaf manuscript, not modern text.
- **Error-Aware** — Explicitly warns about common Grantha OCR glyph confusions (ta↔na, pa↔ya) so the model auto-corrects.
- **Multi-Task Extraction** — A single call returns structured JSON with:
  - IAST transliteration
  - Devanagari conversion
  - Scholarly English translation
  - Source text identification
  - Paleographic notes

---

## 🐘 The 7 SQL Endpoints

These aren't REST endpoints. They're **PL/Python stored procedures.** You wrote 7 Python programs. They just happen to live inside a database.

| # | SQL Function | What It Does |
|---|---|---|
| 1 | `ingest_manuscript(filepath)` | Full pipeline: Image → OCR → Gemini → Embed → INSERT |
| 2 | `search_manuscripts(query)` | ILIKE full-text search across all OCR text |
| 3 | `fuzzy_search(query, threshold)` | pg_trgm trigram similarity (survives typos) |
| 4 | `similar_manuscripts(doc_id, top_k)` | pgvector cosine distance ("philosophically similar") |
| 5 | `translate_manuscript(doc_id)` | Force re-translation via Gemini |
| 6 | `search_and_translate(query)` | Chain: find → translate in one SQL call |
| 7 | `search_by_text(query)` | English query → embedding → nearest Sanskrit match |

---

## 🤝 The Honest Engineering Note

Kraken OCR needs a **custom-trained neural network** (`.mlmodel`) for every historical script. Training one for 11th-century Grantha takes months of academic research and annotated datasets (like the TATTVA project in Tokyo). We had 48 hours.

So: the OCR pipeline is fully wired but uses mock Sanskrit output. **Everything else — Gemini translation, pgvector cosine math, pg_trgm fuzzy search, the PL/Python architecture — is 100% real and running live.** The system is production-ready; it just needs a researcher to drop in trained Grantha weights.

---

## 📁 Project Structure

```
grantha-pg-ocr/
├── grantha_ocr.ipynb        # 🎯 The real deal — Colab + PostgreSQL + live AI
├── client.py                # CLI frontend for local demo
├── local_demo_engine.py     # SQLite mock backend (simulates PL/Python + pgvector)
├── samples/                 # 4 sample manuscript images
│   ├── img1.jpg
│   ├── img2.jpg
│   ├── img3.jpg
│   └── img4.jpg
├── presentation_guide.md    # Full hackathon presentation script
├── requirements.txt         # Production deps (demo needs none)
└── LICENSE                  # MIT
```

---

## 📜 License

MIT — see [LICENSE](LICENSE).

### About the Developer

**Ashvathram B** — Final-year B.Tech CSE student at SASTRA University.
