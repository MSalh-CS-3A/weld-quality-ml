# Prédiction des propriétés mécaniques de soudures

Projet ML sur la base Cambridge Weld DB. L’énoncé original est dans
[sujet.md](sujet.md) et les décisions dans [specs/spec.md](specs/spec.md).

## Organisation

```text
notebooks/
  01_eda.ipynb                 structure, couverture, distributions et ACP
  02_data_preparation.ipynb    nettoyage, provenance, cohortes, plis et imputation
  03_modeling.ipynb            pipelines, réglages et validation supervisée par groupes
  04_diagnostics.ipynb         erreurs par séries, audit Charpy, explicabilité et sensibilités
  05_random_kfold.ipynb        validation aléatoire 16/médiane, comparaison et exports
  06_grouped_exports.ipynb     export groupé 16/médiane et contrôle des prédictions
  07_coreg.ipynb               COREG inductif, contrôles kNN, deux validations et exports
scripts/download_data.py      téléchargement autonome et checksum SHA-256
requirements.txt              dépendances des notebooks
data/raw/                     fichiers d’origine préservés, ignorés par Git
data/processed/modeling/       exports reproductibles, ignorés par Git
data/processed/experiments/    scores, prédictions et recherches, ignorés par Git
models/                       pipelines complètes et métadonnées locales, ignorées par Git
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

Choisir le noyau de `.venv`, puis exécuter **01 → 02 → 03 → 04 → 05 → 06 → 07**, de haut en bas.
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
L’imputation itérative est la méthode du benchmark initial à 13 entrées
numériques + procédé, réajustée dans chaque entraînement interne et externe.
Les labels manquants restent inconnus.

Le notebook 03 entraîne séparément les trois cibles de traction et l’énergie
Charpy avec baseline médiane, Ridge, SVR RBF, Random Forest et kNN. Il utilise
cinq plis externes par groupes et trois plis internes pour régler chaque
pipeline, avec preprocessing appris dans chaque train. Charpy ajoute la
température d’essai aux entrées ; ses 861 couples rapportés constituent une
expérience exploratoire dont les protocoles restent à vérifier par source.
COREG est traité séparément dans le notebook 07. Aucun modèle de production n’est choisi à partir du meilleur
score externe. Voir [le rapport supervisé](reports/10_supervised_training.md).

Le notebook 04 approfondit les erreurs par groupes, les écarts train/validation,
le domaine des entrées et les protocoles Charpy. Il compare les schémas 11/13/16
et les imputations médiane/itérative sur les mêmes plis, avec choix internes.
Les importances par permutation décrivent l'utilisation des variables par le
modèle ; elles ne démontrent pas un effet causal. Ces diagnostics suivent
l'observation du benchmark et ne constituent pas un nouveau test indépendant.
Voir [le rapport de diagnostic](reports/11_performance_diagnostics.md).

Le notebook 05 utilise **16 entrées numériques + procédé, avec médiane**, sur la
même cohorte, et ajoute un KFold aléatoire imbriqué : cinq plis externes, trois
internes. Il compare les mêmes familles, choisit famille et paramètres sur MAE
interne, et analyse les séries et conditions répétées. Le score aléatoire décrit
des lignes dont les séries peuvent déjà être connues ; il ne démontre pas que
la base est IID. Le benchmark groupé demeure un contrôle de transfert.
Les pipelines sélectionnées par pli et les cinq familles réentraînées par cible
sont sauvegardées dans `models/salh_random_kfold_v1/`, avec unités, versions,
paramètres et hashes. Voir [models/README.md](models/README.md).

Les partitions et accès au pool inductif sont préparés pour le semi-supervisé :
849/878/924 candidats sans label pour YS/UTS/allongement.
Charpy n'a aucun candidat sans énergie avec une température d'essai connue dans
cette cohorte. Le semi-supervisé Charpy nécessite donc des données appropriées.
Voir [le benchmark aléatoire et ses limites](reports/12_random_kfold_training.md).

Le notebook 06 complète les exports pour la configuration 16/médiane sous
validation groupée : il reproduit les prédictions de 04 avec ses paramètres
internes enregistrés, puis sauvegarde les modèles des plis et les refits complets
réglés par GroupKFold5. Les deux protocoles ont chacun leur dossier sous `models/`
et leur index de sélection. Les refits complets servent à l'inférence ; COREG
réajuste ses modèles sur chaque train de pli, sans labels de validation.
Voir [les exports groupés et le cadrage semi-supervisé](reports/13_grouped_exports_and_ssl_plan.md).

Le notebook 07 entraîne COREG pour les trois cibles de traction avec les deux
validations imbriquées. Deux kNN L1/L2 échangent les estimations dont le gain
local est positif ; k est choisi en interne. Il compare la moyenne sans
pseudo-labels au même k, les kNN réglés et les références supervisées.
Le preprocessing reste appris sur les vrais labels du train et figé pendant
la boucle ; le pool exclut toutes les validations et déduplique les entrées
transformées. Les modèles des plis et les refits complets sont exportés dans
`models/salh_coreg_v1/`, avec contrôles et journaux de pseudo-labels.
Voir [les résultats COREG](reports/14_coreg_training.md).

Deux documents en français regroupent les travaux pour lecture :
[la synthèse globale des résultats](reports/15_synthese_globale_resultats_fr.md)
et [le rapport du projet, version 1](reports/16_rapport_projet_v1_fr.md).
Ce dernier est aussi disponible en
[PDF de cinq pages](output/pdf/rapport_projet_v1_fr.pdf).
Les trois auteurs sont renseignés ; le numéro d'équipe, les dates, les
responsabilités et les heures réelles du Gantt restent à compléter.

L’EDA conserve une ACP descriptive sur les onze entrées complètes, sans
imputation. Les anciens essais détaillés sont dans les rapports historiques
et Git ; leurs matrices ajustées sur toute la base ne servent pas à la validation.

## Vérifications

Avec les dépendances installées, depuis la racine :

```bash
python -m unittest discover -s tests -v
```

Les tests sont hors ligne : archives, statuts de mesure, doublons, groupes,
statistiques du train, préservation des observations, erreurs PWHT,
non-convergence, recherches imbriquées et échelle des cibles. Les définitions
testées sont chargées directement depuis les notebooks 02 à 07. Les
contrôles du notebook 05 couvrent aussi les accès inductifs, les médianes apprises
dans les trains et la persistance des pipelines.
Les contrôles COREG vérifient aussi le calcul exact du gain local, les transferts
croisés, les répétitions et l'isolement des validations.
Voir [tests/README.md](tests/README.md).

Brut, datasets générés, modèles et environnements ne sont pas commités.
Les notebooks d'entraînement conservent leurs tableaux et sorties pour lecture ;
les exports complets restent sous `data/processed/experiments/`, ignoré par Git.
Les résultats sont documentés et reproductibles. Pour les prochaines tâches,
voir [specs/tasks.md](specs/tasks.md).
