"""Kelly Criterion trade-sizing framework."""

import numpy as np
import pandas as pd


def _edge_to_win_prob(edge: float, action: str) -> float:
    """
    Map CRR mispricing edge to a win probability for Kelly sizing.

    Convention: edge > 0 means model price > market price (market is cheap,
    buying is favoured). The baseline win probability is 0.50; the edge shifts
    it proportionally, clamped to [0.01, 0.99].

    For a sell ticket the edge sign is inverted before mapping so that a
    negative edge (market overpriced) translates to a favourable p_win.
    """
    if action == "sell":
        edge = -edge  # selling an overpriced option is a positive-edge trade
    p = np.clip(0.50 + edge / 2.0, 0.01, 0.99)
    return float(p)


def kelly_fractions(p: float, b: float = 1.0) -> dict:
    """
    Compute full, half, and quarter-Kelly fractions.

    f* = (p·b − q) / b   with q = 1 − p
    Floored at 0 (no leveraged short positions in this framework).
    """
    q = 1.0 - p
    f_full = max((p * b - q) / b, 0.0)
    return {
        "f_full":    f_full,
        "f_half":    f_full / 2.0,
        "f_quarter": f_full / 4.0,
    }


def compute_kelly_recommendations(
    edge_df: pd.DataFrame,
    chain_df: pd.DataFrame,
    capital: float,
    min_edge: float,
) -> pd.DataFrame:
    """
    For each ticket, apply Kelly sizing and produce dollar-position recommendations.

    Tickets whose |edge| < min_edge are flagged NO TRADE to account for
    model uncertainty and transaction costs.
    """
    rows = []
    for _, erow in edge_df.iterrows():
        crow = chain_df.loc[chain_df["ticket_id"] == erow["ticket_id"]].iloc[0]
        edge = erow["edge"]

        if abs(edge) < min_edge:
            p_win = 0.50
            fracs = {"f_full": 0.0, "f_half": 0.0, "f_quarter": 0.0}
            signal = "NO TRADE (edge below threshold)"
        else:
            p_win = _edge_to_win_prob(edge, erow["action"])
            fracs = kelly_fractions(p_win)
            if erow["action"] == "buy" and edge > 0:
                signal = "BUY"
            elif erow["action"] == "sell" and edge < 0:
                signal = "SELL"
            else:
                signal = "NO TRADE (direction mismatch)"

        rows.append({
            "ticket_id":     erow["ticket_id"],
            "action":        erow["action"],
            "option_type":   erow["option_type"],
            "K":             erow["K"],
            "edge_pct":      round(erow["edge_pct"], 3),
            "p_win":         round(p_win, 4),
            "f_full":        round(fracs["f_full"], 4),
            "f_half":        round(fracs["f_half"], 4),
            "f_quarter":     round(fracs["f_quarter"], 4),
            "dollar_full":   round(fracs["f_full"] * capital, 2),
            "dollar_half":   round(fracs["f_half"] * capital, 2),
            "dollar_quarter":round(fracs["f_quarter"] * capital, 2),
            "trade_signal":  signal,
        })

    return pd.DataFrame(rows)
