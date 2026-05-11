"""
market_data.py -- Layer 2, Step 1
Load and prepare the AAPL options dataset for Layer 2 modules.
Computes moneyness, realized volatility, RV-IV spread, bid-ask spread,
and ITM/OTM outcome labels for each contract.
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_FILE = os.path.join(DATA_DIR, "aapl_2016_2020.csv")


def load_raw(path=CSV_FILE):
    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip().strip("[]").strip() for c in df.columns]
    df["QUOTE_DATE"]  = pd.to_datetime(df["QUOTE_DATE"].str.strip())
    df["EXPIRE_DATE"] = pd.to_datetime(df["EXPIRE_DATE"].str.strip())
    for col in ["UNDERLYING_LAST", "STRIKE", "DTE",
                "C_BID", "C_ASK", "C_IV", "C_VOLUME",
                "P_BID", "P_ASK", "P_IV",  "P_VOLUME"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_realized_vol(df, window=30):
    """30-day annualized realized volatility from daily log returns."""
    daily = (df.groupby("QUOTE_DATE")["UNDERLYING_LAST"]
               .last()
               .sort_index()
               .to_frame())
    daily["log_ret"] = np.log(daily["UNDERLYING_LAST"] /
                              daily["UNDERLYING_LAST"].shift(1))
    daily["RV30"] = daily["log_ret"].rolling(window).std() * np.sqrt(252)
    return df.merge(daily[["RV30"]], left_on="QUOTE_DATE",
                    right_index=True, how="left")


def label_outcomes(df):
    """
    For each (EXPIRE_DATE, STRIKE) pair find the underlying close on or
    just before expiry and assign binary ITM labels:
      call_itm = 1 if underlying > strike at expiry else 0
      put_itm  = 1 if underlying < strike at expiry else 0
    """
    expiry_prices = (df.groupby("EXPIRE_DATE")["UNDERLYING_LAST"]
                       .last()
                       .rename("UNDERLYING_AT_EXPIRY"))
    df = df.merge(expiry_prices, on="EXPIRE_DATE", how="left")
    df["call_itm"] = (df["UNDERLYING_AT_EXPIRY"] > df["STRIKE"]).astype(int)
    df["put_itm"]  = (df["UNDERLYING_AT_EXPIRY"] < df["STRIKE"]).astype(int)
    return df


def build_features(df):
    """Engineer the feature columns used by p_estimator.py."""
    df = df.copy()
    df["moneyness"]       = df["UNDERLYING_LAST"] / df["STRIKE"]
    df["call_half_spread"] = (df["C_ASK"] - df["C_BID"]).clip(lower=0) / 2
    df["put_half_spread"]  = (df["P_ASK"] - df["P_BID"]).clip(lower=0) / 2
    df["call_mid"]         = (df["C_BID"] + df["C_ASK"]) / 2
    df["put_mid"]          = (df["P_BID"] + df["P_ASK"]) / 2
    df["rv_iv_spread_call"] = df["C_IV"] - df["RV30"]
    df["rv_iv_spread_put"]  = df["P_IV"] - df["RV30"]
    df["log_dte"]           = np.log1p(df["DTE"])
    df["log_c_volume"]      = np.log1p(df["C_VOLUME"])
    df["log_p_volume"]      = np.log1p(df["P_VOLUME"])
    return df


def load_prepared(path=CSV_FILE, sample_frac=1.0):
    """
    Full pipeline: load -> compute RV -> label outcomes -> engineer features.
    Returns a clean DataFrame ready for p_estimator.py.
    Set sample_frac < 1.0 to work on a random subset (faster for development).
    """
    print(f"Loading {os.path.basename(path)} ...")
    df = load_raw(path)

    if sample_frac < 1.0:
        df = df.sample(frac=sample_frac, random_state=42).reset_index(drop=True)
        print(f"  Sampled {len(df):,} rows ({sample_frac*100:.0f}%)")

    print("  Computing realized volatility ...")
    df = compute_realized_vol(df)

    print("  Labeling ITM/OTM outcomes ...")
    df = label_outcomes(df)

    print("  Engineering features ...")
    df = build_features(df)

    # Drop rows missing any key feature
    required = ["moneyness", "DTE", "C_IV", "P_IV", "RV30",
                "rv_iv_spread_call", "rv_iv_spread_put",
                "call_half_spread", "put_half_spread",
                "log_c_volume", "log_p_volume",
                "call_itm", "put_itm"]
    before = len(df)
    df = df.dropna(subset=required).reset_index(drop=True)
    print(f"  Kept {len(df):,} / {before:,} rows after dropping NaNs")
    print(f"  Date range: {df['QUOTE_DATE'].min().date()} -> "
          f"{df['QUOTE_DATE'].max().date()}")
    return df


CALL_FEATURES = [
    "moneyness", "log_dte", "C_IV", "RV30",
    "rv_iv_spread_call", "call_half_spread", "log_c_volume",
]

PUT_FEATURES = [
    "moneyness", "log_dte", "P_IV", "RV30",
    "rv_iv_spread_put", "put_half_spread", "log_p_volume",
]


if __name__ == "__main__":
    df = load_prepared(sample_frac=0.1)
    print("\nSample rows:")
    print(df[["QUOTE_DATE", "EXPIRE_DATE", "STRIKE", "moneyness",
              "DTE", "C_IV", "RV30", "rv_iv_spread_call",
              "call_itm", "put_itm"]].head(5).to_string())
    print(f"\nCall ITM rate: {df['call_itm'].mean():.3f}")
    print(f"Put  ITM rate: {df['put_itm'].mean():.3f}")
