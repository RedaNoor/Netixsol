import joblib
import pandas as pd
import numpy as np
import sys

PIPELINE_PATH = "adult_income_pipeline.joblib"
EXPLAINER_PATH = "adult_income_shap_explainer.joblib"


def engineer_features(X):
    X = X.copy()

    X["has_capital_gain"] = (X["capital-gain"] > 0).astype(int)
    X["log_capital_gain"] = np.log1p(X["capital-gain"].astype(float))
    X["log_capital_loss"] = np.log1p(X["capital-loss"].astype(float))

    X["higher_education"] = X["education"].astype(str).isin(
        ["Bachelors", "Masters", "Doctorate", "Prof-school"]
    ).astype(int)

    X["edu_hours_interaction"] = (
        X["education-num"].astype(float) * X["hours-per-week"].astype(float)
    )

    X["is_married"] = (
        X["marital-status"].astype(str).str.contains("Married")
    ).astype(int)

    X["age_bucket"] = pd.cut(
        X["age"].astype(float),
        bins=[0, 25, 45, 65, 100],
        labels=["Young", "Adult", "Middle", "Senior"]
    )

    X["hours_bin"] = pd.cut(
        X["hours-per-week"].astype(float),
        bins=[0, 30, 40, 50, 100],
        labels=["Part", "Full", "Overtime", "Extreme"]
    )

    return X


# The pipeline was pickled while `engineer_features` lived on the notebook's
# `__main__` module. When this file is imported (rather than run directly),
# `__main__` is whatever the entry-point script is, so we register the
# function there too to make unpickling work either way.
sys.modules["__main__"].engineer_features = engineer_features

pipeline = joblib.load(PIPELINE_PATH)
explainer = joblib.load(EXPLAINER_PATH)

# -------------------------------------------------------
# Required columns (matches X_train.columns in the notebook — fnlwgt was
# dropped before training and is intentionally NOT required here)
# -------------------------------------------------------

REQUIRED_COLUMNS = [
    "age",
    "workclass",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
]

feature_names = pipeline.named_steps["preprocessor"].get_feature_names_out()

# -------------------------------------------------------
# Input normalisation & validation
# -------------------------------------------------------


def _to_dataframe(data):
    """Normalise dict / Series / DataFrame / CSV-path input into a well-typed
    DataFrame. Building from a dict (rather than `Series.to_frame().T`) lets
    pandas infer a proper numeric dtype per column instead of falling back
    to `object`, which is what broke `np.log1p` previously."""
    if isinstance(data, dict):
        return pd.DataFrame([data])
    elif isinstance(data, pd.Series):
        return pd.DataFrame([data.to_dict()])
    elif isinstance(data, pd.DataFrame):
        return data.reset_index(drop=True)
    elif isinstance(data, str):
        return pd.read_csv(data)
    else:
        raise TypeError(f"Unsupported input type: {type(data)}")


def validate_input(df):
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    return df[REQUIRED_COLUMNS]


# -------------------------------------------------------
# Prediction (probability + class + top-3 SHAP features, in one call)
# -------------------------------------------------------


def predict_income(data, threshold=0.50, top_n=3):
    df_in = _to_dataframe(data)
    df_in = validate_input(df_in)

    probability = pipeline.predict_proba(df_in)[:, 1]
    prediction = (probability >= threshold).astype(int)

    engineered = engineer_features(df_in)
    transformed = pipeline.named_steps["preprocessor"].transform(engineered)
    row_shap = explainer(transformed, check_additivity=False)

    results = []
    for i in range(len(df_in)):
        contributions = pd.DataFrame({
            "Feature": feature_names,
            "Contribution": np.abs(row_shap.values[i]),
        }).sort_values("Contribution", ascending=False).head(top_n)

        results.append({
            "Probability": round(float(probability[i]), 4),
            "Predicted Class": int(prediction[i]),
            "Top Features": contributions.to_dict("records"),
        })

    return results


# -------------------------------------------------------
# CLI
# -------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) == 2:
        input_data = sys.argv[1]
    else:
        print("No CSV supplied. Using built-in sample.\n")
        input_data = {
            "age": 46,
            "workclass": "Private",
            "education": "Masters",
            "education-num": 14,
            "marital-status": "Married-civ-spouse",
            "occupation": "Exec-managerial",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 15000,
            "capital-loss": 0,
            "hours-per-week": 50,
            "native-country": "United-States",
        }

    predictions = predict_income(input_data)

    print("\nPrediction Results\n")
    print(pd.DataFrame(predictions))
