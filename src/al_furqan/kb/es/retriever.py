"""Elasticsearch-backed Unified Retriever.

Searches across the ES quran and hadith indices using text and phrase
queries.  All dataclasses (Source, RetrievalResult, etc.) are defined
here as the canonical location.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from elasticsearch import Elasticsearch

from al_furqan.kb.es.collections import (
    HadithCollection,
    QuranCollection,
)
from al_furqan.kb.es.iifa import IIFAResolutionCollection
from al_furqan.kb.es.fiqh import FiqhRulingCollection
from al_furqan.kb.es.fatwa import FatwaQACollection

# ---------------------------------------------------------------------------
# Retriever dataclasses (canonical location)
# ---------------------------------------------------------------------------


class Source(str, Enum):
    """Knowledge source type."""

    QURAN = "quran"
    HADITH = "hadith"
    FIQH = "fiqh"
    IIFA = "iifa"
    FATWA = "fatwa"


@dataclass
class RetrievalResult:
    """A single retrieval result from any collection."""

    source: Source
    content_ar: str
    content_en: str
    reference: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval."""

    sources: list[Source] = field(
        default_factory=lambda: [
            Source.QURAN,
            Source.HADITH,
            Source.FIQH,
            Source.IIFA,
            Source.FATWA,
        ]
    )
    limit_per_source: int = 3
    hadith_grading_filter: str | None = None


@dataclass
class KnowledgeContext:
    """Aggregated knowledge context ready for engine consumption."""

    results: list[RetrievalResult]
    formatted_text: str
    query: str
    sources_searched: list[Source]


logger = logging.getLogger(__name__)


class ESUnifiedRetriever:
    """Searches across all ES-backed KB collections and merges results.

    This is the ES equivalent of ``kb/retriever.py:UnifiedRetriever``.
    It accepts the same ``RetrievalConfig`` and returns the same
    ``KnowledgeContext`` dataclass, so all downstream code (engine,
    API routers, tafsir pipeline) works without changes.
    """

    def __init__(
        self,
        es: Elasticsearch,
        quran_index: str = "furqan_quran",
        hadith_index: str = "furqan_hadith",
    ) -> None:
        self._quran = QuranCollection(es, index=quran_index)
        self._hadith = HadithCollection(es, index=hadith_index)
        self._iifa = IIFAResolutionCollection(es)
        self._fiqh = FiqhRulingCollection(es)
        self._fatwa = FatwaQACollection(es)

    def retrieve(
        self,
        query: str,
        config: RetrievalConfig | None = None,
    ) -> KnowledgeContext:
        """Search all configured collections and return merged results."""
        if config is None:
            config = RetrievalConfig()

        all_results: list[RetrievalResult] = []
        sources_searched: list[Source] = []

        # Search Quran
        if Source.QURAN in config.sources:
            sources_searched.append(Source.QURAN)
            try:
                verses = self._quran.search(query, limit=config.limit_per_source)
                for v in verses:
                    all_results.append(
                        RetrievalResult(
                            source=Source.QURAN,
                            content_ar=v.text_ar,
                            content_en=v.text_en,
                            reference=f"Quran {v.surah}:{v.ayah}",
                            metadata={
                                "surah": v.surah,
                                "ayah": v.ayah,
                                "surah_name_en": v.surah_name_en,
                                "juz": v.juz,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Quran search failed: %s", e)

        # Search Hadith
        if Source.HADITH in config.sources:
            sources_searched.append(Source.HADITH)
            try:
                hadith_results = self._hadith.search(
                    query,
                    limit=config.limit_per_source,
                    grading_filter=config.hadith_grading_filter,
                )
                for h in hadith_results:
                    all_results.append(
                        RetrievalResult(
                            source=Source.HADITH,
                            content_ar=h.text_ar,
                            content_en=h.text_en,
                            reference=f"{h.collection_name.capitalize()} #{h.number}",
                            metadata={
                                "collection": h.collection_name,
                                "number": h.number,
                                "narrator": h.narrator,
                                "grading": h.grading,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Hadith search failed: %s", e)

        # Search reviewed IIFA precedent
        if Source.FATWA in config.sources:
            sources_searched.append(Source.FATWA)
            try:
                fatwas = self._fatwa.search(query, limit=config.limit_per_source)
                for fatwa in fatwas:
                    all_results.append(
                        RetrievalResult(
                            source=Source.FATWA,
                            content_ar=fatwa.answer,
                            content_en=fatwa.answer,
                            reference=fatwa.fatwa_id,
                            metadata={
                                "question": fatwa.question,
                                "url": fatwa.url,
                                "source_row": fatwa.source_row,
                                "source_dataset": fatwa.source_dataset,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Financial fatwa search failed: %s", e)

        # Search reviewed IIFA precedent
        if Source.FIQH in config.sources:
            sources_searched.append(Source.FIQH)
            try:
                rulings = self._fiqh.search(query, limit=config.limit_per_source)
                for ruling in rulings:
                    all_results.append(
                        RetrievalResult(
                            source=Source.FIQH,
                            content_ar=ruling.text,
                            content_en=ruling.text,
                            reference=ruling.ruling_id,
                            metadata={
                                "school": ruling.school,
                                "scholar": ruling.scholar,
                                "source_reference": ruling.source_reference,
                                "reviewed": ruling.reviewed,
                                "verified": ruling.verified,
                                "conflict_terms": ruling.conflict_terms,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Fiqh ruling search failed: %s", e)

        # Search reviewed IIFA precedent
        if Source.IIFA in config.sources:
            sources_searched.append(Source.IIFA)
            try:
                resolutions = self._iifa.search(query, limit=config.limit_per_source)
                for resolution in resolutions:
                    all_results.append(
                        RetrievalResult(
                            source=Source.IIFA,
                            content_ar="",
                            content_en=resolution.content,
                            reference=resolution.resolution_id,
                            metadata={
                                "title": resolution.title,
                                "official_url": resolution.official_url,
                                "source_hash": resolution.source_hash,
                                "reviewed": resolution.reviewed,
                                "published": resolution.published,
                                "conflict_terms": resolution.conflict_terms,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("IIFA resolution search failed: %s", e)

        # Deduplicate by reference
        seen: set[str] = set()
        deduped: list[RetrievalResult] = []
        for r in all_results:
            if r.reference not in seen:
                seen.add(r.reference)
                deduped.append(r)

        formatted = self._format_results(deduped)

        return KnowledgeContext(
            results=deduped,
            formatted_text=formatted,
            query=query,
            sources_searched=sources_searched,
        )

    @staticmethod
    def _format_results(results: list[RetrievalResult]) -> str:
        """Format results into text for engine consumption."""
        if not results:
            return "No relevant knowledge found."

        sections: list[str] = []

        quran = [r for r in results if r.source == Source.QURAN]
        hadith = [r for r in results if r.source == Source.HADITH]
        iifa = [r for r in results if r.source == Source.IIFA]
        fiqh = [r for r in results if r.source == Source.FIQH]
        fatwas = [r for r in results if r.source == Source.FATWA]

        if quran:
            lines = ["=== Quran Evidence ==="]
            for r in quran:
                lines.append(f"[{r.reference}]")
                lines.append(f"  Arabic: {r.content_ar}")
                lines.append(f"  English: {r.content_en}")
            sections.append("\n".join(lines))

        if hadith:
            lines = ["=== Hadith Evidence ==="]
            for r in hadith:
                grading = r.metadata.get("grading", "")
                narrator = r.metadata.get("narrator", "")
                lines.append(f"[{r.reference}] ({grading}) — Narrated by {narrator}")
                lines.append(f"  Arabic: {r.content_ar}")
                lines.append(f"  English: {r.content_en}")
            sections.append("\n".join(lines))

        if iifa:
            lines = ["=== Approved IIFA Resolutions ==="]
            for r in iifa:
                title = r.metadata.get("title", "")
                lines.append(f"[{r.reference}] {title}")
                lines.append(f"  Official source: {r.metadata.get('official_url', '')}")
                lines.append(f"  Content: {r.content_en}")
            sections.append("\n".join(lines))

        if fiqh:
            lines = ["=== Reviewed Four-School Fiqh Rulings ==="]
            for r in fiqh:
                lines.append(
                    f"[{r.reference}] {r.metadata.get('school', '')} — "
                    f"{r.metadata.get('scholar', '')}"
                )
                lines.append(f"  Reference: {r.metadata.get('source_reference', '')}")
                lines.append(f"  Ruling: {r.content_ar}")
            sections.append("\n".join(lines))

        if fatwas:
            lines = ["=== Financial Fatwa Q&A Evidence ==="]
            for r in fatwas:
                lines.append(f"[{r.reference}] {r.metadata.get('question', '')}")
                lines.append(f"  Source: {r.metadata.get('url', '')}")
                lines.append(f"  Answer: {r.content_en}")
            sections.append("\n".join(lines))

        return "\n\n".join(sections)
