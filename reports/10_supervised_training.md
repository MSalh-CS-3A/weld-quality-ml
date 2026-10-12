# Entraînements supervisés — 10 octobre 2026

> Actualisation du 12 octobre 2026 : XGBoost est ajouté aux benchmarks
> 16/médiane dans le [rapport 17](17_xgboost_training.md). Les chiffres de
> l’exécution du 10 octobre ci-dessous restent historiques, sauf mention explicite.

Le notebook [03_modeling](../notebooks/03_modeling.ipynb) contient et exécute
les pipelines de quatre régressions indépendantes. La branche de travail
`task/salh-supervised-training` a été créée depuis `task/1-eda-salh` à la demande
de l’utilisateur. Les familles ont été confirmées comme vues en cours ; COREG
est différé. Le protocole scientifique actif reste dans [specs/spec.md](../specs/spec.md).

## Population et entrées

1 652 lignes brutes, quatre alias exclus des expériences, 1 648 observations
dédupliquées ; cohorte A1_13 de 1 555 lignes/44 groupes, avec au plus deux
entrées numériques absentes. Le master conserve les NaN. 607 lignes de la
cohorte ont au moins une absence parmi les treize entrées, soit 1 075 cellules.
Une absence de cible n’est jamais imputée. Seules 141 lignes renseignent toutes
les quatre sorties, contre 609 pour les trois propriétés de traction.

| Cible | Unité | Labels éligibles | Groupes | Médiane | Min–max |
| --- | --- | ---: | ---: | ---: | --- |
| Limite d’élasticité | MPa | 706 | 40 | 496,00 | 315,00–920,00 |
| UTS | MPa | 677 | 39 | 576,00 | 447,00–1151,00 |
| Allongement | points de % | 631 | 34 | 26,60 | 10,60–36,40 |
| Charpy — exploratoire | J | 861 | 24 | 100,00 | 3,00–270,00 |

Entrées communes : C/Si/Mn/S/P (% massique), O/N (ppm), courant (A), tension
(V), apport thermique (kJ/mm), température entre passes (°C), température et
durée PWHT (°C, h), plus procédé catégoriel. Charpy ajoute uniquement la
température d’essai `charpy_temp_C` (°C), connue pour les 861 couples éligibles.
Les autres propriétés mécaniques, dureté/FATT50, microstructure, identifiants,
flags, groupes et numéros de plis ne sont pas des entrées.

**Charpy reste exploratoire.** Le benchmark prédit l’énergie rapportée à partir
des couples E(T) définis par la documentation d’origine. Il ne certifie pas que
toutes ces énergies sont des mesures directes sous un protocole homogène.
Des séries à énergie constante peuvent correspondre à des critères fixés ;
aucun seuil 28/100 J ne sert à reclasser ou exclure automatiquement les lignes.
Le tableau de signatures sert seulement au diagnostic. L’audit des sources
précédera toute conclusion sur une tâche Charpy homogène ou son utilisation.
Le choix température en entrée/énergie en sortie est illustré par un travail
primaire de [Bhadeshia, MacKay et Svensson, 1995, pp. 3–5](https://www.phase-trans.msm.cam.ac.uk/abstracts/toughness.pdf),
qui ne valide pas toutes les séries du master.

## Validation et pipelines

Cinq plis externes GroupKFold sans mélange, identiques entre familles et
restreints aux labels de chaque cible ; trois plis internes par groupes dans
chaque train externe, issus du fichier de plis exporté par la préparation.
Les groupes sont des séries inférées des identifiants et liées par les doublons,
pas des publications confirmées. Aucun groupe interne/externe n’est partagé
entre un train et sa validation. La graine des estimateurs est 42.

Pour chaque configuration, ajuster toute la pipeline sur le train interne,
transformer sa validation sans refit et sélectionner la MAE interne moyenne
non pondérée. Réajuster ensuite sur tout le train externe étiqueté et prédire
les groupes externes. Ni les labels ni les features externes ne participent
au fit. Aucun pool non étiqueté ni pseudo-label n’est utilisé.

Preprocessing commun : standardisation numérique (moyenne/écart-type du train),
one-hot du procédé appris sur le train (inconnu → vecteur nul), imputation
itérative BayesianRidge (init médiane, 100 itérations maximum, tol=1e-3, seed 42),
puis projection d’un PWHT manquant sur un couple réel compatible du train.
Non-convergence, colonne entièrement absente ou PWHT incompatible → erreur.
Les valeurs observées sont préservées dans leur unité originale.

| Modèle | Étapes propres | Grille interne |
| --- | --- | --- |
| Médiane de y | Aucun preprocessing X ; médiane de y du train | Une configuration |
| Ridge | Régression linéaire L2, y dans son unité | alpha=0,01/0,1/1/10/100/1 000 |
| SVR RBF | StandardScaler de y du train, SVR, inversion de y | C=1/10/100 ; gamma=scale/0,05 ; epsilon=0,05/0,2 |
| Random Forest | 300 arbres, seed 42, y dans son unité | leaf=1/2/5 ; depth=None/10 ; max_features=0,5/1 |
| kNN | Voisins uniformes sur X standardisé/encodé | k=3/5/9/15 ; p=1/2 |

Aucune ACP ni sélection automatique de variables. A0_11/A1b_16 restent des
sensibilités différées. Le cache ne réutilise un fit que pour le même train
X/y et les mêmes paramètres ; il ne remplace pas les fits locaux aux plis.

## Scores externes

Moyennes **non pondérées des cinq plis**, accompagnées de leurs écarts-types
empiriques (pas des intervalles de confiance). MAE/RMSE dans l’unité de la cible,
R² sans unité. Les scores OOF, distincts de ces moyennes par pli, sont également
exportés dans `metrics_summary.csv`. Chaque ID éligible possède exactement une
prédiction externe par famille pour sa cible.

| Cible | Modèle | MAE ± écart-type | RMSE ± écart-type | R² moyen ± écart-type |
| --- | --- | ---: | ---: | ---: |
| Limite d’élasticité | Médiane de y | 70,45 ± 10,68 | 92,50 ± 13,10 | -0,073 ± 0,052 |
| Limite d’élasticité | Ridge | 69,92 ± 5,17 | 90,88 ± 8,09 | -0,054 ± 0,152 |
| Limite d’élasticité | SVR RBF | 69,28 ± 12,81 | 89,26 ± 15,98 | 0,004 ± 0,129 |
| Limite d’élasticité | Random Forest | 65,88 ± 10,61 | 85,65 ± 15,05 | 0,079 ± 0,146 |
| Limite d’élasticité | kNN | 76,87 ± 15,75 | 98,68 ± 21,15 | -0,208 ± 0,198 |
| UTS | Médiane de y | 72,66 ± 15,24 | 93,73 ± 22,73 | -0,180 ± 0,114 |
| UTS | Ridge | 65,88 ± 15,14 | 82,99 ± 20,54 | 0,054 ± 0,259 |
| UTS | SVR RBF | 63,40 ± 12,70 | 83,43 ± 16,79 | 0,039 ± 0,180 |
| UTS | Random Forest | 57,65 ± 10,78 | 76,25 ± 14,95 | 0,194 ± 0,154 |
| UTS | kNN | 66,65 ± 16,00 | 88,66 ± 19,19 | -0,089 ± 0,264 |
| Allongement | Médiane de y | 4,09 ± 0,31 | 4,96 ± 0,42 | -0,062 ± 0,047 |
| Allongement | Ridge | 3,73 ± 0,31 | 4,57 ± 0,46 | 0,094 ± 0,119 |
| Allongement | SVR RBF | 3,88 ± 0,39 | 4,82 ± 0,55 | -0,007 ± 0,142 |
| Allongement | Random Forest | 3,56 ± 0,18 | 4,49 ± 0,22 | 0,125 ± 0,082 |
| Allongement | kNN | 3,91 ± 0,25 | 5,02 ± 0,45 | -0,093 ± 0,146 |
| Charpy — exploratoire | Médiane de y | 36,04 ± 16,91 | 50,60 ± 11,68 | -0,149 ± 0,251 |
| Charpy — exploratoire | Ridge | 35,74 ± 12,87 | 45,84 ± 11,48 | 0,072 ± 0,132 |
| Charpy — exploratoire | SVR RBF | 36,14 ± 8,51 | 46,12 ± 8,60 | 0,035 ± 0,188 |
| Charpy — exploratoire | Random Forest | 34,71 ± 12,36 | 46,53 ± 11,14 | 0,017 ± 0,306 |
| Charpy — exploratoire | kNN | 34,92 ± 13,12 | 49,36 ± 9,64 | -0,139 ± 0,400 |

## Lecture des résultats

- Limite d’élasticité : la plus faible MAE moyenne observée est celle de Random Forest (65,88 MPa), contre 70,45 pour la constante médiane. Son R² moyen est 0,079.
- UTS : la plus faible MAE moyenne observée est celle de Random Forest (57,65 MPa), contre 72,66 pour la constante médiane. Son R² moyen est 0,194.
- Allongement : la plus faible MAE moyenne observée est celle de Random Forest (3,56 points de %), contre 4,09 pour la constante médiane. Son R² moyen est 0,125.
- Charpy — exploratoire : la plus faible MAE moyenne observée est celle de Random Forest (34,71 J), contre 36,04 pour la constante médiane. Son R² moyen est 0,017.

Ce classement décrit les évaluations des familles ; il ne sélectionne pas un
modèle de production avec une estimation indépendante de cette sélection.
Un choix de famille optimisé doit lui aussi être effectué dans les plis internes.
Les R² de plis, leur dispersion et les erreurs du train sont conservés afin
de discuter la généralisation aux groupes tenus à l’écart. Une corrélation entre
sorties ou une bonne erreur sur les couples rapportés ne démontre pas un effet
causal ou une recommandation de paramètres de soudage.

## Exécution et vérification

Les 20 cellules du notebook ont été exécutées avec un noyau Jupyter de l’environnement local, de haut en bas. La boucle de recherche/refit a duré 5,98 minutes sur cet environnement (durée calcul, pas un temps de travail du binôme). 100 évaluations externes, 780 configurations internes et 2 440 fits d’estimateurs ont terminé.

Les 80 fits de contrôle de preprocessing ont convergé :

| Cible | Itérations min–max, trains internes et externes |
| --- | ---: |
| Limite d’élasticité | 3–9 |
| UTS | 3–13 |
| Allongement | 4–14 |
| Charpy — exploratoire | 3–20 |

Les valeurs observées sont préservées après transformation et inversion
d’échelle ; les tests ciblés vérifient les fits internes, le refit externe,
l’échelle de y de SVR, les groupes et l’éligibilité par cible. La suite hors
ligne comprend 20 tests. Les hashes du brut et des huit exports de préparation
sont inchangés. `sujet.md` est préservé.

Les résultats complets, hashes, versions, grilles, unités et seeds sont dans
`data/processed/experiments/salh_supervised_v1/`, ignoré par Git. Les pipelines
externes sont accessibles dans `outer_models` après une exécution interactive ;
aucun modèle final de production n’est sérialisé. Aucune donnée générée ou
environnement local n’a été ajouté à Git.

Reproduction : ouvrir `notebooks/03_modeling.ipynb` avec les dépendances de
`requirements.txt` et les exports vérifiés de la préparation, puis exécuter
toutes les cellules. Vérifications rapides :

```bash
python -m unittest discover -s tests -v
```
