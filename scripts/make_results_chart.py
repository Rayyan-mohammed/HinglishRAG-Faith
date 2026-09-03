"""Generates the results chart for the presentation (B4) from results/metrics.md's numbers.
Saves to docs/figures/results_chart.png."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

OUTPUT = "docs/figures/results_chart.png"

metrics = {
    "Precision\n(flagged claims)": 0.18,
    "Recall\n(hallucinated claims)": 0.42,
    "Catch rate\n(strict)": 0.50,
    "Catch rate\n(loose)": 0.72,
    "False-alarm rate\n(correct answers)": 0.52,
}

colors = ["#c0392b", "#27ae60", "#2980b9", "#5dade2", "#e67e22"]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(metrics.keys(), metrics.values(), color=colors)

for bar, value in zip(bars, metrics.values()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.02,
        f"{value:.2f}",
        ha="center",
        fontweight="bold",
    )

ax.set_ylim(0, 1.0)
ax.set_ylabel("Score")
ax.set_title("CodeSwitch-Verify — Verification Layer Results\n(60 questions, 209 claims, 24 ground-truth hallucinated — post ADR-015 fixes)")
ax.axhline(0.5, color="gray", linewidth=0.5, linestyle="--")
plt.xticks(rotation=0, fontsize=9)
plt.tight_layout()

Path("docs/figures").mkdir(exist_ok=True)
plt.savefig(OUTPUT, dpi=150)
print(f"Saved {OUTPUT}")
