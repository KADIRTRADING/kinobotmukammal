import pytest

from app.services.promo_math import (
    buyer_amount_due,
    cost_per_activation,
    max_activations_for_budget,
    quote_promo_funding,
)


def test_full_premium_code_cost_per_activation_worked_example():
    # Spec section 7: premium costs 5,000 UZS; full-premium code costs the
    # issuer the full price per activation.
    assert cost_per_activation(5000, discount_percent=0, full_premium=True) == 5000


def test_full_premium_code_max_activations_worked_example():
    # 100,000 UZS balance / 5,000 per activation = 20 activations.
    assert max_activations_for_budget(100_000, 5000) == 20


def test_full_premium_buyer_pays_nothing():
    assert buyer_amount_due(5000, discount_percent=0, full_premium=True) == 0


def test_discount_code_cost_per_activation_worked_example():
    # 10% discount on 5,000 UZS costs the issuer 500 UZS/activation.
    assert cost_per_activation(5000, discount_percent=10, full_premium=False) == 500


def test_discount_code_max_activations_worked_example():
    # 100,000 UZS balance / 500 per activation = 200 activations.
    assert max_activations_for_budget(100_000, 500) == 200


def test_discount_code_buyer_pays_remainder():
    assert buyer_amount_due(5000, discount_percent=10, full_premium=False) == 4500


def test_quote_full_premium_20_activations_reserves_exactly_100000():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=0,
        full_premium=True,
        requested_activations=20,
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is True
    assert quote.total_reserved_amount == 100_000
    assert quote.balance_after == 0
    assert quote.max_activations_affordable == 20


def test_quote_discount_200_activations_reserves_exactly_100000():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=10,
        full_premium=False,
        requested_activations=200,
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is True
    assert quote.total_reserved_amount == 100_000
    assert quote.balance_after == 0
    assert quote.buyer_pays_per_activation == 4500


def test_quote_rejects_when_insufficient_funds():
    quote = quote_promo_funding(
        plan_price=5000,
        discount_percent=0,
        full_premium=True,
        requested_activations=21,  # would need 105,000 but only has 100,000
        issuer_balance=100_000,
    )
    assert quote.sufficient_funds is False
    # Balance must NOT be reduced when rejected.
    assert quote.balance_after == quote.balance_before == 100_000


def test_max_activations_for_budget_rejects_non_positive_cost():
    with pytest.raises(ValueError):
        max_activations_for_budget(1000, 0)


def test_quote_requires_positive_activation_count():
    with pytest.raises(ValueError):
        quote_promo_funding(
            plan_price=5000,
            discount_percent=10,
            full_premium=False,
            requested_activations=0,
            issuer_balance=1000,
        )
