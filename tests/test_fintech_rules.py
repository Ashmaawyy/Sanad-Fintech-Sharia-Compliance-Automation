"""Focused tests for the Sprint Fintech 02 rule engine."""

import pytest

from al_furqan.fintech.models import FintechProduct, MurabahaTerms, ProductType
from al_furqan.fintech.rules import (
    ReviewStatus,
    RuleState,
    evaluate_product,
)


def product_with_terms(**updates) -> FintechProduct:
    """Build a complete candidate with explicit Murabaha facts."""
    terms = {
        "asset_owned_before_sale": True,
        "asset_possessed_before_sale": True,
        "cost_disclosed": True,
        "markup_fixed": True,
        "price_fixed_at_contract": True,
        "payment_schedule_fixed": True,
        "agency_disclosed": True,
        "collateral_defined": True,
        "late_payment_amount_to_charity": True,
        "late_payment_amount_is_income": False,
        "default_amount_increases_with_time": False,
        "settlement_terms_defined": True,
        "settlement_rebate_is_discretionary": True,
    }
    terms.update(updates)
    return FintechProduct(
        name="Rule fixture",
        product_type=ProductType.murabaha,
        murabaha_terms=MurabahaTerms(**terms),
    )


def test_complete_candidate_is_compliant():
    """A complete passing fixture reaches compliant status."""
    evaluation = evaluate_product(product_with_terms())

    assert evaluation.status is ReviewStatus.COMPLIANT
    assert len(evaluation.results) == 10
    assert all(result.state is RuleState.PASS for result in evaluation.results)


@pytest.mark.parametrize(
    "field",
    [
        "asset_owned_before_sale",
        "asset_possessed_before_sale",
        "cost_disclosed",
        "markup_fixed",
        "price_fixed_at_contract",
        "payment_schedule_fixed",
        "settlement_terms_defined",
    ],
)
def test_failed_blocking_rule_prevents_compliance(field):
    """A failed blocking condition produces non-compliant status."""
    evaluation = evaluate_product(product_with_terms(**{field: False}))

    assert evaluation.status is ReviewStatus.NON_COMPLIANT
    assert any(result.state is RuleState.FAIL for result in evaluation.results)


def test_unknown_fact_produces_insufficient_evidence():
    """Missing facts never become an implicit pass."""
    evaluation = evaluate_product(FintechProduct(name="Incomplete", product_type=ProductType.murabaha))

    assert evaluation.status is ReviewStatus.INSUFFICIENT_EVIDENCE
    assert all(result.state is RuleState.UNKNOWN for result in evaluation.results)


def test_conflicting_late_payment_facts_are_exposed():
    """Contradictory source facts are distinct from a normal failure."""
    evaluation = evaluate_product(
        product_with_terms(
            late_payment_amount_is_income=True,
            late_payment_amount_to_charity=True,
        )
    )

    late_rule = next(result for result in evaluation.results if result.rule_id == "MURABAHA-009")
    assert evaluation.status is ReviewStatus.CONFLICTED
    assert late_rule.state is RuleState.CONFLICT


def test_other_profile_is_not_applicable():
    """Unregistered profiles do not accidentally run Murabaha rules."""
    evaluation = evaluate_product(FintechProduct(name="Other", product_type=ProductType.other))

    assert evaluation.status is ReviewStatus.NOT_APPLICABLE
    assert evaluation.results == ()


def test_rule_results_include_evidence_and_remediation():
    """Every rule result remains actionable for the review UI."""
    evaluation = evaluate_product(product_with_terms(asset_owned_before_sale=False))
    failed = next(result for result in evaluation.results if result.rule_id == "MURABAHA-001")

    assert failed.evidence_requirements
    assert failed.remediation
    assert failed.rule_version == "1.0.0"
