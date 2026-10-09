# Spécification du projet — préparation et plan d’expériences

Mise à jour : 9 octobre 2026. L’énoncé original est préservé dans
[sujet.md](../sujet.md). Cette spécification décrit le protocole actif ; les
anciens essais et audits sont référencés à la fin, sans constituer le code courant.

## Objectif et état actuel

Prédire des propriétés mécaniques de soudures à partir de leur composition et
paramètres renseignés, puis comparer des méthodes supervisées et au moins une
méthode semi-supervisée. Une propriété mécanique représente un aspect de la
qualité ; aucun score universel ou seuil de bonne/mauvaise soudure n’est inventé.
La disponibilité effective des entrées dans le scénario d’utilisation doit être
explicitée avant une recommandation pratique.

**La phase de préparation est terminée pour démarrer les benchmarks de traction.**
Le portefeuille supervisé et les budgets initiaux sont définis ci-dessous.
Les réglages, l’implémentation semi-supervisée et les conclusions pratiques
restent à valider. La préparation ne prouve pas une forte performance prédictive.

## Organisation retenue

À la demande explicite de l’utilisateur, le code d’analyse est directement dans
les notebooks autonomes ; cette décision remplace la préférence initiale pour
un package `src/weld_quality/`.

| Notebook | Responsabilité |
| --- | --- |
| `01_eda.ipynb` | Structure, statuts, distributions, dépendances, propriétés et ACP descriptive |
| `02_data_preparation.ipynb` | Parsing, provenance, déduplication, groupes, cohortes, plis, preprocessing et contrôle d’imputation |
| `03_modeling.ipynb` | Chargement vérifié des exports, partitions par cible et préparation des choix de méthodes ; entraînements finaux à ajouter ici |

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

## Modèles, métriques et prochaine phase

Le contrôle existant utilise une constante à la médiane de y, Ridge alpha=1 et
Random Forest 300 arbres/min_samples_leaf=2/graine42. Il est à paramètres fixes,
sans sélection finale et sans tuning interne. MAE moyennes RF/itérative :
66,13 MPa (YS), 56,71 MPa (UTS), 3,55 points de % (allongement) ; R² moyens
0,0765, 0,1899, 0,1136. L’itérative n’est pas uniformément meilleure ; les causes
des performances modestes ne sont pas isolées. Voir le rapport 07.

Métriques : MAE = moyenne de |y−prédiction| ; RMSE = racine de la moyenne des
écarts au carré ; R² = 1−somme des écarts au carré/somme des écarts à la moyenne
observée au carré. MAE/RMSE sont en MPa ou points de %, R² sans unité. Le contrôle
actuel rapporte moyenne non pondérée et écart-type des cinq plis ; conserver
les scores par pli et les effectifs. Ces écarts-types ne sont pas des IC.

Plan du 9 octobre, configuré dans `03_modeling.ipynb`, sans nouveaux scores :

| Méthode | Raison du comparateur | Budget initial par train externe |
| --- | --- | --- |
| Médiane de y du train | Gain minimal à dépasser | Aucun réglage |
| Ridge | Relation linéaire régularisée, comparateur simple | 6 alpha : 0,01 ; 0,1 ; 1 ; 10 ; 100 ; 1 000 |
| SVR RBF | Comparateur à noyau non linéaire | C={1,10,100}, gamma={scale,0,05}, epsilon={0,05,0,2}, soit 12 configurations |
| Random Forest | Interactions non linéaires par arbres | 300 arbres, leaf={1,2,5}, depth={None,10}, max_features={0,5;1}, soit 12 configurations |
| kNN supervisé | Contrôle de la future semi-supervision | k={3,5,9,15}, p={1,2}, poids uniformes, soit 8 configurations |

Les grilles sont des budgets de départ, pas des valeurs optimales établies.
La SVR standardise aussi y sur le train uniquement ; ses prédictions sont
reconverties en MPa/points de %. Les autres modèles gardent y dans son unité.
MAE interne moyenne non pondérée des trois plis = critère de réglage ; conserver
RMSE et R² pour l’analyse externe. A1_13 + imputation itérative sont fixés pour
la première comparaison. La médiane d’imputation reste un contrôle documenté,
pas une option sélectionnée sur les scores externes. L’adéquation du portefeuille
aux méthodes effectivement vues en cours reste à vérifier.

Les schémas A0_11 et A1b_16 seront des sensibilités sur les mêmes lignes
`in_strict13`, mêmes labels et mêmes plis. Le schéma 16 n’autorise pas un filtre
supplémentaire pour améliorer ses scores ; une absence complète dans le train
ou une non-convergence doit être rapportée. Si le jeu d’entrées ou la famille
de modèle est optimisé, ce choix fait partie de la recherche interne. Choisir
le meilleur tableau externe puis annoncer son score comme une estimation
indépendante de la sélection serait optimiste. Voir
[l’exemple de validation imbriquée scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

Au moins une méthode semi-supervisée est exigée par le sujet. COREG est retenu
comme candidat à implémenter et contrôler, pas comme méthode déjà entraînée.
Il utilise deux régressions kNN à distances différentes et un échange de
pseudo-labels sélectionnés ; source primaire :
[Zhou et Li, IJCAI 2005](https://www.lamda.nju.edu.cn/publication/ijcai05.pdf).
Les pseudo-labels ne sont pas des mesures ; aucun gain sur cette base n’est acquis.
Protocole prévu : inductif, pools venant uniquement des groupes du train concerné (interne
comme externe), aucun label de validation dans le fit ou les pseudo-labels.
Comparer au pendant supervisé avec les mêmes labels d’entraînement et les mêmes
deux régressions/agrégation, sans pseudo-labels, en plus du kNN simple. Pour isoler
l’ajout de pseudo-labels, le premier protocole ajuste le preprocessing sur le
train étiqueté uniquement, puis transforme le pool autorisé sans refit. Les
autres propriétés connues d’une ligne du pool ne deviennent ni entrées ni labels
de la cible manquante. Réglages et limites d’itérations de COREG restent à définir
avant son évaluation ; ils ne sont pas déduits des scores externes.

Définitions des méthodes supervisées : documentation officielle
[Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html),
[SVR](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html),
[Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

Exports futurs : prédictions externes par ID brut/cible/pli, métriques, effectifs,
paramètres choisis, jeu d’entrées, imputation, seed, versions, hashes des données
et du code. Datasets d’expérience sous `data/processed/experiments/`, modèles
sous `models/`, tableaux et figures commentés dans les rapports.

## ACP, preuves et limites

EDA active : ACP standardisée sur 1 339 lignes dédupliquées dont les onze entrées
sont des nombres exacts complets, sans imputation. PC1=27,02 %, PC2=19,03 %,
cumul=46,05 %. Cette sous-population ne représente pas automatiquement toute
la base ; l’ACP descriptive n’est pas réutilisée pour scorer les modèles.

Les huit CSV migrés reproduisent les exports AI corrigés, scores compris.
Les trois notebooks ont été exécutés séquentiellement par Python, de haut en bas,
depuis `notebooks/` ; cette vérification ne teste pas l’interface Jupyter.
Quinze tests ciblés hors ligne passent. Les fichiers bruts et `sujet.md` restent
préservés. Les versions sont enregistrées au manifeste à chaque préparation.

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

Les sources AI originales sont sauvegardées au commit `2ecb088` et retirées de
l’arborescence active. Les artefacts fournis restants dans `ai_prepared/` sont des
références locales ignorées, sans rôle dans l’exécution du protocole courant.
