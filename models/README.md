# Pipelines entraînées locales

Les notebooks autonomes `05_random_kfold.ipynb` et `06_grouped_exports.ipynb`
produisent respectivement `salh_random_kfold_v1/` et `salh_group_kfold_v1/`,
ignorés par Git. Les fichiers `.pkl` sont des pipelines
complètes (prétraitement appris et régresseur), sérialisées avec cloudpickle pour
permettre les classes définies dans le notebook, sans package sous `src/`.

- `outer_selected/<target>_fold<k>.pkl` : 20 modèles sélectionnés par MAE interne,
  appris uniquement sur les labels du train externe correspondant.
- `full_fit/<target>_<family>.pkl` : 20 modèles appris sur tous les labels
  disponibles, paramètres réglés par CV5 aléatoire seed1042 dans le premier
  dossier et par GroupKFold5 sur les séries des labels dans le second.
- `selected_models.json` : chemin des quatre familles choisies par cette
  dernière CV, une pour chaque cible. Ce score de sélection n'est pas un test
  indépendant.
- Chaque `.json` à côté d'un `.pkl` documente les colonnes attendues, unités,
  paramètres, IDs d'entraînement, versions de dépendances et hash du modèle.

Pour prédire depuis un processus neuf, utiliser les versions enregistrées et
un DataFrame avec les noms de colonnes du sidecar :

```python
import json
from pathlib import Path
import cloudpickle
import pandas as pd

root = Path('models/salh_random_kfold_v1')  # ou salh_group_kfold_v1
entry = json.loads((root / 'selected_models.json').read_text())[0]
path = Path(entry['path'])  # relatif à la racine du projet
metadata = json.loads(path.with_suffix('.json').read_text())
with path.open('rb') as stream:
    pipeline = cloudpickle.load(stream)
X = pd.read_csv('mes_nouvelles_mesures.csv')[metadata['features']]
prediction = pipeline.predict(X)
```

Ni/Cr/Mo peuvent rester absents : la médiane est celle de l'entraînement, jamais
recalculée sur les nouvelles mesures. La température Charpy doit être connue
pour prédire E(T). Les autres propriétés mécaniques, dureté, FATT50, identifiants
et groupes ne sont pas des entrées. Les unités sont celles du manifeste de
préparation (compositions principales en % massique, O/N en ppm).

Chacun des deux protocoles conserve 40 pipelines (80 au total). Les quatre
refits choisis de chaque protocole sont rechargés dans des processus Python neufs.
Le notebook 06 recharge aussi les 40 exports groupés et reproduit toutes les
prédictions des 20 modèles externes. Les refits sur tous les labels **ne doivent pas servir** à comparer le
semi-supervisé en CV : réentraîner sur le train permis du pli, avec le même
découpage que son contrôle supervisé.

Référence : [persistance scikit-learn](https://scikit-learn.org/stable/model_persistence.html).

## COREG et contrôles

`07_coreg.ipynb` produit séparément `salh_coreg_v1/`, ignoré par Git :

- `random/outer/` et `grouped/outer/` : 90 pipelines au total, COREG,
  moyenne kNN sans pseudo-labels au même k, et moyenne kNN réglée indépendamment,
  pour les trois cibles de traction et leurs cinq plis.
- `random/full_fit/` et `grouped/full_fit/` : 18 refits complets, mêmes trois
  méthodes pour chaque cible/protocole, avec k choisi par CV5.
- `selected_models.json` : index des six refits COREG. Il identifie cette
  méthode ; il ne constitue pas un classement contre les modèles supervisés.

Ces 108 exports s'ajoutent aux 80 pipelines supervisées. Tous sont rechargés
dans un processus indépendant ; les 90 modèles de plis reproduisent leurs OOF.
Le code de chargement ci-dessus fonctionne aussi avec cet index. Le sidecar
précise protocole, rôle, colonnes, IDs vrais/pool, groupes, k, distances,
seed, arrêts et nombre de pseudo-labels. Le pool naturel Charpy est vide :
aucun export semi-supervisé Charpy n'est revendiqué.

Les deux validations peuvent choisir des k différents pour les refits, qui
utilisent ensuite les mêmes vrais labels et le pool naturel complet. Les modèles
externes restent appris sur leur train et leur pool permis uniquement ; les
refits complets ne peuvent pas être utilisés pour scorer ces plis.
Résultats et limites : [rapport COREG](../reports/14_coreg_training.md).

## XGBoost et sélection à six familles

`08_xgboost.ipynb` produit `salh_xgboost_v1/` : pour chacun des protocoles
`random` et `grouped`, 20 pipelines sous `outer_xgboost/`, 20 sous
`outer_selected/` et quatre sous `full_xgboost/`. Les noms incluent la cible
et le pli (`fold-1` pour le refit complet). 88 nouveaux exports vérifiés,
276 au total avec les expériences précédentes.

Utiliser `models/salh_xgboost_v1/selected_models.json` pour les huit choix
complets (six familles candidates, une par cible/protocole). Certains chemins
référencent les refits historiques lorsque XGBoost n’est pas retenu. Les index
05/06 restent historiques à cinq familles. XGBoost et les classes du notebook
sont embarqués avec cloudpickle ; utiliser les versions du sidecar.
Résultats et reproduction : [rapport 17](../reports/17_xgboost_training.md).
