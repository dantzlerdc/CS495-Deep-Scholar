"""Monte Carlo P&L simulation for Kelly strategy evaluation."""

import numpy as np
import pandas as pd


def simulate_pnl(
    p_win: float,
    f: float,
    capital: float,
    n_trades: int = 1000,
    rng_seed: int = 42,
) -> dict:
    """
    Simulate n_trades binary (win/lose) outcomes under Kelly fraction f.

    Each round, the bet size is f * capital (fixed-fractional sizing).
    Win → +bet, Lose → -bet.

    Returns summary statistics and the cumulative P&L path.
    """
    rng = np.random.default_rng(rng_seed)
    wins = rng.random(n_trades) < p_win
    bet = f * capital
    pnl = np.where(wins, bet, -bet)
    cum_pnl = np.cumsum(pnl)

    running_max = np.maximum.accumulate(cum_pnl)
    drawdowns = cum_pnl - running_max
    max_dd = float(np.min(drawdowns))

    std = float(np.std(pnl))
    sharpe = float(np.mean(pnl) / (std + 1e-10) * np.sqrt(252))

    return {
        "n_trades":          n_trades,
        "hit_rate":          float(np.mean(wins)),
        "total_pnl":         float(cum_pnl[-1]),
        "mean_trade_pnl":    float(np.mean(pnl)),
        "std_trade_pnl":     std,
        "max_drawdown":      max_dd,
        "sharpe_annualized": sharpe,
        "cum_pnl":           cum_pnl,
    }


def run_kelly_simulations(
    kelly_df: pd.DataFrame,
    capital: float = 100_000,
) -> pd.DataFrame:
    """Run Monte Carlo for every ticket × Kelly variant with non-zero fraction."""
    rows = []
    for _, krow in kelly_df.iterrows():
        for variant, f_col in [("full", "f_full"), ("half", "f_half"), ("quarter", "f_quarter")]:
            f = krow[f_col]
            if f <= 0:
                continue
            stats = simulate_pnl(p_win=krow["p_win"], f=f, capital=capital)
            rows.append({
                "ticket_id":          krow["ticket_id"],
                "action":             krow["action"],
                "option_type":        krow["option_type"],
                "K":                  krow["K"],
                "kelly_variant":      variant,
                "f":                  round(f, 4),
                "hit_rate":           round(stats["hit_rate"], 4),
                "total_pnl":          round(stats["total_pnl"], 2),
                "max_drawdown":       round(stats["max_drawdown"], 2),
                "sharpe_annualized":  round(stats["sharpe_annualized"], 4),
            })
    return pd.DataFrame(rows)
