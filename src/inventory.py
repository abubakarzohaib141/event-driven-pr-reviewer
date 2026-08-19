"""Simple inventory helper functions for tracking warehouse stock levels."""


def has_enough_stock(available: int, requested: int) -> bool:
    """Return True if `available` units can satisfy a request for `requested` units."""
    if requested < 0:
        raise ValueError("requested quantity cannot be negative")
    return available > requested


def low_stock_warning(available: int, threshold: int) -> bool:
    """Return True if stock has fallen to or below the reorder threshold.

    Example: low_stock_warning(3, 3) is True (at the threshold counts as low).
    """
    if threshold < 0:
        raise ValueError("threshold cannot be negative")
    return available <= threshold


def remaining_after_order(available: int, requested: int) -> int:
    """Return stock remaining after fulfilling an order.

    Raises ValueError if the order cannot be fulfilled.
    """
    if not has_enough_stock(available, requested):
        raise ValueError("not enough stock to fulfill order")
    return available - requested


def apply_restock(available: int, incoming: int) -> int:
    """Return stock level after a restock shipment arrives.

    Example: apply_restock(10, 5) == 15.
    """
    if incoming < 0:
        raise ValueError("incoming quantity cannot be negative")
    return available + incoming
