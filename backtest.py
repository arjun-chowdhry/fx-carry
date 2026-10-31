"""Milestone 3: a simple monthly FX carry backtest.

At each month-end, rank USD, EUR, JPY and AUD by overnight rate. Buy the
highest-yielder against the lowest-yielder with a forward that settles at the
next month-end. Notional 1, no leverage.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from data import RATES, load_daily
from forward import DAY_BASIS, forward

CHART = Path(__file__).parent / "charts" / "equity_curve.png"
COST_BPS = 5  # assumed cost of rolling the forward each month


def split_return(s0, f0, s1):
    """Buy the base currency forward at f0 and settle at spot s1.
    Returns (total, fx, interest); fx + interest == total exactly."""
    total = s1 / f0 - 1
    fx = s1 / s0 - 1
    return total, fx, total - fx


def net(total, cost_bps):
    return total - cost_bps / 1e4


def max_drawdown(equity):
    """Worst peak-to-trough fall: (depth, peak date, trough date)."""
    dd = equity / equity.cummax() - 1
    trough = dd.idxmin()
    peak = equity.loc[:trough].idxmax()
    return dd[trough], peak, trough


def usd_value(df):
    """What one unit of each currency is worth in USD."""
    return pd.DataFrame({"USD": 1.0, "EUR": df["EURUSD"], "JPY": 1 / df["USDJPY"],
                         "AUD": df["AUDUSD"]}, index=df.index)


def month_ends(index):
    ends = index.to_series().groupby(index.to_period("M")).last()
    if (ends.iloc[-1] + pd.offsets.BDay()).month == ends.iloc[-1].month:
        ends = ends.iloc[:-1]  # data stops mid-month, so the last month is incomplete
    return pd.DatetimeIndex(ends)


def backtest(df):
    # A day's overnight rate is published the next morning, so at a month-end
    # close the latest known rate is the previous trading day's.
    known = df[RATES].shift(1) / 100
    px = usd_value(df)
    dates = month_ends(df.index)
    rows = []
    for t0, t1 in zip(dates[:-1], dates[1:]):
        r = known.loc[t0]
        hi, lo = r.idxmax(), r.idxmin()
        s0 = px.at[t0, hi] / px.at[t0, lo]  # price of hi in units of lo
        s1 = px.at[t1, hi] / px.at[t1, lo]
        f0 = forward(s0, r[hi], r[lo], (t1 - t0).days, DAY_BASIS[hi], DAY_BASIS[lo])
        total, fx, interest = split_return(s0, f0, s1)
        rows.append({"start": t0, "end": t1, "pair": f"long {hi} / short {lo}",
                     "gap": r[hi] - r[lo], "fx": fx, "interest": interest, "total": total})
    return pd.DataFrame(rows).set_index("end", drop=False)


def equity(returns, start):
    return pd.concat([pd.Series([1.0], index=[start]), (1 + returns).cumprod()])


def stats(returns, start):
    eq = equity(returns, start)
    vol = returns.std() * 12 ** 0.5
    dd, peak, trough = max_drawdown(eq)
    return {"annual return": f"{eq.iloc[-1] ** (12 / len(returns)) - 1:.2%}",
            "volatility": f"{vol:.2%}", "Sharpe": f"{returns.mean() * 12 / vol:.2f}",
            "worst drawdown": f"{dd:.1%}", "drawdown": f"{peak:%b %Y} - {trough:%b %Y}"}


def stretches(bt):
    block = (bt["pair"] != bt["pair"].shift()).cumsum()
    return bt.groupby(block).agg(start=("start", "first"), end=("end", "last"),
                                 pair=("pair", "first"), months=("pair", "size"),
                                 avg_gap=("gap", "mean"), interest=("interest", "sum"),
                                 fx=("fx", "sum"))


def plot_equity(bt):
    start = bt["start"].iloc[0]
    eq = equity(net(bt["total"], COST_BPS), start)
    dd, peak, trough = max_drawdown(eq)
    simple = lambda s: pd.concat([pd.Series([1.0], index=[start]), 1 + s.cumsum()])

    fig, ax = plt.subplots(figsize=(9, 5), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.axvspan(peak, trough, color="#e6e5e1")
    ax.axhline(1, color="#52514e", linewidth=0.8)
    ax.plot(eq, color="#2a78d6", linewidth=2, label=f"Net of {COST_BPS} bps/month costs")
    ax.plot(simple(bt["interest"]), color="#eb6834", linewidth=2, linestyle="--",
            label="Interest part only")
    ax.plot(simple(bt["fx"]), color="#1baf7a", linewidth=2, linestyle="--",
            label="Exchange-rate part only")
    ax.annotate(f"Worst drawdown {dd:.1%}\n{peak:%b %Y} to {trough:%b %Y}",
                xy=(trough, eq[trough]), xytext=(10, -40), textcoords="offset points",
                fontsize=9, color="#0b0b0b", arrowprops={"arrowstyle": "-", "color": "#52514e"})
    ax.set_title("FX carry: growth of $1 (monthly, highest vs lowest rate)", loc="left")
    ax.grid(axis="y", color="#e6e5e1", linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(CHART, dpi=120)


if __name__ == "__main__":
    bt = backtest(load_daily())
    start = bt["start"].iloc[0]
    pct = lambda x: f"{x:+.1%}"

    print("Positions held (gap = rate gap at entry; interest/fx = summed monthly parts):")
    s = stretches(bt)
    print(s.to_string(index=False, formatters={
        "start": "{:%Y-%m-%d}".format, "end": "{:%Y-%m-%d}".format,
        "avg_gap": "{:.2%}".format, "interest": pct, "fx": pct}))

    print(f"\n{len(bt)} months, {start:%Y-%m} to {bt.index[-1]:%Y-%m}")
    print(pd.DataFrame({f"{c} bps": stats(net(bt["total"], c), start) for c in (0, 5, 10)}))

    print(f"\nWhere the money came from (simple sums, {COST_BPS} bps costs):")
    print(f"  interest {bt['interest'].sum():+.1%}   exchange rate {bt['fx'].sum():+.1%}"
          f"   costs {-len(bt) * COST_BPS / 1e4:+.1%}")
    print(f"  check: interest per year {bt['interest'].mean() * 12:.2%}"
          f" vs average rate gap {bt['gap'].mean():.2%}")

    w = bt.loc[bt["total"].idxmin()]
    print(f"\nWorst month: {w['end']:%b %Y}, {w['pair']}: total {pct(w['total'])}"
          f" = interest {pct(w['interest'])} + exchange rate {pct(w['fx'])}")

    plot_equity(bt)
    print(f"chart -> {CHART}")
