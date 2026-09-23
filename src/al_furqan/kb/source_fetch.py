"""Controlled source download and provenance capture for Sprint 003."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from al_furqan.kb.source_manifest import SourceManifestEntry, SourceStatus


@dataclass(frozen=True)
class FetchedSource:
    """Downloaded source bytes plus network provenance."""

    requested_url: str
    final_url: str
    content_type: str
    content: bytes
    content_hash: str
    status_code: int

    def manifest_entry(
        self,
        *,
        source_id: str,
        retrieved_at: str,
        source_type: str,
        language: str,
        title: str = "",
        publisher: str = "",
        parser_version: str = "",
    ) -> SourceManifestEntry:
        """Create a downloaded-stage manifest entry."""
        return SourceManifestEntry(
            source_id=source_id,
            source_type=source_type,
            canonical_url=self.final_url,
            content_hash=self.content_hash,
            retrieved_at=retrieved_at,
            language=language,
            status=SourceStatus.DOWNLOADED,
            title=title,
            publisher=publisher,
            parser_version=parser_version,
            metadata={
                "requested_url": self.requested_url,
                "content_type": self.content_type,
                "status_code": self.status_code,
            },
        )


def fetch_source(
    url: str,
    *,
    allowed_hosts: tuple[str, ...] = ("iifa-aifi.org",),
    timeout: int = 30,
    session: requests.Session | None = None,
) -> FetchedSource:
    """Fetch HTTPS source content with host, redirect, and type checks."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("source URL must be HTTPS and on an approved host")
    client = session or requests.Session()
    response = client.get(url, timeout=timeout, allow_redirects=True)
    final = urlparse(response.url)
    if final.scheme != "https" or final.hostname not in allowed_hosts:
        raise ValueError("source redirected outside the approved host")
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in {"text/html", "application/pdf", "text/plain"}:
        raise ValueError(f"unsupported source content type: {content_type or 'missing'}")
    content = response.content
    return FetchedSource(
        requested_url=url,
        final_url=response.url,
        content_type=content_type,
        content=content,
        content_hash=hashlib.sha256(content).hexdigest(),
        status_code=response.status_code,
    )
