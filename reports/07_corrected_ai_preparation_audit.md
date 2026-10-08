# Audit de la préparation AI corrigée

> Document historique antérieur à la migration des notebooks. Le protocole actif
> est dans `specs/spec.md` ; les sources antérieures sont conservées dans Git
> (sauvegarde `2ecb088`). Voir `reports/08_notebook_migration.md`.

Date : 8 octobre 2026.

**Verdict : préparation validée comme base des benchmarks supervisés de traction
sur le candidat 13 entrées.** Les corrections majeures du premier audit sont
effectives. Cette validation ne certifie ni les unités encore incertaines, ni
une tâche Charpy, ni la performance d'un modèle final. Le notebook nécessite une
adaptation de ses chemins pour être exécuté dans ce dépôt. Un cas limite PWHT
et des formulations trop générales restent à corriger.

## Périmètre et vérification

Fichiers examinés : `ai_prepared/02_data_preparation.ipynb`,
`ai_prepared/weld_prep.py` et les neuf fichiers de `ai_prepared/modeling.zip`
(huit CSV et un manifeste JSON). Lecture de toutes les cellules, du module et
des sorties enregistrées. Le notebook contient 17 cellules de code exécutées
dans l'ordre, sans sortie d'erreur enregistrée.

Le module a été exécuté indépendamment sur `data/raw/welddb.data`, puis ses
tables comparées à celles de l'archive. La cellule du benchmark a été réexécutée
avec ses paramètres inchangés : Ridge `alpha=1`, Random Forest 300 arbres,
`min_samples_leaf=2`, graine 42, et prédicteur constant à la médiane du train.

Les huit CSV sont reproduits, scores compris (tolérance numérique 1e-10).
Les hashes du brut, du module et de tous les CSV du manifeste sont vérifiés.
La reproduction locale utilise Python 3.14.8, pandas 3.0.6, NumPy 2.5.3 et
scikit-learn 1.9.1 ; le manifeste d'origine indique Python 3.13.16 et pandas
3.0.5 avec les mêmes versions NumPy/scikit-learn.

Les vérifications et résultats sont conservés dans
`data/processed/ai_prepared_corrected_audit/` (ignoré par Git), dont la recette
`audit_corrected.py`, le résumé, les scores reproduits et les diagnostics des
plis. Aucun fichier fourni dans `ai_prepared/` n'a été modifié. Aucun joblib n'a
été chargé. Le brut et l'énoncé sont préservés.

## Corrections effectivement validées

| Point | Vérification |
| --- | --- |
| Doublons | Quatre occurrences excédentaires sur les 43 champs bruts hors ID ; alias conservés, absentes des plis et de la cohorte |
| Traçabilité | Identifiant brut stable, 66 080 cellules numériques décrites avec token, statut, bornes, annotation et représentation principale |
| Unités | Aucune conversion conjecturale ; 322 cellules mises à NaN et journalisées |
| Valeurs spéciales | L/2 et milieu d'intervalle identifiés comme approximations ; bornes et tokens conservés |
| Azote | 59 annotations tot/res conservées séparément, indisponibles dans N principal |
| Procédés | Seuls ShMA→MMA et SMA→SA sont fusionnés ; synonymes vérifiés dans `data/raw/welddb.info` |
| Catégories | Courant et polarité préservés, aucune inférence DC à partir d'une polarité seule |
| Cibles | Valeurs observées identiques au brut ; absences conservées, aucune imputation de labels |
| Groupes | 47 groupes dérivés des identifiants et liens de doublons ; aucun groupe partagé entre partitions externes ou internes |
| Preprocessing | Moyennes, écarts-types, catégories, imputation et couples PWHT appris sur le train du pli uniquement |
| Valeurs observées | Préservées après transformation/inversion d'échelle dans les 15 cas tâche × pli testés |
| Convergence | Les 15 ajustements itératifs sur 13 entrées convergent en 4 à 7 itérations |
| Données non étiquetées | 105 lignes sans aucune des cinq cibles conservées après déduplication, dont 99 dans la cohorte stricte |

Répartition des 322 cellules en quarantaine : Al 26, As 90, Sb 90, Sn 90, Ti 17,
V 9. Ces colonnes ne font pas partie du noyau 13 ; leur quarantaine ne retire
pas directement une entrée de ce noyau. Elle ne démontre pas que chaque valeur
signalée est erronée : c'est une précaution traçable en attendant les sources.

## Ce que les exports permettent

`master.csv` conserve les 1 652 lignes, y compris les quatre alias marqués.
Après exclusion des alias, 1 648 lignes restent. Le filtre `in_strict13` est
vrai pour 1 555 lignes de 44 groupes : au plus deux entrées indisponibles sur
les 13 et aucun alias. Ce filtre ne signifie pas que les cibles sont connues.

| Cible | Labels dans la cohorte stricte |
| --- | ---: |
| Limite d'élasticité | 706 |
| Résistance maximale à la traction | 677 |
| Allongement | 631 |
| Réduction de section | 635 |
| Énergie Charpy | 861, avec protocole encore non adopté |

Pour une tâche supervisée, sélectionner `in_strict13` et `has_<cible>`, joindre
`folds.csv` sur `raw_row_id`, puis utiliser uniquement le schéma d'entrées de
la tâche. Les métadonnées, flags d'éligibilité, autres propriétés mécaniques,
identifiants et numéros de plis ne doivent pas entrer automatiquement dans X.

Les schémas disponibles sont 11 variables de base, 13 avec O/N, et 16 avec
Ni/Cr/Mo, chacun avec le procédé catégoriel. Le benchmark reproduit ne compare
que le schéma 13. La possibilité technique d'utiliser 11 ou 16 ne prouve pas
leur intérêt prédictif ni la fiabilité de leur imputation. Le filtre de cohorte
exporté porte sur 13 ; une autre cohorte exige une règle explicite et des lignes
de validation communes pour les comparaisons.

Les plis sont communs aux cibles sur la table dédupliquée. Dans la cohorte :

| Pli externe | Groupes | Lignes | YS | UTS | Allongement |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 8 | 330 | 132 | 138 | 139 |
| 1 | 9 | 330 | 166 | 142 | 141 |
| 2 | 9 | 298 | 145 | 162 | 137 |
| 3 | 8 | 287 | 120 | 121 | 103 |
| 4 | 10 | 310 | 143 | 114 | 111 |

Les sous-plis internes sont bien réservés aux groupes du train externe et
disjoints entre eux. Ils sont prêts pour le réglage des hyperparamètres, mais
ce réglage n'est pas réalisé par le benchmark actuel à paramètres fixes.

Le pool semi-supervisé est disponible, globalement et par cible. Il faut
sélectionner les lignes sans la cible étudiée uniquement dans les groupes du
train externe, puis également dans ceux du train interne pendant le réglage.
Aucune méthode semi-supervisée n'est entraînée dans ce notebook. La préparation
permet un protocole inductif ; elle ne l'implémente pas à elle seule.

Charpy dispose de signatures par groupe et de schémas conditionnels E(T),
T100J et T28J. Il n'existe pas encore de sélection validée des lignes pour ces
tâches. La méthode évite justement de décréter le protocole à partir de E=100
ou E=28 seulement. Les sources restent nécessaires avant entraînement.

## Lecture indépendante du benchmark

MAE moyennes sur les cinq plis externes :

| Cible | Ridge médiane | Ridge itérative | RF médiane | RF itérative | Baseline constante |
| --- | ---: | ---: | ---: | ---: | ---: |
| Limite d'élasticité, MPa | 80,75 | 80,55 | 65,39 | 66,13 | 70,45 |
| Résistance maximale, MPa | 77,58 | 66,30 | 58,10 | 56,71 | 72,66 |
| Allongement, points de % | 4,37 | 3,80 | 3,70 | 3,55 | 4,09 |

Ces résultats soutiennent le maintien de l'imputation itérative choisie comme
méthode principale, avec la médiane comme comparaison. Ils ne prouvent pas
une supériorité sur toutes les cibles et tous les plis. Sur YS/RF, la médiane
est légèrement meilleure en moyenne. Sur YS/Ridge, au pli 4, la MAE passe de
85,99 à 100,57 MPa avec l'itérative : +14,58 MPa. La phrase « jamais nettement
pire » et la conclusion « prédiction égale ou meilleure » sont trop générales.

Les R² moyens des RF itératives sont 0,0765, 0,1899 et 0,1136 pour YS, UTS et
allongement. Les R² moyens de Ridge restent négatifs. La préparation fonctionne,
mais ces modèles ne démontrent pas encore une forte performance de prédiction.
Les causes des écarts ne sont pas isolées : le notebook ne permet pas d'affirmer
que ce n'est « pas un problème d'imputation », ni que des constantes de médiane
expliquent à elles seules le comportement de Ridge.

Les valeurs 0,85/1,70 de reconstruction citées proviennent du benchmark EDA sur
11 variables. Ce n'est pas une mesure nouvelle de reconstruction sur la cohorte
13 corrigée ; la convergence et les scores de cibles ne remplacent pas ce test.
Les écarts-types de cinq plis décrivent une variabilité, pas un test de
significativité ni une garantie d'équivalence.

## Réserves et corrections restantes

### Exécution et intégration au dépôt

La première cellule cherche `welddb.data` dans le répertoire courant ; ce fichier
n'est pas dans `ai_prepared/`. Le hash de `weld_prep.py` suppose également un
répertoire courant particulier. Adapter les chemins au projet, charger le
module de façon cohérente et écrire les exports sous `data/processed/`.
Pour intégrer cette version, le module réutilisable doit rejoindre
`src/weld_quality/` et le notebook le dossier `notebooks/`. Cet audit n'effectue
pas ces déplacements.

Les anciens `train_processed.csv`, `test_processed.csv`, `welddb_clean.csv` et
`preprocessor.joblib` restent présents et inchangés. Ils appartiennent à la
première préparation et ne sont pas validés par le présent audit. Les nouveaux
exports sont dans `modeling.zip`, avant apprentissage. Le nouveau manifeste
gagnerait aussi à enregistrer le hash du notebook et les paramètres des modèles
du benchmark, qui y sont actuellement définis mais non consignés au manifeste.

### Cas limite PWHT confirmé

Dans `FoldPreprocessor.transform`, lignes 372–375, si une composante PWHT est
observée mais qu'aucun couple du train ne lui correspond, le code conserve tous
les candidats. Il garde ensuite la composante observée et emprunte l'autre à
un couple incompatible. La paire finale peut donc être absente du train.

Test indépendant : train (0 °C,0 h), (600 °C,2 h), (650 °C,3 h), entrée de test
(700 °C,NaN). L'imputation médiane suivie de projection produit (700 °C,2 h),
qui n'est aucun des couples observés. Le mécanisme est commun aux deux méthodes.
Il faut expliciter le cas « aucun couple compatible » : erreur/drapeau et
politique documentée, sans modifier la composante mesurée.

Cela n'affecte pas les scores reproduits : dans le jeu actuel après
déduplication, 1 635 lignes ont les deux composantes PWHT et 13 ont les deux
manquantes ; aucune ligne n'en a une seule manquante. Pour les cas testés avec
les deux absentes, la projection renvoie bien un couple réel du train.

### Portée scientifique et garde-fous

- Les groupes sont des séries inférées des identifiants, pas des publications
  confirmées. Les variantes de noms restent une sensibilité à tester avant
  d'affirmer une généralisation inter-publications.
- Le seuil ≤2 indisponibles n'est pas une garantie de fiabilité. Une vérification
  descriptive donne : ≤1 → 1 087 lignes/34 groupes/501 YS ; ≤2 →
  1 555/44/706 ; ≤3 → 1 603/46/748. Il faudra évaluer les performances et
  la population couverte avant de choisir un autre seuil.
- Le schéma exclut des variables selon la couverture, les ambiguïtés et leur
  disponibilité. Il ne démontre pas leur absence d'effet physique et ne réalise
  pas encore une sélection prédictive de variables.
- La classe enregistre `converged_`, mais autorise encore `transform` si ce
  flag est faux. Les entraînements finaux doivent contrôler ce flag et définir
  un repli explicite. Aucune non-convergence n'a été observée ici.
- Les unités, l'azote annoté et les protocoles Charpy restent ouverts. Leur
  quarantaine actuelle est compatible avec les benchmarks de traction sur 13
  entrées ; elle ne résout pas leur sémantique.

## Décision pour la suite

La base corrigée permet de démarrer la comparaison supervisée des trois cibles
de traction, avec preprocessing par pli et tuning interne. La réduction de
section est techniquement préparée, mais n'a pas été benchmarkée ici.
Conserver le schéma 13 comme candidat principal, la médiane comme contrôle,
les lignes non étiquetées pour la future méthode inductive, et les autres
schémas comme expériences à vérifier sur des validations comparables.

Adapter les chemins, nuancer l'interprétation du benchmark et sécuriser le
cas PWHT partiel avant intégration définitive. Ne pas utiliser les anciens CSV
transformés pour les nouveaux benchmarks, ni adopter une cible Charpy globale.
