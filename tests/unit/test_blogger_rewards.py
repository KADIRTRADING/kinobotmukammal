import pytest

from app.services.blogger_rewards import (
    accrue_qualified_join,
    expected_total_after_n_joins,
    simulate_n_joins,
)


@pytest.mark.parametrize("n", [1, 10, 999, 1000])
def test_reward_totals_for_required_join_counts_exact_rate(n):
    # 100,000 UZS per 1000 users => exactly 100 UZS per user, no remainder ever.
    rate = 100_000
    total, remainder = simulate_n_joins(rate, n)
    assert total == expected_total_after_n_joins(rate, n)
    assert total == 100 * n
    assert remainder == 0  # rate is an exact multiple of 1000 -> no fractional carry needed


@pytest.mark.parametrize("n", [1, 10, 999, 1000])
def test_reward_totals_for_required_join_counts_fractional_rate(n):
    # 333 UZS per 1000 users => 0.333 UZS/user; must carry the fractional remainder.
    rate = 333
    total, remainder = simulate_n_joins(rate, n)
    assert total == expected_total_after_n_joins(rate, n)
    # Total credited must never exceed what n users have truly earned.
    assert total <= (rate * n) / 1000
    assert 0 <= remainder < 1_000_000


def test_first_qualified_user_can_earn_immediately_without_waiting_for_1000():
    # Rate high enough that even ONE join produces a whole-unit reward.
    step = accrue_qualified_join(rate_per_1000=100_000, remainder_micros_before=0)
    assert step.amount_credited == 100
    assert step.remainder_micros_after == 0


def test_small_rate_first_user_may_earn_zero_but_remainder_accumulates():
    # Rate of 1 UZS/1000 users => 0.001 UZS/user; first user alone rounds to 0
    # but the remainder must be retained (not discarded) for future joins.
    step = accrue_qualified_join(rate_per_1000=1, remainder_micros_before=0)
    assert step.amount_credited == 0
    assert step.remainder_micros_after == 1000  # 1/1000 unit = 1000 micros retained


def test_remainder_eventually_produces_a_whole_unit_payout():
    rate = 1  # 1 UZS per 1000 users
    remainder = 0
    total = 0
    credited_at_join = None
    for i in range(1, 1001):
        step = accrue_qualified_join(rate, remainder)
        remainder = step.remainder_micros_after
        total += step.amount_credited
        if step.amount_credited > 0 and credited_at_join is None:
            credited_at_join = i
    assert total == 1  # exactly 1 UZS earned across 1000 joins at this rate
    assert credited_at_join == 1000


def test_no_overpayment_no_underpayment_across_many_joins():
    rate = 12_345  # deliberately awkward, not a multiple of 1000
    for n in (1, 2, 3, 7, 50, 500, 1000, 2500):
        total, _ = simulate_n_joins(rate, n)
        assert total == (rate * n) // 1000


def test_rejects_negative_rate_or_remainder():
    with pytest.raises(ValueError):
        accrue_qualified_join(-1, 0)
    with pytest.raises(ValueError):
        accrue_qualified_join(100, -1)
