"""Milestone 1: turn the raw CSV into one clean daily table.

Columns out:
  EURUSD, USDJPY, AUDUSD  spot FX (FRED H.10, noon New York)
  USD, EUR, JPY, AUD      overnight interest rates, % per year
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw" / "fx_carry_sample.csv"
CLEAN = Path(__file__).parent / "data" / "clean_daily.csv"

# One rate per currency, no splicing. EFFR and the ECB deposit rate are left out.
COLUMNS = {
    "EURUSD": "EURUSD",
    "USDJPY": "USDJPY",
    "AUDUSD": "AUDUSD",
    "USD_SOFR": "USD",
    "EUR_ESTR": "EUR",
    "JPY TONA": "JPY",
    "AUD_CASH": "AUD",
}
FX = ["EURUSD", "USDJPY", "AUDUSD"]
RATES = ["USD", "EUR", "JPY", "AUD"]


def load_daily(path=RAW):
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    df = df[list(COLUMNS)].rename(columns=COLUMNS)

    # No FX price means a US holiday, so there is nothing to trade that day.
    df = df.dropna(subset=FX)
    # A rate missing on a local holiday is still the last rate that was set.
    df[RATES] = df[RATES].ffill(limit=5)

    assert not df.isna().any().any(), "gaps left after cleaning"
    assert df.index.is_monotonic_increasing and df.index.is_unique
    assert (df[FX] > 0).all().all()
    return df


if __name__ == "__main__":
    df = load_daily()
    df.to_csv(CLEAN)
    print(f"{len(df)} rows, {df.index[0].date()} to {df.index[-1].date()} -> {CLEAN}")
    print(df.describe().round(3).to_string())
