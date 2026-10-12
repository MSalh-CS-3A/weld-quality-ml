# COREG entraîné : validation aléatoire et par groupes

> Actualisation du 12 octobre 2026 : XGBoost est ajouté aux benchmarks
> 16/médiane dans le [rapport 17](17_xgboost_training.md). Les chiffres de
> l’exécution du 10 octobre ci-dessous restent historiques, sauf mention explicite.

Exécution réelle du 10 octobre 2026, branche `task/salh-supervised-training`.
Code autonome : [07_coreg.ipynb](../notebooks/07_coreg.ipynb).
Le protocole a été consigné dans [specs/spec.md](../specs/spec.md) avant le calcul.

## Données et pipeline

Cohorte strict13 inchangée : 1 555 lignes, 44 séries inférées ; 706 labels YS,
677 UTS et 631 allongement. Pools naturels globaux : 849, 878 et 924 lignes
respectivement. Un modèle séparé par cible. Charpy est conservé dans les benchmarks
supervisés précédents ; aucun entraînement semi-supervisé Charpy ici, car son pool
sans énergie avec température connue est vide. Aucun label artificiellement masqué.

16 variables numériques : C, Si, Mn, S, P, Ni, Cr, Mo (% massique), O/N (ppm),
courant (A), tension (V), apport thermique (kJ/mm), température interpasses et
PWHT (°C), durée PWHT (h), plus procédé catégoriel. Aucun autre résultat mécanique,
identifiant, groupe, dureté ou FATT50 dans X. Ni/Cr/Mo peuvent être manquants.

Chaque train réel ajuste ses moyennes/écarts-types numériques, ses catégories,
ses médianes et sa garde PWHT ; le pool et la validation sont transformés avec ces
statistiques figées. Les vrais labels répétés sont tous conservés. Le pool est
dédupliqué par représentation transformée exacte et débarrassé des représentations
déjà présentes dans le vrai train ; le raw ID minimal représente chaque entrée.
Cette variante évite de multiplier le poids de représentations identiques, sans
prouver que les observations correspondent physiquement à la même soudure.

## Algorithme et validation

Deux kNN uniformes, distances L1/L2, même k dans 3/5/9/15. COREG évalue le gain
local de SSE après ajout temporaire de sa propre estimation au régresseur source,
puis transmet le candidat accepté à l'autre régresseur. Le voisinage courant inclut
les pseudo-labels précédents. La sortie est la moyenne des deux prédictions.
Source : [Zhou et Li, IJCAI 2005](https://www.ijcai.org/Proceedings/05/Papers/0689.pdf).
L1/L2 et la déduplication sont des choix du projet, distincts des paramètres p2/p5
des expériences originales. Les égalités de distances utilisent un ordre stable
de positions initiales ; les contrôles utilisent exactement la même règle.

Au plus 100 candidats actifs et 100 tours. Gain strictement supérieur à
`1e-12 × max(1,var(y_train)) × k`. Au plus un candidat par source/tour, sans
réutilisation d'ID, échanges simultanés après les deux sélections. Arrêt si le pool
est épuisé, si aucun gain positif n'existe dans le pool actif, ou à 100 tours.
L'arrêt dans le pool actif n'exclut pas un candidat utile dans sa partie non examinée.

Les partitions des notebooks 02/05 sont reprises : cinq plis externes et trois
internes, séparément aléatoires et groupés. **Protocole inductif** : les X et labels
des validations interne et externe sont exclus de l'apprentissage et du pool.
Le groupé exclut leurs séries entières. k est choisi par MAE interne, séparément
pour COREG, moyenne kNN, L1 seul et L2 seul. Les données de validation servent
uniquement à scorer après fit. Les seeds effectives dérivent de la base 42, du
protocole, de la cible et du contexte ; les bases 43/44 sont une sensibilité à k fixé.

Le contrôle **même k** isole l'effet du pseudo-étiquetage. Le contrôle **kNN réglés**
choisit son propre k et compare deux procédures. La référence **supervisés** reprend
les OOF de la sélection interne parmi les cinq familles de 05/06 sur les mêmes IDs.
Elle n'initialise jamais COREG. Le contrôle avec la même représentation est requis :
une différence avec un RF/SVR ne mesure pas à elle seule l'effet du pool.

## Résultats réellement obtenus

Moyennes des cinq plis, MAE dans l'unité de la cible. Les statistiques OOF et
les écarts-types sont présentés séparément ci-dessous.

| CV | Cible | MAE COREG | R² COREG | MAE même k | R² même k | MAE kNN réglés | R² kNN réglés | MAE supervisés | R² supervisés |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random | Limite d’élasticité (MPa) | 37,919 | 0,629 | 38,241 | 0,625 | 38,241 | 0,625 | 31,630 | 0,755 |
| random | UTS (MPa) | 33,037 | 0,709 | 33,319 | 0,698 | 33,319 | 0,698 | 23,861 | 0,836 |
| random | Allongement (points de %) | 2,402 | 0,535 | 2,392 | 0,546 | 2,392 | 0,546 | 2,054 | 0,660 |
| grouped | Limite d’élasticité (MPa) | 71,074 | -0,056 | 70,817 | -0,055 | 71,717 | -0,080 | 56,757 | 0,337 |
| grouped | UTS (MPa) | 63,060 | 0,043 | 62,081 | 0,064 | 62,081 | 0,064 | 54,344 | 0,334 |
| grouped | Allongement (points de %) | 3,904 | -0,028 | 3,879 | -0,015 | 3,879 | -0,015 | 3,517 | 0,157 |

| CV | Cible | MAE moyenne ± SD | R² moyen ± SD | MAE OOF | R² OOF |
| --- | --- | --- | --- | --- | --- |
| random | Limite d’élasticité (MPa) | 37,919 ± 3,151 | 0,629 ± 0,060 | 37,913 | 0,631 |
| random | UTS (MPa) | 33,037 ± 4,905 | 0,709 ± 0,093 | 33,038 | 0,707 |
| random | Allongement (points de %) | 2,402 ± 0,258 | 0,535 ± 0,112 | 2,403 | 0,538 |
| grouped | Limite d’élasticité (MPa) | 71,074 ± 14,263 | -0,056 ± 0,181 | 71,780 | -0,051 |
| grouped | UTS (MPa) | 63,060 ± 15,175 | 0,043 ± 0,193 | 61,470 | 0,146 |
| grouped | Allongement (points de %) | 3,904 ± 0,311 | -0,028 ± 0,183 | 3,883 | 0,018 |

COREG est moins performant en MAE que la sélection supervisée dans les six
comparaisons cible/protocole. Les petits gains face au même k en aléatoire sont
de 0,322 MPa pour YS et 0,283 MPa pour UTS en OOF ; leurs intervalles couvrent
zéro. L'allongement ne progresse pas. En groupé, les trois gains face au même k
sont négatifs ; pour UTS, l'intervalle descriptif reste entièrement négatif.
Ces résultats justifient de conserver les modèles supervisés comme référence
principale, tout en gardant COREG comme expérience semi-supervisée documentée.

Les kNN sans pseudo-labels ont eux-mêmes des R² groupés proches de zéro : la
faiblesse de COREG ne vient donc pas seulement des ajouts. Une moyenne locale
sur des voisins du train fonctionne mieux lorsque leurs séries sont déjà
représentées ; le pool sans y ne fournit pas les valeurs mécaniques manquantes
qui permettraient de corriger un décalage entre séries.

![Comparaison des R² moyens et dispersion entre plis](../data/processed/experiments/salh_coreg_v1/coreg_comparison.png)

COREG réduit la MAE OOF face au même k dans **2/6** cas ; dans **0/6**
cas, la borne basse de l'intervalle descriptif est positive. Ces nombres ne sont pas
une garantie de progrès pour une nouvelle source et ne remplacent pas la comparaison
avec les meilleurs supervisés.

## Gain apparié et stabilité

Gain positif = MAE du contrôle moins MAE COREG, sur les mêmes observations OOF.
Bootstrap descriptif par séries inférées, 2 000 tirages seed42. Les prédictions de
différents plis partagent des données d'entraînement ; ces intervalles ne sont pas
des intervalles d'un nouveau test indépendant, particulièrement en validation aléatoire.

| CV | Cible | Contrôle | Gain MAE OOF | Intervalle bootstrap descriptif 95 % |
| --- | --- | --- | --- | --- |
| grouped | Allongement (points de %) | matched_knn_pair | -0,024 | [-0,106 ; 0,029] |
| grouped | Allongement (points de %) | knn_pair | -0,024 | [-0,106 ; 0,029] |
| grouped | Allongement (points de %) | supervised_inner_selected | -0,382 | [-0,780 ; -0,023] |
| grouped | UTS (MPa) | matched_knn_pair | -0,920 | [-1,939 ; -0,275] |
| grouped | UTS (MPa) | knn_pair | -0,920 | [-1,939 ; -0,275] |
| grouped | UTS (MPa) | supervised_inner_selected | -7,721 | [-18,425 ; 3,331] |
| grouped | Limite d’élasticité (MPa) | matched_knn_pair | -0,272 | [-1,144 ; 0,523] |
| grouped | Limite d’élasticité (MPa) | knn_pair | 0,652 | [-0,781 ; 2,608] |
| grouped | Limite d’élasticité (MPa) | supervised_inner_selected | -14,245 | [-21,023 ; -6,827] |
| random | Allongement (points de %) | matched_knn_pair | -0,011 | [-0,035 ; 0,013] |
| random | Allongement (points de %) | knn_pair | -0,011 | [-0,035 ; 0,013] |
| random | Allongement (points de %) | supervised_inner_selected | -0,349 | [-0,637 ; -0,011] |
| random | UTS (MPa) | matched_knn_pair | 0,283 | [-0,154 ; 0,886] |
| random | UTS (MPa) | knn_pair | 0,283 | [-0,154 ; 0,886] |
| random | UTS (MPa) | supervised_inner_selected | -9,175 | [-15,279 ; -3,679] |
| random | Limite d’élasticité (MPa) | matched_knn_pair | 0,322 | [-0,060 ; 0,782] |
| random | Limite d’élasticité (MPa) | knn_pair | 0,322 | [-0,060 ; 0,782] |
| random | Limite d’élasticité (MPa) | supervised_inner_selected | -6,287 | [-11,367 ; -2,070] |

Sensibilité aux bases 43/44 : même k sélectionné en interne, aucune sélection
de la meilleure graine sur les validations. La base 42 est dans le tableau principal.

| CV | Cible | Base de graine | MAE moyenne | R² moyen |
| --- | --- | --- | --- | --- |
| grouped | Allongement (points de %) | 43 | 3,887 | -0,018 |
| grouped | Allongement (points de %) | 44 | 3,888 | -0,023 |
| grouped | UTS (MPa) | 43 | 62,707 | 0,049 |
| grouped | UTS (MPa) | 44 | 63,083 | 0,040 |
| grouped | Limite d’élasticité (MPa) | 43 | 70,873 | -0,054 |
| grouped | Limite d’élasticité (MPa) | 44 | 70,868 | -0,051 |
| random | Allongement (points de %) | 43 | 2,397 | 0,535 |
| random | Allongement (points de %) | 44 | 2,396 | 0,538 |
| random | UTS (MPa) | 43 | 32,976 | 0,709 |
| random | UTS (MPa) | 44 | 33,314 | 0,703 |
| random | Limite d’élasticité (MPa) | 43 | 37,990 | 0,628 |
| random | Limite d’élasticité (MPa) | 44 | 38,203 | 0,627 |

## Ce qu'apprend la boucle

Comptes des cinq fits externes principaux par cible/protocole :

| CV | Cible | Pool brut min–max | Pool distinct min–max | Pseudo-labels min–max | Tours min–max | Arrêts |
| --- | --- | --- | --- | --- | --- | --- |
| grouped | Allongement (points de %) | 725–763 | 189–293 | 80–200 | 42–100 | max_iter: 3, no_positive_gain_in_active_pool: 2 |
| grouped | UTS (MPa) | 682–742 | 149–270 | 122–200 | 66–100 | no_positive_gain_in_active_pool: 3, max_iter: 2 |
| grouped | Limite d’élasticité (MPa) | 651–696 | 143–240 | 80–200 | 42–100 | no_positive_gain_in_active_pool: 2, max_iter: 2, pool_exhausted: 1 |
| random | Allongement (points de %) | 739–740 | 275–290 | 52–197 | 29–100 | no_positive_gain_in_active_pool: 4, max_iter: 1 |
| random | UTS (MPa) | 702–703 | 249–258 | 70–158 | 38–82 | no_positive_gain_in_active_pool: 5 |
| random | Limite d’élasticité (MPa) | 679–680 | 224–234 | 118–170 | 61–91 | no_positive_gain_in_active_pool: 5 |

![Trajectoires de pseudo-labels dans les plis encore actifs](../data/processed/experiments/salh_coreg_v1/coreg_iterations.png)

Un gain de SSE local décrit la cohérence du kNN sur son voisinage d'entraînement,
incluant les pseudo-labels. Il ne teste pas leur exactitude sur U, dont y est inconnu,
ni leur capacité à prédire une série nouvelle. Les deux distances partagent toutes
les entrées, les vrais labels et les lacunes du dataset : elles peuvent propager des
erreurs communes. C'est une explication possible, pas une cause identifiée par ce
benchmark. Le nombre de pseudo-labels ne doit donc pas être assimilé à un nombre
supplémentaire de mesures mécaniques fiables.

L'écart entre validation aléatoire et groupée mesure ici une difficulté de transfert
entre séries. La validation aléatoire bénéficie de séries et conditions susceptibles
d'être déjà représentées ; elle ne prouve pas l'hypothèse IID. La déduplication du
pool réduit fortement le nombre d'entrées distinctes, ce qui limite les informations
supplémentaires disponibles. Les diagnostics de 04/05 documentent déjà les répétitions
et le changement de domaine ; ils complètent cette lecture.

Le schéma 16/médiane a été choisi rétrospectivement après les diagnostics sur ces
données. Cette expérience est une comparaison documentée sur les mêmes plis,
pas une validation indépendante de toute la démarche de sélection des variables.
Le budget est celui de tous les vrais labels disponibles ; l'intérêt éventuel de
COREG avec seulement 25/50 % des labels nécessiterait une expérience distincte.

## Refits et exports

Nouvelle CV5 de sélection sur l'ensemble des labels : random seed1042 ou
GroupKFold5 ; le pool reste limité au train de chaque pli. Les paramètres ci-dessous
servent aux refits complets et leurs MAE sont des scores de choix, pas un test indépendant.

| CV | Cible | k COREG | MAE CV de sélection | Pseudo-labels du refit |
| --- | --- | --- | --- | --- |
| random | Limite d’élasticité (MPa) | 3 | 38,374 | 82 |
| random | UTS (MPa) | 3 | 31,079 | 44 |
| random | Allongement (points de %) | 3 | 2,301 | 41 |
| grouped | Limite d’élasticité (MPa) | 15 | 71,497 | 200 |
| grouped | UTS (MPa) | 5 | 60,489 | 186 |
| grouped | Allongement (points de %) | 3 | 3,989 | 14 |

108 pipelines complètes sous `models/salh_coreg_v1/` : 90 modèles des trains
externes (30 COREG et deux contrôles moyens par pli), puis 18 refits complets
(six COREG et leurs deux contrôles). Dossiers `random/` et `grouped/` séparés,
sidecars JSON avec IDs, groupes, unités, seeds, paramètres et hashes.
`selected_models.json` indexe les six COREG complets ; cet index identifie les
refits de cette méthode, sans proclamer COREG meilleur que les supervisés.
Ces refits ont vu tous les labels : ne pas les utiliser pour scorer les plis.
Voir [models/README.md](../models/README.md).

## Vérifications et reproduction

Exécuter 02/03/04/05/06, puis 07 de haut en bas dans le noyau du projet. Les
manifests de préparation et des benchmarks précédents sont vérifiés avant calcul.
Durée cumulée des phases terminées : 9.8 minutes,
hors interruption, audit indépendant et tests. L'exécution a été reprise après
une interruption : 516 fits complets et 108 exports conservés, puis les 60 fits
de sensibilité relancés et les cellules de vérification exécutées dans un noyau
neuf. Cette reprise est enregistrée dans le manifeste ; les résultats principaux
n'ont pas été réentraînés ni leurs paramètres modifiés. Versions exactes :
`{"python": "3.14.8", "sklearn": "1.9.1", "numpy": "2.5.3", "pandas": "3.0.6", "joblib": "1.6.0", "cloudpickle": "3.1.2"}`.

37 tests ciblés passent, dont cinq nouveaux sur l'équivalence du gain avec des
refits explicites, les transferts croisés, les répétitions/arrêts, l'imputation
sur les vrais labels et l'isolement inductif. Tous les 108 exports sont rechargés
dans un processus neuf ; les 90 modèles externes reproduisent leurs OOF complètes.
L'audit indépendant recalcule 180 scores, vérifie
l'accès aux données pour 576 fits et leurs
81931 pseudo-labels, ainsi que les hashes et les choix
internes. Il recalcule explicitement 1410
gains/pseudo-prédictions sur douze modèles externes/complets, sans réutiliser le
calcul vectorisé du notebook.

Les CSV de scores, OOF, choix internes, journal des pseudo-labels, voisinages,
itérations, sensibilités, contrôles de rechargement et manifest sont sous
`data/processed/experiments/salh_coreg_v1/`. Données et modèles restent ignorés
par Git ; seuls le code, ses sorties de lecture et les justifications sont suivis.

## Référence supervisée étendue — 12 octobre 2026

Les entraînements COREG et ses contrôles restent identiques. La référence
supervisée intègre désormais XGBoost, mêmes labels et plis ; cette comparaison
ne mesure pas à elle seule l’effet des pseudo-labels. Les gains au même k
ci-dessus restent inchangés. COREG demeure moins performant que la procédure
supervisée dans les six cas.

| CV | Cible | MAE COREG | R² COREG | MAE XGBoost | R² XGBoost | MAE sélection six | R² sélection six |
| --- | --- | --- | --- | --- | --- | --- | --- |
| random | YS (MPa) | 37,919 | 0,629 | 26,334 | 0,816 | 26,334 | 0,816 |
| random | UTS (MPa) | 33,037 | 0,709 | 22,542 | 0,845 | 23,604 | 0,830 |
| random | Allongement (points de %) | 2,402 | 0,535 | 2,021 | 0,654 | 2,064 | 0,646 |
| grouped | YS (MPa) | 71,074 | -0,056 | 54,363 | 0,367 | 54,363 | 0,367 |
| grouped | UTS (MPa) | 63,060 | 0,043 | 50,215 | 0,392 | 55,691 | 0,307 |
| grouped | Allongement (points de %) | 3,904 | -0,028 | 3,322 | 0,238 | 3,278 | 0,260 |
