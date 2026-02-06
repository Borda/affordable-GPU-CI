"""Simple math operations."""


def power(base: float, exponent: float) -> float:
    """Compute base raised to the power of exponent.

    Args:
        base: The base number.
        exponent: The exponent to raise the base to.

    Returns:
        The result of base ** exponent.

    >>> power(2, 3)
    8.0
    >>> power(5, 0)
    1.0

    """
    return float(base**exponent)
