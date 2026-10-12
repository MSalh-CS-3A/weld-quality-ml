# Collaboration workflow and task backlog

Both teammates learn EDA and protocol design, then own different method
experiments before interpreting results and writing together. A and B are role
placeholders; choose which teammate is A before assigning GitHub issues.

## GitHub workflow

1. Create one issue per task below using the Project task template. Copy its
   outcome and acceptance criteria, assign an owner, and name the other teammate
   as reviewer. Replace task dependencies with actual issue links.
2. Use a simple board: Todo, In progress, In review, Done. Keep blocked tasks in
   Todo and record their prerequisite issues. Each person starts with one active
   task; joint tasks have one integration owner and contributions from both.
3. Branch from updated `main`, naming the branch `task/<issue-number>-<short-name>`.
   For example, issue 12 could use `task/12-validation-protocol`. These are naming
   examples, not existing GitHub issue numbers.
4. Open a draft PR early for substantial work. Put `Closes #<issue-number>` in the
   PR description once it delivers the whole issue; use `Related to #...` for
   partial contributions. The other teammate reviews code and scientific claims.
5. Resolve review comments and obtain the other teammate's approval before
   merging into `main`. Squash merging is a convenient default. Update your local
   `main` before starting the next task. A complete linked PR targeting the
   default branch can close its issue automatically.
6. Record actual time per person and work session in `specs/time_log.csv`, using
   ISO dates and decimal hours. Use the local task ID until there is a GitHub
   issue number. For joint sessions, each person logs their own time; do not
   confuse total person-hours with elapsed project duration in the final Gantt.

Use separate notebooks for independent EDA, such as `01_eda_a.ipynb` and
`01_eda_b.ipynb`, then consolidate in `01_eda.ipynb`. Give each method its own
experiment notebook or script. Agree before changing shared evaluation code,
and keep analysis code directly in the relevant notebook. Record scientific decisions
in `specs/spec.md`; GitHub discussion links supplement that record.

Repository templates become available on GitHub after they reach its default
branch. This backlog does not claim that any GitHub issues or board exist yet.

## Backlog

### Current technical state — 2026-10-10

The seven active notebooks are now `01_eda`, `02_data_preparation`,
`03_modeling`, `04_diagnostics`, `05_random_kfold`, `06_grouped_exports` and `07_coreg`,
with analysis code directly in their cells. EDA/preparation,
traction eligibility, grouped outer/inner splits and a fixed-parameter sensitivity
benchmark are implemented and locally reproduced. Notebook 03 now runs tuned
supervised comparisons for three traction targets and exploratory reported Charpy
E(T) pairs: five model families, five outer/three inner group folds, 100 outer
evaluations and 2,440 estimator fits. Course methods are confirmed. Notebook 04 completes retrospective group/error diagnostics,
permutation and local explainability, split controls and the six 11/13/16-feature ×
median/iterative scenarios with the same grouped nested validation. Of 480 planned
outer evaluations, 436 succeed; 44 are unavailable due to 11 documented iterative
preprocessing failures. A joint inner-only selection and MAE/MSE comparison are
also evaluated. Three Charpy source families are matched, with uncertainty kept
explicit; 21 source groups remain unresolved. A homogeneous Charpy protocol,
independent validation after this investigation remains open. Notebook 05 adds the requested 16-input/median random nested KFold,
audits series/condition repetitions, compares three fixed-RF split protocols,
exports complete pipelines and prepares row-separated inductive pools. There
are 849/878/924 candidate unlabeled rows for traction; Charpy has no unlabeled
example with known test temperature. Results are
in `reports/10_supervised_training.md`, `reports/11_performance_diagnostics.md`
`reports/12_random_kfold_training.md` and
`reports/13_grouped_exports_and_ssl_plan.md`. Both random
and grouped 16/median protocols now have 40 exported pipelines each, with
fresh-process reload and OOF reproduction checks. Notebook 07 implements the
authorized inductive COREG experiment: three traction targets, both nested CV
protocols, internal k selection, matched/tuned supervised kNN controls and
base43/44 sensitivity. The preprocessing is fixed on true train labels; repeated
pool representations are deduplicated. Results are recorded in
`reports/14_coreg_training.md`; 37 focused tests pass. COREG exports are separate
from the earlier supervised exports. Teammate cross-review and independent
scientific validation remain open.

This technical status does not claim that both teammates completed independent
EDA, cross-review or reproduction. Agree on owners, course methods and actual
work times; `time_log.csv` is not filled with inferred hours. Historical package
code and AI sources are preserved in Git, outside the active notebook workflow.

These tasks describe outcomes, not chosen targets or model families. Final
method selection depends on the inspected data, task framing, and course content.
Expand any large method task into implementation and experiment issues if needed.

| ID | Issue title | Owner / participation | Depends on |
| --- | --- | --- | --- |
| T01 | Explore the dataset independently — teammate A | A | None |
| T02 | Explore the dataset independently — teammate B | B | None |
| T03 | Consolidate EDA, variable documentation, and PCA | A; both contribute | T01, T02 |
| T04 | Define the prediction task together | B; both contribute | T03 |
| T05 | Agree on the validation and experiment protocol | A; both contribute | T04 |
| T06 | Implement and reproduce a shared baseline | B; both contribute | T05 |
| T07 | Research methods and divide experiment ownership | A; both contribute | T04; T05 before final agreement |
| T08 | Implement and evaluate teammate A's supervised method | A | T06, T07 |
| T09 | Implement and evaluate teammate B's supervised method | B | T06, T07 |
| T10 | Implement and evaluate a suitable semi-supervised method | Choose in T07; other reviews | T06, T07 |
| T11 | Cross-review and reproduce each other's experiments | B; both contribute | T08, T09, T10 |
| T12 | Compare results, interpret errors, and develop conclusions | A; both contribute | T11 |
| T13 | Write and review the report, references, and Gantt | B; both contribute | T12 for final results |

### T01 — Explore the dataset independently — teammate A

Outcome: A understands the source data and presents an evidence-based EDA.

- [ ] Reproduce the existing download and read source variable documentation.
- [ ] Inspect units, missing-value encodings, distributions, and plausible targets.
- [ ] Inspect duplicates and related weld observations without assuming a grouping rule.
- [ ] Save an individual notebook with useful figures, findings, and open questions.
- [ ] Explain the findings to B and log actual time.

### T02 — Explore the dataset independently — teammate B

Outcome: B completes the same learning process independently before comparison.

- [ ] Reproduce the existing download and read source variable documentation.
- [ ] Inspect units, missing-value encodings, distributions, and plausible targets.
- [ ] Inspect duplicates and related weld observations without assuming a grouping rule.
- [ ] Save a separate notebook and identify agreements or differences with A's findings.
- [ ] Explain the findings to A and log actual time.

### T03 — Consolidate EDA, variable documentation, and PCA

Outcome: one shared account of the data and justified preprocessing proposals.

- [ ] Consolidate checked findings in `notebooks/01_eda.ipynb`.
- [ ] Document column names, meanings, units, missingness, and data-quality issues
      in `data/README.md`; implement any reusable loading code.
- [ ] Perform exploratory PCA with justified feature handling, imputation, and
      scaling; explain variance and loadings and save suitable figures.
- [ ] Document preprocessing proposals and evidence about related observations
      in `specs/spec.md`.
- [ ] Label PCA as exploratory; never reuse full-data fitted transformations in
      validation. Future predictive PCA must be fitted inside training folds.

### T04 — Define the prediction task together

Outcome: a jointly understood ML task supported by variable documentation.

- [ ] Choose and justify target properties and their relationship to weld quality.
- [ ] Decide regression or classification; justify any threshold with evidence.
- [ ] Identify predictors available at prediction time and exclude leakage sources.
- [ ] Define labeled eligibility and unlabeled observations for each target.
- [ ] Record definitions, uncertainties, and rationale in `specs/spec.md`.

### T05 — Agree on the validation and experiment protocol

Outcome: every method can be evaluated under a common reproducible protocol.

- [ ] Define reproducible outer splits, seeds, and any evidence-based grouping.
- [ ] Choose metrics and document their formulas, units, and interpretation.
- [ ] Define tuning rules, comparable budgets, and inner validation where needed.
- [ ] Require learned preprocessing within training folds, including imputation,
      scaling, PCA, and feature selection.
- [ ] Specify unlabeled-data eligibility and whether semi-supervised evaluation
      is inductive or transductive; exclude validation labels from all training
      and pseudo-label generation. Keep related observations together when required.
- [ ] Agree on a result format containing dataset identity, target, split identity,
      seed, model parameters, protocol version, and per-fold metrics.
- [ ] Record this protocol in `specs/spec.md` before main experiments begin.

### T06 — Implement and reproduce a shared baseline

Outcome: both teammates can run and explain one complete evaluation pipeline.

- [ ] Implement a simple baseline suitable for the chosen task, with reusable
      preprocessing, metrics, and evaluation code in the modeling notebook.
- [ ] Generate consistent splits and experiment summaries under T05's protocol.
- [ ] Add focused checks for split separation and meaningful leakage risks.
- [ ] Run the baseline on both teammates' environments and record actual outcomes.
- [ ] Document commands and environment/package versions needed to reproduce it.

### T07 — Research methods and divide experiment ownership

Outcome: a justified method portfolio with clear ownership and balanced work.

- [ ] Each teammate researches candidate methods appropriate to the task and course.
- [ ] Select distinct supervised approaches and at least one appropriate
      semi-supervised approach; document assumptions, references, and limitations.
- [ ] Assign T08–T10 owners, ensuring the semi-supervised workload is accounted for.
- [ ] Agree on tuning ranges and resources using T05's shared rules.
- [ ] Record method choices in `specs/spec.md`; do not select methods merely
      because another target or task usually uses them.

### T08 — Implement and evaluate teammate A's supervised method

Outcome: a reproducible supervised experiment owned and explained by A.

- [ ] Implement the agreed method using shared evaluation and fold-local pipelines.
- [ ] Run justified tuning and outer evaluation; record parameters and fold metrics.
- [ ] Compare against the shared baseline and examine errors and limitations.
- [ ] Supply a reproduction command, package versions, figures, and interpretation.
- [ ] Explain the method and results to B; address their PR review.

### T09 — Implement and evaluate teammate B's supervised method

Outcome: a distinct reproducible supervised experiment owned and explained by B.

- [ ] Implement the agreed method using shared evaluation and fold-local pipelines.
- [ ] Run justified tuning and outer evaluation; record parameters and fold metrics.
- [ ] Compare against the shared baseline and examine errors and limitations.
- [ ] Supply a reproduction command, package versions, figures, and interpretation.
- [ ] Explain the method and results to A; address their PR review.

### T10 — Implement and evaluate a suitable semi-supervised method

Outcome: a justified experiment that uses eligible unlabeled observations.

- [x] Implement the researched method appropriate to the chosen prediction task.
- [x] Enforce and document T05's inductive or transductive data-access rules.
- [x] Keep validation labels out of training, tuning outside inner folds, and
      pseudo-label generation; fit learned preprocessing on permitted training data.
- [x] Compare against the relevant supervised counterpart with the same labeled
      training observations and outer validation splits to assess the unlabeled contribution.
- [x] Record tuning, parameters, fold metrics, limitations, and reproduction steps.
- [ ] Have the other teammate inspect data access and explain the method back.

### T11 — Cross-review and reproduce each other's experiments

Outcome: both teammates understand and can reproduce the complete method portfolio.

- [ ] A reruns B's method; B reruns A's; the non-owner reruns T10.
- [ ] Check common dataset/target eligibility, splits, metrics, and tuning rules.
- [ ] Inspect fold-local preprocessing and semi-supervised label isolation.
- [ ] Record observed reproduction results and explain justified stochastic variation.
- [ ] Resolve discrepancies before accepting comparisons in T12.

### T12 — Compare results, interpret errors, and develop conclusions

Outcome: a joint interpretation supported by validated experiments.

- [ ] Produce a common comparison table and figures with per-fold variability.
- [ ] Examine errors and relevant subgroup behavior without treating exploration
      on validation results as an unbiased new model-selection experiment.
- [ ] Discuss predictive performance, stability, complexity, and the observed
      contribution of unlabeled data without assuming it improves performance.
- [ ] Explain limitations and distinguish observed associations from causal claims.
- [ ] Develop evidence-supported welding recommendations, noting uncertainty.
- [ ] Record conclusions and supporting results in `specs/spec.md`.

### T13 — Write and review the report, references, and Gantt

Outcome: an approximately five-page report satisfying `sujet.md`.

Start an outline earlier; finalize results after T12.

- [ ] Include names, team number, date, emails, title, and page numbers.
- [ ] Cover the problem and task framing, dataset and PCA, target meanings,
      methods and justifications, metric definitions, numerical comparisons,
      discussion, conclusions, and evidence-supported recommendations.
- [ ] Include titled figures/tables cited in the text and references cited in context.
- [ ] Create a Gantt with task responsibilities and actual time from the work log;
      distinguish each person's effort from calendar duration.
- [ ] Divide drafting, exchange sections for review, and have both teammates
      review the entire report against the original assignment.
- [ ] Verify every reported result against a reproducible experiment.

## GitHub references

- [Issue and PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [Linking PRs and issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)

### Extension technique — 12 octobre 2026

Le notebook 08 ajoute XGBoost aux quatre cibles/aux deux protocoles
16/médiane, douze configurations choisies en interne, benchmarks et refits
six familles. 40 évaluations XGBoost, 1 968 fits, 88 nouveaux exports
rechargés, 276 au total ; 41 tests passent. Rapports 10 à 16 annotés ou
actualisés et rapport 17 ajouté. Les historiques 13/itérative et COREG
sont préservés. Revue croisée et validation scientifique indépendante
restent ouvertes ; aucun temps humain n’est inféré.

### Seuils et validation — 12 octobre 2026

Recherche normative (ISO 2560-A, ISO 18275-A, AWS A5.1, DNV, JCGM 106) et
choix de l'utilisateur : profil ISO 2560-A E 42 2, k = 2. Le notebook 09
applique la règle VALIDÉ / PARTIEL / NON VALIDÉ aux mesures et aux prédictions
hors pli des deux protocoles (sélection à six familles) ; 47 tests passent.
Rapport 18 ajouté. Le traitement de la borne haute d'UTS reste à arbitrer :
avec k = 2, elle empêche tout VALIDÉ prédit.
