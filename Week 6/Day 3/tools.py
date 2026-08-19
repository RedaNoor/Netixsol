"""
Structured query tools over the AFL feature tables.

These are exact lookups against real match and player data. No numbers here are generated
or estimated by a model — every value returned is read directly from the dataset, which is
why stat questions are routed through these functions instead of left to the language model.
"""
import pandas as pd
from pathlib import Path
from difflib import get_close_matches

_DATA_DIR = Path(__file__).parent / "data"

_matches = pd.read_parquet(_DATA_DIR / "feature_table_matches_v1.parquet")
_rounds = pd.read_parquet(_DATA_DIR / "feature_table_players_v1.parquet")
_players_info = pd.read_csv(_DATA_DIR / "players_info.csv", low_memory=False)
_match_details = pd.read_parquet(_DATA_DIR / "match_details.parquet")

# players_info.csv data quality fix: 257 of 2,843 player_name values (9%) carry leading/
# trailing whitespace (e.g. " Karl Amon "), which breaks exact-match name resolution and
# looks wrong in any answer that echoes the name back. Every other text column in this file
# is already clean; only player_name needs this.
_players_info["player_name"] = _players_info["player_name"].str.strip()

FINALS_ROUNDS = {"EF", "QF", "SF", "PF", "GF"}

VALID_TEAMS = sorted(set(_matches["home_team"]) | set(_matches["away_team"]))

NAME_FIXES = {"W. Bulldogs": "Western Bulldogs"}


def normalize_team(name: str) -> str:
    """Resolve a team name to its canonical form, or raise ValueError if it can't be matched."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Team name must be a non-empty string.")
    n = name.strip()
    if n.islower():
        n = n.title()
    n = NAME_FIXES.get(n, n)
    if n in VALID_TEAMS:
        return n
    close = get_close_matches(n, VALID_TEAMS, n=1, cutoff=0.6)
    if close:
        return close[0]
    raise ValueError(f"Unknown team '{name}'. Valid teams: {', '.join(VALID_TEAMS)}")


def resolve_player(name: str, team: str = None, year: int = None):
    """
    Resolve a player name to a single player_id. If the name matches more than one player,
    narrow using team/year when given; otherwise return an ambiguity error listing the options.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Player name must be a non-empty string.")
    n = name.strip().lower()

    exact = _players_info[_players_info["player_name"].str.strip().str.lower() == n]
    if exact.empty:
        candidates = get_close_matches(name.strip(), _players_info["player_name"].dropna().tolist(), n=3, cutoff=0.75)
        if not candidates:
            raise ValueError(f"No player found matching '{name}'.")
        exact = _players_info[_players_info["player_name"].isin(candidates)]

    if len(exact) == 1:
        return int(exact.iloc[0]["id"]), exact.iloc[0]["player_name"]

    ids = exact["id"].tolist()
    rows = _rounds[_rounds["player_id"].isin(ids)]
    if team is not None:
        rows = rows[rows["team"] == normalize_team(team)]
    if year is not None:
        rows = rows[rows["year"] == year]

    if rows.empty:
        options = ", ".join(f"{r['player_name']} (id {r['id']})" for _, r in exact.iterrows())
        raise ValueError(
            f"'{name}' matches multiple players and none played for the given team/year. Options: {options}")

    counts = rows.groupby("player_id").size().sort_values(ascending=False)
    best_id = int(counts.index[0])
    best_name = exact[exact["id"] == best_id].iloc[0]["player_name"]
    return best_id, best_name


# ---------------------------------------------------------------------------
# Tool 1: head-to-head team record
# ---------------------------------------------------------------------------
def get_team_head_to_head(team_a: str, team_b: str) -> dict:
    """
    All-time head-to-head record between two teams, plus their last 5 meetings.
    """
    a = normalize_team(team_a)
    b = normalize_team(team_b)
    if a == b:
        raise ValueError("team_a and team_b must be different teams.")

    home_ab = _matches[(_matches["home_team"] == a) & (_matches["away_team"] == b)]
    home_ba = _matches[(_matches["home_team"] == b) & (_matches["away_team"] == a)]

    wins_a = (home_ab["target_result"] == "HOME_WIN").sum() + (home_ba["target_result"] == "AWAY_WIN").sum()
    wins_b = (home_ab["target_result"] == "AWAY_WIN").sum() + (home_ba["target_result"] == "HOME_WIN").sum()
    draws = (home_ab["target_result"] == "DRAW").sum() + (home_ba["target_result"] == "DRAW").sum()
    total = len(home_ab) + len(home_ba)

    combined = pd.concat([home_ab, home_ba]).sort_values("match_date", ascending=False)
    last5 = []
    for _, r in combined.head(5).iterrows():
        last5.append({
            "date": str(r["match_date"].date()),
            "home_team": r["home_team"], "away_team": r["away_team"],
            "score": f"{r['home_score']}-{r['away_score']}",
            "result": r["target_result"],
        })

    return {
        "team_a": a, "team_b": b,
        "total_meetings": int(total),
        f"{a}_wins": int(wins_a), f"{b}_wins": int(wins_b), "draws": int(draws),
        "last_5_meetings": last5,
    }


# ---------------------------------------------------------------------------
# Tool 2: player season stats
# ---------------------------------------------------------------------------
def get_player_season_stats(player_name: str, year: int, team: str = None, include_finals: bool = False) -> dict:
    """
    A player's aggregated stats for a single AFL season: games played, totals and per-game
    averages for disposals, goals, and fantasy points. Defaults to home-and-away season only
    (the standard meaning of "season stats"); pass include_finals=True to fold finals games in,
    or call get_player_finals_stats separately to look at finals in isolation.
    """
    player_id, resolved_name = resolve_player(player_name, team=team, year=year)
    rows = _rounds[(_rounds["player_id"] == player_id) & (_rounds["year"] == year)]
    if not include_finals:
        rows = rows[~rows["round"].isin(FINALS_ROUNDS)]
    if rows.empty:
        scope = "season" if not include_finals else "season (incl. finals)"
        raise ValueError(f"No {scope} games found for {resolved_name} in {year}.")

    return {
        "player": resolved_name, "year": int(year), "includes_finals": include_finals,
        "team": rows["team"].mode().iat[0] if not rows["team"].mode().empty else None,
        "games_played": int(len(rows)),
        "total_disposals": int(rows["disposals"].sum(skipna=True)),
        "avg_disposals": round(float(rows["disposals"].mean(skipna=True)), 1),
        "total_goals": int(rows["goals"].sum(skipna=True)),
        "avg_goals": round(float(rows["goals"].mean(skipna=True)), 2),
        "avg_fantasy_points": round(float(rows["fantasy_points"].mean(skipna=True)), 1),
        "brownlow_votes": int(rows["brownlow_votes"].sum(skipna=True)),
    }


# ---------------------------------------------------------------------------
# Tool: player finals stats (isolated from home-and-away season)
# ---------------------------------------------------------------------------
def get_player_finals_stats(player_name: str, year: int, team: str = None) -> dict:
    """
    A player's stats across finals games only (Elimination/Qualifying/Semi/Preliminary/Grand
    Final) for a given season. Use this for finals-specific questions, kept separate from the
    home-and-away season since finals form is often discussed distinctly.
    """
    player_id, resolved_name = resolve_player(player_name, team=team, year=year)
    rows = _rounds[(_rounds["player_id"] == player_id) & (_rounds["year"] == year)
                   & (_rounds["round"].isin(FINALS_ROUNDS))]
    if rows.empty:
        raise ValueError(f"No finals games found for {resolved_name} in {year}.")

    return {
        "player": resolved_name, "year": int(year),
        "finals_played": int(len(rows)),
        "rounds": rows.sort_values("match_date")["round"].tolist(),
        "avg_disposals": round(float(rows["disposals"].mean(skipna=True)), 1),
        "total_goals": int(rows["goals"].sum(skipna=True)),
        "avg_fantasy_points": round(float(rows["fantasy_points"].mean(skipna=True)), 1),
    }


# ---------------------------------------------------------------------------
# Tool 3: player recent games log
# ---------------------------------------------------------------------------
def get_player_recent_games(player_name: str, n: int = 1, team: str = None) -> dict:
    """
    A player's most recent n games with full per-game stats, most recent first.
    Use this for "last round" / "last game" / "last N games" style questions.
    """
    player_id, resolved_name = resolve_player(player_name, team=team)
    rows = _rounds[_rounds["player_id"] == player_id].sort_values("match_date", ascending=False)
    if rows.empty:
        raise ValueError(f"No games found for {resolved_name}.")

    games = []
    for _, r in rows.head(n).iterrows():
        games.append({
            "date": str(r["match_date"].date()), "year": int(r["year"]), "round": r["round"],
            "team": r["team"], "opponent": r["opponent"], "result": r["result"],
            "disposals": None if pd.isna(r["disposals"]) else int(r["disposals"]),
            "goals": int(r["goals"]) if pd.notna(r["goals"]) else None,
            "fantasy_points": None if pd.isna(r["fantasy_points"]) else int(r["fantasy_points"]),
        })

    return {"player": resolved_name, "games_returned": len(games), "games": games}


# ---------------------------------------------------------------------------
# Tool 4: player career stats
# ---------------------------------------------------------------------------
def get_player_career_stats(player_name: str, team: str = None) -> dict:
    """
    A player's full career totals and per-game averages across every season in the dataset.
    Use this for "career average" comparison questions.
    """
    player_id, resolved_name = resolve_player(player_name, team=team)
    rows = _rounds[_rounds["player_id"] == player_id]
    if rows.empty:
        raise ValueError(f"No games found for {resolved_name}.")

    return {
        "player": resolved_name,
        "career_games": int(len(rows)),
        "seasons": sorted(rows["year"].unique().tolist()),
        "career_avg_disposals": round(float(rows["disposals"].mean(skipna=True)), 1),
        "career_avg_goals": round(float(rows["goals"].mean(skipna=True)), 2),
        "career_avg_fantasy_points": round(float(rows["fantasy_points"].mean(skipna=True)), 1),
        "career_total_goals": int(rows["goals"].sum(skipna=True)),
        "career_brownlow_votes": int(rows["brownlow_votes"].sum(skipna=True)),
    }


# ---------------------------------------------------------------------------
# Tool 5: team season record
# ---------------------------------------------------------------------------
def get_team_season_record(team: str, year: int) -> dict:
    """
    A team's win/loss/draw record for a given season, plus points scored/conceded.
    """
    t = normalize_team(team)
    home = _matches[(_matches["home_team"] == t) & (_matches["year"] == year)]
    away = _matches[(_matches["away_team"] == t) & (_matches["year"] == year)]
    if home.empty and away.empty:
        raise ValueError(f"No matches found for {t} in {year}.")

    wins = (home["target_result"] == "HOME_WIN").sum() + (away["target_result"] == "AWAY_WIN").sum()
    losses = (home["target_result"] == "AWAY_WIN").sum() + (away["target_result"] == "HOME_WIN").sum()
    draws = (home["target_result"] == "DRAW").sum() + (away["target_result"] == "DRAW").sum()
    points_for = home["home_score"].sum() + away["away_score"].sum()
    points_against = home["away_score"].sum() + away["home_score"].sum()

    return {
        "team": t, "year": int(year),
        "games_played": int(len(home) + len(away)),
        "wins": int(wins), "losses": int(losses), "draws": int(draws),
        "points_for": int(points_for), "points_against": int(points_against),
        "percentage": round(float(points_for) / float(points_against) * 100, 1) if points_against else None,
    }


# ---------------------------------------------------------------------------
# Tool: match score breakdown (quarter-by-quarter, goals/behinds)
# ---------------------------------------------------------------------------
def get_match_score_breakdown(team_a: str, team_b: str, year: int = None, round: str = None) -> dict:
    """
    Quarter-by-quarter running score and goals/behinds breakdown for a specific match between
    two teams. If year/round aren't given and the teams have met more than once, returns their
    most recent meeting and notes how many other meetings exist.
    """
    a = normalize_team(team_a)
    b = normalize_team(team_b)
    if a == b:
        raise ValueError("team_a and team_b must be different teams.")

    home_ab = _matches[(_matches["home_team"] == a) & (_matches["away_team"] == b)]
    home_ba = _matches[(_matches["home_team"] == b) & (_matches["away_team"] == a)]
    candidates = pd.concat([home_ab, home_ba])
    if year is not None:
        candidates = candidates[candidates["year"] == year]
    if round is not None:
        candidates = candidates[candidates["round"].astype(str) == str(round)]
    if candidates.empty:
        raise ValueError(f"No match found between {a} and {b}" +
                          (f" in {year}" if year else "") + (f" round {round}" if round else "") + ".")

    candidates = candidates.sort_values("match_date", ascending=False)
    chosen = candidates.iloc[0]
    other_meetings = len(candidates) - 1

    detail = _match_details[_match_details["match_id"] == chosen["match_id"]]
    if detail.empty:
        raise ValueError(f"No quarter-by-quarter detail found for this match (match_id {chosen['match_id']}).")
    d = detail.iloc[0]

    return {
        "home_team": d["home_team"], "away_team": d["away_team"],
        "date": str(chosen["match_date"].date()), "year": int(chosen["year"]), "round": chosen["round"],
        "final_score": f"{chosen['home_score']}-{chosen['away_score']}",
        "home_goals": int(d["home_goals"]), "home_behinds": int(d["home_behinds"]),
        "away_goals": int(d["away_goals"]), "away_behinds": int(d["away_behinds"]),
        "quarter_by_quarter_home": [dict(q) for q in d["quarters_home"]],
        "quarter_by_quarter_away": [dict(q) for q in d["quarters_away"]],
        "note": (f"{a} and {b} have met {other_meetings} other time(s); "
                 f"pass year/round to look at a different meeting.") if other_meetings else None,
    }


# ---------------------------------------------------------------------------
# Tool: round / Grand Final lookup
# ---------------------------------------------------------------------------
def get_round_matches(year: int, round: str) -> list:
    """
    All matches played in a given year and round, with final scores and results.
    round can be a regular round number as a string ('1', '12') or a finals round code:
    'EF' (Elimination Final), 'QF' (Qualifying Final), 'SF' (Semi Final),
    'PF' (Preliminary Final), 'GF' (Grand Final).
    """
    rows = _matches[(_matches["year"] == year) & (_matches["round"].astype(str) == str(round))]
    if rows.empty:
        raise ValueError(f"No matches found for {year} round {round}.")

    out = []
    for _, r in rows.sort_values("match_date").iterrows():
        winner = (r["home_team"] if r["target_result"] == "HOME_WIN"
                  else r["away_team"] if r["target_result"] == "AWAY_WIN" else "Draw")
        out.append({
            "date": str(r["match_date"].date()), "home_team": r["home_team"], "away_team": r["away_team"],
            "final_score": f"{int(r['home_score'])}-{int(r['away_score'])}",
            "winner": winner, "venue": r["venue"],
        })
    return out


# ---------------------------------------------------------------------------
# Tool: season leaderboard
# ---------------------------------------------------------------------------
def get_season_leaderboard(year: int, stat: str = "fantasy_points", team: str = None,
                            top_n: int = 10, mode: str = "total", min_games: int = 5,
                            include_finals: bool = False) -> list:
    """
    Rank players for a season by a chosen stat. stat can be 'disposals', 'goals',
    'fantasy_points', 'brownlow_votes', or 'wins' (number of matches their team won while
    they played). mode is 'total' (season sum, the usual meaning of "leading goalkicker") or
    'average' (per-game, only applied to players with at least min_games games to avoid a
    single big game dominating the ranking). Pass team to restrict to one club's players.
    """
    valid_stats = {"disposals", "goals", "fantasy_points", "brownlow_votes", "wins"}
    if stat not in valid_stats:
        raise ValueError(f"stat must be one of {sorted(valid_stats)}")
    if mode not in ("total", "average"):
        raise ValueError("mode must be 'total' or 'average'")

    rows = _rounds[_rounds["year"] == year]
    if not include_finals:
        rows = rows[~rows["round"].isin(FINALS_ROUNDS)]
    if team is not None:
        rows = rows[rows["team"] == normalize_team(team)]
    if rows.empty:
        raise ValueError(f"No player data found for {year}" + (f" for {team}" if team else "") + ".")

    if stat == "wins":
        rows = rows.assign(win=(rows["result"] == "W").astype(int))
        grouped = rows.groupby("player_id").agg(value=("win", "sum"), games_played=("win", "count"))
    else:
        agg_fn = "sum" if mode == "total" else "mean"
        grouped = rows.groupby("player_id").agg(
            value=(stat, agg_fn), games_played=(stat, "count"))
        if mode == "average":
            grouped = grouped[grouped["games_played"] >= min_games]

    if grouped.empty:
        raise ValueError(f"No players met the minimum games threshold ({min_games}) for {year}.")

    grouped = grouped.sort_values("value", ascending=False).head(top_n)
    grouped = grouped.merge(_players_info[["id", "player_name"]], left_on="player_id", right_on="id")

    return [
        {"player": r["player_name"], "value": round(float(r["value"]), 2), "games_played": int(r["games_played"])}
        for _, r in grouped.iterrows()
    ]


# ---------------------------------------------------------------------------
# Tool: team roster
# ---------------------------------------------------------------------------
def get_team_roster(team: str, year: int = None) -> dict:
    """
    Players who played at least one game for a team in a given season, sorted by games played.
    If year isn't given, uses the most recent season in the dataset.
    """
    t = normalize_team(team)
    if year is None:
        year = int(_rounds["year"].max())
    rows = _rounds[(_rounds["team"] == t) & (_rounds["year"] == year)]
    if rows.empty:
        raise ValueError(f"No roster data found for {t} in {year}.")

    grouped = rows.groupby("player_id").size().reset_index(name="games_played")
    grouped = grouped.merge(_players_info[["id", "player_name"]], left_on="player_id", right_on="id")
    grouped = grouped.sort_values("games_played", ascending=False)

    return {
        "team": t, "year": int(year), "roster_size": len(grouped),
        "players": [{"player": r["player_name"], "games_played": int(r["games_played"])}
                    for _, r in grouped.iterrows()],
    }


# ---------------------------------------------------------------------------
# Tool: player biography
# ---------------------------------------------------------------------------
def get_player_bio(player_name: str, team: str = None) -> dict:
    """
    A player's biographical details: full name, birth date, height, weight, debut date, and
    every AFL team they've played for. Use this for non-stat questions like "how tall is X",
    "when did X debut", or "which teams has X played for".
    """
    player_id, resolved_name = resolve_player(player_name, team=team)
    info = _players_info[_players_info["id"] == player_id]
    if info.empty:
        raise ValueError(f"No biographical record found for {resolved_name}.")
    row = info.iloc[0]

    teams_raw = str(row["player_teams"]) if pd.notna(row["player_teams"]) else "Unknown"
    teams = [t.strip() for t in teams_raw.strip("{}").split(",")] if teams_raw != "Unknown" else []

    # player_full_name is stored as a URL-slug (e.g. "Patrick_Dangerfield"), not a display name —
    # underscores are swapped for spaces for readability. A trailing digit occasionally appears
    # (e.g. "Gary_Ablett1"); it's a slug-uniqueness artifact from the source site, not meaningful
    # season/player disambiguation, so it's left as-is rather than guessed at and stripped.
    full_name = row["player_full_name"].replace("_", " ") if pd.notna(row["player_full_name"]) else resolved_name

    return {
        "player": resolved_name,
        "full_name": full_name,
        "born_date": row["born_date"] if pd.notna(row["born_date"]) else None,
        "debut_date": row["debut_date"] if pd.notna(row["debut_date"]) else None,
        "debut_age": None if pd.isna(row["debut_age"]) else round(float(row["debut_age"]), 1),
        "last_played_date": row["last_date"] if pd.notna(row["last_date"]) else None,
        "height_cm": None if pd.isna(row["height"]) else int(row["height"]),
        "weight_kg": None if pd.isna(row["weight"]) else int(row["weight"]),
        "teams_played_for": teams,
    }
