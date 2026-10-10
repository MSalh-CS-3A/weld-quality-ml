# Synthèse globale des résultats du projet

**Auteurs : Mohamed SALH, Mohamed CHEBLI et Idriss BEN LETAIFA.**

**Version du 10 octobre 2026 - branche `task/salh-supervised-training`.**
Cette synthèse consolide les expériences réellement exécutées dans les notebooks
01 à 07. Les chiffres sont lus dans les CSV dont les hashes ont été vérifiés.
Le [rapport complet, première version](16_rapport_projet_v1_fr.md) fournit une
présentation courte adaptée au rendu demandé par l’énoncé.

## 1. Résultat principal

La configuration de travail comprend 16 entrées numériques et le procédé,
avec imputation médiane apprise dans les trains. Les modèles supervisés
prédisent correctement des observations aléatoires de la population couverte,
mais leur performance diminue lorsqu’une série entière est absente du train.
COREG ne dépasse pas la procédure supervisée de référence sur cette cohorte.
Un R² supérieur à 0,5 n’est ni un critère d’acceptation imposé ni une garantie.

**Tableau 1 - Sélection de famille et paramètres par MAE interne ; moyennes des
cinq plis externes, configuration 16/médiane.** Les MAE sont dans les unités
des cibles. YS désigne la limite d’élasticité. Charpy* reste exploratoire.

| Cible (unité) | MAE aléatoire | R² aléatoire | MAE groupée | R² groupé |
| --- | --- | --- | --- | --- |
| YS (MPa) | 31,630 | 0,755 | 56,757 | 0,337 |
| UTS (MPa) | 23,861 | 0,836 | 54,344 | 0,334 |
| Allongement (points de %) | 2,054 | 0,660 | 3,517 | 0,157 |
| Charpy* (J) | 16,461 | 0,776 | 35,752 | 0,075 |

![Figure 1 - Comparaison globale des R² moyens et de leur dispersion.](figures/15_comparaison_globale_fr.png)

La sélection peut changer de famille selon le pli. Ce tableau évalue une
procédure de sélection interne ; il ne décrit pas un modèle choisi après
lecture des R² externes. Le score moyen d’une famille isolée peut être meilleur
que celui de cette procédure sans autoriser une sélection sur la validation.

## 2. Données, cibles et entrées

La base contient 1 652 lignes et 44 champs. Quatre alias exactement répétés hors
identifiant sont retirés des expériences : 1 648 observations restent. Le master
conserve toutes les lignes, leurs identifiants, les flags et les valeurs absentes.
La cohorte principale conserve 1 555 observations et 44 groupes inférés, avec
au plus deux entrées indisponibles sur le noyau de 13 variables.

| Cible | Signification | Labels / groupes | Pool naturel global sans cette cible |
| --- | --- | --- | --- |
| `yield_strength` | Limite d’élasticité, MPa | 706 / 40 | 849 |
| `uts` | Résistance maximale à la traction, MPa | 677 / 39 | 878 |
| `elongation` | Allongement à rupture, % | 631 / 34 | 924 |
| `charpy_J` | Énergie Charpy à température connue, J | 861 / 24 | 0 avec température connue |

Chaque cible dispose d’un modèle séparé et de ses propres labels : imposer
toutes les sorties complètes réduirait inutilement les données. Sur les mesures
exactes dédupliquées de l’EDA, corr(YS, UTS)=0,915 ; corr(YS, allongement)=-0,680
et corr(UTS, allongement)=-0,738. La matrice est une corrélation par paires,
pas une ACP. Elle indique une dépendance, pas l’équivalence physique de YS et
UTS. Résistance et déformation restent des informations complémentaires.

Les entrées communes sont C, Si, Mn, S, P, Ni, Cr, Mo (% massique), O et N (ppm),
courant (A), tension (V), apport thermique (kJ/mm), température entre passes et
PWHT (°C), durée PWHT (h), plus le procédé. Charpy ajoute sa température d’essai
connue. Aucune autre sortie mécanique, dureté, FATT50, microstructure, ID ou groupe
n’est utilisée comme entrée. Réduction de section, dureté et FATT50 ne sont pas
des sorties entraînées dans ce portefeuille.

## 3. Préparation, imputation et ACP

Le token `N` signifie non rapporté, pas zéro [1]. Les valeurs censurées `<L`
utilisent L/2 et les intervalles leur milieu, avec provenance des approximations.
Les 322 cellules signalées pour révision d’unité restent NaN, sans conversion
supposée. Les annotations d’azote sont séparées et indisponibles dans la
représentation principale. Les vrais zéros PWHT sont conservés. Seuls les synonymes
de procédés documentés sont regroupés. Les fichiers bruts sont inchangés.

La cohorte conserve 607 lignes avec au moins une absence dans le noyau 13,
soit 1 075 cellules. Ni, Cr et Mo sont absents sur 58,8 %, 53,2 % et 53,0 %
de la cohorte. Passer de 13 à 16 variables **ajoute des colonnes, pas des lignes**.
Le master n’est jamais globalement imputé pour fournir les modèles de CV.

Dans chaque train : (1) moyenne/écart-type numériques sur les valeurs observées ;
(2) encodage one-hot du procédé, catégorie inconnue vers vecteur nul ;
(3) médianes du train ; (4) garde des couples PWHT imputés via des couples
compatibles réellement présents dans le train. Les couples PWHT sont complets
dans cette cohorte. Les observations connues sont préservées ; les labels ne
sont jamais imputés. La SVR standardise aussi y dans son train puis inverse
cette transformation. Aucune ACP prédictive n’est incluse dans les pipelines.

L’ACP descriptive porte sur 1 339 observations avec onze entrées exactes
complètes, standardisées, sans imputation. PC1=27,02 %, PC2=19,03 % ; cumul
deux axes=46,05 %, trois axes=61,26 %. Elle décrit cette sous-population et
n’est pas réutilisée pour la validation des modèles.

![Figure 2 - Variance expliquée de l’ACP descriptive sur onze entrées.](figures/15_acp_descriptive_fr.png)

## 4. Métriques et protocoles de validation

Pour n observations, avec y observé, ŷ prédit et ȳ moyenne observée :

- MAE = (1/n) Σ |yᵢ - ŷᵢ| : erreur absolue moyenne, métrique de réglage.
- RMSE = √[(1/n) Σ (yᵢ - ŷᵢ)²] : davantage sensible aux grandes erreurs.
- R² = 1 - Σ(yᵢ - ŷᵢ)² / Σ(yᵢ - ȳ)² : sans unité, peut être négatif.

Les MAE/RMSE conservent l’unité de la cible. R²=0 correspond à la référence
constante égale à la moyenne de la validation ; cette référence mathématique
diffère de la baseline entraînée à la médiane de y. Les scores OOF réunissent
toutes les prédictions externes. **R² OOF et moyenne des R² des plis diffèrent**,
car les variances des validations et leurs effectifs diffèrent. SD des cinq
plis n’est pas un intervalle de confiance.

Les deux expériences sont imbriquées : cinq plis externes, trois internes,
mêmes labels et mêmes partitions par cible entre les méthodes comparées.
Les transformations apprises et le choix famille/paramètres restent internes
[3]. KFold aléatoire : shuffle seed42 en externe, seed43+pli en interne.
Groupé : séries des identifiants et liens de doublons, sans partage entre
trains et validations. Une série peut contenir plusieurs conditions ; elle
n’est ni une éprouvette unique certifiée ni une publication systématiquement
identifiée. Les groupes restent des proxies conservateurs.

La validation aléatoire mesure la prédiction dans la population représentée ;
la groupée teste le transfert vers des séries absentes. Le haut score aléatoire
ne démontre pas IID. En moyenne, 99,0/99,9/99,8/100 % des validations
YS/UTS/allongement/Charpy partagent une série avec le train. Pour Charpy,
65 % partagent une condition de soudage, parfois à une autre température.

**Tableau 2 - Résultats de la sélection interne avec dispersion entre plis.**

| Cible | MAE aléatoire ± SD | R² aléatoire ± SD | MAE groupée ± SD | R² groupé ± SD |
| --- | --- | --- | --- | --- |
| YS | 31,630 ± 4,114 | 0,755 ± 0,063 | 56,757 ± 12,398 | 0,337 ± 0,161 |
| UTS | 23,861 ± 0,906 | 0,836 ± 0,027 | 54,344 ± 13,181 | 0,334 ± 0,228 |
| Allongement | 2,054 ± 0,239 | 0,660 ± 0,058 | 3,517 ± 0,516 | 0,157 ± 0,220 |
| Charpy* | 16,461 ± 1,161 | 0,776 ± 0,062 | 35,752 ± 11,863 | 0,075 ± 0,138 |

## 5. Comparaison de toutes les familles supervisées

Toutes les familles utilisent les mêmes pipelines 16/médiane, sauf la baseline
qui prédit seulement la médiane de y. Ridge est le contrôle linéaire régularisé ;
SVR RBF et RF capturent des relations non linéaires ; kNN est le contrôle local.

Grilles internes : Ridge alpha=0,01/0,1/1/10/100/1 000 ; SVR C=1/10/100,
gamma=scale/0,05, epsilon=0,05/0,2 ; RF 300 arbres, feuille=1/2/5,
profondeur libre/10, max_features=0,5/1, seed42 ; kNN k=3/5/9/15, L1/L2,
poids uniformes. 39 configurations au total par cible/pli, baseline incluse.

**Tableau 3 - Validation aléatoire : familles évaluées séparément.**

| Cible | Modèle | MAE ± SD | RMSE | R² ± SD |
| --- | --- | --- | --- | --- |
| YS (MPa) | Médiane de y | 70,032 ± 4,087 | 92,774 | -0,031 ± 0,040 |
| YS (MPa) | Ridge | 54,047 ± 3,440 | 70,005 | 0,412 ± 0,053 |
| YS (MPa) | SVR RBF | 31,747 ± 3,900 | 45,403 | 0,754 ± 0,046 |
| YS (MPa) | Random Forest | 31,242 ± 4,038 | 44,172 | 0,765 ± 0,064 |
| YS (MPa) | kNN | 38,144 ± 2,497 | 56,273 | 0,619 ± 0,059 |
| UTS (MPa) | Médiane de y | 68,879 ± 4,438 | 91,419 | -0,050 ± 0,019 |
| UTS (MPa) | Ridge | 44,319 ± 3,535 | 60,137 | 0,538 ± 0,118 |
| UTS (MPa) | SVR RBF | 23,861 ± 0,906 | 35,989 | 0,836 ± 0,027 |
| UTS (MPa) | Random Forest | 26,906 ± 1,907 | 39,165 | 0,805 ± 0,045 |
| UTS (MPa) | kNN | 33,452 ± 4,870 | 48,626 | 0,697 ± 0,098 |
| Allongement (points de %) | Médiane de y | 4,019 ± 0,149 | 4,903 | -0,015 ± 0,019 |
| Allongement (points de %) | Ridge | 3,011 ± 0,152 | 3,923 | 0,345 ± 0,119 |
| Allongement (points de %) | SVR RBF | 2,268 ± 0,198 | 3,227 | 0,556 ± 0,094 |
| Allongement (points de %) | Random Forest | 2,054 ± 0,239 | 2,835 | 0,660 ± 0,058 |
| Allongement (points de %) | kNN | 2,423 ± 0,260 | 3,305 | 0,530 ± 0,117 |
| Charpy* (J) | Médiane de y | 36,756 ± 2,813 | 51,989 | -0,069 ± 0,037 |
| Charpy* (J) | Ridge | 26,913 ± 0,587 | 34,170 | 0,529 ± 0,113 |
| Charpy* (J) | SVR RBF | 17,393 ± 0,988 | 25,068 | 0,749 ± 0,043 |
| Charpy* (J) | Random Forest | 16,099 ± 1,027 | 22,636 | 0,795 ± 0,035 |
| Charpy* (J) | kNN | 19,253 ± 1,518 | 29,586 | 0,651 ± 0,055 |

**Tableau 4 - Validation groupée : familles évaluées séparément.**

| Cible | Modèle | MAE ± SD | RMSE | R² ± SD |
| --- | --- | --- | --- | --- |
| YS (MPa) | Médiane de y | 70,449 ± 10,682 | 92,501 | -0,073 ± 0,052 |
| YS (MPa) | Ridge | 69,387 ± 6,953 | 88,202 | -0,025 ± 0,362 |
| YS (MPa) | SVR RBF | 59,350 ± 9,755 | 76,275 | 0,264 ± 0,144 |
| YS (MPa) | Random Forest | 54,139 ± 10,658 | 69,570 | 0,390 ± 0,132 |
| YS (MPa) | kNN | 73,496 ± 9,189 | 94,956 | -0,140 ± 0,151 |
| UTS (MPa) | Médiane de y | 72,664 ± 15,237 | 93,729 | -0,180 ± 0,114 |
| UTS (MPa) | Ridge | 61,898 ± 13,272 | 77,232 | 0,179 ± 0,152 |
| UTS (MPa) | SVR RBF | 52,861 ± 11,679 | 70,542 | 0,316 ± 0,145 |
| UTS (MPa) | Random Forest | 48,905 ± 7,269 | 65,236 | 0,394 ± 0,160 |
| UTS (MPa) | kNN | 68,538 ± 14,821 | 90,258 | -0,115 ± 0,121 |
| Allongement (points de %) | Médiane de y | 4,086 ± 0,309 | 4,962 | -0,062 ± 0,047 |
| Allongement (points de %) | Ridge | 3,658 ± 0,362 | 4,735 | 0,016 ± 0,229 |
| Allongement (points de %) | SVR RBF | 3,670 ± 0,345 | 4,534 | 0,106 ± 0,167 |
| Allongement (points de %) | Random Forest | 3,339 ± 0,342 | 4,218 | 0,226 ± 0,146 |
| Allongement (points de %) | kNN | 3,983 ± 0,328 | 4,908 | -0,060 ± 0,223 |
| Charpy* (J) | Médiane de y | 36,035 ± 16,909 | 50,603 | -0,149 ± 0,251 |
| Charpy* (J) | Ridge | 34,752 ± 10,268 | 45,433 | 0,069 ± 0,213 |
| Charpy* (J) | SVR RBF | 35,963 ± 8,404 | 44,879 | 0,091 ± 0,206 |
| Charpy* (J) | Random Forest | 33,033 ± 10,974 | 43,560 | 0,138 ± 0,209 |
| Charpy* (J) | kNN | 35,725 ± 12,222 | 48,624 | -0,099 ± 0,354 |

La RF fournit une référence polyvalente. La SVR est particulièrement utile
pour UTS en aléatoire. Cela ne signifie pas qu’une famille domine toutes les
cibles et tous les contextes ; les choix complets viennent d’une nouvelle CV5,
jamais du classement externe ci-dessus.

## 6. Ce que les diagnostics ont changé

Le premier benchmark groupé 13/itérative donnait des R² RF moyens de
0,079/0,194/0,125/0,017 pour YS/UTS/allongement/Charpy. Avec 16/médiane,
les mêmes familles RF atteignent 0,390/0,394/0,226/0,138. Cette comparaison
change deux facteurs ; les sensibilités factorielles les examinent séparément.

**Tableau 5 - Sensibilités RF, mêmes labels/plis ; les scénarios incomplets ne
sont pas comparables directement à cinq plis réussis.**

| Cible | Schéma / imputation | Plis réussis / 5 | MAE | R² |
| --- | --- | --- | --- | --- |
| YS | 11 / médiane | 5 | 68,978 | 0,000 |
| YS | 11 / itérative | 5 | 69,136 | -0,001 |
| YS | 13 / médiane | 5 | 64,983 | 0,102 |
| YS | 13 / itérative | 5 | 65,876 | 0,079 |
| YS | 16 / médiane | 5 | 54,139 | 0,390 |
| YS | 16 / itérative | 4 | 60,801 | 0,156 |
| UTS | 11 / médiane | 5 | 57,312 | 0,179 |
| UTS | 11 / itérative | 5 | 58,377 | 0,151 |
| UTS | 13 / médiane | 5 | 57,838 | 0,185 |
| UTS | 13 / itérative | 5 | 57,653 | 0,194 |
| UTS | 16 / médiane | 5 | 48,905 | 0,394 |
| UTS | 16 / itérative | 3 | 57,320 | -0,069 |
| Allongement | 11 / médiane | 5 | 3,690 | 0,076 |
| Allongement | 11 / itérative | 5 | 3,679 | 0,063 |
| Allongement | 13 / médiane | 5 | 3,741 | 0,060 |
| Allongement | 13 / itérative | 5 | 3,559 | 0,125 |
| Allongement | 16 / médiane | 5 | 3,339 | 0,226 |
| Allongement | 16 / itérative | 2 | 3,965 | -0,099 |
| Charpy* | 11 / médiane | 5 | 35,139 | 0,018 |
| Charpy* | 11 / itérative | 5 | 34,711 | 0,002 |
| Charpy* | 13 / médiane | 5 | 33,699 | 0,084 |
| Charpy* | 13 / itérative | 5 | 34,709 | 0,017 |
| Charpy* | 16 / médiane | 5 | 33,033 | 0,138 |
| Charpy* | 16 / itérative | 0 | Non calculé | Non calculé |

Sur 480 évaluations prévues, 436 réussissent ; 44 sont indisponibles après
11 échecs de convergence itérative. Le schéma 16/itérative ne termine que
4/3/2/0 plis pour YS/UTS/allongement/Charpy. La médiane est adoptée pour sa
stabilité dans ces données, pas comme méthode universellement supérieure.
À médiane identique, le gain MAE OOF RF de 13 à 16 est de 11,06 MPa pour YS
[3,09 ; 20,19] et 8,80 MPa pour UTS [2,38 ; 15,40], bootstrap descriptif par
groupes. Les gains d’allongement et Charpy sont moins établis.

Dans le RF initial 13/itérative, environ 56 % de la SSE YS et 51 % de la SSE
UTS proviennent des biais moyens entre séries. Les R² train YS/UTS sont
0,795/0,842, contre 0,079/0,194 en validation groupée. Les absences seules
n’expliquent pas tout : les lignes X complètes ne sont pas systématiquement
meilleures. Pour Charpy, MAE initiale hors plages X≈53 J contre≈28 J sinon.
Ces diagnostics concernent ce benchmark initial, pas automatiquement les
modèles 16/médiane ni COREG.

La permutation des blocs du RF initial augmente la MAE YS de 9,13 MPa pour
la composition et de 3,88 MPa pour PWHT ; UTS de 10,75 et 10,42 MPa.
La température d’essai Charpy augmente sa MAE de 7,47 J. Ces importances
décrivent l’utilisation des entrées dans le modèle ; elles ne sont pas
des effets métallurgiques causaux. Les contributions par chemins d’arbres
reconstruisent exactement les prédictions, mais ne sont pas des valeurs SHAP.

## 7. COREG : protocole, résultats et conclusion

COREG est une méthode de régression semi-supervisée à deux kNN échangeant des
estimations retenues selon leur cohérence locale [2]. Notre variante utilise
les mêmes X avec L1/L2, k=3/5/9/15 choisi en interne, une sortie moyenne,
100 candidats actifs maximum et 100 tours. Le gain local de SSE doit dépasser
`1e-12 × max(1,var(y_train)) × k`. Un candidat accepté est transmis à l’autre
régression ; son ID n’est pas réutilisé. Le voisinage source inclut les
pseudo-labels déjà ajoutés. Arrêt sans gain positif dans le pool actif, pool
épuisé ou budget atteint ; un arrêt local ne prouve pas la convergence globale.

Protocole **inductif** : aucun X/label de validation dans le pool, exclusion
des groupes de validation en groupé. Le preprocessing est appris sur les vrais
labels du train, figé pendant la boucle. Les X transformés identiques sont
dédupliqués dans le pool, et ceux déjà représentés dans le vrai train retirés ;
garder le plus petit raw ID. Tous les vrais labels sont conservés, y compris
leurs répétitions. L1/L2 et cette politique de pool sont des variantes du projet.

**Tableau 6 - COREG et moyenne kNN sans pseudo-labels au même k.** Gain positif
= amélioration de MAE OOF ; intervalle descriptif bootstrap par séries, 2 000
tirages seed42. MAE moyenne des plis et gain OOF utilisent des agrégations distinctes.

| CV | Cible | MAE COREG | R² COREG | MAE kNN même k | Gain MAE OOF [intervalle] |
| --- | --- | --- | --- | --- | --- |
| Aléatoire | YS | 37,919 | 0,629 | 38,241 | 0,322 [-0,060 ; 0,782] |
| Aléatoire | UTS | 33,037 | 0,709 | 33,319 | 0,283 [-0,154 ; 0,886] |
| Aléatoire | Allongement | 2,402 | 0,535 | 2,392 | -0,011 [-0,035 ; 0,013] |
| Groupée | YS | 71,074 | -0,056 | 70,817 | -0,272 [-1,144 ; 0,523] |
| Groupée | UTS | 63,060 | 0,043 | 62,081 | -0,920 [-1,939 ; -0,275] |
| Groupée | Allongement | 3,904 | -0,028 | 3,879 | -0,024 [-0,106 ; 0,029] |

Les gains aléatoires YS et UTS restent modestes avec des intervalles couvrant
zéro. Allongement ne progresse pas ; les trois gains groupés sont négatifs.
Pour UTS groupé, l’intervalle reste entièrement négatif. COREG est moins bon
que la sélection supervisée dans les six cas. Les bases de graines 43/44,
avec k fixé, ne changent pas cette lecture. Le gain local n’évalue ni
l’exactitude des labels inconnus ni le transfert entre séries ; les deux
régressions peuvent partager et propager des erreurs. C’est une explication
possible, pas une cause identifiée. Aucun taux d’exactitude des pseudo-labels
n’est inventé. Le budget de tous les labels ne teste pas un scénario 25/50 %.

## 8. Charpy : ce qui est confirmé et ce qui reste exploratoire

Le modèle prédit **l’énergie à température connue**, pas la température à
énergie fixée. Deux colonnes distinctes et deux unités sont documentées [1] ;
aucun mélange d’unités dans une colonne n’est démontré. Les publications
originales montrent toutefois des règles d’échantillonnage différentes : deux
familles totalisent 174 points E(T) apparentés et une famille contient 31
points à 100 J compatibles avec des températures de transition. 21 groupes
restent non résolus. Dans la cohorte, 457/861 énergies sont 28 ou 100 J ;
cette fréquence ne classe pas à elle seule les protocoles.

Le résultat aléatoire Charpy est exploratoire ; la MAE groupée demeure élevée.
Il faut harmoniser les protocoles avant une conclusion opérationnelle. Il
n’existe aucun pool naturel sans énergie avec température connue : Charpy
n’est donc pas entraîné par COREG. Aucun masquage artificiel ni imputation
de température ne crée un pool.

## 9. Refits complets, fichiers et reproduction

Une nouvelle CV5 sélectionne famille et paramètres sur tous les labels,
séparément en aléatoire seed1042 ou par groupes. Les MAE suivantes sont des
scores de choix, pas des tests indépendants. Elles peuvent différer des
scores externes de la procédure imbriquée.

**Tableau 7 - Modèles supervisés complets retenus pour l’inférence.**

| CV de choix | Cible | Famille | MAE de sélection | Paramètres |
| --- | --- | --- | --- | --- |
| Aléatoire | YS | SVR RBF | 31,228 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": "scale"} |
| Aléatoire | UTS | SVR RBF | 24,060 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| Aléatoire | Allongement | Random Forest | 1,940 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| Aléatoire | Charpy* | Random Forest | 15,387 | {"model__max_depth": null, "model__max_features": 1.0, "model__min_samples_leaf": 1} |
| Groupée | YS | Random Forest | 58,695 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 2} |
| Groupée | UTS | SVR RBF | 46,555 | {"model__regressor__C": 10, "model__regressor__epsilon": 0.05, "model__regressor__gamma": 0.05} |
| Groupée | Allongement | Random Forest | 3,282 | {"model__max_depth": null, "model__max_features": 0.5, "model__min_samples_leaf": 1} |
| Groupée | Charpy* | Random Forest | 32,375 | {"model__max_depth": 10, "model__max_features": 0.5, "model__min_samples_leaf": 1} |

80 pipelines supervisées sont exportées : 40 aléatoires et 40 groupées.
COREG ajoute 108 pipelines : 90 externes et 18 complètes, contrôles inclus.
Total **188 pipelines** sous `models/`. Les 80 supervisées se répartissent
en 40 modèles de plis et 40 refits ; COREG en 30+6 modèles et 60+12 contrôles.
Les refits complets ont vu tous les labels et ne servent jamais à scorer
les plis. Le preprocessing et les métadonnées accompagnent chaque export.

37 tests ciblés passent. Pour COREG, l’audit recalcule 180 scores, vérifie
576 fits et 81 931 pseudo-labels sur tous les contextes, et recalcule
1 410 gains sur douze modèles. Ce cumul n’est pas un nombre d’observations
distinctes ; les mêmes U peuvent revenir dans des contextes de CV différents.
Tous les exports COREG sont rechargés et les 90 modèles externes reproduisent
leurs OOF. Les autres audits figurent dans les rapports 10 à 14.

Reproduction : notebooks 01 à 07, dépendances et noyau du projet, fichiers
bruts inchangés, CSV non imputés du master, manifests/hashes, seed42 et dérivées,
grilles et choix internes enregistrés. L’exécution COREG a été reprise après
interruption sans modifier les résultats principaux. Données générées,
environnements et modèles sont ignorés par Git.

## 10. Conclusion et limites pour le rapport final

Retenir les procédures supervisées 16/médiane comme référence principale pour
ce budget ; garder COREG comme expérience semi-supervisée évaluée. Choisir le
protocole selon l’usage : population déjà représentée ou série nouvelle.
Les variables/imputations ont été explorées après le premier benchmark sur
les mêmes données : même une CV imbriquée n’efface pas ce choix rétrospectif.
Une étude indépendante reste nécessaire pour évaluer toute la démarche.

Les recommandations étayées concernent la collecte et l’évaluation : mesurer
les compositions pertinentes plutôt que compter sur leur imputation, enregistrer
les conditions et protocoles d’essai, identifier éprouvettes/séries/publications,
échantillonner de nouvelles séries et valider sur leurs vrais labels.
Aucun réglage de soudage « optimal » ni seuil universel de bonne soudure n’est
déduit de ces associations. Une recommandation physique demande des essais
contrôlés et une validation experte.

Le rapport court inclut une trame Gantt. Le journal `specs/time_log.csv` ne
contient aucune heure : les responsabilités et temps réels restent à compléter
par l’équipe, sans confondre durée de calcul et travail humain.

## Références et preuves

[1] Cool, T. et Bhadeshia, H. K. D. H. [Documentation Cambridge MAP_DATA_WELD](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html), colonnes et unités, consultée le 10 octobre 2026.

[2] Zhou, Z.-H. et Li, M. (2005). [Semi-Supervised Regression with Co-Training](https://www.ijcai.org/Proceedings/05/Papers/0689.pdf). IJCAI, p. 908-913.

[3] Scikit-learn. [Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html), consultée le 10 octobre 2026.

[4] Cool, T. (1996). [Design of Steel Weld Deposits](https://www.phase-trans.msm.cam.ac.uk/2012/Cool_Thesis.pdf), thèse, Cambridge, section 6.4 ; contexte Charpy et variables supplémentaires.

[5] Projet, notebooks 01 à 07 et rapports 10 à 14 : protocoles, résultats locaux et audits reproductibles, 10 octobre 2026.

Les rapports détaillés [supervisé initial](10_supervised_training.md),
[diagnostics](11_performance_diagnostics.md), [aléatoire](12_random_kfold_training.md),
[exports groupés](13_grouped_exports_and_ssl_plan.md) et [COREG](14_coreg_training.md)
documentent les réserves, contrôles et tableaux complets. Les décisions actives
sont dans [specs/spec.md](../specs/spec.md).
