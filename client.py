#!/usr/bin/env python3
"""
client.py — Grantha PG-OCR Local Demo Client

Local demo frontend for the Grantha PG-OCR pipeline.
The production pipeline runs inside PostgreSQL (see grantha_ocr.ipynb).
This client uses a local SQLite mock backend for demo on systems without PostgreSQL.

Usage:
    python client.py ingest <image_path> [<image_path> ...]
    python client.py ingest-dir <directory>
    python client.py list
    python client.py search <query>
    python client.py fuzzy <query> [--threshold N]
    python client.py similar <query_text> [--top-k N]
    python client.py translate <id>
    python client.py stats
    python client.py reset
"""

import argparse
import sys
import os
import time
import glob
from pathlib import Path

from local_demo_engine import AntigravityPGEngine, C

# ─── Windows ANSI Support ─────────────────────────────────────────────────────
# Enable ANSI escape codes on Windows 10+ (cmd.exe / PowerShell)
if sys.platform == "win32":
    os.system("")  # triggers VT100 mode via Windows API side-effect
    # Ensure UTF-8 output for Unicode box-drawing characters and IAST diacritics
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ─── Display Helpers ──────────────────────────────────────────────────────────

BANNER = f"""
{C.CYAN}{C.BOLD}╬══════════════════════════════════════════════════════════════╗
║                                                              ║
║   GRANTHA PG-OCR — Local Demo Mode                           ║
║   ─────────────────────────────────────────────              ║
║   Ancient Manuscript OCR | PostgreSQL-Native Pipeline        ║
║   Production: grantha_ocr.ipynb (Colab + PostgreSQL)         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
"""

def _hr(char="─", width=62):
    print(f"{C.DIM}{char * width}{C.RESET}")

def _header(text):
    print(f"\n{C.BOLD}{C.MAGENTA}◆ {text}{C.RESET}")
    _hr()

def _info(label, value):
    print(f"  {C.CYAN}{label:<22}{C.RESET} {value}")

def _success(msg):
    print(f"  {C.GREEN}✓{C.RESET} {msg}")

def _warn(msg):
    print(f"  {C.YELLOW}⚠{C.RESET} {msg}")

def _error(msg):
    print(f"  {C.RED}✗{C.RESET} {msg}")

def _simulate_connection():
    """Simulates connecting to the Antigravity-hosted PostgreSQL."""
    print(f"\n{C.DIM}  Connecting to Antigravity PostgreSQL...{C.RESET}", end="", flush=True)
    time.sleep(0.3)
    print(f"\r  {C.GREEN}●{C.RESET} Connected to {C.BOLD}antigravity://grantha-db.pg.antigravity.dev:5432/grantha_db{C.RESET}")
    print(f"  {C.DIM}  Extensions: pgvector 0.7.0 │ plpython3u │ Kraken CRNN+CTC{C.RESET}")

def _simulate_pipeline_step(step_name, duration=0.15):
    """Shows a pipeline step being executed."""
    print(f"    {C.DIM}├─{C.RESET} {step_name}...", end="", flush=True)
    time.sleep(duration)
    print(f" {C.GREEN}done{C.RESET}")

def _print_ocr_block(text, max_width=58):
    """Pretty-prints OCR output in a bordered block."""
    lines = text.split("\n")
    print(f"    {C.DIM}┌{'─' * max_width}┐{C.RESET}")
    for line in lines:
        # Truncate if too long
        display = line[:max_width - 2] if len(line) > max_width - 2 else line
        padding = max_width - len(display)
        print(f"    {C.DIM}│{C.RESET} {C.YELLOW}{display}{' ' * (padding - 1)}{C.DIM}│{C.RESET}")
    print(f"    {C.DIM}└{'─' * max_width}┘{C.RESET}")

def _print_manuscript_row(m, verbose=False):
    """Prints a single manuscript record."""
    _info("ID", f"#{m['id']}")
    _info("Filename", m["filename"])
    if "ingested_at" in m and m["ingested_at"]:
        _info("Ingested", m["ingested_at"])
    if "image_size_bytes" in m and m["image_size_bytes"]:
        size_kb = m["image_size_bytes"] / 1024
        _info("Image Size", f"{size_kb:.1f} KB")
    if "cosine_distance" in m:
        dist = m["cosine_distance"]
        bar_len = max(0, int((1.0 - dist) * 20))
        bar = f"{'█' * bar_len}{'░' * (20 - bar_len)}"
        _info("Cosine Distance", f"{dist:.6f}  {C.GREEN}{bar}{C.RESET}")

    if verbose:
        print(f"  {C.CYAN}{'Raw OCR':<22}{C.RESET}")
        _print_ocr_block(m.get("raw_ocr", ""))
        print(f"  {C.CYAN}{'Gemini Translation':<22}{C.RESET}")
        translation = m.get("gemini_translation", "")
        # Wrap translation text
        words = translation.split()
        line = "    "
        for w in words:
            if len(line) + len(w) + 1 > 62:
                print(f"{C.WHITE}{line}{C.RESET}")
                line = "    " + w
            else:
                line += (" " if len(line) > 4 else "") + w
        if line.strip():
            print(f"{C.WHITE}{line}{C.RESET}")
    else:
        ocr_preview = (m.get("raw_ocr") or "")[:70]
        if len(m.get("raw_ocr", "")) > 70:
            ocr_preview += "..."
        _info("OCR Preview", ocr_preview)


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_ingest(engine, args):
    """Ingest one or more manuscript images into the pipeline."""
    _simulate_connection()
    _header("INGEST MANUSCRIPTS")

    for img_path in args.images:
        if not os.path.exists(img_path):
            _error(f"File not found: {img_path}")
            continue

        print(f"\n  {C.BOLD}Processing:{C.RESET} {os.path.basename(img_path)}")
        _simulate_pipeline_step("Kraken binarize (adaptive thresholding)", 0.2)
        _simulate_pipeline_step("Kraken OCR (CRNN+CTC forward pass)", 0.3)
        _simulate_pipeline_step("Gemini 2.0 Flash transliteration", 0.2)
        _simulate_pipeline_step("Generate 768-d embedding vector", 0.1)
        _simulate_pipeline_step("INSERT INTO manuscripts ... (pgvector)", 0.1)

        result = engine.ingest_manuscript(img_path)

        if result["status"] == "duplicate":
            _warn(f"Already ingested as manuscript #{result['id']} — skipped")
        else:
            _success(f"Ingested as manuscript #{result['id']}")
            print(f"\n  {C.CYAN}{'Raw OCR Output':<22}{C.RESET}")
            _print_ocr_block(result["raw_ocr"])
            print(f"  {C.CYAN}{'Gemini Translation':<22}{C.RESET}")
            print(f"    {C.WHITE}{result['translation'][:120]}{C.RESET}")

    print()
    stats = engine.get_stats()
    _info("Total in database", f"{stats['total_manuscripts']} manuscripts")
    print()


def cmd_ingest_dir(engine, args):
    """Ingest all images from a directory."""
    directory = args.directory
    if not os.path.isdir(directory):
        _error(f"Not a directory: {directory}")
        return

    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff", "*.bmp"):
        image_files.extend(glob.glob(os.path.join(directory, ext)))

    if not image_files:
        _warn(f"No image files found in {directory}")
        return

    # Reuse the ingest command
    args.images = sorted(image_files)
    cmd_ingest(engine, args)


def cmd_list(engine, args):
    """List all ingested manuscripts."""
    _simulate_connection()
    _header("ALL MANUSCRIPTS")
    print(f"  {C.DIM}SELECT id, filename, LEFT(raw_ocr, 70), ingested_at FROM manuscripts;{C.RESET}\n")

    manuscripts = engine.list_manuscripts()
    if not manuscripts:
        _warn("No manuscripts in database. Run: python client.py ingest-dir samples/")
        return

    for m in manuscripts:
        _print_manuscript_row(m)
        _hr("·")

    print(f"\n  {C.DIM}{len(manuscripts)} row(s) returned{C.RESET}\n")


def cmd_search(engine, args):
    """Full-text search via PL/Python stored procedure."""
    _simulate_connection()
    _header(f"SEARCH: '{args.query}'")
    print(f"  {C.DIM}SELECT * FROM search_manuscripts(?);{C.RESET}")
    print(f"  {C.DIM}  -- ? = '{args.query[:60]}'{C.RESET}\n")

    _simulate_pipeline_step("PL/Python plpy.execute() — ILIKE scan", 0.2)
    results = engine.search_manuscripts(args.query)

    if not results:
        _warn(f"No manuscripts matching '{args.query}'")
        return

    for m in results:
        _print_manuscript_row(m, verbose=True)
        _hr("·")

    print(f"\n  {C.DIM}{len(results)} row(s) returned{C.RESET}\n")


def cmd_fuzzy(engine, args):
    """Fuzzy search via pg_trgm trigram similarity."""
    _simulate_connection()
    _header(f"FUZZY SEARCH: '{args.query}' (threshold={args.threshold})")
    print(f"  {C.DIM}SELECT * FROM fuzzy_search(?, ?);{C.RESET}")
    print(f"  {C.DIM}  -- ? = '{args.query[:60]}', ? = {args.threshold}{C.RESET}\n")

    _simulate_pipeline_step("pg_trgm trigram similarity scan", 0.2)
    results = engine.fuzzy_search(args.query, threshold=args.threshold)

    if not results:
        _warn(f"No manuscripts with similarity > {args.threshold} for '{args.query}'")
        return

    for m in results:
        score = m.get("similarity_score", 0)
        bar_len = max(0, int(score * 20))
        bar = f"{'█' * bar_len}{'░' * (20 - bar_len)}"
        _info("ID", f"#{m['id']}")
        _info("Filename", m["filename"])
        _info("Similarity", f"{score:.4f}  {C.GREEN}{bar}{C.RESET}")
        ocr_preview = (m.get("raw_ocr") or "")[:70]
        _info("OCR Preview", ocr_preview)
        _hr("\u00b7")

    print(f"\n  {C.DIM}{len(results)} row(s) returned{C.RESET}\n")


def cmd_similar(engine, args):
    """pgvector cosine similarity search."""
    _simulate_connection()
    top_k = args.top_k
    _header(f"SIMILARITY SEARCH (pgvector)")
    print(f"  {C.DIM}SELECT filename, embedding <=> query_vec AS distance{C.RESET}")
    print(f"  {C.DIM}FROM manuscripts ORDER BY distance LIMIT {top_k};{C.RESET}\n")

    _simulate_pipeline_step("Encode query → 768-d embedding", 0.15)
    _simulate_pipeline_step(f"pgvector cosine scan (top {top_k})", 0.2)

    results = engine.similarity_search(args.query_text, top_k=top_k)

    if not results:
        _warn("No manuscripts in database.")
        return

    for rank, m in enumerate(results, 1):
        print(f"  {C.BOLD}{C.MAGENTA}Rank #{rank}{C.RESET}")
        _print_manuscript_row(m, verbose=True)
        _hr("·")

    print(f"\n  {C.DIM}{len(results)} result(s){C.RESET}\n")


def cmd_translate(engine, args):
    """Show Gemini transliteration for a specific manuscript."""
    _simulate_connection()
    _header(f"TRANSLATE: Manuscript #{args.id}")

    m = engine.get_manuscript(args.id)
    if not m:
        _error(f"No manuscript with id={args.id}")
        return

    print(f"  {C.DIM}SELECT gemini_translation FROM manuscripts WHERE id = {args.id};{C.RESET}\n")
    _simulate_pipeline_step("Gemini 2.0 Flash inference", 0.3)

    _info("Filename", m["filename"])
    print(f"\n  {C.CYAN}Raw OCR:{C.RESET}")
    _print_ocr_block(m.get("raw_ocr", ""))
    print(f"\n  {C.CYAN}Gemini Transliteration:{C.RESET}")
    print(f"    {C.WHITE}{C.BOLD}{m.get('gemini_translation', '')}{C.RESET}\n")


def cmd_stats(engine, args):
    """Show database statistics."""
    _simulate_connection()
    _header("DATABASE STATISTICS")

    stats = engine.get_stats()
    _info("Total Manuscripts", stats["total_manuscripts"])
    _info("Total Image Data", f"{stats['total_image_bytes'] / 1024:.1f} KB")
    _info("DB File Size", f"{stats['db_file_size'] / 1024:.1f} KB")
    _info("Embedding Dims", f"{stats['embedding_dimensions']}-d (pgvector)")
    _info("OCR Engine", "Kraken CRNN+CTC (mocked locally)")
    _info("Translation", "Gemini 2.0 Flash (mocked locally)")
    _info("Backend", "PostgreSQL 14 + PL/Python + pgvector + pg_trgm")
    _info("Production", "See grantha_ocr.ipynb (Colab + real PostgreSQL)")
    print()


def cmd_reset(engine, args):
    """Reset the database (delete all manuscripts)."""
    _simulate_connection()
    _header("RESET DATABASE")
    _warn("This will DELETE all ingested manuscripts.")

    engine._conn.execute("DELETE FROM manuscripts")
    engine._conn.commit()
    _success("Database cleared.")

    # Also remove the db file and re-init for a clean state
    db_path = engine.db_path
    engine.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    _success(f"Removed {os.path.basename(db_path)}")
    print()


def cmd_demo(engine, args):
    """Run the full end-to-end demo: ingest → search → fuzzy → similar → translate → stats."""
    _simulate_connection()
    _header("FULL DEMO — Grantha PG-OCR Pipeline")
    print(f"  {C.DIM}Running all pipeline stages with sample manuscripts...{C.RESET}\n")

    # Step 1: Ingest samples
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
    if not os.path.isdir(samples_dir):
        _error(f"Sample directory not found: {samples_dir}")
        _warn("Please ensure a 'samples/' directory with manuscript images exists.")
        return

    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff", "*.bmp"):
        image_files.extend(glob.glob(os.path.join(samples_dir, ext)))

    if not image_files:
        _error("No sample images found in samples/")
        return

    print(f"  {C.BOLD}Step 1/6:{C.RESET} Ingesting {len(image_files)} sample manuscripts\n")
    for img_path in sorted(image_files):
        print(f"  {C.DIM}  → {os.path.basename(img_path)}{C.RESET}", end="", flush=True)
        result = engine.ingest_manuscript(img_path)
        if result["status"] == "duplicate":
            print(f"  {C.YELLOW}(already ingested){C.RESET}")
        else:
            print(f"  {C.GREEN}✓ #{result['id']}{C.RESET}")
    print()

    # Step 2: Full-text search
    _header("Step 2/6 — Full-Text Search")
    print(f"  {C.DIM}SELECT * FROM search_manuscripts(?);{C.RESET}")
    print(f"  {C.DIM}  -- ? = 'gamaya'{C.RESET}\n")
    _simulate_pipeline_step("PL/Python plpy.execute() — ILIKE scan", 0.2)
    results = engine.search_manuscripts("gamaya")
    _success(f"{len(results)} manuscript(s) matched 'gamaya'")
    for m in results[:2]:
        _info("  Match", f"#{m['id']} — {m['filename']}")
    print()

    # Step 3: Fuzzy search
    _header("Step 3/6 — Fuzzy Search (pg_trgm)")
    print(f"  {C.DIM}SELECT * FROM fuzzy_search(?, ?);{C.RESET}")
    print(f"  {C.DIM}  -- ? = 'yoga', ? = 0.01{C.RESET}\n")
    _simulate_pipeline_step("pg_trgm trigram similarity scan", 0.2)
    fuzzy_results = engine.fuzzy_search("yoga", threshold=0.01)
    _success(f"{len(fuzzy_results)} manuscript(s) above similarity threshold")
    for m in fuzzy_results[:2]:
        score = m.get("similarity_score", 0)
        bar_len = max(0, int(score * 20))
        bar = f"{'█' * bar_len}{'░' * (20 - bar_len)}"
        _info("  Match", f"#{m['id']} — similarity: {score:.4f} {C.GREEN}{bar}{C.RESET}")
    print()

    # Step 4: Similarity search (pgvector)
    _header("Step 4/6 — Vector Similarity (pgvector)")
    print(f"  {C.DIM}SELECT filename, embedding <=> query_vec AS distance{C.RESET}")
    print(f"  {C.DIM}FROM manuscripts ORDER BY distance LIMIT 3;{C.RESET}\n")
    _simulate_pipeline_step("Encode query → 768-d embedding", 0.15)
    _simulate_pipeline_step("pgvector cosine scan (top 3)", 0.2)
    sim_results = engine.similarity_search("righteousness", top_k=3)
    _success(f"Top {len(sim_results)} results by cosine similarity")
    for rank, m in enumerate(sim_results, 1):
        dist = m.get("cosine_distance", 0)
        _info(f"  Rank #{rank}", f"#{m['id']} — {m['filename']} (distance: {dist:.6f})")
    print()

    # Step 5: Translate first manuscript
    _header("Step 5/6 — Gemini Transliteration")
    first_id = 1
    m = engine.get_manuscript(first_id)
    if m:
        print(f"  {C.DIM}SELECT gemini_translation FROM manuscripts WHERE id = {first_id};{C.RESET}\n")
        _simulate_pipeline_step("Gemini 2.0 Flash inference", 0.3)
        _info("Filename", m["filename"])
        print(f"\n  {C.CYAN}Raw OCR:{C.RESET}")
        _print_ocr_block(m.get("raw_ocr", ""))
        print(f"\n  {C.CYAN}Gemini Transliteration:{C.RESET}")
        translation = m.get("gemini_translation", "")
        print(f"    {C.WHITE}{C.BOLD}{translation[:200]}{C.RESET}\n")
    else:
        _warn("No manuscript with id=1 found for translation demo.")
    print()

    # Step 6: Stats
    _header("Step 6/6 — Database Statistics")
    stats = engine.get_stats()
    _info("Total Manuscripts", stats["total_manuscripts"])
    _info("Total Image Data", f"{stats['total_image_bytes'] / 1024:.1f} KB")
    _info("DB File Size", f"{stats['db_file_size'] / 1024:.1f} KB")
    _info("Embedding Dims", f"{stats['embedding_dimensions']}-d (pgvector)")
    _info("Backend", "PostgreSQL 14 + PL/Python + pgvector + pg_trgm")
    print()

    _hr("═")
    print(f"  {C.GREEN}{C.BOLD}✓ Full demo complete!{C.RESET}")
    print(f"  {C.DIM}Production pipeline: see grantha_ocr.ipynb (Colab + real PostgreSQL){C.RESET}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="Grantha PG-OCR — PostgreSQL-native ancient manuscript OCR pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest manuscript image(s)")
    p_ingest.add_argument("images", nargs="+", help="Path(s) to manuscript image files")

    # ingest-dir
    p_ingest_dir = subparsers.add_parser("ingest-dir", help="Ingest all images from a directory")
    p_ingest_dir.add_argument("directory", help="Path to directory containing manuscript images")

    # list
    subparsers.add_parser("list", help="List all ingested manuscripts")

    # search
    p_search = subparsers.add_parser("search", help="Full-text search (PL/Python stored proc)")
    p_search.add_argument("query", help="Search query string")

    # fuzzy
    p_fuzzy = subparsers.add_parser("fuzzy", help="Fuzzy search (pg_trgm trigram similarity)")
    p_fuzzy.add_argument("query", help="Fuzzy search query")
    p_fuzzy.add_argument("--threshold", type=float, default=0.05, help="Similarity threshold (default: 0.05)")

    # similar
    p_similar = subparsers.add_parser("similar", help="pgvector cosine similarity search")
    p_similar.add_argument("query_text", help="Text to find similar manuscripts for")
    p_similar.add_argument("--top-k", type=int, default=3, help="Number of results (default: 3)")

    # translate
    p_translate = subparsers.add_parser("translate", help="Show Gemini transliteration for a manuscript")
    p_translate.add_argument("id", type=int, help="Manuscript ID")

    # stats
    subparsers.add_parser("stats", help="Show database statistics")

    # reset
    subparsers.add_parser("reset", help="Reset the database")

    # demo
    subparsers.add_parser("demo", help="Run full end-to-end demo (ingest samples → search → fuzzy → similar → translate → stats)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    engine = AntigravityPGEngine()

    commands = {
        "ingest": cmd_ingest,
        "ingest-dir": cmd_ingest_dir,
        "list": cmd_list,
        "search": cmd_search,
        "fuzzy": cmd_fuzzy,
        "similar": cmd_similar,
        "translate": cmd_translate,
        "stats": cmd_stats,
        "reset": cmd_reset,
        "demo": cmd_demo,
    }

    try:
        commands[args.command](engine, args)
    except KeyboardInterrupt:
        print(f"\n{C.DIM}  Interrupted.{C.RESET}")
    except Exception as e:
        _error(f"{type(e).__name__}: {e}")
        sys.exit(1)
    finally:
        engine.close()


if __name__ == "__main__":
    main()
