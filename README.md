# Prédiction des propriétés mécaniques de soudures

Projet ML sur la base Cambridge Weld DB. L’énoncé original est dans
[sujet.md](sujet.md) et les décisions dans [specs/spec.md](specs/spec.md).

## Organisation

```text
notebooks/
  01_eda.ipynb                 structure, couverture, distributions et ACP
  02_data_preparation.ipynb    nettoyage, provenance, cohortes, plis et imputation
  03_modeling.ipynb            données prêtes et choix des modèles à entraîner
scripts/download_data.py      téléchargement autonome et checksum SHA-256
requirements.txt              dépendances des notebooks
data/raw/                     fichiers d’origine préservés, ignorés par Git
data/processed/modeling/       exports reproductibles, ignorés par Git
reports/                      analyses, rapport intermédiaire et figures
specs/                        protocole et organisation du binôme
tests/                        contrôles ciblés des notebooks et du téléchargement
```

Le code d’analyse est dans les notebooks. Aucun package local sous `src/`,
installation éditable ou import d’un autre notebook n’est nécessaire.
Les notebooks fonctionnent depuis la racine du dépôt ou `notebooks/`.

## Installation et exécution

Depuis la racine, avec Python 3.10 ou plus récent :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_data.py
python -m jupyterlab
```

Choisir le noyau de `.venv`, puis exécuter **01 → 02 → 03**, de haut en bas.
Si nécessaire, enregistrer le noyau :

```bash
python -m ipykernel install --user --name weld-quality --display-name "Welding Quality"
```

Le script de téléchargement utilise seulement la bibliothèque standard. Il
vérifie l’archive Cambridge, préserve le brut et fonctionne hors ligne avec
l’archive en cache. Voir [data/README.md](data/README.md).

## État du projet

La préparation corrigée est migrée et vérifiée : 1 648 lignes dédupliquées,
1 555 lignes de 44 groupes dans la cohorte principale. Elle contient 706 labels
pour la limite d’élasticité, 677 pour la résistance maximale et 631 pour l’allongement.

Le notebook 02 exporte huit CSV **avant apprentissage**, un manifeste avec
unités, hashes, versions et paramètres, et un contrôle médiane / itérative.
L’imputation itérative est la méthode principale du candidat 13 entrées
numériques + procédé, réajustée dans chaque entraînement interne et externe.
Les labels manquants restent inconnus.

Le notebook 03 vérifie les exports et prépare les partitions pour choisir les
modèles. Réglages finaux, comparaison des méthodes et au moins une méthode
semi-supervisée restent à réaliser. Les tâches Charpy attendent la vérification
des protocoles E(T), T100J et T28J. Les scores actuels sont des contrôles à
paramètres fixes, sans modèle final sélectionné.

L’EDA conserve une ACP descriptive sur les onze entrées complètes, sans
imputation. Les anciens essais détaillés sont dans les rapports historiques
et Git ; leurs matrices ajustées sur toute la base ne servent pas à la validation.

## Vérifications

Avec les dépendances installées, depuis la racine :

```bash
python -m unittest discover -s tests -v
```

Les tests sont hors ligne : archives, statuts de mesure, doublons, groupes,
statistiques du train, préservation des observations, erreurs PWHT et
non-convergence. Les définitions testées sont chargées directement depuis le
notebook 02. Voir [tests/README.md](tests/README.md).

Brut, datasets générés, modèles et environnements ne sont pas commités.
Les notebooks versionnés ont leurs sorties vidées ; les résultats sont documentés
et reproductibles. Pour les prochaines tâches, voir [specs/tasks.md](specs/tasks.md).
