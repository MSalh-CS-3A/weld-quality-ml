# Première partie — Analyse descriptive de la base de soudures

**Version intermédiaire, 3 octobre 2026.** Cette section couvre l'audit des mesures et des distributions. L'ACP, la définition définitive des cibles et les résultats de modèles restent à ajouter aux sections appropriées du rapport final.

## Données et disponibilité

La base Cambridge comporte **1 652 observations et 44 variables** décrivant la composition chimique, les paramètres de soudage, les traitements thermiques, les propriétés mécaniques et la microstructure. Les unités documentées comprennent pourcentages massiques, ppm massiques, A, V, kJ/mm, °C, heures, MPa et J. Les données proviennent de publications ; le code `N` indique une valeur non rapportée, sans signifier zéro. [Documentation Cambridge](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html)

Le carbone, le silicium, le manganèse, l'apport thermique et le procédé sont entièrement renseignés. La disponibilité est toutefois hétérogène : aucune ligne ne comporte les 44 valeurs. Supprimer toutes les observations incomplètes supprimerait donc toute la base. La figure 1 distingue les absences des mesures censurées et annotées.

![Figure 1 — Disponibilité des mesures pour une sélection de variables.](figures/01_eda_availability.png)

*Figure 1 — Effectifs par statut de mesure, sur 1 652 lignes. « Exacte » désigne un nombre sans annotation, sans préjuger de l'incertitude expérimentale.*

## Distributions et cohérence des mesures

Le carbone varie de 0,029 à 0,18 % massique, avec une médiane de 0,074 %. Le chrome et le molybdène présentent plusieurs concentrations de valeurs, suggérant différentes familles de compositions ou séries expérimentales à vérifier par source. L'intensité varie de 115 à 900 A, avec une médiane de 170 A ; les 30 observations à 850–900 A appartiennent toutes au procédé `SA`. Ces extrêmes ne doivent donc pas être supprimés automatiquement. Les pics de températures et d'apport thermique peuvent refléter des réglages répétés.

Aucune valeur numérique contrôlée ne dépasse les bornes physiques générales utilisées. Sur les 714 observations où les deux résistances sont renseignées, aucune limite d'élasticité ne dépasse la résistance maximale en traction. Ces contrôles ne prouvent cependant ni l'homogénéité des unités ni la validité métallurgique de chaque mesure. La variable `fatt_50` n'a pas été contrôlée par une borne, son unité n'étant pas explicitée.

Plusieurs ambiguïtés subsistent. Dix lignes EPRI contiennent de l'aluminium entre 0,004 et 0,014 dans une colonne annoncée en ppm. Les mêmes 90 lignes présentent simultanément des valeurs positives inférieures à 1 pour l'étain, l'arsenic et l'antimoine. Ces motifs justifient un retour aux publications, sans conversion automatique. Si une valeur était exprimée en pourcentage massique, `1 % = 10 000 ppm` ; une standardisation ne corrigerait pas une confusion d'unité.

Les valeurs `<L` sont censurées sous une limite. Elles représentent 403 des 905 mesures rapportées d'aluminium et 419 des 504 mesures de bore. Les histogrammes des seuls nombres sans annotation peuvent donc être biaisés. Il faut aussi traiter 38 intervalles de température `150-200`, 59 annotations d'azote et 58 annotations de dureté. Pour la dureté, ces dernières contiennent des nombres allant jusqu'à 467, absents de l'histogramme limité aux 80 valeurs sans annotation. Leur protocole Vickers doit être conservé et vérifié. [Présentation des essais de dureté par TWI](https://www.twi-global.com/technical-knowledge/job-knowledge/hardness-testing-part-1-074)

## Propriétés candidates et conséquences méthodologiques

| Propriété candidate | Mesures | Minimum | Médiane | Maximum |
| --- | ---: | ---: | ---: | ---: |
| Limite d'élasticité, MPa | 780 | 315 | 495 | 920 |
| Résistance maximale en traction, MPa | 738 | 447 | 575,5 | 1 151 |
| Allongement, % | 700 | 10,6 | 26,8 | 37 |
| Réduction de section, % | 705 | 17 | 75 | 83 |
| Énergie Charpy, J | 879 | 3 | 100 | 270 |

*Tableau 1 — Disponibilité et distribution de propriétés candidates à la prédiction ; aucune cible définitive n'est encore retenue.*

L'énergie Charpy comporte 356 valeurs à 100 J et 118 à 28 J. Certaines lignes pourraient décrire une température à énergie fixée : leur origine doit être vérifiée avant de définir la tâche. Cette caractérisation existe dans la littérature sur les soudures. [Article Cambridge sur la transition Charpy](https://www.phase-trans.msm.cam.ac.uk/abstracts/harsha4.html)

Enfin, 91 identifiants sont répétés, concernant 253 lignes ; des identifiants différents peuvent aussi désigner des variantes liées. La validation devra tenir compte de ces dépendances. Les prochaines étapes sont de résoudre les ambiguïtés d'unités et d'annotations, définir cible et entrées disponibles, justifier les groupes, puis établir le preprocessing et l'ACP. Les transformations apprises destinées aux modèles seront ajustées dans les plis d'entraînement. Les absences de cible resteront distinctes des absences d'entrée, et les labels de validation seront exclus de l'entraînement et des pseudo-labels.

Les [détails de l'audit, figures complémentaires, traçabilité et prochaines étapes](01_eda_audit_details.md) accompagnent cette synthèse. Cette analyse descriptive ne permet pas encore de recommander des réglages de soudage.
