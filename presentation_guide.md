# 🪷 Grantha PG-OCR — Complete Hackathon Presentation Guide

This document contains **everything** you need to know, say, and demonstrate to the judges. Use this as your personal script, study guide, and project manifesto.

---

## 1. The Elevator Pitch (30 Seconds)

> "We built an ancient manuscript OCR and search engine, but instead of building a traditional web application, **we turned the database into the application.**
> 
> By using PostgreSQL with Python stored procedures (PL/Python), we run our entire AI pipeline—Kraken OCR, Gemini 2.0 Flash transliterations, vector embeddings, and fuzzy text search—natively inside the database. **There is no Flask, no FastAPI, and no Node.js.** The only API is SQL."

---

## 2. The "Obscure Tech" Hook

The hackathon's theme is **Stack Unknown / Obscure Tech**. Here is how you prove your project fits the theme perfectly.

**The Status Quo:** In 99% of modern apps, the database is just a "dumb" storage box. A web framework (like Python/Flask) reads the data, processes it, and returns it to the user.
**The Obscure Approach:** We ripped out the middleman. We enabled `plpython3u`, an obscure and highly powerful PostgreSQL extension that lets you run a full Python interpreter *inside* the database engine. 

**Why is this brilliant?**
1. **Zero Network Latency:** We don't have to pull 100,000 rows out of the database to process them in Python; the Python code goes directly to the data.
2. **Atomic AI:** An image ingestion triggers OCR, AI translation, and vector embedding generation in a single, atomic SQL transaction. If the AI fails, the whole transaction rolls back safely.

---

## 3. The Tech Stack Breakdown

Be ready to explain exactly what each piece does:

| Technology | What It Does In This Project |
| :--- | :--- |
| **PostgreSQL 14** | The core application runtime. It acts as the backend server. |
| **PL/Python (`plpython3u`)** | Runs Python 3 inside PostgreSQL. This is how we write our API endpoints as SQL functions. |
| **Google Gemini 2.0 Flash** | Called via HTTP directly from the database. It handles the transliteration of raw Grantha OCR into standard IAST, Devanagari, and English. |
| **pgvector** | A Postgres extension that generates 768-dimensional embeddings and performs cosine distance math (`<=>`) for semantic similarity search. |
| **pg_trgm** | A Postgres extension for Trigram similarity. It handles "fuzzy" searching, which is critical because ancient OCR always has typos and spelling mistakes. |
| **Kraken (CRNN+CTC)** | A specialized OCR engine built for historical and non-Latin scripts. Triggered as a subprocess from within Postgres. |
| **Google Colab** | The deployment environment. It proves that the entire Postgres server and AI pipeline can run cleanly in the cloud. |

---

## 4. The Data Pipeline (Step-by-Step)

When you run `SELECT * FROM ingest_manuscript('samples/img1.jpg');`, here is exactly what happens *inside* the database:

1. **OCR Subprocess:** The PL/Python script triggers Kraken OCR to extract raw text from the image.
2. **Gemini Transliteration:** The script takes the raw OCR text and sends a highly specific prompt to Gemini 2.0 Flash to correct OCR errors, convert it to IAST/Devanagari, and translate it to English.
3. **Vectorization:** The translated text is passed to an embedding model to generate a 768-dimensional vector representation.
4. **Insertion:** The raw text, the Gemini JSON translation, and the vector embedding are saved into the `manuscripts` table using `INSERT`.

---

## 5. How to Handle the "Mock OCR" Question

**Do not hide this.** Bring it up yourself before the judges even ask. It shows deep technical maturity and understanding of ML constraints.

**What to say:**
> *"Kraken OCR requires a custom-trained `.mlmodel` for every ancient script. Training a neural network to recognize 11th-century Grantha script takes months of research and academic funding (like the TATTVA project in Tokyo). Since we had 48 hours, we implemented the Kraken pipeline but passed a mock Sanskrit string as the output. 
> 
> However, everything else you see—the Google Gemini 2.0 translation, the JSON parsing, the pgvector cosine math, and the fuzzy searches—are **100% real and running live**. The architecture is fully production-ready; it just needs a researcher to drop in the trained Grantha weights file."*

---

## 6. The 7 API Endpoints (Stored Procedures)

You wrote 7 Python programs. They just happen to live inside the database.

1. `ingest_manuscript(filepath)`: The master pipeline (OCR → AI → Embed → Insert).
2. `search_manuscripts(query)`: Basic exact-text search using `ILIKE`.
3. `fuzzy_search(query, threshold)`: Uses `pg_trgm` to find words even if the OCR spelled them slightly wrong.
4. `similar_manuscripts(doc_id)`: Uses `pgvector` to say "find me other manuscripts that are philosophically similar to this one."
5. `translate_manuscript(doc_id)`: Forces the Gemini API to re-translate an existing document.
6. `search_and_translate(query)`: Chains two functions together: finds a text, then dynamically translates it in one SQL call.
7. `search_by_text(query)`: Takes a user's English query, converts it to a vector embedding on the fly, and finds the closest matching Sanskrit manuscript using pgvector.

---

## 7. Live Demo Presentation Script

When it's your turn to present, follow this exact flow on Google Colab:

> [!TIP]
> **Preparation:** Before the judges walk over, have the Colab notebook open. Make sure your `GEMINI_API_KEY` is in the Colab Secrets. Go to **Runtime > Run all**. Wait for it to finish so the database is populated.

**Step 1: Introduction (Show the Architecture)**
*Scroll to Cell 1.*
"We built an ancient Grantha manuscript search engine. But we didn't use Flask, FastAPI, or Node.js. The theme is obscure tech, so we built the entire backend **inside PostgreSQL** using PL/Python."

**Step 2: The Setup**
*Scroll past the setup cells quickly.*
"This notebook is currently running a live PostgreSQL 14 server with `pgvector` and `pg_trgm` installed directly on Google's cloud infrastructure."

**Step 3: The Secret Sauce (Gemini in Postgres)**
*Scroll to the Prompting Strategy section.*
"We wired the Gemini 2.0 Flash API directly into the database. When a manuscript is ingested, the database reaches out to Gemini to transliterate the text, extract paleographic notes, and flag OCR errors, returning it all as structured JSON."

**Step 4: The Ingestion Pipeline**
*Scroll to Cell 10 (Ingest Pipeline Demo).*
"Here is the ingestion. When we run `SELECT * FROM ingest_manuscript()`, the database runs Kraken OCR, calls Gemini, creates vector embeddings, and saves the record. All atomic. If the API fails, the DB transaction rolls back."
*(Explain the Mock OCR reality here using the script from Section 5).*

**Step 5: The Grand Finale (The 7 Queries)**
*Scroll to Cell 11.*
"Because the database is the application, our API is just SQL. 
- Want a fuzzy search that survives OCR typos? `SELECT * FROM fuzzy_search('karma', 0.1);`
- Want to find philosophically similar texts? `SELECT * FROM similar_manuscripts(1);` 
- Want to translate a text on the fly? `SELECT * FROM search_and_translate('dharma');`

Thank you."
