"""End-to-end pipeline runner — AMD CRR binomial + Kelly Criterion."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import build_option_chain_df, compute_time_to_expiry, fetch_realized_volatility, load_config
from edge import compute_edges
from greeks import compute_greeks
from kelly import compute_kelly_recommendations
from simulation import run_kelly_simulations
from tree import price_american_option

OUTPUT = Path("outputs")


# ── Stage helpers ──────────────────────────────────────────────────────────────

def stage1_ingest(config_path: str) -> tuple[dict, pd.DataFrame, float]:
    print("─" * 60)
    print("Stage 1 · Data ingestion")
    config = load_config(config_path)
    T = compute_time_to_expiry(config["amd"]["collection_date"], config["amd"]["expiry_date"])
    print(f"  T = {T:.4f} years  ({T * 365:.1f} calendar days to expiry)")
    print(f"  Fetching AMD realized volatility …")
    rv = fetch_realized_volatility("AMD")
    print(f"  RV-30d = {rv['rv30']:.2%}   RV-60d = {rv['rv60']:.2%}")
    chain = build_option_chain_df(config, T, rv)
    print(chain[["ticket_id", "action", "option_type", "K", "iv", "V_market",
                  "iv_premium_rv30", "moneyness"]].round(4).to_string(index=False))
    chain.to_csv(OUTPUT / "chain.csv", index=False)
    return config, chain, T


def stage2_price(chain: pd.DataFrame, N: int) -> None:
    print("\n─" * 60)
    print("Stage 2 · CRR binomial tree pricing")
    rows = []
    for _, row in chain.iterrows():
        price, _ = price_american_option(
            row["S"], row["K"], row["r"], row["iv"], row["T"], N, row["option_type"]
        )
        rows.append({"ticket_id": row["ticket_id"], "V_model": round(price, 4), "V_market": row["V_market"]})
    df = pd.DataFrame(rows)
    df["pct_error"] = ((df["V_model"] - df["V_market"]) / df["V_market"] * 100).round(2)
    print(df.to_string(index=False))


def stage3_greeks(chain: pd.DataFrame, N: int) -> pd.DataFrame:
    print("\n─" * 60)
    print("Stage 3 · Greeks (centered finite differences)")
    rows = []
    for _, row in chain.iterrows():
        g = compute_greeks(row["S"], row["K"], row["r"], row["iv"], row["T"], N, row["option_type"])
        rows.append({"ticket_id": row["ticket_id"], "action": row["action"],
                     "option_type": row["option_type"], "K": row["K"], **g})
    gdf = pd.DataFrame(rows)
    cols = ["ticket_id", "action", "option_type", "K", "iv", "delta", "gamma", "theta", "vega", "rho"]
    print(gdf[cols].round(4).to_string(index=False))
    gdf.to_csv(OUTPUT / "greeks.csv", index=False)
    return gdf


def stage4_edge(chain: pd.DataFrame, N: int) -> pd.DataFrame:
    print("\n─" * 60)
    print("Stage 4 · Mispricing edge  (V_model − V_market) / V_market")
    edf = compute_edges(chain, N)
    print(edf[["ticket_id", "action", "option_type", "K",
               "V_model", "V_market", "edge_pct"]].round(3).to_string(index=False))
    edf.to_csv(OUTPUT / "edges.csv", index=False)
    return edf


def stage5_kelly(edge_df: pd.DataFrame, chain: pd.DataFrame, config: dict) -> pd.DataFrame:
    print("\n─" * 60)
    print("Stage 5 · Kelly Criterion sizing")
    kdf = compute_kelly_recommendations(
        edge_df, chain,
        capital=config["kelly"]["capital"],
        min_edge=config["kelly"]["min_edge"],
    )
    print(kdf[["ticket_id", "action", "K", "edge_pct", "p_win",
               "f_half", "dollar_half", "trade_signal"]].to_string(index=False))
    kdf.to_csv(OUTPUT / "kelly.csv", index=False)

    print("\n  Monte Carlo P&L simulation (1 000 trades per variant)")
    sdf = run_kelly_simulations(kdf, capital=config["kelly"]["capital"])
    if not sdf.empty:
        print(sdf[["ticket_id", "kelly_variant", "hit_rate",
                    "total_pnl", "max_drawdown", "sharpe_annualized"]].to_string(index=False))
    sdf.to_csv(OUTPUT / "simulation.csv", index=False)
    return kdf, sdf


# ── Plots ──────────────────────────────────────────────────────────────────────

def _label(row) -> str:
    return f"T{int(row.ticket_id)}\n{row.action[:1].upper()}{row.option_type[:1].upper()}\nK={row.K}"


def plot_model_vs_market(edge_df: pd.DataFrame) -> None:
    labels = [_label(r) for _, r in edge_df.iterrows()]
    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, edge_df["V_model"], w, label="CRR model", color="steelblue")
    ax.bar(x + w / 2, edge_df["V_market"], w, label="Market limit", color="coral")
    for xi, (_, row) in zip(x, edge_df.iterrows()):
        sign = "+" if row["edge_pct"] >= 0 else ""
        ax.text(xi, max(row["V_model"], row["V_market"]) + 0.3,
                f"{sign}{row['edge_pct']:.1f}%", ha="center", fontsize=8, color="black")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Option price ($)")
    ax.set_title("CRR Model vs Market Price — AMD Tickets")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT / "model_vs_market.png", dpi=150)
    plt.close()
    print("  Saved: model_vs_market.png")


def plot_convergence(chain: pd.DataFrame) -> None:
    steps = [5, 10, 25, 50, 100, 150, 200]
    fig, ax = plt.subplots(figsize=(9, 5))
    for _, row in chain.iterrows():
        prices = [
            price_american_option(row["S"], row["K"], row["r"], row["iv"], row["T"], n, row["option_type"])[0]
            for n in steps
        ]
        lbl = f"T{int(row['ticket_id'])} {row['action'][:1].upper()}{row['option_type'][:1].upper()} K={row['K']}"
        ax.plot(steps, prices, marker="o", label=lbl)
    ax.set_xlabel("Steps (N)")
    ax.set_ylabel("CRR price ($)")
    ax.set_title("Binomial Tree Convergence by Step Count")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT / "convergence.png", dpi=150)
    plt.close()
    print("  Saved: convergence.png")


def plot_kelly_fractions(kelly_df: pd.DataFrame) -> None:
    labels = [_label(r) for _, r in kelly_df.iterrows()]
    x = np.arange(len(labels))
    w = 0.25
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w,     kelly_df["f_full"]    * 100, w, label="Full Kelly",    color="firebrick",  alpha=0.85)
    ax.bar(x,         kelly_df["f_half"]    * 100, w, label="Half Kelly",    color="darkorange", alpha=0.85)
    ax.bar(x + w,     kelly_df["f_quarter"] * 100, w, label="Quarter Kelly", color="goldenrod",  alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Kelly fraction (%)")
    ax.set_title("Kelly Fractions by Ticket")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT / "kelly_fractions.png", dpi=150)
    plt.close()
    print("  Saved: kelly_fractions.png")


def plot_early_exercise_boundary(chain: pd.DataFrame, config: dict, N: int) -> None:
    puts = chain[chain["option_type"] == "put"]
    if puts.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 5))
    for _, row in puts.iterrows():
        _, boundary = price_american_option(
            row["S"], row["K"], row["r"], row["iv"], row["T"], N, "put"
        )
        valid = ~np.isnan(boundary)
        if not np.any(valid):
            continue
        dt = row["T"] / N
        days = np.arange(N + 1) * dt * 365
        lbl = f"T{int(row['ticket_id'])} Put K={row['K']}"
        ax.plot(days[valid], boundary[valid], marker=".", markersize=3, label=lbl)
    ax.axhline(config["amd"]["S"], color="gray", linestyle="--",
               label=f"Current S = {config['amd']['S']}")
    ax.set_xlabel("Days from collection date")
    ax.set_ylabel("Critical stock price S* ($)")
    ax.set_title("Early Exercise Boundary — AMD American Puts")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT / "early_exercise_boundary.png", dpi=150)
    plt.close()
    print("  Saved: early_exercise_boundary.png")


# ── Main ───────────────────────────────────────────────────────────────────────

def run(config_path: str = "config.yaml") -> None:
    OUTPUT.mkdir(exist_ok=True)

    config, chain, T = stage1_ingest(config_path)
    N = config["model"]["N"]

    stage2_price(chain, N)
    stage3_greeks(chain, N)
    edge_df = stage4_edge(chain, N)
    kelly_df, sim_df = stage5_kelly(edge_df, chain, config)

    print("\n─" * 60)
    print("Stage 6 · Plots")
    plot_model_vs_market(edge_df)
    plot_convergence(chain)
    plot_kelly_fractions(kelly_df)
    plot_early_exercise_boundary(chain, config, N)

    print("\n" + "═" * 60)
    print(f"Pipeline complete.  Outputs written to: {OUTPUT.resolve()}")


if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    run(cfg)
