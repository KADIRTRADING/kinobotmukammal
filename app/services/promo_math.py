"""Prepaid promo-code funding math (spec section 7).

Two promo kinds:
  - FULL_PREMIUM: each activation costs the issuer the full plan price.
  - PERCENT_DISCOUNT: each activation costs the issuer only the discounted
    amount (e.g. 10% of price), while the redeemer pays the remainder
    through an allowed payment flow.

`max_activations_for_budget` answers "how many activations can the issuer
afford with balance X", which is what the code-creation UI uses to let a
user choose an activation count up to their affordable maximum before
reserving funds.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.money import apply_percent_discount, floor_div


@dataclass(frozen=True)
class PromoFundingQuote:
    plan_price: int
    discount_percent: int
    cost_per_activation: int
    max_activations_affordable: int
    requested_activations: int
    total_reserved_amount: int
    buyer_pays_per_activation: int
    sufficient_funds: bool
    balance_before: int
    balance_after: int


def cost_per_activation(plan_price: int, discount_percent: int, full_premium: bool) -> int:
    """What ONE redemption costs the issuer.

    - full_premium=True (FULL_PREMIUM code): the issuer pays the entire
      plan price per activation, discount_percent is ignored.
    - full_premium=False (PERCENT_DISCOUNT code): the issuer pays exactly
      the discount amount (e.g. 10% of 5,000 = 500), matching spec
      section 7's worked example precisely.
    """
    if full_premium:
        return plan_price
    net_after_discount = apply_percent_discount(plan_price, discount_percent)
    return plan_price - net_after_discount


def buyer_amount_due(plan_price: int, discount_percent: int, full_premium: bool) -> int:
    """What the redeemer must still pay through an allowed payment flow."""
    if full_premium:
        return 0
    return apply_percent_discount(plan_price, discount_percent)


def max_activations_for_budget(balance: int, per_activation_cost: int) -> int:
    if per_activation_cost <= 0:
        raise ValueError("per_activation_cost must be > 0")
    if balance < 0:
        raise ValueError("balance must be >= 0")
    return floor_div(balance, per_activation_cost)


def quote_promo_funding(
    *,
    plan_price: int,
    discount_percent: int,
    full_premium: bool,
    requested_activations: int,
    issuer_balance: int,
) -> PromoFundingQuote:
    if requested_activations <= 0:
        raise ValueError("requested_activations must be > 0")

    per_activation = cost_per_activation(plan_price, discount_percent, full_premium)
    buyer_due = buyer_amount_due(plan_price, discount_percent, full_premium)
    max_affordable = (
        max_activations_for_budget(issuer_balance, per_activation)
        if per_activation > 0
        else requested_activations
    )
    total_reserved = per_activation * requested_activations
    sufficient = total_reserved <= issuer_balance

    return PromoFundingQuote(
        plan_price=plan_price,
        discount_percent=0 if full_premium else discount_percent,
        cost_per_activation=per_activation,
        max_activations_affordable=max_affordable,
        requested_activations=requested_activations,
        total_reserved_amount=total_reserved,
        buyer_pays_per_activation=buyer_due,
        sufficient_funds=sufficient,
        balance_before=issuer_balance,
        balance_after=issuer_balance - total_reserved if sufficient else issuer_balance,
    )
