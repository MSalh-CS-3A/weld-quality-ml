# Spécification du projet — préparation et expériences

Mise à jour : 10 octobre 2026. L’énoncé original est préservé dans
[sujet.md](../sujet.md). Cette spécification décrit le protocole actif ; les
anciens essais et audits sont référencés à la fin, sans constituer le code courant.

## Objectif et état actuel

Prédire des propriétés mécaniques de soudures à partir de leur composition et
paramètres renseignés, puis comparer des méthodes supervisées et au moins une
méthode semi-supervisée. Une propriété mécanique représente un aspect de la
qualité ; aucun score universel ou seuil de bonne/mauvaise soudure n’est inventé.
La disponibilité effective des entrées dans le scénario d’utilisation doit être
explicitée avant une recommandation pratique.

**La préparation, le supervisé et COREG sont implémentés dans les notebooks.**
Le notebook 03 exécute la comparaison réglée de trois propriétés de traction et
une expérience exploratoire d’énergie Charpy. L’utilisateur a confirmé les
méthodes du cours, puis autorisé l'entraînement COREG dans le notebook 07.
Les protocoles de toutes les sources Charpy, une validation indépendante et
les conclusions pratiques restent à valider.

## Organisation retenue

À la demande explicite de l’utilisateur, le code d’analyse est directement dans
les notebooks autonomes ; cette décision remplace la préférence initiale pour
un package `src/weld_quality/`.

| Notebook | Responsabilité |
| --- | --- |
| `01_eda.ipynb` | Structure, statuts, distributions, dépendances, propriétés et ACP descriptive |
| `02_data_preparation.ipynb` | Parsing, provenance, déduplication, groupes, cohortes, plis, preprocessing et contrôle d’imputation |
| `03_modeling.ipynb` | Exports vérifiés, statistiques, variables, pipelines locales, recherches imbriquées par groupes et prédictions externes supervisées |
| `04_diagnostics.ipynb` | Erreurs par séries, audit Charpy, importance par permutation et sensibilités contrôlées des entrées et imputations |
| `05_random_kfold.ipynb` | Validation aléatoire 16/médiane, comparaison des regroupements et exports supervisés |
| `06_grouped_exports.ipynb` | Exports groupés 16/médiane et contrôles de reproduction |
| `07_coreg.ipynb` | COREG inductif traction, contrôles kNN, validations imbriquées aléatoire/groupée, sensibilité et exports |
| `08_xgboost.ipynb` | XGBoost, benchmarks 16/médiane à six familles, comparaison COREG, refits complets et audits |

Le téléchargeur standard-library reste autonome dans `scripts/download_data.py`.
Les dépendances sont dans `requirements.txt`. Aucun notebook ne dépend d’un
module du projet, d’un import d’un autre notebook ou d’un ancien CSV AI imputé.
Le brut va sous `data/raw/`, le dérivé sous `data/processed/` ; ces datasets,
les modèles et les environnements ne sont pas commités.

## Données, unités et nettoyage déterministe

Source : Cambridge Weld DB, Cool & Bhadeshia, 1 652 lignes × 44 champs.
Le fichier brut a le SHA-256
`eb46df81a454c8e549187d87c67a6e72b88676f760e8688a782c832737676ac1`.
Voir [data/README.md](../data/README.md) pour les unités et fichiers.

- Lecture des 44 champs en chaînes ; `raw_row_id` est l’indice brut 0-based stable.
- `N` = non rapporté, jamais zéro. Les valeurs exactes, zéros et extrêmes sont
  conservés. Une valeur extrême n’est pas supprimée sur sa seule amplitude.
- `<L` sans doute d’unité → L/2 ; intervalle → milieu. Ce sont des approximations
  déterministes, avec opérateur, bornes et token conservés, pas des mesures exactes.
- Les valeurs d’unité douteuse sont indisponibles (NaN), sans conversion :
  Ti/Al/Sn/As/Sb exacts positifs <1 ppm, Ti/Al `<0.01`, V `<5` en colonne wt%.
  La quarantaine couvre 322 cellules : Al 26, Ti 17, V 9, Sn/As/Sb 90 chacun.
  Le drapeau ne démontre pas que chaque valeur est erronée ; seule la source
  permet de confirmer une unité ou de restaurer la valeur.
- Les 59 annotations d’azote total/résiduel restent hors de N principal, avec
  extraction lexicale conservée. Dureté : valeur et protocole Vickers séparés,
  sans regroupement automatique des protocoles. `fatt50` reste d’unité non résolue.
- Seuls les synonymes documentés ShMA→MMA et SMA→SA sont regroupés. Les autres
  procédés restent distincts. Courant et polarité restent séparés ; leur `N`
  devient la modalité `missing`, sans déduire DC à partir d’un signe de polarité.
- Les quatre occurrences excédentaires identiques sur les 43 champs bruts hors ID
  (indices 393, 423, 425 et 1434) sont exclues des cohortes et des plis. Le premier
  reste conservé, les autres IDs sont des alias. Une collision après suppression
  de colonnes ne suffit pas à déclarer deux observations brutes identiques.
- Les 13 lignes PWHT manquant restent dans la table maître. Les couples mesurés
  0/0 sont conservés sans affirmer leur signification métallurgique.

Le nettoyage produit une table maître de 1 652 lignes, dont quatre alias marqués ;
1 648 lignes sont dédupliquées. La provenance décrit 66 080 cellules numériques.
Aucune cible observée n’est modifiée et aucune cible manquante n’est imputée.

## Cibles et jeux d’entrées

Régressions séparées, avec éligibilité propre à chaque cible :

| Cible | Définition | Unité | Labels dédupliqués | Labels cohorte principale |
| --- | --- | --- | ---: | ---: |
| `yield_strength` | Limite d’élasticité | MPa | 777 | 706 |
| `uts` | Résistance maximale à la traction | MPa | 735 | 677 |
| `elongation` | Allongement | % | 697 | 631 |
| `reduction_area` | Réduction de section, complémentaire | % | 702 | 635 |

Configuration de référence : **A1_13**, treize entrées numériques + procédé catégoriel.

- A0_11 : C, Si, Mn, S, P, courant, tension, apport thermique, température entre
  passes, température PWHT et durée PWHT.
- A1_13 : A0_11 + oxygène et azote.
- A1b_16 : A1_13 + nickel, chrome et molybdène ; comparaison future.

Le noyau principal vise une couverture suffisante et une imputation contrôlable.
Il ne démontre pas que les variables exclues ont peu d’effet physique, ni que
13 entrées sont optimales pour la prédiction. Les autres sorties mécaniques,
la température Charpy, la microstructure, les IDs, flags d’éligibilité et numéros
séparant les plis ne sont pas des predictors des tâches de traction.

Cohorte principale : au plus deux entrées numériques indisponibles sur A1_13,
après représentation déterministe et retrait des alias. Elle contient **1 555
lignes de 44 groupes** ; Cunh-1982, EvHtIp1979 et Natsume-1990 sont exclus. Le seuil
est un choix d’ingénierie, sans garantie de fiabilité. Des seuils ≤1/≤3 donnent
1 087/1 603 lignes, 34/46 groupes et 501/748 labels YS ; leurs performances ne sont
pas encore comparées. Une autre cohorte/extension exige une règle explicite et
une population de validation commune pour une comparaison équitable.

Le filtre supervisé est `in_strict13 & has_<cible>`. Le pool par cible est
`in_strict13 & ~has_<cible>`, uniquement dans les groupes d’entraînement.
Après déduplication, 105 lignes n’ont aucune des cinq sorties traction/Charpy ;
99 sont dans la cohorte. Les pools par cible sont plus grands que ce total.

Charpy reste conditionnel : 861 valeurs dans la cohorte ne constituent pas
encore une tâche homogène. E(T) utilise la température comme entrée ; T100J/T28J
la prédisent. Les signatures de série sont des hypothèses à vérifier par source,
pas un classement validé à partir d’E=100 ou E=28. Dureté et `fatt50` ne sont
pas des tâches d’entraînement adoptées.

À la demande de l’utilisateur le 10 octobre, l’énergie Charpy est incluse dans
la comparaison supervisée comme **expérience exploratoire sur les couples
rapportés E(T)** : cible `charpy_J` (J), A1_13 + procédé + `charpy_temp_C` (°C).
La température d’essai doit être connue ; elle n’est pas reconstruite pour
fabriquer une condition d’essai. Les 861 couples éligibles couvrent 24 groupes.
Ils ne sont pas présentés comme des mesures directes toutes comparables : la
documentation originale définit les colonnes mais pas le protocole de chaque
ligne. Aucun seuil 28/100 J ne sert à reclasser ou exclure automatiquement une
ligne. Les erreurs par signature sont des diagnostics séparés, sans sélection
de paramètres ou de labels à partir de ces résultats.

Un exemple primaire de prédiction E(T) avec température d’essai en entrée et
énergie moyenne de plusieurs essais en sortie est décrit par
[Bhadeshia, MacKay et Svensson (1995), pp. 3–5](https://www.phase-trans.msm.cam.ac.uk/abstracts/toughness.pdf).
Cet article ne valide pas les protocoles de toutes les séries du master.
L’audit par source reste nécessaire avant un benchmark Charpy déclaré homogène.

Les quatre tâches sont indépendantes : 706/677/631/861 labels respectivement,
dans 40/39/34/24 groupes. Seules 609 lignes ont les trois sorties de traction et
141 les quatre sorties. Conserver des régressions séparées évite de restreindre
chaque tâche aux seuls cas complets communs. La corrélation entre sorties ne
justifie ni leur remplacement automatique ni l’ajout d’une autre sortie à X.

## Validation et preprocessing appris

47 groupes conservateurs dérivés des identifiants : préfixe jusqu’à l’année,
familles explicites de rapports/lettres, préfixe non daté ou ID exact en dernier
recours. Les doublons connectent leurs séries. Ce sont des séries inférées,
pas des publications validées. Les variantes Ga&K/Gar&K et Kocak restent une
sensibilité à tester ; `MERGE_NAME_VARIANTS=False` dans le protocole courant.

- Cinq plis externes GroupKFold sans mélange, communs aux cibles/méthodes.
- Trois plis internes par groupes dans chaque train externe pour les réglages.
- Graine 42 pour les estimateurs stochastiques. Les splits sont exportés par ID brut.
- Dans la cohorte, chaque pli externe a 8–10 groupes ; les validations des trois
  cibles comportent 103–166 labels. Le nombre de lignes ne garantit pas le nombre
  d’observations indépendantes.
- Tous les fits appris (imputation, échelle, encodage, sélection de variables,
  éventuelle ACP) sont refaits dans le train interne, puis dans le train externe
  après sélection. Aucune matrice imputée globalement n’est utilisée pour la CV.

`FoldPreprocessor`, défini dans le notebook 02 : moyenne/écart-type numériques
du train, one-hot du procédé sur catégories du train (inconnue → vecteur nul),
puis IterativeImputer/BayesianRidge. Initialisation médiane, ordre ascendant,
max_iter=100, tol=1e-3, random_state=42, skip_complete=False, bornes non négatives
pour les imputations concernées. Les cibles ne sont jamais passées au transformer.

Les PWHT manquants sont projetés sur un couple réel du train en distance
standardisée ; une composante observée impose la compatibilité. Aucun couple
compatible, aucune paire complète d’apprentissage ou une colonne entièrement
absente → erreur explicite. Non-convergence → erreur, sans fallback silencieux.
Réviser un schéma ou choisir un contrôle médiane se décide dans l’entraînement,
jamais en sélectionnant un repli à partir des scores externes.

La méthode médiane est conservée comme baseline de sensibilité. Les 15 fits
itératifs du contrôle sur trois cibles × cinq plis convergent en 4–7 itérations.
Cela ne prouve pas l’exactitude des absences réelles ni la convergence sur 16/21
entrées. Les anciens scores de reconstruction sur 11 entrées ne sont pas un
nouveau benchmark de reconstruction sur la cohorte 13 corrigée.

Le master nettoyé conserve les NaN : dans la cohorte principale, 607 lignes ont
au moins une entrée numérique absente, soit 1 075 cellules. L’imputation a déjà
été ajustée pour les contrôles ; ses paramètres ne sont pas réutilisés pour
les futurs fits. Pour chaque entraînement supervisé : fit du preprocessing sur
les seules lignes étiquetées du train, transformation du train et de la validation
avec ce même objet, puis fit/prédiction du modèle. Après les expériences, un
modèle destiné à l’utilisation sera réajusté avec sa pipeline sur les données
d’apprentissage retenues ; ce refit n’est pas une nouvelle validation.

## Modèles, métriques et expériences supervisées

Le contrôle existant utilise une constante à la médiane de y, Ridge alpha=1 et
Random Forest 300 arbres/min_samples_leaf=2/graine42. Il est à paramètres fixes,
sans sélection finale et sans tuning interne. MAE moyennes RF/itérative :
66,13 MPa (YS), 56,71 MPa (UTS), 3,55 points de % (allongement) ; R² moyens
0,0765, 0,1899, 0,1136. L’itérative n’est pas uniformément meilleure ; les causes
des performances modestes ne sont pas isolées. Voir le rapport 07.

Métriques : MAE = moyenne de |y−prédiction| ; RMSE = racine de la moyenne des
écarts au carré ; R² = 1−somme des écarts au carré/somme des écarts à la moyenne
observée au carré. MAE/RMSE sont en MPa, points de % ou J, R² sans unité. Le contrôle
actuel rapporte moyenne non pondérée et écart-type des cinq plis ; conserver
les scores par pli et les effectifs. Ces écarts-types ne sont pas des IC.

Budgets du 9 octobre, implémentés dans `03_modeling.ipynb` le 10 octobre :

| Méthode | Raison du comparateur | Budget initial par train externe |
| --- | --- | --- |
| Médiane de y du train | Gain minimal à dépasser | Aucun réglage |
| Ridge | Relation linéaire régularisée, comparateur simple | 6 alpha : 0,01 ; 0,1 ; 1 ; 10 ; 100 ; 1 000 |
| SVR RBF | Comparateur à noyau non linéaire | C={1,10,100}, gamma={scale,0,05}, epsilon={0,05,0,2}, soit 12 configurations |
| Random Forest | Interactions non linéaires par arbres | 300 arbres, leaf={1,2,5}, depth={None,10}, max_features={0,5;1}, soit 12 configurations |
| kNN supervisé | Contrôle de la future semi-supervision | k={3,5,9,15}, p={1,2}, poids uniformes, soit 8 configurations |

Les grilles sont des budgets de départ, pas des valeurs optimales établies.
La SVR standardise aussi y sur le train uniquement ; ses prédictions sont
reconverties en MPa/points de %/J. Les autres modèles gardent y dans son unité.
MAE interne moyenne non pondérée des trois plis = critère de réglage ; conserver
RMSE et R² pour l’analyse externe. A1_13 + imputation itérative sont fixés pour
la première comparaison. La médiane d’imputation reste un contrôle documenté,
pas une option sélectionnée sur les scores externes. L’utilisateur a confirmé
que les modèles supervisés appartiennent aux méthodes vues en cours.

Chaque recherche utilise une `Pipeline` locale contenant `FoldPreprocessor`
puis l’estimateur. Pour SVR, l’estimateur final est un
`TransformedTargetRegressor(SVR, StandardScaler)` : y est ajusté dans le train
courant et les prédictions sont remises en unité originale. La baseline
`DummyRegressor(strategy='median')` ne fait aucun preprocessing X et apprend
uniquement la médiane de y du train. Les paramètres de forêt restent 300 arbres,
graine 42, un worker par forêt ; les recherches utilisent trois threads et un
thread BLAS. Le cache de preprocessing est indexé par le train X/y et les
paramètres du transformer ; aucun fit n’est partagé entre trains distincts.

39 configurations par cible/pli externe, trois validations internes par
configuration et un refit par famille : 2 340 fits internes et 100 refits
externes, soit 2 440 fits d’estimateurs. `error_score='raise'` interdit de masquer
un échec d’imputation ou de modèle. Les prédictions externes doivent couvrir
exactement une fois chaque ID éligible par cible/famille, avec les labels
observés inchangés. Aucune ligne sans la cible n’entre dans le train supervisé.

Les moyennes externes sont non pondérées entre les cinq plis ; les scores OOF
regroupent les prédictions et pondèrent implicitement par les lignes. Conserver
les deux lectures, les effectifs et les scores de chaque pli. Les erreurs du
train sont seulement des diagnostics. La comparaison externe des familles
ne sélectionne pas un modèle final avec une estimation indépendante de cette
sélection ; aucun refit global de production n’est effectué dans cette étape.

Les schémas A0_11 et A1b_16 seront des sensibilités sur les mêmes lignes
`in_strict13`, mêmes labels et mêmes plis. Le schéma 16 n’autorise pas un filtre
supplémentaire pour améliorer ses scores ; une absence complète dans le train
ou une non-convergence doit être rapportée. Si le jeu d’entrées ou la famille
de modèle est optimisé, ce choix fait partie de la recherche interne. Choisir
le meilleur tableau externe puis annoncer son score comme une estimation
indépendante de la sélection serait optimiste. Voir
[l’exemple de validation imbriquée scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

Au moins une méthode semi-supervisée est exigée par le sujet. COREG est retenu
et implémenté dans le notebook 07 après l'autorisation de l'utilisateur ; le
protocole détaillé figure dans « COREG autorisé » ci-dessous.
Il utilise deux régressions kNN à distances différentes et un échange de
pseudo-labels sélectionnés ; source primaire :
[Zhou et Li, IJCAI 2005](https://www.lamda.nju.edu.cn/publication/ijcai05.pdf).
Les pseudo-labels ne sont pas des mesures ; aucun gain sur cette base n’est acquis.
Protocole inductif : pools du train courant uniquement (interne comme externe),
avec exclusion de tous les groupes de validation dans le protocole groupé et
des lignes de validation dans le protocole aléatoire ; aucun label de validation
dans le fit ou les pseudo-labels.
Comparer au pendant supervisé avec les mêmes labels d’entraînement et les mêmes
deux régressions/agrégation, sans pseudo-labels, en plus du kNN simple. Pour isoler
l’ajout de pseudo-labels, le premier protocole ajuste le preprocessing sur le
train étiqueté uniquement, puis transforme le pool autorisé sans refit. Les
autres propriétés connues d’une ligne du pool ne deviennent ni entrées ni labels
de la cible manquante. Réglages et limites d’itérations de COREG ont été définis
avant son évaluation ; ils ne sont pas déduits des scores externes.

Définitions des méthodes supervisées : documentation officielle
[Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html),
[SVR](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html),
[Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

Exports du notebook 03 : prédictions externes par ID brut/cible/pli, métriques, effectifs,
paramètres choisis, jeu d’entrées, imputation, seed, versions, hashes des données
et du code. L’expérience est sous
`data/processed/experiments/salh_supervised_v1/` (ignoré par Git). Les 100
pipelines externes ajustées restent dans le dictionnaire `outer_models` du
noyau ; aucun modèle de production n’est sérialisé. Les résultats sont commentés
dans [le rapport supervisé](../reports/10_supervised_training.md).

### Résultats de l’exécution du 10 octobre

Les 100 évaluations externes réglées ont terminé. La boucle de recherches/refits
a duré environ six minutes sur l’environnement local. Le tableau ci-dessous
décrit Random Forest, qui a la plus faible MAE moyenne observée parmi les familles
dans chaque tâche ; il ne sélectionne pas une famille avec un score indépendant
de cette sélection. Les résultats des cinq familles et de chaque pli sont dans
le notebook et le rapport.

| Cible | MAE RF moyenne ± écart-type | MAE constante médiane | R² RF moyen |
| --- | ---: | ---: | ---: |
| Limite d’élasticité | 65,88 ± 10,61 MPa | 70,45 MPa | 0,0786 |
| UTS | 57,65 ± 10,78 MPa | 72,66 MPa | 0,1942 |
| Allongement | 3,56 ± 0,18 points de % | 4,09 points de % | 0,1247 |
| Énergie Charpy, exploratoire | 34,71 ± 12,36 J | 36,04 J | 0,0173 |

Les performances restent modestes et variables entre groupes ; un réglage
interne n’assure pas une amélioration sur le contrôle historique à paramètres
fixes. Pour Charpy, le faible gain et les protocoles non homogénéisés limitent
encore l’interprétation. Les 80 fits de contrôle d’imputation convergent en
3–9/3–13/4–14/3–20 itérations pour YS/UTS/allongement/Charpy respectivement.
Les scores OOF regroupés sont exportés séparément des moyennes non pondérées
par pli ; ils ne doivent pas être confondus.

## ACP, preuves et limites

EDA active : ACP standardisée sur 1 339 lignes dédupliquées dont les onze entrées
sont des nombres exacts complets, sans imputation. PC1=27,02 %, PC2=19,03 %,
cumul=46,05 %. Cette sous-population ne représente pas automatiquement toute
la base ; l’ACP descriptive n’est pas réutilisée pour scorer les modèles.

Les huit CSV migrés reproduisent les exports AI corrigés, scores compris.
Les trois notebooks ont été exécutés séquentiellement par Python, de haut en bas,
depuis `notebooks/` ; cette vérification ne teste pas l’interface Jupyter.
Quinze tests ciblés hors ligne validaient cette migration. Le notebook 03 a
ensuite été exécuté de haut en bas avec un noyau Jupyter le 10 octobre ; la suite
comprend désormais vingt tests, dont cinq sur l’entraînement et les frontières
internes/externes. Les fichiers bruts, les huit exports de préparation et
`sujet.md` restent préservés. Les versions et hashes sont enregistrés dans les
manifestes de préparation et d’expérience.

Les unités en quarantaine, annotations N, protocoles Charpy, regroupement par
publication, sensibilité au seuil/jeux d’entrées et erreurs des modèles restent
ouverts. Aucun effet causal ni recommandation de réglage de soudure n’est établi.
Le rapport final d’environ cinq pages, les informations du binôme et le Gantt
restent à compléter après les expériences ; les temps réels ne sont pas inventés.

## Historique conservé

| Preuve | Portée |
| --- | --- |
| [Audit EDA initial](../reports/01_eda_audit_details.md) | Mesures brutes et ambiguïtés du 3 octobre |
| [Plan historique](../reports/02_preprocessing_plan.md), [résultats historiques](../reports/03_preprocessing_results.md) | Reconstruction et sensibilités du 5 octobre, code conservé dans Git |
| [Plan d’entraînement](../reports/04_preprocessing_training_plan.md), [design de préparation](../reports/05_data_preparation_notebook_design.md) | Propositions et screening précédant la migration |
| [Premier audit AI](../reports/06_ai_prepared_audit.md) | Première préparation non adoptée |
| [Audit corrigé](../reports/07_corrected_ai_preparation_audit.md) | Huit CSV reproduits, portée et réserves scientifiques |
| [Migration](../reports/08_notebook_migration.md) | Commits, réduction de l’EDA, suppression de src et vérifications |
| [Plan d’expériences](../reports/09_modeling_plan.md) | Cibles, compromis d’entrées, budgets supervisés et portée de l’imputation |
| [Entraînements supervisés](../reports/10_supervised_training.md) | Recherches imbriquées, pipelines, scores externes et portée exploratoire Charpy |
| [Diagnostic approfondi](../reports/11_performance_diagnostics.md) | Erreurs par groupes, audit des sources Charpy, explicabilité et comparaisons 11/13/16 × imputation |
| [KFold aléatoire et exports](../reports/12_random_kfold_training.md) | Benchmark 16/médiane, sens des séries/conditions, modèles persistés et pools inductifs |

Les sources AI originales sont sauvegardées au commit `2ecb088` et retirées de
l’arborescence active. Les artefacts fournis restants dans `ai_prepared/` sont des
références locales ignorées, sans rôle dans l’exécution du protocole courant.

## Diagnostic approfondi demandé le 10 octobre 2026

Le benchmark 03 reste conservé. Le notebook 04 utilise les mêmes labels,
la cohorte strict13 et les cinq plis externes / trois internes exportés.
Il s'agit d'une investigation après observation des scores externes : aucun
résultat n'est une confirmation sur un nouveau jeu indépendant.

Avant les nouvelles recherches, protocole fixé : six combinaisons
A0_11/A1_13/A1b_16 × médiane/itérative, quatre familles Ridge/SVR/RF/kNN,
grilles du notebook 03, choix des paramètres par MAE interne. La cohorte
n'est pas refiltrée sur 16 variables : les absences Ni/Cr/Mo restent visibles.
Contrôle explicite de chaque train interne/externe ; une imputation invalide
invalide la combinaison cible/pli sans fallback. Les échecs sont exportés.
La comparaison de sélection MAE/MSE réutilise des scores internes multimetriques
et refit les paramètres choisis par MSE sur le train externe seulement.
La sélection conjointe schéma/imputation/famille est également interne,
avec scores externes séparés des tableaux descriptifs des scénarios.

Le diagnostic réutilise les prédictions externes pour les erreurs par groupe,
biais, décomposition SSE/SST, domaine des entrées et seuil RMSE correspondant
à R²=0,5. Les RF sont reconstruits avec leurs paramètres internes exportés
et leurs prédictions doivent reproduire le benchmark. Les permutations portent
sur la pipeline entière, par variable et blocs corrélés, sans refit et sans
sélection de nouvelles entrées à partir de ces importances. Elles décrivent le
comportement du modèle ; elles ne mesurent pas un effet physique causal.
Les courbes d'apprentissage emploient des sous-ensembles de groupes du train,
deux graines et des paramètres fixés, sans consulter les labels externes.

L'audit Charpy confronte les séries à des publications originales. Une seule
signature E=28/100 ne justifie aucune suppression : un point de transition
peut aussi appartenir à une courbe E(T), mais sa règle d'échantillonnage diffère.
Les correspondances de composition et de protocole, les incertitudes de
transcription et les groupes non résolus sont consignés séparément.

Contrôles explicatifs supplémentaires fixés avant leur calcul : comparaison
d'un RF identique (300 arbres, feuille minimale 2, profondeur libre,
max_features=1.0, seed42) sous les plis groupés existants et sous KFold lignes
5 plis mélangés seed42. Aucun tuning ni réemploi de paramètres sélectionnés
sur des labels de la nouvelle validation. Le partage lignes est un scénario
alternatif d'observations apparentées, pas la métrique principale de nouvelles
séries. Contributions locales : somme exacte des incréments de valeurs des
nœuds sur les chemins des arbres, order-dependent, sans revendication SHAP/causale.
Reconstruction Ni/Cr/Mo : masquer 20 % des valeurs initialement observées dans
chaque validation cible/pli, seed42+pli et masques communs aux deux imputations ;
train inchangé. Ce contrôle n'est pas utilisé pour choisir une méthode et ne
reproduit pas nécessairement les absences naturelles.

### Résultats de l'investigation

436 évaluations externes réussies sur 480 prévues. L'itérative à 16 entrées ne
converge pas dans 11 contextes cible/pli : YS pli 4 ; UTS plis 3/4 ; allongement
plis 2/3/4 ; Charpy tous les plis. Les 44 évaluations indisponibles sont explicites,
sans fallback ; les comparaisons incomplètes ne sont pas classées avec les cinq
plis complets. Les 80 configurations primaires reproduisent leurs prédictions
de référence. Les choix internes par MAE/MSE et la couverture OOF sont audités.

R² = moyenne non pondérée des cinq plis externes, sur les mêmes populations :

| Cible | RF 13/itérative | RF 16/médiane | Sélection conjointe interne | MAE RF 16/médiane |
| --- | ---: | ---: | ---: | ---: |
| Limite d'élasticité | 0,0786 | 0,3898 | 0,3366 | 54,14 MPa |
| UTS | 0,1942 | 0,3944 | 0,3336 | 48,91 MPa |
| Allongement | 0,1247 | 0,2261 | 0,1636 | 3,34 points de % |
| Charpy exploratoire | 0,0173 | 0,1380 | −0,1003 | 33,03 J |

À médiane identique, l'extension 16 réduit la MAE OOF du RF de 11,06 MPa
(YS, bootstrap par groupes [3,09 ; 20,19]) et 8,80 MPa (UTS [2,38 ; 15,40]).
Les intervalles du gain pour allongement/Charpy incluent zéro. Le schéma 16/médiane
est un candidat à valider sur des séries indépendantes, pas un modèle adopté
sur le meilleur score externe. La sélection conjointe expose la variabilité
des choix faits uniquement dans les trains internes. Le choix MSE n'apporte
qu'un faible changement de R² au noyau initial ; aucune garantie R²≥0,5.

Le RF fixe sous KFold lignes atteint des R² moyens 0,554/0,625/0,531/0,773 ;
99–100 % des lignes de validation appartiennent alors à un groupe déjà présent
dans le train. Ce résultat étaye la difficulté de transfert entre séries ; il
ne remplace pas le protocole principal. Dans le RF initial, les biais de niveau
par groupe portent 56/51/50/36 % de SSE respectivement. Pour Charpy, les lignes
hors plages observées X du train ont une MAE ≈53 J contre ≈28 J pour les autres.
L'imputation ne suffit pas à expliquer ces écarts : X complet n'est pas toujours
associé à une meilleure précision. La reconstruction Ni/Cr/Mo artificiellement
masqués est comparée sur les mêmes contextes réussis pour les deux méthodes.

Audit source : deux familles E(T) confirmées, Svensson/Gretoft (80 lignes) et
Evans stress-relief (94 lignes, publication 1986 malgré l'ID 1991). Le papier
chromium 1989 et ses compositions étayent l'extraction T100 des 31 lignes de
cette série ; valeurs ponctuelles non redigitisées. 21 groupes/656 lignes restent
non résolus. Température et énergie sont deux colonnes à unités distinctes ;
aucun mélange d'unités dans une colonne n'est établi. La fréquence E=28/100 ne
justifie aucune suppression. Deux sources confirmées ne suffisent pas à un
nouveau benchmark imbriqué à cinq groupes/plis. Charpy reste exploratoire.

Le notebook 04 conserve les sorties des calculs principaux et des contrôles
complémentaires exécutés dans un noyau neuf. Vingt-cinq tests passent ; un audit
des exports vérifie leurs hashes, les paramètres sélectionnés en interne, les
labels/IDs OOF et la décomposition locale exacte. Brut, préparation et benchmark
03 restent préservés. Les explications sont associatives et rétrospectives ;
aucun facteur physique isolé ni plafond irréductible de précision n'est démontré.

## Extension demandée : KFold aléatoire et exports — 2026-10-10

Le notebook autonome `05_random_kfold.ipynb` ajoute le scénario aléatoire demandé
par Salh, sur les mêmes labels et la même cohorte strict13. Configuration de
travail : **16 entrées numériques CORE13 + Ni/Cr/Mo, médiane et procédé** ; Charpy
ajoute sa température d'essai connue. Cela ajoute trois colonnes, aucune ligne.
Ce choix s'appuie sur le diagnostic 04 déjà observé : l'évaluation qui suit est
rétrospective, même avec une sélection imbriquée des modèles. Aucun nouveau jeu
indépendant n'est revendiqué et le benchmark groupé est conservé.

Avant entraînement : KFold externe 5, shuffle, seed42, par cible sur les labels
triés par raw_row_id ; KFold interne 3, shuffle, seed43+pli externe. Famille et
hyperparamètres choisis sur MAE interne, sans utiliser les scores externes. Même
baseline médiane de y et mêmes grilles Ridge/SVR RBF/RF/kNN qu'au notebook 03.
Toutes les transformations sont ajustées dans le train courant. Aucun autre
label, identifiant, groupe, dureté ou FATT50 n'entre dans X. La SVR standardise
son y dans son train ; aucune ACP prédictive n'est introduite.

Audit des regroupements : diversité des conditions disponibles dans les séries,
répétitions exactes CORE16+procédé et courbes Charpy confirmées par leurs sources.
Une signature partielle identique est un **proxy**, pas une identité de soudure
vérifiée. Un test de permutation de l'association groupe/cible (999 permutations,
seed42) ne démontre pas l'indépendance. Un contrôle avec le même RF fixe
(300 arbres, feuille2, profondeur libre, max_features1, seed42), sans tuning,
compare plis par lignes, proxies de conditions au sein des séries et séries
inférées. Il sépare l'effet du découpage des réglages. Le scénario aléatoire
estime la prédiction de nouvelles lignes lorsque leurs séries peuvent être
connues ; le scénario groupé estime le transfert aux séries exclues du train.

Pour préparer une comparaison semi-supervisée **inductive**, les lignes sans y
sont affectées à cinq blocs équilibrés seed142, puis à trois blocs internes
seed1042+pli externe. Les X des validations internes/externes sont exclus du pool
autorisé ; leurs labels ne servent jamais à créer des pseudo-labels. Les
partitions sont exportées par cible et les droits d'accès sont vérifiés. Cette
règle complète le protocole par groupes du notebook 02 pour le nouveau scénario
aléatoire : des séries partagées sont permises, des lignes de validation ne le
sont pas. Les pools candidats comptent 849/878/924 lignes pour YS/UTS/allongement.
**Charpy : zéro ligne sans énergie avec température d'essai connue** dans cette
cohorte. Ne pas fabriquer une température pour constituer un pool. Aucun
algorithme semi-supervisé ni COREG n'est encore exécuté dans ce notebook.

Persistance : 20 pipelines sélectionnées dans les trains externes, puis 20
pipelines réentraînées sur tous les labels (cinq familles × quatre cibles), sous
`models/salh_random_kfold_v1/`, ignorées par Git. Les quatre familles recommandées
pour ce scénario sont sélectionnées par une nouvelle CV5 aléatoire seed1042 sur
l'ensemble des labels. Cette CV de choix final n'est pas un nouveau test
indépendant. Chaque pipeline complète inclut son prétraitement ; cloudpickle
permet les classes définies dans un notebook autonome. Les sidecars JSON
conservent unités, entrées, paramètres, IDs du train, versions et hashes. Toutes
les sauvegardes sont rechargées et les quatre modèles choisis sont vérifiés dans
des processus Python neufs. Les refits sur tous les labels ne peuvent jamais
servir à l'évaluation des futurs plis semi-supervisés ; repartir des trains
autorisés et comparer au contrôle supervisé sur les mêmes partitions.

Références de méthode : [validation croisée scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html)
et [persistance de modèles](https://scikit-learn.org/stable/model_persistence.html).

### Résultats et vérification de cette extension

Notebook 05 exécuté intégralement dans un noyau Jupyter neuf en environ sept
minutes. 100 évaluations externes, 780 configurations internes enregistrées,
20 choix de famille/paramètres internes et 60 contrôles RF des trois découpages.
Scores de la sélection imbriquée, moyennes des cinq plis externes :

| Cible | MAE moyenne | R² moyen | Famille retenue pour le refit complet (CV5 seed1042) |
| --- | --- | --- | --- |
| yield_strength | 31,630 MPa | 0,755 | SVR RBF |
| uts | 23,861 MPa | 0,836 | SVR RBF |
| elongation | 2,054 points de % | 0,660 | Random Forest |
| charpy_J, exploratoire | 16,461 J | 0,776 | Random Forest |

Les scores évaluent la sélection des trains externes, qui peut changer de
famille ; ils ne sont pas un test indépendant des quatre refits complets.
Les CV de choix de ces derniers ont 156 candidats au total. Les paramètres
retenus et toutes les MAE/RMSE/R² par famille/pli sont dans
[le rapport 12](../reports/12_random_kfold_training.md).

Le RF fixe donne R² lignes / conditions-proxy / séries :
0,739/0,722/0,318 (YS), 0,786/0,797/0,370 (UTS), 0,644/0,680/0,175
(allongement), 0,769/0,643/0,074 (Charpy). Les conditions répétées seules
n'expliquent donc pas le problème de transfert traction entre séries. Les
groupes actuels sont larges : 37/40, 36/39, 33/34 et 23/24 séries comportent
plusieurs signatures pour les quatre cibles. À l'inverse, 99–100 % des lignes
aléatoires de validation ont une série vue dans le train et environ 65 % des
points Charpy partagent les mêmes conditions de soudage. Ces contrôles
étayent deux usages distincts des scores, pas une certification IID.

Les 40 pipelines exportées sont rechargées dans un Python indépendant de leurs
définitions de notebook ; les 20 modèles externes reproduisent toutes leurs
prédictions OOF. Le contrôle indépendant recalcule les scores, vérifie les
choix internes, les frontières inductives, les IDs et les hashes des modèles,
du brut, des sources et des CSV. Trente tests ciblés passent. Aucun algorithme
semi-supervisé n'est exécuté ; les pools traction sont prêts, le pool Charpy
avec température connue est vide.

## Exports groupés et préparation de COREG — 2026-10-10

À la demande de Salh, le notebook autonome `06_grouped_exports.ipynb` complète
les exports avec le protocole groupé **16/médiane**. Il réajuste les quatre
familles avec les paramètres déjà choisis dans les plis internes de 04, vérifie
toutes leurs prédictions OOF, ajoute la baseline médiane sur les mêmes plis et
exporte les 20 modèles sélectionnés par MAE interne. Les cinq familles sont
ensuite réglées par GroupKFold5 sur les séries des labels complets, sans shuffle,
puis réentraînées sur tous ces labels : 20 refits supplémentaires.

Les dossiers modèles aléatoires et groupés sont distincts, chacun avec
`outer_selected/`, `full_fit/` et `selected_models.json`. Les modèles historiques
13/itérative de 03 ne sont pas renommés en 16/médiane. Les refits complets
ont vu tous les labels : ils ne peuvent pas initialiser une évaluation
semi-supervisée ; repartir du train du pli. Les groupes du pool inductif groupé
sont également exclus de la validation externe et interne.

### Choix encore nécessaires pour COREG

Historique du cadrage avant autorisation ; les décisions désormais appliquées
sont consignées dans la section suivante « COREG autorisé ».

Les cibles, les entrées et les accès aux pools sont définis. COREG original
utilise deux kNN sur les mêmes entrées avec deux distances ; aucune séparation
chimie/procédé n'est requise. La confiance est estimée par un gain local d'erreur
quadratique dans le train courant, pas une probabilité ni un score de validation.
[Zhou et Li, IJCAI 2005](https://www.ijcai.org/Proceedings/05/Papers/0689.pdf),
équation 2 et tableau 1. Utiliser RF et SVR serait une autre variante.

**Cadrage proposé, non implémenté ni validé expérimentalement :**

| Choix | Proposition de démarrage |
| --- | --- |
| Cibles | Trois COREG séparées : YS, UTS, allongement ; pool naturel Charpy vide |
| Régresseurs | Deux kNN uniformes sur les mêmes 16 entrées + procédé ; distances L1 et L2 |
| Voisins | Même k pour les deux, grille 3/5/9/15, choix par MAE interne |
| Prétraitement | Médiane/standardisation/encodage appris sur les vrais labels du train, figés pendant la boucle |
| Vrais labels | Tous les labels du train dans l'essai principal ; 25/50 % possibles en sensibilités distinctes |
| Candidats par tour | Au plus 100, tirage reproductible seed42 dérivé de cible et pli, parmi le pool autorisé |
| Acceptation | Gain local positif ; au plus un ajout par kNN et par tour, transmis à l'autre kNN |
| Arrêt | Maximum 100 tours, pool épuisé ou aucun ajout accepté ; jamais sur labels de validation |
| Prédiction | Moyenne des deux régresseurs |
| Contrôles | kNN seuls et moyenne des deux sans pseudo-labels, mêmes labels/X/plis ; meilleurs supervisés en référence |
| Évaluation | Protocoles aléatoire et groupé séparés, 5 externes/3 internes ; MAE, RMSE, R² et différences appariées |

Il reste à rendre explicites la tolérance numérique du gain positif, la résolution
des égalités/collisions, le voisinage du score local (incluant ou non les
pseudo-labels déjà ajoutés) et la gestion des signatures X répétées : quota,
pondération ou conservation des répétitions avec audit. Une signature partielle
n'est pas une identité physique prouvée. Aucun même raw ID ne doit être ajouté
plusieurs fois ; journaliser ID, origine/destination, valeur estimée et gain.
Les valeurs proposées fixent un budget de départ, pas des hyperparamètres
prouvés optimaux sur les soudures.

Les 849/878/924 candidats naturels traction concernent toute la cohorte ; seuls
ceux permis dans le train courant peuvent être utilisés. Pour Charpy, masquer
des labels **du train uniquement** pourrait créer un test simulé, à distinguer
d'un pool naturel absent. Aucun label interne/externe de validation ne sert au
fit ou au calcul de confiance ; les internes ne servent qu'au tuning après
apprentissage de chaque candidat. COREG reste à implémenter après ce cadrage.

## COREG autorisé : protocole figé avant calcul — 2026-10-10

Salh demande désormais l'implémentation et les entraînements. Notebook autonome
`07_coreg.ipynb` : trois cibles traction, deux protocoles, 16 entrées + procédé,
médiane, tous les vrais labels du train et pools **naturels** exclusivement.
Charpy reste hors de cet entraînement : pool naturel vide avec température connue.
Les expériences à 25/50 % de labels sont des sensibilités futures, pas ce calcul.

Deux kNN uniformes, distances L1/L2, même k sélectionné dans 3/5/9/15 sur MAE
interne. Prétraitement ajusté sur les vrais labels de chaque train, figé pendant
la boucle et partagé à l'identique avec les contrôles. Confiance : somme locale
des réductions d'erreur quadratique après insertion temporaire de sa propre
prédiction dans le régresseur source ; voisinage dans le jeu courant, incluant
les pseudo-labels déjà ajoutés. Uniformité des kNN permet une mise à jour exacte
du voisin remplacé, vérifiée contre le refit explicite dans les tests.

Variante explicitement identifiée : le pool transformé est dédupliqué par X
exact et les X déjà représentés dans le vrai train sont retirés ; garder le raw
ID minimal comme représentant. Cela évite de surpondérer des représentations
répétées, sans certifier l'identité physique des soudures. Les vrais labels
répétés restent tous conservés. Cette variante de gestion du pool et L1/L2
diffère des paramètres expérimentaux p2/p5 du papier original.

Ordre immuable de tie-break : positions des vrais labels triés par raw ID,
puis représentants du pool triés par raw ID. Candidats examinés : au plus 100,
tirage avec seed dérivée de cible/pli/contexte, pool actif conservé et recomplété
après chaque tour. Régresseur L1 sélectionne d'abord ; sa sélection est retirée
avant L2 ; les deux échanges se font après ces sélections. Au plus un ajout
par source/tour, sans réutilisation d'ID. Gain accepté strictement supérieur à
`1e-12 * max(1, variance(y_train)) * k` ; égalité à cette tolérance départagée
par position immuable. Au plus 100 tours ; arrêt pool épuisé ou aucune acceptation
dans le pool actif. Cet arrêt ne garantit pas l'absence de candidat utile dans
la partie non examinée du pool. Aucun label de validation pour confiance/arrêt.

Plis externes/internes des notebooks 02/05 inchangés : cinq externes, trois
internes. À chaque candidat interne, reconstruire le preprocessing et limiter
le pool à ce train interne. Contrôles : kNN L1 seul, L2 seul, moyenne L1/L2
réglés indépendamment, **moyenne sans pseudo-labels au même k que COREG** pour
isoler l'effet du pool, et sélection supervisée existante à titre de référence.
Même validation externe par raw ID pour toutes les méthodes.

Refits complets : nouvelle sélection CV5 seed1042 aléatoire ou GroupKFold5 sur
les séries des labels ; les U des séries étiquetées suivent leur groupe et les
groupes sans label reçoivent une affectation équilibrée seed1142. Les U aléatoires
reçoivent cinq blocs équilibrés seed1142. Exporter COREG et ses contrôles
appariés/tunés avec metadata, preprocessing, journal des pseudo-labels et hashes.
Les modèles complets restent séparés des modèles de trains externes.
Graines : 42 dans le protocole ; graines effectives dérivées du type de CV,
de la cible, du pli et du contexte. Une sensibilité externe aux bases 43/44,
avec k fixé par les internes du calcul principal, mesure l'effet du tirage sans
choisir la meilleure graine sur les scores externes.

## Résultats COREG exécutés — 2026-10-10

Notebook 07 exécuté entièrement : 180 évaluations externes, 576 fits COREG
en comptant choix internes, CV/refits complets et sensibilité aux bases 43/44.
108 nouvelles pipelines exportées (90 externes, 18 complètes), séparées pour
les validations aléatoire et groupée, avec preprocessing et contrôles.

| Validation | Cible | MAE COREG | R² COREG | MAE même k | MAE sélection supervisée |
| --- | --- | --- | --- | --- | --- |
| random | yield_strength | 37.919 | 0.629 | 38.241 | 31.630 |
| random | uts | 33.037 | 0.709 | 33.319 | 23.861 |
| random | elongation | 2.402 | 0.535 | 2.392 | 2.054 |
| grouped | yield_strength | 71.074 | -0.056 | 70.817 | 56.757 |
| grouped | uts | 63.060 | 0.043 | 62.081 | 54.344 |
| grouped | elongation | 3.904 | -0.028 | 3.879 | 3.517 |

Les R² sont les moyennes des cinq plis, distinctes des R² OOF.
Les gains MAE OOF face au même k ne sont positifs que pour YS/UTS en aléatoire,
avec intervalles bootstrap descriptifs couvrant zéro ; les trois gains groupés
sont négatifs. COREG reste moins performant que la sélection supervisée dans
les six cas. Il constitue une expérience semi-supervisée évaluée ; les modèles
supervisés restent la référence principale pour cette cohorte et ce budget.
Les kNN groupés sans pseudo-labels sont eux-mêmes faibles : le gain local
d'entraînement ne résout pas le transfert entre séries. Les labels de U restent
inconnus, donc aucun taux d'exactitude des pseudo-labels n'est inventé.

Ces résultats sont rétrospectifs après le choix 16/médiane ; ils ne représentent
pas une nouvelle validation indépendante de toute la sélection. Le protocole
et le budget de 100 tours restent ceux fixés avant calcul ; aucun réglage n'est
modifié pour améliorer les validations observées. Les refits complets sont
destinés à l'inférence et ne peuvent servir aux évaluations de plis.
37 tests ciblés passent. Scores, graines, pseudo-labels, arrêts et audits sont
documentés dans [le rapport COREG](../reports/14_coreg_training.md).

## Rapports de synthèse — 2026-10-10

La [synthèse globale en français](../reports/15_synthese_globale_resultats_fr.md)
consolide les résultats supervisés, les diagnostics et COREG, en distinguant
le benchmark initial 13/itérative des procédures actuelles 16/médiane.
La [première version du rapport du projet](../reports/16_rapport_projet_v1_fr.md)
est accompagnée d'un [PDF de cinq pages](../output/pdf/rapport_projet_v1_fr.pdf).
Les tableaux sont issus des CSV exécutés ; l'ACP reste descriptive et les
limites de la validation rétrospective et de Charpy sont explicites.

L'équipe comporte trois membres, confirmés par l'utilisateur : Mohamed SALH,
Mohamed CHEBLI et Idriss BEN LETAIFA. Le numéro d'équipe et le Gantt réel
(dates, partage des tâches, heures) ne sont pas encore renseignés. La trame
du rapport ne leur attribue aucun travail ni aucune durée sans information.

## Extension XGBoost autorisée — 12 octobre 2026

L'utilisateur demande l'entraînement et l'intégration aux benchmarks/rapports.
Le notebook `08_xgboost.ipynb` ajoute une sixième famille supervisée aux
comparaisons **16/médiane** aléatoire et groupée, quatre cibles et mêmes labels,
plis externes/internes des notebooks 02/05/06. Les expériences historiques
13/itérative et les sensibilités 11/13/16 ne sont pas renommées ni recalculées.

Choix figés avant calcul : XGBRegressor, objectif `reg:squarederror`, booster
`gbtree`, `tree_method=hist`, CPU, graine42, un thread par estimateur ; grille
profondeur={2,4,6}, learning_rate={0,03;0,1}, n_estimators={150,300}, soit
12 configurations comme RF/SVR. Fixes : min_child_weight=5, subsample=0,8,
colsample_bytree=0,8, reg_lambda=1, reg_alpha=0, gamma=0, max_bin=256.
Les petits arbres et la régularisation limitent la complexité pour ces effectifs ;
cette grille modeste ne prétend pas couvrir tous les réglages de XGBoost.
L'objectif quadratique diffère de la MAE utilisée pour sélectionner les paramètres.
[Référence des paramètres XGBoost](https://xgboost.readthedocs.io/en/stable/parameter.html),
consultée le 12 octobre 2026.

Le preprocessing commun est réajusté dans chaque train interne/externe ; les
NaN sont imputés par médiane, sans exploiter la gestion native de XGBoost, pour
comparer les familles à préparation identique. Aucun early stopping ni eval_set
externe ; les labels de validation ne participent ni à l'ajustement, ni à l'arrêt.
Aucune cible et aucune température Charpy inconnue ne sont imputées. Les unités,
encodages de manquants et définitions des sorties restent ceux du master.

La sélection est recalculée entre six familles par leur MAE interne, avec ordre
historique puis XGBoost pour les égalités. Nouvelle CV5 de choix complet : KFold
seed1042 sur les labels triés ou GroupKFold5 sans shuffle. Les résultats des cinq
familles sont réutilisés après vérification des hashes, paramètres/choix internes,
IDs et prédictions ; les exports sélectionnés historiques sont préservés.
Un nouvel index sous `models/salh_xgboost_v1/` référence les six familles.
La comparaison COREG garde ses entraînements/contrôles inchangés et actualise
seulement la référence supervisée. MAE/RMSE/R² par pli et OOF sont enregistrés.
Cette extension postérieure aux diagnostics demeure une comparaison rétrospective,
sans nouvelle validation indépendante ni recommandation métallurgique causale.

### Résultats XGBoost exécutés — 12 octobre 2026

| CV | Cible | MAE ± SD | RMSE moyen | R² ± SD | MAE OOF | R² OOF |
| --- | --- | --- | --- | --- | --- | --- |
| Aléatoire | YS (MPa) | 26,334 ± 2,735 | 39,147 | 0,816 ± 0,043 | 26,327 | 0,815 |
| Aléatoire | UTS (MPa) | 22,542 ± 2,245 | 34,863 | 0,845 ± 0,044 | 22,543 | 0,846 |
| Aléatoire | Allongement (points de %) | 2,021 ± 0,146 | 2,858 | 0,654 ± 0,039 | 2,021 | 0,655 |
| Aléatoire | Charpy* (J) | 14,151 ± 0,724 | 19,707 | 0,845 ± 0,026 | 14,150 | 0,847 |
| Groupée | YS (MPa) | 54,363 ± 9,820 | 70,263 | 0,367 ± 0,167 | 55,147 | 0,383 |
| Groupée | UTS (MPa) | 50,215 ± 6,720 | 65,165 | 0,392 ± 0,178 | 49,581 | 0,477 |
| Groupée | Allongement (points de %) | 3,322 ± 0,381 | 4,196 | 0,238 ± 0,148 | 3,297 | 0,263 |
| Groupée | Charpy* (J) | 35,450 ± 11,126 | 45,293 | 0,069 ± 0,247 | 35,571 | 0,161 |

Sélection à six familles, uniquement sur MAE interne :

| Cible (unité) | MAE aléatoire | R² aléatoire | MAE groupée | R² groupé |
| --- | --- | --- | --- | --- |
| YS (MPa) | 26,334 | 0,816 | 54,363 | 0,367 |
| UTS (MPa) | 23,604 | 0,830 | 55,691 | 0,307 |
| Allongement (points de %) | 2,064 | 0,646 | 3,278 | 0,260 |
| Charpy* (J) | 14,151 | 0,845 | 36,267 | 0,058 |

| CV de choix | Cible | Famille | MAE de sélection | Paramètres |
| --- | --- | --- | --- | --- |
| Aléatoire | YS (MPa) | XGBoost | 26,698 | {"model__learning_rate": 0.1, "model__max_depth": 6, "model__n_estimators": 300} |
| Aléatoire | UTS (MPa) | XGBoost | 21,609 | {"model__learning_rate": 0.1, "model__max_depth": 6, "model__n_estimators": 300} |
| Aléatoire | Allongement (points de %) | XGBoost | 1,919 | {"model__learning_rate": 0.1, "model__max_depth": 6, "model__n_estimators": 150} |
| Aléatoire | Charpy* (J) | XGBoost | 13,437 | {"model__learning_rate": 0.1, "model__max_depth": 6, "model__n_estimators": 300} |
| Groupée | YS (MPa) | XGBoost | 57,742 | {"model__learning_rate": 0.1, "model__max_depth": 2, "model__n_estimators": 150} |
| Groupée | UTS (MPa) | SVR RBF | 46,555 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| Groupée | Allongement (points de %) | XGBoost | 3,252 | {"model__learning_rate": 0.1, "model__max_depth": 2, "model__n_estimators": 300} |
| Groupée | Charpy* (J) | Random Forest | 32,375 | {"model__max_depth": 10, "model__max_features": 0.5, "model__min_samples_leaf": 1} |

XGBoost améliore la MAE moyenne des quatre cibles en aléatoire. En groupé,
RF reste plus faible pour YS/UTS/Charpy ; XGBoost a une légère amélioration
d’allongement. Ce constat descriptif ne remplace pas le choix interne et ne
démontre ni significativité ni causalité. COREG reste moins performant que
la sélection à six dans les six cas traction/protocole ; ses gains au même k
et ses entraînements sont inchangés. Charpy demeure exploratoire.

40 évaluations XGBoost terminées ; 480 configurations internes et 96 CV5
complètes, 1 968 fits XGBoost. 280 évaluations supervisées réunies et métriques
recalculées ; 88 nouveaux exports rechargés dans un processus neuf,
11580 prédictions vérifiées (écart maximal 1.14e-13).
Total des exports locaux : 276. 41 tests rapides passent.
Python 3.14.8, XGBoost 3.4.1, scikit-learn 1.9.1.
Durée notebook : 1.40 minutes, sans heures humaines inférées.
[Rapport détaillé et fichiers](../reports/17_xgboost_training.md).

L'ajout d'une famille ne garantit pas l'amélioration de la procédure de
sélection : sa MAE externe baisse dans cinq des huit comparaisons. Elle augmente
pour l'allongement aléatoire (2,054 → 2,064), UTS groupé (54,344 → 55,691)
et Charpy groupé (35,752 → 36,267). Ces choix proviennent des scores internes,
sans correction après lecture des validations externes.

