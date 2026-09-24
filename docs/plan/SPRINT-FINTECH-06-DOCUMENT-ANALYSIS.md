# Sprint Fintech 06: Contract and Product Document Analysis

**Goal:** Convert real fintech documents into reviewable, source-linked normalized facts.

## Deliverables

- Upload and malware/size/type validation for PDF, DOCX, HTML, and plain text.
- Text extraction with page, paragraph, table, and clause anchors.
- OCR quarantine and confidence thresholds.
- LLM extraction of parties, obligations, contracts, assets, fees, payment terms, penalties, ownership, risk, and events into the Product Model.
- Clause-to-fact links with quoted text and extraction confidence.
- Human correction workflow before rule execution.
- Document version comparison and changed-clause detection.

## Acceptance criteria

- No extracted fact is silently promoted to verified truth.
- Every fact has a document anchor or is labeled user-provided.
- A reviewer can correct a fact and rerun only affected rules.
- Re-uploading the same document is idempotent.

## Tests

- PDF/DOCX fixture extraction.
- Tables, Arabic text, and mixed-language tests.
- OCR low-confidence tests.
- Prompt-injection-in-document tests.
- Version-diff and selective re-evaluation tests.
