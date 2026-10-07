# Proposition de preprocessing et de validation de l'ACP

Date : 5 octobre 2026. Statut : plan proposé, non implémenté dans le notebook. Aucun dataset imputé, aucune conversion d'unité et aucun résultat d'ACP ou de modèle ne sont produits par ce document.

**Mise à jour du 5 octobre 2026 :** le plan a ensuite été approuvé et son workflow
de comparaison implémenté dans `notebooks/01_eda.ipynb`. La proposition originale
ci-dessous est conservée pour traçabilité. Le protocole effectivement exécuté est
documenté dans `specs/spec.md` ; les résultats locaux, matrices, provenance et
manifestes sont exportés dans `data/processed/preprocessing/`. Les ambiguïtés
métier restent signalées, sans correction inventée ; aucune cible ni méthode
finale n'est adoptée par cette implémentation.

## Objectif et portée

Préparer des matrices adaptées à chaque analyse, en conservant la distinction entre mesures et estimations. Maximiser le nombre de cellules remplies n'est pas un critère de qualité : une colonne presque entièrement reconstruite peut orienter artificiellement l'ACP. Une faible disponibilité ne démontre pas une faible importance métallurgique.

L'ACP des entrées explore la structure de composition et de procédé. Elle ne définit pas à elle seule la qualité d'une soudure et ses contributions ne mesurent pas l'importance prédictive pour une cible. Les propriétés mécaniques sont explorées séparément pour documenter des cibles candidates ; aucune cible ni aucun seuil de qualité n'est adopté ici.

## Vérifications supplémentaires sur les données brutes

Lecture de `data/raw/welddb.data` avec les 44 noms de colonnes du notebook, séparation par espaces, `N` comme absence. Une valeur exacte est un jeton correspondant entièrement à `[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?`. Les nombres ne sont pas corrigés pour les unités suspectes. Les indices cités sont ceux de pandas, commençant à zéro.

- 1 652 lignes, 1 490 identifiants distincts, dont 91 identifiants répétés. Un identifiant distinct ne garantit pas l'indépendance d'une publication ou d'une série.
- Le courant et la tension ont exactement le même masque d'absence : 248 lignes. Les deux variables de traitement thermique ont également le même masque : 13 lignes. Les couples température et énergie Charpy ont le même masque : 773 lignes.
- Le nickel manque sur 70,0 % des 1 140 lignes codées `MMA`, contre 14,6 % des 261 lignes `SA`. La disponibilité dépend donc du procédé observé ; cela ne suffit pas à établir si le mécanisme est MAR ou MNAR.
- L'apport thermique médian est 1,0 kJ/mm lorsque le nickel manque et 1,8 kJ/mm lorsqu'il est renseigné. Les médianes du manganèse sont respectivement 1,35 et 1,08 wt%. Les populations observées et absentes diffèrent sur des variables disponibles.
- Le nickel est renseigné dans 50,0 % des lignes avec limite d'élasticité mesurée et dans 32,0 % des lignes avec énergie Charpy mesurée. La pertinence d'une préparation doit aussi être examinée dans le sous-ensemble propre à la tâche.
- Les onze entrées `carbon`, `silicon`, `manganese`, `sulphur`, `phosphorus`, `current`, `voltage`, `heat_input`, `interpass_temperature`, `pwht_temperature`, `pwht_time` sont toutes exactes dans 1 343 lignes. En ajoutant oxygène et azote, il reste 913 lignes complètes exactes. Ce sont des références exploratoires sélectionnées, pas des échantillons garantis représentatifs.
- Aucune ligne n'a une composition complète exacte sur les 21 éléments plus les six paramètres numériques de procédé/traitement listés ci-dessus.
- 650 lignes possèdent les quatre propriétés de traction exactes : limite d'élasticité, résistance maximale, allongement et réduction de section. Limite d'élasticité et résistance maximale ont une corrélation de Pearson de 0,915 sur 714 paires observées. Limite d'élasticité et allongement ont une corrélation de -0,681 sur 691 paires. Ces résultats sont descriptifs et peuvent refléter des effets de séries.
- Seulement 144 lignes possèdent à la fois limite d'élasticité et énergie Charpy. Aucune ligne n'a simultanément énergie Charpy et dureté renseignées, même en incluant les annotations de dureté. Une relation entre ces deux propriétés dans une matrice imputée ne serait pas directement étayée par des paires mesurées.
- Sur les 89 lignes avec les cinq fractions microstructurales exactes, 86 ont une somme de 100 %, trois ont une somme de 90 %, 99 % et 119 %. La somme de 119 % concerne l'indice 582, `Evans-Ti/CMn-1992-P0.1mic`. Vérifier exhaustivité, exclusivité des catégories et transcription avant toute renormalisation ; ne pas corriger automatiquement.
- Les neuf valeurs de vanadium `<5` appartiennent aux identifiants `EvansLetterC+...`, alors que la colonne est documentée en wt%. Cette concentration par série justifie un audit d'unité, sans prouver la bonne conversion.
- 610 lignes comportent simultanément température et durée de traitement thermique nulles. Aucun couple n'a un seul des deux nombres nul. Le sens « sans traitement » reste à confirmer ; ne pas imputer les deux paramètres indépendamment sans tenir compte du régime.
- Les 30 courants de 850–900 A sont tous associés à `SA`. Leur niveau ne justifie pas à lui seul une suppression.

| Variable ou bloc | Valeurs rapportées, annotations/censure comprises | Absences |
| --- | ---: | ---: |
| Cobalt | 129 | 92,2 % |
| Tungstène | 75 | 95,5 % |
| Étain | 296 | 82,1 % |
| Arsenic | 234 | 85,8 % |
| Antimoine | 260 | 84,3 % |
| Ferrite primaire | 98 | 94,1 % |
| Ferrite aciculaire | 90 | 94,6 % |
| Dureté | 138 | 91,6 % |
| FATT 50 | 31 | 98,1 % |
| Bore | 504, dont 419 censurées | 69,5 % |

Le bore illustre la différence entre absence et censure : il n'a que 85 nombres exacts, mais 504 observations rapportées. Une censure ne doit pas être comptée comme une absence pour décider de la disponibilité.

## Ordre proposé des opérations

1. **Compléter l'audit et définir les matrices.** Construire un dictionnaire des variables avec rôle (entrée, propriété candidate, identifiant, métadonnée), unité, statut, disponibilité par procédé et nombre de groupes observés. Examiner les absences conjointes et les effectifs de paires. La disponibilité au moment de la prédiction déterminera les entrées de chaque future tâche.
2. **Résoudre les ambiguïtés prioritaires.** Consulter les publications pour aluminium EPRI, étain/arsenic/antimoine Mart/Ditt, vanadium `<5`, limites `<0.01` de titane/aluminium, annotations d'azote, protocoles de dureté, polarité `0` et traitement thermique nul. Ne pas multiplier automatiquement toute valeur inférieure à 1 ppm par 10 000. Les cas non résolus restent explicitement ambigus et peuvent être exclus d'un scénario de référence.
3. **Construire une représentation fidèle.** Garder la donnée brute, la valeur numérique quand son sens est confirmé, les bornes, le statut original, le protocole et un éventuel indicateur d'ambiguïté d'unité. Une valeur inutilisable provisoirement ne devient pas une absence originale. Conserver un masque distinct des cellules estimées.
4. **Définir les groupes avant la comparaison des imputations.** Les identifiants identiques restent dans le même groupe. Inspecter ensuite variantes `ch1`, `ch2`, `mic`, `aw`, `ht` et publications pour regrouper les observations apparentées. Ne pas appliquer une suppression générique des suffixes sans vérifier les cas. Un groupement par publication peut servir de test de généralisation complémentaire, si sa provenance est documentée.
5. **Comparer des stratégies simples et multivariées sur les entrées.** Référence : médiane globale. Deuxième candidat : médiane par procédé si assez de groupes mesurés, avec repli global. Troisième candidat : imputation itérative avec contraintes physiques et auxiliaires de procédé. Fixer les mêmes groupes, les mêmes masques et la seed 42. La complexité ne préjuge pas de la qualité ; aucun gagnant n'est encore choisi.
6. **Vérifier reconstruction, distributions et relations.** Appliquer le protocole de masquage et de sensibilité ci-dessous avant de retenir une matrice d'ACP principale.
7. **Réaliser les ACP distinctes et leur analyse de sensibilité.** Publier les effectifs réellement mesurés et estimés, les choix d'échelle et les écarts entre scénarios. L'ACP exploratoire complète ne doit pas être réutilisée pour évaluer un modèle prédictif.

## Traitement proposé par statut

| Statut | Traitement candidat | Vérification |
| --- | --- | --- |
| Numérique exact | Conserver après audit des unités ; ne pas éliminer automatiquement les extrêmes | Cohérence par source, procédé et propriété ; valeurs originales inchangées |
| Censuré `<L` | Conserver limite et statut ; pour les concentrations non négatives d'unité confirmée, comparer `0`, `L/2` et `L/sqrt(2)` comme scénarios approximatifs | Respecter la borne ; mesurer la sensibilité de l'ACP. `0` est un scénario de borne inférieure, pas une mesure nulle. Un imputer ordinaire ne sait pas utiliser cette contrainte par cellule |
| Intervalle `150-200` | Garder les deux bornes ; milieu 175 °C comme approximation de référence | Comparer avec 150 et 200 °C pour les 38 lignes concernées |
| Annotation d'azote | Séparer les composantes et les marqueurs `tot`, `res`, `nd` ; utiliser un nombre uniquement après confirmation de son sens | Ne pas fusionner total et résiduel ni transformer `nd` en zéro sans preuve |
| Annotation de dureté | Extraire le nombre et conserver `Hv5`, `Hv10`, `Hv30` comme protocole | Confirmer la comparabilité et les unités avant regroupement ; réserver à une analyse secondaire vu la faible couverture |
| Absence `N` | Estimer uniquement dans la matrice adaptée à l'analyse, à partir des entrées disponibles | Conserver un masque d'imputation et comparer les méthodes ; jamais remplacer automatiquement par zéro |
| Catégorie | Normaliser seulement les synonymes documentés, puis utiliser comme auxiliaire ou encodage pour les modèles | Pour l'ACP principale, projeter/colorer les catégories comme information supplémentaire ; aucun codage ordinal arbitraire |

La distribution exacte ne représente pas nécessairement les valeurs censurées : celles-ci se situent sous une limite. Par exemple, remplacer le bore `<5` par sa médiane exacte de 17 ppm violerait la borne. Les substitutions de censure restent des approximations, surtout lorsque 419 des 504 observations rapportées de bore sont censurées.

Les zéros observés de concentration restent des nombres mesurés. Pour le traitement thermique, si le régime sans traitement est confirmé, garder cette information et vérifier/imputer le couple température–durée de façon cohérente. Une valeur manquante ne prouve pas l'absence de traitement.

## Vérification des imputations

Les vraies valeurs absentes sont inconnues : aucune comparaison ne peut garantir leur reconstruction exacte. Le protocole doit tester les conséquences et expliciter cette limite.

- Réserver des groupes d'observations pour la vérification. Ajuster les imputers et toutes leurs statistiques sur les autres groupes ; transformer les groupes réservés sans les réajuster.
- Masquer artificiellement 10 %, 20 % puis 40 % des valeurs exactes éligibles des groupes réservés, avec plusieurs graines enregistrées. Les nombres cachés restent disponibles uniquement pour calculer les erreurs.
- Ajouter des masques conjoints ressemblant aux absences observées : courant+tension, blocs d'éléments d'alliage. Définir les schémas et leurs fréquences sur les groupes d'ajustement. Stratifier les résultats par procédé et famille de valeurs ; documenter les cas sans support mesuré. Le masquage de valeurs observées ne reproduit pas nécessairement le mécanisme des véritables absences.
- Calculer MAE et RMSE par variable dans leurs unités ; pour comparer les variables, normaliser par une échelle apprise sur l'entraînement, par exemple l'IQR, avec écart-type en repli si l'IQR est nul. Rapporter l'effectif masqué et les résultats par groupe, pas seulement une moyenne globale.
- Vérifier que les cellules mesurées sont inchangées, que les cellules estimées respectent les contraintes applicables et que les limites de censure sont respectées si ces observations sont traitées par une méthode contrainte.
- Comparer histogrammes ou ECDF des valeurs observées, cachées/reconstruites et imputées, séparément par procédé. Examiner quantiles, variance et amas artificiels à la médiane. Une distribution globale identique n'est pas exigée, puisque populations observées et absentes peuvent différer.
- Examiner corrélations et effectifs sur les seules paires mesurées avant remplissage ; sur un sous-ensemble de référence identique, comparer avant masquage et après reconstruction. Des corrélations entre colonnes imputées par le même modèle ne constituent pas une validation indépendante.
- Comparer la stabilité des premières composantes de l'ACP, leurs sous-espaces, la variance expliquée et les contributions. Aligner les signes ; si des valeurs propres sont proches, des rotations sont possibles sans modification majeure du sous-espace. Vérifier aussi si les axes séparent principalement sources ou profils d'absence.
- Plus tard, comparer l'utilité prédictive des stratégies sur les mêmes plis par groupes. Tout choix reposant sur la cible se fait dans l'entraînement/validation interne, jamais sur les labels de validation externe.

## Matrices d'ACP proposées

**Entrées, référence.** Les onze entrées relativement disponibles listées plus haut, après résolution des intervalles et du traitement thermique. Comparer l'ACP sur les 1 343 lignes complètes exactes à celle sur les lignes conservées après imputation, en examinant le biais de sélection des premières. La liste est un point de départ technique, pas une liste d'éléments métallurgiquement les plus importants.

**Entrées, extension.** Ajouter oxygène et azote après clarification, puis comparer une extension avec nickel, chrome, molybdène, vanadium, cuivre, titane, aluminium, bore et niobium lorsque unités, couverture par groupes et sensibilité le permettent. Cobalt, tungstène, étain, arsenic et antimoine sont réservés initialement à des analyses secondaires vu la couverture et/ou les unités ambiguës ; cette décision ne signifie pas absence d'influence physique.

**Propriétés mécaniques.** Explorer d'abord les quatre propriétés de traction sur les 650 lignes complètes, sans imputation de ces propriétés. Charpy est étudié avec sa température d'essai ; vérifier les énergies fixées et les séries multi-températures avant une tâche de prédiction. Ne pas créer une ACP globale des propriétés massivement imputées pour décider de la qualité. Dureté et FATT restent des analyses distinctes, faute de couverture suffisante pour l'analyse principale.

**Microstructure.** Analyse dédiée du petit sous-ensemble renseigné, après clarification des sommes 90/99/119 %. Si les fractions sont bien une composition exhaustive de catégories exclusives, tenir compte de leur contrainte de somme pour interpréter leurs corrélations ; aucune imputation indépendante des cinq fractions à l'échelle de toute la base n'est proposée.

Pour les ACP principales, centrer-réduire les variables numériques dans leurs unités validées. Comparer des transformations d'asymétrie seulement si elles sont explicites, compatibles avec les zéros et utiles à la stabilité ; ne pas supposer la normalité nécessaire à l'ACP. Ne pas standardiser puis ajouter automatiquement les indicateurs d'absence à la même ACP physique : les examiner séparément ou comme informations supplémentaires. Pour les méthodes sensibles aux distances telles que KNN, le choix d'échelle doit aussi intervenir avant le calcul des voisins.

## Frontière avec la modélisation future

Une cible absente n'est jamais remplacée par une imputation traitée comme label réel. Une éventuelle semi-supervision est un protocole distinct, inductif ou transductif explicitement documenté, sans labels de validation dans l'apprentissage ou les pseudo-labels. Les imputers d'entrées ne doivent pas utiliser les propriétés cibles indisponibles lors de l'inférence. Réajuster sélection de variables, imputation, échelle et ACP à l'intérieur de chaque pli d'entraînement. Consigner seed, groupes, paramètres, taux d'estimation et diagnostics dans `specs/spec.md` au moment où les choix seront effectivement adoptés.

## Sources méthodologiques

- [Documentation de la base Cambridge](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html) : unités, origine bibliographique et sens de `N` (non rapporté, pas zéro).
- [Imputation dans scikit-learn](https://scikit-learn.org/stable/modules/impute.html) : méthodes univariées, multivariées, voisins et imputations multiples.
- [ACP dans scikit-learn](https://scikit-learn.org/stable/modules/decomposition.html#pca) : exploration des directions de variance.
- [Prévention des fuites de données](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) : séparation de l'ajustement et de la transformation.
- [Van Buuren et Groothuis-Oudshoorn, 2011](https://www.jstatsoft.org/article/view/v045i03) : imputation par équations chaînées et diagnostics.
