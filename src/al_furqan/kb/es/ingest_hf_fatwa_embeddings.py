"""Index staged Hugging Face fatwa question and embedding shards.

The staged dataset contains questions/metadata and answer embeddings, but no
answer text. It is therefore indexed separately from the reviewed financial
Q&A corpus and never presented as a complete fatwa answer.

Usage:
    python -m al_furqan.kb.es.setup_indices --index fatwa_embeddings
    python -m al_furqan.kb.es.ingest_hf_fatwa_embeddings --dry-run
    python -m al_furqan.kb.es.ingest_hf_fatwa_embeddings
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.paths import DATA_STAGING

logger = logging.getLogger(__name__)
DEFAULT_ROOT = DATA_STAGING / "huggingface" / "islamqa_embeddings"
DEFAULT_INDEX = "furqan_fatwa_embeddings"
MODEL_NAME = "bert-base-multilingual-uncased"


def _embedding(record: dict) -> list[float]:
    """Extract the first vector from the staged answer embedding record."""
    vectors = record["answer_embeddings"]["truncated_answ"][MODEL_NAME]
    return [float(value) for value in vectors[0]]


def iter_actions(root: Path = DEFAULT_ROOT, index: str = DEFAULT_INDEX):
    """Yield actions from every extracted shard, pairing data and embeddings."""
    for dataset_dir in sorted(root.glob("islamqa_emb_*")):
        shard_dir = dataset_dir / dataset_dir.name
        if not shard_dir.is_dir():
            continue
        for data_path in sorted(shard_dir.glob("file_data_*")):
            suffix = data_path.name.removeprefix("file_data_")
            embedding_path = shard_dir / f"file_emb_{suffix}"
            if not embedding_path.exists():
                raise FileNotFoundError(f"Missing embedding pair for {data_path}")
            data = json.loads(data_path.read_text(encoding="utf-8"))
            embeddings = json.loads(embedding_path.read_text(encoding="utf-8"))
            if set(data) != set(embeddings):
                raise ValueError(f"Record keys differ between {data_path} and {embedding_path}")
            for record_key in sorted(data, key=lambda value: int(value)):
                record = data[record_key]
                embedding_record = embeddings[record_key]
                record_id = f"hf_{dataset_dir.name}_{suffix}_{record_key}"
                yield {
                    "_index": index,
                    "_id": record_id,
                    "_source": {
                        "record_id": record_id,
                        "question": record.get("question", ""),
                        "metadata": record.get("metadata", {}),
                        "source_archive": "islamqa_emb_0.tar.xz/islamqa_emb_1.tar.xz",
                        "source_shard": f"{dataset_dir.name}/{data_path.name}",
                        "embedding_model": MODEL_NAME,
                        "answer_embedding": _embedding(embedding_record),
                    },
                }


def ingest(es: Elasticsearch | None, root: Path, index: str, dry_run: bool) -> int:
    """Validate or index all staged HF records."""
    actions = iter_actions(root, index)
    if dry_run:
        count = sum(1 for _ in actions)
        logger.info("Dry run: %d HF fatwa embedding records ready", count)
        return count
    success, errors = bulk(es, actions, stats_only=False, raise_on_error=False)
    if errors:
        logger.error("HF fatwa embedding ingestion had %d failed actions", len(errors))
    logger.info("Indexed %d HF fatwa embedding records", success)
    return success


def main() -> None:
    """Run the HF shard ingestion command."""
    setup_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--es-url", default=None)
    args = parser.parse_args()
    if not args.root.exists():
        raise SystemExit(f"HF staging directory not found: {args.root}")
    es = None if args.dry_run else create_es_client(hosts=[args.es_url] if args.es_url else None)
    ingest(es, args.root, args.index, args.dry_run)


if __name__ == "__main__":
    main()
