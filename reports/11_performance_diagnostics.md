# Diagnostic approfondi des faibles performances

Investigation du 10 octobre 2026, branche `task/salh-supervised-training`.
Code autonome et sorties dans [notebook 04](../notebooks/04_diagnostics.ipynb).
Le [benchmark 03](10_supervised_training.md) est conservé.

Les faibles scores sont étayés : les modèles apprennent des relations dans les
séries d'entraînement mais les transfèrent mal à certaines nouvelles séries.
Un R² de 0,5 n'est pas un minimum garanti par le choix d'un algorithme. Cette
investigation sépare les constats mesurés des explications encore hypothétiques.
Les résultats sont rétrospectifs, sur les mêmes données déjà examinées ; ils ne
constituent pas une validation indépendante d'un choix issu de ce diagnostic.

Comparaison descriptive RF, mêmes populations et cinq plis groupés :

| target | MAE_13_iterative | R2_13_iterative | folds | MAE_16_median | R2_16_median | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- |
| yield_strength | 65.876 | 0.079 | 5 | 54.139 | 0.390 | 0.394 |
| uts | 57.653 | 0.194 | 5 | 48.905 | 0.394 | 0.473 |
| elongation | 3.559 | 0.125 | 5 | 3.339 | 0.226 | 0.251 |
| charpy_J | 34.709 | 0.017 | 5 | 33.033 | 0.138 | 0.227 |

Les schémas 13/itérative et 16/médiane diffèrent par deux décisions. Les tableaux factoriels ci-dessous isolent l'extension à imputation identique et l'imputation à schéma identique. Cette comparaison n'adopte pas automatiquement un nouveau modèle de production.

## Méthode annoncée avant les calculs

1. Décomposer les erreurs hors entraînement par groupe, mesurer le biais,
   l'écart train/validation et le domaine des entrées. Reconstruire les RF à
   partir des paramètres internes exportés et exiger les mêmes prédictions.
   Rééchantillonner les groupes pour le gain vs baseline ; faire varier la
   quantité de groupes d'entraînement sans toucher à la validation.
2. Vérifier les définitions Charpy et les publications originales. Établir une
   correspondance par composition/conditions, sans classer les lignes à partir
   d'E=28/100 seulement. Consigner ce qui est confirmé et ce qui reste inconnu.
3. Comparer 11/13/16 entrées × médiane/itérative, avec les quatre familles et
   grilles originales, les mêmes labels/plis. Choisir uniquement sur MAE interne,
   comparer aussi le choix MSE et la sélection conjointe interne. Expliquer les
   modèles par permutation externe et contributions de chemins d'arbres.

Cohorte : 1 555 lignes/44 groupes ; labels YS=706, UTS=677, allongement=631,
Charpy=861. Cinq plis externes, trois internes, groupes exportés du notebook 02.
Seed 42 ; courbes d'apprentissage seeds 42/43. Ni/Cr/Mo sont ajoutés sans
refiltrer la cohorte. Baseline médiane de y du train. X ne contient aucune autre
sortie mécanique, dureté, FATT50, ID ou numéro de groupe/pli. Charpy ajoute sa
température connue en °C ; énergie prédite en J. Aucun label manquant n'est imputé.

Preprocessing refait dans chaque train : statistiques numériques, encodage du
procédé, imputation médiane ou BayesianRidge itérative et projection des couples
PWHT sur des couples réellement présents dans ce train. Valeurs observées
préservées ; colonnes totalement absentes, non-convergence et incompatibilités
PWHT refusées explicitement. Ni/Cr/Mo absents ne sont pas transformés en zéro.

## 1. Les modèles apprennent, mais généralisent mal entre séries

Le RF présente un grand écart entre entraînement et validation. Ses scores train
ne constituent pas une preuve de précision sur une nouvelle soudure. Les modèles
linéaires ont aussi de faibles R² train : cela indique que la capacité non linéaire
seule ne suffit pas à résoudre le transfert entre populations.

| target | train_MAE | validation_MAE | train_R2 | validation_R2 |
| --- | --- | --- | --- | --- |
| charpy_J | 8.395 | 34.709 | 0.941 | 0.017 |
| elongation | 1.326 | 3.559 | 0.859 | 0.125 |
| uts | 23.794 | 57.653 | 0.842 | 0.194 |
| yield_strength | 30.078 | 65.876 | 0.795 | 0.079 |

La dispersion prédite est comprimée : le rapport écart-type prédit/observé est
≈0,53 pour YS et Charpy, ≈0,68 pour UTS et ≈0,64 pour l'allongement. Les cas très
résistants ou très tenaces sont souvent sous-estimés. La décomposition suivante
mesure exactement la part de SSE portée par le biais moyen de chaque série :
Σ_g n_g × biais_g² / SSE. Le reste est la variation d'erreur à l'intérieur des
séries. Les labels de validation servent uniquement à cette analyse après coup.

| target | between_group_SST_fraction | group_bias_SSE_fraction | R2 | RMSE | RMSE_required_for_pooled_R2_05 |
| --- | --- | --- | --- | --- | --- |
| charpy_J | 0.291 | 0.365 | 0.116 | 47.485 | 35.709 |
| elongation | 0.544 | 0.500 | 0.156 | 4.482 | 3.451 |
| uts | 0.549 | 0.506 | 0.280 | 75.928 | 63.264 |
| yield_strength | 0.480 | 0.564 | 0.091 | 87.721 | 65.043 |

Les R² ci-dessus sont calculés sur toutes les prédictions OOF réunies. Ils
n'égalent pas la moyenne des cinq R², chaque pli ayant son propre SST. Pour
R²=0,5 sur ces mêmes labels, il faudrait abaisser le RMSE OOF à environ 65 MPa
(YS), 63 MPa (UTS), 3,45 points de % (allongement), 36 J (Charpy). Ces seuils
ne démontrent pas qu'ils sont atteignables avec les entrées disponibles.

### Séries qui concentrent les erreurs : `yield_strength`

| group | n | MAE | bias | SSE_fraction |
| --- | --- | --- | --- | --- |
| Hunt&-Di-1994 | 16 | 166.842 | -166.842 | 0.087 |
| Birmingham | 8 | 236.989 | -236.989 | 0.087 |
| SurianEtAl-C-1991 | 8 | 232.561 | -232.561 | 0.087 |
| Evans-Nb/Mn-1991 | 77 | 64.007 | -52.380 | 0.084 |
| Gar&K-1975 | 37 | 90.904 | -63.340 | 0.070 |

### Séries qui concentrent les erreurs : `uts`

| group | n | MAE | bias | SSE_fraction |
| --- | --- | --- | --- | --- |
| Evans-Nb/Mn-1991 | 77 | 56.465 | -49.884 | 0.094 |
| Evans-Cr/CMn-1989 | 40 | 59.159 | -41.062 | 0.082 |
| Sw&Rog-1973 | 4 | 239.972 | -210.014 | 0.075 |
| SurianEtAl-C-1991 | 8 | 173.458 | -173.458 | 0.075 |
| EvansLetter | 52 | 56.873 | -40.979 | 0.074 |

### Séries qui concentrent les erreurs : `elongation`

| group | n | MAE | bias | SSE_fraction |
| --- | --- | --- | --- | --- |
| Evans-Nb/Mn-1991 | 76 | 4.312 | 3.625 | 0.149 |
| EvansLetter | 51 | 4.302 | 3.074 | 0.115 |
| RR82011 | 46 | 4.588 | -4.417 | 0.102 |
| Evans-Cr/CMn-1989 | 40 | 3.556 | 3.096 | 0.075 |
| Gar&K-1975 | 37 | 3.451 | -0.132 | 0.061 |

### Séries qui concentrent les erreurs : `charpy_J`

| group | n | MAE | bias | SSE_fraction |
| --- | --- | --- | --- | --- |
| Evans-StressRelief-1991 | 94 | 60.822 | -25.473 | 0.248 |
| PantK-1990 | 12 | 134.821 | 134.821 | 0.116 |
| Mart | 63 | 48.675 | 13.872 | 0.096 |
| Ditt | 14 | 110.165 | -110.165 | 0.093 |
| SvenGret-1990 | 80 | 40.642 | -24.646 | 0.088 |

Les signes de biais montrent des décalages de niveau entre séries, pas seulement
une dispersion aléatoire. L'absence de Cr/Ni/Mo dans le noyau 13 est une explication
plausible pour certaines familles alliées ; son importance effective est testée
par l'extension 16. D'autres facteurs restent exclus ou incomplets (Nb, V, Cu,
Ti/Al/B, structure, conditions précises). Le diagnostic ne prouve pas quel facteur
cause chaque décalage. Les groupes sont des séries inférées des identifiants,
pas des publications toutes identifiées.

### Le changement de domaine est surtout visible pour Charpy

| target | indicator | present | n | MAE |
| --- | --- | --- | --- | --- |
| charpy_J | missing_X | False | 512 | 33.484 |
| charpy_J | missing_X | True | 349 | 37.118 |
| charpy_J | outside_observed_X | False | 624 | 28.191 |
| charpy_J | outside_observed_X | True | 237 | 52.772 |
| charpy_J | unseen_process | False | 716 | 32.880 |
| charpy_J | unseen_process | True | 145 | 45.214 |
| elongation | missing_X | False | 358 | 3.639 |
| elongation | missing_X | True | 273 | 3.436 |
| elongation | outside_observed_X | False | 522 | 3.669 |
| elongation | outside_observed_X | True | 109 | 2.985 |
| elongation | unseen_process | False | 592 | 3.502 |
| elongation | unseen_process | True | 39 | 4.294 |
| uts | missing_X | False | 409 | 58.500 |
| uts | missing_X | True | 268 | 53.509 |
| uts | outside_observed_X | False | 558 | 54.930 |
| uts | outside_observed_X | True | 119 | 63.997 |
| uts | unseen_process | False | 645 | 54.601 |
| uts | unseen_process | True | 32 | 95.290 |
| yield_strength | missing_X | False | 425 | 72.547 |
| yield_strength | missing_X | True | 281 | 57.445 |
| yield_strength | outside_observed_X | False | 570 | 64.950 |
| yield_strength | outside_observed_X | True | 136 | 73.181 |
| yield_strength | unseen_process | False | 667 | 64.441 |
| yield_strength | unseen_process | True | 39 | 102.360 |

| target | spearman_abs_error_nearest_distance | fraction_outside_X | fraction_y_outside_train |
| --- | --- | --- | --- |
| charpy_J | 0.410 | 0.275 | 0.007 |
| elongation | 0.044 | 0.173 | 0.002 |
| uts | 0.140 | 0.176 | 0.001 |
| yield_strength | 0.162 | 0.193 | 0.003 |

Pour Charpy, les lignes hors plages X du train ont une MAE ≈53 J contre ≈28 J
pour les autres ; corrélation de rang erreur/distance ≈0,41. Ce signal est faible
pour l'allongement et modeste pour la traction. Un dépassement min/max univarié
ne détecte pas toutes les combinaisons inédites ; la distance transformée dépend
des échelles et de l'imputation. Les comparaisons sont descriptives et confondues
par les séries : elles ne prouvent pas un effet causal d'une absence ou d'un procédé.

L'hypothèse « l'imputation explique tout » est contredite : les cas X complets
ne sont pas systématiquement meilleurs. Pour YS, leur MAE est même plus forte.
L'absence peut identifier une autre population ; elle n'est pas un traitement
aléatoire. Les collisions exactes des entrées complètes montrent quelques labels
différents pour les mêmes X enregistrés, mais leur nombre ne permet pas de
conclure à un plancher global irréductible.

| target | complete_X_rows | rows_in_X_collisions | rows_in_ambiguous_X_collisions | collision_within_SSE |
| --- | --- | --- | --- | --- |
| yield_strength | 425 | 54 | 40 | 948.500 |
| uts | 409 | 56 | 46 | 233.500 |
| elongation | 358 | 56 | 42 | 23.370 |
| charpy_J | 512 | 28 | 18 | 4574.333 |

### Gain RF vs médiane et quantité de données

Bootstrap apparié par groupes (2 000 rééchantillonnages). Gain positif = baisse
de MAE. L'intervalle est conditionnel aux splits/modèles déjà entraînés, sans refit.
Il n'est pas un intervalle complet de généralisation sur de nouvelles publications.

| target | gain_MAE | group_bootstrap_low | group_bootstrap_high | groups |
| --- | --- | --- | --- | --- |
| yield_strength | 4.165 | -3.292 | 11.374 | 40 |
| uts | 14.621 | 6.277 | 25.508 | 39 |
| elongation | 0.539 | -0.064 | 1.359 | 34 |
| charpy_J | 1.802 | -4.545 | 7.051 | 24 |

### Même RF, découpage par groupes ou aléatoire des lignes

Paramètres fixes avant ce contrôle : 300 arbres, feuille minimale 2, profondeur libre, toutes les features à chaque split, seed 42. Chaque transformation est ajustée uniquement sur son train ; aucun réglage ne réutilise des labels de cette validation.

| target | protocol | MAE_mean | R2_mean | mean_fraction_valid_rows_in_train_groups | OOF_MAE | OOF_RMSE | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| charpy_J | group_fixed_RF | 34.378 | -0.025 | 0.000 | 34.583 | 48.166 | 0.090 |
| charpy_J | random_row_fixed_RF | 16.652 | 0.773 | 1.000 | 16.651 | 23.910 | 0.776 |
| elongation | group_fixed_RF | 3.549 | 0.114 | 0.000 | 3.533 | 4.505 | 0.148 |
| elongation | random_row_fixed_RF | 2.477 | 0.531 | 0.998 | 2.477 | 3.332 | 0.534 |
| uts | group_fixed_RF | 56.709 | 0.190 | 0.000 | 55.740 | 75.826 | 0.282 |
| uts | random_row_fixed_RF | 38.003 | 0.625 | 0.999 | 38.004 | 54.838 | 0.624 |
| yield_strength | group_fixed_RF | 66.134 | 0.077 | 0.000 | 66.852 | 87.982 | 0.085 |
| yield_strength | random_row_fixed_RF | 43.532 | 0.554 | 0.990 | 43.525 | 61.480 | 0.553 |

Le partage aléatoire répond à une autre question : prédire des lignes quand la plupart des séries sont déjà présentes dans le train. Une hausse indique l'aide fournie par ces observations apparentées. Le score principal reste celui des nouvelles séries ; aucune validation n'est remplacée pour atteindre 0,5.

Dans le benchmark initial 13/itérative, seul le gain UTS est clairement positif
vs baseline selon ce contrôle. Les autres intervalles
incluent zéro. Les deux graines des courbes d'apprentissage constituent une petite
sensibilité, pas une estimation précise de l'effet d'un nouvel achat de données.

| target | fraction | MAE | R2 | train_MAE |
| --- | --- | --- | --- | --- |
| charpy_J | 0.500 | 35.733 | -0.039 | 7.560 |
| charpy_J | 0.750 | 33.672 | 0.094 | 8.230 |
| charpy_J | 1.000 | 34.709 | 0.017 | 8.395 |
| elongation | 0.500 | 3.610 | 0.115 | 1.204 |
| elongation | 0.750 | 3.757 | 0.060 | 1.266 |
| elongation | 1.000 | 3.559 | 0.125 | 1.326 |
| uts | 0.500 | 62.931 | 0.072 | 20.985 |
| uts | 0.750 | 59.031 | 0.153 | 22.609 |
| uts | 1.000 | 57.653 | 0.194 | 23.794 |
| yield_strength | 0.500 | 68.771 | 0.007 | 28.086 |
| yield_strength | 0.750 | 68.712 | 0.028 | 29.003 |
| yield_strength | 1.000 | 65.876 | 0.079 | 30.078 |

YS/UTS bénéficient ici de davantage de groupes. Charpy et allongement n'ont pas
une amélioration monotone : la diversité et l'information disponible paraissent
aussi importantes que le nombre de lignes. Les hyperparamètres restent ceux
choisis initialement sur le train complet ; ce contrôle n'est pas une courbe
optimisée séparément à chaque taille.

### Explicabilité : quelles informations le RF utilise-t-il ?

Permutation des entrées brutes de validation via la pipeline entière, dix fois
par pli. Les blocs sont déplacés ensemble pour préserver leurs liens internes.
Augmentation de MAE positive = information utile au modèle dans ce contexte.
La dispersion répétitions/plis n'est pas un intervalle causal ; des variables
corrélées peuvent se remplacer et une permutation peut créer une situation
rare. Les importances d'un modèle faible ne sont pas une hiérarchie métallurgique.

| target | feature | MAE_increase | repeat_fold_sd |
| --- | --- | --- | --- |
| charpy_J | bloc_temperature_essai | 7.469 | 3.046 |
| charpy_J | bloc_soudage | 1.473 | 1.781 |
| charpy_J | bloc_composition | 0.831 | 1.190 |
| charpy_J | bloc_PWHT | 0.646 | 0.945 |
| charpy_J | bloc_procede | 0.203 | 0.360 |
| elongation | bloc_composition | 0.544 | 0.269 |
| elongation | bloc_soudage | 0.224 | 0.154 |
| elongation | bloc_PWHT | 0.188 | 0.136 |
| elongation | bloc_procede | 0.052 | 0.068 |
| uts | bloc_composition | 10.747 | 5.439 |
| uts | bloc_PWHT | 10.417 | 7.275 |
| uts | bloc_soudage | 3.454 | 2.643 |
| uts | bloc_procede | 0.538 | 1.147 |
| yield_strength | bloc_composition | 9.125 | 4.827 |
| yield_strength | bloc_PWHT | 3.876 | 4.140 |
| yield_strength | bloc_soudage | 1.014 | 1.845 |
| yield_strength | bloc_procede | 0.548 | 0.914 |

La température d'essai est le bloc le plus utile pour Charpy ; la composition
et PWHT dominent la traction. Cela confirme que les modèles exploitent de
l'information, sans réussir à transférer tous les niveaux entre séries.

Les trois plus grandes erreurs de chaque cible sont aussi expliquées par les
chemins des arbres. Pour chaque prédiction, base moyenne des racines + somme
des contributions = prédiction, vérifié numériquement. Les contributions sont
dépendantes de l'ordre des splits, peuvent porter sur une valeur imputée et ne
sont ni des SHAP ni des effets causaux. Elles montrent pourquoi le modèle a
produit sa valeur, sans prouver pourquoi la mesure physique diffère.

| target | raw_row_id | group | outer_fold | baseline | y_true | y_pred | abs_error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| charpy_J | 1206 | PantK-1990 | 1 | 86.768 | 23.000 | 187.807 | 164.807 |
| charpy_J | 1210 | PantK-1990 | 1 | 86.768 | 27.000 | 189.207 | 162.207 |
| charpy_J | 1209 | PantK-1990 | 1 | 86.768 | 8.000 | 159.244 | 151.244 |
| elongation | 1160 | Ga&K-1975 | 0 | 26.421 | 16.000 | 28.586 | 12.586 |
| elongation | 422 | Evans-Nb/Mn-1991 | 1 | 26.192 | 19.800 | 31.515 | 11.715 |
| elongation | 269 | Evans-Cr/CMn-1989 | 2 | 25.841 | 18.600 | 29.818 | 11.218 |
| uts | 722 | Evans-AlEl9Cr1Mo-1994 | 0 | 592.952 | 1151.000 | 729.368 | 421.632 |
| uts | 1378 | Sw&Rog-1973 | 4 | 589.371 | 909.000 | 549.056 | 359.944 |
| uts | 1377 | Sw&Rog-1973 | 4 | 589.371 | 901.000 | 548.609 | 352.391 |
| yield_strength | 710 | SurianEtAl-C-1991 | 4 | 503.056 | 808.000 | 489.576 | 318.424 |
| yield_strength | 722 | Evans-AlEl9Cr1Mo-1994 | 0 | 507.657 | 920.000 | 601.801 | 318.199 |
| yield_strength | 708 | SurianEtAl-C-1991 | 4 | 503.056 | 798.000 | 487.434 | 310.566 |

Exemples concrets du master : ligne 1209 (`PantK-1990`), Cr=8,7 %, énergie observée 8 J/prédite 159 J ; ligne 722, Ni=3,01 % et Cr=9,17 %, UTS observée 1 151 MPa/prédite 729 MPa. Ni/Cr/Mo ne sont pas des entrées du benchmark 13. La ligne 422 a Nb=985 ppm, qui reste exclu même du schéma 16. Ces valeurs montrent une information omise disponible dans le master ; le test d'extension mesure son apport prédictif sans affirmer un effet causal pour chaque erreur.

## 2. Charpy : colonnes correctes, échantillonnages à distinguer

La [documentation Cambridge](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html)
sépare température °C et énergie J. **Aucune colonne à unités mélangées n'a été
démontrée.** La courbe utilisateur représente bien deux colonnes distinctes.
Le [modèle de la thèse Cool](https://www.phase-trans.msm.cam.ac.uk/2012/Cool_Thesis.pdf),
§6.4 p.85/tableau 6.5 p.86, prédit une énergie avec température en entrée ; il
emploie aussi la limite d'élasticité et davantage de compositions. Ses résultats
ne sont pas une référence directement comparable à nos entrées 13.
L'[article de 1995](https://www.phase-trans.msm.cam.ac.uk/abstracts/toughness.pdf)
emploie YS/microstructure et une séparation aléatoire d'exemples, différente de
notre transfert à des séries inédites.

Correspondances vérifiées :

- [Svensson–Gretoft 1990](https://canteach.candu.org/content%20library/20053409.pdf),
  p.455-s/456-s : les 16 compositions C/Si/Mn/P/S/N/O et les conditions de soudage
  concordent, soit 80 lignes. Essais à cinq températures, cinq éprouvettes par
  température. Protocole E(T) confirmé ; précision de transcription des figures
  non certifiée ligne par ligne.
- [Evans 1986, stress relieving](https://www.researchgate.net/publication/277011176_The_Effect_of_Stress_Relieving_on_the_Microstructure_and_Properties_of_C-Mn_all-weld-metal_deposits),
  p.326-s/327-s : 16 compositions C/Si/Mn et six conditions concordent avec
  `Evans-StressRelief-1991`, 94 lignes. Environ 35 éprouvettes par courbe complète
  de transition ; l'année 1991 de l'identifiant ne correspond pas à la publication.
  Famille de courbes E(T) confirmée, valeurs ponctuelles non redigitisées.
- [Evans 1989, chromium](https://www.researchgate.net/publication/326989878_Effect_of_chromium_on_the_microstructure_and_properties_of_C-Mn_all-weld_metal_deposits),
  tableau 1 : 20 compositions C/Si/Mn/Cr concordent. Les figures 20/21 présentent
  les températures correspondant à 100 J ; les 31 couples Charpy du groupe
  ont E=100 J. Cela étaye une extraction de températures de transition ; chaque
  température enregistrée n'est pas encore vérifiée par redigitisation.

457 des 861 énergies sont exactement 28 ou 100 J (53,1 %). Cette fréquence est
une signature de sélection plausible, pas une preuve de protocole pour chaque ligne.

Un point T100/100 appartient aussi à la courbe E(T), mais sa température a été
choisie en fonction de l'énergie. Il renseigne la position de la transition,
pas toute la courbe ni ses plateaux. Mélanger des règles d'échantillonnage peut
modifier la distribution évaluée et favoriser des prédictions autour des
énergies de seuil. **Cela n'établit pas que ce facteur explique à lui seul le
faible score Charpy.** Les points à 28/100 ne sont pas supprimés automatiquement.

| group | n | protocol_status |
| --- | --- | --- |
| Blond&-1984 | 6 | unresolved_by_original_series_source |
| Chandel&-1985 | 19 | unresolved_by_original_series_source |
| Ditt | 14 | unresolved_by_original_series_source |
| Evans-Al/CMn-1990 | 35 | unresolved_by_original_series_source |
| Evans-AlTi-1994 | 60 | unresolved_by_original_series_source |
| Evans-B/9Cr1Mo-1994 | 24 | unresolved_by_original_series_source |
| Evans-Cr/CMn-1989 | 31 | source_matched_threshold_sampling_likely |
| Evans-Mn-1977 | 8 | unresolved_by_original_series_source |
| Evans-Nb/Mn-1991 | 78 | unresolved_by_original_series_source |
| Evans-Ni/CMn-1990 | 30 | unresolved_by_original_series_source |
| Evans-StressRelief-1991 | 94 | confirmed_transition_curve_E_T_family |
| Evans-Ti/CMn-1992 | 20 | unresolved_by_original_series_source |
| Evans-Ti/Mn-1992 | 40 | unresolved_by_original_series_source |
| Evans-intpss-1978 | 16 | unresolved_by_original_series_source |
| EvansLetter | 104 | unresolved_by_original_series_source |
| Icici&-1992 | 16 | unresolved_by_original_series_source |
| JorgeEtAl-1993 | 16 | unresolved_by_original_series_source |
| Kluket-CuMnB-1994 | 12 | unresolved_by_original_series_source |
| Mart | 63 | unresolved_by_original_series_source |
| PantK-1990 | 12 | unresolved_by_original_series_source |
| Pat-1981 | 63 | unresolved_by_original_series_source |
| SurianEtAl-C-1991 | 8 | unresolved_by_original_series_source |
| SvenGret-1990 | 80 | confirmed_E_at_preselected_temperatures |
| Wats-1981 | 12 | unresolved_by_original_series_source |

Les 21 autres groupes restent non résolus par leur publication originale,
656 lignes au total. Le tableau d'audit expose leurs signatures descriptives
sans leur attribuer un protocole certain. Deux séries E(T) confirmées (174 lignes)
ne suffisent pas à une nouvelle validation imbriquée à cinq plis par sources.
Les essais ne sont pas redéfinis en température-cible dans cette investigation.
Le benchmark Charpy reste exploratoire, sur les 861 couples rapportés.

Point supplémentaire d'unité : le tableau Svensson exprime Ti/Al/Sn/As/Sb en
wt% alors que la documentation globale annonce ppm pour certaines colonnes.
Ce constat appuie la quarantaine existante ; il justifie un futur correctif
par source, pas une conversion globale. Le master et le benchmark sont préservés.

## 3. Sensibilités : entrées, imputation et objectif de réglage

480 évaluations prévues. Chaque famille garde sa grille d'origine et sélectionne
ses paramètres par MAE interne. Les 11 entrées retirent O/N ; 13 les ajoutent ;
16 ajoutent Ni/Cr/Mo. Même population de validation pour toutes les combinaisons.
Les fractions manquantes de Ni/Cr/Mo sont environ 59/53/53 %, même après le
filtre strict13. Le choix de médiane peut être plus stable qu'une reconstruction
itérative, mais l'amélioration prédictive ne certifie pas les valeurs imputées.

Évaluations complétées : **436/480**. Échecs consignés : **11**.

| target | outer_fold | feature_set | imputer | model | stage | reason |
| --- | --- | --- | --- | --- | --- | --- |
| yield_strength | 4 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| uts | 3 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| uts | 4 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| elongation | 2 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| elongation | 3 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| elongation | 4 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| charpy_J | 0 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| charpy_J | 1 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| charpy_J | 2 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| charpy_J | 3 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |
| charpy_J | 4 | A1b_16 | iterative | all | preflight | Imputation itérative non convergée : réviser le schéma dans le train. |

### Random Forest — toutes les combinaisons

| target | feature_set | imputer | folds | MAE_mean | R2_mean | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- |
| yield_strength | A0_11 | median | 5 | 68.978 | 0.000 | 0.006 |
| yield_strength | A0_11 | iterative | 5 | 69.136 | -0.001 | -0.002 |
| yield_strength | A1_13 | median | 5 | 64.983 | 0.102 | 0.111 |
| yield_strength | A1_13 | iterative | 5 | 65.876 | 0.079 | 0.091 |
| yield_strength | A1b_16 | median | 5 | 54.139 | 0.390 | 0.394 |
| yield_strength | A1b_16 | iterative | 4 | 60.801 | 0.156 | 0.143 |
| uts | A0_11 | median | 5 | 57.312 | 0.179 | 0.275 |
| uts | A0_11 | iterative | 5 | 58.377 | 0.151 | 0.255 |
| uts | A1_13 | median | 5 | 57.838 | 0.185 | 0.283 |
| uts | A1_13 | iterative | 5 | 57.653 | 0.194 | 0.280 |
| uts | A1b_16 | median | 5 | 48.905 | 0.394 | 0.473 |
| uts | A1b_16 | iterative | 3 | 57.320 | -0.069 | 0.069 |
| elongation | A0_11 | median | 5 | 3.690 | 0.076 | 0.111 |
| elongation | A0_11 | iterative | 5 | 3.679 | 0.063 | 0.097 |
| elongation | A1_13 | median | 5 | 3.741 | 0.060 | 0.094 |
| elongation | A1_13 | iterative | 5 | 3.559 | 0.125 | 0.156 |
| elongation | A1b_16 | median | 5 | 3.339 | 0.226 | 0.251 |
| elongation | A1b_16 | iterative | 2 | 3.965 | -0.099 | -0.089 |
| charpy_J | A0_11 | median | 5 | 35.139 | 0.018 | 0.114 |
| charpy_J | A0_11 | iterative | 5 | 34.711 | 0.002 | 0.111 |
| charpy_J | A1_13 | median | 5 | 33.699 | 0.084 | 0.189 |
| charpy_J | A1_13 | iterative | 5 | 34.709 | 0.017 | 0.116 |
| charpy_J | A1b_16 | median | 5 | 33.033 | 0.138 | 0.227 |
| charpy_J | A1b_16 | iterative | 0 | — | — | — |

### Toutes les familles

| target | feature_set | imputer | model | folds | MAE_mean | R2_mean | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| yield_strength | A0_11 | median | ridge | 5 | 70.745 | -0.058 | -0.018 |
| yield_strength | A0_11 | median | svr_rbf | 5 | 74.901 | -0.152 | -0.127 |
| yield_strength | A0_11 | median | random_forest | 5 | 68.978 | 0.000 | 0.006 |
| yield_strength | A0_11 | median | knn | 5 | 77.896 | -0.325 | -0.342 |
| yield_strength | A0_11 | iterative | ridge | 5 | 70.509 | -0.052 | -0.011 |
| yield_strength | A0_11 | iterative | svr_rbf | 5 | 76.722 | -0.230 | -0.222 |
| yield_strength | A0_11 | iterative | random_forest | 5 | 69.136 | -0.001 | -0.002 |
| yield_strength | A0_11 | iterative | knn | 5 | 78.863 | -0.340 | -0.363 |
| yield_strength | A1_13 | median | ridge | 5 | 71.142 | -0.077 | -0.017 |
| yield_strength | A1_13 | median | svr_rbf | 5 | 67.654 | 0.039 | 0.063 |
| yield_strength | A1_13 | median | random_forest | 5 | 64.983 | 0.102 | 0.111 |
| yield_strength | A1_13 | median | knn | 5 | 76.157 | -0.186 | -0.186 |
| yield_strength | A1_13 | iterative | ridge | 5 | 69.920 | -0.054 | 0.011 |
| yield_strength | A1_13 | iterative | svr_rbf | 5 | 69.283 | 0.004 | 0.014 |
| yield_strength | A1_13 | iterative | random_forest | 5 | 65.876 | 0.079 | 0.091 |
| yield_strength | A1_13 | iterative | knn | 5 | 76.872 | -0.208 | -0.213 |
| yield_strength | A1b_16 | median | ridge | 5 | 69.387 | -0.025 | 0.073 |
| yield_strength | A1b_16 | median | svr_rbf | 5 | 59.350 | 0.264 | 0.282 |
| yield_strength | A1b_16 | median | random_forest | 5 | 54.139 | 0.390 | 0.394 |
| yield_strength | A1b_16 | median | knn | 5 | 73.496 | -0.140 | -0.089 |
| yield_strength | A1b_16 | iterative | ridge | 4 | 67.049 | -0.032 | 0.039 |
| yield_strength | A1b_16 | iterative | svr_rbf | 4 | 62.413 | 0.137 | 0.152 |
| yield_strength | A1b_16 | iterative | random_forest | 4 | 60.801 | 0.156 | 0.143 |
| yield_strength | A1b_16 | iterative | knn | 4 | 67.232 | -0.029 | -0.003 |
| uts | A0_11 | median | ridge | 5 | 71.337 | -0.119 | -0.006 |
| uts | A0_11 | median | svr_rbf | 5 | 66.981 | -0.059 | 0.069 |
| uts | A0_11 | median | random_forest | 5 | 57.312 | 0.179 | 0.275 |
| uts | A0_11 | median | knn | 5 | 70.889 | -0.215 | -0.101 |
| uts | A0_11 | iterative | ridge | 5 | 71.348 | -0.126 | -0.008 |
| uts | A0_11 | iterative | svr_rbf | 5 | 68.375 | -0.222 | -0.044 |
| uts | A0_11 | iterative | random_forest | 5 | 58.377 | 0.151 | 0.255 |
| uts | A0_11 | iterative | knn | 5 | 69.948 | -0.181 | -0.079 |
| uts | A1_13 | median | ridge | 5 | 69.423 | -0.107 | 0.030 |
| uts | A1_13 | median | svr_rbf | 5 | 65.442 | 0.022 | 0.136 |
| uts | A1_13 | median | random_forest | 5 | 57.838 | 0.185 | 0.283 |
| uts | A1_13 | median | knn | 5 | 72.934 | -0.217 | -0.099 |
| uts | A1_13 | iterative | ridge | 5 | 65.882 | 0.054 | 0.134 |
| uts | A1_13 | iterative | svr_rbf | 5 | 63.403 | 0.039 | 0.139 |
| uts | A1_13 | iterative | random_forest | 5 | 57.653 | 0.194 | 0.280 |
| uts | A1_13 | iterative | knn | 5 | 66.649 | -0.089 | 0.026 |
| uts | A1b_16 | median | ridge | 5 | 61.898 | 0.179 | 0.252 |
| uts | A1b_16 | median | svr_rbf | 5 | 52.861 | 0.316 | 0.384 |
| uts | A1b_16 | median | random_forest | 5 | 48.905 | 0.394 | 0.473 |
| uts | A1b_16 | median | knn | 5 | 68.538 | -0.115 | -0.012 |
| uts | A1b_16 | iterative | ridge | 3 | 61.150 | -0.013 | 0.090 |
| uts | A1b_16 | iterative | svr_rbf | 3 | 56.713 | -0.095 | 0.047 |
| uts | A1b_16 | iterative | random_forest | 3 | 57.320 | -0.069 | 0.069 |
| uts | A1b_16 | iterative | knn | 3 | 56.239 | -0.063 | 0.088 |
| elongation | A0_11 | median | ridge | 5 | 4.093 | -0.078 | -0.046 |
| elongation | A0_11 | median | svr_rbf | 5 | 4.122 | -0.111 | -0.062 |
| elongation | A0_11 | median | random_forest | 5 | 3.690 | 0.076 | 0.111 |
| elongation | A0_11 | median | knn | 5 | 4.151 | -0.176 | -0.139 |
| elongation | A0_11 | iterative | ridge | 5 | 4.089 | -0.074 | -0.042 |
| elongation | A0_11 | iterative | svr_rbf | 5 | 4.135 | -0.117 | -0.068 |
| elongation | A0_11 | iterative | random_forest | 5 | 3.679 | 0.063 | 0.097 |
| elongation | A0_11 | iterative | knn | 5 | 4.158 | -0.172 | -0.135 |
| elongation | A1_13 | median | ridge | 5 | 3.950 | -0.227 | -0.149 |
| elongation | A1_13 | median | svr_rbf | 5 | 3.889 | -0.008 | 0.022 |
| elongation | A1_13 | median | random_forest | 5 | 3.741 | 0.060 | 0.094 |
| elongation | A1_13 | median | knn | 5 | 4.051 | -0.110 | -0.074 |
| elongation | A1_13 | iterative | ridge | 5 | 3.733 | 0.094 | 0.124 |
| elongation | A1_13 | iterative | svr_rbf | 5 | 3.880 | -0.007 | 0.029 |
| elongation | A1_13 | iterative | random_forest | 5 | 3.559 | 0.125 | 0.156 |
| elongation | A1_13 | iterative | knn | 5 | 3.911 | -0.093 | -0.049 |
| elongation | A1b_16 | median | ridge | 5 | 3.658 | 0.016 | 0.072 |
| elongation | A1b_16 | median | svr_rbf | 5 | 3.670 | 0.106 | 0.140 |
| elongation | A1b_16 | median | random_forest | 5 | 3.339 | 0.226 | 0.251 |
| elongation | A1b_16 | median | knn | 5 | 3.983 | -0.060 | -0.014 |
| elongation | A1b_16 | iterative | ridge | 2 | 3.824 | 0.125 | 0.130 |
| elongation | A1b_16 | iterative | svr_rbf | 2 | 4.022 | -0.100 | -0.089 |
| elongation | A1b_16 | iterative | random_forest | 2 | 3.965 | -0.099 | -0.089 |
| elongation | A1b_16 | iterative | knn | 2 | 3.964 | -0.028 | -0.019 |
| charpy_J | A0_11 | median | ridge | 5 | 35.288 | 0.066 | 0.161 |
| charpy_J | A0_11 | median | svr_rbf | 5 | 38.685 | -0.184 | -0.032 |
| charpy_J | A0_11 | median | random_forest | 5 | 35.139 | 0.018 | 0.114 |
| charpy_J | A0_11 | median | knn | 5 | 37.576 | -0.256 | -0.067 |
| charpy_J | A0_11 | iterative | ridge | 5 | 36.048 | 0.048 | 0.118 |
| charpy_J | A0_11 | iterative | svr_rbf | 5 | 38.710 | -0.206 | -0.041 |
| charpy_J | A0_11 | iterative | random_forest | 5 | 34.711 | 0.002 | 0.111 |
| charpy_J | A0_11 | iterative | knn | 5 | 37.763 | -0.254 | -0.049 |
| charpy_J | A1_13 | median | ridge | 5 | 37.304 | -0.233 | -0.404 |
| charpy_J | A1_13 | median | svr_rbf | 5 | 35.066 | 0.091 | 0.182 |
| charpy_J | A1_13 | median | random_forest | 5 | 33.699 | 0.084 | 0.189 |
| charpy_J | A1_13 | median | knn | 5 | 35.343 | -0.084 | 0.055 |
| charpy_J | A1_13 | iterative | ridge | 5 | 35.737 | 0.072 | 0.125 |
| charpy_J | A1_13 | iterative | svr_rbf | 5 | 36.142 | 0.035 | 0.135 |
| charpy_J | A1_13 | iterative | random_forest | 5 | 34.709 | 0.017 | 0.116 |
| charpy_J | A1_13 | iterative | knn | 5 | 34.924 | -0.139 | 0.006 |
| charpy_J | A1b_16 | median | ridge | 5 | 34.752 | 0.069 | 0.149 |
| charpy_J | A1b_16 | median | svr_rbf | 5 | 35.963 | 0.091 | 0.175 |
| charpy_J | A1b_16 | median | random_forest | 5 | 33.033 | 0.138 | 0.227 |
| charpy_J | A1b_16 | median | knn | 5 | 35.725 | -0.099 | 0.038 |
| charpy_J | A1b_16 | iterative | ridge | 0 | — | — | — |
| charpy_J | A1b_16 | iterative | svr_rbf | 0 | — | — | — |
| charpy_J | A1b_16 | iterative | random_forest | 0 | — | — | — |
| charpy_J | A1b_16 | iterative | knn | 0 | — | — | — |

### Sélection conjointe réalisée à l'intérieur du train

Le scénario avec le meilleur R² externe du tableau n'est pas annoncé comme
modèle validé. Dans chaque pli, schéma/imputation/famille/paramètres sont choisis
sur la MAE interne ; sa prédiction externe est ensuite évaluée une seule fois.
Cette évaluation imbriquée demeure rétrospective à l'échelle de cette investigation.

| target | MAE_mean | R2_mean | folds | OOF_MAE | OOF_RMSE | OOF_R2 |
| --- | --- | --- | --- | --- | --- | --- |
| charpy_J | 36.022 | -0.100 | 5 | 36.420 | 49.616 | 0.035 |
| elongation | 3.494 | 0.164 | 5 | 3.476 | 4.393 | 0.190 |
| uts | 54.344 | 0.334 | 5 | 53.749 | 69.245 | 0.401 |
| yield_strength | 56.757 | 0.337 | 5 | 57.535 | 75.344 | 0.329 |

| target | outer_fold | feature_set | imputer | model | inner_MAE | MAE | R2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| yield_strength | 0 | A1b_16 | median | random_forest | 60.524 | 43.617 | 0.472 |
| yield_strength | 1 | A1b_16 | median | random_forest | 54.516 | 68.484 | 0.204 |
| yield_strength | 2 | A1b_16 | median | svr_rbf | 61.168 | 49.940 | 0.273 |
| yield_strength | 3 | A1b_16 | median | random_forest | 63.281 | 50.282 | 0.543 |
| yield_strength | 4 | A1b_16 | median | svr_rbf | 58.141 | 71.462 | 0.191 |
| uts | 0 | A1b_16 | median | ridge | 53.429 | 74.904 | 0.038 |
| uts | 1 | A1b_16 | median | random_forest | 50.614 | 49.485 | 0.155 |
| uts | 2 | A1b_16 | median | svr_rbf | 52.589 | 38.756 | 0.399 |
| uts | 3 | A1b_16 | median | random_forest | 52.538 | 52.599 | 0.555 |
| uts | 4 | A1b_16 | median | random_forest | 47.986 | 55.979 | 0.523 |
| elongation | 0 | A1b_16 | median | random_forest | 3.352 | 2.859 | 0.468 |
| elongation | 1 | A1b_16 | median | random_forest | 3.042 | 3.633 | 0.166 |
| elongation | 2 | A1_13 | iterative | random_forest | 3.580 | 3.495 | 0.013 |
| elongation | 3 | A1b_16 | median | random_forest | 3.416 | 3.239 | 0.251 |
| elongation | 4 | A1b_16 | median | svr_rbf | 3.644 | 4.246 | -0.080 |
| charpy_J | 0 | A1_13 | median | svr_rbf | 37.781 | 29.214 | -0.044 |
| charpy_J | 1 | A1_13 | iterative | knn | 35.027 | 25.658 | -0.609 |
| charpy_J | 2 | A1_13 | median | svr_rbf | 39.416 | 30.880 | -0.090 |
| charpy_J | 3 | A1_13 | median | random_forest | 24.431 | 52.904 | 0.203 |
| charpy_J | 4 | A1_13 | iterative | knn | 33.840 | 41.452 | 0.038 |

### Optimiser MAE ou MSE ?

Le contrôle A1_13/itérative choisit les paramètres selon MSE interne, sur les
mêmes configurations. À validation identique, minimiser MSE maximise R² ; cela
ne garantit pas qu'un choix interne améliorera R² sur une nouvelle série.

| target | model | MAE_mean | RMSE_mean | R2_mean |
| --- | --- | --- | --- | --- |
| charpy_J | knn | 35.146 | 48.032 | -0.074 |
| charpy_J | random_forest | 34.266 | 46.229 | 0.027 |
| charpy_J | ridge | 35.737 | 45.839 | 0.072 |
| charpy_J | svr_rbf | 36.577 | 46.316 | 0.040 |
| elongation | knn | 3.911 | 5.018 | -0.093 |
| elongation | random_forest | 3.599 | 4.513 | 0.116 |
| elongation | ridge | 3.790 | 4.636 | 0.071 |
| elongation | svr_rbf | 3.899 | 4.828 | -0.009 |
| uts | knn | 69.139 | 91.061 | -0.129 |
| uts | random_forest | 57.429 | 75.811 | 0.206 |
| uts | ridge | 65.882 | 82.991 | 0.054 |
| uts | svr_rbf | 63.046 | 82.717 | 0.052 |
| yield_strength | knn | 76.537 | 98.017 | -0.191 |
| yield_strength | random_forest | 66.257 | 85.780 | 0.076 |
| yield_strength | ridge | 70.116 | 91.084 | -0.058 |
| yield_strength | svr_rbf | 68.787 | 88.600 | 0.019 |

Comparaison RF des deux critères internes :

| target | MAE_selected_MAE | R2_selected_MAE | MAE_selected_MSE | R2_selected_MSE |
| --- | --- | --- | --- | --- |
| yield_strength | 65.876 | 0.079 | 66.257 | 0.076 |
| uts | 57.653 | 0.194 | 57.429 | 0.206 |
| elongation | 3.559 | 0.125 | 3.599 | 0.116 |
| charpy_J | 34.709 | 0.017 | 34.266 | 0.027 |

### Gain apparié de l’extension 16 vs 13

| target | model | imputer | status | gain_MAE | group_bootstrap_low | group_bootstrap_high | groups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| yield_strength | ridge | median | ok | 2.153 | -3.273 | 7.907 | 40.000 |
| yield_strength | ridge | iterative | incomplete | — | — | — | — |
| yield_strength | svr_rbf | median | ok | 8.470 | 2.149 | 17.139 | 40.000 |
| yield_strength | svr_rbf | iterative | incomplete | — | — | — | — |
| yield_strength | random_forest | median | ok | 11.058 | 3.093 | 20.188 | 40.000 |
| yield_strength | random_forest | iterative | incomplete | — | — | — | — |
| yield_strength | knn | median | ok | 2.999 | -1.690 | 9.164 | 40.000 |
| yield_strength | knn | iterative | incomplete | — | — | — | — |
| uts | ridge | median | ok | 7.456 | -1.116 | 17.276 | 39.000 |
| uts | ridge | iterative | incomplete | — | — | — | — |
| uts | svr_rbf | median | ok | 12.875 | 5.513 | 21.442 | 39.000 |
| uts | svr_rbf | iterative | incomplete | — | — | — | — |
| uts | random_forest | median | ok | 8.798 | 2.378 | 15.396 | 39.000 |
| uts | random_forest | iterative | incomplete | — | — | — | — |
| uts | knn | median | ok | 3.821 | -4.415 | 13.931 | 39.000 |
| uts | knn | iterative | incomplete | — | — | — | — |
| elongation | ridge | median | ok | 0.284 | -0.016 | 0.674 | 34.000 |
| elongation | ridge | iterative | incomplete | — | — | — | — |
| elongation | svr_rbf | median | ok | 0.218 | -0.098 | 0.622 | 34.000 |
| elongation | svr_rbf | iterative | incomplete | — | — | — | — |
| elongation | random_forest | median | ok | 0.389 | -0.045 | 0.874 | 34.000 |
| elongation | random_forest | iterative | incomplete | — | — | — | — |
| elongation | knn | median | ok | 0.072 | -0.201 | 0.393 | 34.000 |
| elongation | knn | iterative | incomplete | — | — | — | — |
| charpy_J | ridge | median | ok | 2.591 | -1.406 | 8.529 | 24.000 |
| charpy_J | ridge | iterative | incomplete | — | — | — | — |
| charpy_J | svr_rbf | median | ok | -0.891 | -2.427 | 0.529 | 24.000 |
| charpy_J | svr_rbf | iterative | incomplete | — | — | — | — |
| charpy_J | random_forest | median | ok | 0.648 | -0.211 | 1.636 | 24.000 |
| charpy_J | random_forest | iterative | incomplete | — | — | — | — |
| charpy_J | knn | median | ok | -0.449 | -2.295 | 1.605 | 24.000 |
| charpy_J | knn | iterative | incomplete | — | — | — | — |

À médiane identique, RF `yield_strength` : gain de MAE OOF de 11.06, intervalle du bootstrap par groupes [3.09, 20.19]. Le gain positif étaye l'information prédictive ajoutée par Ni/Cr/Mo, sous les limites de ce contrôle rétrospectif.

À médiane identique, RF `uts` : gain de MAE OOF de 8.80, intervalle du bootstrap par groupes [2.38, 15.40]. Le gain positif étaye l'information prédictive ajoutée par Ni/Cr/Mo, sous les limites de ce contrôle rétrospectif.

Le gain de l'extension 16 selon la disponibilité Ni/Cr/Mo est aussi rapporté.
Ces strates ne sont pas randomisées et n'isolent pas l'effet causal de l'imputation.

| target | imputer | missing_NiCrMo | n | groups | MAE_13 | MAE_16 | gain_MAE | complete_OOF_pairing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| yield_strength | median | 0 | 276 | 19 | 80.753 | 63.480 | 17.273 | True |
| yield_strength | median | 1 | 48 | 4 | 78.467 | 57.107 | 21.360 | True |
| yield_strength | median | 2 | 106 | 5 | 63.970 | 51.865 | 12.105 | True |
| yield_strength | median | 3 | 276 | 13 | 49.684 | 47.034 | 2.649 | True |
| yield_strength | iterative | 0 | 209 | 14 | 79.163 | 63.816 | 15.347 | False |
| yield_strength | iterative | 1 | 40 | 3 | 58.780 | 46.978 | 11.802 | False |
| yield_strength | iterative | 2 | 90 | 4 | 54.855 | 57.691 | -2.837 | False |
| yield_strength | iterative | 3 | 224 | 10 | 54.324 | 65.065 | -10.741 | False |
| uts | median | 0 | 240 | 17 | 66.616 | 54.952 | 11.664 | True |
| uts | median | 1 | 71 | 6 | 65.206 | 48.249 | 16.958 | True |
| uts | median | 2 | 106 | 5 | 57.662 | 53.148 | 4.514 | True |
| uts | median | 3 | 260 | 12 | 45.441 | 39.770 | 5.671 | True |
| uts | iterative | 0 | 100 | 7 | 54.547 | 51.894 | 2.653 | False |
| uts | iterative | 1 | 45 | 4 | 50.802 | 68.266 | -17.464 | False |
| uts | iterative | 2 | 90 | 4 | 52.047 | 60.051 | -8.003 | False |
| uts | iterative | 3 | 207 | 8 | 47.096 | 55.801 | -8.705 | False |
| elongation | median | 0 | 230 | 15 | 4.095 | 3.459 | 0.636 | True |
| elongation | median | 1 | 36 | 3 | 3.891 | 2.173 | 1.718 | True |
| elongation | median | 2 | 106 | 5 | 3.678 | 3.798 | -0.119 | True |
| elongation | median | 3 | 259 | 12 | 3.378 | 3.184 | 0.194 | True |
| elongation | iterative | 0 | 78 | 4 | 4.084 | 4.234 | -0.150 | False |
| elongation | iterative | 1 | 28 | 2 | 2.019 | 1.324 | 0.695 | False |
| elongation | iterative | 2 | 50 | 3 | 2.287 | 3.173 | -0.886 | False |
| elongation | iterative | 3 | 124 | 5 | 3.933 | 4.716 | -0.783 | False |
| charpy_J | median | 0 | 250 | 9 | 43.040 | 41.472 | 1.568 | True |
| charpy_J | median | 1 | 40 | 2 | 45.260 | 42.568 | 2.691 | True |
| charpy_J | median | 2 | 140 | 4 | 25.758 | 26.565 | -0.807 | True |
| charpy_J | median | 3 | 431 | 9 | 30.134 | 29.737 | 0.397 | True |

### Reconstruction de valeurs observées Ni/Cr/Mo

Masquage artificiel de 20 % des valeurs connues en validation, mêmes masques pour les deux imputations, puis reconstruction avec un imputer ajusté sur le train uniquement. Cibles et masques n'interviennent pas dans le choix des modèles. Erreurs en % massique ; ce diagnostic sur valeurs initialement renseignées ne reproduit pas nécessairement le mécanisme des absences naturelles.

| target | imputer | feature | n | MAE | MSE |
| --- | --- | --- | --- | --- | --- |
| charpy_J | iterative | Cr | 40 | 4.792 | 38.465 |
| charpy_J | iterative | Mo | 30 | 1.060 | 1.270 |
| charpy_J | iterative | Ni | 33 | 1.035 | 1.676 |
| charpy_J | median | Cr | 40 | 1.504 | 2.954 |
| charpy_J | median | Mo | 30 | 0.696 | 0.594 |
| charpy_J | median | Ni | 33 | 0.782 | 1.595 |
| elongation | iterative | Cr | 64 | 1.945 | 8.747 |
| elongation | iterative | Mo | 58 | 0.362 | 0.338 |
| elongation | iterative | Ni | 58 | 0.723 | 2.689 |
| elongation | median | Cr | 64 | 1.098 | 6.020 |
| elongation | median | Mo | 58 | 0.407 | 0.297 |
| elongation | median | Ni | 58 | 0.325 | 0.508 |
| uts | iterative | Cr | 52 | 1.705 | 6.399 |
| uts | iterative | Mo | 43 | 0.399 | 0.434 |
| uts | iterative | Ni | 45 | 0.537 | 0.887 |
| uts | median | Cr | 52 | 1.556 | 8.026 |
| uts | median | Mo | 43 | 0.370 | 0.271 |
| uts | median | Ni | 45 | 0.439 | 0.857 |
| yield_strength | iterative | Cr | 71 | 1.419 | 5.669 |
| yield_strength | iterative | Mo | 70 | 0.313 | 0.207 |
| yield_strength | iterative | Ni | 71 | 0.419 | 0.620 |
| yield_strength | median | Cr | 71 | 1.612 | 10.773 |
| yield_strength | median | Mo | 70 | 0.388 | 0.262 |
| yield_strength | median | Ni | 71 | 0.388 | 0.655 |

Les comparaisons gardent les mêmes cellules uniquement dans les contextes où les deux méthodes ont réussi. Les autres tentatives restent exportées, avec leurs échecs. La reconstruction itérative ne domine pas systématiquement la médiane : par exemple, pour Charpy, sa MAE de Cr est ≈4,79 % contre ≈1,50 % avec médiane sur les mêmes cellules. Une imputation plus complexe ne garantit donc pas une meilleure reconstruction hors série.

## Constats établis et limites des explications

- Établi : grand écart train/validation du RF initial ; biais de niveau par séries ;
  prédictions comprimées ; dans le noyau 13, gain vs baseline plus robuste pour UTS.
- Établi : Charpy présente davantage de difficultés hors plages X ; la température
  d'essai apporte de l'information au modèle ; plusieurs règles d'échantillonnage
  sont étayées par les sources. La fraction totale de protocoles concernés reste inconnue.
- Hypothèses plausibles : compositions/états métallurgiques omis ou insuffisamment
  renseignés, différences de séries et précision des labels numérisés. Ces causes
  ne sont pas identifiées séparément par l'expérience actuelle.
- Non démontré : l'imputation explique tout ; le bruit expérimental fixe un plafond
  R²<0,5 ; une ACP ou un modèle multi-sorties résoudrait le problème ; retirer
  les séries difficiles serait une amélioration de généralisation.

L'extension à 16 et médiane donne un signal utile pour la traction, surtout YS/UTS.
Pour Charpy, son gain apparié vs 13 à médiane identique est seulement ≈0,65 J,
avec intervalle [−0,21 ; 1,64] incluant zéro. La sélection conjointe interne donne
un R² moyen −0,100 pour Charpy, malgré le R² descriptif RF 16/médiane de 0,138.
Cela expose la fragilité du transfert et du choix entre pipelines, plutôt qu'une
réussite confirmée par le meilleur résultat externe.

Avant un choix opérationnel : choisir le périmètre d'utilisation et les entrées
réellement mesurées, poursuivre les correspondances source/protocoles et vérifier
les unités/états. Après un choix issu de cette investigation, collecter une
validation indépendante par nouvelles séries. COREG reste différé ; les
pseudo-labels ne créeraient pas l'information physique absente des entrées.

## Reproduction et contrôles

Exécuter 02 → 03 → 04 avec les dépendances du projet. Les calculs prennent plus
longtemps que les tests rapides. Les exports sont sous
`data/processed/experiments/salh_diagnostics_v1/`, ignorés par Git ; les tableaux
et figures sont conservés dans le notebook. Aucun modèle entraîné n'est commité.

Hashes des exports 02/03 vérifiés avant lecture ; reproduction des 20 RF de
référence vérifiée ; préservation des entrées observées dans les preflights ;
groupes train/validation disjoints ; gains appariés sur les mêmes IDs ;
décomposition additive des chemins d'arbres contrôlée. La suite rapide couvre
les décompositions SSE/SST, permutations de blocs, bootstrap par groupes et
éligibilité inchangée. Elle ne remplace pas la reproduction des entraînements.
