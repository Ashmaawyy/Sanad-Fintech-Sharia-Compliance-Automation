"""Focused Sprint 004 tests for evidence-grounded findings."""

import pytest
from pydantic import ValidationError

from al_furqan.fintech.evidence import (
    ComplianceFinding,
    EvidenceCitation,
    EvidenceKind,
    EvidenceValidator,
    ReasoningBasis,
)
from al_furqan.kb import IIFAResolution, SourceManifest, SourceStatus, manifest_entry_for_iifa


def reviewed_manifest() -> SourceManifest:
    """Build a reviewed source manifest fixture."""
    resolution = IIFAResolution(
        resolution_id="IIFA-262",
        title="Governance",
        official_url="https://iifa-aifi.org/en/56070.html",
        source_hash="hash-262",
    )
    return SourceManifest(
        [
            manifest_entry_for_iifa(
                resolution,
                retrieved_at="2026-09-23T00:00:00Z",
                status=SourceStatus.REVIEWED,
                reviewer="board-reviewer",
            )
        ]
    )


def citation(**updates) -> EvidenceCitation:
    """Create a valid-looking published IIFA citation."""
    values = {
        "evidence_id": "ev-1",
        "kind": EvidenceKind.IIFA_RESOLUTION,
        "source_id": "IIFA-262",
        "reference": "Resolution 262, paragraph 3",
        "text_ar": "نص عربي موثق",
        "source_hash": "hash-262",
        "anchor": "p. 3, paragraph 2",
        "url": "https://iifa-aifi.org/en/56070.html",
        "published": True,
        "verified": True,
    }
    values.update(updates)
    return EvidenceCitation(**values)


def test_final_finding_with_reviewed_citation_is_valid():
    """Reviewed source text can support a final finding."""
    finding = ComplianceFinding(
        finding_id="f-1",
        issue="Governance evidence",
        severity="advisory",
        summary="The source addresses governance requirements.",
        citations=[citation()],
        basis=ReasoningBasis.SOURCE_TEXT,
        confidence=0.9,
        final=True,
    )

    result = EvidenceValidator(reviewed_manifest()).validate_finding(finding)

    assert result.valid
    assert result.coverage == 1.0


def test_unpublished_or_stale_citation_cannot_support_final_finding():
    """Manifest and hash failures block final evidence."""
    finding = ComplianceFinding(
        finding_id="f-2",
        issue="Unsupported source",
        severity="blocking",
        summary="This must not be finalized.",
        citations=[citation(source_hash="stale-hash", published=False)],
        final=True,
    )

    result = EvidenceValidator(reviewed_manifest()).validate_finding(finding)

    assert not result.valid
    assert any("hash" in issue for issue in result.issues)
    assert any("published" in issue for issue in result.issues)


def test_translation_requires_explicit_language():
    """Translation text must remain distinguishable from Arabic source text."""
    with pytest.raises(ValidationError, match="translation_language"):
        citation(text_ar=None, text_translation="Official translation")


def test_iifa_citation_requires_anchor():
    """Institutional rulings need an exact passage anchor."""
    finding = ComplianceFinding(
        finding_id="f-3",
        issue="Missing anchor",
        severity="advisory",
        summary="Anchor is required.",
        citations=[citation(anchor=None)],
        final=True,
    )

    result = EvidenceValidator(reviewed_manifest()).validate_finding(finding)

    assert not result.valid
    assert any("anchor" in issue for issue in result.issues)
