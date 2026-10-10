# KFold aléatoire 16/médiane, sens des groupes et modèles exportés

Expérience exécutée le 10 octobre 2026 sur `task/salh-supervised-training`.
Code autonome et sorties : [notebook 05](../notebooks/05_random_kfold.ipynb).
Décisions : [specification](../specs/spec.md). Exports locaux ignorés par Git :
`data/processed/experiments/salh_random_kfold_v1/` et
`models/salh_random_kfold_v1/`.

## Ce que le choix 16/médiane signifie

La configuration de travail demandée est adoptée pour **ce benchmark et les
contrôles supervisés de la future semi-supervision**. Le diagnostic précédent
étaye surtout l'ajout Ni/Cr/Mo pour YS/UTS et la stabilité de la médiane ; les
gains groupés d'allongement et Charpy sont moins établis. Ce choix ajoute trois
colonnes, aucune observation. Il ne choisit pas automatiquement une famille de
modèle : les familles et hyperparamètres sont comparés séparément par cible.

Les 1 555 lignes strict13/44 séries sont conservées. YS=706, UTS=677,
allongement=631, Charpy=861. Ni/Cr/Mo restent absents sur environ 59/53/53 % de
la cohorte ; leur absence ne déclenche pas une exclusion supplémentaire.
L'imputation n'est pas une nouvelle mesure physique.

Entrées numériques : C/Si/Mn/S/P/Ni/Cr/Mo en % massique, O/N en ppm, courant en A,
tension en V, apport thermique en kJ/mm, température entre passes et PWHT en °C,
durée PWHT en h. Ajouter le procédé catégoriel ; pour Charpy, ajouter la température
d'essai connue en °C et prédire l'énergie en J. Trois régressions traction
prédisent respectivement MPa, MPa et points de %. Autres propriétés mécaniques,
dureté, FATT50, microstructure, IDs et groupes sont exclus de X.

## Méthode annoncée avant les entraînements

1. Inspecter les séries, conditions répétées et courbes confirmées par les sources.
2. Comparer trois découpages avec une RF identique et sans tuning.
3. Réaliser un benchmark aléatoire imbriqué, choisir famille et paramètres dans
   la validation interne et conserver une prédiction externe par label.
4. Exporter les pipelines externes ; régler puis réentraîner les cinq familles
   sur tous les labels pour l'inférence, avec un index du choix par cible.
5. Vérifier rechargement, hashes et frontières d'accès aux pools inductifs.

KFold externe 5, shuffle, seed42, par cible sur les raw IDs triés. KFold interne
3, shuffle, seed43+pli externe. Optimiser **MAE**, pas le R² externe : un modèle
avec meilleure MAE peut avoir un R² plus faible. Le R² n'a pas de seuil garanti
de 0,5 ; il dépend aussi de la variance de y et de la population évaluée.
Écart-type des cinq scores ≠ intervalle de confiance ; R² moyen des plis ≠ R² OOF
sur les prédictions réunies. Les deux sont exportés.

Le benchmark reste rétrospectif : les choix d'entrées et d'imputation ont été
informés par 03/04 sur ces mêmes labels. Des partitions différentes ne créent
pas une nouvelle validation indépendante. Pour vérifier la généralisation à
une nouvelle étude, conserver le contrôle par séries ou obtenir de nouvelles
données. [Principes de validation scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html).

## Pipelines réellement entraînées

Dans **chaque train interne**, puis au refit externe : moyenne/écart-type calculés
sur les X observés → one-hot du procédé avec catégories du train → médiane du
train → projection des couples PWHT imputés sur des couples compatibles
réellement observés dans le train. Les cellules connues sont préservées ; une
colonne entièrement absente du train est refusée. La standardisation précède
l'imputation ; pour une transformation affine par colonne, la médiane se
transforme de la même façon. Aucun preprocessing global ajusté n'est réutilisé.
Les couples PWHT étant complets dans cette cohorte, leur garde ne modifie pas
les mesures observées. Aucune ACP ou sélection supervisée supplémentaire.

- Baseline : médiane de y du train, sans traitement X.
- Ridge : alpha 0,01 / 0,1 / 1 / 10 / 100 / 1000.
- SVR RBF : C 1 / 10 / 100 ; gamma scale / 0,05 ; epsilon 0,05 / 0,2.
  Son y est standardisé dans le train et les prédictions reviennent à l'unité
  physique par TransformedTargetRegressor.
- RF : 300 arbres, seed42 ; feuille 1 / 2 / 5, profondeur libre / 10,
  max_features 0,5 / 1. Un worker par forêt.
- kNN : poids uniformes, k 3 / 5 / 9 / 15, distance L1 / L2.

39 configurations par cible/pli, cinq familles incluant baseline. Trois workers
de recherche, backend threading ; cache limité aux transformations du train
identifiées par données et paramètres. Le cache est détaché lors de l'export.

## Les groupes ont-ils une signification ?

Un groupe actuel est une série inférée de l'identifiant et éventuellement reliée
par des alias dupliqués, pas un identifiant d'éprouvette certifié. La plupart
regroupent plusieurs conditions de soudage : les assimiler à une seule soudure
serait faux. L'audit quantifie cette diversité :

| target | series | distinct_conditions | repeated_condition_rows | multi_condition_series |
| --- | --- | --- | --- | --- |
| charpy_J | 24 | 432 | 623 | 23 |
| elongation | 34 | 590 | 79 | 33 |
| uts | 39 | 631 | 86 | 36 |
| yield_strength | 40 | 661 | 84 | 37 |

Une « condition » est la signature exacte des 16 entrées + procédé **au sein
d'une série**, sans température d'essai. NaN est un marqueur explicite ; aucune
imputation ne crée la signature. Les signatures partielles peuvent fusionner
des soudures différentes dont des conditions non renseignées diffèrent : c'est
un proxy descriptif. Même une signature complète ne couvre pas tous les champs
du brut et ne certifie pas l'identité physique de la soudure.

Deux familles Charpy confirmées dans 04 représentent 32 compositions/conditions
et 174 points : 16 × 5 températures pour Svensson/Gretoft (80), 16 × 5 ou 6 pour
Evans stress-relief (94). Ce sont des essais différents de courbes de transition
apparentées, pas des lignes que l'on peut toutes déclarer indépendantes.
Sources et réserves de transcription : [audit détaillé](11_performance_diagnostics.md).

Association descriptive série/cible, fraction de SST portée par les différences
de moyennes entre séries, comparée à 999 permutations (seed42) :

| target | between_series_SST_fraction | permuted_mean | permuted_95pct | permutation_association_p |
| --- | --- | --- | --- | --- |
| yield_strength | 0.480 | 0.055 | 0.076 | 0.001 |
| uts | 0.549 | 0.057 | 0.082 | 0.001 |
| elongation | 0.544 | 0.052 | 0.073 | 0.001 |
| charpy_J | 0.291 | 0.027 | 0.040 | 0.001 |

Cette association peut refléter la chimie et les conditions X déjà observées,
des protocoles ou d'autres différences ; elle ne démontre pas une dépendance
résiduelle ni un effet causal de la série. Le p de permutation est un indicateur
exploratoire ; les répétitions limitent l'échangeabilité. Aucun de ces calculs
ne certifie IID, et le score aléatoire élevé ne le fait pas non plus.

Recouvrement moyen réellement observé dans les validations aléatoires :

| target | shared_series | shared_condition | same_test_X |
| --- | --- | --- | --- |
| charpy_J | 1.000 | 0.650 | 0.038 |
| elongation | 0.998 | 0.106 | 0.106 |
| uts | 0.999 | 0.106 | 0.106 |
| yield_strength | 0.990 | 0.102 | 0.102 |

Les proportions sont entre 0 et 1. Pour Charpy, `shared_condition` peut avoir une
température différente ; `same_test_X` inclut sa température. Les répétitions de X
ne signifient pas nécessairement des doublons complets : les labels peuvent différer.

## Contrôle : mêmes features, médiane et RF sous trois découpages

RF300, feuille2, profondeur libre, max_features1, seed42, aucun tuning. Changer
uniquement les partitions et réapprendre le preprocessing à chaque train :

| target | protocol | MAE_mean | R2_mean | R2_sd | shared_series_fraction |
| --- | --- | --- | --- | --- | --- |
| charpy_J | condition_proxy | 19.937 | 0.643 | 0.097 | 0.984 |
| charpy_J | inferred_series | 33.134 | 0.074 | 0.290 | 0.000 |
| charpy_J | random_rows | 17.129 | 0.769 | 0.044 | 1.000 |
| elongation | condition_proxy | 1.996 | 0.680 | 0.023 | 0.998 |
| elongation | inferred_series | 3.387 | 0.175 | 0.202 | 0.000 |
| elongation | random_rows | 2.108 | 0.644 | 0.058 | 0.998 |
| uts | condition_proxy | 27.986 | 0.797 | 0.083 | 0.988 |
| uts | inferred_series | 49.558 | 0.370 | 0.203 | 0.000 |
| uts | random_rows | 28.409 | 0.786 | 0.042 | 0.999 |
| yield_strength | condition_proxy | 34.243 | 0.722 | 0.024 | 0.989 |
| yield_strength | inferred_series | 56.158 | 0.318 | 0.133 | 0.000 |
| yield_strength | random_rows | 33.197 | 0.739 | 0.066 | 0.990 |

`random_rows` : lignes aléatoires ; `condition_proxy` : GroupKFold5 sur les
signatures de conditions ci-dessus ; `inferred_series` : plis par séries du
notebook 02. Ces trois scénarios utilisent les mêmes labels, mais leurs folds
et distributions de validation diffèrent.

Pour la traction, séparer les signatures répétées ne reproduit pas la chute
observée quand on exclut des séries entières. Le transfert entre séries est
donc une difficulté plus large que les quelques signatures exactement répétées.
Pour Charpy, séparer ces conditions diminue la performance, tout en gardant des
séries partagées ; exclure des séries est encore nettement plus difficile.
Le proxy ne résout pas la vérification des identités physiques ou des protocoles.

**Conclusion pratique** : présenter KFold lignes comme scénario d'interpolation
dans la population couverte par la base, et KFold séries comme stress-test de
transfert. Le choix du protocole principal dépend de la future utilisation
(séries connues ou étude/soudure nouvelle), pas du protocole qui affiche le plus
grand R². Les groupes inférés restent imparfaits et peuvent être larges ; les
répétitions confirmées empêchent toutefois de supposer IID pour toute la base.

## Benchmark aléatoire imbriqué complet

100 évaluations cible/famille/pli ; 780 configurations internes enregistrées.
Une sélection de famille et paramètres sur la seule MAE interne est évaluée
sur chacun des 20 plis cible/validation. Ses scores sont :

| target | MAE_mean | MAE_sd | R2_mean | R2_sd | OOF_R2 |
| --- | --- | --- | --- | --- | --- |
| charpy_J | 16.461 | 1.161 | 0.776 | 0.062 | 0.782 |
| elongation | 2.054 | 0.239 | 0.660 | 0.058 | 0.658 |
| uts | 23.861 | 0.906 | 0.836 | 0.027 | 0.837 |
| yield_strength | 31.630 | 4.114 | 0.755 | 0.063 | 0.752 |

Toutes les familles, présentées descriptivement sans choisir sur les scores
externes :

| target | model | MAE_mean | MAE_sd | R2_mean | R2_sd | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- |
| charpy_J | inner_selected | 16.461 | 1.161 | 0.776 | 0.062 | 0.782 |
| charpy_J | knn | 19.253 | 1.518 | 0.651 | 0.055 | 0.656 |
| charpy_J | median_y | 36.756 | 2.813 | -0.069 | 0.037 | -0.063 |
| charpy_J | random_forest | 16.099 | 1.027 | 0.795 | 0.035 | 0.798 |
| charpy_J | ridge | 26.913 | 0.587 | 0.529 | 0.113 | 0.541 |
| charpy_J | svr_rbf | 17.393 | 0.988 | 0.749 | 0.043 | 0.752 |
| elongation | inner_selected | 2.054 | 0.239 | 0.660 | 0.058 | 0.658 |
| elongation | knn | 2.423 | 0.260 | 0.530 | 0.117 | 0.535 |
| elongation | median_y | 4.019 | 0.149 | -0.015 | 0.019 | -0.012 |
| elongation | random_forest | 2.054 | 0.239 | 0.660 | 0.058 | 0.658 |
| elongation | ridge | 3.011 | 0.152 | 0.345 | 0.119 | 0.350 |
| elongation | svr_rbf | 2.268 | 0.198 | 0.556 | 0.094 | 0.557 |
| uts | inner_selected | 23.861 | 0.906 | 0.836 | 0.027 | 0.837 |
| uts | knn | 33.452 | 4.870 | 0.697 | 0.098 | 0.697 |
| uts | median_y | 68.879 | 4.438 | -0.050 | 0.019 | -0.049 |
| uts | random_forest | 26.906 | 1.907 | 0.805 | 0.045 | 0.806 |
| uts | ridge | 44.319 | 3.535 | 0.538 | 0.118 | 0.543 |
| uts | svr_rbf | 23.861 | 0.906 | 0.836 | 0.027 | 0.837 |
| yield_strength | inner_selected | 31.630 | 4.114 | 0.755 | 0.063 | 0.752 |
| yield_strength | knn | 38.144 | 2.497 | 0.619 | 0.059 | 0.622 |
| yield_strength | median_y | 70.032 | 4.087 | -0.031 | 0.040 | -0.022 |
| yield_strength | random_forest | 31.242 | 4.038 | 0.765 | 0.064 | 0.763 |
| yield_strength | ridge | 54.047 | 3.440 | 0.412 | 0.053 | 0.418 |
| yield_strength | svr_rbf | 31.747 | 3.900 | 0.754 | 0.046 | 0.751 |

Familles retenues dans les trains externes :

| target | outer_fold | selected_family | inner_MAE | MAE | R2 | best_params |
| --- | --- | --- | --- | --- | --- | --- |
| yield_strength | 0 | svr_rbf | 37.001 | 28.267 | 0.769 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| yield_strength | 1 | random_forest | 35.868 | 29.257 | 0.817 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| yield_strength | 2 | random_forest | 33.883 | 35.668 | 0.671 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| yield_strength | 3 | svr_rbf | 36.421 | 28.418 | 0.807 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": "scale"} |
| yield_strength | 4 | svr_rbf | 33.199 | 36.541 | 0.710 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": "scale"} |
| uts | 0 | svr_rbf | 26.652 | 25.408 | 0.814 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| uts | 1 | svr_rbf | 27.367 | 23.845 | 0.819 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": "scale"} |
| uts | 2 | svr_rbf | 26.237 | 23.590 | 0.859 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| uts | 3 | svr_rbf | 27.580 | 23.332 | 0.816 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| uts | 4 | svr_rbf | 27.733 | 23.130 | 0.871 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| elongation | 0 | random_forest | 2.243 | 1.857 | 0.680 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |
| elongation | 1 | random_forest | 2.189 | 1.838 | 0.728 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| elongation | 2 | random_forest | 2.174 | 2.138 | 0.651 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| elongation | 3 | random_forest | 2.243 | 2.017 | 0.673 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| elongation | 4 | random_forest | 2.141 | 2.421 | 0.569 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |
| charpy_J | 0 | random_forest | 18.068 | 14.921 | 0.849 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |
| charpy_J | 1 | random_forest | 17.609 | 15.619 | 0.806 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| charpy_J | 2 | svr_rbf | 18.401 | 17.510 | 0.683 | {"model__regressor__C": 100, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| charpy_J | 3 | random_forest | 18.295 | 17.529 | 0.756 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |
| charpy_J | 4 | random_forest | 18.072 | 16.726 | 0.784 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |

Comparaison à features/imputation identiques avec 04 ; les réglages internes
suivent leur protocole respectif. Une comparaison RF fixe est donnée plus haut
pour isoler le découpage sans différence de tuning.

| target | model | MAE_mean_random | MAE_mean_group | R2_mean_random | R2_mean_group |
| --- | --- | --- | --- | --- | --- |
| charpy_J | knn | 19.253 | 35.725 | 0.651 | -0.099 |
| charpy_J | random_forest | 16.099 | 33.033 | 0.795 | 0.138 |
| charpy_J | ridge | 26.913 | 34.752 | 0.529 | 0.069 |
| charpy_J | svr_rbf | 17.393 | 35.963 | 0.749 | 0.091 |
| elongation | knn | 2.423 | 3.983 | 0.530 | -0.060 |
| elongation | random_forest | 2.054 | 3.339 | 0.660 | 0.226 |
| elongation | ridge | 3.011 | 3.658 | 0.345 | 0.016 |
| elongation | svr_rbf | 2.268 | 3.670 | 0.556 | 0.106 |
| uts | knn | 33.452 | 68.538 | 0.697 | -0.115 |
| uts | random_forest | 26.906 | 48.905 | 0.805 | 0.394 |
| uts | ridge | 44.319 | 61.898 | 0.538 | 0.179 |
| uts | svr_rbf | 23.861 | 52.861 | 0.836 | 0.316 |
| yield_strength | knn | 38.144 | 73.496 | 0.619 | -0.140 |
| yield_strength | random_forest | 31.242 | 54.139 | 0.765 | 0.390 |
| yield_strength | ridge | 54.047 | 69.387 | 0.412 | -0.025 |
| yield_strength | svr_rbf | 31.747 | 59.350 | 0.754 | 0.264 |

Le gain aléatoire étaye l'aide apportée par les séries déjà représentées ; il ne
montre pas que le GroupKFold dégrade artificiellement un modèle approprié à de
nouvelles séries. Les scores Charpy restent exploratoires : 21 séries/656 lignes
non résolues par publication originale dans 04, et règles d'échantillonnage
E(T)/T100 encore hétérogènes. Une bonne interpolation de ces points ne suffit
pas à prédire une courbe complète d'un nouvel acier à n'importe quelle température.

## Modèles sauvegardés et choix final

40 pipelines locales complètes, prétraitement inclus : 20 modèles de trains
externes sélectionnés en interne (`outer_selected/`) et 20 refits sur tous les
labels (`full_fit/`, cinq familles × quatre cibles). Les premières reproduisent
l'OOF ; les secondes servent à l'inférence. Les 20 refits ont tous des paramètres
réglés par CV5 aléatoire **seed1042** ; l'index choisit, par cible, la plus petite
MAE de cette CV. Cette MAE de choix final est optimiste comme estimation d'une
performance externe et **ne remplace pas** l'évaluation imbriquée ci-dessus.

| target | family | selection_CV_MAE | best_params | path |
| --- | --- | --- | --- | --- |
| yield_strength | svr_rbf | 31.228 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": "scale"} | models/salh_random_kfold_v1/full_fit/yield_strength_svr_rbf.pkl |
| uts | svr_rbf | 24.060 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} | models/salh_random_kfold_v1/full_fit/uts_svr_rbf.pkl |
| elongation | random_forest | 1.940 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} | models/salh_random_kfold_v1/full_fit/elongation_random_forest.pkl |
| charpy_J | random_forest | 15.387 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} | models/salh_random_kfold_v1/full_fit/charpy_J_random_forest.pkl |

Tous les exports ont un round-trip de prédiction ; les quatre retenus ont été
rechargés par le notebook dans des processus Python neufs, sans exécuter ses
définitions. Le contrôle indépendant recharge en plus les 40 fichiers et
reproduit toutes les prédictions des 20 modèles externes. Les sidecars `.json`
enregistrent features/unités, IDs du train, paramètres, versions et SHA-256.
Index : `models/salh_random_kfold_v1/selected_models.json`.
Mode d'emploi : [models/README.md](../models/README.md).
[Persistance scikit-learn](https://scikit-learn.org/stable/model_persistence.html).

## Passage au semi-supervisé

| target | labels | unlabeled_X_available | semi_supervised_status |
| --- | --- | --- | --- |
| yield_strength | 706 | 849 | inductive_pool_ready_algorithm_not_implemented |
| uts | 677 | 878 | inductive_pool_ready_algorithm_not_implemented |
| elongation | 631 | 924 | inductive_pool_ready_algorithm_not_implemented |
| charpy_J | 861 | 0 | no_pool_with_known_test_temperature |

Les nombres de candidats concernent toute la cohorte, pas un train unique ni
nécessairement autant de conditions indépendantes. Les répétitions devront
être prises en compte dans la sélection et la pondération des pseudo-labels.
Les lignes sans la cible ont cinq blocs équilibrés seed142, puis trois blocs
internes seed1042+pli externe. Pendant un pli, **uniquement** les X sans label
affectés au train courant sont autorisés ; ni les X ni les labels de validation
interne/externe ne font partie du pool. Les règles sont exportées dans
`random_fold_assignments.csv` et les tailles dans `semi_supervised_access_counts.csv`.
Le scénario est inductif, avec séries partagées permises mais lignes séparées.

Charpy : toutes les lignes avec température renseignée ont déjà une énergie.
Une ligne sans énergie et sans température n'est pas un exemple X pour E(T).
Il faut de nouvelles mesures sans énergie **avec température prévue connue**
pour une expérience semi-supervisée Charpy ; ne pas fabriquer cette condition.

Pour l'étape suivante, définir COREG (ses deux vues/régresseurs et distances),
les budgets de labels et pseudo-labels, les paramètres réglés dans les plis
internes, le maximum d'itérations et les critères d'arrêt. Comparer au contrôle
supervisé correspondant sur **exactement les mêmes train labels, features,
prétraitement et validations**, pour isoler la contribution des pseudo-labels.
Si les statistiques de preprocessing utilisent aussi le pool X train, le
documenter et fournir le contrôle correspondant ; le benchmark présent apprend
son preprocessing sur les seuls labels du train. Aucun score semi-supervisé
n'est inventé et aucun COREG n'est exécuté ici, conformément à son report.

**Ne pas réutiliser les refits sur tous les labels pour l'évaluation semi-supervisée** :
ils ont déjà vu les futurs labels de validation. Reconstruire chaque train de pli.
Garder aussi le contrôle par séries pour étudier si le gain transfère aux groupes
absents du train. La semi-supervision n'est pas assurée d'améliorer le score.

## Reproduction et vérification

Exécuter 01 → 02 → 03 → 04 → 05 avec l'environnement de `requirements.txt`.
Les sorties du notebook 05 proviennent d'une exécution Jupyter complète ; les
versions sont dans son manifeste :

| python | sklearn | numpy | pandas | joblib | cloudpickle |
| --- | --- | --- | --- | --- | --- |
| 3.14.8 | 1.9.1 | 2.5.3 | 3.0.6 | 1.6.0 | 3.1.2 |

30 tests ciblés passent, dont cinq nouveaux sur les frontières inductives,
reproductibilité, température Charpy obligatoire, apprentissage des médianes
dans les trains et persistance. L'audit indépendant confirme couverture OOF
exacte, 100 métriques recalculées, 780 choix/candidats internes, 20 choix de
famille internes, 60 contrôles de découpages, 156 candidats de refit final,
40 rechargements et hashes des inputs/exports/brut/source du notebook.
Le brut, la préparation et les expériences précédentes restent préservés.
Les artefacts dérivés et modèles restent ignorés par Git.
