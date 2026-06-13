"""
crr_binomial_pricing_amd_html.py
CRR Binomial Tree -- AMD $350 American Put, step-by-step construction animation.
Appends Stage 2 pricing results and key takeaways at the end.
Saves a self-contained HTML file; also displays in Jupyter via %run.

Run with:
    python crr_binomial_pricing_amd_html.py
    %run crr_binomial_pricing_amd_html.py   (Jupyter)
"""

import io, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_HTML = "crr_pipeline_animation.html"

# ── Parameters: AMD $350 American Put (pipeline IV, N=4 for visual) ───
S0, K, r, sigma = 341.35, 350.0, 0.053, 0.7473   # put IV from pipeline
T_days, N       = 18, 4        # N=4 for visual clarity; pipeline uses N=100
N_pipeline      = 100
HOLD            = 3

call_iv = 0.7392
put_iv  = 0.7473
rv30    = 0.6549

T    = T_days / 365.0
dt   = T / N
u    = np.exp(sigma * np.sqrt(dt))
d    = 1.0 / u
p    = (np.exp(r * dt) - d) / (u - d)
q    = 1.0 - p
disc = np.exp(-r * dt)

# ── Build stock + option trees ────────────────────────────────────────
stock   = [[S0 * (u**(i-j)) * (d**j) for j in range(i+1)] for i in range(N+1)]
intr    = [[max(K - stock[i][j], 0)   for j in range(i+1)] for i in range(N+1)]
opt     = [[None]*(i+1)               for i in range(N+1)]
ex_flag = [[False]*(i+1)              for i in range(N+1)]

for j in range(N+1):
    opt[N][j] = intr[N][j]
for i in range(N-1, -1, -1):
    for j in range(i+1):
        cont      = disc * (p * opt[i+1][j] + (1-p) * opt[i+1][j+1])
        opt[i][j] = max(intr[i][j], cont)
        if intr[i][j] > cont and intr[i][j] > 0:
            ex_flag[i][j] = True

def pos(i, j):
    return float(i), float(i - 2*j)

# ── Palette (identical to crr_animation_html.py) ──────────────────────
BG        = '#0d1117'
PANEL     = '#161b22'
NODE_FWD  = '#2563eb'
NODE_ITM  = '#16a34a'
NODE_OTM  = '#6b7280'
NODE_EX   = '#f59e0b'
NODE_CONT = '#0e7490'
EDGE_U    = '#3b82f6'
EDGE_D    = '#64748b'
WHITE     = '#f1f5f9'
DIM       = '#94a3b8'
GOLD      = '#fbbf24'
PINK      = '#e879f9'
NODE_R    = 0.28

# ── Drawing helpers (identical to crr_animation_html.py) ──────────────

def draw_node(ax, i, j, face, line1, line2=None):
    x, y = pos(i, j)
    ax.add_patch(plt.Circle((x, y), NODE_R, color=face, zorder=5,
                             lw=1.4, ec='#ffffff18'))
    ax.text(x, y + 0.07, line1, ha='center', va='center',
            fontsize=7.2, color=WHITE, fontweight='bold', zorder=6)
    if line2:
        ax.text(x, y - 0.18, line2, ha='center', va='center',
                fontsize=6.5, color=DIM, zorder=6)

def draw_edge(ax, i, j, direction):
    x0, y0 = pos(i, j)
    x1, y1 = pos(i+1, j) if direction == 'up' else pos(i+1, j+1)
    color   = EDGE_U if direction == 'up' else EDGE_D
    dx, dy  = x1-x0, y1-y0
    ln      = np.sqrt(dx**2 + dy**2)
    ux, uy  = dx/ln, dy/ln
    ax.annotate('', xy=(x1 - ux*NODE_R, y1 - uy*NODE_R),
                 xytext=(x0 + ux*NODE_R, y0 + uy*NODE_R),
                 arrowprops=dict(arrowstyle='->', color=color, lw=1.3), zorder=4)

def draw_info_panel(axL, phase):
    axL.clear()
    axL.set_facecolor(PANEL)
    axL.set_xticks([]); axL.set_yticks([])
    for sp in axL.spines.values():
        sp.set_color('#30363d')

    y = 0.97
    def hd(txt, col=WHITE):
        nonlocal y
        axL.text(0.07, y, txt, transform=axL.transAxes, color=col,
                 fontsize=10, fontweight='bold', va='top')
        y -= 0.055

    def ln(txt, col=DIM, mono=False):
        nonlocal y
        axL.text(0.09, y, txt, transform=axL.transAxes, color=col,
                 fontsize=8, va='top',
                 family='monospace' if mono else 'sans-serif')
        y -= 0.044

    def sw(r2, g2, b2, label, desc):
        nonlocal y
        axL.add_patch(plt.Circle((0.075, y - 0.01), 0.026,
                                 color=(r2/255, g2/255, b2/255),
                                 transform=axL.transAxes, clip_on=False))
        axL.text(0.13, y, label, transform=axL.transAxes,
                 color=(r2/255, g2/255, b2/255),
                 fontsize=8, fontweight='bold', va='top')
        axL.text(0.30, y, desc, transform=axL.transAxes,
                 color=DIM, fontsize=7.8, va='top')
        y -= 0.044

    hd('AMD Parameters', WHITE)
    ln(f'S  = ${S0}',           WHITE, True)
    ln(f'K  = ${K:.2f}',        WHITE, True)
    ln(f'r  = {r:.1%}',         WHITE, True)
    ln(f'IV = {sigma:.2%} (put)',WHITE, True)
    ln(f'T  = {T_days}d',       WHITE, True)
    ln(f'N  = {N} (visual)',    WHITE, True)
    y -= 0.01
    hd('CRR Formulas', WHITE)
    ln(f'u = {u:.4f}', mono=True)
    ln(f'd = {d:.4f}', mono=True)
    ln(f'p = {p:.4f}', mono=True)
    y -= 0.01

    if phase in ('intro', 'forward'):
        hd('Forward Pass', EDGE_U)
        ln('S(i,j)=S*u^(i-j)*d^j', GOLD, True)
        y -= 0.01
        hd('Legend', DIM)
        sw(37, 99, 235, 'Blue ', 'Stock price node')
    elif phase == 'terminal':
        hd('Terminal Payoffs', '#4ade80')
        ln('V = max(K - S, 0)', GOLD, True)
        y -= 0.01
        hd('Legend', DIM)
        sw(22, 163,  74, 'Green', 'In the money')
        sw(107,114, 128, 'Gray ', 'Out of the money')
    elif phase == 'backward':
        hd('Backward Induction', GOLD)
        ln('hold=disc*(p*Vu+q*Vd)', GOLD, True)
        ln('V = max(hold, exer)',    GOLD, True)
        y -= 0.01
        hd('Legend', DIM)
        sw(22, 163,  74, 'Green', 'ITM at terminal')
        sw(107,114, 128, 'Gray ', 'OTM at terminal')
        sw(245,158,  11, 'Amber', 'Early exercise')
        sw( 14,116, 144, 'Teal ', 'Continuation')

    axL.text(0.5, 0.02, 'CS495 Deep Scholar | AMD $350 Options',
             transform=axL.transAxes, color='#334155',
             fontsize=7, ha='center', va='bottom')

# ── Phase metadata ────────────────────────────────────────────────────
phase_titles = {
    'intro':     'CRR Binomial Tree -- AMD $350 American Put  (N=4 visual | N=100 pipeline)',
    'forward':   'Phase 1: Forward Pass -- Building Stock Price Lattice',
    'terminal':  'Phase 2: Terminal Payoffs -- max(K - S, 0)',
    'backward':  'Phase 3: Backward Induction -- American Put Pricing',
    'pricing':   'Stage 2 Results: CRR Model vs Market Price -- AMD $350 Strike (N=100)',
    'takeaways': 'Key Takeaways -- CRR Binomial Pricing + AMD Options Analysis',
}

phase_labels = {
    'intro':     'Intro -- AMD Parameters',
    'forward':   'Phase 1: Forward Pass',
    'terminal':  'Phase 2: Terminal Payoffs',
    'backward':  'Phase 3: Backward Induction',
    'pricing':   'Stage 2 Results -- CRR Pricing vs Market',
    'takeaways': 'Key Takeaways',
}

# ── Tree frame builder (identical logic to crr_animation_html.py) ─────

def build_frame(phase, fwd_col, bwd_col):
    fig = plt.figure(figsize=(14, 7.5), facecolor=BG)
    ax  = fig.add_axes([0.02, 0.09, 0.65, 0.83], facecolor=BG)
    axL = fig.add_axes([0.70, 0.09, 0.28, 0.83], facecolor=PANEL)

    for sp in ax.spines.values():  sp.set_visible(False)
    for sp in axL.spines.values(): sp.set_color('#30363d')
    axL.set_xticks([]); axL.set_yticks([])

    ax.set_xlim(-0.6, N + 0.6)
    ax.set_ylim(-N - 1.1, N + 1.1)
    ax.set_yticks([])
    ax.set_xticks(range(N+1))
    ax.set_xticklabels(
        [f'Step {i}\n({i*dt*365:.1f}d)' for i in range(N+1)],
        color=DIM, fontsize=8)
    ax.tick_params(length=0)
    for i in range(N+1):
        ax.axvline(i, color='#1c2333', lw=0.7, zorder=0)

    fig.text(0.02 + 0.65/2, 0.97, phase_titles[phase],
             ha='center', va='top', color=WHITE, fontsize=11, fontweight='bold')

    for i in range(min(fwd_col, N)):
        for j in range(i+1):
            draw_edge(ax, i, j, 'up')
            draw_edge(ax, i, j, 'down')

    if fwd_col >= 1:
        x0, y0 = pos(0, 0); xu, yu = pos(1, 0); xd, yd = pos(1, 1)
        ax.text((x0+xu)/2+0.13, (y0+yu)/2, f'u={u:.4f}',
                color=EDGE_U, fontsize=7.5, ha='left', va='center', zorder=7)
        ax.text((x0+xd)/2+0.13, (y0+yd)/2, f'd={d:.4f}',
                color=EDGE_D, fontsize=7.5, ha='left', va='center', zorder=7)
        ax.text(-0.55, N+0.6, f'p = {p:.4f}  (prob. up)',
                color=EDGE_U, fontsize=8, zorder=7)
        ax.text(-0.55, N+0.2, f'q = {q:.4f}  (prob. down)',
                color=EDGE_D, fontsize=8, zorder=7)

    for i in range(fwd_col + 1):
        for j in range(i+1):
            s_lbl  = f'${stock[i][j]:.1f}'
            ij_lbl = f'i={i},j={j}'
            if phase in ('intro', 'forward'):
                draw_node(ax, i, j, NODE_FWD, s_lbl, ij_lbl)
            elif phase == 'terminal':
                if i < N:
                    draw_node(ax, i, j, NODE_FWD, s_lbl, ij_lbl)
                else:
                    face = NODE_ITM if intr[i][j] > 0 else NODE_OTM
                    draw_node(ax, i, j, face, s_lbl, f'V=${opt[i][j]:.2f}')
            elif phase == 'backward':
                if i == N:
                    face = NODE_ITM if intr[i][j] > 0 else NODE_OTM
                    draw_node(ax, i, j, face, s_lbl, f'V=${opt[i][j]:.2f}')
                elif i >= bwd_col:
                    face = NODE_EX if ex_flag[i][j] else NODE_CONT
                    draw_node(ax, i, j, face, s_lbl, f'V=${opt[i][j]:.2f}')
                else:
                    draw_node(ax, i, j, NODE_FWD, s_lbl, ij_lbl)

    if phase == 'backward':
        ax.text(-0.55, -(N+0.5),
                'Amber = early exercise optimal  |  Teal = continuation used',
                color=NODE_EX, fontsize=7.5, zorder=7)

    draw_info_panel(axL, phase)
    return fig

# ── Result frame: Stage 2 CRR Pricing ────────────────────────────────

def build_pricing_frame():
    fig = plt.figure(figsize=(14, 7.5), facecolor=BG)

    ax1 = fig.add_axes([0.04, 0.51, 0.61, 0.39], facecolor=BG)   # price bars
    ax2 = fig.add_axes([0.04, 0.11, 0.61, 0.31], facecolor=BG)   # vol bars
    axL = fig.add_axes([0.70, 0.09, 0.28, 0.83], facecolor=PANEL)

    for sp in axL.spines.values(): sp.set_color('#30363d')
    axL.set_xticks([]); axL.set_yticks([])

    fig.text(0.04 + 0.61/2, 0.97, phase_titles['pricing'],
             ha='center', va='top', color=WHITE, fontsize=11, fontweight='bold')

    # ── Top: V_model vs V_market grouped bars ─────────────────────────
    labels  = ['T1\nBUY CALL', 'T2\nSELL CALL', 'T3\nBUY PUT', 'T4\nSELL PUT']
    v_model = [18.9486, 18.9486, 27.0014, 27.0014]
    v_mkt   = [18.9500, 18.9500, 27.0000, 27.0000]
    edges   = [-0.007,  -0.007,  +0.005,  +0.005 ]
    x = np.arange(4)
    w = 0.35

    for sp in ax1.spines.values(): sp.set_color('#30363d')
    ax1.bar(x - w/2, v_model, w, label='CRR Model (N=100)', color=NODE_CONT, alpha=0.9, zorder=3)
    ax1.bar(x + w/2, v_mkt,   w, label='Market Limit Price', color=PINK,      alpha=0.9, zorder=3)

    for xi, (vm, mk, e) in enumerate(zip(v_model, v_mkt, edges)):
        sign = '+' if e >= 0 else ''
        ax1.text(xi, max(vm, mk) + 0.35, f'edge {sign}{e:.3f}%',
                 ha='center', fontsize=8.5, color=GOLD, fontweight='bold', zorder=5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, color=WHITE, fontsize=10)
    ax1.set_ylabel('Option Price ($)', color=DIM, fontsize=9)
    ax1.tick_params(colors=DIM)
    ax1.set_ylim(0, 33)
    ax1.set_facecolor(BG)
    ax1.grid(axis='y', color='#1c2333', lw=0.8, zorder=0)
    ax1.legend(fontsize=9, facecolor=PANEL, edgecolor='#30363d',
               labelcolor=WHITE, loc='upper left')
    ax1.set_title('CRR Model vs Fidelity Market Price  (edges shown above)',
                  color=DIM, fontsize=9, pad=6)

    # ── Bottom: Implied Vol vs Realized Vol ───────────────────────────
    vol_labels = ['Call IV', 'Put IV', 'RV-30d']
    vol_pct    = [call_iv * 100, put_iv * 100, rv30 * 100]
    vol_colors = [NODE_CONT, PINK, EDGE_D]

    for sp in ax2.spines.values(): sp.set_color('#30363d')
    ax2.bar(np.arange(3), vol_pct, color=vol_colors, alpha=0.9, width=0.5, zorder=3)
    ax2.axhline(rv30 * 100, color=EDGE_D, lw=1.3, ls='--', zorder=4)

    for xi, (lbl, pct) in enumerate(zip(vol_labels, vol_pct)):
        ax2.text(xi, pct + 0.8, f'{pct:.2f}%',
                 ha='center', color=WHITE, fontsize=9, fontweight='bold', zorder=5)

    # Annotate IV premium arrows
    for xi, iv_pct in enumerate([call_iv * 100, put_iv * 100]):
        prem = iv_pct - rv30 * 100
        ax2.annotate(
            f'+{prem:.1f}% premium',
            xy=(xi, rv30 * 100), xytext=(xi + 0.28, rv30 * 100 + 3.5),
            color=GOLD, fontsize=8,
            arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.0))

    ax2.set_xticks(np.arange(3))
    ax2.set_xticklabels(vol_labels, color=WHITE, fontsize=10)
    ax2.set_ylabel('Volatility (%)', color=DIM, fontsize=9)
    ax2.tick_params(colors=DIM)
    ax2.set_ylim(0, 90)
    ax2.set_facecolor(BG)
    ax2.grid(axis='y', color='#1c2333', lw=0.8, zorder=0)
    ax2.set_title('Implied Volatility vs Realized Volatility (RV-30d dashed)',
                  color=DIM, fontsize=9, pad=6)

    # ── Right info panel ──────────────────────────────────────────────
    y = 0.97
    def hd(txt, col=WHITE):
        nonlocal y
        axL.text(0.07, y, txt, transform=axL.transAxes,
                 color=col, fontsize=10, fontweight='bold', va='top')
        y -= 0.055

    def ln(txt, col=DIM, mono=False):
        nonlocal y
        axL.text(0.09, y, txt, transform=axL.transAxes, color=col,
                 fontsize=8, va='top',
                 family='monospace' if mono else 'sans-serif')
        y -= 0.044

    hd('Stage 2 Inputs', WHITE)
    ln(f'S = ${S0}   K = ${K:.0f}', WHITE, True)
    ln(f'T = {T_days} days', WHITE, True)
    ln(f'N = {N_pipeline} steps', WHITE, True)
    y -= 0.01
    hd('Call Tickets', NODE_CONT)
    ln(f'IV       = {call_iv:.2%}', GOLD, True)
    ln(f'V_model  = $18.9486', GOLD, True)
    ln(f'V_market = $18.9500', GOLD, True)
    ln(f'Error    =  -0.007%', '#4ade80', True)
    y -= 0.01
    hd('Put Tickets', PINK)
    ln(f'IV       = {put_iv:.2%}', GOLD, True)
    ln(f'V_model  = $27.0014', GOLD, True)
    ln(f'V_market = $27.0000', GOLD, True)
    ln(f'Error    =  +0.005%', '#4ade80', True)
    y -= 0.01
    hd('Vol Analysis', GOLD)
    ln(f'RV-30d  = {rv30:.2%}',           DIM, True)
    ln(f'Call prem= +{call_iv-rv30:.2%}', GOLD, True)
    ln(f'Put  prem= +{put_iv-rv30:.2%}',  GOLD, True)
    y -= 0.01
    ln('Market prices IV above', DIM)
    ln('realized vol by ~8-9%.', DIM)
    ln('Options appear expensive', DIM)
    ln('vs recent AMD moves.', DIM)

    axL.text(0.5, 0.02, 'CS495 Deep Scholar | AMD $350 Options',
             transform=axL.transAxes, color='#334155',
             fontsize=7, ha='center', va='bottom')
    return fig

# ── Result frame: Key Takeaways ───────────────────────────────────────

def build_takeaways_frame():
    fig = plt.figure(figsize=(14, 7.5), facecolor=BG)

    ax  = fig.add_axes([0.02, 0.09, 0.65, 0.83], facecolor=PANEL)
    axL = fig.add_axes([0.70, 0.09, 0.28, 0.83], facecolor=PANEL)

    for sp in ax.spines.values():  sp.set_color('#30363d')
    for sp in axL.spines.values(): sp.set_color('#30363d')
    ax.set_xticks([]); ax.set_yticks([])
    axL.set_xticks([]); axL.set_yticks([])

    fig.text(0.02 + 0.65/2, 0.97, phase_titles['takeaways'],
             ha='center', va='top', color=WHITE, fontsize=11, fontweight='bold')

    takeaways = [
        (NODE_CONT,
         '1.  CRR Model Accuracy < 0.01%',
         f'N={N_pipeline} binomial steps reproduced Fidelity market prices for both',
         'call ($18.95) and put ($27.00) within 0.01% -- well inside the bid-ask spread.'),
        (NODE_EX,
         '2.  IV exceeds Realized Volatility by 8-9%',
         f'Call IV ({call_iv:.2%}) and Put IV ({put_iv:.2%}) both exceed AMD RV-30d',
         f'({rv30:.2%}). The market prices a volatility risk premium above recent moves.'),
        (NODE_ITM,
         '3.  American Put triggers early exercise (amber nodes)',
         'Backward induction finds early exercise optimal at nodes (3,2) and (3,3)',
         'where the put is deep ITM -- holding is suboptimal at those nodes.'),
        (EDGE_U,
         '4.  IV-calibrated model yields no mispricing edge',
         'Because IV is solved from market price (scipy.brentq), CRR reproduces',
         'that price by construction.  |edge| < 0.01% -- noise, not signal.'),
        (GOLD,
         '5.  Kelly Criterion correctly blocks all four trades',
         'With |edge| < 0.01% vs 2% minimum threshold, all Kelly fractions = 0.',
         'No position recommended.  To find edge, use an independent IV forecast.'),
    ]

    y = 0.92
    for col, title, line1, line2 in takeaways:
        ax.add_patch(plt.Circle((0.034, y - 0.010), 0.018,
                                color=col, transform=ax.transAxes,
                                clip_on=False, zorder=5))
        ax.text(0.07, y, title, transform=ax.transAxes,
                color=col, fontsize=10, fontweight='bold', va='top')
        y -= 0.052
        ax.text(0.08, y, line1, transform=ax.transAxes,
                color=WHITE, fontsize=8.5, va='top')
        y -= 0.040
        ax.text(0.08, y, line2, transform=ax.transAxes,
                color=DIM, fontsize=8.5, va='top')
        y -= 0.058

    # ── Right info panel ──────────────────────────────────────────────
    y2 = 0.97
    def hd(txt, col=WHITE):
        nonlocal y2
        axL.text(0.07, y2, txt, transform=axL.transAxes,
                 color=col, fontsize=10, fontweight='bold', va='top')
        y2 -= 0.055

    def ln(txt, col=DIM, mono=False):
        nonlocal y2
        axL.text(0.09, y2, txt, transform=axL.transAxes, color=col,
                 fontsize=8, va='top',
                 family='monospace' if mono else 'sans-serif')
        y2 -= 0.044

    hd('Pipeline Stages', WHITE)
    ln('1: Config + RV + IV solve', DIM)
    ln('2: CRR pricing N=100', DIM)
    ln('3: Greeks finite diff', DIM)
    ln('4: Edge (Vm-Vk)/Vk', DIM)
    ln('5: Kelly f* sizing', DIM)
    ln('6: Charts + reports', DIM)
    y2 -= 0.01
    hd('Final Result', GOLD)
    ln('4 tickets evaluated', WHITE, True)
    ln('0 trades recommended', WHITE, True)
    ln('All |edge| < 2% cutoff', WHITE, True)
    y2 -= 0.01
    hd('Market Data 05/04/26', WHITE)
    ln(f'AMD S   = $341.35', DIM, True)
    ln(f'Strike  = $350.00', DIM, True)
    ln(f'Expiry  = 2026-05-22', DIM, True)
    ln(f'T       = {T_days} days', DIM, True)
    ln(f'r       = {r:.1%}', DIM, True)
    y2 -= 0.01
    hd('Next Steps', NODE_CONT)
    ln('Use forecasted IV to', DIM)
    ln('find edge vs market IV.', DIM)
    ln('Monitor RV compression', DIM)
    ln('for vol-selling signals.', DIM)

    axL.text(0.5, 0.02, 'CS495 Deep Scholar | AMD $350 Options',
             transform=axL.transAxes, color='#334155',
             fontsize=7, ha='center', va='bottom')
    return fig

# ── Frame sequence (same pattern as crr_animation_html.py + result frames)
frames_seq = []
for _  in range(HOLD):        frames_seq.append(('intro',     -1, N+1))
for c  in range(N+1):
    for _ in range(HOLD):     frames_seq.append(('forward',    c, N+1))
for _  in range(HOLD):        frames_seq.append(('forward',    N, N+1))
for _  in range(HOLD):        frames_seq.append(('terminal',   N, N+1))
for c  in range(N-1, -1, -1):
    for _ in range(HOLD):     frames_seq.append(('backward',   N,  c))
for _  in range(HOLD):        frames_seq.append(('backward',   N,  0))
for _  in range(HOLD * 2):    frames_seq.append(('pricing',   None, None))
for _  in range(HOLD * 2):    frames_seq.append(('takeaways', None, None))

TOTAL = len(frames_seq)

# Jump indices for navigation buttons
j_intro     = 0
j_forward   = HOLD
j_terminal  = HOLD + (N + 1) * HOLD + HOLD
j_backward  = j_terminal + HOLD
j_pricing   = j_backward + N * HOLD + HOLD
j_takeaways = j_pricing + HOLD * 2

# ── Pre-render all frames to base64 PNG ──────────────────────────────
print(f"Pre-rendering {TOTAL} frames ...")
b64_frames  = []
frame_descs = []
for k, (ph, fc, bc) in enumerate(frames_seq):
    if k % 10 == 0:
        print(f"  {k}/{TOTAL}")
    if ph in ('intro', 'forward', 'terminal', 'backward'):
        fig = build_frame(ph, fc, bc)
    elif ph == 'pricing':
        fig = build_pricing_frame()
    else:
        fig = build_takeaways_frame()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor=BG, bbox_inches='tight')
    buf.seek(0)
    b64_frames.append(base64.b64encode(buf.getvalue()).decode('ascii'))
    frame_descs.append(f'Frame {k+1}/{TOTAL} | {phase_labels[ph]}')
    plt.close(fig)

print(f"Done -- {TOTAL} frames ready.\n")

# ── Build HTML / JS player (same template as crr_animation_html.py) ──
frames_js = '[' + ','.join(f'"{f}"' for f in b64_frames)  + ']'
descs_js  = '[' + ','.join(f'"{d}"' for d in frame_descs) + ']'

html = f"""
<style>
  #crr-player {{
    background: #0d1117;
    border-radius: 10px;
    padding: 12px 16px;
    font-family: monospace;
    color: #94a3b8;
    max-width: 960px;
  }}
  #crr-player img {{ width: 100%; border-radius: 6px; display: block; }}
  #crr-desc {{
    font-size: 12px; margin: 7px 0 4px 0; color: #94a3b8; letter-spacing: 0.4px;
  }}
  #crr-controls {{
    display: flex; align-items: center; gap: 8px;
    margin-top: 8px; flex-wrap: wrap;
  }}
  .crr-btn {{
    background: #1c2333; color: #f1f5f9; border: 1px solid #30363d;
    border-radius: 5px; padding: 5px 14px; cursor: pointer; font-size: 13px;
    font-family: monospace;
  }}
  .crr-btn:hover {{ background: #2563eb; border-color: #3b82f6; }}
  #crr-slider {{
    flex: 1; min-width: 200px; accent-color: #2563eb;
  }}
  #crr-speed-label {{ font-size: 12px; min-width: 48px; color: #fbbf24; }}
  #crr-speed {{ width: 100px; accent-color: #f59e0b; }}
  #crr-jumps {{
    display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px;
  }}
  .crr-jump {{
    background: #161b22; color: #94a3b8; border: 1px solid #21262d;
    border-radius: 4px; padding: 3px 11px; cursor: pointer;
    font-size: 11px; font-family: monospace;
  }}
  .crr-jump:hover {{ background: #1e3a5f; color: #f1f5f9; border-color: #2563eb; }}
</style>

<div id="crr-player">
  <div id="crr-desc">Frame 1/{TOTAL} | Intro -- AMD Parameters</div>
  <img id="crr-img" src="data:image/png;base64,{b64_frames[0]}" />
  <div id="crr-controls">
    <button class="crr-btn" onclick="crrRestart()">&#8676; Restart</button>
    <button class="crr-btn" onclick="crrStepBack()">&#9664; Step</button>
    <button class="crr-btn" id="crr-play-btn" onclick="crrToggle()">&#9654; Play</button>
    <button class="crr-btn" onclick="crrStepFwd()">Step &#9654;</button>
    <input type="range" id="crr-slider" min="0" max="{TOTAL-1}"
           value="0" oninput="crrSeek(this.value)" />
    <span style="font-size:12px; color:#64748b;">Speed:</span>
    <input type="range" id="crr-speed" min="80" max="900" step="40"
           value="220" oninput="crrSetSpeed(this.value)" />
    <span id="crr-speed-label">Normal</span>
  </div>
  <div id="crr-jumps">
    <span style="font-size:11px;color:#4b5563;align-self:center;">Jump:</span>
    <button class="crr-jump" onclick="crrSeek({j_intro})">Intro</button>
    <button class="crr-jump" onclick="crrSeek({j_forward})">Forward Pass</button>
    <button class="crr-jump" onclick="crrSeek({j_terminal})">Terminal</button>
    <button class="crr-jump" onclick="crrSeek({j_backward})">Backward</button>
    <button class="crr-jump" onclick="crrSeek({j_pricing})">Results</button>
    <button class="crr-jump" onclick="crrSeek({j_takeaways})">Takeaways</button>
  </div>
</div>

<script>
(function() {{
  const frames = {frames_js};
  const descs  = {descs_js};
  let cur = 0, timer = null, interval = 220;

  function show(i) {{
    cur = Math.max(0, Math.min(i, frames.length - 1));
    document.getElementById('crr-img').src = 'data:image/png;base64,' + frames[cur];
    document.getElementById('crr-desc').innerText = descs[cur];
    document.getElementById('crr-slider').value = cur;
  }}

  function crrTick() {{ show((cur + 1) % frames.length); }}

  window.crrToggle = function() {{
    const btn = document.getElementById('crr-play-btn');
    if (timer) {{
      clearInterval(timer); timer = null;
      btn.innerHTML = '&#9654; Play';
    }} else {{
      timer = setInterval(crrTick, interval);
      btn.innerHTML = '&#9646;&#9646; Pause';
    }}
  }};

  window.crrRestart  = function() {{ show(0); }};
  window.crrStepBack = function() {{ show(cur - 1); }};
  window.crrStepFwd  = function() {{ show(cur + 1); }};
  window.crrSeek     = function(v) {{ show(parseInt(v)); }};

  window.crrSetSpeed = function(v) {{
    interval = parseInt(v);
    const lbl = document.getElementById('crr-speed-label');
    lbl.innerText = interval <= 120 ? 'Fast' : interval <= 300 ? 'Normal' : 'Slow';
    if (timer) {{ clearInterval(timer); timer = setInterval(crrTick, interval); }}
  }};
}})();
</script>
"""

# ── Save standalone HTML file ─────────────────────────────────────────
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRR Binomial Tree -- AMD $350 Options | CS495 Deep Scholar</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #060a0f; display: flex; justify-content: center;
          padding: 24px 16px; }}
</style>
</head>
<body>
{html}
</body>
</html>
"""

import os
with open(OUTPUT_HTML, 'w') as f:
    f.write(html_doc)
print(f"Saved: {OUTPUT_HTML}")
print(f"Open:  file://{os.path.abspath(OUTPUT_HTML)}")

# ── Display in Jupyter if available ──────────────────────────────────
try:
    from IPython.display import HTML, display
    display(HTML(html))
except ImportError:
    pass
