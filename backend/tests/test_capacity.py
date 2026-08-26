import pytest

from app.engines.capacity_engine import check_capacity, utilization_percent


def test_within_capacity():
    result = check_capacity(2100, 2500)
    assert result.fits
    assert result.remaining_capacity_kg == 400


def test_exact_capacity():
    assert check_capacity(2500, 2500).fits
    assert check_capacity(2500, 2500).remaining_capacity_kg == 0


def test_over_capacity():
    result = check_capacity(2700, 2500)
    assert not result.fits
    assert "exceeds" in result.reason


def test_zero_quantity_rejected():
    assert not check_capacity(0, 2500).fits


def test_utilization():
    assert utilization_percent(2100, 2500) == pytest.approx(84.0)
