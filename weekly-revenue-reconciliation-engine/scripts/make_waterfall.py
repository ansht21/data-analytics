"""Generate Gross-to-Net waterfall PNG from real parquet data for README/LinkedIn."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_parquet(ROOT / "data" / "processed" / "cleaned_transactions.parquet")
sums = df.groupby("financial_bucket")["Amount"].sum()

gross = float(df["Amount"].sum())
cancel = float(sums.get("Cancellation Leakage", 0))
ret = float(sums.get("Return Leakage", 0))
loss = float(sums.get("Loss Leakage", 0))
transit = float(sums.get("In-Transit", 0))
pending = float(sums.get("Pending", 0))
net = float(sums.get("Net Realized", 0))

labels = ["Gross\nInvoiced", "Cancellations", "Returns", "Loss/\nDamage",
          "In-Transit\n(settlement lag)", "Pending", "Net\nRealized"]
deltas = [-cancel, -ret, -loss, -transit, -pending]  # negative steps


def fmt(v: float) -> str:
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1e7:
        return f"{sign}{a / 1e7:.2f} Cr"
    if a >= 1e5:
        return f"{sign}{a / 1e5:.2f} L"
    if a >= 1e3:
        return f"{sign}{a / 1e3:.1f}K"
    return f"{sign}{a:.0f}"


fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Same hue family as the "Midnight Deck" dashboard, darkened for a light
# background (this chart is shared on LinkedIn, where white reads best).
NAVY, RED, AMBER, GREY, TEAL = "#0B1220", "#E11D48", "#D97706", "#64748B", "#059669"
step_colors = [RED, AMBER, "#94A3B8", GREY, GREY]

# Floating steps: running total before each step
tops, bottoms, heights = [], [], []
running = gross
levels = [gross]  # level after each bar: levels[0]=gross, levels[1..5] after steps, levels[6]=net
for d in deltas:
    top = running
    running += d
    bottom = running
    tops.append(top)
    bottoms.append(bottom)
    heights.append(top - bottom)
    levels.append(running)
running_levels = levels  # levels[0..5]; net appended separately

x = list(range(7))
# Gross bar 0..gross, steps, net bar 0..net
bar_bottoms = [0] + bottoms + [0]
bar_tops = [gross] + tops + [net]
bar_heights = [t - b for b, t in zip(bar_bottoms, bar_tops, strict=False)]
bar_colors = [NAVY] + step_colors + [TEAL]

bars = ax.bar(x, bar_heights, bottom=bar_bottoms, color=bar_colors,
              edgecolor="white", linewidth=1.4, width=0.58, zorder=3)

# Connector lines: horizontal at each intermediate level between bars
width = 0.58
for i in range(6):
    # level after bar i = levels[i+1] for i=0..4, and net for i=5
    y_level = running_levels[i + 1] if i < 5 else net
    ax.plot([x[i] + width / 2, x[i + 1] - width / 2], [y_level, y_level],
            color=NAVY, linestyle=":", linewidth=1.2, alpha=0.6, zorder=2)

# Labels: value on top of each bar; tiny Loss bar gets offset label with arrow
offset = gross * 0.022
all_vals = [gross] + deltas + [net]
for i, (b, h, v) in enumerate(zip(bar_bottoms, bar_heights, all_vals, strict=False)):
    top = b + h
    if labels[i].startswith("Loss"):
        ax.annotate(fmt(v), xy=(i, top), xytext=(i + 0.9, top + gross * 0.06),
                    ha="left", va="bottom", fontsize=10, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color="black", linewidth=1))
    elif i == 5:  # Pending thin sliver — label above
        ax.text(i, top + offset, fmt(v), ha="center", va="bottom", fontsize=10, fontweight="bold")
    else:
        # inside top for tall bars, above for short ones
        if h > gross * 0.12:
            ax.text(i, top - gross * 0.03, fmt(v), ha="center", va="top",
                    fontsize=10, fontweight="bold", color="white")
            ax.text(i, top + offset * 0.6, "", ha="center", va="bottom")
        else:
            ax.text(i, top + offset, fmt(v), ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.5)
ax.set_title("Gross → Net Revenue Waterfall  |  ₹7.86 Cr invoiced → ₹1.86 Cr realized (23.7% clearance)",
             fontsize=12, fontweight="bold", pad=16)
ax.set_ylabel("Amount (₹)")
ax.set_ylim(0, gross * 1.14)
ax.spines[["top", "right"]].set_visible(False)
ax.ticklabel_format(style="plain", axis="y")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1e7:.1f} Cr" if v >= 1e7 else f"{v / 1e5:.0f}L"))
fig.tight_layout()

out = ROOT / "docs" / "images" / "08_gross_to_net_waterfall.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"wrote {out} ({out.stat().st_size} bytes)")
print(f"gross={gross:,.0f} cancel={cancel:,.0f} return={ret:,.0f} loss={loss:,.0f} "
      f"transit={transit:,.0f} pending={pending:,.0f} net={net:,.0f}")
