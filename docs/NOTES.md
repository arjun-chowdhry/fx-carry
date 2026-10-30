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
