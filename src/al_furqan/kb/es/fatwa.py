"""Elasticsearch retrieval for the financial fatwa Q&A corpus."""

from __future__ import annotations

from dataclasses import dataclass

from elasticsearch import Elasticsearch


@dataclass(frozen=True)
class FatwaQA:
    """A financial fatwa Q&A record."""

    fatwa_id: str
    question: str
    answer: str
    url: str
    source_row: int
    source_dataset: str


class FatwaQACollection:
    """Search the reviewed financial fatwa corpus."""

    def __init__(self, es: Elasticsearch, index: str = "furqan_fatwa_qa") -> None:
        self._es = es
        self._index = index

    def search(self, query: str, limit: int = 5) -> list[FatwaQA]:
        """Search questions and answers using the Arabic analyzer."""
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["question^3", "answer"],
                }
            },
            "size": limit,
        }
        response = self._es.search(index=self._index, body=body)
        return [self._from_source(hit["_source"]) for hit in response["hits"]["hits"]]

    @staticmethod
    def _from_source(source: dict) -> FatwaQA:
        return FatwaQA(
            fatwa_id=source["fatwa_id"],
            question=source.get("question", ""),
            answer=source.get("answer", ""),
            url=source.get("url", ""),
            source_row=source.get("source_row", 0),
            source_dataset=source.get("source_dataset", ""),
        )
