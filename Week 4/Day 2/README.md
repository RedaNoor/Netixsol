# Core Supervised Learning: Preprocessing, Models and Evaluation


Builds the first real supervised models on the Adult (Census Income) dataset, on top of the Day 1 baseline notebook (majority-class and rule-based baselines, hold-out test set already defined). Focus is on leak-free preprocessing for mixed numeric/categorical data and a fair comparison between two classifiers.

## Contents

| File | Description |
|---|---|
| `supervised_learning_preprocessing_models.ipynb` | Fully executed notebook: preprocessing pipeline, both models, evaluation, interpretability |
| `supervised_learning_writeup.docx` | 2-page write-up: preprocessing rationale, model comparison, model selection |

## What's inside the notebook

**Preprocessing**
- Reproduces the exact Day 1 hold-out test set (same cleaning, same `train_test_split` parameters, `random_state=42`) — verified by recomputing the Day 1 rule baseline's precision on this test set
- Drops `education` (redundant with `education-num`) and `fnlwgt` (sampling weight, no business meaning)
- Groups `native-country` into `US` / `Non-US` before the split (a fixed rule, not a learned statistic, so no leakage)
- `ColumnTransformer`: median imputation + `StandardScaler` for numeric features, constant `"Missing"` imputation + `OneHotEncoder(handle_unknown='ignore')` for categorical features

**Models**
- Logistic Regression and Decision Tree, each wrapped in a `Pipeline` with the shared preprocessor, fit on the training split only

**Evaluation**
- Accuracy, precision, recall, F1, ROC AUC, PR AUC for both models, compared against the Day 1 baselines
- ROC and precision-recall curves
- Confusion matrices, with a discussion of false positives vs false negatives against the project's precision-focused business goal

**Interpretability**
- Logistic Regression coefficients mapped back to feature names, top 10 positive and negative with plain-English interpretation
- Decision Tree depth, leaf count, and train-vs-test accuracy to diagnose overfitting, plus the top 3 splits

**Reuse**
- Fitted preprocessor and both fitted pipelines saved with `joblib` for tomorrow's iteration

## Results summary

| Model | Accuracy | Precision | Recall | F1 | ROC AUC | PR AUC |
|---|---|---|---|---|---|---|
| Majority class (Day 1) | 0.761 | 0.000 | 0.000 | 0.000 | — | — |
| Rule: edu>=13 OR cap-gain>0 (Day 1) | 0.745 | 0.475 | 0.603 | 0.531 | 0.697 | 0.381 |
| Decision Tree (unrestricted) | 0.829 | 0.647 | 0.629 | 0.638 | 0.781 | 0.522 |
| Logistic Regression | 0.851 | 0.730 | 0.601 | 0.659 | 0.905 | 0.765 |

**Model carried forward: Logistic Regression.** Wins on every metric except recall (where it's close), its ROC/PR curves dominate across thresholds, and its coefficients are directly interpretable. The Decision Tree overfit badly at full depth (depth 49, train accuracy 0.977 vs test accuracy 0.829) and is worth revisiting only after pruning.

## Planned next iteration

- Constrain Decision Tree `max_depth` / `min_samples_leaf`
- Log-transform or bucket `capital-gain` and `capital-loss` (currently mostly zero with a long tail)
- Revisit handling of rare/unseen `occupation` categories at test time

**Author: Rida Noor**