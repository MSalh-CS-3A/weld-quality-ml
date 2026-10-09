# Plan d’expériences — 9 octobre 2026

Les décisions scientifiques actives sont dans [specs/spec.md](../specs/spec.md).
Ce document précise le passage de la préparation à l’entraînement ; aucun nouveau
score prédictif n’est annoncé. Le notebook [03_modeling](../notebooks/03_modeling.ipynb)
configure les estimateurs non ajustés et les grilles, sans lancer les recherches.

## Ce qui est prêt, ce qui reste à apprendre

La préparation ne se limite pas à un benchmark : parsing, unités douteuses,
provenance, déduplication, cohortes, groupes et splits sont exportés. Les contrôles
ont déjà entraîné Ridge et Random Forest avec imputation médiane/itérative à
paramètres fixes. En revanche, le master nettoyé garde les absences : 607 lignes
de la cohorte ont au moins une entrée numérique manquante, soit 1 075 cellules.

Il ne faut pas imputer globalement avant de découper les données. Chaque essai
interne ajuste imputation, échelles et catégories dans son train étiqueté, puis
transforme sa validation sans nouvel ajustement. Après réglage, la pipeline est
réajustée sur le train externe et évaluée sur le pli externe. Les sorties absentes
restent inconnues. La pipeline définitive sera réajustée après les comparaisons.

## Compromis d’entrées retenu

Référence : A1_13 (C, Si, Mn, S, P, courant, tension, apport thermique, température
entre passes, température/durée PWHT, O et N) + procédé catégoriel. Cette liste
couvre plusieurs familles de champs présents dans la base : composition,
paramètres de soudage et traitement thermique. Le choix ne prouve pas l’effet
de chaque champ sur chaque cible, ni sa disponibilité en situation d’utilisation.

Dans les 1 648 lignes dédupliquées avant filtre, les absences de O/N sont d’environ
24 %/28 %, celles de Ni/Cr/Mo d’environ 58 %/53 %/52 %. L’extension imposerait donc
plus de valeurs reconstruites. Le screening historique et le contrôle courant
motivent une référence plus mesurée : ils ne montrent pas que Ni/Cr/Mo sont
inutiles, ni que treize entrées maximisent la qualité des prédictions.

Le seuil d’au plus deux entrées numériques absentes conserve 1 555 lignes et
44 groupes ; c’est une règle explicite de départ, pas une garantie statistique.
A0_11 et A1b_16 restent des sensibilités sur cette même cohorte et ses mêmes
validations. Toute sélection optimisée de schéma doit se faire dans les plis
internes. Les échecs d’imputation de l’extension sont rapportés sans repli silencieux.

## Quoi prédire

| Régression indépendante | Labels dans la cohorte | Rôle |
| --- | ---: | --- |
| Limite d’élasticité, MPa | 706 | Tâche principale |
| Résistance maximale à la traction, MPa | 677 | Tâche principale |
| Allongement, % | 631 | Tâche principale |
| Réduction de section, % | 635 | Extension complémentaire |

On apprend une propriété avec les lignes qui renseignent cette propriété, sans
exiger toutes les sorties. Les autres propriétés restent hors des entrées :
leur disponibilité future n’est pas garantie. Charpy attend la distinction E(T)
et température à énergie fixée ; dureté attend la séparation des protocoles.
Ces mesures ne sont pas fusionnées en un score inventé de « qualité globale ».

## Comment comparer

| Modèle | Pourquoi le comparer | Grille initiale |
| --- | --- | --- |
| Médiane de y | Référence minimale | Aucun réglage |
| Ridge | Comparateur linéaire régularisé | 6 valeurs de alpha |
| SVR RBF | Comparateur non linéaire à noyau | 12 combinaisons C/gamma/epsilon |
| Random Forest | Comparateur non linéaire par arbres | 12 combinaisons, 300 arbres |
| kNN supervisé | Comparateur de voisinage pour COREG | 8 combinaisons k/p |

Les paramètres exacts sont enregistrés dans les specs et le notebook. Pour SVR,
y est standardisé à partir du train seulement et les prédictions reviennent à
l’unité originale. Les grilles sont des budgets proposés, pas des résultats.
Définitions : documentation officielle
[Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html),
[SVR](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html),
[Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).
L’adéquation aux méthodes effectivement vues en cours reste à vérifier.

Imputation itérative fixée pour la première comparaison. Cinq plis externes par
groupes pour l’évaluation, trois plis internes par groupes pour les réglages,
graine 42. Critère interne : MAE moyenne non pondérée. Rapporter aussi RMSE, R²,
effectifs et dispersion par pli dans les unités des cibles. Une famille/entrée
choisie en maximisant les scores externes ne possède pas une estimation
indépendante de cette sélection : inclure le choix dans la recherche interne
si l’on souhaite évaluer cette procédure de choix. Voir
[la validation imbriquée](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

## Candidat semi-supervisé

COREG est proposé pour la régression à labels incomplets : deux régressions kNN
à distances différentes échangent des pseudo-labels sélectionnés. Source
primaire : [Zhou et Li, IJCAI 2005](https://www.lamda.nju.edu.cn/publication/ijcai05.pdf).
Il reste à implémenter le mécanisme de sélection et définir son budget avant
les évaluations ; une simple auto-prédiction ne sera pas appelée COREG.

Protocole inductif : uniquement le pool des groupes du train courant, sans X/y
de validation interne ou externe. Pour isoler l’effet des pseudo-labels, le
preprocessing est ajusté sur les lignes étiquetées du train puis appliqué au pool
sans refit. Comparer au contrôle des mêmes deux régressions et de leur agrégation,
sans pseudo-labels, avec les mêmes labels et le même preprocessing. Les autres
sorties connues d’une ligne du pool ne sont pas utilisées. Un pseudo-label reste
une estimation ; l’amélioration sur cette base reste à mesurer.

## Validation de cette étape

Le notebook de configuration a été exécuté de haut en bas par Python, sans lancer
les nouveaux entraînements. Les quinze tests ciblés existants passent et contrôlent notamment
l’isolation des groupes, les fits sur le train et les refus d’imputation invalide.
Les exports et sources brutes sont inchangés ; configurations et documentation
sont seules concernées par cette étape.
