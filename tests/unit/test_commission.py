from app.services.commission import (
    CommissionInput,
    calculate_referral_commission,
    reverse_commission_amount,
)


def make_input(**overrides) -> CommissionInput:
    base = dict(
        net_paid_amount=10_000,
        standard_referral_percent=1000,  # 10.00%
        blogger_referral_percent=1500,  # 15.00%
        referrer_is_blogger=False,
        is_first_purchase_of_referred_user=True,
        commission_applies_to_renewals=False,
    )
    base.update(overrides)
    return CommissionInput(**base)


def test_each_plan_independent_commission_percent():
    # One-week plan: 10% commission.
    weekly = make_input(net_paid_amount=10_000, standard_referral_percent=1000)
    result_weekly = calculate_referral_commission(weekly)
    assert result_weekly.eligible
    assert result_weekly.amount == 1_000

    # One-month plan: 15% commission on a DIFFERENT plan/purchase -- proves
    # commission is never hard-coded identically across plans.
    monthly = make_input(net_paid_amount=10_000, standard_referral_percent=1500)
    result_monthly = calculate_referral_commission(monthly)
    assert result_monthly.eligible
    assert result_monthly.amount == 1_500
    assert result_weekly.amount != result_monthly.amount


def test_blogger_referrer_gets_blogger_rate_not_standard_rate():
    inp = make_input(
        net_paid_amount=10_000,
        standard_referral_percent=1000,
        blogger_referral_percent=1500,
        referrer_is_blogger=True,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible
    assert result.used_blogger_rate is True
    assert result.amount == 1_500  # blogger rate, not standard 10%


def test_standard_referrer_still_works_when_not_blogger():
    inp = make_input(referrer_is_blogger=False)
    result = calculate_referral_commission(inp)
    assert result.used_blogger_rate is False
    assert result.amount == 1_000


def test_renewal_commission_disabled_by_policy():
    inp = make_input(
        is_first_purchase_of_referred_user=False,
        commission_applies_to_renewals=False,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible is False
    assert result.amount == 0
    assert result.reason == "renewal_commission_disabled"


def test_renewal_commission_enabled_by_policy():
    inp = make_input(
        is_first_purchase_of_referred_user=False,
        commission_applies_to_renewals=True,
        standard_referral_percent=1000,
        net_paid_amount=20_000,
    )
    result = calculate_referral_commission(inp)
    assert result.eligible is True
    assert result.amount == 2_000


def test_first_purchase_always_eligible_regardless_of_renewal_policy():
    inp = make_input(is_first_purchase_of_referred_user=True, commission_applies_to_renewals=False)
    result = calculate_referral_commission(inp)
    assert result.eligible is True


def test_reverse_commission_full_refund():
    assert reverse_commission_amount(1000, 1, 1) == 1000


def test_reverse_commission_partial_refund_rounds_down():
    # Refund 1/3 of the purchase -> claw back floor(1000/3) = 333.
    assert reverse_commission_amount(1000, 1, 3) == 333


def test_reverse_commission_zero_refund():
    assert reverse_commission_amount(1000, 0, 1) == 0
