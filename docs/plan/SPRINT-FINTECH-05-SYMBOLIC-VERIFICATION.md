# Sprint Fintech 05: Contract Logic and Symbolic Verification

**Goal:** Extend formal verification from generic axioms to normalized fintech contract facts.

## Deliverables

- Predicate vocabulary for ownership, possession, sale, loan, fee, interest, risk, guarantee, penalty, agency, and sequence.
- Z3 constraints for Murabaha ordering and ownership conditions.
- Proof/contradiction result linked to predicates, clauses, and rule IDs.
- Separation between satisfiable facts and Shariah judgment: SAT means logically consistent, not compliant.
- Explicit UNKNOWN result for incomplete or solver-inconclusive cases.
- Predicate extraction audit record.

## Acceptance criteria

- The verifier detects impossible transaction sequences and contradictory ownership claims.
- A logically consistent contract can still fail a Shariah rule.
- Z3 output never overrides a blocking deterministic rule or human decision.
- Hardcoded placeholder predicates are removed from the fintech evaluation path.

## Tests

- SAT, UNSAT, and UNKNOWN fixtures.
- Transaction-order tests.
- Contradiction-core tests.
- Separation-of-concerns tests proving that Z3 consistency is not compliance approval.
