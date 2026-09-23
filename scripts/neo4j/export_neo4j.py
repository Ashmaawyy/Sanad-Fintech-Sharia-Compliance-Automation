"""Export the current Neo4j graph to JSONL recovery files.

Usage:
    python scripts/neo4j/export_neo4j.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from _neo4j import add_neo4j_arg, init_logging, neo4j_driver

DEFAULT_OUTPUT = Path("data_archive/recovered/neo4j")


def _write_jsonl(path: Path, records: list[dict]) -> str:
    """Write deterministic JSONL and return its SHA-256 hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def export(driver, output: Path) -> dict:
    """Export nodes and relationships using generic Neo4j projections."""
    with driver.session() as session:
        nodes = [
            {
                "neo4j_id": record["neo4j_id"],
                "labels": record["labels"],
                "properties": record["properties"],
            }
            for record in session.run(
                "MATCH (n) RETURN elementId(n) AS neo4j_id, labels(n) AS labels, properties(n) AS properties ORDER BY elementId(n)"
            )
        ]
        relationships = [
            {
                "neo4j_id": record["neo4j_id"],
                "type": record["type"],
                "start_node": record["start_node"],
                "end_node": record["end_node"],
                "properties": record["properties"],
            }
            for record in session.run(
                "MATCH (a)-[r]->(b) RETURN elementId(r) AS neo4j_id, type(r) AS type, elementId(a) AS start_node, elementId(b) AS end_node, properties(r) AS properties ORDER BY elementId(r)"
            )
        ]

    node_hash = _write_jsonl(output / "nodes.jsonl", nodes)
    relationship_hash = _write_jsonl(output / "relationships.jsonl", relationships)
    return {
        "nodes": {"count": len(nodes), "path": "nodes.jsonl", "sha256": node_hash},
        "relationships": {
            "count": len(relationships),
            "path": "relationships.jsonl",
            "sha256": relationship_hash,
        },
    }


def main() -> None:
    """Export Neo4j and write a recovery manifest."""
    init_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    add_neo4j_arg(parser)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    with neo4j_driver(args.neo4j_url) as driver:
        result = export(driver, args.output)
    manifest = {
        "recovered_at": datetime.now(timezone.utc).isoformat(),
        "source": "neo4j",
        "neo4j_url": args.neo4j_url,
        "files": result,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()