# Vérifications ciblées

Depuis la racine, avec les dépendances de `requirements.txt` :

```bash
python -m unittest discover -s tests -v
```

- `test_download.py` : cinq tests hors ligne sur les checksums, le cache,
  la préservation des fichiers bruts et les chemins/liens d’archives.
- `test_notebooks.py` : dix tests chargent les cellules taguées `definitions` de
  `02_data_preparation.ipynb`. Ils vérifient statuts et unités, déduplication,
  schémas sans fuite, groupes externes/internes, statistiques du train,
  mesures observées et refus des cas PWHT/non-convergence invalides.
- `test_modeling.py` : cinq tests chargent les définitions autonomes du notebook
  03. Ils contrôlent l'éligibilité propre aux cibles, la température réservée à
  Charpy, les frontières internes/externes, les fits du preprocessing dans chaque
  train de recherche, l'échelle de y de la SVR et la baseline sans imputation X.
- `test_diagnostics.py` : décompositions SSE/SST exactes, permutation conjointe
  qui préserve les relations internes au bloc, bootstrap par groupes et
  conservation de l'éligibilité lorsque Ni/Cr/Mo restent absents, reconstruction
  exacte des prédictions par les contributions locales des chemins d'arbres.
- `test_random_kfold.py` : cinq tests sur la reproductibilité sans consultation
  des valeurs de y, l'exclusion des X/labels de validation du pool inductif, la
  température Charpy requise, les médianes apprises dans chaque train interne et
  les prédictions/métadonnées conservées par les exports sans cache.
- `test_grouped_exports.py` : deux tests sur l'exclusion de tous les groupes de
  validation du pool inductif et les groupes disjoints dans la CV de refit complet.
- `test_coreg.py` : cinq tests sur le gain local exact contre un refit explicite,
  les transferts croisés sans réutilisation d'ID, les arrêts et représentations
  répétées, l'imputation sur les seuls vrais labels et la sérialisation, ainsi
  que les accès inductifs internes/externes des deux protocoles.

Aucun package de projet ni donnée réelle n’est nécessaire aux tests. Le benchmark
n’est pas exécuté par cette suite. Le téléchargement peut être testé sans les
dépendances scientifiques :

```bash
python -m unittest discover -s tests -p 'test_download.py' -v
```

La migration des trois notebooks est décrite dans
`reports/08_notebook_migration.md`. L'exécution complète des recherches supervisées
du notebook 03 utilise les données locales et prend plus longtemps que cette
suite rapide ; ses résultats sont décrits dans `reports/10_supervised_training.md`.
Les calculs du notebook 04 et ses contrôles complémentaires sont décrits dans
`reports/11_performance_diagnostics.md` ; la couverture, les hashes des exports et
les choix de paramètres internes ont également été audités sur les données locales.
Cette suite rapide ne reproduit pas à elle seule les résultats scientifiques.

Le notebook 05, ses exports cloudpickle et l'analyse des regroupements sont
documentés dans `reports/12_random_kfold_training.md`. Il a été exécuté dans un
noyau Jupyter neuf ; un audit indépendant a recalculé les 100 scores, vérifié les
780 configurations internes, les droits d'accès au pool et rechargé les 40
pipelines sans exécuter leurs définitions. Les 20 modèles externes reproduisent
leurs prédictions OOF complètes. Ces vérifications d'artefacts complètent les
30 tests rapides ; elles nécessitent les données et modèles locaux ignorés.

Le complément groupé du notebook 06 est décrit dans
`reports/13_grouped_exports_and_ssl_plan.md` : 80 évaluations/11 500 prédictions
du benchmark groupé 16/médiane sont reproduites, puis les 40 exports groupés sont
rechargés dans un processus indépendant. Un audit recalcule ses 100 scores et
vérifie hashes, choix internes et frontières de groupes. La suite comprend
32 tests rapides à cette étape ; COREG n'est pas exécuté par le notebook 06.

Le notebook 07 implémente COREG et ses contrôles. La suite comprend désormais
37 tests rapides ; elle exerce la boucle sur des exemples synthétiques mais
ne reproduit pas les entraînements réels. Le benchmark complet, ses audits
d'accès aux données et les rechargements de modèles sont décrits dans
`reports/14_coreg_training.md`.
