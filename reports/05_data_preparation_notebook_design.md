# Résultats complémentaires et contenu du futur notebook de préparation

Date : 8 octobre 2026. Le choix de l'imputation itérative est fixé par
l'utilisateur. Ce document précise les variables, les contrôles et les exports
du futur notebook ; il ne crée pas encore ce notebook et ne produit aucun
modèle prédictif. Il actualise le plan du rapport 04, qui proposait encore de
comparer plusieurs familles d'imputation.

## Travail effectué et reproductibilité

Relecture du brut et des ambiguïtés par série ; simulations de filtres de
complétude ; contrôle de convergence sur six variantes ; nouveau benchmark
ITÉRATIF SEULEMENT sur 11, 13 et 16 variables ; convergence complémentaire sur
les observations étiquetées de chaque cible de traction initiale.

Résultats locaux, recettes exécutables et manifestes :
`data/processed/preparation_audit_2026-10-08/`, ignoré par Git. Reproduction,
depuis la racine avec les dépendances du projet :

```bash
.venv/bin/python data/processed/preparation_audit_2026-10-08/weld_preparation_audit.py
.venv/bin/python data/processed/preparation_audit_2026-10-08/weld_iterative_screen.py
```

Le premier script contrôle la convergence ; le second effectue le benchmark et
les contrôles par cible. Le tableau `row_filter_sensitivity.csv` et les audits
de source/Charpy sont des vérifications descriptives complémentaires. Le brut
reste intact ; aucun label n'est fourni comme entrée à l'imputer.

## 1. Ensembles de variables à comparer

| Nom | Variables numériques | Usage proposé |
| --- | --- | --- |
| B11 | C, Si, Mn, S, P, courant, tension, apport thermique, température entre passes, température PWHT, durée PWHT | Contrôle compact, continuité avec l'EDA |
| B13 | B11 + O et N | Candidate principale de préparation |
| B16 | B13 + Ni, Cr, Mo | Variante enrichie à comparer |
| B21 | B16 + V, Cu, Ti, Al, Nb | Analyse secondaire ; non retenue initialement avec l'imputer actuel |

Les noms de code exacts et paramètres figurent dans les manifestes locaux. Le
procédé `weld_type` est utilisé comme auxiliaire catégoriel dans l'imputation
itérative et pourra également être fourni au modèle prédictif. Il s'ajoute au
nombre de variables numériques affiché.

Exclusions du premier jeu d'entrées : Co, W, Sn, As, Sb, bore, microstructure,
dureté, FATT, identifiant et groupe. Les propriétés mécaniques autres que la
cible ne sont pas fournies au modèle. Cu, V, Ti, Al, Nb restent disponibles pour
des variantes dédiées plutôt que d'être déclarés physiquement inutiles.

Ce choix repose sur le périmètre de prédiction, le support des données et les
contrôles réalisés. Une sélection par pouvoir prédictif n'a pas encore été
effectuée. Il ne s'agit pas d'une liste universelle des variables essentielles
à la qualité de toutes les soudures.

## 2. Nouveau contrôle de l'imputation itérative

Protocole : quatre répétitions exactes hors identifiant retirées, groupes
conservés avant suppression, règles de préparation actuelles sans correction
d'unité, 3 plis GroupKFold, seed du modèle 42, BayesianRidge par défaut,
`max_iter=100`, `tol=1e-3`. Les filtres ci-dessous comptent les cellules restant
indisponibles APRÈS substitutions déterministes ; les approximations de censure
ne sont pas comptées comme manquantes, mais leur incertitude reste à considérer.

| Variante | Lignes | Groupes | Cellules à estimer | Convergence sur 3 plis |
| --- | ---: | ---: | ---: | --- |
| B11, toutes les lignes dédupliquées | 1 648 | 47 | 2,96 % | 3/3, 4/6/9 itérations |
| B13, toutes les lignes dédupliquées | 1 648 | 47 | 6,53 % | 3/3, 4/8/26 itérations |
| B13, au plus 2 cellules indisponibles par ligne | 1 555 | 44 | 5,32 % | 3/3, 4/4/4 itérations |
| B16, toutes les lignes dédupliquées | 1 648 | 47 | 15,44 % | 3/3, 20/42/30 itérations |
| B16, au plus 3 cellules indisponibles par ligne | 1 284 | 40 | 11,62 % | 3/3, 14/38/8 itérations |
| B21, toutes les lignes dédupliquées | 1 648 | 47 | 23,93 % | 0/3, plafond atteint dans tous les plis |

Le retrait du bore ne suffit donc pas à rendre l'extension convergente.
L'extension n'est pas seulement affectée par le nombre de colonnes ; support
par série, censure, dépendances, échelles et ajustement statistique contribuent
au problème. Aucun rôle causal précis de chaque colonne n'a été établi.

### Reconstruction sur les mêmes valeurs cachées

Pour B11/B13/B16 non filtrés : mêmes lignes, mêmes plis, graines de masquage
42/43, taux 10/20/40 %, cellules et blocs empiriques. Les masques sont générés
sur B16 puis restreints au sous-espace de chaque candidat : les cellules cachées
des variables communes sont exactement les mêmes. Les patterns empiriques
proviennent exclusivement des groupes d'entraînement.

| Matrice de l'imputer | MAE normalisée moyenne sur les seules 11 variables communes |
| --- | ---: |
| B11 | 0,7651 |
| B13 | 0,7924 |
| B16 | 0,8816 |

Moyenne des lignes du fichier de métriques, soit des erreurs par variable,
pli, seed, taux et pattern disposant d'un support. Les scores sont sans unité,
normalisés par IQR d'entraînement avec repli sur l'écart-type. Leur agrégation
n'est pas une moyenne des erreurs physiques ni une métrique de prédiction de
qualité. Les nouveaux scores ne sont pas directement comparables au benchmark
EDA : déduplication, partitions et génération de masques ont changé.

Sur les 13 variables communes à B13/B16, la moyenne est respectivement 0,9840
et 1,0406. L'apport des variables supplémentaires ne réduit donc pas globalement
l'erreur de reconstruction des variables déjà présentes dans ce protocole.
En revanche, certaines variables en bénéficient : erreur d'azote 96,84 ppm pour
B13 contre 89,04 ppm pour B16, et température PWHT 241,86 °C contre 202,68 °C.
Ce ne sont pas des garanties de reconstruction des absences réelles.

L'erreur d'oxygène de B13 est 127,48 ppm en moyenne sur les scénarios scorés,
et celle d'azote 96,84 ppm. Ces erreurs invitent à examiner les procédés, séries
et différences de populations. La convergence n'est pas un certificat de
justesse. Les assertions confirment la conservation des cellules observées
non masquées et la séparation des groupes. Aucune estimation scorée ne dépasse
les bornes générales, qui restent trop larges pour valider la métallurgie.

La reconstruction de B13 filtré n'a PAS été benchmarkée dans cette exécution :
seuls couverture et ajustements/convergence y ont été contrôlés. Il serait
incorrect d'affirmer que son filtre améliore la précision.

### Convergence quand seules les lignes étiquetées servent à ajuster

Avec B13, B13 filtré et B16, l'imputer converge dans les trois plis pour chacune
des cibles `yield_strength`, `ultimate_tensile_strength`, `elongation` :
27 fits complémentaires, sans jamais utiliser les valeurs de ces labels.
Le maximum observé est 20 itérations pour B13, 15 pour B13 filtré et 74 pour B16.
Ces contrôles utilisent trois plis ; un protocole final à cinq plis doit
refaire ses propres contrôles. Les scores prédictifs restent à produire.

## 3. Combien de lignes faut-il garder ?

Il n'y a pas d'objectif obligatoire de 1 500 lignes, ni de garantie de fiabilité
à 700 ou 1 000. Il faut connaître le nombre de labels par cible, le nombre de
groupes indépendants et les sous-populations éliminées.

| Règle sur B13 | Lignes totales | Labels YS | Labels UTS | Labels allongement |
| --- | ---: | ---: | ---: | ---: |
| Aucune cellule indisponible après préparation | 948 | 425 | 409 | 358 |
| Au plus 2 cellules indisponibles | 1 555 | 706 | 677 | 631 |
| Au plus 3 cellules indisponibles | 1 603 | 748 | 719 | 668 |
| Toutes les lignes dédupliquées | 1 648 | 777 | 735 | 697 |

La première règle accepte les approximations de censure et d'intervalle : elle
n'est pas équivalente au sous-ensemble de mesures entièrement exactes.

Avec la règle à deux cellules, les labels YS représentent 40 groupes et les
labels d'allongement 34. Dans les contrôles à trois plis, cela laisse 235–236
labels et 12–14 groupes pour vérifier YS, et 210–211 labels et 10–12 groupes
pour vérifier l'allongement. C'est un effectif réel, pas une preuve que toutes
les sous-populations sont suffisamment couvertes. La validation croisée utilise
successivement les données comme observations réservées plutôt que de figer
une petite validation permanente.

Le filtre retire 93 lignes et perd entièrement trois groupes : Cunh-1982,
EvHtIp1979 et Natsume-1990 ; il retire aussi 19 lignes Gar&K-1975. Il modifie les
parts de procédés : SA passe de 260 à 227 lignes et MMA de 1 177 à 1 121 après
normalisation des synonymes. C'est une restriction de population, pas un simple
effacement de bruit.

Recommandation : exporter la table maître dédupliquée et un masque de fiabilité
par jeu d'entrées. Proposer B13 « au plus deux cellules indisponibles » comme
cohorte stricte, et conserver B13 complet comme comparaison de couverture. Le
seuil de deux est une règle d'ingénierie (au moins 11/13 entrées préparées), pas
une norme ni une mesure de certitude. Tester aussi la sensibilité aux bornes et
le support exact par groupe. Ne pas réduire arbitrairement le fichier à 700
lignes ; les cohortes étiquetées produisent déjà environ 600–700 observations.

Les comparaisons entre jeux d'entrées portent sur des lignes de validation
communes. Si une restriction modifie le domaine évalué, présenter ses résultats
séparément et ne pas attribuer tout gain au preprocessing. Les lignes sans
label sont conservées dans le pool semi-supervisé autorisé par les partitions.

## 4. Ambiguïtés d'unité : décision opérationnelle

La documentation Cambridge affecte C/Si/Mn/S/P/Ni/Cr/Mo/V/Cu/Co/W au pourcentage
massique, et O/Ti/N/Al/B/Nb/Sn/As/Sb aux ppm massiques. Une standardisation ne
corrige pas une unité erronée. La conversion, si une source confirme le besoin,
est 1 wt% = 10 000 ppm.

| Cas | Ce qui est établi | Action dans le futur notebook |
| --- | --- | --- |
| 10 valeurs Al 0,004–0,014, EPRI | Contraste d'ordre de grandeur ; le même groupe contient aussi 160 dans cette colonne | Conserver brut et alerte ; ne pas multiplier toute la série ; masquer les 10 cellules tant que le tableau source n'est pas confirmé |
| Sn/As/Sb sous 1 ppm, 90 lignes Mart/Ditt | Les trois éléments portent des petites valeurs dans les mêmes lignes | Exclure ces variables du modèle principal ; conserver les lignes et l'audit ; correction seulement par référence source |
| Ti 0,5, une ligne Stil-TiB | Une petite valeur dans la colonne ppm, sans preuve d'erreur | Garder le signalement dans l'audit ; hors B13/B16, pas de suppression de la ligne |
| Ti et Al `<0.01`, 16 lignes PantK | Deux limites identiques dans des colonnes documentées ppm | Masquer ces cellules dans une variante qui les utilise ; conversion conditionnelle seulement |
| V `<5`, 9 lignes EvansLetter | Limite suspecte pour une colonne wt% | Masquer la cellule dans la variante avec V ; ne pas appliquer `<5 → 2,5 wt%` |
| 59 annotations N `tot/res/nd` | Forme lexicale et localisation dans Evans-Al/CMn-1990 établies | Exporter les composantes ; pour B13 principal, garder la cellule N indisponible tant que sa comparabilité n'est pas confirmée ; `nd` ne devient pas zéro |

Les recherches externes ont identifié des références de travaux et confirmé
que les températures à énergie Charpy fixée sont utilisées dans la littérature.
Elles n'ont pas apporté de preuve suffisante pour corriger les cellules d'unité
ci-dessus ni pour certifier la comparaison des 59 annotations N avec toutes les
autres mesures de N. Aucune correction n'est présentée comme établie.

Les unités de B13 restent celles du dictionnaire initial : chimie de base en
wt%, O/N en ppm, courant A, tension V, apport thermique kJ/mm, températures °C,
durée PWHT h. Le statut incertain de N est traité par cellule. Les 610 couples
PWHT 0/0 restent observés sans affirmer que leur sémantique est vérifiée.

## 5. Charpy : E(T), T100J et T28J sont des tâches différentes

Après la déduplication proposée : 877 couples température/énergie numériques,
355 lignes à 100 J, 118 à 28 J, et 404 à d'autres énergies. Les 355 lignes à
100 J couvrent 15 groupes ; les 118 à 28 J seulement 6 groupes, dont une ligne
Mart qui peut être une énergie ordinaire observée et ne doit pas être classée
automatiquement comme température de transition.

La littérature primaire, notamment les articles d'Evans, utilise la température
correspondant à une énergie Charpy donnée. Cela étaye la nécessité d'une
classification des protocoles, mais ne fournit pas une correspondance certaine
pour chaque ligne du présent fichier. Le seul test `energy == 100` ou `28`
ne suffit pas : une courbe E(T) peut également passer par ces valeurs.

Construire une table d'audit par série et condition de soudure : énergie,
température, identifiants, nombre de valeurs distinctes, publication, page/table,
type de protocole et niveau de preuve. La catégorie par défaut est « non
résolu », et non « E(T) » par élimination. Une source peut aussi contenir
plusieurs types de records : vérifier le niveau observation/condition.

Après confirmation :

- E(T) : cible = énergie en J ; température d'essai en °C comme entrée connue.
- T100J : cible = température pour atteindre 100 J en °C ; ni cette température
  ni l'énergie constante 100 ne sont des prédicteurs.
- T28J : cible = température pour atteindre 28 J en °C ; même exclusion.

Pour T100J/T28J, regrouper les observations d'une même soudure et ses variantes
entre tâches et partitions. Ne pas fusionner les seuils ni fabriquer une
température de transition par interpolation de points insuffisants. Si la
classification des sources ne peut être terminée immédiatement, exporter
l'audit et les mesures, mais ne pas entraîner un modèle Charpy global ambigu.
Les régressions de traction peuvent commencer indépendamment.

Avec seulement six groupes candidats T28J avant confirmation, la taille de
118 ne justifie pas automatiquement une validation à cinq plis ni une forte
capacité de généralisation. Définir le nombre de plis après la classification
et l'inspection du support de chaque tâche.

## 6. Étapes exactes du notebook court de préparation

Nom proposé : `02_data_preparation.ipynb`. L'actuel squelette de modélisation
pourra devenir `03_modeling.ipynb` lors de la prochaine implémentation. L'EDA
reste le notebook d'explication générale ; le nouveau notebook exécute des
règles et montre uniquement des synthèses utiles à la préparation.

1. **Configuration et identité des données.** Schéma, unités, hashes, règles de
   nettoyage, ensembles B11/B13/B16, seed 42, paramètres de l'imputer.
2. **Audit et liens de groupes.** Utiliser les fonctions réutilisables du package,
   conserver un `raw_row_id` stable, construire les groupes avant déduplication.
3. **Déduplication.** Retirer les quatre occurrences excédentaires hors ID,
   conserver alias et journal de suppression ; pas de suppression par ID seul.
4. **Conversion déterministe des tokens.** N → NaN ; `<L` → L/2 seulement si
   concentration non négative et unité non signalée ; intervalle → midpoint ;
   annotations → champs séparés ; cellules non résolues → NaN avec raison.
   Conserver les bornes/statuts, mesures exactes, zéros et extrêmes valides.
5. **Contrôles de cohérence.** Unités, non-finitudes, bornes, YS≤UTS quand les
   deux sont mesurées, cohérence des couples PWHT et provenance. Une alerte
   déclenche examen et journal, pas une suppression automatique par IQR.
6. **Schémas et éligibilité.** Une table de labels par propriété, champs
   disponibles à la prédiction, taux de reconstruction par ligne, masques de
   cohorte stricte et comparaison de leur couverture par procédé/groupe.
7. **Table de protocoles Charpy.** Décisions E(T)/T100J/T28J source par source,
   sinon statut non résolu. Ne pas reporter cette température dans les entrées
   d'un modèle T100J/T28J ; l'autoriser explicitement pour E(T).
8. **Export pré-imputation.** Table maître propre mais avec NaN ; tables X/y
   par tâche, labels et masque non étiqueté, provenance, IDs, groupes, protocoles,
   exclusions, sets de variables et manifeste. Données dans `data/processed/`.
9. **Contrôle itératif ciblé.** Reproduire le benchmark sur les cohortes retenues,
   avec groupes, exacts masqués, taux/scénarios, convergence, erreurs natives et
   normalisées, distributions par procédé et bornes. Le choix de la méthode
   reste itératif ; ce contrôle choisit le périmètre et vérifie sa faisabilité.
10. **Partitions et contrat avec la modélisation.** Enregistrer les partitions
    par groupes et les paramètres de la pipeline ; exporter un résumé compact
    des effectifs et limites. Les règles apprises ne sont pas figées à partir
    des groupes réservés.

Toute nouvelle fonction réutilisable va dans `src/weld_quality/`. Le notebook
appelle ce code et interprète les tableaux ; il ne recopie pas un deuxième EDA.

## 7. Étapes exactes de l'imputation pour l'entraînement

Pour chaque cible, candidat d'entrées et pli :

1. Choisir les lignes étiquetées éligibles et séparer les groupes. Les cibles
   absentes restent non étiquetées ; elles ne passent pas dans l'imputer.
2. Sur le training autorisé uniquement, ajuster la standardisation numérique
   nécessaire à l'imputer et l'encodage du procédé. Un code de groupe/ID n'est
   pas une entrée du modèle.
3. Ajuster l'itérative : initialisation médiane, BayesianRidge, seed 42,
   tolérance 1e-3, plafond 100, bornes générales. L'initialisation médiane n'est
   pas une remise en question du choix de méthode.
4. Transformer training, validation et test avec CE fit ; maintenir les mesures
   non manquantes intactes et projeter les couples PWHT absents sur les couples
   d'entraînement compatibles comme dans le code existant.
5. Vérifier convergence, valeurs finies, bornes, provenance et support. Aucune
   colonne entièrement absente dans l'entraînement ne reçoit une médiane
   inventée. Une absence de convergence ne devient pas silencieusement un fit
   accepté ; réviser le candidat à partir de l'entraînement/validation interne.
6. Ajuster ensuite les transformations et le modèle prédictif sur le training.
   Tout réglage des variables, paramètres, filtres et substitutions guidé par
   le score reste interne ; les plis externes évaluent la procédure figée.

Le benchmark réalisé ici est une investigation de reconstruction sur entrées,
avec un espace commun et des masques contrôlés. Le choix final de B11/B13/B16
pour prédire une propriété doit aussi être évalué sans réutiliser les labels
externes pour le réglage.

Pour la semi-supervision inductive, les observations non étiquetées viennent
uniquement des groupes d'entraînement. Par défaut, ajuster l'imputer initial
sur les mêmes lignes étiquetées que le comparateur supervisé, puis transformer
le pool autorisé ; un autre choix doit être annoncé et évalué séparément.

Un export intégralement imputé sur toutes les données peut servir à l'exploration
ou à l'ajustement final après évaluation. Il n'est pas l'entrée de référence
pour la validation croisée. Pour des fichiers entièrement numériques destinés
aux expériences, exporter par cible ET pli : X_train imputé, X_validation
transformé par le fit du train, y et IDs séparés, avec un manifeste du fit.
Dans une validation imbriquée, les plis internes doivent refaire l'imputation
sur leur propre training ; un export imputé au niveau externe n'est donc pas
réutilisé tel quel pour ajuster les hyperparamètres internes.

## Références et limites

- [Cambridge MAP_DATA_WELD](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html) : unités, origine et `N`.
- [scikit-learn IterativeImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.IterativeImputer.html) : initialisation, convergence, paramètres et limites.
- [Evans, Effect of Aluminum and Nitrogen on Ti-B Containing Steel Welds, Welding Journal 1997](https://citeseerx.ist.psu.edu/document?doi=2bf148923f635a2095ff0d3963da62dd1b8561c9&repid=rep1&type=pdf) : exemple primaire de température correspondant à 100 J, sans attribution automatique aux lignes de 1990–1994.
- [Lalam et al., Estimation of mechanical properties of ferritic steel welds, part 2, 2000](https://www.phase-trans.msm.cam.ac.uk/abstracts/harsha2.pdf) : modélisation des propriétés et de l'énergie Charpy avec conditions d'essai. Le lien antérieur `harsha4.html` concerne le fluage, pas la transition Charpy.

Pas de nouvelle correction d'unité prouvée, pas de définition universelle de
qualité, pas de performance prédictive ni d'assertion que la censure, les vraies
absences ou la convergence sont pleinement validées par ce screening.
