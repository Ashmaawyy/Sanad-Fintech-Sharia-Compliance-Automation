# Sprint Fintech 02: Islamic-Finance Rule Engine

**Goal:** Implement deterministic, versioned rules for the first product family: Murabaha financing.

## Deliverables

- Rule model with identifier, scope, prerequisites, prohibited condition, exceptions, severity, evidence requirements, and remediation.
- Initial rules for riba, ownership, possession/qabd, cost-plus markup, agency, payment schedule, collateral, default, late-payment amounts, and settlement.
- Product-profile rule registry so later profiles can add Ijarah, Salam, Istisna, Musharakah, Mudarabah, Wakalah, Qard, Kafalah, and Rahn without changing the core engine.
- Rule evaluation result with pass, fail, unknown, conflict, and not-applicable states.
- Rule and profile versioning.

## Acceptance criteria

- Rules execute without an LLM once normalized facts are available.
- A failed blocking rule prevents a “compliant” result.
- Unknown facts produce insufficient evidence, not a pass.
- Every rule has an evidence requirement and test fixture.

## Tests

- Table-driven rule tests for positive, negative, boundary, and missing-data cases.
- Cross-rule conflict tests.
- Regression snapshots for approved reviewer outcomes.
