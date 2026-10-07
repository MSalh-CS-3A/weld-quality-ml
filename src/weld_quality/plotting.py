"""Plots for measured coverage, reconstruction checks and exploratory PCA."""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .schema import UNITS

METHOD_LABELS = {"median": "Médiane globale", "process_median": "Médiane par procédé",
                 "iterative": "Imputation itérative"}


def plot_missingness(audit, process):
    missing = audit.status.eq("missing")
    rates = missing.groupby(process).mean().mul(100).T
    counts = process.value_counts()
    rates.columns = [f"{c}\n(n={counts[c]})" for c in rates]
    fig, ax = plt.subplots(figsize=(12, 0.32 * len(rates) + 2))
    sns.heatmap(rates, vmin=0, vmax=100, cmap="YlOrRd", ax=ax,
                cbar_kws={"label": "Absences originales (%)"})
    ax.set_title("Absences par procédé — N signifie non rapporté")
    ax.set_xlabel("Procédé (synonymes documentés regroupés)")
    ax.set_ylabel("")
    fig.tight_layout()
    return fig


def plot_observed_correlations(values, title):
    correlations = values.corr()
    observed = values.notna().astype(int)
    counts = observed.T @ observed
    labels = pd.DataFrame("", index=values.columns, columns=values.columns)
    for a in values:
        for b in values:
            r = correlations.at[a, b]
            labels.at[a, b] = f"{r:.2f}\nn={counts.at[a, b]}" if pd.notna(r) else f"—\nn={counts.at[a, b]}"
    fig, ax = plt.subplots(figsize=(max(7, 1.1 * len(values.columns)), max(5, .8 * len(values.columns))))
    sns.heatmap(correlations, annot=labels, fmt="", vmin=-1, vmax=1, cmap="vlag", ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_benchmark(metrics, title):
    scores = metrics.loc[metrics.scope.eq("all")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, pattern in zip(axes, ["cells", "blocks"]):
        subset = scores.loc[scores.pattern.eq(pattern)]
        # Macro average across variables, then folds/seeds; no unit mixing.
        averages = subset.groupby(["method", "rate", "fold", "seed"]).normalized_mae.mean()
        for method, label in METHOD_LABELS.items():
            rates = averages.loc[method].groupby("rate")
            means, stds = rates.mean(), rates.std().fillna(0)
            ax.errorbar(means.index * 100, means, yerr=stds, marker="o", capsize=3, label=label)
        ax.set_title("Cellules isolées / PWHT conjoint" if pattern == "cells" else "Blocs inspirés de l'entraînement")
        ax.set_xlabel("Taux de masquage demandé (%)")
        ax.grid(alpha=.2)
    axes[0].set_ylabel("MAE / IQR d'entraînement (repli : écart-type)")
    axes[1].legend(fontsize=9)
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_ecdfs(before, filled, exact_observed, process=None, columns=None):
    """Plot separate populations; matching global distributions is not required."""
    columns = list(before) if columns is None else list(columns)
    processes = [None] if process is None else list(process.value_counts().head(3).index)
    fig, axes = plt.subplots(len(processes) * math.ceil(len(columns) / 4), 4,
                             figsize=(16, 3 * len(processes) * math.ceil(len(columns) / 4)), squeeze=False)
    for block, label in enumerate(processes):
        start = block * math.ceil(len(columns) / 4) * 4
        for j, col in enumerate(columns):
            ax = axes.flat[start + j]
            subset = pd.Series(True, index=before.index) if label is None else process.eq(label)
            populations = [
                ("Exactes utilisables", before.loc[subset & exact_observed[col], col], "#276c96"),
                ("Approximations", before.loc[subset & ~exact_observed[col] & before[col].notna(), col], "#f59b3b"),
                ("Estimations", filled.loc[subset & before[col].isna(), col], "#7b68a6"),
            ]
            for name, series, color in populations:
                values = np.sort(series.dropna().to_numpy())
                if len(values):
                    ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post",
                            label=f"{name} (n={len(values)})", color=color)
            ax.set_title(col + ("" if label is None else f" — {label}"))
            ax.set_xlabel(UNITS[col])
            ax.set_ylabel("Proportion cumulée")
            ax.legend(fontsize=7, loc="best")
        for j in range(len(columns), math.ceil(len(columns) / 4) * 4):
            axes.flat[start + j].set_visible(False)
    fig.suptitle("Distributions mesurées, approximées et estimées — populations distinctes", y=1.005)
    fig.tight_layout()
    return fig


def plot_pca(result, process, title):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    positions = np.arange(1, len(result.explained) + 1)
    axes[0].bar(positions, result.explained.variance_ratio * 100, label="Par axe")
    axes[0].plot(positions, result.explained.cumulative_ratio * 100, "o-", color="#f59b3b", label="Cumulée")
    axes[0].set_xlabel("Composante principale")
    axes[0].set_ylabel("Variance expliquée (%)")
    axes[0].legend()
    labels = process.reindex(result.scores.index)
    palette = sns.color_palette("tab10", labels.nunique())
    for color, name in zip(palette, sorted(labels.unique())):
        subset = result.scores.loc[labels.eq(name)]
        axes[1].scatter(subset.PC1, subset.PC2, s=12, alpha=.5, color=color, label=name)
    axes[1].set_xlabel(f"PC1 ({result.explained.variance_ratio.iloc[0]:.1%})")
    axes[1].set_ylabel(f"PC2 ({result.explained.variance_ratio.iloc[1]:.1%})")
    axes[1].legend(fontsize=7, loc="best")
    sns.heatmap(result.contributions.iloc[:, :2], cmap="Blues", ax=axes[2],
                cbar_kws={"label": "Contribution à l'axe (%)"})
    axes[2].set_ylabel("")
    axes[2].set_title("Contributions, sans importance prédictive")
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_sensitivity(table):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for ax, family in zip(axes, ["core", "extended"]):
        data = table.loc[table.family.eq(family) & table.max_angle_degrees.notna()]
        labels = data.scenario.str.removeprefix(family + "_")
        ax.barh(labels, data.max_angle_degrees, color="#7b68a6")
        ax.invert_yaxis()
        ax.set_title("Noyau" if family == "core" else "Entrées étendues")
        ax.set_xlabel("Angle maximal entre les sous-espaces PC1–PC2 (degrés)")
    fig.suptitle("Sensibilité de l'ACP — référence médiane, L/2 et milieu des intervalles")
    fig.tight_layout()
    return fig
