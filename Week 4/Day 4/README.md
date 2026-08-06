# Adult Income Prediction
## Model Tuning, Regularization & Reproducible Pipelines

## Overview

This project develops a reproducible machine learning pipeline for predicting whether an individual's annual income exceeds \$50K using the Adult Income dataset. The notebook builds upon baseline models by applying hyperparameter tuning, regularization analysis, probability calibration, threshold optimization, and final model evaluation.

---

## Objectives

- Build fully reproducible Scikit-learn pipelines.
- Tune multiple machine learning models using RandomizedSearchCV.
- Diagnose underfitting and overfitting using learning curves and hyperparameter analysis.
- Improve probability estimates using calibration techniques.
- Optimize the decision threshold based on Precision.
- Evaluate the final tuned model on an unseen test dataset.
- Save the complete trained pipeline for deployment.

---

## Models Evaluated

- Logistic Regression
- Random Forest Classifier
- HistGradientBoosting Classifier

The best-performing model was selected based on **cross-validated Precision**.

---

## Pipeline Architecture

```
Raw Dataset
      │
      ▼
Feature Engineering
      │
      ▼
ColumnTransformer
├── StandardScaler (Numerical Features)
└── OneHotEncoder (Categorical Features)
      │
      ▼
Machine Learning Model
      │
      ▼
Probability Calibration
      │
      ▼
Threshold Optimization
      │
      ▼
Final Prediction
```

---

## Evaluation Metrics

The final model was evaluated using:

- Accuracy
- Precision (Primary Metric)
- Recall
- F1-score
- ROC-AUC
- Precision-Recall AUC
- Brier Score
- Confusion Matrix
- ROC Curve
- Precision-Recall Curve
- Calibration Curve

---

## Reproducibility

The notebook is fully reproducible.

- Random Seed: **42**
- Cross Validation: **Stratified 5-Fold**
- Hyperparameter Search: **RandomizedSearchCV**
- Primary Metric: **Precision**

All preprocessing, feature engineering, model training, calibration, and evaluation steps are implemented inside Scikit-learn Pipelines.

---

## Project Structure

```
## Project Structure

## Project Structure

```
.
├── day4_model_tuning.ipynb
├── adult_income_pipeline.joblib
├── README.md
├── tuning_report.pdf
└── 50_iterations/
    ├── day4_model_tuning_50_iterations.ipynb
    └── outputs/
```

> **Note:** The main notebook uses a reduced RandomizedSearchCV search budget for faster execution. A separate folder named **`50_iterations`** contains the notebook and outputs generated using **50 RandomizedSearchCV iterations**, as recommended in the assignment, for more extensive hyperparameter tuning.
```

---

## Requirements

- Python 3.x
- pandas
- numpy
- scikit-learn
- matplotlib
- joblib

---

## Running the Notebook

1. Install the required Python libraries.
2. Open the notebook in Jupyter Notebook or JupyterLab.
3. Run all cells sequentially from top to bottom.
4. The notebook will:
   - Load and preprocess the data.
   - Train and tune candidate models.
   - Evaluate calibration and optimize the classification threshold.
   - Evaluate the final model on the hold-out test set.
   - Save the trained pipeline as `adult_income_pipeline.joblib`.

---

## Saved Model

The trained pipeline is saved as:

```
adult_income_pipeline.joblib
```

The saved artifact contains the calibrated pipeline and the optimized decision threshold, allowing direct inference on new data.

---
