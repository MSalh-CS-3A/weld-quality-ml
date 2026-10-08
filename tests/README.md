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

Aucun package de projet ni donnée réelle n’est nécessaire aux tests. Le benchmark
n’est pas exécuté par cette suite. Le téléchargement peut être testé sans les
dépendances scientifiques :

```bash
python -m unittest discover -s tests -p 'test_download.py' -v
```

Les trois notebooks ont aussi été exécutés séquentiellement avec les données
locales ; voir `reports/08_notebook_migration.md`. Cette suite rapide ne reproduit
pas à elle seule tous les résultats scientifiques.
