"""Central filesystem path constants for the al-furqan project.

Every module that needs a filesystem path should import from here rather
than re-deriving ``PROJECT_ROOT`` from ``Path(__file__).resolve().parent...``.
This gives us one place to change when directories move, and eliminates the
depth-dependent ``.parent`` chains that silently break on reorganization.

Anchors
-------
- :data:`PROJECT_ROOT` — repo root (directory containing ``pyproject.toml``)
- :data:`DATA_ARCHIVE` — static reference data and archived snapshots
- :data:`DATA_TRAINING` — training-pipeline outputs (JSONL files)
- :data:`DATA_HUMAN_HISTORY` — human-history raw source material

All other constants are derived from these four.

Note
----
``PROJECT_ROOT`` here is the **repo root**, not the user-level data directory.
The user-level directory lives in :mod:`al_furqan.config` as ``USER_DATA_ROOT``
(``~/.al-furqan`` by default).  The two are different things and must not be
confused — keep them clearly named at the import site.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Root anchors
# ---------------------------------------------------------------------------

# This file lives at: <repo>/src/al_furqan/paths.py
# parent.parent.parent → <repo>
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

DATA_ARCHIVE: Path = PROJECT_ROOT / "data_archive"

# ---------------------------------------------------------------------------
# Archive subtrees (static reference data)
# ---------------------------------------------------------------------------

DATA_QURAN: Path = DATA_ARCHIVE / "quran"
DATA_HADITH: Path = DATA_ARCHIVE / "hadith"
DATA_GRAPH: Path = DATA_ARCHIVE / "graph"
DATA_LESSONS: Path = DATA_ARCHIVE / "lessons"
DATA_HUMAN_HISTORY: Path = DATA_ARCHIVE / "human_history"
DATA_EXTERNAL: Path = DATA_ARCHIVE / "external"
DATA_REVIEW: Path = DATA_ARCHIVE / "review"
DATA_FEEDBACK: Path = DATA_ARCHIVE / "feedback"
DATA_AUDIT: Path = DATA_ARCHIVE / "audit"
DATA_TAFSIR_FEEDBACK: Path = DATA_ARCHIVE / "tafsir_feedback"
DATA_SOURCES: Path = DATA_ARCHIVE / "sources"
DATA_FATWA_SOURCES: Path = DATA_SOURCES / "fatwas"
DATA_HUGGINGFACE_SOURCES: Path = DATA_SOURCES / "huggingface"
DATA_STAGING: Path = DATA_ARCHIVE / "staging"
DATA_FINANCIAL_FATWAS: Path = DATA_ARCHIVE / "fiqh" / "financial_qa"
DATA_DERIVED_FIQH: Path = DATA_ARCHIVE / "derived" / "fiqh"

FINANCIAL_FATWAS_CSV: Path = DATA_FINANCIAL_FATWAS / "financial_fatwas.csv"
FULL_FATWA_SOURCE_CSV: Path = DATA_FATWA_SOURCES / "islamic_qa_full.csv"
FULL_FATWA_EMBEDDINGS: Path = DATA_FATWA_SOURCES / "islamic_qa_embeddings.pt"
FINANCIAL_FATWA_ROW_INDICES: Path = (
    DATA_DERIVED_FIQH / "financial_fatwas_source_row_indices.txt"
)

# ---------------------------------------------------------------------------
# Training pipeline paths
# ---------------------------------------------------------------------------

DATA_TRAINING: Path = DATA_ARCHIVE / "training"
DATA_TRAINING_TESTING: Path = DATA_TRAINING / "testing"
DATA_TRAINING_LEARNING: Path = DATA_TRAINING / "learning"

# Specific well-known jsonl outputs
HUMAN_HISTORY_JSONL: Path = DATA_TRAINING / "human_history.jsonl"
HUMAN_LESSONS_JSONL: Path = DATA_TRAINING / "human_lessons.jsonl"
QURAN_GRAPH_JSONL: Path = DATA_TRAINING / "quran_graph.jsonl"
TESTING_TALK_ABOUT_HISTORY_JSONL: Path = (
    DATA_TRAINING_TESTING / "model_testing_how_people_talk_about_history.jsonl"
)

# ---------------------------------------------------------------------------
# Well-known individual files
# ---------------------------------------------------------------------------

QURAN_COMPLETE_JSON: Path = DATA_QURAN / "quran_complete.json"
HADITH_SAMPLE_JSON: Path = DATA_HADITH / "hadith_sample.json"
SAMPLE_GRAPH_JSON: Path = DATA_GRAPH / "sample_graph.json"
LESSONS_ENRICHED_DIR: Path = DATA_LESSONS / "lessons_enriched_json"

# ---------------------------------------------------------------------------
# ES cache (transient snapshots — gitignored)
# ---------------------------------------------------------------------------

ES_CACHE_DIR: Path = DATA_ARCHIVE / ".es_cache"

# ---------------------------------------------------------------------------
# Review / proposed-edge SQLite store
# ---------------------------------------------------------------------------

PROPOSED_EDGES_DB: Path = DATA_REVIEW / "proposed_edges.db"
