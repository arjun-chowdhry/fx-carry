"""Hand-worked forward prices. Rates are decimals; 90-day trades.

EURUSD: spot 1.1000, USD 5% (ACT/360), EUR 3% (ACT/360)
    F = 1.1 * (1 + 0.05*90/360) / (1 + 0.03*90/360)
      = 1.1 * 1.0125 / 1.0075 = 1.105459   -> +54.59 pips
    USD pays more, so EUR is worth more forward.

USDJPY: spot 150.00, USD 5% (ACT/360), JPY 0.5% (ACT/365)
    F = 150 * (1 + 0.005*90/365) / (1 + 0.05*90/360)
      = 150 * 1.0012329 / 1.0125 = 148.3308 -> -166.92 pips
    USD pays more, so USD buys fewer yen forward.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from forward import forward, forward_points  # noqa: E402


def test_eurusd_forward():
    assert forward(1.1, 0.03, 0.05, 90, 360, 360) == pytest.approx(1.105459, abs=1e-6)
    assert forward_points(1.1, 0.03, 0.05, 90, 360, 360, 0.0001) == pytest.approx(54.59, abs=0.01)


def test_usdjpy_forward():
    assert forward(150, 0.05, 0.005, 90, 360, 365) == pytest.approx(148.3308, abs=1e-4)
    assert forward_points(150, 0.05, 0.005, 90, 360, 365, 0.01) == pytest.approx(-166.92, abs=0.01)


def test_equal_rates_give_spot():
    assert forward(1.1, 0.04, 0.04, 90, 360, 360) == pytest.approx(1.1)
