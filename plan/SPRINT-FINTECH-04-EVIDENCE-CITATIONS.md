# Sprint Fintech 04: Evidence-Grounded Findings

**Goal:** Make every material finding traceable to a source passage and an extracted product fact.

## Deliverables

- Citation model for source, passage, page/anchor, language, hash, rule, and relevance.
- Finding model: issue, severity, affected clause/event, rule, evidence, confidence, disagreement, and remediation.
- Citation validator that rejects nonexistent, unpublished, or weakly anchored references.
- Explicit reasoning-basis labels distinguishing source text, scholarly interpretation, system inference, and reviewer judgment.
- Grounded prompt contract requiring citations for explanatory text.
- Evidence coverage metrics: cited findings, unsupported claims, and unresolved evidence requests.
- API and report serialization for citations.

## Acceptance criteria

- A finding without valid evidence cannot be marked final.
- The UI can open the source passage associated with a finding.
- Arabic source text remains available beside any translation.
- Explanations distinguish source text, scholarly interpretation, system inference, and reviewer judgment.

## Implementation status

The evidence and finding models, manifest-backed citation validator, publication,
hash, anchor, translation-label, and evidence-coverage checks are implemented in
`src/al_furqan/fintech/evidence.py`. UI opening and HTTP report wiring remain
dependent on the review workbench endpoint.

## Tests

- Invalid citation and stale-hash tests.
- Citation coverage tests.
- Translation-label tests.
- Finding-to-clause and finding-to-source round trips.
