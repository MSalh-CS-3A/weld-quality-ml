# Rapport complet en LaTeX

Rapport détaillé du projet, de l'analyse exploratoire à l'analyse des résultats
d'entraînement (EDA, préparation, modélisation, validation croisée, résultats
supervisés avec XGBoost, diagnostics, COREG, seuils normatifs et validation des
soudures, discussion). PDF compilé : [`output/pdf/rapport_complet_fr.pdf`](../output/pdf/rapport_complet_fr.pdf).

## Structure

```text
rapport_latex/
  main.tex                 document principal (ordre des sections)
  informations.tex         titre, auteurs, e-mails, date
  preambule.tex            paquets, couleurs, encadrés, en-têtes
  page_de_garde.tex        page de garde avec le logo CentraleSupélec
  sections/00–12           résumé, puis une section par étape du projet (10 : seuils et validation)
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
réentraîner de modèle. Exécuter d'abord les notebooks 01 → 09, puis depuis la racine :

```bash
python rapport_latex/scripts/generer_figures.py
```
