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
