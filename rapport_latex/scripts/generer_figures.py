"""Génère les figures du rapport LaTeX à partir des données et des exports.

Ce script ne réentraîne aucun modèle : il relit le brut (`data/raw/`), la
préparation (`data/processed/modeling/`) et les exports des notebooks 03 à 09
(`data/processed/experiments/`), puis écrit des PDF vectoriels dans
`rapport_latex/figures/`. Exécuter les notebooks 01 → 09 au préalable.
Les résultats supervisés utilisent la sélection interne à six familles
(XGBoost compris) du notebook 08.

    python rapport_latex/scripts/generer_figures.py

Les valeurs clés recalculées (ACP, effectifs) sont affichées pour contrôle.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = next(p for p in [Path(__file__).resolve(), *Path(__file__).resolve().parents]
            if (p / "sujet.md").is_file() and (p / "notebooks").is_dir())
RAW = ROOT / "data/raw/welddb.data"
MODELING = ROOT / "data/processed/modeling"
EXP = ROOT / "data/processed/experiments"
OUT = ROOT / "rapport_latex/figures"
OUT.mkdir(parents=True, exist_ok=True)

# Palette catégorielle validée (ordre fixe) et encres de texte.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
NEUTRAL = "#c3c2b7"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
DIVERGING = LinearSegmentedColormap.from_list("div", [BLUE, "#f0efec", "#e34948"])
SEQUENTIAL = LinearSegmentedColormap.from_list(
    "seq", ["#f7fbff", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": NEUTRAL, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "legend.frameon": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

TARGETS = ["yield_strength", "uts", "elongation", "charpy_J"]
TRACTION = TARGETS[:3]
LABEL = {"yield_strength": "Limite d'élasticité (MPa)", "uts": "Résistance maximale (MPa)",
         "elongation": "Allongement (points de %)", "charpy_J": "Énergie Charpy* (J)"}
SHORT = {"yield_strength": "YS", "uts": "UTS", "elongation": "Allong.", "charpy_J": "Charpy*"}
FAMILY = {"median_y": "Médiane de y", "ridge": "Ridge", "svr_rbf": "SVR RBF",
          "random_forest": "Random Forest", "knn": "kNN", "xgboost": "XGBoost",
          "inner_selected": "Sélection\ninterne"}
TEXT_W = 6.3  # largeur utile du rapport en pouces


def fr(x, digits=3):
    return f"{x:.{digits}f}".replace(".", ",")


class CommaFormatter(ScalarFormatter):
    """Graduations numériques avec virgule décimale, comme dans le texte."""

    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace(".", ",")


def save(fig, name):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if type(axis.get_major_formatter()) is ScalarFormatter:
                axis.set_major_formatter(CommaFormatter())
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print(f"  figures/{name}.pdf")


# ---------------------------------------------------------------- EDA (brut)
RAW_COLS = ["C", "Si", "Mn", "S", "P", "Ni", "Cr", "Mo", "V", "Cu", "Co", "W",
            "O_ppm", "Ti_ppm", "N_ppm", "Al_ppm", "B_ppm", "Nb_ppm", "Sn_ppm", "As_ppm",
            "Sb_ppm", "current_A", "voltage_V", "ac_dc", "polarity", "heat_input_kJmm",
            "interpass_C", "weld_type", "pwht_temp_C", "pwht_time_h", "yield_strength",
            "uts", "elongation", "reduction_area", "charpy_temp_C", "charpy_J", "hardness",
            "fatt50", "prim_ferrite", "ferrite_2nd_phase", "acicular_ferrite", "martensite",
            "ferrite_carbide", "weld_id"]
NUM_COLS = [c for c in RAW_COLS if c not in ["ac_dc", "polarity", "weld_type", "weld_id"]]
CORE11 = ["C", "Si", "Mn", "S", "P", "current_A", "voltage_V", "heat_input_kJmm",
          "interpass_C", "pwht_temp_C", "pwht_time_h"]
INPUTS16 = CORE11 + ["O_ppm", "N_ppm", "Ni", "Cr", "Mo"]
VAR_FR = {"C": "C", "Si": "Si", "Mn": "Mn", "S": "S", "P": "P", "Ni": "Ni", "Cr": "Cr",
          "Mo": "Mo", "O_ppm": "O", "N_ppm": "N", "current_A": "Courant",
          "voltage_V": "Tension", "heat_input_kJmm": "Apport thermique",
          "interpass_C": "T. entre passes", "pwht_temp_C": "T. PWHT",
          "pwht_time_h": "Durée PWHT", "charpy_temp_C": "T. essai Charpy",
          "yield_strength": "YS", "uts": "UTS", "elongation": "Allongement",
          "reduction_area": "Réd. de section", "charpy_J": "Énergie Charpy"}

raw = pd.read_csv(RAW, sep=r"\s+", header=None, names=RAW_COLS, dtype=str,
                  keep_default_na=False)
exact = raw[NUM_COLS].apply(pd.to_numeric, errors="coerce")
duplicate_excess = raw[RAW_COLS[:-1]].duplicated()
observed = exact.loc[~duplicate_excess]
process = raw.weld_type.replace({"ShMA": "MMA", "SMA": "SA"})
print(f"Brut : {len(raw)} lignes ; dédupliqué : {len(observed)} lignes")


def fig_statuts():
    status = pd.DataFrame({
        "Nombre exact": exact.notna().sum(),
        "Non rapporté (N)": raw[NUM_COLS].eq("N").sum(),
        "Valeur spéciale (<L, intervalle, annotation)": (raw[NUM_COLS].ne("N") & exact.isna()).sum(),
    }).div(len(raw))
    fig, ax = plt.subplots(figsize=(TEXT_W, 6.4))
    left = np.zeros(len(status))
    for col, color in zip(status.columns, [BLUE, NEUTRAL, ORANGE]):
        ax.barh(status.index, status[col], left=left, color=color, height=0.72,
                label=col, edgecolor="white", linewidth=0.8)
        left += status[col].to_numpy()
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Proportion des 1 652 lignes brutes")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3)
    save(fig, "eda_statuts_mesures")


def fig_distributions():
    selected = [("C", "% massique"), ("Mn", "% massique"), ("heat_input_kJmm", "kJ/mm"),
                ("current_A", "A"), ("interpass_C", "°C"), ("pwht_temp_C", "°C"),
                ("yield_strength", "MPa"), ("uts", "MPa"), ("elongation", "%")]
    names = {"C": "Carbone", "Mn": "Manganèse", "heat_input_kJmm": "Apport thermique",
             "current_A": "Courant", "interpass_C": "T. entre passes",
             "pwht_temp_C": "T. PWHT", "yield_strength": "Limite d'élasticité",
             "uts": "Résistance max.", "elongation": "Allongement"}
    fig, axes = plt.subplots(3, 3, figsize=(TEXT_W, 5.6))
    for ax, (col, unit) in zip(axes.flat, selected):
        s = observed[col].dropna()
        ax.hist(s, bins=25, color=BLUE, edgecolor="white", linewidth=0.5)
        ax.set_title(f"{names[col]} (n = {len(s)})", fontsize=8.5)
        ax.set_xlabel(unit)
        ax.grid(axis="x", visible=False)
    for ax in axes[:, 0]:
        ax.set_ylabel("Effectif")
    fig.tight_layout(h_pad=0.8)
    save(fig, "eda_distributions")


def fig_absences_procede():
    cols = INPUTS16 + ["yield_strength", "uts", "elongation", "charpy_temp_C", "charpy_J"]
    dedup = raw.loc[~duplicate_excess]
    proc = process.loc[~duplicate_excess]
    missing = dedup[cols].eq("N").groupby(proc).mean().T * 100
    counts = proc.value_counts()
    missing = missing[counts.index]
    fig, ax = plt.subplots(figsize=(TEXT_W, 5.4))
    im = ax.imshow(missing.to_numpy(), cmap=SEQUENTIAL, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(missing.shape[1]),
                  [f"{p}\n(n={counts[p]})" for p in missing.columns])
    ax.set_yticks(range(missing.shape[0]), [VAR_FR[c] for c in missing.index])
    for i in range(missing.shape[0]):
        for j in range(missing.shape[1]):
            v = missing.iat[i, j]
            if v >= 0.5:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                        color="white" if v > 55 else INK)
    ax.grid(False)
    ax.axhline(len(INPUTS16) - 0.5, color="white", linewidth=2.5)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Valeurs non rapportées (%)")
    cb.outline.set_visible(False)
    ax.set_xlabel("Procédé de soudage (synonymes documentés regroupés)")
    save(fig, "eda_absences_procede")


def fig_correlations():
    cols = ["yield_strength", "uts", "elongation", "reduction_area"]
    corr = observed[cols].corr()
    labels = [VAR_FR[c] for c in cols]
    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    im = ax.imshow(corr.to_numpy(), cmap=DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(4), labels, rotation=30, ha="right")
    ax.set_yticks(range(4), labels)
    for i in range(4):
        for j in range(4):
            v = corr.iat[i, j]
            ax.text(j, i, fr(v, 2), ha="center", va="center", fontsize=7.5,
                    color="white" if abs(v) > 0.75 else INK)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.outline.set_visible(False)
    save(fig, "eda_correlations_cibles")
    print("  corr YS/UTS =", round(corr.iat[0, 1], 3), "; UTS/allong. =", round(corr.iat[1, 2], 3))


def fig_charpy():
    charpy = observed[["charpy_temp_C", "charpy_J"]].dropna()
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.6))
    ax.scatter(charpy.charpy_temp_C, charpy.charpy_J, s=9, color=BLUE, alpha=0.35,
               linewidths=0)
    for e in (28, 100):
        share = (charpy.charpy_J == e).sum()
        ax.axhline(e, color=MUTED, linewidth=0.8, linestyle=(0, (3, 2)))
        ax.text(charpy.charpy_temp_C.max(), e + 4, f"{e} J : {share} couples",
                ha="right", va="bottom", fontsize=7, color=INK2)
    ax.set_xlabel("Température d'essai (°C)")
    ax.set_ylabel("Énergie Charpy (J)")
    save(fig, "eda_charpy_couples")
    print(f"  Charpy : {len(charpy)} couples exacts dédupliqués")


def fig_acp():
    complete = observed[CORE11].dropna()
    proc = process.loc[complete.index]
    Z = StandardScaler().fit_transform(complete)
    pca = PCA().fit(Z)
    ratio = pca.explained_variance_ratio_
    scores = pca.transform(Z)
    print(f"  ACP : {len(complete)} lignes ; PC1={ratio[0]:.4f} PC2={ratio[1]:.4f} "
          f"cumul2={ratio[:2].sum():.4f} cumul3={ratio[:3].sum():.4f}")
    fig = plt.figure(figsize=(TEXT_W, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.55, wspace=0.32)
    ax1 = fig.add_subplot(gs[0, 0])
    k = np.arange(1, len(ratio) + 1)
    ax1.bar(k, ratio * 100, color=BLUE, width=0.6, label="Par composante")
    ax1.plot(k, ratio.cumsum() * 100, color=ORANGE, marker="o", markersize=4,
             linewidth=1.6, label="Cumul")
    ax1.set_xlabel("Composante principale")
    ax1.set_ylabel("Variance expliquée (%)")
    ax1.set_xticks(k)
    ax1.grid(axis="x", visible=False)
    ax1.legend(loc="center right")
    ax1.set_title("(a) Éboulis des valeurs propres")

    ax2 = fig.add_subplot(gs[0, 1])
    groups = [("MMA", BLUE), ("SA", ORANGE)]
    other = ~proc.isin([g for g, _ in groups])
    ax2.scatter(scores[other.to_numpy(), 0], scores[other.to_numpy(), 1], s=7,
                color=AQUA, alpha=0.6, linewidths=0, label=f"Autres procédés ({other.sum()})")
    for name, color in groups:
        m = (proc == name).to_numpy()
        ax2.scatter(scores[m, 0], scores[m, 1], s=7, color=color, alpha=0.45,
                    linewidths=0, label=f"{name} ({m.sum()})")
    ax2.set_xlabel(f"PC1 ({fr(ratio[0] * 100, 2)} %)")
    ax2.set_ylabel(f"PC2 ({fr(ratio[1] * 100, 2)} %)")
    ax2.legend(loc="upper left", markerscale=1.8, handletextpad=0.2)
    ax2.set_title("(b) Projection des observations")

    ax3 = fig.add_subplot(gs[1, :])
    load = pd.DataFrame(pca.components_[:2].T, index=CORE11, columns=["PC1", "PC2"])
    x = np.arange(len(CORE11))
    ax3.bar(x - 0.18, load.PC1, width=0.34, color=BLUE, label="PC1")
    ax3.bar(x + 0.18, load.PC2, width=0.34, color=ORANGE, label="PC2")
    ax3.axhline(0, color=NEUTRAL, linewidth=0.8)
    ax3.set_xticks(x, [VAR_FR[c] for c in CORE11], rotation=25, ha="right")
    ax3.set_ylabel("Coefficient (loading)")
    ax3.grid(axis="x", visible=False)
    ax3.legend(ncol=2, loc="upper left")
    ax3.set_title("(c) Contribution des variables standardisées aux deux premiers axes")
    save(fig, "eda_acp")


# ------------------------------------------------------- Préparation (cohorte)
def fig_absences_cohorte():
    miss = pd.read_csv(EXP / "salh_coreg_v1/input_missingness.csv").set_index("feature")
    miss = miss.loc[INPUTS16, "missing_fraction"] * 100
    order = miss.sort_values().index
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.9))
    colors = [ORANGE if c in ("Ni", "Cr", "Mo") else BLUE for c in order]
    ax.barh([VAR_FR[c] for c in order], miss[order], color=colors, height=0.62)
    for i, c in enumerate(order):
        if miss[c] > 0:
            ax.text(miss[c] + 0.8, i, f"{fr(miss[c], 1)} %", va="center", fontsize=7,
                    color=INK2)
    ax.set_xlabel("Entrées absentes dans la cohorte de 1 555 lignes (%)")
    ax.set_xlim(0, 70)
    ax.grid(axis="y", visible=False)
    ax.text(0.98, 0.05, "Orange : extension Ni/Cr/Mo (schéma 16)",
            transform=ax.transAxes, ha="right", fontsize=7, color=INK2)
    save(fig, "prep_absences_cohorte")


# ------------------------------------------------------------- Supervisé
def fold_stats(df, value):
    return df.groupby(["target", "model"])[value].agg(["mean", "std"])


def supervised_tables():
    # Six familles réglées en interne et procédure de sélection à six familles (notebook 08).
    scores = pd.read_csv(EXP / "salh_xgboost_v1/benchmark_outer_metrics.csv")
    return (fold_stats(scores[scores.protocol == "random"], "R2"),
            fold_stats(scores[scores.protocol == "grouped"], "R2"))


def fig_synthese():
    r, g = supervised_tables()
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.5))
    x = np.arange(len(TARGETS))
    for off, stats, color, name in [(-0.17, r, BLUE, "Validation aléatoire (KFold lignes)"),
                                    (0.17, g, ORANGE, "Validation groupée (séries exclues)")]:
        m = [stats.loc[(t, "inner_selected"), "mean"] for t in TARGETS]
        s = [stats.loc[(t, "inner_selected"), "std"] for t in TARGETS]
        ax.bar(x + off, m, width=0.32, color=color, label=name, yerr=s,
               error_kw={"ecolor": INK2, "elinewidth": 0.9, "capsize": 2.5})
        for xi, v in zip(x + off, m):
            ax.text(xi, -0.13, fr(v), ha="center", va="top", fontsize=7, color=INK2)
    ax.axhline(0, color=NEUTRAL, linewidth=0.8)
    ax.set_xticks(x, [LABEL[t].replace(" (", "\n(") for t in TARGETS])
    ax.tick_params(axis="x", pad=14)
    ax.set_ylabel("R² moyen des 5 plis ± écart-type")
    ax.set_ylim(-0.3, 1.0)
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    save(fig, "res_synthese_r2")


def fig_familles():
    r, g = supervised_tables()
    models = ["median_y", "ridge", "svr_rbf", "random_forest", "knn", "xgboost", "inner_selected"]
    fig, axes = plt.subplots(2, 2, figsize=(TEXT_W, 4.9), sharey=True)
    x = np.arange(len(models))
    for ax, t in zip(axes.flat, TARGETS):
        for off, stats, color, name in [(-0.19, r, BLUE, "Aléatoire"),
                                        (0.19, g, ORANGE, "Groupée")]:
            m = [stats.loc[(t, mo), "mean"] for mo in models]
            s = [stats.loc[(t, mo), "std"] for mo in models]
            ax.bar(x + off, m, width=0.36, color=color, label=name, yerr=s,
                   error_kw={"ecolor": INK2, "elinewidth": 0.7, "capsize": 1.8})
        ax.axhline(0, color=NEUTRAL, linewidth=0.8)
        ax.set_title(LABEL[t])
        ax.set_xticks(x, [FAMILY[m] for m in models], rotation=35, ha="right", fontsize=6.8)
        ax.grid(axis="x", visible=False)
        ax.axvspan(len(models) - 1.5, len(models) - 0.5, color=GRID, alpha=0.45, zorder=0)
    for ax in axes[:, 0]:
        ax.set_ylabel("R² moyen ± écart-type")
    axes[0, 0].set_ylim(-0.6, 1.0)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout(h_pad=1.0, rect=(0, 0, 1, 0.97))
    save(fig, "res_familles_r2")


def fig_obs_pred():
    preds = pd.read_csv(EXP / "salh_xgboost_v1/inner_selected_predictions.csv")
    rnd, grp = preds[preds.protocol == "random"], preds[preds.protocol == "grouped"]
    r, g = supervised_tables()
    fig, axes = plt.subplots(2, 4, figsize=(TEXT_W, 3.6))
    for row, (df, stats, color, name) in enumerate([(rnd, r, BLUE, "Aléatoire"),
                                                     (grp, g, ORANGE, "Groupée")]):
        for col, t in enumerate(TARGETS):
            ax = axes[row, col]
            d = df[df.target == t]
            lo = min(d.y_true.min(), d.y_pred.min())
            hi = max(d.y_true.max(), d.y_pred.max())
            ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=0.8, linestyle=(0, (3, 2)))
            ax.scatter(d.y_true, d.y_pred, s=4, color=color, alpha=0.4, linewidths=0)
            ax.text(0.04, 0.95, f"R² = {fr(stats.loc[(t, 'inner_selected'), 'mean'])}",
                    transform=ax.transAxes, va="top", fontsize=6.8, color=INK)
            ax.set_xlim(lo, hi)
            ax.set_ylim(lo, hi)
            ax.tick_params(labelsize=6)
            if row == 0:
                ax.set_title(SHORT[t] + {"yield_strength": " (MPa)", "uts": " (MPa)",
                                         "elongation": " (%)", "charpy_J": " (J)"}[t])
            if col == 0:
                ax.set_ylabel(f"{name}\nprédit", fontsize=7.5)
            if row == 1:
                ax.set_xlabel("observé", fontsize=7.5)
    fig.tight_layout(w_pad=0.6, h_pad=0.6)
    save(fig, "res_observe_predit")


# ------------------------------------------------------------ Diagnostics
def fig_sensibilites():
    s = pd.read_csv(EXP / "salh_diagnostics_v1/sensitivity_summary.csv")
    s = s[s.model == "random_forest"]
    fig, axes = plt.subplots(1, 4, figsize=(TEXT_W, 2.4), sharey=True)
    sets = ["A0_11", "A1_13", "A1b_16"]
    x = np.arange(3)
    for ax, t in zip(axes, TARGETS):
        d = s[s.target == t].set_index(["feature_set", "imputer"])
        for off, imp, color, name in [(-0.19, "median", BLUE, "Médiane"),
                                      (0.19, "iterative", ORANGE, "Itérative")]:
            vals = [d.loc[(fs, imp), "R2_mean"] for fs in sets]
            folds = [int(d.loc[(fs, imp), "folds"]) for fs in sets]
            ax.bar(x + off, np.nan_to_num(vals), width=0.36, color=color, label=name)
            for xi, v, f in zip(x + off, vals, folds):
                if f < 5:
                    y = 0.02 if np.isnan(v) or v < 0 else v + 0.02
                    ax.text(xi, y, f"{f}/5", ha="center", va="bottom", fontsize=6,
                            color=INK2, rotation=90)
        ax.axhline(0, color=NEUTRAL, linewidth=0.8)
        ax.set_xticks(x, ["11", "13", "16"])
        ax.set_xlabel("Nombre d'entrées")
        ax.set_title(SHORT[t])
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("R² moyen RF (groupée)")
    axes[0].legend(loc="upper left")
    fig.tight_layout(w_pad=0.5)
    save(fig, "diag_sensibilites_rf")


def fig_decoupages():
    s = pd.read_csv(EXP / "salh_random_kfold_v1/grouping_fixed_rf_summary.csv")
    s = s.set_index(["target", "protocol"])
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.5))
    x = np.arange(len(TARGETS))
    protos = [("random_rows", BLUE, "Lignes aléatoires"),
              ("condition_proxy", AQUA, "Conditions de soudage séparées"),
              ("inferred_series", ORANGE, "Séries inférées séparées")]
    for i, (p, color, name) in enumerate(protos):
        m = [s.loc[(t, p), "R2_mean"] for t in TARGETS]
        sd = [s.loc[(t, p), "R2_sd"] for t in TARGETS]
        ax.bar(x + (i - 1) * 0.26, m, width=0.24, color=color, label=name, yerr=sd,
               error_kw={"ecolor": INK2, "elinewidth": 0.8, "capsize": 2})
    ax.axhline(0, color=NEUTRAL, linewidth=0.8)
    ax.set_xticks(x, [LABEL[t].replace(" (", "\n(") for t in TARGETS])
    ax.set_ylabel("R² moyen ± écart-type")
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    save(fig, "diag_decoupages_rf")


def fig_biais_series():
    ge = pd.read_csv(EXP / "salh_diagnostics_v1/group_errors.csv")
    ge = ge[ge.model == "random_forest"]
    fig, axes = plt.subplots(2, 2, figsize=(TEXT_W, 4.4))
    for ax, t in zip(axes.flat, TARGETS):
        d = ge[ge.target == t].nlargest(6, "SSE_fraction").iloc[::-1]
        colors = [BLUE if b < 0 else "#e34948" for b in d.bias]
        ax.barh(d.group, d.bias, color=colors, height=0.6)
        ax.axvline(0, color=INK2, linewidth=0.8)
        ax.set_title(LABEL[t], fontsize=8.5)
        ax.tick_params(axis="y", labelsize=6.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Biais moyen prédit − observé", fontsize=7.5)
    fig.legend([Patch(color=BLUE), Patch(color="#e34948")],
               ["Sous-estimation de la série", "Surestimation de la série"],
               loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout(h_pad=1.0, w_pad=1.0, rect=(0, 0, 1, 0.97))
    save(fig, "diag_biais_series")


def fig_importance():
    pi = pd.read_csv(EXP / "salh_diagnostics_v1/permutation_importance_summary.csv")
    pi = pi[pi.kind == "bloc"]
    names = {"bloc_composition": "Composition", "bloc_PWHT": "PWHT",
             "bloc_soudage": "Paramètres de soudage", "bloc_procede": "Procédé",
             "bloc_temperature_essai": "Température d'essai"}
    units = {"yield_strength": "MPa", "uts": "MPa", "elongation": "points de %",
             "charpy_J": "J"}
    fig, axes = plt.subplots(2, 2, figsize=(TEXT_W, 3.9))
    for ax, t in zip(axes.flat, TARGETS):
        d = pi[pi.target == t].sort_values("MAE_increase")
        ax.barh([names[f] for f in d.feature], d.MAE_increase, color=BLUE, height=0.55,
                xerr=d.repeat_fold_sd, error_kw={"ecolor": INK2, "elinewidth": 0.8,
                                                 "capsize": 2})
        ax.axvline(0, color=INK2, linewidth=0.8)
        ax.set_title(LABEL[t], fontsize=8.5)
        ax.set_xlabel(f"Hausse de MAE ({units[t]})", fontsize=7.5)
        ax.grid(axis="y", visible=False)
    fig.tight_layout(h_pad=1.0, w_pad=1.0)
    save(fig, "diag_importance_blocs")


def fig_apprentissage():
    lc = pd.read_csv(EXP / "salh_diagnostics_v1/group_learning_curves.csv")
    m = lc.groupby(["target", "fraction"])[["MAE", "train_MAE"]].mean().reset_index()
    fig, axes = plt.subplots(1, 4, figsize=(TEXT_W, 2.2))
    for ax, t in zip(axes, TARGETS):
        d = m[m.target == t]
        ax.plot(d.fraction, d.MAE, color=ORANGE, marker="o", markersize=4, linewidth=1.6,
                label="Validation groupée")
        ax.plot(d.fraction, d.train_MAE, color=BLUE, marker="o", markersize=4,
                linewidth=1.6, label="Entraînement")
        ax.set_title(SHORT[t])
        ax.set_xticks([0.5, 0.75, 1.0], ["50 %", "75 %", "100 %"])
        ax.set_xlabel("Groupes du train")
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("MAE moyenne")
    axes[0].legend(loc="lower left", fontsize=6.5)
    fig.tight_layout(w_pad=0.6)
    save(fig, "diag_courbes_apprentissage")


# ------------------------------------------------------------------ COREG
def fig_coreg():
    # Référence supervisée actuelle : sélection à six familles ; COREG et contrôles inchangés.
    c = pd.read_csv(EXP / "salh_xgboost_v1/supervised_coreg_summary.csv").rename(
        columns={"model": "method"}).set_index(["protocol", "target", "method"])
    methods = [("inner_selected", BLUE, "Sélection supervisée à six familles (référence)"),
               ("matched_knn_pair", AQUA, "Moyenne kNN L1/L2, même k, sans pseudo-labels"),
               ("coreg", ORANGE, "COREG")]
    fig, axes = plt.subplots(1, 2, figsize=(TEXT_W, 2.5), sharey=True)
    x = np.arange(3)
    for ax, proto, title in [(axes[0], "random", "Validation aléatoire"),
                             (axes[1], "grouped", "Validation groupée")]:
        for i, (meth, color, name) in enumerate(methods):
            m = [c.loc[(proto, t, meth), "R2_mean"] for t in TRACTION]
            sd = [c.loc[(proto, t, meth), "R2_sd"] for t in TRACTION]
            ax.bar(x + (i - 1) * 0.26, m, width=0.24, color=color, label=name, yerr=sd,
                   error_kw={"ecolor": INK2, "elinewidth": 0.8, "capsize": 2})
        ax.axhline(0, color=NEUTRAL, linewidth=0.8)
        ax.set_xticks(x, [SHORT[t] for t in TRACTION])
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("R² moyen ± écart-type")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, fontsize=6.8,
               bbox_to_anchor=(0.5, 1.04))
    fig.tight_layout(w_pad=0.8, rect=(0, 0, 1, 0.92))
    save(fig, "coreg_comparaison")


def fig_coreg_iterations():
    it = pd.read_csv(EXP / "salh_coreg_v1/iteration_history.csv")
    it = it[it.stage == "outer"].sort_values("iteration")
    fig, axes = plt.subplots(1, 3, figsize=(TEXT_W, 2.2), sharey=True)
    for ax, t in zip(axes, TRACTION):
        for proto, color, name in [("random", BLUE, "Aléatoire"),
                                   ("grouped", ORANGE, "Groupée")]:
            d = it[(it.target == t) & (it.protocol == proto)]
            for k, (fold, f) in enumerate(d.groupby("outer_fold")):
                ax.plot(f.iteration, f.accepted.cumsum(), color=color, linewidth=1.1,
                        alpha=0.8, label=name if k == 0 else None)
                ax.plot(f.iteration.iloc[-1], f.accepted.sum(), "o", color=color,
                        markersize=3)
        ax.set_title(SHORT[t])
        ax.set_xlabel("Tour")
    axes[0].set_ylabel("Pseudo-labels cumulés")
    axes[0].legend(loc="upper left")
    fig.tight_layout(w_pad=0.6)
    save(fig, "coreg_iterations")


# ------------------------------------------------------------- Validation
def fig_validation():
    d = pd.read_csv(EXP / "salh_validation_v1/decision_summary.csv").set_index("source")
    sources = [("grouped", "Modèle GroupKFold"), ("random", "Modèle KFold aléatoire"),
               ("mesures", "Mesures")]
    # Couleurs de statut réservées, toujours accompagnées d'une étiquette.
    decisions = [("VALIDÉ", "#0ca30c"), ("PARTIEL", "#fab219"), ("NON VALIDÉ", "#d03b3b")]
    share = d.div(d.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(TEXT_W, 1.9))
    left = np.zeros(len(sources))
    for decision, color in decisions:
        v = np.array([share.loc[s, decision] for s, _ in sources])
        n = [int(d.loc[s, decision]) for s, _ in sources]
        ax.barh(range(len(sources)), v, left=left, height=0.62, color=color,
                edgecolor="white", linewidth=1.5, label=decision)
        for y, (x0, w, k) in enumerate(zip(left, v, n)):
            if w >= 6:
                ax.text(x0 + w / 2, y, f"{fr(w, 1)} % ({k})", ha="center", va="center",
                        fontsize=7, color=INK)
        left += v
    ax.set_yticks(range(len(sources)), [name for _, name in sources])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Part des 1 555 soudures de la cohorte (%)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.28))
    save(fig, "val_decisions")


if __name__ == "__main__":
    print("Génération des figures du rapport :")
    fig_statuts()
    fig_distributions()
    fig_absences_procede()
    fig_correlations()
    fig_charpy()
    fig_acp()
    fig_absences_cohorte()
    fig_synthese()
    fig_familles()
    fig_obs_pred()
    fig_sensibilites()
    fig_decoupages()
    fig_biais_series()
    fig_importance()
    fig_apprentissage()
    fig_coreg()
    fig_coreg_iterations()
    fig_validation()
