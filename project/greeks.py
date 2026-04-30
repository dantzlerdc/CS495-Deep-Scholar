"""Numerical Greeks via centered finite differences on the CRR tree."""

from tree import price_american_option


def compute_greeks(
    S: float,
    K: float,
    r: float,
    sigma: float,
    T: float,
    N: int,
    option_type: str,
) -> dict:
    """
    Return all six Greeks for one option contract.

    Perturbation sizes follow standard practitioner conventions:
      dS      = 1% of spot (Delta, Gamma)
      dsigma  = 0.01 (1 vol point) for Vega
      dr      = 0.01 (100 bps) for Rho
      dt_day  = 1/365 year for Theta
    """
    dS = S * 0.01
    dsigma = 0.01
    dr = 0.01
    dt_day = 1.0 / 365.0

    def price(s=S, k=K, rate=r, vol=sigma, t=T):
        return price_american_option(s, k, rate, vol, t, N, option_type)[0]

    V0 = price()
    V_sup = price(s=S + dS)
    V_sdn = price(s=S - dS)

    delta = (V_sup - V_sdn) / (2 * dS)
    gamma = (V_sup - 2 * V0 + V_sdn) / (dS ** 2)

    # Theta: value change for one calendar day less to expiry (negative = decay)
    T_short = max(T - dt_day, 1e-8)
    theta = (price(t=T_short) - V0) / dt_day

    vega = (price(vol=sigma + dsigma) - price(vol=sigma - dsigma)) / (2 * dsigma)
    rho  = (price(rate=r + dr)       - price(rate=r - dr))       / (2 * dr)

    return {
        "iv":    sigma,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,   # per calendar day
        "vega":  vega,    # per 1 vol-point (0.01) change
        "rho":   rho,     # per 100 bps (0.01) rate change
    }
