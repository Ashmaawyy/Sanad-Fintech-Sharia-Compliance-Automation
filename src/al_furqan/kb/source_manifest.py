"""Reproducible source manifest and publication gate for KB materials."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from al_furqan.kb.iifa import IIFAResolution


class SourceStatus(str, Enum):
    """Lifecycle state of an imported source."""

    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    PARSED = "parsed"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class SourceManifestEntry:
    """Immutable provenance record for one source artifact."""

    source_id: str
    source_type: str
    canonical_url: str
    content_hash: str
    retrieved_at: str
    language: str
    status: SourceStatus
    title: str = ""
    publisher: str = ""
    parser_version: str = ""
    reviewer: str = ""
    notes: str = ""
    metadata: dict = field(default_factory=dict)

    def can_publish(self) -> bool:
        """Only reviewed, hash-identified sources may be published."""
        return bool(
            self.content_hash
            and self.reviewer
            and self.status in {SourceStatus.REVIEWED, SourceStatus.PUBLISHED}
        )


class SourceManifest:
    """Idempotent manifest store for source provenance."""

    def __init__(self, entries: list[SourceManifestEntry] | None = None) -> None:
        self._entries = {entry.source_id: entry for entry in entries or []}

    def add(self, entry: SourceManifestEntry) -> None:
        """Add or replace one source record without duplicating IDs."""
        self._entries[entry.source_id] = entry

    def get(self, source_id: str) -> SourceManifestEntry | None:
        """Return one manifest entry."""
        return self._entries.get(source_id)

    def publishable(self, source_id: str) -> bool:
        """Check whether the source has passed the publication gate."""
        entry = self.get(source_id)
        return entry is not None and entry.can_publish()

    def entries(self) -> tuple[SourceManifestEntry, ...]:
        """Return deterministic entries for export or auditing."""
        return tuple(self._entries[key] for key in sorted(self._entries))

    def save(self, path: Path) -> None:
        """Write a deterministic JSON manifest."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for entry in self.entries():
            record = asdict(entry)
            record["status"] = entry.status.value
            payload.append(record)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "SourceManifest":
        """Load a previously saved manifest."""
        records = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            [
                SourceManifestEntry(
                    **{**record, "status": SourceStatus(record["status"])}
                )
                for record in records
            ]
        )


def manifest_entry_for_iifa(
    resolution: IIFAResolution,
    *,
    retrieved_at: str,
    status: SourceStatus = SourceStatus.PARSED,
    reviewer: str = "",
    parser_version: str = "iifa-html-v1",
) -> SourceManifestEntry:
    """Convert a digested IIFA resolution into a provenance manifest entry."""
    return SourceManifestEntry(
        source_id=resolution.resolution_id,
        source_type="iifa_resolution",
        canonical_url=resolution.official_url,
        content_hash=resolution.source_hash,
        retrieved_at=retrieved_at,
        language=resolution.language,
        status=status,
        title=resolution.title,
        publisher="International Islamic Fiqh Academy",
        parser_version=parser_version,
        reviewer=reviewer,
    )
