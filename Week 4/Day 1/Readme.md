# Adult Income Baseline

Author: Rida Noor

A reproducible baseline for predicting whether a person earns more than 50K a year, using the UCI Adult (Census Income) dataset. This is the starting point for a week of modeling work: it sets up the problem definition, a proper hold-out split, and two baselines that any real model needs to beat.

## Business framing

The model is framed as feeding a targeted marketing campaign for a premium product. Every contact costs money, so a false positive (contacting someone who isn't actually a high earner) is wasted budget, not just a missed opportunity. Because of that, **precision** is the primary metric tracked across the week, not accuracy or F1.

The dataset is imbalanced, about 24% of people earn more than 50K, so a model that always predicts "no" is already 76% accurate without learning anything. That's why accuracy alone isn't used as the scorecard.

## Data source

Loaded directly from the UCI Machine Learning Repository via the `ucimlrepo` package, no manual file download required.

```python
from ucimlrepo import fetch_ucirepo
adult = fetch_ucirepo(id=2)
```

## Setup

```bash
pip install ucimlrepo pandas numpy scikit-learn matplotlib seaborn
```

Then run the notebook top to bottom. It needs an internet connection on first run to fetch the data; after that everything is deterministic (`random_state=42` everywhere a split or a sampled model is involved).

## What's in the notebook

1. **Problem definition** — target, business objective, and why precision was chosen as the primary metric over accuracy or F1.
2. **Data load and EDA** — cleaning `'?'` placeholders to proper missing values, class balance, numeric summaries, and visualizations (age/hours distributions, education vs income rate, correlation heatmap, box plots, marital status/sex/occupation breakdowns).
3. **Reproducible splits** — stratified train (70%) / dev (10%) / hold-out test (20%) split, with the hold-out only touched for final baseline evaluation.
4. **Baselines** — a majority-class predictor and a rule-based classifier (`education-num >= 13 OR capital-gain > 0`), chosen after comparing three candidate rules on precision, recall, and flag rate.
5. **Error analysis** — false positive / false negative patterns, plus a list of data and feature issues to address before real modeling starts (missing values, redundant columns, skewed numerics, high-cardinality categoricals).

## Baseline results (hold-out test set)

| Baseline | Accuracy | Precision | Recall | F1 | ROC AUC | PR AUC |
|---|---|---|---|---|---|---|
| Majority class | 0.761 | 0.000 | 0.000 | 0.000 | - | - |
| Rule: education-num >= 13 OR capital-gain > 0 | 0.745 | 0.475 | 0.603 | 0.531 | 0.697 | 0.381 |

The combined rule was chosen over the narrower `capital-gain > 0` rule (precision 0.62, but only flags 8% of people) because it gives a usable flag rate and meaningfully better recall, while keeping precision close to what education alone provides.

**Bar for the rest of the week:** any real model needs to clear a precision of 0.475 on this same hold-out test set by a real margin, not just barely edge past it.

## Known data issues carried into next steps

- `workclass`, `occupation`, `native-country` missing values are currently filled with an explicit `'Unknown'` category, worth testing model-based imputation
- `education` and `education-num` are redundant, keep one
- `capital-gain` / `capital-loss` are heavily skewed (mostly zero), consider log-transform or bucketing
- `fnlwgt` is a census sampling weight, not a real attribute of the person, likely drop it
- `native-country` is high cardinality dominated by the US, needs grouping rather than raw one-hot encoding
- all categorical features still need proper encoding before any model beyond a simple rule can use them

## Files

- `adult_income_baseline.ipynb` — the full notebook (problem framing through error analysis, fully executed)
- `adult_income_summary.docx` — 1-page summary (problem framing, chosen metric, baseline results, error analysis)
- `README.md` 
