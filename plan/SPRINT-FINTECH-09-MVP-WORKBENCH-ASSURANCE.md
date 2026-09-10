# Sprint Fintech 09: MVP Review Workbench and Assurance Loop

**Goal:** Deliver the first usable website while proving end-to-end review reliability.

## Product shape

Build a web workbench with a chat interface, not a chat-only bot. The primary screen should combine:

- Conversation pane for questions and missing-information requests.
- Product/contract workspace with structured facts.
- Document viewer with clause anchors.
- Findings panel with severity, rule, citation, and remediation.
- Evidence drawer showing Arabic source, translation, resolution metadata, and hash/status.
- Reviewer decision controls and an exportable review packet.

## MVP scope

- One organization/project workspace.
- One uploaded Murabaha contract or product brief.
- IIFA resolutions corpus slice for Islamic finance plus supporting reviewed sources.
- Deterministic Murabaha rule pack.
- LLM-assisted extraction and explanation with citations.
- Human reviewer approval required.
- No public certification badge, autonomous approval, or broad product coverage.

## Assurance loop

- Create a curated benchmark of real-looking but anonymized Murabaha cases.
- Include compliant, non-compliant, incomplete, disputed, and adversarial documents.
- Record expected findings and reviewer rationale.
- Run regression tests on every rule, prompt, parser, source, or model change.
- Add monitoring for source changes, rule changes, document changes, extraction confidence, citation coverage, reviewer overrides, and processing failures.
- Provide a re-review queue when an IIFA source or rule version changes.

## Acceptance criteria

- A reviewer can complete a contract review from upload to decision packet in one workflow.
- Chat answers cite findings and ask for missing facts instead of guessing.
- The benchmark demonstrates deterministic rule behavior and records reviewer agreement.
- The website is usable on desktop and tablet and exposes no unsupported compliance claim.
- A source update, rule update, or contract version change creates a visible reassessment task.

## Tests

- Browser smoke test for upload, chat, finding review, citation opening, and report export.
- End-to-end Murabaha benchmark suite.
- Accessibility and authorization tests.
- Red-team tests for prompt injection in chat and documents.
- Source refresh and reassessment tests.

## Definition of done

The MVP is a **Shariah contract-review assistant with governed human approval**, not an automated Shariah certification authority.
