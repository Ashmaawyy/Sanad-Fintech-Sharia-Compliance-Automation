"""Al-Furqan Knowledge Base Layer — Elasticsearch-backed."""

from al_furqan.kb.es.collections import (
    Hadith,
    HadithCollection,
    IIFAResolutionDocument,
    QuranCollection,
    QuranVerse,
)
from al_furqan.kb.es.iifa import IIFAResolutionCollection
from al_furqan.kb.iifa import (
    IIFAConflictBlocked,
    IIFAResolution,
    VerifiedSource,
    check_against_iifa,
    digest_resolution,
    discover_resolution_links,
    enforce_iifa_precedent,
    ingest_official_resolutions,
)
from al_furqan.kb.es.retriever import (
    ESUnifiedRetriever as UnifiedRetriever,
)
from al_furqan.kb.es.retriever import (
    KnowledgeContext,
    RetrievalConfig,
    RetrievalResult,
    Source,
)

__all__ = [
    "Hadith",
    "HadithCollection",
    "IIFAResolution",
    "IIFAConflictBlocked",
    "IIFAResolutionCollection",
    "IIFAResolutionDocument",
    "KnowledgeContext",
    "QuranCollection",
    "QuranVerse",
    "RetrievalConfig",
    "RetrievalResult",
    "Source",
    "UnifiedRetriever",
    "VerifiedSource",
    "check_against_iifa",
    "digest_resolution",
    "discover_resolution_links",
    "enforce_iifa_precedent",
    "ingest_official_resolutions",
]
