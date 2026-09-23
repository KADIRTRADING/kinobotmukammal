"""Referral commission calculation (spec section 5, standard referrer).

Pure functions only -- no DB/network access -- so every plan's independent
commission percentage, the first-purchase-only vs. renewals policy, and
refund reversal math can be tested directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.money import percent_of


@dataclass(frozen=True)
class CommissionInput:
    net_paid_amount: int
    """The amount actually paid by the referred user for this order (after
    any promo discount was applied) -- i.e. the *eligible net paid amount*
    referenced in spec section 5."""
    standard_referral_percent: int
    """percent*100 basis, taken from the PLAN the purchase was for."""
    blogger_referral_percent: int
    """percent*100 basis, taken from the PLAN the purchase was for."""
    referrer_is_blogger: bool
    is_first_purchase_of_referred_user: bool
    commission_applies_to_renewals: bool
    """Global/plan policy: if False, a referrer is only ever paid on the
    referred user's very first premium purchase."""


@dataclass(frozen=True)
class CommissionResult:
    eligible: bool
    amount: int
    percent_used: int
    used_blogger_rate: bool
    reason: str | None = None


def calculate_referral_commission(inp: CommissionInput) -> CommissionResult:
    """Compute the commission owed to a referrer for one verified purchase.

    Rules:
      - A blogger referrer ALWAYS gets the (potentially different) blogger
        rate for the plan, on top of retaining every standard-referrer
        right (spec section 5: "Has ALL rights ... including the
        plan-specific premium purchase commission").
      - If the purchase is a renewal (not the referred user's first ever
        premium purchase) and the effective policy says commission only
        applies to first purchases, no commission is paid -- this is not a
        fraud case, just policy, so `eligible=False` with a reason.
    """
    if not inp.is_first_purchase_of_referred_user and not inp.commission_applies_to_renewals:
        return CommissionResult(
            eligible=False,
            amount=0,
            percent_used=0,
            used_blogger_rate=inp.referrer_is_blogger,
            reason="renewal_commission_disabled",
        )

    percent = (
        inp.blogger_referral_percent if inp.referrer_is_blogger else inp.standard_referral_percent
    )
    amount = percent_of(inp.net_paid_amount, percent)
    return CommissionResult(
        eligible=True,
        amount=amount,
        percent_used=percent,
        used_blogger_rate=inp.referrer_is_blogger,
    )


def reverse_commission_amount(
    original_amount: int, refunded_fraction_numerator: int, refunded_fraction_denominator: int
) -> int:
    """Amount to claw back when a purchase is refunded.

    Policy (documented, spec section 4 "Reverse eligible commissions on a
    refunded purchase according to a documented policy"): commission
    reversal is proportional to the fraction of the original purchase that
    was refunded. A full refund (numerator==denominator) reverses the
    entire commission. A partial refund reverses the same proportion,
    rounded down so the platform never claws back more than what was
    actually refunded.
    """
    if refunded_fraction_denominator <= 0:
        raise ValueError("refunded_fraction_denominator must be > 0")
    if not (0 <= refunded_fraction_numerator <= refunded_fraction_denominator):
        raise ValueError("refunded_fraction_numerator out of range")
    return (original_amount * refunded_fraction_numerator) // refunded_fraction_denominator
