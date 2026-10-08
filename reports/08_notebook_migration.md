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

## Étape 4 — Documentation active et clôture de la migration

Les specs sont réécrites autour du protocole actif : cibles de traction,
cohorte 13, provenance, imputation dans les plis, métriques et données permises
pour la future semi-supervision. Le README, la documentation des unités/exports,
le backlog et le template d'issue reflètent l'organisation en notebooks.
`reports/01_eda_report.md` devient le rapport intermédiaire actuel, avec l'ACP
recalculée et les résultats de contrôle, sans prétendre aux expériences finales.
Les rapports précédents sont signalés comme historiques.

Les sources AI originales, sauvegardées dans `2ecb088`, sont retirées de
l'arborescence active ; les artefacts fournis restants dans `ai_prepared/` sont
ignorés et ne sont jamais chargés par les notebooks. Le répertoire `src/` et ses
caches/metadata d'installation devenus inutiles sont supprimés. Ni le brut,
ni l'énoncé, ni les fichiers fournis de données/joblib/ZIP ne sont modifiés.

| Étape | Commit |
| --- | --- |
| Sauvegarde initiale et audits | `2ecb088` |
| Préparation autonome et point d'entrée de modélisation | `643dbee` |
| EDA allégée, package supprimé et tests directs | `1863426` |
| Documentation active et clôture | Commit de cette révision |

## Phase disponible après migration

Le prochain travail commence dans `03_modeling.ipynb` : choisir les méthodes,
leurs budgets et une approche semi-supervisée justifiée, puis régler et entraîner
avec les plis exportés. Il n'est pas nécessaire de reconstruire le nettoyage.
Les règles de tuning, les extensions et sensibilités doivent être arrêtées dans
l'entraînement ; les validations externes restent réservées à l'évaluation.

Les notebooks versionnés ont les sorties vidées pour rester lisibles. Les cinq
figures EDA actuelles sont disponibles dans `reports/figures/` ; les CSV et logs
sont générés localement, ignorés par Git. Aucun entraînement final, résultat
semi-supervisé, heure de binôme ou recommandation pratique n'est inventé.

Vérification finale après retrait des anciens modules : les quinze tests passent,
le point d'entrée `03_modeling` s'exécute aussi depuis la racine, les hashes de
tous les exports et du source du notebook 02 correspondent au manifeste. Les
hashes des CSV/ZIP/joblib fournis restent identiques à ceux de l'audit ; `sujet.md`
est identique à la sauvegarde initiale. L'état final contient trois notebooks
de 13, 24 et 7 cellules, respectivement, sans sorties versionnées volumineuses.
