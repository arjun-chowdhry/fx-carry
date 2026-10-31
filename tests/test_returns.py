"""Hand-worked return math.

Buy a currency forward at 99 when spot is 100 (the forward is below spot
because the currency pays the higher rate).
  Spot ends at 100: total = 100/99 - 1 = +1.0101%, all of it interest.
  Spot ends at 95:  total = 95/99 - 1 = -4.04%
                    fx = 95/100 - 1 = -5.00%, interest = total - fx = +0.96%
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from backtest import max_drawdown, net, split_return  # noqa: E402


def test_spot_unchanged_is_all_interest():
    total, fx, interest = split_return(100, 99, 100)
    assert total == pytest.approx(0.010101, abs=1e-6)
    assert fx == 0
    assert interest == pytest.approx(0.010101, abs=1e-6)


def test_spot_falls():
    total, fx, interest = split_return(100, 99, 95)
    assert total == pytest.approx(-0.040404, abs=1e-6)
    assert fx == pytest.approx(-0.05)
    assert interest == pytest.approx(0.009596, abs=1e-6)
    assert fx + interest == pytest.approx(total)


def test_cost_in_bps():
    assert net(0.01, 5) == pytest.approx(0.0095)


def test_max_drawdown():
    depth, peak, trough = max_drawdown(pd.Series([1, 1.2, 0.9, 1.1]))
    assert depth == pytest.approx(-0.25)
    assert (peak, trough) == (1, 2)
