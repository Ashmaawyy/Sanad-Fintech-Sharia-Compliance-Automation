# ADR-001: Fintech Contract Review Workbench and IIFA-Grounded Knowledge Base

- **Status:** Proposed
- **Date:** 2026-09-10
- **Decision owners:** Product, engineering, and Shariah governance board
- **Scope:** Al-Furqan as a reusable reasoning layer for Shariah review of fintech products

## Context

Al-Furqan already provides a generic Scan -> Mirror -> Verdict -> Self-Correction engine, source retrieval, formal predicates, audit logging, and human review. It is intentionally not tied to one financial product.

A fintech compliance workflow needs a product-specific layer above that engine. It must represent contracts and transaction flows, apply reviewed Islamic-finance rules, cite evidence, expose uncertainty, and retain a qualified human decision. A generic score or an LLM explanation is not a Shariah certificate.

The first proof of concept should be narrow enough to validate the complete loop. A contract-review workbench is preferable to a broad autonomous checker: it can accept a real contract, extract claims and clauses, retrieve relevant rulings, identify missing evidence, and produce a review packet for a Shariah reviewer.

The International Islamic Fiqh Academy (IIFA) is the initial institutional source. Its official English resolutions index is https://iifa-aifi.org/en/resolutions. During this decision review, the official index exposed the 2024 ebook for Resolutions 1-255 and newer individual resolutions, including Resolution 262 (7/26), “Shari’ah Governance in Contemporary Islamic Financial Institutions,” and Resolution 259 (4/26), concerning an increment on a loan by a third party. The source must be ingested from the official publication and preserved as an immutable, versioned record.

## Decision

Build a **Fintech Shariah Contract Review Workbench** as the first product layer over Al-Furqan.

The workbench will:

1. Accept a structured product brief and uploaded contract documents.
2. Extract parties, contracts, clauses, assets, money flows, fees, risks, and lifecycle events.
3. Classify the proposed structure and retrieve applicable, reviewed IIFA resolutions and supporting sources.
4. Run deterministic Shariah-finance rules and formal consistency checks.
5. Use the LLM for extraction, question generation, and explanation only; it must not create an unsupported ruling or final approval.
6. Return cited findings, missing-information requests, remediation actions, confidence, disagreement flags, and a review status.
7. Require a qualified Shariah reviewer to approve, reject, correct, or escalate the assessment.
8. Preserve the complete evidence, model, rule, source, document, and reviewer audit trail.

The first supported product family will be **Murabaha financing**, with a deliberately small scope: asset ownership and possession, promise/order sequence, cost and markup disclosure, payment schedule, agency, collateral, default handling, late-payment amounts, and settlement/termination.

## IIFA source-of-truth policy

“IIFA source of truth” means authoritative institutional evidence for the IIFA corpus, not that the corpus replaces Qur’an, authentic Sunnah, usul al-fiqh, or qualified scholarly judgment.

Each source record must retain:

- Official URL and publication URL/PDF.
- IIFA resolution number, session, title, language, and publication date.
- Original Arabic content as the canonical text when available.
- Official English/French translations as translations, never silently substituted for Arabic.
- Retrieval timestamp, content hash, file hash, and parser/OCR version.
- Page and paragraph anchors for every extracted passage.
- Relationships to topics, contract types, rules, and affected findings.
- Ingestion state: discovered, downloaded, parsed, human-reviewed, published, superseded, or quarantined.
- Reviewer identity, review notes, and correction history.

Scraped or machine-translated text may support discovery but cannot become a published rule without source verification. A resolution may be retrieved automatically, but a final product conclusion remains subject to human Shariah review.

## Alternatives considered

### Continue with generic question evaluation

Rejected. It does not reliably expose contract mechanics or prove that a finding applies to the product.

### Build a broad autonomous “Shariah certificate” first

Rejected. It creates unacceptable authority, explainability, and governance risk before the domain model and evidence controls are validated.

### Start with a static checklist only

Rejected as the final architecture. A checklist is useful for the first deterministic rule pack, but it cannot represent alternative structures, evidence citations, uncertainty, or evolving institutional decisions by itself.

### Start with a website chat interface over the existing API

Rejected as the sole MVP. Chat is the interaction surface, not the product capability. The MVP will include chat, a structured review workspace, document evidence, deterministic checks, and a reviewer decision packet.

## Consequences

### Positive

- Preserves the generic engine while adding a clear fintech application boundary.
- Produces a useful first demo without claiming autonomous certification.
- Makes IIFA decisions searchable, versioned, citable, and reviewable.
- Creates a repeatable path to add Ijarah, Musharakah, Mudarabah, payments, crowdfunding, and digital assets later.
- Enables deterministic regression tests against approved cases.

### Negative

- Requires domain modeling and data curation before broad product coverage.
- A qualified Shariah review process remains a human dependency.
- Official documents may have inconsistent HTML/PDF structure, language coverage, or availability.
- The first version must explicitly report “insufficient evidence” rather than guessing.

## Acceptance criteria for this decision

- A Murabaha contract can be uploaded and represented as structured clauses and transaction events.
- Each blocking finding links to an exact source passage, rule version, and affected clause.
- The system distinguishes compliant, non-compliant, conditional, insufficient-evidence, and escalated outcomes.
- A reviewer can correct extraction and rule application per finding.
- Published IIFA records are immutable and reproducible from their recorded hash.
- No UI wording or API response represents an automated result as a final Shariah certificate.
