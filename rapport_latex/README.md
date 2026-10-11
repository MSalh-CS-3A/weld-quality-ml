# Rapport complet en LaTeX

Rapport détaillé du projet, de l'analyse exploratoire à l'analyse des résultats
d'entraînement (EDA, préparation, modélisation, validation, résultats supervisés,
diagnostics, COREG, discussion, Gantt). Le rapport court de cinq pages demandé
par l'énoncé reste [`reports/16_rapport_projet_v1_fr.md`](../reports/16_rapport_projet_v1_fr.md).

## Structure

```text
rapport_latex/
  main.tex                 document principal (ordre des sections)
  informations.tex         titre, auteurs, e-mails, numéro d'équipe, date  ← à vérifier
  preambule.tex            paquets, couleurs, encadrés, en-têtes
  page_de_garde.tex        page de garde avec le logo CentraleSupélec
  sections/00–12           résumé, puis une section par étape du projet
  annexes/A–D              variables, reproductibilité, tableaux complets, glossaire
  references.bib           bibliographie (BibTeX, style unsrtnat)
  figures/                 logo + figures PDF générées
  scripts/generer_figures.py   régénère toutes les figures depuis les exports
```

## Compiler

pdfLaTeX (Overleaf par défaut), XeLaTeX ou Tectonic conviennent :

```bash
cd rapport_latex
latexmk -pdf main.tex          # ou : pdflatex main && bibtex main && pdflatex main && pdflatex main
# ou : tectonic main.tex
```

Sur Overleaf : importer le dossier `rapport_latex/` tel quel, document principal `main.tex`.

## Régénérer les figures

Les figures sont recalculées à partir du brut et des exports des notebooks, sans
réentraîner de modèle. Exécuter d'abord les notebooks 01 → 07, puis depuis la racine :

```bash
python rapport_latex/scripts/generer_figures.py
```

## Éléments à compléter par l'équipe

Ils apparaissent en rouge (`[À compléter]`) dans le PDF ; rien n'a été inventé :

- `informations.tex` : numéro d'équipe ; vérifier les e-mails (repris du rapport v1) et la date ;
- `sections/12_organisation.tex` : membres et heures réelles par tâche (tableau `tab:taches`),
  date de rendu du jalon dans le Gantt ; on peut colorer les barres par membre.

Le Gantt reprend les dates de l'historique Git et des rapports intermédiaires :
elles indiquent quand chaque livrable a été produit, pas le temps de travail.
