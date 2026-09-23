"""Evidence-grounded findings for fintech Shariah review.

This module exposes reviewable rationale and source provenance. It does not
store or expose private model chain-of-thought.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from al_furqan.kb.source_manifest import SourceManifest


class EvidenceKind(str, Enum):
    """Origin of an evidence citation."""

    IIFA_RESOLUTION = "iifa_resolution"
    FIQH_RULING = "fiqh_ruling"
    QURAN = "quran"
    SUNNAH = "sunnah"
    CONTRACT = "contract"
    PRODUCT_FACT = "product_fact"


class ReasoningBasis(str, Enum):
    """Layer that produced a statement in a review finding."""

    SOURCE_TEXT = "source_text"
    SCHOLARLY_INTERPRETATION = "scholarly_interpretation"
    SYSTEM_INFERENCE = "system_inference"
    REVIEWER_JUDGMENT = "reviewer_judgment"


class EvidenceCitation(BaseModel):
    """A source passage that can be opened and independently checked."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    evidence_id: str = Field(..., min_length=1, max_length=200)
    kind: EvidenceKind
    source_id: str = Field(..., min_length=1, max_length=200)
    reference: str = Field(..., min_length=1, max_length=500)
    text_ar: str | None = Field(default=None, max_length=10000)
    text_translation: str | None = Field(default=None, max_length=10000)
    translation_language: str | None = Field(default=None, min_length=2, max_length=20)
    source_hash: str | None = Field(default=None, min_length=8, max_length=128)
    anchor: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=2000)
    published: bool = False
    verified: bool = False

    @model_validator(mode="after")
    def validate_translation(self) -> "EvidenceCitation":
        """Do not label translation text without naming its language."""
        if self.text_translation and not self.translation_language:
            raise ValueError("translation_language is required with text_translation")
        return self

    def passage_hash(self) -> str | None:
        """Hash the visible passage when text is available."""
        text = self.text_ar or self.text_translation
        return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


class ComplianceFinding(BaseModel):
    """A review finding with explicit evidence and reasoning provenance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    finding_id: str = Field(..., min_length=1, max_length=200)
    issue: str = Field(..., min_length=1, max_length=2000)
    severity: str = Field(..., min_length=1, max_length=50)
    summary: str = Field(..., min_length=1, max_length=4000)
    clause_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    citations: list[EvidenceCitation] = Field(default_factory=list)
    basis: ReasoningBasis = ReasoningBasis.SYSTEM_INFERENCE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    disagreement: bool = False
    remediation: str | None = Field(default=None, max_length=4000)
    final: bool = False


@dataclass(frozen=True)
class EvidenceValidation:
    """Validation result suitable for UI and audit logs."""

    valid: bool
    issues: tuple[str, ...] = ()
    coverage: float = 0.0


class EvidenceValidator:
    """Validate citation provenance against a reviewed source manifest."""

    def __init__(self, manifest: SourceManifest):
        self.manifest = manifest

    def validate_citation(self, citation: EvidenceCitation) -> tuple[str, ...]:
        """Return citation issues; an empty tuple means valid."""
        issues: list[str] = []
        entry = self.manifest.get(citation.source_id)
        if citation.kind in {EvidenceKind.IIFA_RESOLUTION, EvidenceKind.FIQH_RULING}:
            if entry is None:
                issues.append("source is absent from the manifest")
            elif not self.manifest.publishable(citation.source_id):
                issues.append("source is not published by the manifest")
            elif citation.source_hash != entry.content_hash:
                issues.append("source hash does not match the manifest")
        if citation.kind in {EvidenceKind.IIFA_RESOLUTION, EvidenceKind.FIQH_RULING} and not citation.anchor:
            issues.append("scholarly source citation requires an anchor")
        if not citation.text_ar and not citation.text_translation:
            issues.append("citation must include source text or an explicitly labeled translation")
        if citation.text_translation and not citation.translation_language:
            issues.append("translation language is missing")
        if citation.published is not True:
            issues.append("citation is not marked published")
        return tuple(issues)

    def validate_finding(
        self,
        finding: ComplianceFinding,
        *,
        required_citations: int = 1,
    ) -> EvidenceValidation:
        """Prevent final findings from carrying unsupported evidence."""
        issues: list[str] = []
        valid_count = 0
        for citation in finding.citations:
            citation_issues = self.validate_citation(citation)
            if citation_issues:
                issues.extend(f"{citation.evidence_id}: {issue}" for issue in citation_issues)
            else:
                valid_count += 1
        coverage = min(valid_count / required_citations, 1.0) if required_citations else 1.0
        if finding.final and valid_count < required_citations:
            issues.append("final finding does not meet required evidence coverage")
        return EvidenceValidation(not issues, tuple(issues), coverage)
