#!/usr/bin/env python3
"""
make_cover_slide.py
Reproduces CRR-Pipeline-Build-Flowchart.pdf page 1 exactly,
scaled to beamer 16:9 (16" × 9"), with the CS495 Research Report
title substituted.  Outputs: cover_slide.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
import matplotlib.patches as mpatches
import numpy as np
import textwrap

# ── Coordinate space ──────────────────────────────────────────────────────────
OW, OH = 11.0, 8.5          # original flowchart dimensions (inches)
FW, FH = 16.0, 9.0          # target: beamer 16:9
SX     = FW / OW             # 1.4545
SY     = FH / OH             # 1.0588

def sx(v): return v * SX
def sy(v): return v * SY
def fs(v): return v * SY     # font size scaled by height ratio

# ── Colors (exact from make_pipeline_flowchart.py) ───────────────────────────
PANEL_BG  = '#0B2041'
DIVIDER   = '#3A7BD5'
LABEL_C   = '#88B8E8'
DESC_C    = '#C8DCF0'
AUTHOR_C  = '#607898'
MUTED     = '#546E7A'
EDGE_C    = '#607D8B'
NODE_FILL = '#E8EDF8'
NODE_EDGE = '#3F5080'
NODE_TXT  = '#1A1A2E'
GRID_C    = '#E8ECF2'
FOOT_LINE = '#B0BEC5'
FOOT_TXT  = '#8898A8'
TERM_CLRS = ['#1A5E20', '#2E7D32', '#F57F17', '#C62828', '#880E4F']
BADGES    = [('L1', 'CRR Pricing Engine',     '#163A8C'),
             ('L2', 'ML Extensions',          '#145A22'),
             ('L3', 'Cross-Model Comparison', '#7A1E00')]

# ── Figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(FW, FH))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FW)
ax.set_ylim(0, FH)
ax.axis('off')

# ── Right panel grid (same logic as original, scaled) ────────────────────────
for gy in np.arange(sy(1.0), sy(8.0), sy(0.62)):
    ax.plot([sx(5.65), FW], [gy, gy], color=GRID_C, lw=0.4, zorder=0)
for gx in np.arange(sx(6.0), FW, sx(0.62)):
    ax.plot([gx, gx], [0, FH], color=GRID_C, lw=0.4, zorder=0)

# ── Dark navy left panel ──────────────────────────────────────────────────────
ax.add_patch(plt.Rectangle((0, 0), sx(5.55), FH,
                             facecolor=PANEL_BG, zorder=2))

# ── Blue vertical stripe ──────────────────────────────────────────────────────
ax.add_patch(plt.Rectangle((sx(5.53), 0), sx(0.07), FH,
                             facecolor=DIVIDER, zorder=3))

# ── Left panel text ───────────────────────────────────────────────────────────
# Top label (same position as original "CS495 Deep Scholar")
ax.text(sx(0.32), sy(7.58), 'CS495 Capstone Project Spring 2026',
        color=LABEL_C, fontsize=fs(11), fontweight='bold',
        va='center', ha='left', zorder=5)

# Main title: research report title in the same 2-line format as original
ax.text(sx(0.32), sy(6.95),
        'Mathematical and Empirical\nModels in Agreement:',
        color='white', fontsize=fs(21), fontweight='bold',
        va='center', ha='left', zorder=5, linespacing=1.3)

# Subtitle: research report subtitle  (original was 1 short line at fontsize=12)
# Using 2–3 lines at fontsize=10 to match vertical space used
ax.text(sx(0.32), sy(5.76),
        'Cross-Validating CRR Binomial Pricing and\n'
        'Machine Learning for Crowd Mispricing\n'
        'Detection in Equity Options',
        color=LABEL_C, fontsize=fs(10), va='center', ha='left',
        zorder=5, linespacing=1.35)

# Horizontal rule (original y=5.55; shifted down to y=4.95 for longer subtitle)
ax.plot([sx(0.32), sx(5.18)], [sy(4.95), sy(4.95)],
        color=DIVIDER, lw=1.5, zorder=5)

# Description paragraph
desc_lines = [
    'Walk-forward cross-validated framework for American equity options:',
    '(L1) - A CRR no-arbitrage pricer',
    '(L2) - Independently cross-validated by an IV-free XGBoost classifier',
    '(L3) - Sized via regime-conditioned Kelly criterion',
]
for i, ln in enumerate(desc_lines):
    ax.text(sx(0.32), sy(4.62) - i * sy(0.30), ln,
            color=DESC_C, fontsize=fs(9.2), va='center', ha='left', zorder=5)

# Layer badges (exact original logic, scaled)
for i, (tag, lbl, clr) in enumerate(BADGES):
    bx = sx(0.38 + i * 1.68)
    ax.add_patch(FancyBboxPatch((bx, sy(0.72)), sx(1.55), sy(0.82),
                                 boxstyle='round,pad=0.05',
                                 facecolor=clr, edgecolor='none', zorder=5))
    ax.text(bx + sx(0.775), sy(1.13), f'({tag})  {lbl}',
            color='white', fontsize=fs(7.8), fontweight='bold',
            va='center', ha='center', zorder=6)

# Author line (exact original position, scaled)
ax.text(sx(0.32), sy(0.28),
        'DeWayne Dantzler  ·  CS495 Capstone Project 6  ·  May 2026',
        color=AUTHOR_C, fontsize=fs(8), va='center', ha='left', zorder=5)

# ── CRR Binomial Tree  (N=4) — exact _crr_tree_art, scaled ───────────────────
N  = 4
ys = 0.85 * SY
xs = 1.00 * SX
x0 = 6.30 * SX
y0 = 4.80 * SY

nodes = {(k, j): (x0 + k * xs, y0 + (k / 2 - j) * ys)
         for k in range(N + 1) for j in range(k + 1)}

# Edges
for k in range(N):
    for j in range(k + 1):
        x1, y1 = nodes[(k, j)]
        for nj in [j, j + 1]:
            x2, y2 = nodes[(k + 1, nj)]
            ax.plot([x1, x2], [y1, y2], color=EDGE_C,
                    lw=1.3, alpha=0.75, zorder=1)

# Nodes — Unicode labels matching original exactly
lbls = {
    (0,0):'S₀',
    (1,0):'Su',    (1,1):'Sd',
    (2,0):'Su²',   (2,1):'Sud',   (2,2):'Sd²',
    (3,0):'Su³',   (3,1):'Su²d',  (3,2):'Sud²',  (3,3):'Sd³',
    (4,0):'Su⁴',   (4,1):'Su³d',  (4,2):'Su²d²', (4,3):'Sud³', (4,4):'Sd⁴',
}
node_r = 0.28 * SY   # scale radius by height factor

for (k, j), (nx, ny) in nodes.items():
    fc = TERM_CLRS[j] if k == N else NODE_FILL
    ec = fc            if k == N else NODE_EDGE
    tc = 'white'       if k == N else NODE_TXT
    ax.add_patch(Circle((nx, ny), node_r,
                        facecolor=fc, edgecolor=ec, lw=1.5, zorder=3))
    if lbl := lbls.get((k, j)):
        ax.text(nx, ny, lbl, ha='center', va='center',
                fontsize=fs(8.0), fontweight='bold', color=tc, zorder=4)

# Legend (exact original placement, bbox_to_anchor unchanged)
leg = [mpatches.Patch(facecolor='#1A5E20', label='ITM (call)'),
       mpatches.Patch(facecolor='#F57F17', label='Near ATM'),
       mpatches.Patch(facecolor='#880E4F', label='OTM (call)'),
       mpatches.Patch(facecolor=NODE_FILL, edgecolor=NODE_EDGE,
                      lw=1.2, label='Intermediate')]
ax.legend(handles=leg, loc='lower right',
          bbox_to_anchor=(0.985, 0.07), fontsize=fs(7.8),
          framealpha=0.92, edgecolor='#B0BEC5')

# Tree caption (scaled from original ax.text(8.25, 7.92, ...))
ax.text(sx(8.25), sy(7.92), 'CRR Binomial Tree  (N = 4)',
        ha='center', va='center', fontsize=fs(9), color=MUTED, style='italic')

# ── Page footer (exact original logic, scaled) ────────────────────────────────
ax.axhline(sy(0.43), color=FOOT_LINE, lw=0.6, xmin=0.03, xmax=0.97)

# ── Output ────────────────────────────────────────────────────────────────────
fig.savefig('cover_slide.png', dpi=200, facecolor='white', edgecolor='none')
plt.close(fig)
print("Generated cover_slide.png")
