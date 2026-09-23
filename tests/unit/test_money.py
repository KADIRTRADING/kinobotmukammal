import pytest

from app.services.money import (
    InsufficientFundsError,
    apply_percent_discount,
    ceil_div,
    floor_div,
    percent_of,
)


def test_percent_of_exact():
    assert percent_of(5000, 1000) == 500  # 10.00% of 5000


def test_percent_of_floors_down():
    # 10% of 999 = 99.9 -> floors to 99, never overpays the recipient.
    assert percent_of(999, 1000) == 99


def test_percent_of_zero_percent():
    assert percent_of(12345, 0) == 0


def test_percent_of_rejects_negative():
    with pytest.raises(ValueError):
        percent_of(-1, 1000)
    with pytest.raises(ValueError):
        percent_of(100, -1)


def test_apply_percent_discount_worked_example():
    # Spec section 7 worked example: 5000 UZS premium, 10% discount -> buyer pays 4500.
    assert apply_percent_discount(5000, 10) == 4500


def test_apply_percent_discount_zero_percent():
    assert apply_percent_discount(5000, 0) == 5000


def test_apply_percent_discount_full_percent():
    assert apply_percent_discount(5000, 100) == 0


def test_apply_percent_discount_rounds_ceiling_discount_amount():
    # 3 * 33% = 0.99 -> ceil -> 1 minor unit discount -> net = 2
    assert apply_percent_discount(3, 33) == 2


def test_apply_percent_discount_rejects_out_of_range():
    with pytest.raises(ValueError):
        apply_percent_discount(100, 101)
    with pytest.raises(ValueError):
        apply_percent_discount(100, -1)


def test_ceil_div_and_floor_div():
    assert ceil_div(10, 3) == 4
    assert floor_div(10, 3) == 3
    assert ceil_div(9, 3) == 3
    assert floor_div(9, 3) == 3


def test_insufficient_funds_error_message():
    err = InsufficientFundsError(available=100, requested=500, currency="UZS")
    assert "100" in str(err) and "500" in str(err) and "UZS" in str(err)
