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

La simplification de l'EDA, la suppression du package devenu inutile et la mise
à jour générale des documents font partie des étapes suivantes de cette migration.
