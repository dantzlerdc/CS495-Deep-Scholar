#!/usr/bin/env python3
"""
make_pipeline_flowchart.py  v3

Template-matched flowchart based on Example-Workflow-Diagram.pdf:
  • Central horizontal spine (bold blue/colored bar)
  • Elliptical loop overlays on the overview page
  • Icon nodes on the spine at each component/stage
  • Vertical badge labels (rotated text, colored)
  • White rounded description panels with bullet points
  • Dashed connector lines from spine node to panel

Pages
─────
  1  Cover  — dark left panel + CRR binomial tree artwork
  2  Overview  — 3-stage template layout (L1 → L2 → L3)
  3  Layer 1 Detail  — 8-component spine, alternating panels
  4  Layer 2 Detail  — 6-component spine, alternating panels
  5  Layer 3 + Build Commands

Output:  CRR-Pipeline-Build-Flowchart.pdf
Build:   .venv/bin/python make_pipeline_flowchart.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, Circle, FancyArrow
import matplotlib.patches as mpatches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import textwrap, os

OUT    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'CRR-Pipeline-Build-Flowchart.pdf')
ICONS  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'assets', 'icons')
GITHUB = 'github.com/dantzlerdc/CS495-Deep-Scholar'
FW, FH = 11.0, 8.5
PAGES  = 6

# ── Layer colour palette ──────────────────────────────────────────
# (spine/node fill, dark border, badge/header, loop outline)
LC = {
    'l1':  ('#3A6FD8', '#0B2C6E', '#163A8C', '#7FA8E8'),
    'l2':  ('#3D9E55', '#0A3D18', '#145A22', '#80C490'),
    'l3':  ('#D05030', '#7A1E00', '#A83000', '#E89070'),
    'mk':  ('#5A7888', '#1A2830', '#263840', '#98B4C0'),
    'cfg': ('#7B50C8', '#35086A', '#4E18A0', '#B090E0'),
    'out': ('#C04070', '#5E0028', '#880040', '#E090B0'),
    'orc': ('#D07028', '#6A2000', '#923000', '#F0A860'),
}
HDR_BG  = '#0B2C6E'
BG_C    = '#FFFFFF'
BODY_C  = '#1A1A2E'
MUTED   = '#546E7A'
LOOP_C  = '#B0BEC5'
SPINE_C = '#1A3A7A'


# ─────────────────────────────────────────────────────────────────
#  PRIMITIVES
# ─────────────────────────────────────────────────────────────────

def make_fig():
    fig = plt.figure(figsize=(FW, FH))
    fig.patch.set_facecolor(BG_C)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FW)
    ax.set_ylim(0, FH)
    ax.axis('off')
    return fig, ax


def page_header(ax, title, subtitle=''):
    ax.add_patch(plt.Rectangle((0, FH - 0.58), FW, 0.58,
                                facecolor=HDR_BG, zorder=10))
    ax.text(0.22, FH - 0.29, title, color='white', fontsize=11,
            fontweight='bold', va='center', ha='left', zorder=11)
    if subtitle:
        ax.text(FW / 2, FH - 0.92, subtitle, color=MUTED,
                fontsize=8.5, style='italic', va='center', ha='center')


def page_footer(ax, pn):
    ax.axhline(0.43, color='#B0BEC5', lw=0.6, xmin=0.03, xmax=0.97)
    ax.text(FW / 2, 0.24,
            f'Page {pn} of {PAGES}  ·  CS495 Capstone Project-6',
            ha='center', va='center', fontsize=7, color='#8898A8')


# ── Spine bar ────────────────────────────────────────────────────

def spine(ax, x0, x1, y, color=SPINE_C, h=0.28, zorder=4):
    # Rounded-cap spine using a wide FancyBboxPatch
    ax.add_patch(FancyBboxPatch(
        (x0, y - h / 2), x1 - x0, h,
        boxstyle='round,pad=0.06',
        facecolor=color, edgecolor='none', zorder=zorder
    ))


# ── Elliptical loop (template's figure-8 ovals) ──────────────────

def loop(ax, cx, cy, w, h, color=LOOP_C, lw=2.2, zorder=2):
    ax.add_patch(Ellipse((cx, cy), width=w, height=h,
                          facecolor='none', edgecolor=color,
                          linewidth=lw, zorder=zorder))


def loop_arrows(ax, cx, cy, w, h, color, zorder=3):
    """Directional teal arrows at the midpoints of each oval."""
    # Top midpoint → right
    ax.annotate('', xy=(cx + 0.20, cy + h / 2 - 0.04),
                xytext=(cx - 0.20, cy + h / 2 - 0.04),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8),
                zorder=zorder)
    # Bottom midpoint → left
    ax.annotate('', xy=(cx - 0.20, cy - h / 2 + 0.04),
                xytext=(cx + 0.20, cy - h / 2 + 0.04),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8),
                zorder=zorder)


# ── Stage node icon box (sits on the spine) ───────────────────────

def node_box(ax, cx, cy, size, layer, zorder=6):
    fc, bc, hc, _ = LC[layer]
    ax.add_patch(FancyBboxPatch(
        (cx - size / 2, cy - size / 2), size, size,
        boxstyle='round,pad=0.04',
        facecolor=hc, edgecolor=bc, linewidth=2.0, zorder=zorder
    ))


def _draw_tree_icon(ax, cx, cy, s, col):
    """Mini CRR-tree icon."""
    pts = [(cx - s, cy), (cx, cy + s * 0.7), (cx, cy - s * 0.7),
           (cx + s, cy + s), (cx + s, cy), (cx + s, cy - s)]
    for a, b in [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (2, 5)]:
        ax.plot([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]],
                color=col, lw=1.3, zorder=8)
    for px, py in pts[:3]:
        ax.add_patch(Circle((px, py), s * 0.18, facecolor=col,
                            edgecolor=col, zorder=9))


def _draw_ml_icon(ax, cx, cy, s, col):
    """Mini neural-net icon."""
    inp  = [(cx - s, cy + s * 0.5), (cx - s, cy - s * 0.5)]
    hid  = [(cx,     cy + s * 0.7), (cx,     cy),  (cx,     cy - s * 0.7)]
    out_ = [(cx + s, cy)]
    for n1 in inp:
        for n2 in hid:
            ax.plot([n1[0], n2[0]], [n1[1], n2[1]],
                    color=col, lw=0.9, alpha=0.7, zorder=8)
    for n1 in hid:
        for n2 in out_:
            ax.plot([n1[0], n2[0]], [n1[1], n2[1]],
                    color=col, lw=0.9, alpha=0.7, zorder=8)
    for layer in [inp, hid, out_]:
        for px, py in layer:
            ax.add_patch(Circle((px, py), s * 0.18, facecolor=col,
                                edgecolor=col, zorder=9))


def _draw_compare_icon(ax, cx, cy, s, col):
    """Mini comparison arrows icon."""
    ax.annotate('', xy=(cx + s * 0.7, cy + s * 0.35),
                xytext=(cx - s * 0.7, cy + s * 0.35),
                arrowprops=dict(arrowstyle='->', color=col, lw=1.4), zorder=8)
    ax.annotate('', xy=(cx - s * 0.7, cy - s * 0.35),
                xytext=(cx + s * 0.7, cy - s * 0.35),
                arrowprops=dict(arrowstyle='->', color=col, lw=1.4), zorder=8)


def _draw_build_icon(ax, cx, cy, s, col):
    """Mini play-button / terminal icon."""
    tri_x = [cx - s * 0.4, cx + s * 0.7, cx - s * 0.4]
    tri_y = [cy + s * 0.6, cy, cy - s * 0.6]
    ax.fill(tri_x, tri_y, color=col, zorder=8)


ICON_FN = {
    'l1': _draw_tree_icon,
    'l2': _draw_ml_icon,
    'l3': _draw_compare_icon,
    'mk': _draw_build_icon,
}

def node_with_icon(ax, cx, cy, size, layer):
    """Draw the node box and its icon."""
    node_box(ax, cx, cy, size, layer)
    icon_col = 'white'
    s = size * 0.28
    fn = ICON_FN.get(layer)
    if fn:
        fn(ax, cx, cy, s, icon_col)


# ── Vertical badge label (matching template's rotated labels) ─────

def vert_badge(ax, cx, badge_cy, text, layer, badge_w=0.36, badge_h=1.10):
    fc, bc, hc, _ = LC[layer]
    ax.add_patch(FancyBboxPatch(
        (cx - badge_w / 2, badge_cy - badge_h / 2),
        badge_w, badge_h,
        boxstyle='round,pad=0.03',
        facecolor=hc, edgecolor=bc, linewidth=1.8, zorder=7
    ))
    ax.text(cx, badge_cy, text, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color='white',
            rotation=90, zorder=8)


# ── White description panel with bullet points ────────────────────

def desc_panel(ax, xl, yb, w, h, title, bullets, layer):
    """White rounded panel: coloured title bar + bullet body.

    Title may contain '\n' to render on two lines; title bar grows
    automatically so the second line isn't clipped.
    """
    fc, bc, hc, _ = LC[layer]
    two_line = '\n' in title
    title_h = 0.54 if two_line else 0.34
    # Outer card
    ax.add_patch(FancyBboxPatch(
        (xl, yb), w, h,
        boxstyle='round,pad=0.05',
        facecolor='white', edgecolor='#B0C0D0',
        linewidth=1.6, zorder=6
    ))
    # Title bar fill (inset rect so card's rounded corners show)
    ax.add_patch(plt.Rectangle(
        (xl + 0.048, yb + h - title_h + 0.01),
        w - 0.096, title_h - 0.01,
        facecolor=hc, zorder=7
    ))
    ax.plot([xl, xl + w], [yb + h - title_h, yb + h - title_h],
            color=bc, lw=1.5, zorder=7)
    ax.text(xl + w / 2, yb + h - title_h / 2, title,
            ha='center', va='center', fontsize=8, fontweight='bold',
            color='white', zorder=8, linespacing=1.1)

    # Bullets
    body_top  = yb + h - title_h - 0.10
    line_step = (body_top - yb - 0.08) / max(len(bullets), 1)
    line_step = min(line_step, 0.32)
    for i, b in enumerate(bullets[:6]):
        by = body_top - i * line_step
        wrapped = textwrap.shorten(b, width=int(w * 10.5), placeholder='…')
        ax.text(xl + 0.14, by, '•  ' + wrapped,
                ha='left', va='top', fontsize=7.8, color=BODY_C,
                zorder=7, linespacing=1.3)


# ── Dashed connector: node → panel ───────────────────────────────

def connector(ax, x1, y1, x2, y2, color=MUTED):
    ax.plot([x1, x2], [y1, y2], color=color, lw=1.1,
            linestyle='--', dashes=(4, 3), zorder=3, alpha=0.7)


# ─────────────────────────────────────────────────────────────────
#  PAGE 1 — COVER
# ─────────────────────────────────────────────────────────────────

def _crr_tree_art(ax):
    N, ys, xs, x0, y0 = 4, 0.60, 0.76, 6.55, 4.25
    nodes = {(k, j): (x0 + k * xs, y0 + (k / 2 - j) * ys)
             for k in range(N + 1) for j in range(k + 1)}
    for k in range(N):
        for j in range(k + 1):
            x1, y1 = nodes[(k, j)]
            for nj in [j, j + 1]:
                x2, y2 = nodes[(k + 1, nj)]
                ax.plot([x1, x2], [y1, y2], color='#607D8B', lw=1.3,
                        alpha=0.75, zorder=1)
    term_clrs = ['#1A5E20', '#2E7D32', '#F57F17', '#C62828', '#880E4F']
    lbls = {(0,0):'S₀',(1,0):'Su',(1,1):'Sd',(2,0):'Su²',(2,1):'Sud',
            (2,2):'Sd²',(3,0):'Su³',(3,1):'Su²d',(3,2):'Sud²',(3,3):'Sd³',
            (4,0):'Su⁴',(4,1):'Su³d',(4,2):'Su²d²',(4,3):'Sud³',(4,4):'Sd⁴'}
    for (k, j), (nx, ny) in nodes.items():
        fc = term_clrs[j] if k == N else '#E8EDF8'
        ec = fc if k == N else '#3F5080'
        tc = 'white' if k == N else '#1A1A2E'
        ax.add_patch(Circle((nx, ny), 0.21, facecolor=fc, edgecolor=ec,
                            lw=1.5, zorder=3))
        if lbl := lbls.get((k, j)):
            ax.text(nx, ny, lbl, ha='center', va='center',
                    fontsize=6.5, fontweight='bold', color=tc, zorder=4)
    leg = [mpatches.Patch(facecolor='#1A5E20', label='ITM (call)'),
           mpatches.Patch(facecolor='#F57F17', label='Near ATM'),
           mpatches.Patch(facecolor='#880E4F', label='OTM (call)'),
           mpatches.Patch(facecolor='#E8EDF8', edgecolor='#3F5080',
                          lw=1.2, label='Intermediate')]
    ax.legend(handles=leg, loc='lower right',
              bbox_to_anchor=(0.985, 0.07), fontsize=7.8,
              framealpha=0.92, edgecolor='#B0BEC5')
    ax.text(8.25, 7.92, 'CRR Binomial Tree  (N = 4)',
            ha='center', va='center', fontsize=9, color=MUTED, style='italic')


def page_cover(pdf):
    fig, ax = make_fig()
    PANEL_W   = 5.85
    PANEL_BOT = 0.55      # lift panel above footer strip
    ax.add_patch(plt.Rectangle((0, PANEL_BOT), PANEL_W, FH - PANEL_BOT,
                                facecolor='#0B2041', zorder=0))
    ax.add_patch(plt.Rectangle((PANEL_W - 0.02, PANEL_BOT), 0.07,
                                FH - PANEL_BOT,
                                facecolor='#3A7BD5', zorder=1))

    ax.text(0.32, 7.58, 'CS495 Deep Scholar', color='#88B8E8',
            fontsize=11, fontweight='bold', va='center', ha='left', zorder=5)
    ax.text(0.32, 6.95, 'CRR Binomial Option\nPricing Pipeline',
            color='white', fontsize=21, fontweight='bold',
            va='center', ha='left', zorder=5, linespacing=1.3)
    ax.text(0.32, 5.90, 'Full Build Pipeline Flowchart',
            color='#88B8E8', fontsize=12, va='center', ha='left', zorder=5)
    ax.plot([0.32, PANEL_W - 0.40], [5.55, 5.55],
            color='#3A7BD5', lw=1.5, zorder=5)

    ax.text(0.32, 5.22,
            'A six-page walkthrough of every component across '
            'the three pipeline layers:',
            color='#C8DCF0', fontsize=9.2, va='center', ha='left', zorder=5)
    bullets = [
        '(L1)  CRR Pricing Engine',
        '(L2)  Prediction Market ML Extensions',
        '(L3)  Cross-Model Comparison',
    ]
    for i, b in enumerate(bullets):
        ax.text(0.48, 4.65 - i * 0.40,
                f'•  {b}', color='#C8DCF0',
                fontsize=9.2, va='center', ha='left', zorder=5)

    # Three colored boxes, widened with centered (tag + label) blocks
    box_w   = 1.72
    gap     = 0.10
    total_w = 3 * box_w + 2 * gap
    bx0     = (PANEL_W - total_w) / 2
    for i, (tag, lbl, clr) in enumerate([
        ('L1', 'CRR Pricing Engine',      '#163A8C'),
        ('L2', 'ML Extensions',           '#145A22'),
        ('L3', 'Cross-Model Comparison',  '#7A1E00'),
    ]):
        bx = bx0 + i * (box_w + gap)
        ax.add_patch(FancyBboxPatch((bx, 1.55), box_w, 0.82,
                                     boxstyle='round,pad=0.05',
                                     facecolor=clr, edgecolor='none', zorder=5))
        cx = bx + box_w / 2
        ax.text(cx, 1.96,
                f'$\\bf{{{tag}}}$   {lbl}',
                color='white', fontsize=8.4,
                va='center', ha='center', zorder=6)

    # Byline lifted into blue panel, above PANEL_BOT
    ax.text(0.32, 0.92,
            'DeWayne Dantzler  ·  CS495 Capstone Project-6  ·  May 2026',
            color='#88B8E8', fontsize=8, va='center', ha='left', zorder=5)

    # Grid backdrop on right panel — shifted right to clear tree migration
    for gy in np.arange(1.0, 8.0, 0.62):
        ax.plot([PANEL_W + 0.10, FW], [gy, gy],
                color='#E8ECF2', lw=0.4, zorder=0)
    for gx in np.arange(PANEL_W + 0.45, FW, 0.62):
        ax.plot([gx, gx], [0, FH], color='#E8ECF2', lw=0.4, zorder=0)

    _crr_tree_art(ax)
    page_footer(ax, 1)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────
#  PAGE 2 — OVERVIEW (template-matched layout)
# ─────────────────────────────────────────────────────────────────

def page_overview(pdf):
    fig, ax = make_fig()
    page_header(ax, 'Full Pipeline Architecture — Overview',
                'L1 and L2 run independently; L3 merges both edge signals on the same AAPL sample')

    # ── Title block (left column) ──────────────────────────────
    ax.text(0.28, 6.90, 'Build Pipeline',
            color=HDR_BG, fontsize=15, fontweight='bold',
            va='center', ha='left')
    ax.text(0.28, 6.38,
            'Three independent layers\nconnected by shared\nedge signals.',
            color=BODY_C, fontsize=9, va='center', ha='left', linespacing=1.5)
    ax.plot([0.28, 2.40], [5.90, 5.90], color='#B0C0D0', lw=1.0)

    # Layer chips — text stacked over two lines to keep boxes inside divider
    chip_w, chip_h = 2.15, 0.62
    for i, (tag, lbl, layer) in enumerate([
        ('LAYER 1', 'CRR Pricing Engine',     'l1'),
        ('LAYER 2', 'ML Extensions',          'l2'),
        ('LAYER 3', 'Cross-Model Comparison', 'l3'),
    ]):
        cy = 5.52 - i * 0.78
        fc, bc, hc, _ = LC[layer]
        ax.add_patch(FancyBboxPatch((0.28, cy - chip_h / 2),
                                     chip_w, chip_h,
                                     boxstyle='round,pad=0.04',
                                     facecolor=hc, edgecolor=bc,
                                     lw=1.5, zorder=3))
        ax.text(0.28 + chip_w / 2, cy + 0.13, tag,
                color='white', fontsize=8.0, fontweight='bold',
                va='center', ha='center', zorder=4)
        ax.text(0.28 + chip_w / 2, cy - 0.13, lbl,
                color='white', fontsize=7.3,
                va='center', ha='center', zorder=4)

    ax.text(0.28, 3.35, 'make run-all',
            color=HDR_BG, fontsize=9.5, fontweight='bold',
            va='center', ha='left')
    ax.text(0.28, 2.95,
            'Chains all three layers\nin sequence automatically.',
            color=MUTED, fontsize=8, va='center', ha='left', linespacing=1.4)

    # Vertical divider
    ax.plot([2.55, 2.55], [0.55, 7.80], color='#D0D8E0', lw=1.0)

    # ── Spine ──────────────────────────────────────────────────
    SPY = 4.00
    spine(ax, 2.72, 10.65, SPY, color=SPINE_C, h=0.30, zorder=4)

    # ── Stage positions ───────────────────────────────────────
    stages = [
        (4.10, 'l1', 'CRR\nPricing\nEngine',
         ['CRR binomial tree (N=100)',
          'V_model vs V_market',
          'Kelly trade sizing',
          'Monte Carlo simulation',
          'Build: make run']),
        (6.85, 'l2', 'ML\nExtensions',
         ['XGBoost p-estimator',
          'Crowd bias / regime detection',
          'Microstructure cost model',
          'Walk-forward backtest',
          'Build: make run-layer2']),
        (9.55, 'l3', 'Cross-Model\nComparison',
         ['Common 3,000-contract sample',
          'edge_L1 vs edge_L2 scatter',
          '4-panel comparison figure',
          'Animated CRR HTML (html)',
          'Build: make run-comparison']),
    ]

    # Two elliptical loops
    loop_params = [
        ((stages[0][0] + stages[1][0]) / 2, SPY,
         stages[1][0] - stages[0][0] + 0.85, 3.80),
        ((stages[1][0] + stages[2][0]) / 2, SPY,
         stages[2][0] - stages[1][0] + 0.85, 3.80),
    ]
    for i, (cx, cy, w, h) in enumerate(loop_params):
        loop(ax, cx, cy, w, h, color=LOOP_C, lw=2.2)
        fc, bc, hc, lc = LC[stages[i][1]]
        loop_arrows(ax, cx, cy, w, h, color=hc)

    # Stage nodes, badges, panels (alternating above/below)
    node_size  = 0.68
    badge_w    = 0.36
    badge_h    = 1.00
    badge_gap  = 0.10     # gap between node and badge
    badge_pg   = 0.12     # gap between badge and panel
    panel_w    = 2.30
    panel_h    = 1.75

    for i, (cx, layer, badge_txt, bullets) in enumerate(stages):
        above = (i % 2 == 0)
        fc, bc, hc, lc = LC[layer]

        # Node
        node_with_icon(ax, cx, SPY, node_size, layer)

        # Badge position
        if above:
            badge_cy = SPY + node_size / 2 + badge_gap + badge_h / 2
            panel_yb = badge_cy + badge_h / 2 + badge_pg
        else:
            badge_cy = SPY - node_size / 2 - badge_gap - badge_h / 2
            panel_yb = badge_cy - badge_h / 2 - badge_pg - panel_h

        vert_badge(ax, cx, badge_cy, badge_txt, layer, badge_w, badge_h)

        # Panel
        panel_xl = cx - panel_w / 2
        desc_panel(ax, panel_xl, panel_yb, panel_w, panel_h,
                   f'Layer {i+1}', bullets, layer)

        # Connector: badge top/bottom → panel
        if above:
            connector(ax, cx, badge_cy + badge_h / 2,
                      cx, panel_yb, color=hc)
        else:
            connector(ax, cx, badge_cy - badge_h / 2,
                      cx, panel_yb + panel_h, color=hc)

    # Cross-layer arrows beneath stage 2 (L2)
    # From L1 node down, then from L2 node down to L3
    ax.annotate('', xy=(stages[2][0], SPY),
                xytext=(stages[1][0] + 0.45, SPY),
                arrowprops=dict(arrowstyle='->', color=SPINE_C, lw=2.0), zorder=5)
    ax.annotate('', xy=(stages[1][0], SPY),
                xytext=(stages[0][0] + 0.45, SPY),
                arrowprops=dict(arrowstyle='->', color=SPINE_C, lw=2.0), zorder=5)

    page_footer(ax, 2)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────
#  TEMPLATE-STYLE DETAIL PAGE (reusable)
# ─────────────────────────────────────────────────────────────────

def detail_page(pdf, page_num, hdr_title, hdr_subtitle,
                layer, spine_color, components):
    """
    Generic template-style detail page.

    components: list of
        (short_name, full_name, [bullet strings])
    Panels alternate above (even index) and below (odd index).
    """
    fig, ax = make_fig()
    page_header(ax, hdr_title, hdr_subtitle)

    n   = len(components)
    SPY = 4.00

    # Spine width — inset so end-panels fit within the page margins
    x0 = 0.85
    x1 = FW - 0.85
    spine(ax, x0, x1, SPY, color=spine_color, h=0.28)

    # Node x-positions (evenly spaced)
    node_xs = [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]

    # Flow arrows along spine (between nodes)
    fc_, bc_, hc_, _ = LC[layer]
    for i in range(n - 1):
        mid_x = (node_xs[i] + node_xs[i + 1]) / 2
        ax.annotate('', xy=(node_xs[i + 1] - 0.28, SPY),
                    xytext=(node_xs[i] + 0.28, SPY),
                    arrowprops=dict(arrowstyle='->', color='white',
                                   lw=1.6), zorder=5)

    # Node size and panel dimensions
    node_sz   = 0.56
    badge_w   = 0.32
    badge_h   = 0.85
    badge_gap = 0.08
    badge_pg  = 0.10
    panel_w   = (x1 - x0) / (n - 1) - 0.08
    panel_w   = max(panel_w, 1.30)
    panel_w   = min(panel_w, 2.10)
    panel_h   = 1.75

    # Above panel ceiling and below panel floor
    above_top = FH - 0.65
    below_bot = 0.55

    for i, (short, full, bullets) in enumerate(components):
        cx    = node_xs[i]
        above = (i % 2 == 0)

        # ── Node box with step number ──
        node_box(ax, cx, SPY, node_sz, layer)
        r = node_sz * 0.30
        ax.add_patch(Circle((cx, SPY), r, facecolor='white',
                            edgecolor='white', zorder=8))
        ax.text(cx, SPY, str(i + 1), ha='center', va='center',
                fontsize=8, fontweight='bold', color=hc_, zorder=9)

        # ── Vertical badge ──
        if above:
            badge_cy  = SPY + node_sz / 2 + badge_gap + badge_h / 2
            panel_yb  = badge_cy + badge_h / 2 + badge_pg
            panel_yt  = panel_yb + panel_h
            # clamp if it would exceed header
            if panel_yt > above_top - 0.05:
                panel_yb = above_top - 0.05 - panel_h
                badge_cy = panel_yb - badge_pg - badge_h / 2
        else:
            badge_cy  = SPY - node_sz / 2 - badge_gap - badge_h / 2
            panel_yt  = badge_cy - badge_h / 2 - badge_pg
            panel_yb  = panel_yt - panel_h
            if panel_yb < below_bot + 0.05:
                panel_yb  = below_bot + 0.05
                badge_cy  = panel_yb + panel_h + badge_pg + badge_h / 2

        # badge
        vert_badge(ax, cx, badge_cy, short, layer, badge_w, badge_h)

        # connector
        if above:
            connector(ax, cx, badge_cy + badge_h / 2,
                      cx, panel_yb, color=hc_)
        else:
            connector(ax, cx, badge_cy - badge_h / 2,
                      cx, panel_yb + panel_h, color=hc_)

        # panel
        xl = cx - panel_w / 2
        desc_panel(ax, xl, panel_yb, panel_w, panel_h, full, bullets, layer)

    page_footer(ax, page_num)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────
#  LAYER 1 COMPONENTS
# ─────────────────────────────────────────────────────────────────

L1_COMPS = [
    ('config', 'config.yaml',
     ['Central parameter store',
      'AMD ticker, strikes, premiums',
      'IV, risk-free rate, time T',
      'No hard-coded values',
      'Single reproducible source']),

    ('data.py', 'data.py  Stage 1',
     ['Fetch AMD prices via yfinance',
      'Compute rv30 and rv60',
      'RV30 = independent sigma',
      'NOT back-solved from price',
      'Basis of the edge signal']),

    ('tree.py', 'tree.py  Stage 2',
     ['CRR American binomial tree',
      'N=100, vectorised NumPy',
      'Forward pass: S(i,j)=S·uⁱ⁻ʲ·dʲ',
      'Backward induction at every node',
      'Produces V_model (4 contracts)']),

    ('greeks', 'greeks.py  Stage 3',
     ['Δ, Γ, θ, Vega, Rho',
      'Central finite differences',
      'Consistent with binomial model',
      'Not Black-Scholes closed form',
      'Saved to greeks.csv']),

    ('edge', 'edge.py  Stage 4',
     ['Positive → BUY signal',
      'Negative → SELL signal',
      '±2% dead-band filter',
      'Saved to edges.csv']),

    ('kelly', 'kelly.py  Stage 5a',
     ['f* = (p·b − q) / b',
      'Full, half, quarter Kelly',
      'Translates edge → $ size',
      'Fractional = ruin protection',
      'Saved to kelly.csv']),

    ('sim.py', 'simulation.py\nStage 5b',
     ['1,000 trades, seed=42',
      'Sharpe ratio + max drawdown',
      'Hit rate per Kelly variant',
      '15% circuit breaker',
      'Saved to simulation.csv']),

    ('main', 'main.py\nOrchestrator',
     ['Single pipeline entry point',
      'Reads & validates config.yaml',
      'Stages 1–5b in order',
      'Writes all outputs',
      'Equiv: make run']),
]


# ─────────────────────────────────────────────────────────────────
#  LAYER 2 COMPONENTS
# ─────────────────────────────────────────────────────────────────

L2_COMPS = [
    ('mkt_data', 'market_data.py',
     ['AAPL 2016-2020 Kaggle dataset',
      'Proxy for AMD (chains unavailable)',
      'Moneyness (S/K), DTE, RV-IV spread',
      'Volume / OI ratio, bid-ask width',
      'Single prepared DataFrame output']),

    ('p_est', 'p_estimator.py',
     ['XGBoost: predicts P(ITM)',
      'Uses only historical features',
      'Never uses market price as input',
      'Platt scaling calibration',
      'Brier score baseline = 0.25']),

    ('bias', 'bias_detector.py',
     ['Normal regime: RV-IV spread < 5%',
      'Herding regime: spread > 10%',
      'IV momentum (3-day, 5-day)',
      'Volume spike indicator',
      'Regime label → policy module']),

    ('cost', 'micro_cost.py',
     ['Bid-ask spread (half on entry+exit)',
      'Fidelity fee: $0.65/contract',
      'Volume-scaled slippage model',
      'edge_net = edge − costs/V_mkt',
      'Prevents overtrading thin edges']),

    ('policy', 'policy.py',
     ['Normal: |edge_net| > 2%',
      'Herding: |edge_net| > 8%',
      'VaR constraint: ≤ 5% of capital',
      '15% drawdown circuit breaker',
      'Regime-conditional entry/exit']),

    ('backtest', 'backtest.py',
     ['Walk-forward historical backtest',
      'Hit rate, Sharpe, max drawdown',
      'Brier score across all trades',
      'Regime state recorded per trade',
      'Equiv: make run-layer2']),
]


# ─────────────────────────────────────────────────────────────────
#  PAGE 5 — LAYER 3: CROSS-MODEL COMPARISON
# ─────────────────────────────────────────────────────────────────

def page_layer3(pdf):
    fig, ax = make_fig()
    page_header(ax, 'Layer 3 — Cross-Model Comparison',
                'make run-comparison  ·  Outputs: l1_vs_l2_comparison.png  +  aapl_crr_comparison.html')

    # ── Scientific question ────────────────────────────────────
    qbox_yb, qbox_h = 6.10, 1.35
    qbox_xl = 0.80
    qbox_w  = FW - 2 * qbox_xl
    ax.add_patch(FancyBboxPatch((qbox_xl, qbox_yb), qbox_w, qbox_h,
                                 boxstyle='round,pad=0.05',
                                 facecolor='#FFF8E1', edgecolor='#F9A825',
                                 lw=1.8, zorder=3))
    ax.text(FW / 2, qbox_yb + qbox_h - 0.28,
            'Core Scientific Question', ha='center',
            va='center', fontsize=10, fontweight='bold',
            color='#BF360C', zorder=4)
    qbody = textwrap.fill(
        'Do CRR (mathematical, no-arbitrage) and XGBoost (empirical, ML) '
        'independently agree on which AAPL options the crowd misprices? '
        'Agreement validates both models simultaneously; disagreement '
        'zones are findings in their own right.',
        width=110)
    ax.text(FW / 2, qbox_yb + 0.45, qbody,
            ha='center', va='center', fontsize=8.5,
            color=BODY_C, zorder=4, linespacing=1.4)

    # ── L3 spine + 2 nodes ────────────────────────────────────
    SPY3 = 4.75
    spine(ax, 1.0, FW - 0.5, SPY3, color=LC['l3'][2], h=0.26, zorder=4)

    l3_nodes = [
        (3.30,  'layer1_vs_layer2.py',
         ['Draws 3,000 common AAPL contracts',
          'Applies L1 (sigma=RV30) + L2 (XGBoost)',
          'Joins regime labels from bias_detector',
          '4-panel comparison figure',
          'Saved: l1_vs_l2_comparison.png']),
        (8.20,  'make_aapl_crr_animation.py',
         ['Contract A: herding, both say SELL',
          '  edge_L1 < −15%, edge_L2 < −3%',
          'Contract B: normal, both say fair',
          'Animates CRR tree (~28 frames)',
          'Output: aapl_crr_comparison.html']),
    ]

    # Input arrows from L1 and L2 into first node
    fc3, bc3, hc3, _ = LC['l3']
    ax.annotate('', xy=(l3_nodes[0][0] - 0.33, SPY3),
                xytext=(1.20, SPY3),
                arrowprops=dict(arrowstyle='->', color=LC['l1'][2], lw=1.6), zorder=5)
    ax.text(2.00, SPY3 + 0.35, 'edge_L1\n(RV30)',
            ha='center', fontsize=8.5, fontweight='bold',
            color=LC['l1'][2], style='italic', linespacing=1.2)
    ax.annotate('', xy=(l3_nodes[0][0] - 0.33, SPY3 - 0.22),
                xytext=(1.20, SPY3 - 0.22),
                arrowprops=dict(arrowstyle='->', color=LC['l2'][2], lw=1.6), zorder=5)
    ax.text(2.00, SPY3 - 0.50, 'edge_L2\n(ML)',
            ha='center', fontsize=8.5, fontweight='bold',
            color=LC['l2'][2], style='italic', linespacing=1.2)

    for i, (cx, full, bullets) in enumerate(l3_nodes):
        node_box(ax, cx, SPY3, 0.58, 'l3')
        ax.add_patch(Circle((cx, SPY3), 0.17, facecolor='white',
                            edgecolor='white', zorder=8))
        ax.text(cx, SPY3, str(i + 1), ha='center', va='center',
                fontsize=8, fontweight='bold', color=hc3, zorder=9)
        vert_badge(ax, cx, SPY3 - 0.30 - 0.50, str(i + 1), 'l3',
                   badge_w=0.32, badge_h=0.96)

        panel_yb = 1.10
        panel_w  = 4.10
        panel_h_l3 = 2.40
        xl = cx - panel_w / 2
        desc_panel(ax, xl, panel_yb, panel_w, panel_h_l3, full, bullets, 'l3')
        connector(ax, cx, SPY3 - 0.58, cx, panel_yb + panel_h_l3, color=hc3)

    # Arrow between L3 nodes
    ax.annotate('', xy=(l3_nodes[1][0] - 0.33, SPY3),
                xytext=(l3_nodes[0][0] + 0.33, SPY3),
                arrowprops=dict(arrowstyle='->', color='white', lw=1.6), zorder=5)

    page_footer(ax, 5)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────
#  PAGE 6 — BUILD COMMANDS
# ─────────────────────────────────────────────────────────────────

def _draw_tool_cell(ax, x_left, y_center, cell_w, item):
    """Render a single icon-left + name-right tool cell.

    item: ('img', basename, label) or ('chip', label, brand_color).
    The icon (or chip) is anchored near the cell's left edge; the
    label sits to its right, vertically centered on y_center.
    """
    icon_size  = 0.28
    icon_cx    = x_left + 0.14 + icon_size / 2
    label_x    = icon_cx + icon_size / 2 + 0.08
    kind = item[0]
    if kind == 'img':
        key, label = item[1], item[2]
        try:
            img = mpimg.imread(os.path.join(ICONS, f'{key}.png'))
        except FileNotFoundError:
            return
        h_px, w_px = img.shape[:2]
        zoom = min(icon_size * 100 / h_px, icon_size * 100 / w_px)
        ab = AnnotationBbox(OffsetImage(img, zoom=zoom),
                             (icon_cx, y_center),
                             frameon=False, zorder=8)
        ax.add_artist(ab)
        ax.text(label_x, y_center, label,
                ha='left', va='center', fontsize=7.2,
                color=BODY_C, zorder=9)
    elif kind == 'chip':
        label, color = item[1], item[2]
        chip_w = 0.32
        chip_h = 0.22
        ax.add_patch(FancyBboxPatch(
            (icon_cx - chip_w / 2, y_center - chip_h / 2),
            chip_w, chip_h,
            boxstyle='round,pad=0.02',
            facecolor=color, edgecolor='none', zorder=8))
        ax.text(icon_cx + chip_w / 2 + 0.10, y_center, label,
                ha='left', va='center', fontsize=7.2,
                color=BODY_C, zorder=9)


def tools_card(ax, xl, yb, w, h, title, bullets, tools, layer):
    """Full make-target card: title + bullets + 'TOOLS' divider + 2-col icon grid."""
    desc_panel(ax, xl, yb, w, h, title, bullets, layer)

    # Divider line + 'TOOLS' label sits just below the bullets region.
    divider_y = yb + 2.55
    ax.plot([xl + 0.22, xl + w - 0.22],
            [divider_y, divider_y],
            color=MUTED, lw=0.7, alpha=0.7, zorder=8)
    ax.text(xl + w / 2, divider_y + 0.18, 'TOOLS',
            ha='center', va='center',
            fontsize=7.2, fontweight='bold',
            color=MUTED, zorder=9)

    # 2-column tool grid below the divider.
    cell_w = (w - 0.30) / 2
    row_h  = 0.45
    n      = len(tools)
    for i, tool in enumerate(tools):
        row = i // 2
        col = i % 2
        n_in_row = min(2, n - row * 2)
        if n_in_row == 1:
            x_left = xl + (w - cell_w) / 2
        else:
            x_left = xl + 0.15 + col * cell_w
        y_center = divider_y - 0.35 - row * row_h
        _draw_tool_cell(ax, x_left, y_center, cell_w, tool)


def page_build_commands(pdf):
    fig, ax = make_fig()
    page_header(ax, 'Makefile Build Commands',
                'Run from project root  ·  Sequence: setup → run → run-layer2 → run-comparison')

    # ── 4 build command cards arranged 1 × 4 horizontally ──────
    mk_cmds = [
        ('make setup',          'mk',
         ['Create .venv',
          'Install Poetry',
          'Install dependencies',
          'Run once'],
         [('img', 'python', 'Python'),
          ('img', 'poetry', 'Poetry'),
          ('chip', 'pip', '#3776AB')]),
        ('make run',            'l1',
         ['main.py config.yaml',
          'All 6 Layer 1 stages',
          'Outputs → project/outputs/',
          'Layer 1 complete'],
         [('img', 'numpy', 'NumPy'),
          ('img', 'pandas', 'pandas'),
          ('img', 'matplotlib', 'Matplotlib'),
          ('chip', 'yfinance', '#5F01D1'),
          ('img', 'scipy', 'SciPy')]),
        ('make run-layer2',     'l2',
         ['Runs 6 Layer 2 modules',
          'Trains XGBoost models',
          'Outputs → project/outputs/',
          'Layer 2 complete'],
         [('img', 'pandas', 'pandas'),
          ('img', 'numpy', 'NumPy'),
          ('img', 'matplotlib', 'Matplotlib'),
          ('img', 'xgboost', 'XGBoost'),
          ('img', 'scikitlearn', 'scikit-learn')]),
        ('make run-comparison', 'l3',
         ['Runs L3 comparison scripts',
          'Requires L1 + L2 first',
          'Outputs: PNG + HTML',
          'Layer 3 complete'],
         [('img', 'pandas', 'pandas'),
          ('img', 'matplotlib', 'Matplotlib'),
          ('chip', 'Pillow', '#11A9DD')]),
    ]
    MCW, MCH = 2.32, 5.10
    hgap   = 0.18
    total  = 4 * MCW + 3 * hgap
    x0m    = (FW - total) / 2
    box_yb = 1.55
    for i, (cmd, layer, bullets, icons) in enumerate(mk_cmds):
        xl = x0m + i * (MCW + hgap)
        tools_card(ax, xl, box_yb, MCW, MCH, cmd, bullets, icons, layer)

    page_footer(ax, 6)
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    with PdfPages(OUT) as pdf:
        meta = pdf.infodict()
        meta['Title']    = 'CS495 Deep Scholar — Build Pipeline Flowchart'
        meta['Author']   = 'DeWayne Dantzler'
        meta['Subject']  = 'CRR Binomial + Prediction Market Pipeline (PLAN2.md)'
        meta['Keywords'] = 'CRR, Kelly, XGBoost, options, pipeline, flowchart'

        page_cover(pdf)
        page_overview(pdf)

        detail_page(pdf, 3,
                    'Layer 1 — CRR Pricing Engine: Component Flow',
                    'Build: make run  ·  Entry: python main.py config.yaml  ·  Outputs: project/outputs/',
                    'l1', LC['l1'][2], L1_COMPS)

        detail_page(pdf, 4,
                    'Layer 2 — Prediction Market Extensions: Component Flow',
                    'Build: make run-layer2  ·  Data: AAPL 2016-2020 Kaggle  ·  Outputs: project/outputs/',
                    'l2', LC['l2'][2], L2_COMPS)

        page_layer3(pdf)
        page_build_commands(pdf)

    print(f'Written → {OUT}')


if __name__ == '__main__':
    main()
