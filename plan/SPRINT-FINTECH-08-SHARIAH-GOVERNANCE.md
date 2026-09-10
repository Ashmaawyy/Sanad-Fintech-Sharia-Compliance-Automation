# Sprint Fintech 08: Shariah Governance and Human Review

**Goal:** Make qualified human review a first-class control rather than an afterthought.

## Deliverables

- Reviewer profiles, qualifications, affiliation, and conflict-of-interest declaration.
- Per-finding approve, reject, correct, defer, and escalate actions.
- Required second review for blocking or disputed findings.
- Madhhab/standard/context selection and visible scope.
- IIFA source-review workflow and correction log.
- Approval, expiry, supersession, and change-triggered reassessment.
- Role-based permissions and signed review events.

## Acceptance criteria

- The system cannot issue a final product decision without the required reviewer action.
- Reviewer changes preserve the original machine output and evidence.
- Disagreement is represented, not collapsed into a single confidence score.
- A product change invalidates or flags affected prior approvals.

## Tests

- Role and permission tests.
- Required-review and dual-review tests.
- Conflict-of-interest blocking tests.
- Approval expiry and supersession tests.
- Full audit-trail reconstruction tests.
