import pytest

from app.engines.profit_engine import calculate_profit, net_gain


def test_normal_calculation():
    result = calculate_profit(quantity_kg=800, price_per_kg=48, transport_cost=752, spoilage_percentage=0)
    assert result.sellable_quantity_kg == 800
    assert result.gross_revenue == 38400
    assert result.net_profit == 38400 - 752
    assert result.spoilage_loss == 0


def test_spoilage_adjusted_calculation():
    result = calculate_profit(800, 63, 444, spoilage_percentage=10)
    assert result.sellable_quantity_kg == pytest.approx(720)
    assert result.gross_revenue == pytest.approx(45360)
    assert result.spoilage_loss == pytest.approx(5040)
    assert result.net_profit == pytest.approx(45360 - 444)


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        calculate_profit(-1, 48, 0, 0)
    with pytest.raises(ValueError):
        calculate_profit(100, -5, 0, 0)
    with pytest.raises(ValueError):
        calculate_profit(100, 48, -1, 0)
    with pytest.raises(ValueError):
        calculate_profit(100, 48, 0, 101)


def test_baseline_comparison():
    baseline = calculate_profit(800, 48, 752, 0).net_profit
    recommended = calculate_profit(800, 63, 444, 2).net_profit
    assert net_gain(recommended, baseline) > 0
