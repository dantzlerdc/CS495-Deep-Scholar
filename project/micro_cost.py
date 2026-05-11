"""
micro_cost.py -- Layer 2, Step 4
Compute net edge after subtracting transaction costs:
  - Bid-ask half-spread (paid on entry and exit)
  - Brokerage fee ($0.65 per contract confirmed from AMD Fidelity tickets)
  - Slippage estimate (0.1% of mid price for market impact)
Trade is blocked when net edge < regime-appropriate min_edge threshold.
"""

FEE_PER_CONTRACT  = 0.65    # Fidelity: $0.65/contract (confirmed from AMD tickets)
SHARES_PER_CONTRACT = 100
FEE_PER_SHARE     = FEE_PER_CONTRACT / SHARES_PER_CONTRACT   # $0.0065/share
SLIPPAGE_RATE     = 0.001   # 0.1% of mid price as market impact estimate
VAR_LIMIT_PCT     = 0.05    # max 5% of capital at risk per trade
DRAWDOWN_LIMIT    = 0.15    # halt trading if cumulative loss > 15% of capital


def transaction_cost_per_share(half_spread, mid_price):
    """
    Total round-trip cost per share:
      entry half-spread + exit half-spread + fee (both legs) + slippage
    """
    spread_cost   = 2 * half_spread
    fee_cost      = 2 * FEE_PER_SHARE
    slippage_cost = SLIPPAGE_RATE * mid_price
    return spread_cost + fee_cost + slippage_cost


def compute_net_edge(raw_edge, half_spread, mid_price):
    """
    Deduct transaction costs from raw edge.
    raw_edge     : (V_model - V_market) / V_market  or  p_independent - q_market
    half_spread  : (ask - bid) / 2  in dollars per share
    mid_price    : option mid price in dollars per share
    """
    if mid_price <= 0:
        return -999.0
    cost_frac = transaction_cost_per_share(half_spread, mid_price) / mid_price
    return raw_edge - cost_frac


def check_var(kelly_dollar, capital):
    """Return True if position is within the VaR limit."""
    return kelly_dollar <= VAR_LIMIT_PCT * capital


def check_drawdown(cumulative_pnl, capital):
    """Return True (trading allowed) if drawdown is within limit."""
    return cumulative_pnl >= -DRAWDOWN_LIMIT * capital


def should_trade(net_edge, min_edge, kelly_dollar, capital, cumulative_pnl):
    """
    Master gate: all three conditions must pass to emit a TRADE signal.
    Returns (trade: bool, reason: str)
    """
    if not check_drawdown(cumulative_pnl, capital):
        return False, "HALT -- drawdown circuit breaker triggered"
    if abs(net_edge) < min_edge:
        return False, f"NO TRADE -- net edge {net_edge:.3%} < min {min_edge:.0%}"
    if not check_var(kelly_dollar, capital):
        return False, f"NO TRADE -- position ${kelly_dollar:,.0f} exceeds VaR limit"
    direction = "BUY" if net_edge > 0 else "SELL"
    return True, f"TRADE {direction} -- net edge {net_edge:.3%}"


if __name__ == "__main__":
    print("=== micro_cost.py -- AMD ticket verification ===\n")

    tickets = [
        {"name": "AMD Call (buy/sell)", "half_spread": 0.40,
         "mid": 19.00, "raw_edge": -0.00007, "min_edge": 0.02,
         "kelly_dollar": 0.0, "capital": 100_000, "cum_pnl": 0.0},
        {"name": "AMD Put  (buy/sell)", "half_spread": 0.60,
         "mid": 27.00, "raw_edge":  0.00005, "min_edge": 0.02,
         "kelly_dollar": 0.0, "capital": 100_000, "cum_pnl": 0.0},
    ]

    for t in tickets:
        net = compute_net_edge(t["raw_edge"], t["half_spread"], t["mid"])
        trade, reason = should_trade(
            net, t["min_edge"], t["kelly_dollar"],
            t["capital"], t["cum_pnl"]
        )
        cost = transaction_cost_per_share(t["half_spread"], t["mid"])
        print(f"{t['name']}")
        print(f"  Half-spread      : ${t['half_spread']:.2f}/share")
        print(f"  Round-trip cost  : ${cost:.4f}/share  "
              f"({cost/t['mid']:.3%} of mid)")
        print(f"  Raw edge         : {t['raw_edge']:.4%}")
        print(f"  Net edge         : {net:.4%}")
        print(f"  Decision         : {reason}\n")
