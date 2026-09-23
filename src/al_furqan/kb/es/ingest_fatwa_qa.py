"""Index the filtered financial fatwa Q&A corpus into Elasticsearch.

Usage:
    python -m al_furqan.kb.es.setup_indices --index fatwa_qa
    python -m al_furqan.kb.es.ingest_fatwa_qa --dry-run
    python -m al_furqan.kb.es.ingest_fatwa_qa
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.paths import FINANCIAL_FATWAS_CSV

logger = logging.getLogger(__name__)
DEFAULT_INDEX = "furqan_fatwa_qa"
SOURCE_DATASET = "Islamic Q and A.csv (financial subset)"


def _fatwa_id(row_number: int, question: str, url: str) -> str:
    """Build a stable ID from the source row and source URL/content."""
    digest = hashlib.sha256(f"{question}\n{url}".encode("utf-8")).hexdigest()[:16]
    return f"fatwa_{row_number}_{digest}"


def iter_actions(
    csv_path: Path = FINANCIAL_FATWAS_CSV,
    index: str = DEFAULT_INDEX,
):
    """Yield Elasticsearch bulk actions for the filtered CSV."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for row_number, row in enumerate(reader):
            question = row.get("question", "").strip()
            answer = row.get("answer", "").strip()
            url = row.get("URL", "").strip()
            if not question or not answer:
                continue
            yield {
                "_index": index,
                "_id": _fatwa_id(row_number, question, url),
                "_source": {
                    "fatwa_id": _fatwa_id(row_number, question, url),
                    "question": question,
                    "answer": answer,
                    "url": url,
                    "source_dataset": SOURCE_DATASET,
                    "source_row": row_number,
                    "topics": [],
                },
            }


def ingest(es: Elasticsearch, csv_path: Path, index: str, dry_run: bool = False) -> int:
    """Bulk-index the filtered financial corpus and return action count."""
    actions = iter_actions(csv_path, index)
    if dry_run:
        count = sum(1 for _ in actions)
        logger.info("Dry run: %d financial fatwa records ready", count)
        return count
    success, errors = bulk(es, actions, stats_only=False, raise_on_error=False)
    if errors:
        logger.error("Fatwa ingestion had %d failed actions", len(errors))
    logger.info("Indexed %d financial fatwa records", success)
    return success


def main() -> None:
    """Run the financial fatwa ingestion command."""
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=FINANCIAL_FATWAS_CSV)
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--es-url", default=None)
    args = parser.parse_args()
    if not args.csv.exists():
        raise SystemExit(f"Financial fatwa CSV not found: {args.csv}")
    es = None if args.dry_run else create_es_client(hosts=[args.es_url] if args.es_url else None)
    ingest(es, args.csv, args.index, args.dry_run)


if __name__ == "__main__":
    main()
