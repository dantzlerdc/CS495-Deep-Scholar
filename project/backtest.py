"""
backtest.py -- Layer 2, Step 7
Walk-forward historical backtest using the full Layer 2 policy.
Trains p_estimator on past data, tests on the next period, rolls forward.
Reports P&L distribution, Sharpe, max drawdown, hit rate, and Brier score.
Saves pnl_curve.png to project/outputs/.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss

from market_data   import load_prepared, CALL_FEATURES, PUT_FEATURES
from p_estimator   import _build_model, predict_p
from bias_detector import compute_atm_iv, compute_regime
from micro_cost    import compute_net_edge, should_trade
from bias_detector import min_edge_for_regime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CAPITAL      = 100_000
TRAIN_MONTHS = 12    # months of history for each training window
TEST_MONTHS  = 3     # months per test window


def run_backtest(df, option_type="put", capital=CAPITAL):
    """
    Walk-forward backtest:
      - Sort by QUOTE_DATE
      - For each window: train on TRAIN_MONTHS, test on next TEST_MONTHS
      - Record trade decisions and realized P&L
    Returns a DataFrame of trade records.
    """
    features = PUT_FEATURES if option_type == "put" else CALL_FEATURES
    label    = "put_itm"    if option_type == "put" else "call_itm"

    df = df.sort_values("QUOTE_DATE").reset_index(drop=True)

    # Build regime labels
    daily = compute_atm_iv(df)
    daily = compute_regime(daily)
    regime_map = dict(zip(daily["QUOTE_DATE"], daily["regime"]))

    dates      = df["QUOTE_DATE"].unique()
    dates      = pd.Series(sorted(dates))
    min_date   = dates.min()

    records        = []
    cumulative_pnl = 0.0
    halted         = False

    # Walk-forward windows
    start_idx = 0
    while True:
        train_end_date = min_date + pd.DateOffset(months=TRAIN_MONTHS +
                                                  start_idx * TEST_MONTHS)
        test_end_date  = train_end_date + pd.DateOffset(months=TEST_MONTHS)

        train_mask = (df["QUOTE_DATE"] >= min_date) & \
                     (df["QUOTE_DATE"] <  train_end_date)
        test_mask  = (df["QUOTE_DATE"] >= train_end_date) & \
                     (df["QUOTE_DATE"] <  test_end_date)

        if test_mask.sum() < 50:
            break   # not enough test data

        train_df = df[train_mask]
        test_df  = df[test_mask]

        # Train model on this window
        X_train = train_df[features].values
        y_train = train_df[label].values
        if len(np.unique(y_train)) < 2:
            start_idx += 1
            continue

        scaler  = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        model   = _build_model()
        try:
            model.fit(X_train, y_train)
        except Exception:
            start_idx += 1
            continue

        # Evaluate on test window
        X_test  = scaler.transform(test_df[features].values)
        y_test  = test_df[label].values
        p_pred  = model.predict_proba(X_test)[:, 1]
        bs      = brier_score_loss(y_test, p_pred)

        for i, (_, row) in enumerate(test_df.iterrows()):
            if halted:
                break

            p_ind  = p_pred[i]
            regime = regime_map.get(row["QUOTE_DATE"], "normal")
            min_edge = min_edge_for_regime(regime)

            # Market-implied probability proxy
            if option_type == "put":
                mid       = (row["P_BID"] + row["P_ASK"]) / 2
                half_spread = (row["P_ASK"] - row["P_BID"]) / 2
                q_market  = mid / row["STRIKE"] if row["STRIKE"] > 0 else 0.5
                outcome   = int(row["put_itm"])
            else:
                mid       = (row["C_BID"] + row["C_ASK"]) / 2
                half_spread = (row["C_ASK"] - row["C_BID"]) / 2
                q_market  = mid / row["UNDERLYING_LAST"] \
                            if row["UNDERLYING_LAST"] > 0 else 0.5
                outcome   = int(row["call_itm"])

            if mid <= 0 or np.isnan(mid):
                continue

            raw_edge = p_ind - q_market
            net_edge = compute_net_edge(raw_edge, half_spread, mid)

            f   = max((p_ind - (1 - p_ind)), 0.0)
            pos = f * capital * 0.25   # quarter-Kelly for backtest conservatism

            trade, reason = should_trade(
                net_edge, min_edge, pos, capital, cumulative_pnl)

            if trade:
                pnl = pos * (1 if outcome == 1 else -1)
                cumulative_pnl += pnl
                if cumulative_pnl < -0.15 * capital:
                    halted = True
                records.append({
                    "date"           : row["QUOTE_DATE"],
                    "option_type"    : option_type,
                    "strike"         : row["STRIKE"],
                    "dte"            : row["DTE"],
                    "regime"         : regime,
                    "p_independent"  : round(p_ind, 4),
                    "q_market"       : round(q_market, 4),
                    "net_edge"       : round(net_edge, 5),
                    "outcome"        : outcome,
                    "trade_pnl"      : round(pnl, 2),
                    "cumulative_pnl" : round(cumulative_pnl, 2),
                    "brier_window"   : round(bs, 4),
                    "halted"         : halted,
                })

        start_idx += 1

    return pd.DataFrame(records)


def compute_metrics(trades):
    if trades.empty:
        return {}
    pnl     = trades["trade_pnl"]
    cum_pnl = trades["cumulative_pnl"]
    hit_rate  = (pnl > 0).mean()
    sharpe    = pnl.mean() / pnl.std() * np.sqrt(252) if pnl.std() > 0 else 0
    drawdown  = (cum_pnl.cummax() - cum_pnl).max()
    total_pnl = cum_pnl.iloc[-1] if len(cum_pnl) else 0
    return {
        "n_trades"   : len(trades),
        "hit_rate"   : round(hit_rate, 3),
        "total_pnl"  : round(total_pnl, 2),
        "sharpe"     : round(sharpe, 3),
        "max_drawdown": round(drawdown, 2),
        "avg_brier"  : round(trades["brier_window"].mean(), 4),
    }


def plot_pnl(trades, path=None):
    if path is None:
        path = os.path.join(OUTPUT_DIR, "pnl_curve.png")
    if trades.empty:
        print("  No trades to plot.")
        return

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=False)
    fig.suptitle("Walk-Forward Backtest -- P&L Summary",
                 fontsize=13, fontweight="bold")

    # Panel 1 -- Cumulative P&L
    axes[0].plot(trades["date"], trades["cumulative_pnl"],
                 color="#2563EB", lw=1.5)
    axes[0].axhline(0, color="gray", lw=0.8, ls="--")
    axes[0].fill_between(trades["date"], trades["cumulative_pnl"], 0,
                         where=(trades["cumulative_pnl"] >= 0),
                         color="#059669", alpha=0.3, label="Profit")
    axes[0].fill_between(trades["date"], trades["cumulative_pnl"], 0,
                         where=(trades["cumulative_pnl"] < 0),
                         color="#DC2626", alpha=0.3, label="Loss")
    axes[0].set_ylabel("Cumulative P&L ($)")
    axes[0].set_title("Cumulative P&L (Quarter-Kelly sizing)")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=0.3)

    # Panel 2 -- P&L distribution
    axes[1].hist(trades["trade_pnl"], bins=40,
                 color="#7C3AED", alpha=0.7, edgecolor="white")
    axes[1].axvline(0, color="black", lw=1)
    axes[1].axvline(trades["trade_pnl"].mean(), color="#FBBF24",
                    lw=1.5, ls="--", label=f"Mean ${trades['trade_pnl'].mean():.2f}")
    axes[1].set_xlabel("Trade P&L ($)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Trade P&L Distribution")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved P&L curve -> {path}")


if __name__ == "__main__":
    print("Loading dataset (20% sample for backtest speed) ...")
    df = load_prepared(sample_frac=0.20)

    print("\nRunning walk-forward backtest (put options) ...")
    put_trades = run_backtest(df, option_type="put")
    put_metrics = compute_metrics(put_trades)

    print("\nRunning walk-forward backtest (call options) ...")
    call_trades = run_backtest(df, option_type="call")
    call_metrics = compute_metrics(call_trades)

    print("\n=== PUT Backtest Results ===")
    for k, v in put_metrics.items():
        print(f"  {k:15s}: {v}")

    print("\n=== CALL Backtest Results ===")
    for k, v in call_metrics.items():
        print(f"  {k:15s}: {v}")

    all_trades = pd.concat([put_trades, call_trades]).sort_values("date")
    all_trades["cumulative_pnl"] = all_trades["trade_pnl"].cumsum()

    print("\nGenerating P&L curve plot ...")
    plot_pnl(all_trades)

    csv_path = os.path.join(OUTPUT_DIR, "backtest_trades.csv")
    all_trades.to_csv(csv_path, index=False)
    print(f"Saved trade log -> {csv_path}")
    print("\nBacktest complete.")
