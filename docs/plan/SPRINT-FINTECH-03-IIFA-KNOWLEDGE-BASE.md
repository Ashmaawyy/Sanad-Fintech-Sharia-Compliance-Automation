# Sprint Fintech 03: IIFA Resolutions Knowledge Base

**Goal:** Ingest and publish a reliable, reproducible IIFA resolutions corpus for retrieval and citation.

## Source policy

Start from the official index: https://iifa-aifi.org/en/resolutions. Preserve the official Arabic original and official translations when available. The 2024 ebook covers Resolutions 1-255; newer official resolution pages must be tracked individually. Initial finance-oriented triage includes Resolution 259 and Resolution 262, while the broader corpus remains available for future domains.

## Deliverables

- Source manifest with official URLs, resolution number, session, title, date, language, hash, and retrieval timestamp. **Implemented.**
- Downloader with HTTPS host/content-type checks, redirect recording, and source hashing. **Implemented; raw storage remains deployment-owned because corpus files are excluded from Git.**
- HTML/PDF parser retaining page and paragraph anchors; OCR quarantine for low-confidence extraction.
- Arabic canonical text and separately labeled translations.
- Resolution schema with topics, contract types, rule statements, conditions, exceptions, and related resolutions.
- Reviewed fiqh-ruling corpus for Hanafi, Maliki, Shafi'i, and Hanbali school interpretations, with scholar and book attribution.
- Conflict policy that treats reviewed school rulings as interpretive precedent and reserves Qur'an/Sunnah evidence for escalation against IIFA precedent.
- Human review queue before publication to the searchable KB. **Publication gate implemented; reviewer UI remains a follow-up.**
- Supersession and correction model.
- ES index and retrieval filters for source status, language, topic, contract, and resolution number. **Status/review filters implemented; remaining filters depend on enriched records.**

## Acceptance criteria

- A published record can be reproduced from its URL and recorded hash.
- No machine-generated translation is labeled as official.
- Every extracted rule points to an exact source passage.
- A reviewer can quarantine a malformed or changed source.
- Retrieval returns only published records by default.

## Tests

- Fixture ingestion for one HTML resolution and one PDF ebook.
- Hash and idempotency tests.
- Anchor preservation tests.
- Source status and supersession tests.
- Retrieval tests for Murabaha, loan increments, and Shariah governance.
- Four-school attribution, verification, and conflict-escalation tests.

## Sprint 003 completion note

The ingestion boundary is complete: IIFA and four-school fiqh records cannot be
published to Elasticsearch without a matching reviewed manifest entry and
reviewer identity. Remaining product work is the reviewer UI and richer
resolution/fiqh extraction (PDF anchors, OCR, translations, conditions, and
supersession relationships).
