import pytest

from app.engines.transport_engine import calculate_transport_cost


def test_fixed_plus_distance_cost():
    result = calculate_transport_cost(distance_km=72, farmer_quantity_kg=800, return_trip=False)
    assert result.base_cost == 500 + 72 * 18


def test_pool_sharing():
    solo = calculate_transport_cost(72, 800, total_pool_quantity_kg=800, return_trip=False)
    shared = calculate_transport_cost(72, 800, total_pool_quantity_kg=2100, return_trip=False)
    # Same leg, sharing splits the cost proportionally.
    assert shared.effective_total_cost == solo.effective_total_cost
    assert shared.farmer_share == pytest.approx(solo.effective_total_cost * 800 / 2100)


def test_return_trip_discount_applied():
    normal = calculate_transport_cost(72, 800, return_trip=False)
    returning = calculate_transport_cost(72, 800, return_trip=True)
    assert returning.effective_total_cost < normal.effective_total_cost
    expected_discount = 1 - (returning.effective_total_cost / normal.effective_total_cost)
    assert 0.30 < expected_discount < 0.40  # configured ~35%


def test_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_transport_cost(-5, 100)
    with pytest.raises(ValueError):
        calculate_transport_cost(10, 0)
    with pytest.raises(ValueError):
        calculate_transport_cost(10, 900, total_pool_quantity_kg=500)
