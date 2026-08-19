import pytest

from inventory import apply_restock, has_enough_stock, remaining_after_order


def test_has_enough_stock_true_when_more_available():
    assert has_enough_stock(10, 5) is True


def test_has_enough_stock_true_when_exactly_equal():
    # Boundary case: requesting exactly what's available should succeed.
    assert has_enough_stock(5, 5) is True


def test_has_enough_stock_false_when_not_enough():
    assert has_enough_stock(3, 5) is False


def test_remaining_after_order_exact_match_leaves_zero():
    assert remaining_after_order(5, 5) == 0


def test_remaining_after_order_raises_when_insufficient():
    with pytest.raises(ValueError):
        remaining_after_order(3, 5)


def test_apply_restock():
    assert apply_restock(10, 5) == 15


def test_apply_restock_rejects_negative():
    with pytest.raises(ValueError):
        apply_restock(10, -1)
