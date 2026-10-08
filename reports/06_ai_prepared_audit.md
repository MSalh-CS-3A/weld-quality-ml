# Audit du dataset et du notebook `ai_prepared`

Date : 8 octobre 2026. Verdict : cohérence technique des CSV validée ; nettoyage
scientifique et protocole non validés comme préparation finale du projet.
Aucun fichier fourni dans `ai_prepared/` n'a été modifié.

## Méthode de vérification

Lecture de toutes les cellules et sorties du notebook ; comparaison aux tokens
bruts du projet ; reproduction des cellules de lecture, parsing, conversions,
sélection, groupes, split et preprocessing dans une exécution séparée. Le chemin
de lecture `welddb.data` a été adapté à `data/raw/welddb.data`, le fichier absent
du dossier fourni. Les cellules d'export n'ont pas été exécutées et le fichier
`preprocessor.joblib` n'a pas été chargé. La pipeline a été reconstruite depuis
le code pour comparer ses résultats aux CSV.

Les vérifications détaillées sont dans `data/processed/ai_prepared_audit/`,
ignoré par Git : résumé JSON, correspondance des lignes avec le brut, répartition
des séries et cellules exactes modifiées. La recette exécutée y est conservée
comme `audit_ai_prepared.py`. Les hashes des cinq fichiers fournis sont dans
`summary.json`.

## Résultats techniques validés

| Vérification | Résultat |
| --- | --- |
| `welddb_clean.csv` | 1 534 lignes, 32 colonnes ; concordance avec les opérations du notebook |
| `train_processed.csv` | 1 206 lignes, 54 colonnes ; concordance avec un nouvel ajustement indépendant |
| `test_processed.csv` | 328 lignes, 54 colonnes ; concordance avec la transformation du test par le fit du train |
| Entrées transformées | 48 features ; valeurs numériques finies, sans NaN |
| Cibles | Non imputées ; valeurs mesurées préservées |
| Apprentissage du preprocessing externe | Médianes, échelles, choix des logs et catégories ajustés sur le train, pas sur le test |
| Groupes propres au notebook | 606 groupes ; aucun de ces groupes partagé entre train et test |

La validation de concordance confirme l'exécution du code, pas la validité
métallurgique des choix. Les noms, transformations et contenus exportés ne sont
pas incohérents avec la méthode déclarée.

| Cible | Train | Test | Total conservé |
| --- | ---: | ---: | ---: |
| Limite d'élasticité | 611 | 156 | 767 |
| Résistance maximale | 590 | 148 | 738 |
| Allongement | 548 | 139 | 687 |
| Réduction de section | 554 | 138 | 692 |
| Énergie Charpy | 683 | 196 | 879 |

Les opérations favorables comprennent la lecture en texte, N → NaN, l'absence
d'imputation des labels, le découpage avant l'ajustement des transformations
externes, la conservation des extrêmes et la suppression initiale des variables
très peu couvertes ou indisponibles avant fabrication. Les substitutions L/2
et les milieux d'intervalles sont utilisables comme approximations explicites,
pas comme mesures exactes garanties.

## Points empêchant une validation finale

### 1. Méthode différente de la décision du projet

La cellule 25 utilise `SimpleImputer(strategy='median', add_indicator=True)`.
Il n'y a pas d'imputation itérative, de contrôle de convergence ou de benchmark
de reconstruction dans ce notebook. La médiane est une baseline légitime,
mais ne met pas en œuvre le choix explicitement fixé par l'utilisateur.

La liste NUM comporte 23 variables, dont la température Charpy : elle revient
à utiliser une grande extension, avec bore, plutôt que les candidats B11/B13/B16
étudiés. Une absence de NaN après cette imputation ne prouve pas la reconstruction
fiable des colonnes peu observées.

### 2. Les doublons bruts restent présents

Le contrôle `df.duplicated()` de la cellule 20 inclut `weld_id`, d'où zéro.
Il ne contrôle pas l'égalité des mesures sous des identifiants différents et
aucun `drop_duplicates` n'est ensuite appliqué.

Les quatre occurrences excédentaires déjà repérées dans les 43 colonnes brutes
hors ID sont toutes conservées, aux indices bruts 393, 423, 425 et 1434.
Il y a également cinq répétitions dans la projection du CSV propre hors ID et
groupe. La cinquième paire n'est pas un doublon du brut : indices 334 et 394,
avec ferrite primaire 48/47 et ferrite de seconde phase 26/27 ; ces colonnes ont
été supprimées. Ne pas confondre déduplication du brut et collision après
projection sur moins de variables.

Dans le protocole fourni, les paires brutes identiques sont gardées dans le même
groupe de composition ; elles ne traversent pas le split. Le problème présent
est leur poids répété et le contrôle incomplet, pas une fuite démontrée entre
train et test pour ces quatre paires.

### 3. Groupes insuffisants pour évaluer des séries nouvelles

Le groupe du notebook repose sur l'égalité exacte de composition et de certains
paramètres, après numérisation et fusion de catégories, hors PWHT et température
Charpy. Ce groupe décrit un profil d'entrées ; il ne prouve pas qu'il s'agit
d'une soudure physique distincte. Les NaN, mesures partielles ou changements
de paramètres peuvent séparer des observations apparentées. Des profils égaux
peuvent aussi fusionner des observations distinctes.

En utilisant les 47 groupes conservateurs de séries du projet comme audit :

- les 47 ont au moins une ligne dans le train ;
- 39 ont au moins une ligne dans le test ;
- les 39 séries du test sont également dans le train ;
- les 328 lignes de test viennent donc de séries présentes dans le train.

L'identifiant `RC81033` apparaît sur trois lignes de train et une ligne de test,
avec des compositions différentes. Cette observation ne prouve pas une copie
du même essai, mais montre que l'identifiant répété ne reste pas nécessairement
dans un seul groupe.

Le split peut évaluer des profils de composition réservés au sein de séries
connues. Il ne permet pas d'annoncer une généralisation à une nouvelle série
ou publication. Les 47 groupes de référence sont eux-mêmes déduits d'identifiants,
pas des publications validées : leur révision doit être justifiée selon le
domaine visé. Une partition de séries, ou un test de sensibilité par séries,
est requis pour l'objectif de généralisation retenu dans le projet.

### 4. La validation croisée proposée réutiliserait un preprocessing appris

Le fit du train externe avant transformation du test est correct. En revanche,
la cellule 31 propose de partir de `train_processed.csv` et d'utiliser
GroupKFold. Ce fichier est déjà imputé et standardisé à partir de tout le train
externe ; le choix des logs est également déjà appris. Les futurs plis de
validation internes auraient participé à ces étapes.

Aucune validation croisée n'a réellement été exécutée dans ce dossier. Le défaut
porte sur la procédure suggérée : il faut repartir des entrées non imputées et
placer le preprocessing dans une pipeline ajustée dans chaque pli. La validation
externe n'est pas contaminée directement par le fit constaté, mais le fichier
prétraité ne doit pas être réutilisé tel quel pour régler les hyperparamètres.

### 5. Conversions d'unités plausibles mais non justifiées par les sources

Les cellules 11–12 déclarent des erreurs établies puis convertissent Al EPRI,
Ti/Al PantK, Sn/As/Sb Mart/Ditt et V `<5`. Aucune publication, page ou tableau
justifiant les unités originales de ces cellules n'est cité.

Le CSV conserve dix modifications de valeurs numériques exactes d'aluminium
EPRI : par exemple 0,014 → 140 ppm. Il conserve également des substitutions
transformées de limites PantK en 50 ppm et de V `<5` en 0,00025 wt%. Ces
conversions peuvent être correctes, mais un ordre de grandeur suspect ne suffit
pas à les certifier. Sn/As/Sb sont finalement supprimés, ce qui retire leurs
corrections du CSV final mais pas le problème de justification du notebook.

La règle combine un préfixe de source et un seuil <1 appliqué APRÈS parsing,
sans conserver dans le CSV l'unité d'origine, la borne ou le statut de censure.
Une ligne à 50 ppm ne distingue plus une mesure exacte d'une approximation
issue de `<0.01` avec unité supposée wt%.

Correction requise : table de conversions traçables, référence source explicite,
statut « confirmé » ou « hypothèse », comparaison des scénarios si pertinent.
En l'absence de preuve, rendre les cellules ambiguës indisponibles dans la
référence plutôt que de présenter ces conversions comme établies.

### 6. Azote et catégories : interprétations non documentées

L'azote annoté est remplacé par le premier nombre. La phrase « les autres lignes
rapportent l'azote total » n'est pas étayée par une source dans le dossier.
Les composantes résiduelles et marqueurs `nd` sont perdus du CSV. L'extraction
est techniquement correcte, sa comparabilité scientifique reste à établir.

La fusion `weld_type` réduit 10 modalités à 5 familles, notamment GMAA, NGGMA
et GTAA réunis sous `GMA_GTA`. La documentation distingue ces procédés ; ils
ne sont pas des synonymes. Une catégorie grossière peut être une expérience
justifiée, mais il faut conserver le code original et comparer son effet.
Il en va de même pour les autres regroupements non explicitement documentés.

La fusion courant/polarité traite notamment les 59 lignes avec `+` et courant
non rapporté comme `DC+`. Ce choix est une inférence, pas une valeur mesurée.
Quatre lignes AC portent aussi `+` : la règle leur donne priorité AC, mais
l'incohérence de métadonnées n'est pas tracée. Conserver origine et statut
inféré ou garder les deux colonnes avant confirmation.

### 7. Température Charpy utilisée pour toutes les cibles

`charpy_temp_C` figure dans NUM et dans les 48 features de tous les modèles
proposés par la boucle de cellule 31. Cette condition d'essai peut être connue
pour E(T), mais elle n'est pas une entrée de fabrication requise pour prédire
limite d'élasticité, UTS ou ductilité dans le scénario annoncé.

L'indicateur de température absente est parfaitement corrélé à la disponibilité
du label Charpy (corrélation -1 avec la disponibilité), puisque température et
énergie ont les mêmes absences. Il peut révéler le type de ligne ou le protocole
de collecte dans les modèles de traction. Ce n'est pas une copie numérique de
l'énergie cible, mais son utilisation doit être justifiée par les informations
disponibles à la prédiction, plutôt qu'être incluse automatiquement.

Il faut des schémas par tâche : traction sans température Charpy ; E(T) avec
température d'essai connue ; T100J/T28J avec température comme cible et donc
exclue des prédicteurs.

### 8. Charpy 100/28 J identifié mais non résolu

Le notebook signale la possible présence de températures de transition puis
conserve les 879 lignes dans une cible d'énergie commune, dont 356 à 100 J et
118 à 28 J. Une paire (T,E) peut être physiquement valide tout en provenant
d'un protocole de sélection différent, T recherché à E fixé versus E mesuré
à T fixé. Les objectifs et populations de mesure ne sont pas automatiquement
équivalents.

Il manque une table de protocole par source/observation et une référence
justifiant les affectations E(T), T100J, T28J. Ne pas classer les protocoles
uniquement d'après E==100 ou E==28. Tant que cette étape reste ouverte, le
dataset ne valide pas une tâche Charpy globale ni une note globale de qualité.

### 9. Suppressions et traçabilité

13 lignes Gar&K avec PWHT manquant sont supprimées. Cela enlève 13 labels YS,
13 labels d'allongement et 13 de réduction de section. L'exclusion peut être
un choix conservateur, mais le code ne vérifie pas le suffixe `ht` annoncé dans
le texte ; il sélectionne le préfixe et l'absence de température. Son motif et
ses effets doivent être enregistrés, sans prétendre que tous les paramètres
PWHT doivent toujours être connus exactement pour toutes les tâches.

105 lignes sans les cinq labels sont également supprimées. C'est compatible
avec une table supervisée, mais ces lignes sont des candidates non étiquetées
pour la semi-supervision demandée par le sujet. Il faut les conserver dans la
table maître et gérer leur éligibilité par cible et par partition.

`reset_index(drop=True)` puis les exports sans index font perdre les indices
bruts. Les fichiers processed n'ont pas `weld_id` ; `weld_group` n'identifie pas
chaque ligne. Il manque un `raw_row_id`, un journal des suppressions/conversions,
les statuts par cellule, les splits enregistrés, un manifeste de versions/hashes
et les supports par variable et groupe.

Les descriptions « midpoint = meilleure estimation », « censures /2 = convention
standard » et « toutes les valeurs extrêmes correspondent à des familles réelles »
doivent être nuancées : approximation, scénario et hypothèse ne constituent pas
une confirmation exhaustive.

## Corrections prioritaires avant l'entraînement du projet

1. Restaurer une table maître avec indices bruts, statuts, bornes et pool non
   étiqueté ; dédupliquer les quatre répétitions brutes selon la règle fixée.
2. Justifier ou mettre en quarantaine les corrections d'unités ; préserver les
   annotations N et les codes catégoriels originaux.
3. Définir les schémas par cible, avec B13 comme candidat principal et sans
   température Charpy pour la traction. Garder les variantes documentées.
4. Construire une partition cohérente avec l'objectif de généralisation ;
   contrôler les séries apparentées et identifiants répétés, pas seulement
   l'égalité des profils d'entrées.
5. Remplacer la médiane par l'itérative choisie et ajuster toute la pipeline dans
   chaque pli, y compris les plis internes ; exécuter les contrôles de convergence
   et de reconstruction sur le périmètre effectivement retenu.
6. Classifier les protocoles Charpy ou commencer seulement par les tâches de
   traction ; conserver les observations exclues dans les audits appropriés.

## Conclusion de validation

- **Validé :** les CSV sont conformes au code, les cibles restent mesurées,
  le preprocessing du split externe est ajusté sur le train et les exports
  numériques se reproduisent sans charger le joblib fourni.
- **Non validé pour le projet :** unités présentées comme corrigées sans preuve,
  déduplication manquante, généralisation par séries non évaluée, procédure CV
  sur données déjà préparées, méthode médiane au lieu de l'itérative choisie,
  schéma unique avec température Charpy et protocoles Charpy non résolus.

Le dossier est une base de travail techniquement cohérente. Il ne constitue
pas encore un dataset de référence scientifiquement validé pour les comparaisons
supervisées et semi-supervisées prévues. Aucun score prédictif n'a été calculé.

Références de méthode : [scikit-learn, prévention des fuites](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage),
[validation par groupes](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).
