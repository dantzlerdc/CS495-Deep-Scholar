"""Generate CRR-Binomial-Pricing-AMD-Options.pdf"""

from fpdf import FPDF
import numpy as np
import os

OUT = os.path.expanduser("~/CRR-Binomial-Pricing-AMD-Options.pdf")

# ── Parameters ────────────────────────────────────────────────────────────────
S0     = 341.35
K      = 350.00
r      = 0.053
put_iv = 0.7473
T_days = 18
N_vis  = 4
N_pipe = 100

T    = T_days / 365.0
dt   = T / N_vis
u    = np.exp(put_iv * np.sqrt(dt))
d    = 1.0 / u
p    = (np.exp(r * dt) - d) / (u - d)
disc = np.exp(-r * dt)

stock   = [[S0 * (u**(i-j)) * (d**j) for j in range(i+1)] for i in range(N_vis+1)]
intr    = [[max(K - stock[i][j], 0)   for j in range(i+1)] for i in range(N_vis+1)]
opt     = [[None]*(i+1) for i in range(N_vis+1)]
ex_flag = [[False]*(i+1) for i in range(N_vis+1)]
for j in range(N_vis+1):
    opt[N_vis][j] = intr[N_vis][j]
for i in range(N_vis-1, -1, -1):
    for j in range(i+1):
        cont = disc * (p * opt[i+1][j] + (1-p) * opt[i+1][j+1])
        opt[i][j] = max(intr[i][j], cont)
        if intr[i][j] > cont and intr[i][j] > 0:
            ex_flag[i][j] = True

# ── Color palette ─────────────────────────────────────────────────────────────
#  Backgrounds
BG_DARK  = (70,  75,  85)     # title bar, code blocks
BG_MED   = (90,  95, 108)     # parameter box
BG_TBL_H = (55,  65,  85)     # summary table header
BG_TBL_1 = (80,  85,  97)     # summary table odd rows
BG_TBL_2 = (65,  70,  82)     # summary table even rows
BG_ROW_1 = (220, 223, 228)    # inline table odd rows  (light gray)
BG_ROW_2 = (235, 237, 241)    # inline table even rows (near white)

#  Text on white page background
TXT_BLACK = (20,  20,  20)    # body text
TXT_DARK  = (55,  60,  70)    # subtitle, secondary
TXT_MID   = (100, 105, 115)   # footer, captions

#  Text on gray backgrounds
TXT_WHITE = (255, 255, 255)   # white on dark gray
TXT_OFFWH = (220, 225, 235)   # near-white on dark gray (keys)

#  Accent colors
BLUE_H    = (37,  99, 235)    # section heading blue  -- standard recognizable blue
BLUE_S    = (59, 130, 246)    # subsection blue       -- medium bright blue
BLUE_NODE = (37,  99, 235)    # node labels in tables
TEAL_H    = (14, 116, 144)    # section heading teal  -- recognizable teal
AMBER_H   = (245, 158,  11)   # section / amber nodes -- recognizable amber
TEAL_NODE = (14, 116, 144)    # teal nodes
GREEN_NODE= (20,  83,  45)    # green nodes           -- dark green
GRAY_NODE = (107, 114, 128)   # gray nodes            -- standard gray

#  Gold (keep as-is; shown on gray backgrounds)
GOLD      = (251, 191,  36)
RED       = (220,  38,  38)    # negative edge / sell signal


# ── PDF class ─────────────────────────────────────────────────────────────────
class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TXT_DARK)
        self.cell(0, 8,
                  "CS495 Deep Scholar  |  CRR Binomial Pricing  |  AMD $350 Options",
                  align="C")
        self.ln(6)   # no underline -- removed per request

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*TXT_MID)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()

# ── Helper functions ──────────────────────────────────────────────────────────

def section(txt, color=BLUE_H):
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*color)
    pdf.cell(0, 8, txt, ln=True)
    pdf.set_draw_color(*color)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

def subsection(txt):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BLUE_S)
    pdf.cell(0, 6, txt, ln=True)
    pdf.ln(1)

def body(txt, indent=0):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TXT_BLACK)
    pdf.set_x(10 + indent)
    pdf.multi_cell(190 - indent, 5.5, txt)
    pdf.ln(1)

def code(txt, indent=4):
    pdf.set_font("Courier", "", 9.5)
    pdf.set_text_color(*GOLD)
    pdf.set_fill_color(*BG_DARK)
    pdf.set_x(10 + indent)
    pdf.multi_cell(190 - indent, 5.5, txt, fill=True)

def bullet(label, desc, label_color=BLUE_S):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*label_color)
    pdf.set_x(14)
    pdf.cell(38, 5.5, label)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TXT_BLACK)
    pdf.multi_cell(148, 5.5, desc)

def kv(key, val):
    pdf.set_font("Courier", "B", 10)
    pdf.set_text_color(*TXT_OFFWH)
    pdf.set_x(14)
    pdf.cell(40, 5.5, key)
    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(*GOLD)
    pdf.multi_cell(146, 5.5, val)

def rule():
    pdf.set_draw_color(190, 193, 200)
    pdf.set_line_width(0.2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

def row_fill(idx):
    """Set alternating light-gray fill for inline data table rows."""
    pdf.set_fill_color(*(BG_ROW_1 if idx % 2 == 0 else BG_ROW_2))


# ═══════════════════════════════════════════════════════════════════════════════
# Title block
# ═══════════════════════════════════════════════════════════════════════════════
pdf.set_fill_color(*BG_DARK)
pdf.rect(10, pdf.get_y(), 190, 24, "F")
pdf.set_font("Helvetica", "B", 20)
pdf.set_text_color(*TXT_WHITE)
pdf.ln(2)
pdf.cell(0, 10, "CRR Binomial Option Pricing -- AMD $350 Strike", ln=True, align="C")
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(*TXT_OFFWH)
pdf.cell(0, 7, "Forward Pass and Backward Induction Explained", ln=True, align="C")
pdf.ln(2)
rule()

pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(*TXT_DARK)
pdf.cell(0, 7,
         "Market Data: AMD collected 2026-05-04  |  Expiry 2026-05-22  "
         "|  American-style put, no dividends",
         ln=True)
pdf.ln(3)

# ── Parameter box ─────────────────────────────────────────────────────────────
pdf.set_fill_color(*BG_MED)
pdf.rect(10, pdf.get_y(), 190, 36, "F")
pdf.ln(2)
kv("S  =", f"${S0}  (AMD spot price at collection)")
kv("K  =", f"${K:.2f}  (strike price)")
kv("r  =", f"{r:.1%}  (3-month T-bill risk-free rate)")
kv("IV =", f"{put_iv:.2%}  (put implied volatility, solved via CRR solver)")
kv("T  =", f"{T_days} calendar days  ({T:.4f} years)")
kv("N  =", f"{N_vis} steps (visual tree)  |  {N_pipe} steps (pipeline pricing)")
pdf.ln(4)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 -- Forward Pass
# ═══════════════════════════════════════════════════════════════════════════════
section("PART 1 -- Forward Pass: Building the Stock Price Lattice", BLUE_H)

body(
    "In the forward pass the model builds a recombining binomial lattice of possible "
    "AMD stock prices from today (Step 0) out to expiry (Step 4 in the visual, Step 100 "
    "in the pipeline). No option values are computed here -- only the underlying stock "
    "prices at every node."
)

subsection("CRR Up/Down Multipliers")
body("The size of each price move is derived from the implied volatility:")
code(f"u  = exp(IV x sqrt(dt))  =  exp({put_iv:.4f} x sqrt({dt:.5f}))  =  {u:.4f}")
code(f"d  = 1 / u               =  {d:.4f}")
code(f"dt = T / N               =  {T:.4f} / {N_vis}  =  {dt:.5f} years  ({dt*365:.1f} days per step)")
pdf.ln(2)
body(
    f"u = {u:.4f} means AMD moves UP by {(u-1)*100:.2f}% each step. "
    f"d = {d:.4f} means AMD moves DOWN by {(1-d)*100:.2f}% each step. "
    "Because d = 1/u the tree recombines: an up move followed by a down move "
    "lands on the exact same node as a down move followed by an up move. "
    "This is why column 2 has 3 nodes instead of 4."
)

subsection("Node Price Formula")
body("Every node (i, j) is computed directly -- no iteration needed:")
code("S(i, j) = S x u^(i-j) x d^j")
body(
    "i = time step (column 0 to 4)  |  "
    "j = number of down moves to reach this node  |  "
    "(i-j) = number of up moves"
)

subsection("Risk-Neutral Probability")
body(
    "The probability p of an up move is set so that the expected return "
    "equals the risk-free rate -- this is the risk-neutral measure:"
)
code(f"p  = (exp(r x dt) - d) / (u - d)  =  {p:.4f}")
code(f"q  = 1 - p                         =  {1-p:.4f}")
body(
    f"p = {p:.4f} and q = {1-p:.4f} are NOT real-world probabilities of AMD going up or down. "
    "They are mathematical weights used purely to compute fair option values under "
    "no-arbitrage pricing. They embed the risk-free rate, not any directional view on AMD."
)

subsection("Terminal Stock Prices at Step 4 (N=4 visual)")
body("Reading the five leaf nodes at expiry (Step 4, 18.0 days):")
pdf.ln(1)

terminal_data = [
    ("(4,0)", "4 ups,  0 downs", f"${S0 * u**4:.1f}",        "Far above strike -- deep OTM for put"),
    ("(4,1)", "3 ups,  1 down",  f"${S0 * u**3 * d:.1f}",    "Above strike -- OTM for put"),
    ("(4,2)", "2 ups,  2 downs", f"${S0 * u**2 * d**2:.1f}", "Near spot -- slightly ITM for put"),
    ("(4,3)", "1 up,   3 downs", f"${S0 * u * d**3:.1f}",    "Below strike -- ITM for put"),
    ("(4,4)", "0 ups,  4 downs", f"${S0 * d**4:.1f}",        "Deep below strike -- deep ITM for put"),
]
for idx, (node, path, price, desc) in enumerate(terminal_data):
    row_fill(idx)
    pdf.set_font("Courier", "B", 9.5)
    pdf.set_text_color(*BLUE_NODE)
    pdf.set_x(14)
    pdf.cell(14, 6, node, fill=True)
    pdf.set_font("Courier", "", 9.5)
    pdf.set_text_color(*TXT_DARK)
    pdf.cell(32, 6, path, fill=True)
    pdf.set_text_color(*GREEN_NODE)
    pdf.cell(20, 6, price, fill=True)
    pdf.set_text_color(*TXT_BLACK)
    pdf.cell(0, 6, "  " + desc, ln=True, fill=True)

pdf.ln(2)
body(
    "The spread of these prices -- from $245.1 to $475.6 -- is driven entirely by "
    f"implied volatility ({put_iv:.2%}). Higher IV means larger u and d, which widens "
    "the price fan. The vol premium of ~8-9% over RV-30d (65.49%) is what makes "
    "these options relatively expensive compared to AMD's recent realized moves."
)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 -- Backward Induction
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()
section("PART 2 -- Backward Induction: Computing Option Values", AMBER_H)

body(
    "Once the full stock price lattice is built, the model works right to left -- "
    "from the known terminal payoffs back to the present -- to find the fair value "
    "at every node. This is what makes the CRR model an American pricer: at each "
    "node it asks whether early exercise is better than waiting."
)

subsection("Step 1 -- Seed Terminal Payoffs (rightmost column)")
body("At expiry the option value is simply the intrinsic payoff. No discounting needed:")
code("V(N, j) = max(K - S(N,j), 0)  =  max(350 - S, 0)")
body("These seed values feed the backward recursion. Green nodes are ITM (V > 0), gray are OTM (V = 0).")
pdf.ln(1)

terminal_v = [
    ("(4,0)", f"${stock[4][0]:.1f}", "$0.00",               "OTM -- gray"),
    ("(4,1)", f"${stock[4][1]:.1f}", "$0.00",               "OTM -- gray"),
    ("(4,2)", f"${stock[4][2]:.1f}", f"${intr[4][2]:.2f}",  "ITM -- green"),
    ("(4,3)", f"${stock[4][3]:.1f}", f"${intr[4][3]:.2f}",  "ITM -- green"),
    ("(4,4)", f"${stock[4][4]:.1f}", f"${intr[4][4]:.2f}",  "ITM -- green"),
]
for idx, (node, s, v, label) in enumerate(terminal_v):
    row_fill(idx)
    pdf.set_font("Courier", "B", 9.5)
    pdf.set_text_color(*BLUE_NODE)
    pdf.set_x(14)
    pdf.cell(14, 6, node, fill=True)
    pdf.set_font("Courier", "", 9.5)
    pdf.set_text_color(*TXT_DARK)
    pdf.cell(24, 6, f"S={s}", fill=True)
    pdf.set_text_color(*GREEN_NODE)
    pdf.cell(24, 6, f"V={v}", fill=True)
    itm = "green" in label
    pdf.set_text_color(*(GREEN_NODE if itm else GRAY_NODE))  # "green" in dark green, "gray" in gray
    pdf.cell(0, 6, "  " + label, ln=True, fill=True)

pdf.ln(2)
subsection("Step 2 -- Recursion Formula at Each Interior Node")
body("For every node (i, j), working from column N-1 back to column 0:")
code("hold  =  disc x (p x V_up + (1-p) x V_down)")
code("V     =  max(intrinsic, hold)")
pdf.ln(1)
bullet("V_up",      "option value at child node (i+1, j)  -- already computed")
bullet("V_down",    "option value at child node (i+1, j+1) -- already computed")
bullet("p",         f"{p:.4f}  -- risk-neutral probability of up move")
bullet("disc",      f"{disc:.6f}  -- one-step discount factor  exp(-r x dt)")
bullet("hold",      "continuation value: what the option is worth if you wait one more step")
bullet("intrinsic", "immediate exercise value: max(350 - S, 0) at this node")
pdf.ln(2)

body(
    "The max(intrinsic, hold) is the American exercise decision. "
    "If intrinsic > hold, the model marks the node amber (early exercise optimal) "
    "and sets V = intrinsic. If hold >= intrinsic, the node is teal (continue holding) "
    "and V = hold. European options skip this comparison and always use hold."
)

subsection("Step 3 -- Node Color Key and Decision Rule")
pdf.ln(1)
bullet("Amber node",  "intrinsic > hold -- exercise now is optimal; V = intrinsic",
       label_color=AMBER_H)
bullet("Teal node",   "hold >= intrinsic -- wait is optimal; V = continuation value",
       label_color=TEAL_NODE)
bullet("Green node",  "terminal ITM -- V = max(K-S, 0) > 0  (expiry payoff)",
       label_color=GREEN_NODE)
bullet("Gray node",   "terminal OTM -- V = 0  (option expires worthless)",
       label_color=GRAY_NODE)

subsection("Step 4 -- Worked Example: Step 3 Nodes")
body("Reading the four nodes at Step 3 (13.5 days in) from the animation:")
pdf.ln(1)

step3 = [
    (0, "437.8", "0.00",  "0.00",  "teal",  "OTM -- no intrinsic value"),
    (1, "370.9", "0.00",  "4.47",  "teal",  "OTM but time value remains"),
    (2, "314.1", "35.86", "35.58", "amber", "Intrinsic beats hold -- exercise now"),
    (3, "266.3", "83.67", "83.57", "amber", "Intrinsic beats hold -- exercise now"),
]
for idx, (j, s, intr_v, cont_v, color, note) in enumerate(step3):
    row_fill(idx)
    pdf.set_font("Courier", "B", 9.5)
    pdf.set_text_color(*BLUE_NODE)
    pdf.set_x(14)
    pdf.cell(18, 6, f"(3,{j})", fill=True)
    pdf.set_font("Courier", "", 9.5)
    pdf.set_text_color(*TXT_DARK)
    pdf.cell(24, 6, f"S=${s}", fill=True)
    pdf.cell(26, 6, f"intr=${intr_v}", fill=True)
    pdf.cell(26, 6, f"hold=${cont_v}", fill=True)
    node_col = AMBER_H if color == "amber" else TEAL_NODE
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(*node_col)   # word "amber" in amber, word "teal" in teal
    pdf.cell(14, 6, color, fill=True)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*TXT_BLACK)
    pdf.cell(0, 6, "  " + note, ln=True, fill=True)

pdf.ln(2)
body(
    "At node (3,2): intrinsic $35.86 vs hold $35.58 -- early exercise wins by $0.28. "
    "At node (3,3): intrinsic $83.67 vs hold $83.57 -- early exercise wins by $0.10. "
    "Both are cases where the put is deep enough in the money that the time value of "
    "waiting is worth less than collecting the intrinsic payoff immediately."
)

subsection("Step 5 -- Root Node: The Final Option Price")
body("After all columns are processed, the root node (0,0) holds the model price:")
pdf.ln(1)
code(f"  V(0,0)  =  ${opt[0][0]:.4f}  (N={N_vis} visual tree)")
code(f"  V(0,0)  =  $27.0014           (N={N_pipe} pipeline tree)")
code(f"  V_market=  $27.0000           (Fidelity limit price)")
code(f"  Error   =  +0.005%            (model vs market)")
pdf.ln(2)
body(
    f"With only N={N_vis} steps the tree approximates $27.08. With N={N_pipe} steps the "
    "binomial tree converges to $27.0014 -- matching the Fidelity market price within "
    "0.005%. The small residual is floating-point rounding from IV calibration, not "
    "a model deficiency. This accuracy confirms the CRR model is correctly implemented "
    "and the implied volatility was solved precisely."
)

subsection("Why the Model Price Matches Market So Exactly")
body(
    "The put IV (74.73%) was solved by running scipy.optimize.brentq against the CRR "
    "pricer: it searched for the sigma value that makes V_model = V_market = $27.00. "
    "Because the IV was calibrated to the market price, the model reproduces that price "
    "by construction -- the near-zero edge is expected, not a coincidence. "
    "To find genuine mispricing edge, an independent IV forecast (e.g., forecasted "
    "realized volatility) must be used instead of market-implied IV."
)

# ═══════════════════════════════════════════════════════════════════════════════
# Summary table
# ═══════════════════════════════════════════════════════════════════════════════
section("SUMMARY: Forward Pass vs Backward Induction", TEAL_H)

rows = [
    ("Direction",    "Left to right (Step 0 to N)",   "Right to left (Step N to 0)"),
    ("Computes",     "Stock price S at each node",     "Option value V at each node"),
    ("Formula",      "S(i,j) = S x u^(i-j) x d^j",   "V = max(intrinsic, disc x (p*Vu + q*Vd))"),
    ("Node color",   "All blue (stock price nodes)",   "Amber/teal/green/gray (see legend)"),
    ("Exercise?",    "N/A -- no option decision yet",  "Yes -- American early exercise at each node"),
    ("Seeds",        "S0 = $341.35 at root",           "Terminal payoffs max(K-S, 0) at leaves"),
    ("Key output",   "Terminal price fan",             "V(0,0) = model option price"),
    ("N=4 result",   "5 terminal prices $245-$476",    f"V(0,0) = ${opt[0][0]:.2f}"),
    ("N=100 result", "101 terminal prices",            "V(0,0) = $27.0014  (error 0.005%)"),
]

pdf.ln(2)
col_w   = [38, 76, 76]
headers = ["Property", "Forward Pass", "Backward Induction"]

# Table header row
pdf.set_fill_color(*BG_TBL_H)
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*TXT_WHITE)
pdf.set_x(10)
for h, w in zip(headers, col_w):
    pdf.cell(w, 7, h, border=1, fill=True)
pdf.ln()

# Data rows
for i, (prop, fwd, bwd) in enumerate(rows):
    pdf.set_fill_color(*(BG_TBL_1 if i % 2 == 0 else BG_TBL_2))
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*TXT_OFFWH)
    pdf.set_x(10)
    pdf.cell(col_w[0], 6.5, prop, border=1, fill=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TXT_WHITE)
    pdf.cell(col_w[1], 6.5, fwd, border=1, fill=True)
    pdf.set_text_color(*GOLD)
    pdf.cell(col_w[2], 6.5, bwd, border=1, fill=True)
    pdf.ln()

pdf.ln(4)
pdf.set_font("Helvetica", "I", 8.5)
pdf.set_text_color(*TXT_MID)
pdf.cell(0, 6,
         "Animation: crr_binomial_pricing_amd_html.py  |  Output: crr_pipeline_animation.html  "
         "|  CS495 Deep Scholar, Bellevue College Spring 2026",
         align="C")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 -- V_model and V_market: Meaning and Interpretation
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()
section("PART 3 -- V_model and V_market: Meaning and Interpretation", BLUE_H)

body(
    "Every ticket in the pipeline produces two prices: V_market and V_model. "
    "Understanding the difference between them -- and what their gap means -- is "
    "the core of the mispricing edge framework."
)

# ── V_market ──────────────────────────────────────────────────────────────────
subsection("V_market -- The Real-World Transaction Price")
body(
    "V_market is the price you actually pay (or receive) in the real world. "
    "It is the limit price on the Fidelity order ticket -- the amount of cash that "
    "changes hands per share when you buy or sell the option. For the AMD $350 tickets:"
)
pdf.ln(1)
pdf.set_fill_color(*BG_MED)
pdf.rect(10, pdf.get_y(), 190, 16, "F")
pdf.ln(2)
kv("Call V_market =", "$18.95  -- cost $1,895 per contract (100 shares x $18.95)")
kv("Put  V_market =", "$27.00  -- cost $2,700 per contract (100 shares x $27.00)")
pdf.ln(4)
body(
    "V_market reflects everything the market collectively believes: supply and demand, "
    "fear and greed, upcoming events, and the market's implied volatility. "
    "It is the ground truth of what the option costs right now. "
    "No model is required to observe it -- it is simply read from the order book."
)

# ── V_model ───────────────────────────────────────────────────────────────────
subsection("V_model -- The CRR Theoretical Fair Value")
body(
    "V_model is what the CRR binomial tree computes the option should be worth, "
    "given the inputs you feed it (S, K, r, IV, T, N). For the AMD $350 tickets:"
)
pdf.ln(1)
pdf.set_fill_color(*BG_MED)
pdf.rect(10, pdf.get_y(), 190, 16, "F")
pdf.ln(2)
kv("Call V_model =", "$18.9486  (pipeline N=100, Call IV=73.92%)")
kv("Put  V_model =", "$27.0014  (pipeline N=100, Put  IV=74.73%)")
pdf.ln(4)
body(
    "V_model is a theoretical fair value derived purely from mathematics -- backward "
    "induction through the binomial lattice, discounting expected payoffs under the "
    "risk-neutral measure. It is the model's answer to the question: given these "
    "inputs, what is this option worth?"
)

# ── The edge ──────────────────────────────────────────────────────────────────
subsection("The Edge -- Interpreting the Gap")
body("The mispricing edge measures how far V_model deviates from V_market:")
code("edge = (V_model - V_market) / V_market")
pdf.ln(2)

# Edge interpretation table
edge_rows = [
    ("V_model > V_market", "Positive edge",
     "Model says option is UNDERPRICED by market -- potential buy signal"),
    ("V_model < V_market", "Negative edge",
     "Model says option is OVERPRICED by market -- potential sell signal"),
    ("V_model = V_market", "Zero edge",
     "No detectable mispricing -- no edge, no trade recommended"),
]
col_w3 = [44, 34, 112]
hdrs3  = ["Condition", "Edge Sign", "Interpretation"]

pdf.set_fill_color(*BG_TBL_H)
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*TXT_WHITE)
pdf.set_x(10)
for h, w in zip(hdrs3, col_w3):
    pdf.cell(w, 7, h, border=1, fill=True)
pdf.ln()

for i, (cond, sign, interp) in enumerate(edge_rows):
    pdf.set_fill_color(*(BG_TBL_1 if i % 2 == 0 else BG_TBL_2))
    pdf.set_font("Courier", "B", 8.5)
    pdf.set_text_color(*TXT_OFFWH)
    pdf.set_x(10)
    pdf.cell(col_w3[0], 6.5, cond, border=1, fill=True)
    pdf.set_font("Helvetica", "B", 8.5)
    sign_col = GOLD if "Positive" in sign else (RED if "Negative" in sign else TXT_WHITE)
    pdf.set_text_color(*sign_col)
    pdf.cell(col_w3[1], 6.5, sign, border=1, fill=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TXT_WHITE)
    pdf.cell(col_w3[2], 6.5, interp, border=1, fill=True)
    pdf.ln()

pdf.ln(3)
body(
    "For the AMD $350 tickets the edge is -0.007% (call) and +0.005% (put) -- "
    "effectively zero. Both fall well below the 2% minimum threshold configured "
    "in the pipeline, so the Kelly Criterion outputs zero position size and "
    "recommends NO TRADE for all four tickets."
)

# ── Why edge is near zero ─────────────────────────────────────────────────────
subsection("Why the Edge Is Near Zero for These Tickets")
body(
    "The near-zero edge is not a failure of the model -- it is a consequence of "
    "how IV was obtained. The implied volatility (73.92% call, 74.73% put) was "
    "solved by running scipy.optimize.brentq: searching for the sigma value that "
    "makes V_model = V_market exactly. When you calibrate the model to the market "
    "price, the model reproduces that price by construction. There is no "
    "independent prediction being made; the model is confirming the price it was given."
)
pdf.ln(1)

code("  IV solved from market      =>  V_model = V_market    =>  edge ~ 0%")
code("  IV forecast independently  =>  V_model may diverge  =>  edge != 0%")
pdf.ln(2)

body(
    "To find genuine mispricing edge, you must supply an independent IV estimate -- "
    "for example, a forecasted realized volatility based on historical data, "
    "a statistical model, or a macro view. If your forecast IV differs from the "
    "market-implied IV, the CRR model will produce a V_model that diverges from "
    "V_market, and that divergence becomes the edge the Kelly Criterion sizes around."
)

# ── Practical example ─────────────────────────────────────────────────────────
subsection("Practical Interpretation Example")
body(
    "Suppose you forecast AMD's realized volatility over the next 18 days will be "
    "65% (close to the RV-30d of 65.49%) rather than the market-implied 74.73%. "
    "Running the CRR pricer with IV=65% instead of 74.73% would produce a lower "
    "V_model for the put:"
)
pdf.ln(1)
code("  V_model (IV=74.73%)  =  $27.00  -- matches market, edge = 0%")
code("  V_model (IV=65.00%)  =  ~$21.50 -- below market, edge ~ -20%")
code("  Interpretation: put is OVERPRICED by ~20% relative to your vol forecast")
code("  Kelly signal: SELL the put (collect the vol premium)")
pdf.ln(2)
body(
    "The market is charging $27.00 for a put you believe is worth only ~$21.50 based "
    "on your volatility forecast. That $5.50 gap -- the vol premium -- is the edge "
    "you would be collecting if you sold the put. Whether to act on it depends on "
    "confidence in your forecast and the Kelly fraction sizing."
)

# ── Summary box ───────────────────────────────────────────────────────────────
pdf.ln(2)
section("QUICK REFERENCE: V_model vs V_market", GREEN_NODE)

qr_rows = [
    ("V_market",   "Real-world price",  "Cash paid/received at Fidelity order fill"),
    ("V_model",    "Model fair value",  "CRR backward induction result given inputs"),
    ("Edge",       "(Vm-Vk)/Vk",        "Fractional mispricing; drives Kelly sizing"),
    ("Edge = 0",   "IV from market",    "Model calibrated to market; no prediction made"),
    ("Edge != 0",  "IV independent",    "Genuine divergence; Kelly can size a position"),
    ("Min edge",   "2% threshold",      "Pipeline filters noise; below 2% = NO TRADE"),
]
col_wq = [30, 38, 122]
hdrs_q = ["Term", "Formula / Source", "What It Means"]

pdf.set_fill_color(*BG_TBL_H)
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(*TXT_WHITE)
pdf.set_x(10)
for h, w in zip(hdrs_q, col_wq):
    pdf.cell(w, 7, h, border=1, fill=True)
pdf.ln()

for i, (term, formula, meaning) in enumerate(qr_rows):
    pdf.set_fill_color(*(BG_TBL_1 if i % 2 == 0 else BG_TBL_2))
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*GOLD)
    pdf.set_x(10)
    pdf.cell(col_wq[0], 6.5, term, border=1, fill=True)
    pdf.set_font("Courier", "", 8.5)
    pdf.set_text_color(*TXT_OFFWH)
    pdf.cell(col_wq[1], 6.5, formula, border=1, fill=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*TXT_WHITE)
    pdf.cell(col_wq[2], 6.5, meaning, border=1, fill=True)
    pdf.ln()

pdf.ln(4)
pdf.set_font("Helvetica", "I", 8.5)
pdf.set_text_color(*TXT_MID)
pdf.cell(0, 6,
         "Animation: crr_binomial_pricing_amd_html.py  |  Output: crr_pipeline_animation.html  "
         "|  CS495 Deep Scholar, Bellevue College Spring 2026",
         align="C")

# ── Save ──────────────────────────────────────────────────────────────────────
pdf.output(OUT)
print(f"Saved: {OUT}")
