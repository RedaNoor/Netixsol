"""
Derives match_details.parquet from the raw team_matches_home_away_raw.csv — the in-match detail
(quarter-by-quarter scores, goals/behinds breakdown) that Day 1's feature_table_matches_v1.parquet
correctly excluded (it's not a pre-match predictive feature) but a chat agent needs for questions
like "what was the quarter-time score" or "how many goals vs behinds did they kick".

The output (data/match_details.parquet) is already included — this script is here for
reproducibility/audit, not something you need to run again unless the raw data changes.

Run: python build_match_details.py   (from inside afl_chat_agent/)
"""
import pandas as pd
from pathlib import Path

_DIR = Path(__file__).parent
RAW_PATH = _DIR / "data" / "team_matches_home_away_raw.csv"
FEATURE_TABLE_PATH = _DIR / "data" / "feature_table_matches_v1.parquet"
OUT_PATH = _DIR / "data" / "match_details.parquet"

NAME_FIXES = {"W. Bulldogs": "Western Bulldogs"}


def normalize_team(s):
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s.islower():
        s = s.title()
    return NAME_FIXES.get(s, s)


def parse_quarter_scores(s: str) -> list:
    """'4.5 5.7 10.11 13.13' -> [{'goals': 4, 'behinds': 5, 'score': 29}, ...] cumulative per quarter."""
    out = []
    for token in s.split():
        g, b = token.split(".")
        g, b = int(g), int(b)
        out.append({"goals": g, "behinds": b, "score": g * 6 + b})
    return out


def build():
    raw = pd.read_csv(RAW_PATH, low_memory=False)
    raw["team"] = raw["team_name"].apply(normalize_team)
    raw["opponent"] = raw["opponent"].apply(normalize_team)
    raw["venue"] = raw["venue"].str.strip()
    raw["match_key"] = raw.apply(lambda r: "_".join(sorted([r["team"], r["opponent"]])), axis=1)
    raw["match_id"] = raw["match_key"] + "_" + raw["match_date"].astype(str) + "_" + raw["round"].astype(str)

    home = raw[raw["home_away"] == "H"].copy()
    away = raw[raw["home_away"] == "A"].copy()
    merged = home.merge(away, on="match_id", suffixes=("_home", "_away"), validate="one_to_one")

    mf = pd.read_parquet(FEATURE_TABLE_PATH)
    assert merged["match_id"].isin(mf["match_id"]).all(), "match_id join broken vs Day 1 feature table"

    out = merged[[
        "match_id", "team_home", "team_away",
        "team_quarter_scores_home", "team_goals_kicked_home", "team_behinds_home",
        "team_quarter_scores_away", "team_goals_kicked_away", "team_behinds_away",
    ]].rename(columns={"team_home": "home_team", "team_away": "away_team"})

    out["quarters_home"] = out["team_quarter_scores_home"].apply(parse_quarter_scores)
    out["quarters_away"] = out["team_quarter_scores_away"].apply(parse_quarter_scores)
    out = out.drop(columns=["team_quarter_scores_home", "team_quarter_scores_away"])
    out = out.rename(columns={
        "team_goals_kicked_home": "home_goals", "team_behinds_home": "home_behinds",
        "team_goals_kicked_away": "away_goals", "team_behinds_away": "away_behinds",
    })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"Saved {len(out)} rows to {OUT_PATH}")


if __name__ == "__main__":
    build()
