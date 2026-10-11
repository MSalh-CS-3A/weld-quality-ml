# Prédiction de la Qualité des Soudures Métalliques par Apprentissage Statistique

> **Branche de travail :** `travail_CHEBLI`  
> **Cadre :** Module d'Apprentissage Automatique -- CentraleSupélec 

---

## 📌 Présentation du Projet
L'assemblage par soudage des aciers de construction constitue une étape critique dans la réalisation d'infrastructures de grande envergure (éoliennes offshore, conduites de transport sous-marines, cuves sous pression). Traditionnellement guidée par des qualifications d'ateliers empiriques et destructives, la caractérisation des cordons de soudure représente un enjeu économique majeur.

Ce projet développe une chaîne complète de Machine Learning permettant de :
1. Prédire avec précision les propriétés mécaniques de traction ($R_m$, UTS) à partir de la composition chimique et des paramètres thermiques d'arc.
2. Classifier la conformité métallurgique selon les normes industrielles (API 5L X70 / EN 10025 S460).
3. Exploiter les données non étiquetées ($55\%$ des éprouvettes sans mesure mécanique) via des paradigmes d'apprentissage **semi-supervisé** (*Self-Training* et *Label Spreading*).

---

## 📂 Organisation de la Branche (`travail_CHEBLI`)

```text
├── README.md                      <- Présentation globale, méthodologie et résultats
├── requirements.txt               <- Dépendances Python pour reproduire les résultats
├── projet_soudures_ml.ipynb       <- Notebook Jupyter complet et exécuté (EDA, ACP, Modèles, SSL)
├── summary_metrics.json           <- Métriques numériques détaillées exportées des modèles
├── rapport_projet_soudures.tex    <- Rapport scientifique complet rédigé en LaTeX (format article ~5 pages)
│
├── figures/                       <- Graphiques haute résolution générés pour le rapport
│   ├── acp_projection.png         <- Projection des soudures sur le plan factoriel PC1-PC2
│   ├── acp_scree_circle.png       <- Éboulis des valeurs propres et cercle des corrélations
│   ├── eda_missing_values.png     <- Taux de données manquantes par descripteur
│   ├── feature_importance.png     <- Importance des variables métallurgiques (Random Forest)
│   ├── model_comparison_regression.png <- Comparatif R² et RMSE des modèles supervisés
│   ├── parity_and_residuals.png   <- Graphique de parité (y vs y_hat) et distribution des résidus
│   └── semi_supervised_comparison.png  <- Gain de précision du semi-supervisé selon le taux de labels
│
└── data/
    └── README.md                  <- Source, dictionnaire des variables et lien vers WeldDB (Cambridge)
```

---

## 🔬 Méthodologie et Principaux Résultats

### 1. Prétraitement et ACP
* **Intégrité métrologique :** Correction de l'interprétation locale du point décimal anglais et exclusion des éléments traces à $>85\%$ de valeurs manquantes (Co, W, As, Sn, Sb).
* **Pipelines sans fuite (*Data Leakage Free*) :** Imputation médiane et standardisation $Z$-score calculées strictement à l'intérieur de chaque pli d'apprentissage en validation croisée 5-plis.
* **ACP factorielle (32,3% d'inertie sur PC1-PC2) :** L'axe 1 capture la trempabilité et l'alliage (Mo, Cr, Ni, Mn), tandis que l'axe 2 traduit le bilan thermique (énergie d'arc vs traitement post-soudage PWHT).

### 2. Régression Supervisée Multi-Modèles (Prédiction de $R_m$)
Banc d'essai comparatif en validation croisée 5-plis :

| Modèle | $R^2$ (moyenne $\pm$ std) | RMSE (MPa) | MAE (MPa) | Statut |
| :--- | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** | $\mathbf{0{,}872 \pm 0{,}052}$ | $\mathbf{30{,}51 \pm 6{,}68}$ | $\mathbf{19{,}89 \pm 2{,}53}$ | **Champion** 🏆 |
| Random Forest Regressor | $0{,}835 \pm 0{,}051$ | $35{,}09 \pm 6{,}47$ | $24{,}66 \pm 2{,}74$ | Très robuste |
| Support Vector Regression (RBF) | $0{,}762 \pm 0{,}076$ | $42{,}32 \pm 8{,}29$ | $26{,}91 \pm 4{,}42$ | Performant |
| $k$-Plus Proches Voisins ($k=7$) | $0{,}745 \pm 0{,}081$ | $43{,}64 \pm 7{,}23$ | $28{,}58 \pm 2{,}79$ | Non-linéaire local |
| Régression Ridge ($\alpha=10$) | $0{,}604 \pm 0{,}077$ | $54{,}84 \pm 7{,}52$ | $40{,}09 \pm 4{,}43$ | Baseline linéaire |
| Multi-Layer Perceptron (MLP) | $0{,}275 \pm 0{,}808$ | $66{,}74 \pm 35{,}29$ | $37{,}57 \pm 4{,}48$ | Forte variance |

> **Constat :** XGBoost capture avec une précision remarquable ($\text{MAE} < 20\,\text{MPa}$) les interactions non-linéaires entre chimie et procédé, sous le seuil d'incertitude expérimentale de traction normalisée ($\pm 25\,\text{MPa}$).

### 3. Apprentissage Semi-Supervisé (SSL)
Pour valoriser les 914 soudures sans essai mécanique, nous avons testé le *Self-Training* (avec seuil de confiance $\tau=0{,}80$) et le *Label Spreading* (sur graphe de similarité) :
* À **10% de données labellisées** (budget d'essais réduit), le **Self-Training** porte la précision de classification à **$75{,}00\%$** (contre $73{,}31\%$ en supervisé seul, soit un gain net de **$+1{,}69\%$**).

### 4. Interprétabilité Métallurgique (Top Features)
* **Molybdène (Mo, 34,1%) :** Favorise la nucléation de **ferrite aciculaire** (compromis optimal haute résistance / ténacité) et durcit par précipitation de carbures fins lors du revenu.
* **Manganèse (Mn, 14,1%) et Chrome (Cr, 10,7%) :** Éléments majeurs de trempabilité et d'affinement du grain.
* **Paramètres thermiques (PWHT et Heat Input) :** Régulent le temps de refroidissement $t_{8/5}$ et relaxent les contraintes résiduelles de traction.

---

## 🚀 Guide de Reproduction

### Installation de l'environnement
```bash
git clone <URL_DU_REPO>
git checkout travail_CHEBLI
pip install -r requirements.txt
```

### Exécution du Notebook
Lancer Jupyter Notebook ou JupyterLab :
```bash
jupyter notebook projet_soudures_ml.ipynb
```

### Compilation du Rapport LaTeX
```bash
pdflatex rapport_projet_soudures.tex
pdflatex rapport_projet_soudures.tex
```

---

## 📚 Références des Données
* **Base WeldDB :** Cool T., Bhadeshia H.K.D.H., MacKay D.J.C., *Neural Network Analysis of Steel Weld Metal Mechanical Properties*, Materials Science and Engineering: A, 1997.
* **Lien de téléchargement :** [https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html)
