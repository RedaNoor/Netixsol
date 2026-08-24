"""
Explanation layer for match-winner predictions.

Every prediction response needs to show what's driving it, not just a bare probability. This
computes a global permutation-importance ranking once (same method as the Day 2 notebook, same
held-out season), then for a specific prediction reports the top-ranked features alongside their
actual values for that matchup.

This is deliberately NOT presented as a per-prediction causal attribution (that would need
something like SHAP, which isn't part of this project's model stack) — it's an honest "these are
the factors this model leans on most in general, and here's where this matchup sits on them,"
which is a materially different and more defensible claim.
"""
import os
import warnings
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
warnings.filterwarnings(
    "ignore",
    message=r"Could not find the number of physical cores.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Setting the shape on a NumPy array has been deprecated.*",
    category=DeprecationWarning,
)

import pandas as pd
import numpy as np
from sklearn.inspection import permutation_importance
import joblib

_DIR = Path(__file__).parent / "data"

FEATURE_LABELS = {
    "form_win_rate_last5": "recent form (win rate, last 5 games)",
    "form_avg_score_last5": "recent scoring output (avg, last 5 games)",
    "form_avg_margin_last5": "recent winning margin (avg, last 5 games)",
    "win_streak": "current win/loss streak",
    "days_rest": "days of rest before this match",
    "ladder_pos_before": "ladder position",
    "h2h_win_rate_prior": "historical head-to-head record vs this opponent",
    "away_is_interstate": "away team traveling interstate",
}

NUMERIC_MATCH_FEATURES = [
    "form_win_rate_last5_home", "form_avg_score_last5_home", "form_avg_margin_last5_home",
    "win_streak_home", "days_rest_home", "ladder_pos_before_home", "h2h_win_rate_prior_home",
    "form_win_rate_last5_away", "form_avg_score_last5_away", "form_avg_margin_last5_away",
    "win_streak_away", "days_rest_away", "ladder_pos_before_away", "h2h_win_rate_prior_away",
    "away_is_interstate",
]

_importance_cache = None


def _global_importance_ranking():
    """Computed once, cached — same held-out season and method as the Day 2 notebook."""
    global _importance_cache
    if _importance_cache is not None:
        return _importance_cache

    model = joblib.load(_DIR / "model_match_winner_hgb.joblib")
    mf = pd.read_parquet(_DIR / "feature_table_matches_v1.parquet")
    holdout_year = mf["year"].max()
    test = mf[mf["year"] == holdout_year]
    X_test, y_test = test[NUMERIC_MATCH_FEATURES], test["target_result"]

    perm = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, scoring="accuracy")
    ranking = sorted(zip(NUMERIC_MATCH_FEATURES, perm.importances_mean), key=lambda x: -x[1])
    _importance_cache = [f for f, _ in ranking]
    return _importance_cache


def _friendly_label(feature_name: str) -> tuple:
    for base, label in FEATURE_LABELS.items():
        if feature_name.startswith(base):
            side = "home" if feature_name.endswith("_home") else ("away" if feature_name.endswith("_away") else None)
            return label, side
    return feature_name, None


def _to_python_scalar(value):
    """Convert NumPy/Pandas scalars into plain Python values for safe state serialization."""
    if isinstance(value, dict):
        return {k: _to_python_scalar(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_python_scalar(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_to_python_scalar(v) for v in value)
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return _to_python_scalar(value.item())
        except (AttributeError, TypeError, ValueError):
            pass
    return value


def explain_match_prediction(feature_row: dict, top_n: int = 3) -> list:
    """
    Given the feature dict used for a specific match prediction, return the top_n most globally
    important features with a plain-language label and this matchup's actual value on each.
    """
    ranking = _global_importance_ranking()
    out = []
    seen_labels = set()
    for feat in ranking:
        label, side = _friendly_label(feat)
        if label in seen_labels:
            continue
        seen_labels.add(label)

        home_key = feat if feat.endswith("_home") else feat.replace("_away", "_home")
        away_key = feat if feat.endswith("_away") else feat.replace("_home", "_away")
        if home_key in feature_row and away_key in feature_row:
            out.append({
                "factor": label,
                "home_value": _to_python_scalar(feature_row.get(home_key)),
                "away_value": _to_python_scalar(feature_row.get(away_key)),
            })
        else:
            out.append({"factor": label, "value": _to_python_scalar(feature_row.get(feat))})

        if len(out) >= top_n:
            break
    return out
