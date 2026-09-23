"""Tests for the Sprint 003 source manifest publication gate."""

from al_furqan.kb import (
    IIFAResolution,
    SourceManifest,
    SourceStatus,
    manifest_entry_for_iifa,
)


def test_unreviewed_iifa_source_cannot_publish():
    """Parsed sources remain outside the published KB until review."""
    resolution = IIFAResolution(
        resolution_id="IIFA-259",
        title="Loan increment",
        official_url="https://iifa-aifi.org/en/56039.html",
        source_hash="abc123",
    )
    entry = manifest_entry_for_iifa(
        resolution,
        retrieved_at="2026-09-23T00:00:00Z",
    )
    manifest = SourceManifest([entry])

    assert entry.status is SourceStatus.PARSED
    assert not manifest.publishable("IIFA-259")


def test_reviewed_iifa_source_is_publishable_and_round_trips(tmp_path):
    """Reviewed provenance survives deterministic manifest serialization."""
    resolution = IIFAResolution(
        resolution_id="IIFA-262",
        title="Shariah governance",
        official_url="https://iifa-aifi.org/en/56070.html",
        source_hash="def456",
        language="en",
    )
    entry = manifest_entry_for_iifa(
        resolution,
        retrieved_at="2026-09-23T00:00:00Z",
        status=SourceStatus.REVIEWED,
        reviewer="reviewer-1",
    )
    path = tmp_path / "manifest.json"
    manifest = SourceManifest([entry])
    manifest.save(path)
    loaded = SourceManifest.load(path)

    assert loaded.publishable("IIFA-262")
    assert loaded.get("IIFA-262").content_hash == "def456"
