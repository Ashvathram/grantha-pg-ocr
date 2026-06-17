"""
local_demo_engine.py — Local Demo Mode for Grantha PG-OCR

This is a LOCAL DEMO fallback. The production pipeline runs entirely inside
PostgreSQL via PL/Python stored procedures (see grantha_ocr.ipynb).

This module uses SQLite + mock inference to demonstrate the pipeline locally
on systems without PostgreSQL installed (e.g., Windows without WSL).
It mirrors the exact schema and query patterns of the real pipeline.
"""

import sqlite3
import os
import hashlib
import random
import math
import json
from pathlib import Path
from datetime import datetime

# ─── ANSI color helpers ───────────────────────────────────────────────────────

class C:
    """ANSI escape codes for terminal styling."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    CYAN    = "\033[36m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    MAGENTA = "\033[35m"
    RED     = "\033[31m"
    BLUE    = "\033[34m"
    WHITE   = "\033[97m"
    BG_DIM  = "\033[48;5;236m"


# ─── Mock Grantha OCR corpus ─────────────────────────────────────────────────

# Realistic transliterated Grantha-script fragments (Sanskrit in IAST)
_GRANTHA_FRAGMENTS = [
    "oṁ namaḥ śivāya | śrī mahāgaṇapataye namaḥ | atha śrī bhagavadgītā ārambhaḥ |",
    "dharma-kṣetre kuru-kṣetre samavetā yuyutsavaḥ | māmakāḥ pāṇḍavāś caiva kim akurvata sañjaya ||",
    "yadā yadā hi dharmasya glānir bhavati bhārata | abhyutthānam adharmasya tadātmānaṁ sṛjāmy aham ||",
    "paritrāṇāya sādhūnāṁ vināśāya ca duṣkṛtām | dharma-saṁsthāpanārthāya sambhavāmi yuge yuge ||",
    "karmaṇy evādhikāras te mā phaleṣu kadācana | mā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi ||",
    "nainaṁ chindanti śastrāṇi nainaṁ dahati pāvakaḥ | na cainaṁ kledayanty āpo na śoṣayati mārutaḥ ||",
    "vāsāṁsi jīrṇāni yathā vihāya navāni gṛhṇāti naro 'parāṇi | tathā śarīrāṇi vihāya jīrṇāny anyāni saṁyāti navāni dehī ||",
    "aśocyān anvaśocas tvaṁ prajñā-vādāṁś ca bhāṣase | gatāsūn agatāsūṁś ca nānuśocanti paṇḍitāḥ ||",
    "yogasthaḥ kuru karmāṇi saṅgaṁ tyaktvā dhanañjaya | siddhy-asiddhyoḥ samo bhūtvā samatvaṁ yoga ucyate ||",
    "śrī rāmāyaṇam ādikāvyam | tapas svādhyāya nirataṁ tapasvī vāgvidāṁ varam | nāradaṁ paripapraccha vālmīkir munipuṅgavam ||",
    "oṁ asato mā sad gamaya | tamaso mā jyotir gamaya | mṛtyor māmṛtaṁ gamaya | oṁ śāntiḥ śāntiḥ śāntiḥ ||",
    "sarve bhavantu sukhinaḥ | sarve santu nirāmayāḥ | sarve bhadrāṇi paśyantu | mā kaścid duḥkha-bhāg bhavet ||",
]

_GEMINI_TRANSLATIONS = [
    "This passage is an invocation to Lord Śiva and Gaṇapati, marking the beginning of the Bhagavad Gītā recitation — a common opening formula in South Indian palm-leaf manuscript traditions.",
    "This verse from the Bhagavad Gītā (1.1) describes the gathering of warriors at Kurukṣetra. The Grantha script rendering preserves the classical sandhi patterns characteristic of 10th-century Pallava manuscript conventions.",
    "Bhagavad Gītā 4.7 — 'Whenever dharma declines and adharma rises, I manifest myself.' This is one of the most frequently copied verses in the Grantha manuscript tradition, often found on protective amulet-leaves.",
    "Bhagavad Gītā 4.8 — Lord Kṛṣṇa's promise to protect the righteous and restore cosmic order. The scribe's hand shows the characteristic rounded vowel markers of late Chola-period Grantha.",
    "Bhagavad Gītā 2.47 — The cornerstone verse on karma yoga. Manuscript analysis shows this verse was emphasized with vermilion marking in the original palm-leaf, indicating liturgical importance.",
    "Bhagavad Gītā 2.23 — The indestructibility of the ātman. The Grantha ligatures here demonstrate the complex consonant clusters typical of philosophical Sanskrit texts preserved in Tamil Nadu.",
    "Bhagavad Gītā 2.22 — The analogy of changing garments for the transmigration of the soul. Multi-line verse with characteristic Grantha line-breaking conventions at metrical caesura points.",
    "Bhagavad Gītā 2.11 — Kṛṣṇa's rebuke to Arjuna for grieving over the imperishable. The manuscript shows marginal annotations in Tamil-Grantha mixed script, common in commentarial traditions.",
    "Bhagavad Gītā 2.48 — Definition of yoga as equanimity. This folio shows wear patterns consistent with frequent liturgical use in temple recitation traditions.",
    "Opening verse of the Rāmāyaṇa — Vālmīki's inquiry to Nārada about the ideal person. The Grantha manuscript tradition for the Rāmāyaṇa is distinct from the Devanāgarī recension.",
    "Bṛhadāraṇyaka Upaniṣad 1.3.28 — The famous 'Lead me from untruth to truth' prayer. Frequently preserved as standalone folios in Grantha temple archives across Tamil Nadu and Kerala.",
    "A universal benediction from the tradition: 'May all beings be happy, may all be healthy.' This closing verse is characteristic of manuscript colophons in the South Indian Grantha tradition.",
]


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grantha_mock.db")


class AntigravityPGEngine:
    """
    Simulates an Antigravity-hosted PostgreSQL instance with:
      - pgvector extension (768-d embeddings stored as JSON blobs)
      - PL/Python stored procedures (search_manuscripts)
      - Kraken OCR inference (mocked with realistic Grantha corpus)
      - Gemini API transliteration (mocked with curated translations)
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn = None
        self._connect()

    # ─── Connection lifecycle ─────────────────────────────────────────────

    def _connect(self):
        """Simulate connecting to Antigravity-hosted PostgreSQL."""
        is_new = not os.path.exists(self.db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        if is_new:
            self._init_schema()

    def _init_schema(self):
        """Mirror the grantha_db schema: manuscripts table with vector column."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS manuscripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                raw_ocr TEXT,
                embedding TEXT,
                gemini_translation TEXT,
                ingested_at TEXT DEFAULT (datetime('now')),
                image_hash TEXT,
                image_size_bytes INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_manuscripts_filename ON manuscripts(filename);
        """)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    # ─── Mock Kraken OCR ──────────────────────────────────────────────────

    def _run_kraken_ocr(self, image_path: str) -> str:
        """
        Mock Kraken CRNN+CTC inference.
        In production, this calls: kraken -i <img> ocr -m grantha.mlmodel
        Here we return a deterministic fragment seeded by the image hash.
        """
        img_hash = self._hash_file(image_path)
        idx = int(img_hash[:8], 16) % len(_GRANTHA_FRAGMENTS)
        # Combine 2-3 fragments for a realistic multi-line OCR output
        num_lines = 2 + (int(img_hash[8:10], 16) % 2)
        lines = []
        for i in range(num_lines):
            frag_idx = (idx + i) % len(_GRANTHA_FRAGMENTS)
            lines.append(_GRANTHA_FRAGMENTS[frag_idx])
        return "\n".join(lines)

    # ─── Mock Gemini API ──────────────────────────────────────────────────

    def _run_gemini_transliteration(self, raw_ocr: str, image_path: str) -> str:
        """
        Mock Gemini 2.0 Flash transliteration.
        In production: model.generate_content(prompt).text
        """
        img_hash = self._hash_file(image_path)
        idx = int(img_hash[:8], 16) % len(_GEMINI_TRANSLATIONS)
        return _GEMINI_TRANSLATIONS[idx]

    # ─── Mock pgvector embedding ──────────────────────────────────────────

    def _generate_embedding(self, text: str) -> list:
        """
        Generate a deterministic 768-d pseudo-embedding from text.
        In production, this would use a sentence-transformer or Gemini embedding API.
        """
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        vec = [rng.gauss(0, 1) for _ in range(768)]
        # L2-normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    # ─── Core pipeline operations ─────────────────────────────────────────

    def ingest_manuscript(self, image_path: str) -> dict:
        """
        Full pipeline: Image → Kraken OCR → Gemini Translation → pgvector embedding → INSERT.
        Returns the inserted row as a dict.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        filename = os.path.basename(image_path)
        image_size = os.path.getsize(image_path)
        img_hash = self._hash_file(image_path)

        # Check for duplicates
        existing = self._conn.execute(
            "SELECT id FROM manuscripts WHERE image_hash = ?", (img_hash,)
        ).fetchone()
        if existing:
            return {"status": "duplicate", "id": existing["id"], "filename": filename}

        # Pipeline stages
        raw_ocr = self._run_kraken_ocr(image_path)
        translation = self._run_gemini_transliteration(raw_ocr, image_path)
        embedding = self._generate_embedding(raw_ocr)

        self._conn.execute(
            """INSERT INTO manuscripts (filename, raw_ocr, embedding, gemini_translation, image_hash, image_size_bytes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (filename, raw_ocr, json.dumps(embedding), translation, img_hash, image_size)
        )
        self._conn.commit()

        row_id = self._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {
            "status": "ingested",
            "id": row_id,
            "filename": filename,
            "raw_ocr": raw_ocr,
            "translation": translation,
            "image_size_bytes": image_size,
        }

    def list_manuscripts(self) -> list:
        """SELECT * FROM manuscripts; — returns all ingested manuscripts."""
        rows = self._conn.execute(
            "SELECT id, filename, raw_ocr, gemini_translation, ingested_at, image_size_bytes FROM manuscripts ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def search_manuscripts(self, query: str) -> list:
        """
        PL/Python stored procedure: search_manuscripts(query TEXT)
        Runs ILIKE full-text search inside PostgreSQL.
        """
        rows = self._conn.execute(
            "SELECT id, filename, raw_ocr, gemini_translation FROM manuscripts WHERE raw_ocr LIKE ? OR filename LIKE ?",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
        return [dict(r) for r in rows]

    def fuzzy_search(self, query: str, threshold: float = 0.1) -> list:
        """
        PL/Python stored procedure: fuzzy_search(query TEXT, threshold FLOAT)
        Uses pg_trgm trigram similarity. Simulated here with character n-gram overlap.
        """
        def _trigram_similarity(a: str, b: str) -> float:
            a_lower, b_lower = a.lower(), b.lower()
            a_trgms = {a_lower[i:i+3] for i in range(max(0, len(a_lower) - 2))}
            b_trgms = {b_lower[i:i+3] for i in range(max(0, len(b_lower) - 2))}
            if not a_trgms or not b_trgms:
                return 0.0
            return len(a_trgms & b_trgms) / len(a_trgms | b_trgms)

        rows = self._conn.execute(
            "SELECT id, filename, raw_ocr, gemini_translation FROM manuscripts"
        ).fetchall()
        results = []
        for row in rows:
            score = _trigram_similarity(row["raw_ocr"] or "", query)
            if score >= threshold:
                results.append({
                    "id": row["id"],
                    "filename": row["filename"],
                    "raw_ocr": row["raw_ocr"],
                    "gemini_translation": row["gemini_translation"],
                    "similarity_score": round(score, 6),
                })
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results

    def similarity_search(self, query_text: str, top_k: int = 3) -> list:
        """
        pgvector cosine similarity: embedding <=> query_vector
        Simulated with cosine distance computation over stored JSON embeddings.
        """
        query_vec = self._generate_embedding(query_text)
        rows = self._conn.execute(
            "SELECT id, filename, raw_ocr, gemini_translation, embedding FROM manuscripts"
        ).fetchall()

        results = []
        for row in rows:
            stored_vec = json.loads(row["embedding"])
            dist = self._cosine_distance(query_vec, stored_vec)
            results.append({
                "id": row["id"],
                "filename": row["filename"],
                "raw_ocr": row["raw_ocr"],
                "gemini_translation": row["gemini_translation"],
                "cosine_distance": round(dist, 6),
            })

        results.sort(key=lambda x: x["cosine_distance"])
        return results[:top_k]

    def get_manuscript(self, manuscript_id: int) -> dict | None:
        """Fetch a single manuscript by ID."""
        row = self._conn.execute(
            "SELECT id, filename, raw_ocr, gemini_translation, ingested_at, image_size_bytes FROM manuscripts WHERE id = ?",
            (manuscript_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_stats(self) -> dict:
        """Database statistics."""
        count = self._conn.execute("SELECT COUNT(*) FROM manuscripts").fetchone()[0]
        total_size = self._conn.execute("SELECT COALESCE(SUM(image_size_bytes), 0) FROM manuscripts").fetchone()[0]
        return {
            "total_manuscripts": count,
            "total_image_bytes": total_size,
            "db_file_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            "embedding_dimensions": 768,
        }

    # ─── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _hash_file(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _cosine_distance(a: list, b: list) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 1.0
        similarity = dot / (norm_a * norm_b)
        return 1.0 - similarity
