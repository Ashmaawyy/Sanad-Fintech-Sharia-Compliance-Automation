"""Tests for the Sprint Fintech 01 product model."""

import pytest
from pydantic import ValidationError

from al_furqan.api.schemas import EvaluateRequest
from al_furqan.fintech.models import FintechProduct, ProductType


@pytest.fixture
def murabaha_product() -> FintechProduct:
    """A minimal product with intentionally unordered collections."""
    return FintechProduct(
        name="Home Murabaha",
        version="2026.1",
        product_type=ProductType.murabaha,
        currency="USD",
        parties=[
            {"id": "customer", "name": "Customer", "role": "buyer"},
            {"id": "bank", "name": "Bank", "role": "seller"},
        ],
        assets=[{"description": "Commodity", "asset_type": "commodity"}],
        contracts=[
            {
                "id": "sale",
                "name": "Murabaha sale",
                "contract_type": "murabaha",
                "parties": ["bank", "customer"],
            }
        ],
        clauses=[
            {
                "id": "price",
                "title": "Deferred price",
                "text": "The disclosed cost and markup form the sale price.",
                "contract_id": "sale",
            }
        ],
        cash_flows=[
            {
                "from_party": "customer",
                "to_party": "bank",
                "amount": 120000,
                "currency": "USD",
                "purpose": "deferred sale installments",
            }
        ],
        events=[
            {
                "sequence": 1,
                "name": "Bank acquires asset",
                "actor": "bank",
                "description": "Bank acquires and takes possession before sale.",
            }
        ],
    )


def test_normalization_assigns_stable_ids_and_is_order_independent(murabaha_product):
    """Equivalent products have identical canonical representations."""
    normalized = murabaha_product.normalized()
    reordered = murabaha_product.model_copy(
        update={
            "parties": list(reversed(murabaha_product.parties)),
            "cash_flows": list(reversed(murabaha_product.cash_flows)),
        }
    )

    assert normalized.id.startswith("product_")
    assert all(item.id for item in normalized.assets)
    assert all(item.id for item in normalized.events)
    assert normalized.canonical_json() == reordered.canonical_json()


def test_unknown_references_are_rejected():
    """A product cannot silently point to an absent party or clause."""
    with pytest.raises(ValidationError, match="unknown party"):
        FintechProduct(
            name="Invalid product",
            product_type=ProductType.murabaha,
            parties=[{"id": "bank", "name": "Bank", "role": "seller"}],
            contracts=[
                {
                    "name": "Sale",
                    "contract_type": "murabaha",
                    "parties": ["missing-customer"],
                }
            ],
        )


def test_missing_evidence_is_not_inferred_as_compliance(murabaha_product):
    """The model preserves absent facts as null/empty values."""
    normalized = murabaha_product.normalized()

    assert normalized.assets[0].ownership_holder is None
    assert normalized.assets[0].possession_holder is None
    assert normalized.assets[0].prohibited_activity is None


def test_generic_evaluation_request_remains_backward_compatible():
    """Existing question-only requests still validate."""
    request = EvaluateRequest(question="Is this contract permissible?")

    assert request.product is None


def test_evaluation_request_accepts_structured_product(murabaha_product):
    """The API boundary accepts product facts alongside chat text."""
    request = EvaluateRequest(
        question="Review this Murabaha product.",
        product=murabaha_product.model_dump(mode="json"),
    )

    assert request.product is not None
    assert request.product.product_type is ProductType.murabaha
