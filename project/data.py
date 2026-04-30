"""Data ingestion and preprocessing for the AMD CRR + Kelly pipeline."""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import yfinance as yf


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def compute_time_to_expiry(collection_date: str, expiry_date: str) -> float:
    """Return T in years between two date strings (YYYY-MM-DD)."""
    t0 = datetime.strptime(collection_date, "%Y-%m-%d")
    t1 = datetime.strptime(expiry_date, "%Y-%m-%d")
    return (t1 - t0).days / 365.0


def fetch_realized_volatility(ticker: str = "AMD", window_30: int = 30, window_60: int = 60) -> dict:
    """Download 6 months of daily closes and return annualized realized vol."""
    hist = yf.Ticker(ticker).history(period="6mo")["Close"]
    log_ret = np.log(hist / hist.shift(1)).dropna()
    rv30 = float(log_ret.tail(window_30).std() * np.sqrt(252))
    rv60 = float(log_ret.tail(window_60).std() * np.sqrt(252))
    return {"rv30": rv30, "rv60": rv60, "n_obs": len(log_ret)}


def build_option_chain_df(config: dict, T: float, rv: dict) -> pd.DataFrame:
    """Assemble all ticket inputs into one tidy DataFrame."""
    S = config["amd"]["S"]
    r = config["amd"]["r"]
    rows = []
    for t in config["tickets"]:
        rows.append({
            "ticket_id":       t["id"],
            "action":          t["action"],
            "option_type":     t["option_type"],
            "S":               S,
            "K":               t["K"],
            "iv":              t["iv"],
            "r":               r,
            "T":               T,
            "V_market":        t["V_market"],
            "break_even":      t["break_even"],
            "moneyness":       (S - t["K"]) / t["K"],
            "iv_premium_rv30": t["iv"] - rv["rv30"],
            "iv_premium_rv60": t["iv"] - rv["rv60"],
            "collection_date": config["amd"]["collection_date"],
            "expiry_date":     config["amd"]["expiry_date"],
        })
    return pd.DataFrame(rows)
