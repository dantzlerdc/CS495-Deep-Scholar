"""
policy.py -- Layer 2, Step 6
Regime-conditional trade decision engine.
Combines p_independent, net edge, regime label, and Kelly sizing
into a final TRADE / NO TRADE signal per option contract.
"""

import numpy as np
import pandas as pd

from micro_cost  import compute_net_edge, should_trade
from bias_detector import min_edge_for_regime


def kelly_fraction(p_win, b=1.0):
    """f* = (p*b - q) / b  with b=1 (1:1 simplified odds)."""
    q = 1.0 - p_win
    f = (p_win * b - q) / b
    return max(f, 0.0)


def decide(ticket, regime, capital, cumulative_pnl):
    """
    Evaluate one option ticket and return a decision dict.

    ticket keys:
      option_type  : 'call' or 'put'
      action       : 'buy' or 'sell'
      p_independent: float -- model ITM probability
      q_market     : float -- market-implied ITM probability
      half_spread  : float -- (ask-bid)/2 per share
      mid_price    : float -- option mid price per share
      V_market     : float -- market limit price (same as mid_price here)

    regime : 'normal' or 'herding'
    capital: float -- total capital base
    cumulative_pnl: float -- running P&L (negative = loss)
    """
    p   = ticket["p_independent"]
    q   = ticket["q_market"]

    # For sell tickets, the model edge is reversed
    raw_edge = (p - q) if ticket["action"] == "buy" else (q - p)

    net_edge = compute_net_edge(
        raw_edge, ticket["half_spread"], ticket["mid_price"]
    )
    min_edge = min_edge_for_regime(regime)

    # Kelly fraction based on p_win = p if buy, (1-p) if sell
    p_win   = p if ticket["action"] == "buy" else (1.0 - p)
    f_full  = kelly_fraction(p_win)
    f_half  = f_full / 2
    f_qtr   = f_full / 4

    dollar_full  = f_full  * capital
    dollar_half  = f_half  * capital
    dollar_qtr   = f_qtr   * capital

    trade, reason = should_trade(
        net_edge, min_edge, dollar_full, capital, cumulative_pnl
    )

    return {
        "option_type"  : ticket["option_type"],
        "action"       : ticket["action"],
        "p_independent": round(p, 4),
        "q_market"     : round(q, 4),
        "raw_edge"     : round(raw_edge, 5),
        "net_edge"     : round(net_edge, 5),
        "regime"       : regime,
        "min_edge"     : min_edge,
        "f_full"       : round(f_full, 4),
        "dollar_full"  : round(dollar_full, 2),
        "dollar_half"  : round(dollar_half, 2),
        "dollar_qtr"   : round(dollar_qtr, 2),
        "trade_signal" : "TRADE" if trade else "NO TRADE",
        "reason"       : reason,
    }


def run_policy(tickets, regime, capital=100_000, cumulative_pnl=0.0):
    """Evaluate a list of tickets and return a results DataFrame."""
    rows = [decide(t, regime, capital, cumulative_pnl) for t in tickets]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Demo using AMD ticket values from Fidelity order tickets
    # p_independent is set to a hypothetical forecast value (IV=65% scenario)
    # to demonstrate what a non-zero edge looks like
    print("=== policy.py -- AMD $350 demonstration ===\n")

    amd_tickets = [
        {"option_type": "call", "action": "buy",
         "p_independent": 0.42,   # model says 42% chance call expires ITM
         "q_market": 0.40,        # market implies ~40% (rough call proxy)
         "half_spread": 0.40,     "mid_price": 19.00, "V_market": 18.95},
        {"option_type": "call", "action": "sell",
         "p_independent": 0.42,
         "q_market": 0.40,
         "half_spread": 0.40,     "mid_price": 19.00, "V_market": 18.95},
        {"option_type": "put",  "action": "buy",
         "p_independent": 0.62,   # model says 62% chance put expires ITM
         "q_market": 0.60,        # market implies ~60% (rough put proxy)
         "half_spread": 0.60,     "mid_price": 27.00, "V_market": 27.00},
        {"option_type": "put",  "action": "sell",
         "p_independent": 0.62,
         "q_market": 0.60,
         "half_spread": 0.60,     "mid_price": 27.00, "V_market": 27.00},
    ]

    for regime in ["normal", "herding"]:
        print(f"--- Regime: {regime.upper()} "
              f"(min edge: {min_edge_for_regime(regime):.0%}) ---")
        results = run_policy(amd_tickets, regime=regime, capital=100_000)
        cols = ["option_type", "action", "p_independent", "q_market",
                "net_edge", "regime", "dollar_half", "trade_signal", "reason"]
        print(results[cols].to_string(index=False))
        print()
