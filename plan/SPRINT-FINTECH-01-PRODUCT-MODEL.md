# Sprint Fintech 01: Product and Contract Model

**Goal:** Add a structured fintech product representation above the generic reasoning engine.

## Deliverables

- Pydantic/domain models for product, parties, contracts, assets, cash flows, fees, risks, collateral, events, and jurisdictions.
- Murabaha profile with required and optional fields.
- Stable identifiers for products, contract versions, clauses, and transaction events.
- API request schema that accepts structured data alongside chat text.
- Validation for missing, contradictory, or unverifiable facts.
- Fixture products: valid candidate, obvious riba case, and incomplete case.

## Acceptance criteria

- The same product produces the same normalized representation regardless of input order.
- Every finding can refer to a clause or transaction event identifier.
- Missing evidence is represented explicitly; it is never inferred as a compliant fact.
- Existing generic `/evaluate` behavior remains backward compatible.

## Tests

- Schema validation and round-trip serialization.
- Contract version/diff tests.
- Required-field and contradiction tests.
- API compatibility tests.
