"""Tests for official IIFA digestion and precedent conflict policy."""

from al_furqan.kb.iifa import (
    FiqhRuling,
    IIFAConflictBlocked,
    IIFA_RESOLUTIONS_URL,
    IIFAResolution,
    VerifiedSource,
    check_against_iifa,
    digest_resolution,
    discover_resolution_links,
    enforce_iifa_precedent,
    ingest_official_resolutions,
)


INDEX_HTML = """
<html><body>
<a href=\"/en/56039.html\">Resolution No. 259 (4/26) Payment of Increment on Loan</a>
<a href=\"https://example.com/nope\">Resolution No. 1 unrelated host</a>
</body></html>
"""


PAGE_HTML = """
<html><head><style>ignored</style></head><body>
<h1>Resolution No. 259 (4/26)</h1>
<p>Payment of increment on loan by a third party.</p>
</body></html>
"""


def test_discovery_accepts_only_official_resolution_links():
    """The index parser rejects non-IIFA links."""
    links = discover_resolution_links(INDEX_HTML)

    assert links == [("https://iifa-aifi.org/en/56039.html", "Resolution No. 259 (4/26) Payment of Increment on Loan")]


def test_digest_preserves_hash_and_official_provenance():
    """Digesting the same page produces the same source identity."""
    first = digest_resolution(
        PAGE_HTML,
        official_url="https://iifa-aifi.org/en/56039.html",
        title="Resolution No. 259 (4/26) Payment of Increment on Loan",
        published=True,
        reviewed=True,
        conflict_terms=["increment on loan"],
    )
    second = digest_resolution(
        PAGE_HTML,
        official_url="https://iifa-aifi.org/en/56039.html",
        title="Resolution No. 259 (4/26) Payment of Increment on Loan",
        published=True,
        reviewed=True,
        conflict_terms=["increment on loan"],
    )

    assert first.resolution_id == "IIFA-259 (4/26)"
    assert first.source_hash == second.source_hash
    assert "Payment of increment" in first.content
    assert first.eligible_precedent
    assert IIFA_RESOLUTIONS_URL.startswith("https://iifa-aifi.org/")


def test_official_index_can_digest_linked_pages():
    """Bulk digestion preserves official URLs and review gating."""
    records = ingest_official_resolutions(
        INDEX_HTML,
        lambda _url: PAGE_HTML,
    )

    assert len(records) == 1
    assert records[0].published is False
    assert records[0].reviewed is False


def test_unreviewed_ruling_cannot_block_output():
    """Fetched but unreviewed content is not a verdict constraint."""
    ruling = IIFAResolution(
        resolution_id="IIFA-1",
        title="Loan increment",
        official_url="https://iifa-aifi.org/en/1.html",
        source_hash="hash",
        published=True,
        reviewed=False,
        conflict_terms=("loan increment",),
    )

    result = check_against_iifa("This proposal includes a loan increment", [ruling])

    assert result.status == "clear"
    assert not result.conflicts


def test_approved_conflict_is_blocked_without_primary_source_evidence():
    """The agent cannot silently contradict approved IIFA precedent."""
    ruling = IIFAResolution(
        resolution_id="IIFA-259",
        title="Loan increment",
        official_url="https://iifa-aifi.org/en/259.html",
        source_hash="hash",
        published=True,
        reviewed=True,
        conflict_terms=("loan increment",),
    )

    result = check_against_iifa("This proposal includes a loan increment", [ruling])

    assert result.status == "blocked_conflict"
    assert result.conflicts == (ruling,)
    assert "blocked" in result.message

    try:
        enforce_iifa_precedent("This proposal includes a loan increment", [ruling])
    except IIFAConflictBlocked as exc:
        assert "blocked" in str(exc)
    else:
        raise AssertionError("unsupported IIFA conflict was not blocked")


def test_verified_quran_or_sunnah_evidence_escalates_conflict():
    """Verified primary-source evidence opens review instead of silent override."""
    ruling = IIFAResolution(
        resolution_id="IIFA-259",
        title="Loan increment",
        official_url="https://iifa-aifi.org/en/259.html",
        source_hash="hash",
        published=True,
        reviewed=True,
        conflict_terms=("loan increment",),
    )
    source = VerifiedSource("quran", "Quran 2:275", "Verified text", verified=True)

    result = check_against_iifa("This proposal includes a loan increment", [ruling], [source])

    assert result.status == "escalated_conflict"
    assert result.evidence == (source,)


def test_reviewed_four_school_ruling_raises_conflict():
    """Approved school interpretation is part of the precedent check."""
    ruling = FiqhRuling(
        ruling_id="FIQH-HANAFI-001",
        school="hanafi",
        scholar="Abu Hanifa school authority",
        title="Deferred debt increment",
        source_reference="Al-Hidayah, Book of Sale",
        text="An increment on a debt due solely to time is not permitted.",
        reviewed=True,
        verified=True,
        conflict_terms=("debt increment",),
    )

    result = check_against_iifa("This product permits a debt increment", [], fiqh_rulings=[ruling])

    assert result.status == "blocked_conflict"
    assert result.fiqh_conflicts == (ruling,)


def test_unverified_fiqh_ruling_cannot_raise_conflict():
    """School labels alone are not enough to enter the trusted corpus."""
    ruling = FiqhRuling(
        ruling_id="FIQH-MALIKI-001",
        school="maliki",
        scholar="Unverified attribution",
        title="Unreviewed ruling",
        source_reference="unverified manuscript",
        text="Text",
        reviewed=False,
        verified=False,
        conflict_terms=("debt increment",),
    )

    result = check_against_iifa("This product permits a debt increment", [], fiqh_rulings=[ruling])

    assert result.status == "clear"
    assert not result.fiqh_conflicts
