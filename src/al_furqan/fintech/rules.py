"""Deterministic Islamic-finance rule profiles.

The rule engine evaluates normalized facts only. It does not call an LLM and
it does not issue a religious certificate; its output is a review artifact for
qualified Shariah governance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from al_furqan.fintech.models import FintechProduct, MurabahaTerms, ProductType


class RuleState(str, Enum):
    """Outcome of one deterministic rule evaluation."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"
    NOT_APPLICABLE = "not_applicable"


class FindingSeverity(str, Enum):
    """Review severity of a rule result."""

    BLOCKING = "blocking"
    ADVISORY = "advisory"


class ReviewStatus(str, Enum):
    """Aggregated product-review status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTED = "conflicted"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class RuleDefinition:
    """Versioned metadata and executable condition for a rule."""

    rule_id: str
    version: str
    profile: ProductType
    title: str
    scope: str
    prerequisites: tuple[str, ...]
    prohibited_condition: str
    exceptions: tuple[str, ...]
    severity: FindingSeverity
    evidence_requirements: tuple[str, ...]
    remediation: str
    evaluate: Callable[[FintechProduct], "RuleResult"]


@dataclass(frozen=True)
class RuleResult:
    """Auditable result of evaluating one rule."""

    rule_id: str
    rule_version: str
    state: RuleState
    severity: FindingSeverity
    title: str
    summary: str
    missing_facts: tuple[str, ...] = ()
    affected_clause_ids: tuple[str, ...] = ()
    affected_event_ids: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    remediation: str = ""

    @property
    def is_blocking_failure(self) -> bool:
        """Whether this result blocks a compliant aggregate status."""
        return self.state in {RuleState.FAIL, RuleState.CONFLICT} and self.severity is FindingSeverity.BLOCKING


@dataclass(frozen=True)
class RuleEvaluation:
    """Complete deterministic evaluation and aggregate decision."""

    product_id: str
    profile: ProductType
    profile_version: str
    status: ReviewStatus
    results: tuple[RuleResult, ...]

    @property
    def passed(self) -> bool:
        """Whether all applicable rules pass with no missing facts."""
        return self.status is ReviewStatus.COMPLIANT



def _terms(product: FintechProduct) -> MurabahaTerms | None:
    return product.murabaha_terms


def _fact_rule(
    product: FintechProduct,
    definition: RuleDefinition,
    fact_name: str,
    *,
    passing_summary: str,
    failing_summary: str,
) -> RuleResult:
    terms = _terms(product)
    value = getattr(terms, fact_name, None) if terms else None
    if value is None:
        return _result(
            definition,
            RuleState.UNKNOWN,
            f"Evidence is required for {fact_name.replace('_', ' ')}.",
            missing_facts=(fact_name,),
        )
    return _result(
        definition,
        RuleState.PASS if value else RuleState.FAIL,
        passing_summary if value else failing_summary,
    )


def _result(
    definition: RuleDefinition,
    state: RuleState,
    summary: str,
    *,
    missing_facts: tuple[str, ...] = (),
) -> RuleResult:
    return RuleResult(
        rule_id=definition.rule_id,
        rule_version=definition.version,
        state=state,
        severity=definition.severity,
        title=definition.title,
        summary=summary,
        missing_facts=missing_facts,
        evidence_requirements=definition.evidence_requirements,
        remediation=definition.remediation,
    )


def _late_payment_rule(product: FintechProduct, definition: RuleDefinition) -> RuleResult:
    terms = _terms(product)
    if terms is None:
        return _result(definition, RuleState.UNKNOWN, "Late-payment treatment is not documented.", missing_facts=("murabaha_terms",))
    income = terms.late_payment_amount_is_income
    charity = terms.late_payment_amount_to_charity
    time_increase = terms.default_amount_increases_with_time
    if income is True and charity is True:
        return _result(definition, RuleState.CONFLICT, "The product marks the late amount as both income and charitable disposition.")
    if income is None or charity is None or time_increase is None:
        missing = tuple(
            name
            for name, value in (
                ("late_payment_amount_is_income", income),
                ("late_payment_amount_to_charity", charity),
                ("default_amount_increases_with_time", time_increase),
            )
            if value is None
        )
        return _result(definition, RuleState.UNKNOWN, "Late-payment treatment is incomplete.", missing_facts=missing)
    if income or time_increase:
        return _result(definition, RuleState.FAIL, "Late-payment treatment contains a blocking time-based or income condition.")
    return _result(definition, RuleState.PASS, "Late-payment treatment does not identify income or a time-based increase.")


def _profile_rules() -> tuple[RuleDefinition, ...]:
    common = {
        "version": "1.0.0",
        "profile": ProductType.murabaha,
        "scope": "Murabaha financing product facts",
        "prerequisites": ("product_type=murabaha",),
        "exceptions": (),
        "severity": FindingSeverity.BLOCKING,
        "evidence_requirements": ("contract_clause_or_verified_product_fact",),
    }
    specs = [
        ("MURABAHA-001", "Asset ownership before sale", "asset ownership exists before resale", "selling an asset before ownership is established", "Document acquisition and ownership before sale.", "asset_owned_before_sale", "Ownership before resale is documented.", "Ownership before resale is not established."),
        ("MURABAHA-002", "Asset possession before sale", "constructive or physical possession exists before resale", "resale occurs before possession", "Provide possession or qabd evidence before sale.", "asset_possessed_before_sale", "Possession before resale is documented.", "Possession before resale is not established."),
        ("MURABAHA-003", "Cost disclosure", "original cost is disclosed to the buyer", "cost is hidden or unavailable", "Add the original cost disclosure to the contract.", "cost_disclosed", "Original cost disclosure is documented.", "Original cost disclosure is not documented."),
        ("MURABAHA-004", "Fixed markup", "markup is fixed and disclosed", "markup is variable or undefined", "Define and disclose the markup in the sale contract.", "markup_fixed", "Markup is fixed.", "Markup is not fixed or documented."),
        ("MURABAHA-005", "Fixed sale price", "sale price is fixed at contract", "price changes by reference to elapsed time after contract", "Fix the deferred sale price at contract formation.", "price_fixed_at_contract", "Sale price is fixed at contract.", "Sale price is not fixed at contract."),
        ("MURABAHA-006", "Payment schedule", "installments and due dates are defined", "payment schedule is open-ended", "Document installment amounts and due dates.", "payment_schedule_fixed", "Payment schedule is defined.", "Payment schedule is not defined."),
        ("MURABAHA-007", "Agency disclosure", "agency arrangement is disclosed where used", "agency is used but undisclosed", "Document the agency role and sequence.", "agency_disclosed", "Agency facts are disclosed or no agency is asserted.", "Agency treatment is not disclosed."),
        ("MURABAHA-008", "Collateral definition", "collateral and enforcement terms are defined", "collateral is undefined or unlimited", "Define collateral scope and enforcement terms.", "collateral_defined", "Collateral treatment is defined.", "Collateral treatment is not defined."),
        ("MURABAHA-009", "Late-payment treatment", "late amounts do not become lender income or increase solely with time", "late amount becomes income or increases solely with time", "Remove prohibited income treatment and document approved disposition.", None, None, None),
        ("MURABAHA-010", "Settlement terms", "settlement and rebate treatment are defined", "settlement is undefined or an automatic rebate is represented as contractual entitlement", "Document settlement and rebate treatment for review.", "settlement_terms_defined", "Settlement terms are defined.", "Settlement terms are not defined."),
    ]
    rules: list[RuleDefinition] = []
    for rule_id, title, scope, prohibited, remediation, fact_name, passing, failing in specs:
        evaluator = _late_payment_rule if rule_id == "MURABAHA-009" else None
        definition = RuleDefinition(
            **common,
            rule_id=rule_id,
            title=title,
            prohibited_condition=prohibited,
            remediation=remediation,
            evaluate=evaluator or (lambda product, fact=fact_name, p=passing, f=failing, d=None: _fact_rule(product, d, fact, passing_summary=p, failing_summary=f)),
        )
        # Bind the definition after construction so the shared evaluator keeps
        # the complete immutable metadata in every result.
        if evaluator is None:
            definition = RuleDefinition(**{**definition.__dict__, "evaluate": lambda product, fact=fact_name, p=passing, f=failing, d=definition: _fact_rule(product, d, fact, passing_summary=p, failing_summary=f)})
        else:
            definition = RuleDefinition(**{**definition.__dict__, "evaluate": lambda product, d=definition: _late_payment_rule(product, d)})
        rules.append(definition)
    return tuple(rules)


MURABAHA_RULES = _profile_rules()
RULE_PROFILES: dict[ProductType, tuple[RuleDefinition, ...]] = {ProductType.murabaha: MURABAHA_RULES}


def evaluate_product(product: FintechProduct) -> RuleEvaluation:
    """Evaluate a normalized product using its registered deterministic profile."""
    normalized = product.normalized()
    rules = RULE_PROFILES.get(normalized.product_type)
    if not rules:
        return RuleEvaluation(normalized.id or "unknown", normalized.product_type, "1.0.0", ReviewStatus.NOT_APPLICABLE, ())
    results = tuple(rule.evaluate(normalized) for rule in rules)
    if any(result.state is RuleState.CONFLICT for result in results):
        status = ReviewStatus.CONFLICTED
    elif any(result.is_blocking_failure for result in results):
        status = ReviewStatus.NON_COMPLIANT
    elif any(result.state is RuleState.UNKNOWN for result in results):
        status = ReviewStatus.INSUFFICIENT_EVIDENCE
    else:
        status = ReviewStatus.COMPLIANT
    return RuleEvaluation(normalized.id or "unknown", normalized.product_type, "1.0.0", status, results)
