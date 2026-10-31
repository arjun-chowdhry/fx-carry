# FX Carry — Notes

The question: **does FX carry earn money after costs, and what does a crash look like?**

FX carry means borrowing in a currency with a low interest rate and holding a currency with a high one. You earn the gap between the two rates. The risk is that the high-yield currency falls in value and wipes out what you earned.

## Milestone 1 — Data: one clean daily table

**What we built.** `data.py` reads `data/raw/fx_carry_sample.csv` (copied from the earlier data test) and writes `data/clean_daily.csv`. That file is one row per trading day from 2019-10-01 to 2026-10-23, 1,765 rows in all.

| Column | Meaning |
|---|---|
| `EURUSD` | US dollars per 1 euro |
| `USDJPY` | Japanese yen per 1 US dollar |
| `AUDUSD` | US dollars per 1 Australian dollar |
| `USD` | SOFR, the US overnight rate, % per year |
| `EUR` | €STR, the euro overnight rate, % per year |
| `JPY` | TONA, the yen overnight rate, % per year |
| `AUD` | RBA cash rate, the Australian overnight rate, % per year |

**Why one rate per currency.** Carry is about the gap between two currencies' interest rates, so each currency needs exactly one rate. We use each country's main overnight rate. All four cover the whole period, so nothing had to be stitched together from different sources. The raw file also had the Fed funds rate and the ECB deposit rate. They track SOFR and €STR closely, so we dropped them to keep things simple.

**Why we drop some days and fill others.**
- **Dropped (79 days):** days with no FX price, which are US holidays. You can't trade or value a position without a price, so these rows go.
- **Filled:** a rate missing on a day we kept means it was a holiday in that country (Japan has the most). On a holiday the rate stays at the last value set, so we carry it forward, for at most 5 days. Cells filled: USD 7, EUR 23, JPY 106, AUD 42.
- The script then checks that no gaps remain, the dates are in order with no repeats, and all prices are positive.

**A first look at the numbers.** Over the period, USD rates averaged about 2.8% and JPY rates about 0.2%. That gap is the classic "yen carry trade". Rates were near zero everywhere in 2020–21 and rose sharply from 2022, so the carry on offer changed a lot over time.

**Run it:** `.venv\Scripts\python data.py`

## Milestone 2 — Forward pricer and forward points

**What we built.** `forward.py` prices an FX forward, which is an agreement today to swap currencies on a future date at a rate fixed now. `tests/test_forward.py` checks it against two worked examples, and the script draws `charts/forward_points.png`.

**Why the forward differs from spot (no free lunch).** Say USD pays 5% and EUR pays 3%. If the EUR/USD forward were the same as spot, you could borrow euros at 3%, swap them into dollars, earn 5%, and lock in the swap back at today's rate. That's a risk-free profit. So the forward has to adjust until the trade earns nothing: the high-rate currency is worth *less* in the forward market. This is **covered interest parity**:

    F = S × (1 + r_quote × days/basis_quote) / (1 + r_base × days/basis_base)

- *Base* is the first currency in the pair and *quote* is the second (for EURUSD, base EUR, quote USD).
- Rates are decimals (5% = 0.05).
- *basis* is how many days a market counts in a year: 360 for USD and EUR, 365 for JPY and AUD.

**Worked example (it's also the test).** EURUSD spot 1.1000, USD 5%, EUR 3%, 90 days:
F = 1.1 × 1.0125 / 1.0075 = **1.105459**. EUR is worth more forward because it's the lower-rate currency.

**Forward points** are just F − S quoted in pips. A pip is 0.0001 for EURUSD and AUDUSD and 0.01 for USDJPY. Traders quote forwards this way because the points show the rate gap directly. The example above is +54.6 points.

**How to read the chart** (1-month points, 2019–2026):
- **Points below zero** mean the base currency pays the higher rate. USDJPY is the clearest case. It's flat near zero in 2020–21 (every rate near 0%), then falls to about −70 pips by mid-2024 as the Fed hiked and Japan stayed near zero. It has narrowed since as Japan raised rates.
- **EURUSD** stays positive throughout because USD always paid more than EUR. The short spikes are SOFR jumping at month- and quarter-ends.
- **AUDUSD** turns negative in 2026 because Australia's rate is now above the US rate.

**Link to carry.** A carry trader holds the high-rate currency. With forwards, that means *buying it forward*, below spot. If spot doesn't move, the trade earns those points. That's the setup for Milestone 3.

**Run it:** `.venv\Scripts\python forward.py` · tests: `.venv\Scripts\python -m pytest`

## Milestone 3 — Monthly carry backtest

**The strategy.** At each month-end, rank USD, EUR, JPY and AUD by overnight interest rate. Buy the highest-yielder against the lowest-yielder with a forward that settles at the next month-end, then repeat. There's one position at a time, a notional of 1, and no leverage. Crosses such as AUD/JPY are built from the USD pairs. Because a forward needs no cash up front, its return is already the return *over* cash. That's why the Sharpe ratio below doesn't subtract a risk-free rate.

**No looking ahead.** Overnight rates are published the next morning, so at a month-end close the newest rate anyone knows is the previous day's. The ranking and the forward price both use the previous trading day's rates and the month-end spot. The result is measured at the next month-end's spot. The run covers 83 full months, Oct 2019 to Sep 2026. October 2026 is incomplete, so it's left out.

**Splitting each month's return.** If you buy forward at F and later sell at spot S₁:
- total = S₁/F − 1
- exchange-rate part = S₁/S₀ − 1, which is how much spot moved
- interest part = total − exchange-rate part, which is the carry locked in by buying below spot

The two parts add up exactly. As a check, the interest part earned 2.97% a year against an average rate gap at entry of 2.92%.

**What was held:**

| From | To | Position | Months | Avg rate gap |
|---|---|---|---|---|
| Oct 2019 | Mar 2020 | long USD / short EUR | 5 | 2.15% |
| Mar 2020 | Nov 2020 | long AUD / short EUR | 8 | 0.69% |
| Nov 2020 | Mar 2021 | long USD / short EUR | 4 | 0.62% |
| Mar 2021 | Jun 2021 | long AUD / short EUR | 3 | 0.60% |
| Jun 2021 | Sep 2022 | long USD / short EUR | 15 | 1.03% |
| Sep 2022 | Feb 2026 | long USD / short JPY | 41 | 4.46% |
| Feb 2026 | Sep 2026 | long AUD / short JPY | 7 | 3.37% |

**Does carry earn money after costs?** Yes, in this sample.

| Cost per monthly roll | 0 bps | 5 bps | 10 bps |
|---|---|---|---|
| Annual return | 8.42% | 7.78% | 7.14% |
| Volatility | 9.46% | 9.46% | 9.46% |
| Sharpe | 0.90 | 0.84 | 0.78 |
| Worst drawdown | −11.6% | −11.7% | −11.8% |

Each 5 bps of monthly cost takes about 0.6% a year off the return. That's small next to a rate gap of about 3%, so costs don't decide the answer here.

**How the stats are computed.**
- *Annual return* is **compounded**: (final equity)^(12 / months) − 1. It's the steady yearly rate that turns $1 into the final equity.
- *Volatility* is the standard deviation of monthly returns × √12.
- *Sharpe* is (average monthly return × 12) / volatility.

**Caution: most of the profit was luck in the exchange rate, not carry.** At 5 bps, the parts summed to interest +20.6%, exchange rate +38.6%, and costs −4.2%. Textbook theory (*uncovered interest parity*; general knowledge, not tested here) says the high-rate currency should *fall* by about the rate gap on average, which would cancel the carry. Here it did the opposite: the dollar rallied hard against the euro (2021–22) and the yen (2022–24) exactly while we held it. One position at a time, seven years and one big dollar trend aren't enough to call carry reliably profitable. The steady part is the orange interest line on the equity chart.

**What a crash looks like.** Carry earns small steady gains and gives them back in sudden drops. The equity chart shows this as a slow climb broken by sharp falls.
Items marked *(general knowledge)* are explanations from outside our data; everything else is checked against `data/clean_daily.csv`.

- **Worst drawdown: −11.7%, end-Oct 2022 to end-Jan 2023,** while long USD / short JPY. Equity fell from 1.40 to 1.24.
  - USD/JPY went from 148.63 at end-October to 130.17 at end-January. The daily high was 149.82 on Oct 20 and the low 127.85 on Jan 13.
  - Most of the fall came in two one-day drops:
    - **Nov 10, 2022:** 146.15 → 141.78 (−3.0%). *(General knowledge: a softer-than-expected US inflation report.)*
    - **Dec 20, 2022:** 136.87 → 131.08 (−4.2%). *(General knowledge: the Bank of Japan unexpectedly loosened its cap on Japanese bond yields. This doesn't show in the overnight rate, which didn't move.)*
  - There was also a one-day drop on **Oct 21, 2022** (149.82 → 146.35). *(General knowledge: Japan's Ministry of Finance bought yen to support it.)* That came *before* the drawdown started, since the strategy's equity was still at its peak at the end of October.
  - The interest part was positive every month, so the whole loss came from the exchange rate.
- **Worst single month: July 2024, −6.1%** = interest +0.5% + exchange rate −6.5%.
  - USD/JPY fell from 160.88 to 150.38 over the month. The yen's overnight rate jumped from 0.07% to 0.23% on Aug 1, the first day after a Bank of Japan rate hike.
  - The position was earning about 4.5% a year in interest, so this one month's exchange-rate loss was worth more than a year of interest.
  - *(General knowledge: this was the start of the "yen carry unwind". Many traders held the same long-dollar / short-yen trade and rushed to exit together.)*
  - On the equity chart it's the fall from 1.63 (end-Jun 2024) to 1.47 (end-Sep 2024).
- **Monthly data understates crashes.** USD/JPY fell from 150.38 on Jul 31 to 143.95 on Aug 5 (−4.3% in three trading days), then recovered to 147.42 by Aug 7. Month-end prices don't show that swing, and our daily prices are noon-New-York fixes, so even they miss the intraday low.

**Run it:** `.venv\Scripts\python backtest.py` (prints the positions, cost table, return split and worst month, and saves `charts/equity_curve.png`).
