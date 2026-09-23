"""Structured fintech product models for Shariah review.

These models describe facts supplied by a product team or extracted from a
contract. They do not determine compliance. Rule evaluation and qualified
Shariah review consume the normalized representation.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductType(str, Enum):
    """Supported product profile identifiers."""

    murabaha = "murabaha"
    other = "other"


class MurabahaTerms(BaseModel):
    """Structured facts required by the initial Murabaha rule profile."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    asset_owned_before_sale: bool | None = None
    asset_possessed_before_sale: bool | None = None
    cost_disclosed: bool | None = None
    markup_fixed: bool | None = None
    price_fixed_at_contract: bool | None = None
    payment_schedule_fixed: bool | None = None
    agency_disclosed: bool | None = None
    collateral_defined: bool | None = None
    late_payment_amount_to_charity: bool | None = None
    late_payment_amount_is_income: bool | None = None
    default_amount_increases_with_time: bool | None = None
    settlement_terms_defined: bool | None = None
    settlement_rebate_is_discretionary: bool | None = None


class _Entity(BaseModel):
    """Base model with stable serialization settings."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str | None = Field(default=None, min_length=1, max_length=200)


class Party(_Entity):
    """A participant and its contractual role."""

    name: str = Field(..., min_length=1, max_length=300)
    role: str = Field(..., min_length=1, max_length=100)


class Asset(_Entity):
    """The asset or service underlying a transaction."""

    description: str = Field(..., min_length=1, max_length=2000)
    asset_type: str = Field(..., min_length=1, max_length=100)
    ownership_holder: str | None = None
    possession_holder: str | None = None
    prohibited_activity: bool | None = None


class Fee(_Entity):
    """A fee or charge, including its trigger and recipient."""

    name: str = Field(..., min_length=1, max_length=200)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    calculation: str | None = Field(default=None, max_length=1000)
    trigger: str = Field(..., min_length=1, max_length=500)
    recipient: str | None = None
    purpose: str | None = Field(default=None, max_length=1000)


class CashFlow(_Entity):
    """A money movement in the product lifecycle."""

    from_party: str = Field(..., min_length=1, max_length=200)
    to_party: str = Field(..., min_length=1, max_length=200)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    purpose: str = Field(..., min_length=1, max_length=500)
    event_id: str | None = None
    is_contingent_on_time: bool | None = None


class Clause(_Entity):
    """A contract clause that can be cited by a finding."""

    text: str = Field(..., min_length=1, max_length=10000)
    title: str | None = Field(default=None, max_length=300)
    contract_id: str | None = None
    source_reference: str | None = Field(default=None, max_length=500)


class ContractEvent(_Entity):
    """An ordered lifecycle event in the transaction."""

    sequence: int = Field(..., ge=0)
    name: str = Field(..., min_length=1, max_length=200)
    actor: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    prerequisites: list[str] = Field(default_factory=list)


class Contract(_Entity):
    """A contract in the product structure."""

    name: str = Field(..., min_length=1, max_length=300)
    contract_type: str = Field(..., min_length=1, max_length=100)
    parties: list[str] = Field(default_factory=list)
    clause_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)


class Risk(_Entity):
    """A stated risk and the party bearing it."""

    description: str = Field(..., min_length=1, max_length=2000)
    bearer: str | None = None
    mitigation: str | None = Field(default=None, max_length=2000)


class EvidenceTrace(BaseModel):
    """Public, reviewable reasoning trace for the MVP UI.

    This intentionally contains evidence and rationale, not hidden model
    chain-of-thought or raw internal deliberation.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    step: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1, max_length=4000)
    clause_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


class FintechProduct(BaseModel):
    """Normalized product facts supplied for a Shariah review."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str | None = Field(default=None, min_length=1, max_length=200)
    name: str = Field(..., min_length=1, max_length=300)
    version: str = Field(default="1", min_length=1, max_length=50)
    product_type: ProductType = ProductType.other
    murabaha_terms: MurabahaTerms | None = None
    jurisdiction: str | None = Field(default=None, max_length=200)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    parties: list[Party] = Field(default_factory=list)
    assets: list[Asset] = Field(default_factory=list)
    contracts: list[Contract] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    cash_flows: list[CashFlow] = Field(default_factory=list)
    fees: list[Fee] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    events: list[ContractEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "FintechProduct":
        """Reject references to entities that are not in this product."""
        party_ids = {item.id for item in self.parties if item.id}
        contract_ids = {item.id for item in self.contracts if item.id}
        clause_ids = {item.id for item in self.clauses if item.id}
        event_ids = {item.id for item in self.events if item.id}

        errors: list[str] = []
        for contract in self.contracts:
            errors.extend(
                f"contract {contract.id or contract.name} references unknown party {ref}"
                for ref in contract.parties
                if party_ids and ref not in party_ids
            )
            errors.extend(
                f"contract {contract.id or contract.name} references unknown clause {ref}"
                for ref in contract.clause_ids
                if clause_ids and ref not in clause_ids
            )
            errors.extend(
                f"contract {contract.id or contract.name} references unknown event {ref}"
                for ref in contract.event_ids
                if event_ids and ref not in event_ids
            )
        for flow in self.cash_flows:
            if party_ids and (flow.from_party not in party_ids or flow.to_party not in party_ids):
                errors.append(f"cash flow {flow.id or flow.purpose} references an unknown party")
            if flow.event_id and event_ids and flow.event_id not in event_ids:
                errors.append(f"cash flow {flow.id or flow.purpose} references unknown event {flow.event_id}")

        if errors:
            raise ValueError("; ".join(errors))
        if self.product_type is ProductType.murabaha and self.murabaha_terms is None:
            # The profile may be incomplete, but the missing fact must remain
            # visible to the rule engine as insufficient evidence.
            return self
        return self

    def normalized(self) -> "FintechProduct":
        """Return a deterministic copy with stable IDs and sorted collections."""
        data = self.model_dump(mode="json", exclude_none=True)
        data = _assign_ids(data)
        data["parties"] = sorted(data.get("parties", []), key=lambda item: item["id"])
        data["assets"] = sorted(data.get("assets", []), key=lambda item: item["id"])
        data["contracts"] = sorted(data.get("contracts", []), key=lambda item: item["id"])
        data["clauses"] = sorted(data.get("clauses", []), key=lambda item: item["id"])
        data["cash_flows"] = sorted(data.get("cash_flows", []), key=lambda item: item["id"])
        data["fees"] = sorted(data.get("fees", []), key=lambda item: item["id"])
        data["risks"] = sorted(data.get("risks", []), key=lambda item: item["id"])
        data["events"] = sorted(data.get("events", []), key=lambda item: (item.get("sequence", 0), item["id"]))
        product_payload = {key: value for key, value in data.items() if key != "id"}
        data["id"] = self.id or _stable_id("product", product_payload)
        return FintechProduct.model_validate(data)

    def canonical_json(self) -> str:
        """Serialize the normalized product for hashing, storage, and diffs."""
        return json.dumps(
            self.normalized().model_dump(mode="json", exclude_none=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


def _stable_id(prefix: str, value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _assign_ids(data: dict[str, Any]) -> dict[str, Any]:
    """Assign IDs from entity content, excluding mutable references."""
    prefixes = {
        "parties": "party",
        "assets": "asset",
        "contracts": "contract",
        "clauses": "clause",
        "cash_flows": "flow",
        "fees": "fee",
        "risks": "risk",
        "events": "event",
    }
    for collection, prefix in prefixes.items():
        for item in data.get(collection, []):
            if not item.get("id"):
                item["id"] = _stable_id(prefix, {key: value for key, value in item.items() if key != "id"})
    return data
