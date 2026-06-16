# Grantha PG-OCR

> Ancient Grantha manuscript OCR pipeline where the entire application lives inside PostgreSQL.

## The Obscure Stack
- PostgreSQL as the application layer — no app server, no Flask, no FastAPI
- PL/Python stored procedures — search and query logic runs inside the database
- pgvector — semantic similarity search via vector embeddings
- Kraken OCR — CRNN+CTC based OCR for ancient scripts
- Google Colab — runtime environment (Google technology)
- Gemini API — wired for transliteration (requires billing-enabled key)

## Why This Is Obscure
The frontend is psql. The backend is PostgreSQL stored procedures written in Python (PL/Python). There is no web server. Queries, search, and AI transliteration are all triggered via SQL.

## Pipeline
Manuscript Image -> Kraken OCR -> raw text -> INSERT into PostgreSQL -> PL/Python stored proc -> search_manuscripts() -> pgvector similarity search -> Gemini API transliteration

## Demo Queries

View all manuscripts:
SELECT id, filename, LEFT(raw_ocr, 80), LEFT(gemini_translation, 100) FROM manuscripts;

Full-text search inside Postgres:
SELECT filename, raw_ocr FROM manuscripts WHERE raw_ocr ILIKE '%query%';

Search via PL/Python stored procedure:
SELECT * FROM search_manuscripts('query');

## Setup
See the Colab notebook for full setup. Installs PostgreSQL, pgvector, plpython3u, and Kraken inside Colab.

## Gemini API Note
Gemini integration is fully wired in the code. Free tier quota was unavailable during development (limit: 0 for India region). Replace YOUR_KEY in the notebook with a billing-enabled Gemini API key to activate live transliteration.

## Context
Built for Stack Unknown — The Obscure Tech Hackathon (GDG on Campus, SASTRA University).
Manuscript images sourced from Wikimedia Commons (public domain Grantha scripts).
