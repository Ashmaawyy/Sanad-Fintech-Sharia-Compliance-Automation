"""Official IIFA resolution ingestion and precedent conflict policy.

IIFA records are precedent constraints for agent output. This module does not
claim that a web page is authentic merely because it was fetched: publication
status and source hashes are retained, and only reviewed records are eligible
for precedent checks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urljoin

import requests

IIFA_RESOLUTIONS_URL = "https://iifa-aifi.org/en/resolutions"
IIFA_DOMAIN = "iifa-aifi.org"


@dataclass(frozen=True)
class VerifiedSource:
    """A verified primary source offered to justify a board conflict."""

    source_type: str  # quran or sunnah
    reference: str
    text: str
    verified: bool = False

    @property
    def is_eligible(self) -> bool:
        """Only verified Qur'an or Sunnah evidence can open a conflict review."""
        return self.verified and self.source_type.lower() in {"quran", "sunnah"}


@dataclass(frozen=True)
class IIFAResolution:
    """Immutable, citable IIFA publication record."""

    resolution_id: str
    title: str
    official_url: str
    source_hash: str
    content: str = ""
    language: str = "en"
    session: str = ""
    published: bool = False
    reviewed: bool = False
    topics: tuple[str, ...] = ()
    conflict_terms: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    @property
    def eligible_precedent(self) -> bool:
        """Only reviewed official records enter the verdict RAG policy."""
        return (
            self.published
            and self.reviewed
            and self.official_url.startswith("https://iifa-aifi.org/")
        )

    def to_document(self) -> dict:
        """Return an Elasticsearch-ready source document."""
        return {
            "resolution_id": self.resolution_id,
            "title": self.title,
            "official_url": self.official_url,
            "source_hash": self.source_hash,
            "content": self.content,
            "language": self.language,
            "session": self.session,
            "published": self.published,
            "reviewed": self.reviewed,
            "topics": list(self.topics),
            "conflict_terms": list(self.conflict_terms),
            "metadata": self.metadata,
        }


class _ResolutionParser(HTMLParser):
    """Extract resolution links and visible text without trusting markup."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._text: list[str] = []
        self.visible_text: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "a":
            self._href = dict(attrs).get("href") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "a" and self._href:
            text = " ".join("".join(self._text).split())
            if text:
                self.links.append((self._href, text))
            self._href = ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.visible_text.append(data)
        if self._href:
            self._text.append(data)


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def discover_resolution_links(html: str, base_url: str = IIFA_RESOLUTIONS_URL) -> list[tuple[str, str]]:
    """Discover only official resolution links from the IIFA index."""
    parser = _ResolutionParser()
    parser.feed(html)
    discovered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, title in parser.links:
        absolute = urljoin(base_url, href)
        if "iifa-aifi.org/" not in absolute or absolute in seen:
            continue
        if re.search(r"resolution\s+no\.?", title, re.IGNORECASE):
            seen.add(absolute)
            discovered.append((absolute, title))
    return discovered


def digest_resolution(
    html: str,
    *,
    official_url: str,
    title: str = "",
    resolution_id: str | None = None,
    published: bool = False,
    reviewed: bool = False,
    topics: Iterable[str] = (),
    conflict_terms: Iterable[str] = (),
) -> IIFAResolution:
    """Create a reproducible resolution record from an official page body."""
    if not official_url.startswith("https://iifa-aifi.org/"):
        raise ValueError("IIFA resolution must use the official HTTPS domain")
    parser = _ResolutionParser()
    parser.feed(html)
    text = " ".join(" ".join(parser.visible_text).split())
    match = re.search(r"Resolution\s+No\.?\s*([0-9]+(?:\s*\([^)]*\))?)", title, re.IGNORECASE)
    resolved_id = resolution_id or (f"IIFA-{match.group(1)}" if match else f"IIFA-{_hash(html)[:16]}")
    return IIFAResolution(
        resolution_id=resolved_id,
        title=title.strip(),
        official_url=official_url,
        source_hash=_hash(html),
        content=text,
        published=published,
        reviewed=reviewed,
        topics=tuple(sorted(set(topics))),
        conflict_terms=tuple(sorted(set(term.lower() for term in conflict_terms))),
    )


def ingest_official_resolutions(
    index_html: str,
    fetch_page,
    *,
    published: bool = False,
    reviewed: bool = False,
) -> list[IIFAResolution]:
    """Digest every resolution linked by an official IIFA index page.

    ``fetch_page`` is injected so production code can apply timeouts, retries,
    rate limits, and raw-response archival while tests remain deterministic.
    Records default to unpublished/unreviewed and therefore cannot constrain
    verdicts until an authorized reviewer promotes them.
    """
    resolutions: list[IIFAResolution] = []
    for official_url, title in discover_resolution_links(index_html):
        page_html = fetch_page(official_url)
        resolutions.append(
            digest_resolution(
                page_html,
                official_url=official_url,
                title=title,
                published=published,
                reviewed=reviewed,
            )
        )
    return resolutions


def fetch_official_index(timeout: int = 30) -> str:
    """Fetch the official IIFA resolutions index over HTTPS."""
    response = requests.get(IIFA_RESOLUTIONS_URL, timeout=timeout)
    response.raise_for_status()
    if IIFA_DOMAIN not in response.url:
        raise ValueError(f"Unexpected IIFA redirect: {response.url}")
    return response.text


@dataclass(frozen=True)
class ConflictCheck:
    """Policy result for comparing agent output with IIFA precedent."""

    status: str  # clear, blocked_conflict, escalated_conflict, no_precedent
    conflicts: tuple[IIFAResolution, ...] = ()
    evidence: tuple[VerifiedSource, ...] = ()
    message: str = ""


def check_against_iifa(
    proposal: str,
    rulings: Iterable[IIFAResolution],
    verified_sources: Iterable[VerifiedSource] = (),
) -> ConflictCheck:
    """Enforce the IIFA precedent policy for a verdict or proposal.

    Matching is deliberately conservative and explainable: an eligible ruling
    conflicts when one of its curated terms appears in the proposal. A future
    semantic retriever may find candidates, but it must still pass this policy
    gate before output is released.
    """
    text = proposal.casefold()
    ruling_list = tuple(rulings)
    conflicts = tuple(
        ruling
        for ruling in ruling_list
        if ruling.eligible_precedent
        and ruling.conflict_terms
        and any(term.casefold() in text for term in ruling.conflict_terms)
    )
    if not conflicts:
        return ConflictCheck("clear" if ruling_list else "no_precedent", message="No approved IIFA conflict matched.")
    evidence = tuple(source for source in verified_sources if source.is_eligible)
    if evidence:
        return ConflictCheck(
            "escalated_conflict",
            conflicts,
            evidence,
            "Output conflicts with approved IIFA precedent; verified primary-source evidence requires scholarly review.",
        )
    return ConflictCheck(
        "blocked_conflict",
        conflicts,
        (),
        "Output conflicts with approved IIFA precedent and lacks verified Qur'an/Sunnah evidence; release is blocked.",
    )


def enforce_iifa_precedent(
    proposal: str,
    rulings: Iterable[IIFAResolution],
    verified_sources: Iterable[VerifiedSource] = (),
) -> ConflictCheck:
    """Check generated output and raise on an unsupported board conflict.

    Callers may release ``clear`` results, route ``escalated_conflict`` to a
    qualified scholar, and must not release ``blocked_conflict`` results.
    """
    result = check_against_iifa(proposal, rulings, verified_sources)
    if result.status == "blocked_conflict":
        raise IIFAConflictBlocked(result.message)
    return result


class IIFAConflictBlocked(RuntimeError):
    """Raised when generated output contradicts approved IIFA precedent."""
