"""CRR American binomial tree — vectorized NumPy implementation."""

import numpy as np


def price_american_option(
    S: float,
    K: float,
    r: float,
    sigma: float,
    T: float,
    N: int,
    option_type: str,
) -> tuple[float, np.ndarray]:
    """
    Price an American option with the Cox-Ross-Rubinstein binomial model.

    No dividend adjustment is applied (AMD scope restriction).
    Early exercise is tested at every interior node via backward induction.

    Returns
    -------
    price : float
        Model fair value at t=0.
    exercise_boundary : ndarray, shape (N+1,)
        exercise_boundary[i] = highest stock price at step i where early
        exercise dominates continuation (puts only; NaN where not applicable).
    """
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp(r * dt) - d) / (u - d)
    discount = np.exp(-r * dt)

    # Terminal stock prices: node j at step N has S * u^(N-j) * d^j
    j = np.arange(N + 1)
    ST = S * (u ** (N - j)) * (d ** j)

    if option_type == "call":
        V = np.maximum(ST - K, 0.0)
    else:
        V = np.maximum(K - ST, 0.0)

    exercise_boundary = np.full(N + 1, np.nan)

    for i in range(N - 1, -1, -1):
        j_i = np.arange(i + 1)
        S_nodes = S * (u ** (i - j_i)) * (d ** j_i)

        if option_type == "call":
            intrinsic = np.maximum(S_nodes - K, 0.0)
        else:
            intrinsic = np.maximum(K - S_nodes, 0.0)

        # Continuation value (risk-neutral expected discounted payoff)
        V_hold = discount * (p * V[: i + 1] + (1 - p) * V[1 : i + 2])

        # American exercise: take the better of hold or exercise
        V = np.maximum(intrinsic, V_hold)

        # Track early-exercise boundary for puts
        if option_type == "put":
            early = intrinsic > V_hold
            if np.any(early):
                # S* = highest price at which immediate exercise beats waiting
                exercise_boundary[i] = float(np.max(S_nodes[early]))

    return float(V[0]), exercise_boundary
