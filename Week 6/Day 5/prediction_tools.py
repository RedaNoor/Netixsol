"""
LangChain tool wrappers around the Day 2 prediction models (predict.py), callable from the
prediction node. Entity resolution (team nicknames, relative dates) happens inside these tools
rather than being left to the LLM to get right — the model is asked to extract raw mentions
("the Pies", "this week"), and resolution to the dataset's exact keys is deterministic Python,
not another LLM guess.

Every function here returns a plain dict on both success and failure (never raises) so the
prediction node and validation node can inspect the result uniformly rather than catching
exceptions in two different places.
"""
import pandas as pd
from typing import Optional
from langchain_core.tools import tool

import predict
import explain
import entity_resolution as er


@tool
def predict_match_winner_tool(team_a: str, team_b: str, date: Optional[str] = None) -> dict:
    """Predict the winner of a match between two AFL teams (team_a is treated as home).
    team_a and team_b can be official names, nicknames, or common abbreviations (e.g. "Pies",
    "Cats"). date can be a specific date, a relative reference like "this week" (which falls
    back to each team's most recent known form, since no future fixture list exists), or
    omitted entirely."""
    try:
        resolved_a = er.resolve_team(team_a)
    except er.TeamResolutionError as e:
        return {"error": str(e), "error_type": "team_resolution", "unresolved": team_a,
                "suggestions": e.suggestions}
    try:
        resolved_b = er.resolve_team(team_b)
    except er.TeamResolutionError as e:
        return {"error": str(e), "error_type": "team_resolution", "unresolved": team_b,
                "suggestions": e.suggestions}
    if resolved_a == resolved_b:
        return {"error": f"'{team_a}' and '{team_b}' both resolved to {resolved_a} — need two different teams.",
                "error_type": "same_team"}

    resolved_date, date_note = er.resolve_date(date or "", predict.DATE_MAX)

    try:
        result = predict.predict_match_winner(resolved_a, resolved_b, str(pd.Timestamp(resolved_date).date()))
    except Exception as e:
        return {"error": str(e), "error_type": "model_error"}

    result["explanation"] = explain.explain_match_prediction(result.pop("feature_row"), top_n=3)
    if date_note:
        result["notes"] = result.get("notes", []) + [date_note]
    return result


@tool
def predict_top_player_tool(team: str, stat_type: str = "fantasy_points", date: Optional[str] = None, top_k: int = 5) -> dict:
    """Predict the likely top-performing players for a team's next match, ranked by a stat.
    team can be an official name, nickname, or abbreviation. stat_type is 'fantasy_points'
    (uses the trained regression model), 'disposals', or 'goals' (these two use a simpler
    rolling-average estimate, not a full model — say so if asked which). date can be a specific
    date, a relative reference like "this week", or omitted."""
    try:
        resolved_team = er.resolve_team(team)
    except er.TeamResolutionError as e:
        return {"error": str(e), "error_type": "team_resolution", "unresolved": team,
                "suggestions": e.suggestions}

    if stat_type not in ("fantasy_points", "disposals", "goals"):
        return {"error": f"'{stat_type}' isn't a supported stat for prediction.",
                "error_type": "unsupported_stat", "stat_type": stat_type}

    resolved_date, date_note = er.resolve_date(date or "", predict.DATE_MAX)

    try:
        predictions = predict.predict_top_player(
            resolved_team, stat_type=stat_type,
            date=str(pd.Timestamp(resolved_date).date()), top_k=top_k)
    except Exception as e:
        return {"error": str(e), "error_type": "model_error"}

    result = {
        "team": resolved_team, "stat_type": stat_type, "predictions": predictions,
        "model_based": stat_type == "fantasy_points",
        "notes": [date_note] if date_note else [],
    }
    if stat_type != "fantasy_points":
        result["notes"].append(
            f"'{stat_type}' predictions use a rolling-average estimate, not the trained "
            f"regression model — fantasy_points is the only fully model-based prediction here.")
    return result
