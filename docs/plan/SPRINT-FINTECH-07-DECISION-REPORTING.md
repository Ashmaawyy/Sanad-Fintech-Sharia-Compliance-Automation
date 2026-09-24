# Sprint Fintech 07: Compliance Decision and Reporting Model

**Goal:** Replace generic scores as the primary product outcome with an auditable compliance decision model.

## Deliverables

- Status enum: compliant, non-compliant, conditionally-compliant, insufficient-evidence, disputed, escalated, and draft.
- Blocking versus advisory finding severity.
- Deterministic aggregation rules; no score-only auto-approval.
- Remediation plan with owner, required evidence, due date, and verification state.
- Versioned review report in JSON and human-readable HTML/PDF.
- API endpoints for review packet, findings, evidence, remediation, and decision history.
- Explicit disclaimer that automated review is not a Shariah certificate.

## Acceptance criteria

- One blocking finding makes the result non-compliant or escalated until resolved.
- Any unresolved required fact yields insufficient evidence.
- Reports contain product/document/rule/source/model/reviewer versions.
- A final decision is immutable after approval; corrections create a new version.

## Tests

- Aggregation matrix tests.
- Report completeness tests.
- Immutable decision-history tests.
- Backward-compatible generic verdict tests.
