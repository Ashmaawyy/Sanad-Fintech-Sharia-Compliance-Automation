"""Elasticsearch persistence and retrieval for IIFA resolutions."""

from __future__ import annotations

from elasticsearch import Elasticsearch

from al_furqan.kb.es.collections import IIFAResolutionDocument
from al_furqan.kb.iifa import IIFAResolution
from al_furqan.kb.source_manifest import SourceManifest


class IIFAResolutionCollection:
    """Store and search only official IIFA resolution documents."""

    def __init__(self, es: Elasticsearch, index: str = "furqan_iifa_resolutions") -> None:
        self._es = es
        self._index = index

    def save(self, resolution: IIFAResolution, manifest: SourceManifest) -> str:
        """Index a digested resolution by immutable resolution/hash identity."""
        if not resolution.official_url.startswith("https://iifa-aifi.org/"):
            raise ValueError("IIFA resolution must use the official HTTPS domain")
        if not manifest.publishable(resolution.resolution_id):
            raise ValueError("IIFA resolution is not approved by the source manifest")
        document = resolution.to_document()
        document["manifest_status"] = manifest.get(resolution.resolution_id).status.value
        document["manifest_reviewer"] = manifest.get(resolution.resolution_id).reviewer
        self._es.index(
            index=self._index,
            id=resolution.resolution_id,
            document=document,
            refresh="wait_for",
        )
        return resolution.resolution_id

    def search(self, query: str, limit: int = 10, reviewed_only: bool = True) -> list[IIFAResolutionDocument]:
        """Search approved precedent records by title, content, and topics."""
        filters = [{"term": {"published": True}}]
        if reviewed_only:
            filters.append({"term": {"reviewed": True}})
        body = {
            "query": {
                "bool": {
                    "must": [{"multi_match": {"query": query, "fields": ["title^3", "content", "topics"]}}],
                    "filter": filters,
                }
            },
            "size": limit,
        }
        response = self._es.search(index=self._index, body=body)
        return [self._from_source(hit["_source"]) for hit in response["hits"]["hits"]]

    @staticmethod
    def _from_source(source: dict) -> IIFAResolutionDocument:
        return IIFAResolutionDocument(
            resolution_id=source["resolution_id"],
            title=source.get("title", ""),
            official_url=source["official_url"],
            source_hash=source["source_hash"],
            content=source.get("content", ""),
            language=source.get("language", "en"),
            session=source.get("session", ""),
            published=source.get("published", False),
            reviewed=source.get("reviewed", False),
            topics=source.get("topics", []),
            conflict_terms=source.get("conflict_terms", []),
            metadata=source.get("metadata", {}),
        )
