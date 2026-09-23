"""Blogger acquisition-reward accrual (spec section 5, verified blogger).

The admin configures a rate "per 1,000 qualified users" (globally, or
per-blogger). Spec requires:
  - Accrual starts with the FIRST qualified user, not batched to 1,000.
  - Fractional minor units (e.g. 100,000 UZS / 1000 = 100 UZS/user is exact,
    but a rate like 333 UZS/1000 users = 0.333 UZS/user is not) must be
    carried forward safely -- never lost, never overpaid.

Implementation: track a running remainder in "micros" (millionths of one
minor unit). Each qualified join contributes exactly
`rate_per_1000 * 1000` micros (because 1 minor unit == 1_000_000 micros and
1/1000 of that is exactly 1000 micros -- no rounding at this step, this
multiplication is always exact). We then extract as many whole minor units
as the accumulated micros allow and keep the sub-unit leftover for the next
join. This guarantees that after N joins, the *total* amount ever credited
equals floor(rate_per_1000 * N / 1000) -- i.e. mathematically identical to
computing the exact fraction once for N users and rounding down ONCE,
without ever having to know N in advance and without losing any fraction
along the way.
"""

from __future__ import annotations

from dataclasses import dataclass

MICROS_PER_UNIT = 1_000_000


@dataclass(frozen=True)
class AccrualStep:
    amount_credited: int
    """Whole minor units credited for THIS join (often 0)."""
    remainder_micros_before: int
    remainder_micros_after: int


def accrue_qualified_join(rate_per_1000: int, remainder_micros_before: int) -> AccrualStep:
    if rate_per_1000 < 0:
        raise ValueError("rate_per_1000 must be >= 0")
    if remainder_micros_before < 0:
        raise ValueError("remainder_micros_before must be >= 0")

    contribution_micros = rate_per_1000 * 1000  # exact: (rate_per_1000 / 1000) * 1_000_000
    total_micros = remainder_micros_before + contribution_micros
    whole_units, remainder_after = divmod(total_micros, MICROS_PER_UNIT)
    return AccrualStep(
        amount_credited=whole_units,
        remainder_micros_before=remainder_micros_before,
        remainder_micros_after=remainder_after,
    )


def simulate_n_joins(rate_per_1000: int, n: int) -> tuple[int, int]:
    """Test/debug helper: simulate N sequential qualified joins and return
    (total_amount_credited, final_remainder_micros)."""
    remainder = 0
    total = 0
    for _ in range(n):
        step = accrue_qualified_join(rate_per_1000, remainder)
        total += step.amount_credited
        remainder = step.remainder_micros_after
    return total, remainder


def expected_total_after_n_joins(rate_per_1000: int, n: int) -> int:
    """Closed-form expectation used by tests to cross-check the sequential
    simulation: floor(rate_per_1000 * n / 1000)."""
    return (rate_per_1000 * n) // 1000
