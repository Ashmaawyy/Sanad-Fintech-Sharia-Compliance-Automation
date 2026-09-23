"""Elasticsearch persistence and retrieval for four-school fiqh rulings."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from al_furqan.kb.iifa import FiqhRuling
from al_furqan.kb.source_manifest import SourceManifest


class FiqhRulingCollection:
    """Store and search reviewed Hanafi, Maliki, Shafii, and Hanbali rulings."""

    def __init__(self, es: Elasticsearch, index: str = "furqan_fiqh_rulings") -> None:
        self._es = es
        self._index = index

    def save(self, ruling: FiqhRuling, manifest: SourceManifest) -> str:
        """Index only a recognized school attribution."""
        if ruling.school.casefold() not in {"hanafi", "maliki", "shafii", "hanbali"}:
            raise ValueError("Fiqh ruling must identify one of the four supported schools")
        if not manifest.publishable(ruling.ruling_id):
            raise ValueError("Fiqh ruling is not approved by the source manifest")
        document = ruling.to_document()
        document["manifest_status"] = manifest.get(ruling.ruling_id).status.value
        document["manifest_reviewer"] = manifest.get(ruling.ruling_id).reviewer
        self._es.index(
            index=self._index,
            id=ruling.ruling_id,
            document=document,
            refresh="wait_for",
        )
        return ruling.ruling_id

    def search(self, query: str, limit: int = 10, reviewed_only: bool = True) -> list[FiqhRuling]:
        """Search verified school rulings, filtering unpublished review data."""
        filters = [{"term": {"reviewed": True}}, {"term": {"verified": True}}]
        if not reviewed_only:
            filters = []
        body = {
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": query, "fields": ["title^3", "text", "school", "source_reference"]}}],
                    "filter": filters,
                }
            },
            "size": limit,
        }
        response = self._es.search(index=self._index, body=body)
        return [self._from_source(hit["_source"]) for hit in response["hits"]["hits"]]

    @staticmethod
    def _from_source(source: dict) -> FiqhRuling:
        return FiqhRuling(
            ruling_id=source["ruling_id"],
            school=source["school"],
            scholar=source["scholar"],
            title=source.get("title", ""),
            source_reference=source["source_reference"],
            text=source.get("text", ""),
            reviewed=source.get("reviewed", False),
            verified=source.get("verified", False),
            conflict_terms=tuple(source.get("conflict_terms", [])),
            metadata=source.get("metadata", {}),
        )
