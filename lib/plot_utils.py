"""AUROC1 plotting for easy-search remote homology."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import FIGURES_DIR, METHODS, METRICS_DIR, PALETTE, ensure_work_dirs, metric_prefix


def roc_plot(ax, file: Path, tool: str, color: str | None = None) -> float:
    """Sort by sensitivity descending; AUC = mean sensitivity."""
    data = []
    with file.open() as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                data.append(parts)
    if not data:
        return 0.0
    data.sort(key=lambda x: float(x[3]), reverse=True)
    x = [(i + 1) / len(data) for i in range(len(data))]
    y = [float(row[3]) for row in data]
    auc_val = sum(y) / len(y)
    ax.plot(x, y, label=f"{tool} AUC={auc_val:.3f}", color=color, linewidth=1.4)
    return auc_val


def plot_auroc1_easy(
    output_png: Path | None = None,
    auc_csv: Path | None = None,
) -> tuple[Path, Path]:
    ensure_work_dirs()
    output_png = Path(output_png or (FIGURES_DIR / "auroc1_easy.png"))
    auc_csv = Path(auc_csv or (METRICS_DIR / "auc_easy.csv"))

    level_files = {"Family": "fam", "Superfamily": "sup", "Fold": "fol"}
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    auc_rows: list[dict] = []

    for ax, (title, level_key) in zip(axs, level_files.items()):
        ax.set_title(title, fontsize=16)
        row: dict[str, float | str] = {"search_mode": "easy", "level": title}
        for label, key, _di in METHODS:
            path = Path(str(metric_prefix(key)) + f"_{level_key}.tsv")
            if not path.is_file():
                print(f"❌ {label} {title}: 缺少 {path}")
                continue
            auc_val = roc_plot(ax, path, label, color=PALETTE.get(label))
            row[label] = auc_val
            print(f"✅ {label} {title}: AUC={auc_val:.4f}")
        auc_rows.append(row)
        ax.set_xlim(-0.01, 1.01)
        ax.set_ylim(-0.01, 1.01)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        legend_loc = "upper right" if title == "Fold" else "lower left"
        ax.legend(fontsize=8, loc=legend_loc)

    axs[0].set_ylabel("Fraction of TPs up to first FP", fontsize=12)
    axs[1].set_xlabel("Fraction of queries", fontsize=12)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close()
    print(f"图片: {output_png}")

    df = pd.DataFrame(auc_rows)
    df.to_csv(auc_csv, index=False)
    print(f"AUC CSV: {auc_csv}")
    return output_png, auc_csv
