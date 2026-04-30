"""Mispricing edge: signed percentage gap between CRR model and market price."""

import pandas as pd

from tree import price_american_option


def compute_edges(chain_df: pd.DataFrame, N: int) -> pd.DataFrame:
    """
    For each ticket, price with the CRR tree and compute:
        edge = (V_model - V_market) / V_market

    Positive edge → model says market is cheap → favour buying.
    Negative edge → model says market is expensive → favour selling.
    """
    rows = []
    for _, row in chain_df.iterrows():
        V_model, _ = price_american_option(
            S=row["S"],
            K=row["K"],
            r=row["r"],
            sigma=row["iv"],
            T=row["T"],
            N=N,
            option_type=row["option_type"],
        )
        edge = (V_model - row["V_market"]) / row["V_market"]
        rows.append({
            "ticket_id":    row["ticket_id"],
            "action":       row["action"],
            "option_type":  row["option_type"],
            "K":            row["K"],
            "V_model":      round(V_model, 4),
            "V_market":     row["V_market"],
            "edge":         edge,
            "edge_pct":     edge * 100,
            "abs_edge_pct": abs(edge) * 100,
        })
    return pd.DataFrame(rows)
