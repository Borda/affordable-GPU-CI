"""Tests for math_ops module."""

import pytest

from sample_pkg import power


@pytest.mark.parametrize(
    ("base", "exponent", "expected"),
    [
        (2, 3, 8.0),
        (5, 0, 1.0),
        (10, 1, 10.0),
        (2, -1, 0.5),
        (0, 5, 0.0),
        (3, 3, 27.0),
    ],
)
def test_power(base: float, exponent: float, expected: float) -> None:
    assert power(base, exponent) == expected


def test_power_identity() -> None:
    """Any number to the power of 1 is itself."""
    for n in range(1, 10):
        assert power(n, 1) == float(n)


def test_power_zero_exponent() -> None:
    """Any non-zero number to the power of 0 is 1."""
    for n in [1, 2, 5, 100, -3]:
        assert power(n, 0) == 1.0


def test_power_negative_exponent() -> None:
    assert power(2, -2) == 0.25


def test_power_fractional_exponent() -> None:
    assert power(4, 0.5) == pytest.approx(2.0)
    assert power(27, 1 / 3) == pytest.approx(3.0)
