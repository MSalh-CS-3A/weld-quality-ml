# Analyse du preprocessing et plan proposé jusqu'à l'entraînement

> Document historique antérieur à la migration des notebooks. Le protocole actif
> est dans `specs/spec.md` ; les sources antérieures sont conservées dans Git
> (sauvegarde `2ecb088`). Voir `reports/08_notebook_migration.md`.

Date : 8 octobre 2026. Statut : proposition d'action, pas une exécution du
nettoyage ni de l'entraînement. Les chiffres nouveaux ci-dessous viennent d'une
relecture du brut et des exports existants. Aucune performance prédictive n'est
annoncée. Les décisions scientifiques proposées sont consignées dans
`specs/spec.md`, section du 8 octobre 2026.

## 1. Sources examinées et portée

- Proposition fournie en pièce jointe : prédire plusieurs propriétés mécaniques
  séparément, puis les confronter aux exigences d'une application.
- `sujet.md`, `data/raw/welddb.info`, `data/raw/welddb.data`.
- Notebook `01_eda.ipynb`, code de préparation et d'exploration, rapports 01–03.
- Exports : benchmarks, convergence, diagnostics par variable, groupes,
  sensibilité ACP, manifeste. Le hash du brut et les trois hashes de code du
  manifeste correspondent aux fichiers actuels.

La base documente des compositions et propriétés du métal déposé. La prédiction
de plusieurs propriétés constitue un profil mécanique ; elle ne fournit pas
automatiquement un score global, des seuils d'acceptation ou une évaluation de
tous les défauts possibles d'un assemblage. La documentation Cambridge précise
que `N` veut dire non rapporté, et non zéro.

## 2. Ce que les résultats permettent de décider

### Couverture et dépendance au remplissage

Avant déduplication, les matrices préparées requièrent l'estimation de 536
cellules sur 18 172 pour le noyau (2,95 %), contre 9 445 sur 36 344 pour
l'extension (25,99 %). Une cellule censurée remplacée par une approximation
n'est pas comptée dans ces cellules manquantes ; ces taux ne mesurent donc pas
toute l'incertitude.

Quelques colonnes de l'extension :

| Variable | Exactes utilisables | Approximations | Cellules à estimer | Part à estimer |
| --- | ---: | ---: | ---: | ---: |
| Oxygène | 1 256 | 0 | 396 | 24,0 % |
| Azote | 1 183 | 0 | 469 | 28,4 % |
| Nickel | 697 | 0 | 955 | 57,8 % |
| Cuivre | 564 | 14 | 1 074 | 65,0 % |
| Aluminium | 492 | 387 | 773 | 46,8 % |
| Bore | 85 | 419 | 1 148 | 69,5 % |

Pour l'azote, les 469 comprennent 410 absences originales et 59 annotations
encore non utilisées numériquement. Pour le bore, seules 85 cellules sont
exactes : les 419 limites et les 1 148 imputations rendent la matrice très
dépendante des choix de préparation.

La couverture marginale masque celle par cible et par série. Après la
déduplication proposée, le bore exact n'est disponible que sur 44 lignes et
4 groupes pour la limite d'élasticité, et sur 20 lignes et 2 groupes pour
l'allongement. Pour Charpy, le niobium exact couvre 132 lignes et 5 groupes.
Il ne suffit donc pas de compter des lignes pour annoncer une capacité à
généraliser à des séries nouvelles.

### Reconstruction : la moyenne ne désigne pas un gagnant universel

Les moyennes enregistrées des erreurs normalisées sont reproduites par la
moyenne des lignes de benchmark de portée `all`, par méthode. Elles valent :

| Matrice | Médiane globale | Médiane par procédé | Itérative |
| --- | ---: | ---: | ---: |
| Noyau | 1,6966 | 1,2541 | 0,8532 |
| Extension | 2,2532 | 2,0599 | 2,0089 |

Ces moyennes n'utilisent pas exactement les mêmes poids qu'une moyenne donnant
un poids égal à chaque combinaison de scénario : certains masquages n'ont pas
de valeur éligible pour certaines variables. Il faut conserver les effectifs et
préciser l'agrégation. Les cellules sont répétées entre expériences ; leurs
comptes ne représentent pas de nouvelles observations indépendantes.

L'itérative du noyau améliore fortement la moyenne, mais la médiane par procédé
est meilleure dans le pli 2 : 0,418 contre 0,559, en moyennant les lignes de
benchmark de ce pli. Le courant domine une partie du contraste : dans le pli 0,
son IQR d'entraînement n'est que de 10 A. La médiane produit une MAE moyenne de
261,95 A, soit une MAE normalisée de 26,20 pour cette seule variable. Ce résultat
indique un transfert difficile entre groupes, pas une erreur prédictive sur la
qualité.

Pour l'extension, l'itérative échoue à converger dans les trois plis à 100
itérations et sur la base entière. Dans le pli 1, sa moyenne d'erreur est 1,590
contre 0,886 pour la médiane globale. L'erreur native moyenne pour l'azote est
84,27 ppm contre 50,70 ppm ; pour le bore, 21,82 ppm contre 18,75 ppm. Une
amélioration globale ne signifie donc pas une amélioration de chaque variable.

Le diagnostic de corrélation est également défavorable à l'itérative de
l'extension : delta absolu moyen 0,1589 contre 0,1060 pour la médiane globale.
Respecter des bornes physiques très larges ne prouve pas la plausibilité des
valeurs ni leur conformité aux unités.

### ACP : noyau relativement stable, extension plus sensible

Les deux premiers axes de la référence médiane expliquent 45,41 % de la variance
du noyau et 34,08 % de l'extension. Les espaces diffèrent : ces pourcentages ne
classent pas leur qualité.

Dans un même espace, les angles maximaux entre sous-espaces à deux axes et la
référence médiane sont 1,99° (médiane par procédé) et 2,81° (itérative) pour le
noyau, contre 13,18° et 19,74° pour l'extension. Les substitutions de censure
modifient les axes de l'extension d'au plus 2,10° dans les scénarios testés. Le
choix d'imputation y a donc un effet plus marqué que ces substitutions.

L'ACP sur cas complets du noyau présente un angle de 6,10° ; elle change aussi
la population analysée. Aucune contribution ACP ne constitue une preuve
d'inutilité prédictive d'un élément chimique.

## 3. Doublons : règle proposée et effet exact

Il n'existe pas de doublon exact incluant l'identifiant. Sur les 43 autres
colonnes brutes, quatre paires sont identiques :

| Indices bruts, base zéro | Identifiants |
| --- | --- |
| 333 / 393 | `Evans-V/Mn-1991-A3aw` / `Evans-Nb/Mn-1991-A<5aw` |
| 363 / 423 | `Evans-V/Mn-1991-C4aw` / `Evans-Nb/Mn-1991-C<6aw` |
| 365 / 425 | `Evans-V/Mn-1991-C4ht` / `Evans-Nb/Mn-1991-C<6ht` |
| 1418 / 1434 | `Ditt-oatch3` / `Ditt-iatch3` |

Proposition conforme à la demande de suppression : conserver la première
occurrence dans la matrice de modélisation, soit supprimer les indices 393,
423, 425 et 1434, et exporter les identifiants alternatifs et motifs. Cela donne
1 648 lignes. L'égalité des valeurs rapportées ne démontre pas à elle seule
qu'il s'agit de copies du même essai ; la suppression est ici une convention
explicite pour éviter de compter deux fois le même enregistrement disponible.

Construire et conserver les liens de groupes AVANT la suppression : les séries
Evans-V/Mn et Evans-Nb/Mn restent liées même si les lignes qui révèlent cette
relation sont retirées. Conserver les 47 groupes actuels comme référence
provisoire, avec audit des cas et justification de la généralisation visée.

Ne pas supprimer les lignes seulement parce que `weld_id` est répété, ni parce
que la composition est identique : conditions d'essai, traitements et propriétés
peuvent différer.

## 4. Valeurs spéciales : représentation numérique et exclusions

Supprimer toutes les lignes ayant une censure, un intervalle ou une annotation
retirerait 522 lignes. Ajouter tous les signalements actuels d'unité porterait
ce nombre à 593, soit 35,9 % du brut. Après déduplication, il resterait 1 059
lignes, dont 525 labels de limite d'élasticité, 456 d'allongement et 519 de
Charpy. Les doublons excédentaires sont déjà dans cet ensemble de 593 lignes.
Ce scénario enlève systématiquement certaines séries : ce n'est pas un
nettoyage neutre.

La proposition est donc de supprimer les chaînes des entrées du modèle en les
numérisant, et de retirer uniquement les doublons et les valeurs démontrées
invalides. Les ambiguïtés non résolues rendent la cellule indisponible dans le
scénario principal, pas toute la ligne. Un scénario de suppression stricte peut
être conservé comme sensibilité avec ses effectifs et groupes perdus.

| Forme | Traitement proposé | Information à conserver |
| --- | --- | --- |
| Nombre exact | Conserver dans l'unité documentée, après audit | Jeton brut et unité |
| `N` et autres encodages d'absence documentés | `NaN`, puis imputation des entrées dans l'entraînement | Masque d'absence originale |
| `<L`, concentration non négative d'unité non signalée | `L/2` comme approximation principale | Borne L, opérateur, statut censuré ; sensibilité 0 et L/√2 |
| `150-200` | 175 °C comme approximation principale | Bornes 150/200 ; sensibilité aux deux extrémités |
| `67tot33res` | Extraire séparément 67 et 33 dans des champs d'audit | Jeton brut et nature de chaque composante ; ne jamais concaténer en 6733 |
| `66totndres` | Extraire 66 ; composante `nd` indisponible | Marqueur `nd`, sans le remplacer par zéro ni inventer une limite |
| `203(Hv30)` | Extraire valeur 203 et protocole `Hv30` | Protocole séparé ; dureté hors cibles initiales |
| Unité suspecte | Vérifier par source ; sinon masquer la cellule | Valeur originale, raison, référence de toute correction |
| Extrême numérique | Conserver tant qu'aucune erreur n'est démontrée | Série, procédé et contrôles de cohérence |

Les annotations d'azote sont toutes dans la série Evans-Al/CMn-1990. L'extraction
lexicale de `tot`/`res` ne suffit pas à certifier leur comparabilité avec les
autres mesures d'azote. Le scénario principal garde les 59 cellules annotées
indisponibles tant que cette sémantique n'est pas confirmée ; l'audit exporte
déjà les composantes. Une variante utilisant le total devra annoncer cette
interprétation et sa source, puis être évaluée dans les validations internes.

Ne pas supprimer automatiquement les 30 courants 850–900 A, associés au procédé
SA, ni les faibles concentrations. Les signalements sous 1 ppm sont des
heuristiques de revue et non des preuves d'erreur. Les 610 couples PWHT 0/0
restent observés ; leur sens n'est pas déclaré confirmé. Les couples absents
sont imputés conjointement. Les sommes microstructurales 90/99/119 % ne sont
pas renormalisées automatiquement.

Priorités de vérification : 10 cellules Al EPRI sous 1 ppm ; 90 lignes Mart/Ditt
avec Sn/As/Sb sous 1 ppm ; 1 cellule Ti sous 1 ppm ; 16 limites `<0.01` pour Ti
et 16 pour Al ; 9 limites V `<5`. Pas de conversion générale ×10 000 fondée
seulement sur l'ordre de grandeur.

## 5. Cibles et matrices pour les premiers entraînements

Après déduplication proposée, avant les autres exclusions éventuelles :

| Cible | Labels numériques exacts | Groupes représentés | Statut proposé |
| --- | ---: | ---: | --- |
| `yield_strength` | 777 | 43 | Première régression, MPa |
| `ultimate_tensile_strength` | 735 | 42 | Deuxième régression, MPa |
| `elongation` | 697 | 37 | Troisième régression, % |
| `reduction_area` | 702 | 35 | Cible complémentaire, % |
| `charpy_toughness` | 877 | 25 | Tâche conditionnelle après audit du protocole |

Les quatre propriétés de traction sont simultanément exactes sur 647 lignes,
contre 650 avant déduplication. Commencer par un modèle par propriété permet
d'utiliser tous ses labels, sans exiger l'intersection et sans imputer de cible.
Une ligne sans le label d'une propriété est non étiquetée pour cette propriété,
même si elle possède d'autres labels.

Pour Charpy, 356 lignes brutes sont à 100 J et 118 à 28 J. Toutes les 79 lignes
Charpy du groupe lié Evans-Nb/Mn + Evans-V/Mn sont à 100 J mais réparties sur
47 températures. D'autres séries ont également des énergies fixées. Cela
renforce, sans prouver, l'hypothèse d'un mélange de températures de transition
à énergie fixée et d'énergies mesurées à température donnée. Auditer les
publications avant d'adopter une tâche unique. Séparer ensuite les protocoles
confirmés : E(T) avec température en entrée, ou T à énergie de référence
fixée. Toutes les 877 lignes Charpy conservées ont une température numérique.
L'audit Charpy ne bloque pas les trois régressions de traction.

Proposition de trois jeux d'entrées numériques :

- A0 : noyau existant de 11 variables, référence de continuité.
- A1 : A0 + oxygène + azote, soit 13 variables, référence principale proposée.
- A2 : A1 + Ni, Cr, Mo, V, Cu, Ti, Al, Nb, soit 21 variables, modèle enrichi.
  Le bore est un ajout de sensibilité spécialisé, pas une colonne obligatoire.

Après déduplication et selon les règles actuelles, A1 a 1 399 cellules
indisponibles sur 21 424 (6,53 %). Ce calcul de disponibilité n'est PAS un
benchmark d'imputation ni une validation prédictive de ce nouvel espace.
A2 a 23,93 % de cellules à estimer ; avec le bore, 26,00 %.

Ajouter `weld_type` comme catégorie pour les trois variantes. Comparer
`current_type` et `electrode_polarity` comme ajout secondaire ; conserver la
modalité `0` séparée sans supposer son sens. Normaliser uniquement les synonymes
documentés, sans fusionner automatiquement les autres variantes de procédé.

Écarter du premier modèle Co, W, Sn, As, Sb, microstructure, dureté et FATT :
ce sont des exclusions de périmètre et de support, pas une démonstration
d'inutilité physique. Les autres propriétés mécaniques ne sont pas des
prédicteurs de la propriété cible. L'identifiant et le groupe restent des
métadonnées de séparation. Pour la tâche Charpy E(T), adapter explicitement
le schéma : l'imputer actuel rejette `charpy_temperature` comme propriété ;
il faut l'autoriser comme condition d'essai pour cette tâche uniquement.

## 6. Construire le dataset préparé puis la pipeline

Le premier export définitif doit être une table NETTOYÉE AVANT IMPUTATION.
La présence de `NaN` dans cette table est voulue. Imputer une fois la base entière
avant validation apprendrait aussi des informations des groupes d'évaluation.

Artefacts proposés dans `data/processed/modeling/`, ignorés par Git :

- `clean_numeric.csv` : valeurs exactes ou approximations documentées et `NaN`.
- `cell_provenance.csv` : indices, statut, bornes, motifs et transformations.
- `row_metadata.csv` : index brut stable, ID, alias de doublon, groupe, inclusion.
- `duplicate_map.csv` et `cleaning_log.csv` : suppressions et raisons.
- `target_eligibility.csv` : label disponible par propriété, protocole Charpy.
- `feature_sets.json`, `splits.csv`, `manifest.json` : schémas, partitions, hashes,
  versions, graines et règles scientifiques.

Ordre des opérations : audit brut → liens de groupes → déduplication →
conversions déterministes justifiées → éligibilité par cible → partitions →
imputation/encodage/échelle/sélection/modèle dans l'entraînement.

Imputation initiale : médiane par procédé avec support d'au moins 3 groupes
mesurés et repli global, comparée à la médiane globale. Pour A0, l'itérative
convergée est une candidate. A1 doit avoir son propre contrôle de reconstruction
et convergence ; les résultats A0 ne se transfèrent pas automatiquement.
L'itérative de l'extension à 22 variables ne sera pas la référence initiale.

Dans chaque entraînement : encoder les catégories avec gestion des inconnues ;
conserver des indicateurs d'absence et de censure et tester leur apport ;
standardiser pour Ridge/SVR/kNN, pas nécessairement pour les arbres ; garder
PWHT température/durée cohérents. Si une colonne n'a aucune observation dans
un pli d'entraînement, ne pas fabriquer sa médiane : exclure cette colonne pour
la pipeline de ce pli, consigner ce fait et appliquer le même schéma au groupe
réservé. La sélection d'un sous-ensemble et toute ACP prédictive sont apprises
dans les plis internes, sans réutiliser les fits exploratoires.

## 7. Protocole d'entraînement proposé

1. Audit de la répartition des labels, catégories et support mesuré par groupe
   pour chaque cible après nettoyage.
2. Validation externe à 5 plis de groupes et validation interne à 3 plis de
   groupes, si les effectifs et le support le permettent ; graines fixées à 42
   pour les modèles stochastiques. Sauvegarder les affectations, ne pas les
   reconstruire implicitement. Comparaisons sur les mêmes lignes pour une cible.
3. Référence constante `DummyRegressor` médiane ; Ridge ; Random Forest ; SVR
   comme candidat complémentaire selon les méthodes vues en cours. Budgets de
   réglage bornés et comparables, consignés avant les expériences.
4. Comparer A0/A1/A2 et les imputations dans la validation INTERNE. Même principe
   pour retirer des variables ou des blocs, tester les indicateurs et l'ACP.
   Les scores externes servent à évaluer la procédure, pas à ajuster à nouveau
   les choix puis annoncer ces mêmes scores comme une validation indépendante.
5. MAE et RMSE dans l'unité de la cible, R², scores par pli et par groupe ;
   moyenne par ligne et moyenne par groupe clairement distinguées. Produire
   des prédictions hors entraînement et inspecter les erreurs sans inventer de
   causalité. Rapporter les plis constants pour lesquels R² n'est pas informatif.
6. Documenter la stabilité des variables retenues entre plis. Une faible
   corrélation ou un faible coefficient ACP ne suffit pas pour une élimination.

Les transformations déterministes de censure restent des approximations. Si le
choix entre `L/2` et ses variantes est optimisé avec la cible, cette optimisation
doit aussi rester dans les validations internes.

## 8. Semi-supervision et synthèse des propriétés

Pour répondre au sujet, étudier une méthode de régression semi-supervisée, avec
COREG comme candidate bibliographique concrète. L'algorithme original utilise
deux régresseurs kNN et des métriques différentes, avec sélection des
pseudo-labels. Son bénéfice sur cette base reste à mesurer. Ne pas substituer
directement une méthode de classification à ces régressions.

Protocole proposé : inductif. À chaque pli, seuls les groupes d'entraînement
alimentent les ensembles étiquetés et non étiquetés. Les entrées ET les labels
des groupes réservés restent hors imputation, réglage et pseudo-étiquetage.
Même règle dans les plis internes. Pour isoler l'effet des pseudo-labels,
ajuster le preprocessing initial sur les mêmes lignes étiquetées que la
référence supervisée, puis transformer le pool non étiqueté autorisé. Comparer
à la version supervisée correspondante avec les mêmes labels et partitions.
Vérifier aussi que le pool non étiqueté couvre des procédés et compositions
comparables ; la disponibilité des labels n'est pas uniforme entre séries.

La sortie initiale est un profil de propriétés avec erreurs de validation.
Construire un score d'acceptabilité seulement lorsqu'une application fournit
les températures d'essai, seuils et compromis requis. Aucun seuil industriel
ne sera fabriqué à partir des quartiles ou des axes ACP.

## 9. Critères de fin et points restant conditionnels

Le dataset prêt à modéliser est livré lorsque les suppressions sont tracées,
les valeurs spéciales ont une représentation explicite, les schémas sont
définis et les partitions sont enregistrées. La première comparaison est
livrée lorsque les trois cibles de traction ont une référence constante et au
moins deux modèles supervisés évalués selon la même procédure.

Contrôles nécessaires lors de l'implémentation : brut intact ; 4 suppressions
exactes selon la règle proposée ; conservation des alias et liens de groupes ;
cellules exactes inchangées ; approximations respectant leurs bornes ; aucune
chaîne non encodée dans les entrées du modèle ; aucune cible imputée ; groupes
disjoints ; transformations apprises exclusivement sur les données permises ;
graines, hashes, effectifs et exclusions reproductibles. Ajouter des tests
ciblés pour ces comportements et exécuter ceux qui existent déjà.

Les unités incertaines, le sens de certaines annotations et les protocoles
Charpy restent conditionnels. La stratégie de repli par cellule permet de
démarrer la traction sans prétendre les avoir résolus. Le choix prédictif final
de variables, d'imputation et de modèle dépend des expériences futures.

## Références

- [Cambridge, documentation MAP_DATA_WELD](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html) : périmètre, unités, sens de `N`.
- [scikit-learn, prévention des fuites de données](https://scikit-learn.org/stable/common_pitfalls.html) : ajustement dans l'entraînement et pipelines.
- [scikit-learn, imputation](https://scikit-learn.org/stable/modules/impute.html) : méthodes univariées, multivariées et indicateurs.
- [scikit-learn, sélection de variables](https://scikit-learn.org/stable/modules/feature_selection.html) : sélection, validation et limites des critères univariés.
- [scikit-learn, validation par groupes](https://scikit-learn.org/stable/modules/cross_validation.html#group-k-fold).
- [Zhou et Li, COREG, IJCAI 2005](https://www.ijcai.org/Proceedings/05/Papers/0689.pdf).
