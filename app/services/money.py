"""Integer money arithmetic helpers.

Every monetary amount in this project is an **integer number of minor
units** of a single currency (UZS has no minor unit so "minor unit" == 1
UZS; USD minor unit == 1 cent; Telegram Stars (XTR) minor unit == 1 star).
Floats are never used for money anywhere in the codebase. Percentages are
stored as integers scaled by 100 ("basis": 1000 == 10.00%) to avoid float
rounding entirely, matching `PremiumPlan.standard_referral_percent`.

This module has zero external dependencies so it can be unit-tested
without a database, network, or any third-party package.
"""

from __future__ import annotations

PERCENT_BASIS = 10_000  # percent*100 stored as integer; 10000 == 100.00%


def percent_of(amount: int, percent_basis: int) -> int:
    """Return floor(amount * percent_basis / PERCENT_BASIS).

    Uses floor (banker-safe, never overpays) so that, e.g., 10.00% of 999
    minor units is 99, not 100 or 99.9. Rounding always favors the
    business/platform, never the recipient, to avoid slow balance drift.
    """
    if amount < 0:
        raise ValueError("amount must be >= 0")
    if percent_basis < 0:
        raise ValueError("percent_basis must be >= 0")
    return (amount * percent_basis) // PERCENT_BASIS


def apply_percent_discount(gross_amount: int, discount_percent: int) -> int:
    """Return the net amount payable after a whole-percent discount.

    `discount_percent` is a plain 0-100 integer (NOT the *100 basis used for
    referral rates) because promo discounts are specified in whole percent
    in the spec ("Discount is 10%"). Net amount is rounded UP (ceiling) so
    the platform never under-charges by a fraction of a minor unit; the
    issuer's cost-per-activation (see promo_math.py) is computed
    separately and is what determines their reserved liability.
    """
    if not (0 <= discount_percent <= 100):
        raise ValueError("discount_percent must be within 0..100")
    if gross_amount < 0:
        raise ValueError("gross_amount must be >= 0")
    discount_amount = ceil_div(gross_amount * discount_percent, 100)
    return gross_amount - discount_amount


def ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be > 0")
    if numerator < 0:
        raise ValueError("numerator must be >= 0")
    return -(-numerator // denominator)


def floor_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be > 0")
    if numerator < 0:
        raise ValueError("numerator must be >= 0")
    return numerator // denominator


class InsufficientFundsError(Exception):
    """Raised whenever a debit/reservation would push a balance below zero."""

    def __init__(self, available: int, requested: int, currency: str) -> None:
        self.available = available
        self.requested = requested
        self.currency = currency
        super().__init__(
            f"Insufficient funds: available={available} requested={requested} currency={currency}"
        )
