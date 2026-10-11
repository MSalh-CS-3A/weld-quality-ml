# Données du Projet : Base de Données WeldDB (Cambridge)

## Origine et Téléchargement des Données
Les données exploitées dans ce projet proviennent de la base de référence internationale **WeldDB**, hébergée par le *Phase Transformation & Complex Properties Research Group* du Département de Science des Matériaux et Métallurgie de l'Université de Cambridge :

* **Lien officiel du dataset :** [Cambridge Materials WeldDB (welddb-b.html)](https://www.phase-trans.msm.cam.ac.uk/map/data/materials/welddb-b.html)
* **Archive originale :** `welddb.tar` (format texte tabulé ASCII)
* **Auteurs :** Tracey Cool, Prof. H.K.D.H. Bhadeshia, et Prof. David J.C. MacKay.

---

## Description du Jeu de Données
Le jeu de données contient **1 652 cordons de soudure** caractérisés par **44 attributs physico-chimiques et métallurgiques** :

1. **Composition Chimique (21 éléments en % massique wt% ou ppm) :**
   * Éléments majeurs : Carbone ($C$), Manganèse ($Mn$), Silicium ($Si$), Chrome ($Cr$), Nickel ($Ni$), Molybdène ($Mo$), Vanadium ($V$), Niobium ($Nb$), Cuivre ($Cu$), Titane ($Ti$), Aluminium ($Al$), Bore ($B$).
   * Impuretés et gaz dissous : Soufre ($S$), Phosphore ($P$), Oxygène ($O$), Azote ($N$).
   * Éléments traces : Cobalt ($Co$), Tungstène ($W$), Étain ($Sn$), Arsenic ($As$), Antimoine ($Sb$).

2. **Paramètres Opératoires et Thermiques (9 descripteurs) :**
   * Courant de soudage ($I$ en A), Tension d'arc ($U$ en V), Vitesse d'avance ($v_s$ en mm/s).
   * Énergie de soudage apportée (*Heat Input* $E$ en kJ/mm).
   * Températures de préchauffage et d'interpasse ($T$ en $^\circ\text{C}$).
   * Traitement thermique post-soudage (*PWHT* : température en $^\circ\text{C}$ et durée en heures).

3. **Propriétés Mécaniques et Microstructure (Variables Cibles) :**
   * Résistance ultime à la traction ($R_m$ / UTS en MPa) — 738 éprouvettes labellisées.
   * Limite conventionnelle d'élasticité ($R_e$ / Yield Strength en MPa).
   * Énergie d'impact Charpy ($VE$ en J) et allongement à rupture ($El$ en %).
   * Fractions volumiques microstructurales : Ferrite aciculaire ($AF$), Ferrite primaire / en joints de grains ($PF$), Ferrite avec seconde phase alignée ($FS$).

---

## Remarque Métrologique Importante
* Dans les fichiers originaux de Cambridge, la lettre `'N'` désigne expressément une mesure non effectuée (*Missing Value*) et ne doit en aucun cas être remplacée par 0.
* Lors de l'import d'un tableur configuré en locale française (virgule décimale), veiller à ne pas interpréter le point décimal anglais comme un séparateur de milliers (ex. $0.037$ ne doit pas devenir $37$).
