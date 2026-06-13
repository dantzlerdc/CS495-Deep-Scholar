"""
crr_animation_html.py
CRR Binomial Option Tree -- Interactive HTML animation for Jupyter.
No ipywidgets extensions required. Works in any Jupyter environment.

Run with:
    %run ~/crr_animation_html.py
"""

import io, base64
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Parameters ────────────────────────────────────────────────────────
S0, K, r, sigma = 275.10, 280.0, 0.053, 0.65
T_days, N       = 11, 4
HOLD            = 3

T    = T_days / 365.0
dt   = T / N
u    = np.exp(sigma * np.sqrt(dt))
d    = 1.0 / u
p    = (np.exp(r * dt) - d) / (u - d)
q    = 1.0 - p
disc = np.exp(-r * dt)

# ── Build trees ───────────────────────────────────────────────────────
stock   = [[S0 * (u**(i-j)) * (d**j) for j in range(i+1)] for i in range(N+1)]
intr    = [[max(K - stock[i][j], 0)   for j in range(i+1)] for i in range(N+1)]
opt     = [[None]*(i+1)               for i in range(N+1)]
ex_flag = [[False]*(i+1)              for i in range(N+1)]

for j in range(N+1):
    opt[N][j] = intr[N][j]
for i in range(N-1, -1, -1):
    for j in range(i+1):
        cont       = disc * (p * opt[i+1][j] + (1-p) * opt[i+1][j+1])
        opt[i][j]  = max(intr[i][j], cont)
        if intr[i][j] > cont and intr[i][j] > 0:
            ex_flag[i][j] = True

def pos(i, j):
    return float(i), float(i - 2*j)

# ── Palette ───────────────────────────────────────────────────────────
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
NODE_R    = 0.28

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

    hd('Parameters', WHITE)
    ln(f'S  = ${S0}',        WHITE, True)
    ln(f'K  = ${K}',         WHITE, True)
    ln(f'r  = {r:.1%}',      WHITE, True)
    ln(f'IV = {sigma:.0%}',  WHITE, True)
    ln(f'T  = {T_days}d',    WHITE, True)
    ln(f'N  = {N} steps',    WHITE, True)
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

    axL.text(0.5, 0.02, 'CS495 Deep Scholar | AMD Options',
             transform=axL.transAxes, color='#334155',
             fontsize=7, ha='center', va='bottom')

phase_titles = {
    'intro':    'CRR Binomial Tree Construction -- AMD $280 Put',
    'forward':  'Phase 1: Forward Pass -- Building Stock Price Lattice',
    'terminal': 'Phase 2: Terminal Payoffs -- max(K - S, 0)',
    'backward': 'Phase 3: Backward Induction -- American Put Pricing',
}

phase_labels = {
    'intro':    'Intro -- Parameters',
    'forward':  'Phase 1: Forward Pass',
    'terminal': 'Phase 2: Terminal Payoffs',
    'backward': 'Phase 3: Backward Induction',
}

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

# ── Frame sequence ────────────────────────────────────────────────────
frames_seq = []
for _  in range(HOLD):        frames_seq.append(('intro',    -1, N+1))
for c  in range(N+1):
    for _ in range(HOLD):     frames_seq.append(('forward',   c, N+1))
for _  in range(HOLD):        frames_seq.append(('forward',   N, N+1))
for _  in range(HOLD):        frames_seq.append(('terminal',  N, N+1))
for c  in range(N-1, -1, -1):
    for _ in range(HOLD):     frames_seq.append(('backward',  N,  c))
for _  in range(HOLD):        frames_seq.append(('backward',  N,  0))

TOTAL = len(frames_seq)

# ── Pre-render all frames to base64 PNG ───────────────────────────────
print(f"Pre-rendering {TOTAL} frames ...")
b64_frames  = []
frame_descs = []
for k, (ph, fc, bc) in enumerate(frames_seq):
    if k % 10 == 0:
        print(f"  {k}/{TOTAL}")
    fig = build_frame(ph, fc, bc)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, facecolor=BG, bbox_inches='tight')
    buf.seek(0)
    b64_frames.append(base64.b64encode(buf.getvalue()).decode('ascii'))
    frame_descs.append(f'Frame {k+1}/{TOTAL} | {phase_labels[ph]}')
    plt.close(fig)

print(f"Done -- {TOTAL} frames ready.\n")

# ── Build HTML / JS player ─────────────────────────────────────────────
frames_js  = '[' + ','.join(f'"{f}"' for f in b64_frames)  + ']'
descs_js   = '[' + ','.join(f'"{d}"' for d in frame_descs) + ']'

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
</style>

<div id="crr-player">
  <div id="crr-desc">Frame 1/{TOTAL} | Intro -- Parameters</div>
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

standalone = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CRR Binomial Tree -- AMD Options</title>
</head>
<body style="background:#0d1117; margin:20px;">
{html}
</body>
</html>"""

out_path = "crr_pipeline_animation.html"
with open(out_path, "w") as f:
    f.write(standalone)
print(f"Saved -> {out_path}")
