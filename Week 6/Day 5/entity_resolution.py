"""
Entity resolution for user-phrased team names, nicknames, and relative dates.

Prediction and retrieval requests come in phrased casually ("will the Pies beat the Cats this
week") but the tools need exact dataset keys and concrete dates. This module is the one place
that translation happens, so both the retrieval and prediction nodes resolve entities the same
way.
"""
import re
from datetime import datetime
import pandas as pd

from tools import VALID_TEAMS, normalize_team as _tools_normalize_team

TEAM_NICKNAMES = {
    "crows": "Adelaide Crows",
    "lions": "Brisbane Lions", "brisbane": "Brisbane Lions",
    "blues": "Carlton Blues", "carlton": "Carlton Blues",
    "pies": "Collingwood Magpies", "magpies": "Collingwood Magpies", "collingwood": "Collingwood Magpies",
    "bombers": "Essendon Bombers", "dons": "Essendon Bombers", "essendon": "Essendon Bombers",
    "dockers": "Fremantle Dockers", "freo": "Fremantle Dockers", "fremantle": "Fremantle Dockers",
    "cats": "Geelong Cats", "geelong": "Geelong Cats",
    "suns": "Gold Coast Suns", "gold coast": "Gold Coast Suns",
    "giants": "Greater Western Sydney Giants", "gws": "Greater Western Sydney Giants",
    "hawks": "Hawthorn Hawks", "hawthorn": "Hawthorn Hawks",
    "demons": "Melbourne Demons", "dees": "Melbourne Demons", "melbourne": "Melbourne Demons",
    "kangaroos": "North Melbourne Kangaroos", "roos": "North Melbourne Kangaroos",
    "north": "North Melbourne Kangaroos", "north melbourne": "North Melbourne Kangaroos",
    "power": "Port Adelaide Power", "port": "Port Adelaide Power", "port adelaide": "Port Adelaide Power",
    "tigers": "Richmond Tigers", "richmond": "Richmond Tigers",
    "saints": "St Kilda Saints", "st kilda": "St Kilda Saints",
    "swans": "Sydney Swans", "sydney": "Sydney Swans",
    "eagles": "West Coast Eagles", "west coast": "West Coast Eagles",
    "bulldogs": "Western Bulldogs", "dogs": "Western Bulldogs", "footscray": "Western Bulldogs",
    "western bulldogs": "Western Bulldogs",
}

RELATIVE_DATE_TERMS = {"this week", "next week", "this round", "next round", "upcoming",
                        "today", "tomorrow", "this weekend", "next weekend"}


class TeamResolutionError(ValueError):
    """Raised when a team reference can't be resolved — the caller should ask for clarification,
    not guess."""
    def __init__(self, original_text, suggestions=None):
        self.original_text = original_text
        self.suggestions = suggestions or []
        msg = f"Could not resolve team '{original_text}'."
        if self.suggestions:
            msg += f" Did you mean: {', '.join(self.suggestions)}?"
        super().__init__(msg)


def resolve_team(text: str) -> str:
    """
    Resolve a team reference (official name, nickname, or common abbreviation) to the exact
    canonical name the dataset uses. Raises TeamResolutionError rather than guessing if nothing
    reasonable matches — callers should route that to a clarification step, not a fallback.
    """
    if not isinstance(text, str) or not text.strip():
        raise TeamResolutionError(text)
    cleaned = text.strip().lower()
    cleaned = re.sub(r"^\s*the\s+", "", cleaned)  # "the Pies" -> "pies"

    if cleaned in TEAM_NICKNAMES:
        return TEAM_NICKNAMES[cleaned]

    try:
        return _tools_normalize_team(text)
    except ValueError:
        pass

    # last resort: substring match against nicknames and canonical names
    for nickname, canonical in TEAM_NICKNAMES.items():
        if nickname in cleaned or cleaned in nickname:
            return canonical
    for canonical in VALID_TEAMS:
        if cleaned in canonical.lower():
            return canonical

    close_nicknames = [n for n in TEAM_NICKNAMES if n[:3] == cleaned[:3]]
    suggestions = sorted({TEAM_NICKNAMES[n] for n in close_nicknames})[:3]
    raise TeamResolutionError(text, suggestions=suggestions)


def contains_relative_date(text: str) -> bool:
    """True if the text references a relative/unresolvable date like 'this week' or 'next round'."""
    lowered = text.lower()
    return any(term in lowered for term in RELATIVE_DATE_TERMS)


def resolve_date(text: str, dataset_latest_date) -> tuple:
    """
    Resolve a date reference to a concrete date the prediction model can use.
    Returns (resolved_date, note). A relative reference ("this week", "next round") can't be
    tied to a real fixture — there's no upcoming-fixture list in this dataset — so it falls back
    to the dataset's most recent known date and returns a note explaining that, rather than
    silently pretending it found a real scheduled match.
    """
    if not text or contains_relative_date(text):
        note = (f"No fixture list is available for future rounds, so this uses each team's most "
                 f"recently known form (as of {pd.Timestamp(dataset_latest_date).date()}) rather "
                 f"than a confirmed upcoming match date.")
        return dataset_latest_date, note

    try:
        return pd.Timestamp(text), None
    except Exception:
        note = (f"Could not parse '{text}' as a date — using the most recently known team form "
                f"(as of {pd.Timestamp(dataset_latest_date).date()}) instead.")
        return dataset_latest_date, note
