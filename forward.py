"""Milestone 2: price an FX forward from spot and two interest rates.

Covered interest parity: a forward must make borrowing in one currency and
lending in the other worth exactly the same, so
    F = S * (1 + r_quote * days / basis_quote) / (1 + r_base * days / basis_base)
Rates are decimals (5% = 0.05). For EURUSD, EUR is the base and USD the quote.
"""
from pathlib import Path

import matplotlib.pyplot as plt

from data import load_daily

# Days in the interest-rate year, by market convention.
DAY_BASIS = {"USD": 360, "EUR": 360, "JPY": 365, "AUD": 365}
# Pair -> (base, quote, size of one pip).
PAIRS = {
    "EURUSD": ("EUR", "USD", 0.0001),
    "USDJPY": ("USD", "JPY", 0.01),
    "AUDUSD": ("AUD", "USD", 0.0001),
}
CHART = Path(__file__).parent / "charts" / "forward_points.png"


def forward(spot, r_base, r_quote, days, basis_base, basis_quote):
    return spot * (1 + r_quote * days / basis_quote) / (1 + r_base * days / basis_base)


def forward_points(spot, r_base, r_quote, days, basis_base, basis_quote, pip):
    return (forward(spot, r_base, r_quote, days, basis_base, basis_quote) - spot) / pip


def pair_points(df, pair, days=30):
    """Forward points for one pair, every day in the clean table."""
    base, quote, pip = PAIRS[pair]
    return forward_points(df[pair], df[base] / 100, df[quote] / 100, days,
                          DAY_BASIS[base], DAY_BASIS[quote], pip)


def plot_points(df):
    fig, axes = plt.subplots(3, 1, figsize=(9, 7.5), sharex=True, facecolor="#fcfcfb")
    for ax, pair in zip(axes, PAIRS):
        ax.set_facecolor("#fcfcfb")
        ax.axhline(0, color="#52514e", linewidth=0.8)
        ax.plot(pair_points(df, pair), color="#2a78d6", linewidth=2)
        ax.set_title(f"{pair} 1-month forward points (pips)", loc="left", fontsize=10)
        ax.grid(axis="y", color="#e6e5e1", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Forward points = interest-rate gap, quoted in pips", x=0.01, ha="left")
    fig.tight_layout()
    CHART.parent.mkdir(exist_ok=True)
    fig.savefig(CHART, dpi=120)


if __name__ == "__main__":
    df = load_daily()
    plot_points(df)
    for pair in PAIRS:
        pts = pair_points(df, pair)
        print(f"{pair}: latest {pts.iloc[-1]:+.1f} pips, range {pts.min():+.1f} to {pts.max():+.1f}")
    print(f"chart -> {CHART}")
