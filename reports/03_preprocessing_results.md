# Résultats de l'investigation de preprocessing

> Document historique antérieur à la migration des notebooks. Le protocole actif
> est dans `specs/spec.md` ; les sources antérieures sont conservées dans Git
> (sauvegarde `2ecb088`). Voir `reports/08_notebook_migration.md`.

Date : 5 octobre 2026. Analyse descriptive et vérification de reconstruction ;
aucune cible de qualité ou méthode prédictive n'est adoptée.

## Protocole exécuté

Le notebook `notebooks/01_eda.ipynb` a été exécuté de haut en bas. La comparaison
porte sur un noyau de 11 entrées et une extension de 22 entrées, avec 3 plis de
séries, graines 42 et 43, taux de masquage 10/20/40 %, cellules et blocs empiriques.
Les méthodes partagent les mêmes masques. Les valeurs cachées sont uniquement
exactes et sans drapeau de revue. Les imputers et les diagnostics appris de
reconstruction sont ajustés sur l'entraînement ; les ACP sur toute la base sont
strictement descriptives. Une ACP de diagnostic des scores est ajustée sur les
lignes exactes complètes d'entraînement, jamais sur les groupes de vérification.

Les erreurs normalisées ci-dessous sont des moyennes par variable et scénario,
avec IQR d'entraînement et repli sur l'écart-type. Elles ne représentent ni une
erreur en MPa ni un pourcentage d'erreur. Les deltas de corrélation utilisent
les mêmes paires exactes avant/après masquage, avec au moins 20 observations.
Les événements masqués se répètent entre scénarios : ils ne sont pas des
observations indépendantes supplémentaires.

| Matrice | Méthode | MAE normalisée moyenne | Delta absolu moyen des corrélations | Plis convergés |
| --- | --- | ---: | ---: | ---: |
| core | median | 1.6966 | 0.0840 | 3/3 |
| core | process_median | 1.2541 | 0.0692 | 3/3 |
| core | iterative | 0.8532 | 0.0663 | 3/3 |
| extended | median | 2.2532 | 0.1060 | 3/3 |
| extended | process_median | 2.0599 | 0.1063 | 3/3 |
| extended | iterative | 2.0089 | 0.1589 | 0/3 |

## Interprétation des contrôles

Le classement de reconstruction n'est pas un choix automatique de méthode pour
l'ACP. L'imputation itérative de l'extension ne converge pas avec le plafond
final de 100 itérations (tol=1e-3), y compris sur le jeu entier. Ses résultats
restent des diagnostics de sensibilité et ne justifient pas son adoption.
La référence médiane est conservée pour disposer d'un scénario simple explicite.
Les distributions par procédé et les changements de corrélations restent à
considérer avec les erreurs. Aucun résultat ne garantit la récupération des
vraies valeurs non rapportées.

Aucune estimation scorée ne dépasse les bornes physiques générales appliquées.
Ces bornes larges ne valident pas les unités ni la plausibilité métallurgique.
Les cellules mesurées non cachées ont été préservées par les assertions de chaque
comparaison. Les groupes d'entraînement et de vérification sont disjoints.

## ACP et couverture

La référence médiane du noyau explique 45.41 % de la
variance sur PC1–PC2 ; celle de l'extension explique
34.08 %. Cette différence ne mesure pas une
meilleure qualité d'analyse : le nombre de variables et leur préparation diffèrent.
Le fichier `pca_sensitivity.csv` contient les angles et distances des sous-espaces
pour les scénarios qui partagent les mêmes variables. Les cas complets sont aussi
sensibles à la sélection des observations, et pas seulement à l'imputation.

Les quatre propriétés de traction ont 650
lignes complètes pour une ACP sans imputation des propriétés. Charpy, dureté,
FATT et microstructure ne sont pas reconstruits dans une matrice globale de
qualité. Les résultats restent descriptifs et peuvent refléter les séries.

## Limites non résolues

- Les unités suspectes restent en revue, sans conversion arbitraire.
- Les annotations d'azote sont extraites lexicalement, sans assimiler `nd` à zéro.
- Les protocoles de dureté sont conservés, sans comparabilité déclarée.
- Les zéros de traitement thermique sont conservés et leur sens reste à confirmer.
- Les sommes microstructurales 90/99/119 % ne sont pas renormalisées.
- Les 47 groupes sont des séries déduites des identifiants,
  liées aussi par les doublons bruts ; ce ne sont pas des publications validées.
- Les contributions de l'ACP ne sont pas des importances prédictives ou des
  recommandations industrielles.

## Reproduction et artefacts

Repartir d'un noyau neuf et exécuter toutes les cellules du notebook. Les matrices,
provenances par cellule, bornes, statuts originaux, cas à vérifier, annotations,
groupes, plis, métriques et manifeste sont dans
`data/processed/preprocessing/` (ignoré par Git). Les figures sont dans
`reports/figures/`. Aucun modèle entraîné n'est sauvegardé.

SHA-256 du brut : `eb46df81a454c8e549187d87c67a6e72b88676f760e8688a782c832737676ac1`.
Versions : Python 3.14.7, pandas 3.0.6,
NumPy 2.5.3, scikit-learn 1.9.1.
Les hashes du code et paramètres complets figurent dans le manifeste.

Validation : 17 tests unitaires passent ; toutes les cellules de code du notebook
s'exécutent ; les sorties et figures sont enregistrées. Pour l'évaluation future,
repartir des valeurs préparées avant imputation et réajuster imputation, échelle,
sélection et ACP dans les plis d'entraînement. Une cible absente reste unlabeled.
