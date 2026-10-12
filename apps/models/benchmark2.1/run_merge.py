"""
Benchmark 2.1 — Merge & Final Analysis Script
Merges Part A & Part B results, computes:
1. Master Comparison Table (5-Fold Stratified CV, Balanced Categorical Cross-Entropy)
2. Per-Class Metrics Table (7 Classes: aceh, bali, limusin, madura, non_sapi, pasundan, po)
3. 8x8 Paired McNemar Statistical Significance Matrix
4. 8-Model Confusion Matrices (Aggregated across 5 folds, N=313)
5. Deployment Pareto Trade-off Scatter Plot (Macro F1 vs Latency vs Model Size)
6. Merged Pickle Artifacts
"""

import os
import math
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as scipy_stats
from sklearn.metrics import confusion_matrix

warnings.filterwarnings("ignore")
plt.rcParams["figure.dpi"] = 200
sns.set_style("whitegrid")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR

PARTA_RES = BASE_DIR / "all_results_partA.pkl"
PARTB_RES = BASE_DIR / "all_results_partB.pkl"
PARTA_DEP = BASE_DIR / "deployment_partA.pkl"
PARTB_DEP = BASE_DIR / "deployment_partB.pkl"

print(f"Loading Part A results from: {PARTA_RES}")
with open(PARTA_RES, "rb") as f:
    res_a = pickle.load(f)

print(f"Loading Part B results from: {PARTB_RES}")
with open(PARTB_RES, "rb") as f:
    res_b = pickle.load(f)

print(f"Loading Part A deployment metrics from: {PARTA_DEP}")
with open(PARTA_DEP, "rb") as f:
    dep_a = pickle.load(f)

print(f"Loading Part B deployment metrics from: {PARTB_DEP}")
with open(PARTB_DEP, "rb") as f:
    dep_b = pickle.load(f)

all_results = {**res_a, **res_b}
deployment = {**dep_a, **dep_b}

sample_key = list(all_results.keys())[0]
class_names = all_results[sample_key]["class_names"]
NUM_CLASSES = len(class_names)

MODEL_ORDER = [
    "MobileNetV3Large", "MobileNetV2", "EfficientNetB0", "DenseNet121",
    "EfficientNetV2S", "ConvNeXtTiny", "ResNet50", "MobileViT-XS"
]
MODEL_ORDER = [m for m in MODEL_ORDER if m in all_results]

print(f"\n[OK] Successfully merged {len(MODEL_ORDER)} models:")
for m in MODEL_ORDER:
    print(f"  - {m}")
print(f"Classes ({NUM_CLASSES}): {class_names}\n")

# ==========================================
# 1. Master Table (Phase 2)
# ==========================================
master_rows = []
for name in MODEL_ORDER:
    r = all_results[name]
    p2 = r["phase2"]
    dep = deployment.get(name, {})
    master_rows.append({
        "Model": name,
        "Macro F1": f"{np.mean(p2['f1']):.4f} ± {np.std(p2['f1']):.4f}",
        "Macro F1 (Mean)": round(float(np.mean(p2['f1'])), 4),
        "Macro F1 (Std)": round(float(np.std(p2['f1'])), 4),
        "Accuracy (%)": f"{np.mean(p2['acc'])*100:.2f} ± {np.std(p2['acc'])*100:.2f}",
        "Accuracy (Mean %)": round(float(np.mean(p2['acc']) * 100), 2),
        "Macro Precision": f"{np.mean(p2['prec']):.4f} ± {np.std(p2['prec']):.4f}",
        "Macro Recall": f"{np.mean(p2['rec']):.4f} ± {np.std(p2['rec']):.4f}",
        "Params (M)": round(float(dep.get('params_m', 0.0)), 2),
        "TFLite (MB)": round(float(dep.get('tflite_mb', 0.0)), 2),
        "Latency (ms)": round(float(dep.get('latency_ms', 0.0)), 2),
    })

master_df = pd.DataFrame(master_rows)
master_table_file = OUTPUT_DIR / "benchmark2_1_master_table.csv"
master_df.to_csv(master_table_file, index=False)
print("=" * 100)
print("  TABEL MASTER — BENCHMARK 2.1 (8 ARSITEKTUR, 7 KELAS, 5-FOLD STRATIFIED CV)")
print("=" * 100)
print(master_df[["Model", "Macro F1", "Accuracy (%)", "Macro Precision", "Macro Recall", "Params (M)", "TFLite (MB)", "Latency (ms)"]].to_string(index=False))
print(f"\nSaved master table to: {master_table_file}")

# ==========================================
# 2. Per-Class Metrics Table
# ==========================================
pc_rows = []
for name in MODEL_ORDER:
    p2 = all_results[name]["phase2"]
    p_mean = np.mean(p2["pc_p"], axis=0)
    r_mean = np.mean(p2["pc_r"], axis=0)
    f_mean = np.mean(p2["pc_f1"], axis=0)
    for i, c in enumerate(class_names):
        pc_rows.append({
            "Model": name,
            "Kelas": c,
            "Precision": round(float(p_mean[i]), 4),
            "Recall": round(float(r_mean[i]), 4),
            "F1_Score": round(float(f_mean[i]), 4),
        })

pc_df = pd.DataFrame(pc_rows)
pc_table_file = OUTPUT_DIR / "benchmark2_1_per_class_metrics.csv"
pc_df.to_csv(pc_table_file, index=False)
print(f"Saved per-class metrics to: {pc_table_file}")

# ==========================================
# 3. Paired McNemar Test (8x8)
# ==========================================
preds_dict = {}
trues_dict = {}
for name in MODEL_ORDER:
    preds_dict[name] = np.concatenate(all_results[name]["phase2"]["y_preds"])
    trues_dict[name] = np.concatenate(all_results[name]["phase2"]["y_trues"])

mcnemar_rows = []
for i in range(len(MODEL_ORDER)):
    for j in range(i + 1, len(MODEL_ORDER)):
        m_a = MODEL_ORDER[i]
        m_b = MODEL_ORDER[j]
        y_true = trues_dict[m_a]
        correct_a = (preds_dict[m_a] == y_true)
        correct_b = (preds_dict[m_b] == y_true)

        b = int(np.sum(correct_a & ~correct_b))  # A correct, B wrong
        c = int(np.sum(~correct_a & correct_b))  # A wrong, B correct

        if (b + c) == 0:
            p_val = 1.0
        elif (b + c) < 25:
            # Exact Binomial test
            p_val = float(2 * min(
                scipy_stats.binom.cdf(min(b, c), b + c, 0.5),
                1 - scipy_stats.binom.cdf(min(b, c) - 1, b + c, 0.5)
            ))
        else:
            # Chi-square with Edwards continuity correction
            chi2 = (abs(b - c) - 1)**2 / (b + c)
            p_val = float(1 - scipy_stats.chi2.cdf(chi2, df=1))

        p_val = min(1.0, max(0.0, p_val))
        sig = "Signifikan (p < 0.05)" if p_val < 0.05 else "Tidak Signifikan (Setara)"

        mcnemar_rows.append({
            "Model_A": m_a,
            "Model_B": m_b,
            "b (A+/B-)": b,
            "c (A-/B+)": c,
            "p_value": round(p_val, 4),
            "Kesimpulan": sig,
        })

mcnemar_df = pd.DataFrame(mcnemar_rows)
mcnemar_file = OUTPUT_DIR / "mcnemar_test_results_8x8.csv"
mcnemar_df.to_csv(mcnemar_file, index=False)
print(f"Saved McNemar test results to: {mcnemar_file}")

# ==========================================
# 4. Aggregated Confusion Matrices (8 Models)
# ==========================================
n_models = len(MODEL_ORDER)
cols = 4
rows = math.ceil(n_models / cols)
fig, axes = plt.subplots(rows, cols, figsize=(20, 10))
axes = np.array(axes).reshape(-1)

for idx, name in enumerate(MODEL_ORDER):
    ax = axes[idx]
    y_t = trues_dict[name]
    y_p = preds_dict[name]
    cm = confusion_matrix(y_t, y_p)
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=class_names, yticklabels=class_names, ax=ax
    )
    f1_val = np.mean(all_results[name]["phase2"]["f1"])
    ax.set_title(f"{name}\n(Macro F1: {f1_val:.4f})", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Label", fontsize=9)
    ax.set_xlabel("Predicted Label", fontsize=9)
    ax.tick_params(axis="x", rotation=45)

for idx in range(n_models, len(axes)):
    fig.delaxes(axes[idx])

plt.tight_layout()
cm_file = OUTPUT_DIR / "confusion_matrices_7class.png"
plt.savefig(cm_file, dpi=200, bbox_inches="tight")
plt.close()
print(f"Saved confusion matrices to: {cm_file}")

# ==========================================
# 5. Deployment Pareto Trade-off Scatter Plot
# ==========================================
fig, ax = plt.subplots(figsize=(10, 6.5))

xs, ys, sizes, labels = [], [], [], []
for name in MODEL_ORDER:
    f1_mean = np.mean(all_results[name]["phase2"]["f1"])
    dep = deployment.get(name, {})
    lat = float(dep.get("latency_ms", 10.0))
    tfl_mb = float(dep.get("tflite_mb", 10.0))

    xs.append(lat)
    ys.append(f1_mean)
    sizes.append(max(60.0, tfl_mb * 18.0))
    labels.append(name)

scatter = ax.scatter(
    xs, ys, s=sizes, alpha=0.65, edgecolors="black", linewidths=1.2,
    c=range(len(labels)), cmap="viridis"
)

for i, txt in enumerate(labels):
    tfl_size = deployment.get(txt, {}).get("tflite_mb", 0.0)
    # Give slight offset adjustments for readability
    xytext = (0, 12)
    if txt == "MobileNetV2":
        xytext = (-20, -18)
    elif txt == "MobileNetV3Large":
        xytext = (15, 12)
    elif txt == "EfficientNetB0":
        xytext = (0, 14)
    elif txt == "DenseNet121":
        xytext = (0, -20)
    elif txt == "ConvNeXtTiny":
        xytext = (-40, 12)

    ax.annotate(
        f"{txt}\n({float(tfl_size):.1f} MB)",
        (xs[i], ys[i]), textcoords="offset points", xytext=xytext,
        ha="center", fontsize=9, fontweight="bold"
    )

ax.set_title(
    "Pareto Trade-off: Macro F1-Score vs Latensi CPU vs Ukuran Model TFLite\n(Benchmark 2.1 — 8 Arsitektur, 7 Kelas)",
    fontsize=12, fontweight="bold", pad=12
)
ax.set_xlabel("CPU Latency (ms) [Lebih rendah lebih baik]", fontsize=10, labelpad=8)
ax.set_ylabel("Macro F1-Score [Lebih tinggi lebih baik]", fontsize=10, labelpad=8)
ax.set_ylim([0.65, 0.85])
ax.grid(True, linestyle="--", alpha=0.6)

plt.tight_layout()
tradeoff_file = OUTPUT_DIR / "tradeoff_chart_8models.png"
plt.savefig(tradeoff_file, dpi=200, bbox_inches="tight")
plt.close()
print(f"Saved Pareto trade-off plot to: {tradeoff_file}")

# ==========================================
# 6. Save Merged Pickles
# ==========================================
with open(OUTPUT_DIR / "all_results_merged.pkl", "wb") as f:
    pickle.dump(all_results, f)
with open(OUTPUT_DIR / "deployment_merged.pkl", "wb") as f:
    pickle.dump(deployment, f)
print(f"Saved merged pickle files to: {OUTPUT_DIR}")
print("\n[COMPLETE] All Part C artifacts successfully generated!")
