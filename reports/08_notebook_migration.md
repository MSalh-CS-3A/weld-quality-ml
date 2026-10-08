# Migration vers les notebooks et passage à la modélisation

Date : 8 octobre 2026. La migration est demandée par l'utilisateur, qui préfère
du code directement lisible dans des notebooks séparés plutôt qu'un package
d'analyse sous `src/`. Le brut et l'énoncé restent inchangés.

## Étape 1 — Sauvegarde avant migration

Commit `2ecb088` : audits, décisions et sources AI sauvegardés. Les CSV, ZIP et
joblib fournis ne sont pas ajoutés à Git. Les conclusions de validation sont
consignées dans les rapports 06 et 07.

## Étape 2 — Préparation et point d'entrée de modélisation

- `notebooks/02_data_preparation.ipynb` contient directement le schéma, le parsing,
  la provenance, la déduplication, les groupes, les cohortes, les plis et la classe
  de preprocessing. Aucun import de `weld_prep` ou du package du projet.
- Les chemins fonctionnent depuis la racine ou `notebooks/`. Les exports sont
  écrits exclusivement sous `data/processed/modeling/`.
- Le cas PWHT partiel incompatible produit désormais une erreur explicite. Un
  fit non convergé ou sans couple PWHT complet est aussi refusé.
- Le manifeste inclut les unités, le hash du contenu source du notebook, les
  paramètres du benchmark et les politiques d'erreur.
- `notebooks/03_modeling.ipynb` remplace l'ancien squelette `02_modeling`. Il
  vérifie les hashes des exports, les schémas autorisés et les partitions des
  labels/pools. Les modèles finaux restent à choisir/régler.

Vérification : exécution séquentielle de toutes les cellules Python des deux
notebooks, depuis le dossier `notebooks/`, dans des namespaces propres, puis
comparaison des huit CSV avec l'archive AI corrigée. Concordance numérique
1e-10, scores de benchmark compris. Test ciblé du garde-fou PWHT partiel réussi.
Les hashes des fichiers bruts sont inchangés. Les logs d'exécution sont locaux
sous `data/processed/notebook_verification/`. Cette vérification exécute le code
des cellules avec Python ; elle ne prétend pas tester l'interface Jupyter.

## Étape 3 — EDA allégée et suppression du package d'analyse

- `01_eda.ipynb` passe de 40 à 13 cellules. Il conserve les statuts de mesure,
  répétitions, procédés, distributions sélectionnées, relations entre propriétés,
  ambiguïtés Charpy et une ACP descriptive. Les longues comparaisons d'imputation,
  leurs répétitions de tableaux et leurs multiples scénarios d'ACP sont retirés
  du notebook, avec les preuves historiques conservées dans les rapports et Git.
- L'ACP actuelle utilise 1 339 lignes dédupliquées avec les onze entrées exactes
  complètes, sans imputation. PC1/PC2 expliquent respectivement 27,02 % et 19,03 %
  de la variance standardisée de ce sous-ensemble (46,05 % cumulés).
- Le package `src/weld_quality/` et sa configuration d'installation sont supprimés.
  Le téléchargeur existant devient autonome dans `scripts/download_data.py`, avec
  les mêmes garanties de checksum et de préservation du brut.
- `requirements.txt`, le README et la consigne d'architecture reflètent les
  notebooks autonomes. Les tests de l'ancien package sont remplacés par des
  contrôles ciblés qui exécutent les définitions du notebook 02 directement.

Vérification : six cellules de code EDA exécutées de haut en bas depuis
`notebooks/`, cinq figures exportées, fichiers bruts inchangés. Quinze tests
hors ligne passent : cinq téléchargement et dix parsing, provenance, groupes,
schémas, fit du train, valeurs observées, PWHT et non-convergence.

La prochaine étape clôt la mise à jour des specs, du rapport et du backlog,
et retire les sources AI originales de l'arborescence active après sauvegarde Git.
