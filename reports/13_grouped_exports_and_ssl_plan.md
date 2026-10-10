# Exports des deux protocoles et cadrage semi-supervisé

Complément exécuté le 10 octobre 2026 sur `task/salh-supervised-training`.
Le cadrage ci-dessous décrit cette étape ; COREG est désormais implémenté et
évalué séparément dans [le rapport 14](14_coreg_training.md).
Code autonome : [06_grouped_exports.ipynb](../notebooks/06_grouped_exports.ipynb).
Configuration : 16 entrées numériques + procédé, médiane ; Charpy ajoute la
température connue. Les historiques 13/itérative du notebook 03 restent conservés.

## Exports disponibles

| Protocole | Dossier local ignoré par Git | Modèles de trains externes | Refits complets |
| --- | --- | --- | --- |
| KFold aléatoire | `models/salh_random_kfold_v1/` | 20 | 20 |
| Validation par groupes | `models/salh_group_kfold_v1/` | 20 | 20 |

80 pipelines complètes au total, avec prétraitement appris, sidecars JSON et
index `selected_models.json` propres à chaque protocole. Chaque train externe
conserve la famille choisie par sa MAE interne, pas les cinq familles de chaque
pli. Chaque protocole conserve aussi les cinq familles réentraînées sur tous les
labels, soit 20 refits. [Chargement et portée](../models/README.md).

KFold et GroupKFold définissent la validation et le tuning. Les refits complets
utilisent les mêmes labels, mais leurs hyperparamètres ou familles peuvent
différer selon le protocole. Ils servent à l'inférence ; ils ont vu les labels
des validations et ne peuvent donc initialiser une nouvelle évaluation de plis.

## Vérification des modèles groupés

Le notebook 06 vérifie les hashes de préparation et diagnostic, reprend les
paramètres déjà sélectionnés dans les plis internes groupés du notebook 04 pour
16/médiane et réajuste les modèles sur leurs trains externes. Il reproduit les
**80 évaluations et 11 500 prédictions OOF** des quatre familles, toutes vérifiées
à tolérance 1e-8. La baseline médiane est aussi évaluée avec ces mêmes plis,
puis le minimum de MAE interne sélectionne chaque export de train externe.

Cette sélection fixe le schéma 16/médiane et ajoute la baseline ; elle est
distincte de la sélection conjointe schéma/imputer du diagnostic. Elle ne
constitue pas une nouvelle validation indépendante du choix 16/médiane.

Scores moyens des cinq plis de cette sélection par groupes :

| Cible | MAE moyenne | R² moyen |
| --- | --- | --- |
| Limite d'élasticité | 56,757 MPa | 0,337 |
| UTS | 54,344 MPa | 0,334 |
| Allongement | 3,517 points de % | 0,157 |
| Charpy, exploratoire | 35,752 J | 0,075 |

Pour les refits complets, une CV GroupKFold5 sur les séries des labels règle
chaque famille ; aucune validation externe ne décide du choix final. Ces MAE
sont des scores de **sélection**, pas un nouveau test indépendant :

| Cible | Famille retenue | MAE CV de sélection | Paramètres |
| --- | --- | --- | --- |
| Limite d'élasticité | RF300 | 58,695 MPa | feuille2, profondeur libre, max_features0,5, seed42 |
| UTS | SVR RBF | 46,555 MPa | C10, gamma0,05, epsilon0,05 ; y standardisé dans le train |
| Allongement | RF300 | 3,282 points de % | feuille1, profondeur libre, max_features0,5, seed42 |
| Charpy | RF300 | 32,375 J | feuille1, profondeur10, max_features0,5, seed42 |

Les 40 pipelines groupées ont été rechargées dans un processus indépendant,
sans exécution des définitions du notebook ; les 20 modèles externes reproduisent
toutes leurs prédictions sélectionnées OOF. L'audit indépendant vérifie hashes,
100 métriques recalculées, sélection interne, IDs/groupes séparés et choix des
refits. 32 tests rapides passent, dont deux nouveaux sur les frontières du pool
groupé et les groupes disjoints de la CV de refit. L'exécution complète du
notebook 06 prend environ deux minutes dans l'environnement enregistré.

Exports reproductibles sous `data/processed/experiments/salh_group_kfold_v1/` :
`outer_metrics.csv`, `outer_predictions.csv`, `inner_selected_*`,
`selected_metrics_summary.csv`, `full_refit_*`, `selected_final_models.csv`,
`model_artifacts.csv`, `fresh_reload_checks.csv`, les probes et
`grouped_semi_supervised_access_counts.csv`. Le manifeste conserve les hashes,
versions, grilles, paramètres du protocole et identités des sources.

## Ce qui reste à définir avant l'entraînement semi-supervisé

Les cibles, la configuration 16/médiane et les partitions sont définies.
Les pools naturels traction ont 849/878/924 candidats dans toute la cohorte,
limités au train courant. Les X et labels de validation restent hors du pool
en protocole inductif. En validation groupée, les groupes de ces X sont eux
aussi séparés ; en validation aléatoire, les séries peuvent être partagées.

Pour COREG, préciser les deux kNN et leurs distances, le nombre de voisins,
les budgets de vrais labels et de candidats, la règle de confiance/acceptation,
le traitement des entrées répétées, les limites et critères d'arrêt, puis les
contrôles supervisés sur les mêmes données. La proposition détaillée est
consignée dans [specs/spec.md](../specs/spec.md), section « Choix encore
nécessaires pour COREG ». Elle propose L1/L2, k3/5/9/15, au plus 100 candidats
par tour et au plus 100 tours, sans revendiquer leur optimalité.

Le preprocessing serait appris sur les vrais labels du train et figé pendant
la boucle, pour isoler les pseudo-labels. La comparaison clé est la moyenne
des mêmes deux kNN **sans pseudo-labels**, en plus des kNN simples et des meilleurs
supervisés du protocole. Les SVR/RF exportés restent des références, tandis que
COREG requiert son propre apprentissage dans chaque train de pli.

Le pool naturel Charpy avec température connue est vide. Une simulation masquant
des labels du train uniquement peut étudier la méthode, mais ne constitue pas
un pool naturel et reste à définir séparément. Les protocoles Charpy demeurent
partiellement vérifiés. Aucun COREG n'a été entraîné dans ce complément.

Source algorithmique : [Zhou et Li, IJCAI 2005](https://www.ijcai.org/Proceedings/05/Papers/0689.pdf).
