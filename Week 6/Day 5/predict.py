"""
predict.py — Week 6 Day 2 deliverable.

Clean, documented, callable wrappers around the saved match-winner and top-player models.
This is exactly the interface Day 4's LangChain/LangGraph tools wrap directly.

Required files alongside this module (all produced by day2_pipeline.py / the Day 2 notebook):
    model_match_winner_hgb.joblib
    model_top_player_ridge.joblib
    team_match_history.parquet
    player_match_history.parquet
    players_lookup.parquet

Usage:
    from predict import predict_match_winner, predict_top_player

    predict_match_winner("Hawthorn Hawks", "Carlton Blues", "2025-08-20")
    predict_top_player("Hawthorn Hawks", stat_type="fantasy_points", date="2025-08-20")
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime

_DIR = Path(__file__).parent / 'data'

_match_model = joblib.load(_DIR / 'model_match_winner_hgb.joblib')
_player_model = joblib.load(_DIR / 'model_top_player_ridge.joblib')
_team_hist = pd.read_parquet(_DIR / 'team_match_history.parquet')
_player_hist = pd.read_parquet(_DIR / 'player_match_history.parquet')
_players_lookup = pd.read_parquet(_DIR / 'players_lookup.parquet')
# same fix as Day 3's tools.py: 257 of 2,843 player_name values carry stray whitespace
# (e.g. " Karl Amon "), which this file inherited since it was generated before that fix.
_players_lookup['player_name'] = _players_lookup['player_name'].str.strip()

VALID_TEAMS = sorted(_team_hist['team'].unique())
DATE_MIN = _team_hist['match_date'].min()
DATE_MAX = _team_hist['match_date'].max()

NAME_FIXES = {'W. Bulldogs': 'Western Bulldogs'}
NUMERIC_MATCH_FEATURES = [
    'form_win_rate_last5_home', 'form_avg_score_last5_home', 'form_avg_margin_last5_home',
    'win_streak_home', 'days_rest_home', 'ladder_pos_before_home', 'h2h_win_rate_prior_home',
    'form_win_rate_last5_away', 'form_avg_score_last5_away', 'form_avg_margin_last5_away',
    'win_streak_away', 'days_rest_away', 'ladder_pos_before_away', 'h2h_win_rate_prior_away',
    'away_is_interstate',
]


class TeamNotFoundError(ValueError):
    pass


class DateOutOfRangeError(ValueError):
    pass


class InsufficientHistoryError(ValueError):
    pass


def _normalize_team(name):
    if not isinstance(name, str):
        raise TeamNotFoundError(f"Team name must be a string, got {type(name)}")
    n = name.strip()
    if n.islower():
        n = n.title()
    n = NAME_FIXES.get(n, n)
    if n not in VALID_TEAMS:
        raise TeamNotFoundError(
            f"Unknown team '{name}'. Valid teams are: {', '.join(VALID_TEAMS)}")
    return n


def _parse_date(date):
    if isinstance(date, str):
        try:
            d = pd.Timestamp(date)
        except Exception:
            raise ValueError(f"Could not parse date '{date}'. Use format YYYY-MM-DD.")
    elif isinstance(date, (datetime, pd.Timestamp)):
        d = pd.Timestamp(date)
    else:
        raise ValueError(f"Date must be a string or datetime, got {type(date)}")
    if d < DATE_MIN:
        raise DateOutOfRangeError(
            f"Date {d.date()} is before the earliest match in the dataset ({DATE_MIN.date()}).")
    return d


def _signed_streak_from_series(win_series):
    """Same definition as training: +N = N straight wins coming in, -N = N straight losses."""
    cur, last = 0, None
    for v in win_series:
        cur = cur + 1 if (last is None or v == last) else 1
        last = v
    return cur if last == 1 else -cur


def _team_form_asof(team, asof_date, n=5):
    """
    Compute a team's rolling-form features using ONLY matches strictly before asof_date.
    Mirrors the shift(1)-then-roll definition used at training time, just evaluated live.
    """
    hist = _team_hist[(_team_hist['team'] == team) & (_team_hist['match_date'] < asof_date)]
    hist = hist.sort_values('match_date')
    if hist.empty:
        raise InsufficientHistoryError(
            f"No matches found for '{team}' before {asof_date.date()} — cannot compute form.")

    last_n = hist.tail(n)
    form_win_rate = last_n['win'].mean()
    form_avg_score = last_n['team_score'].mean()
    form_avg_margin = last_n['margin'].mean()
    win_streak = _signed_streak_from_series(hist['win'].tail(10).tolist())  # 10 is plenty to find the current streak
    days_rest = (asof_date - hist['match_date'].iloc[-1]).days

    # ladder position: rank this team's season-to-date points against every other team's
    # season-to-date points as of the same date. Documented approximation vs. the training-time
    # round-label ranking — for a genuinely future match there is no round label to align to yet.
    season = hist[hist['year'] == asof_date.year]
    team_points = season['points'].sum() if not season.empty else 0
    all_season = _team_hist[(_team_hist['year'] == asof_date.year) & (_team_hist['match_date'] < asof_date)]
    league_points = all_season.groupby('team')['points'].sum()
    if team not in league_points.index:
        league_points.loc[team] = team_points
    ladder_pos = float((league_points > team_points).sum() + 1)

    return {
        'form_win_rate_last5': form_win_rate, 'form_avg_score_last5': form_avg_score,
        'form_avg_margin_last5': form_avg_margin, 'win_streak': win_streak,
        'days_rest': days_rest, 'ladder_pos_before': ladder_pos,
    }


def _h2h_asof(team_a, team_b, asof_date):
    key = tuple(sorted([team_a, team_b]))
    hist = _team_hist[(_team_hist['team'] == team_a) & (_team_hist['opponent'] == team_b)
                       & (_team_hist['match_date'] < asof_date)]
    if hist.empty:
        return np.nan
    return hist['win'].mean()


TEAM_STATE = {
    'Hawthorn Hawks': 'VIC', 'Carlton Blues': 'VIC', 'Collingwood Magpies': 'VIC',
    'Essendon Bombers': 'VIC', 'Geelong Cats': 'VIC', 'Melbourne Demons': 'VIC',
    'North Melbourne Kangaroos': 'VIC', 'Richmond Tigers': 'VIC', 'St Kilda Saints': 'VIC',
    'Western Bulldogs': 'VIC', 'Fitzroy Lions': 'VIC',
    'West Coast Eagles': 'WA', 'Fremantle Dockers': 'WA',
    'Adelaide Crows': 'SA', 'Port Adelaide Power': 'SA',
    'Brisbane Lions': 'QLD', 'Brisbane Bears': 'QLD', 'Gold Coast Suns': 'QLD',
    'Sydney Swans': 'NSW', 'Greater Western Sydney Giants': 'NSW',
}


def build_match_features(home: str, away: str, d) -> tuple:
    """
    Build the exact feature row the match-winner model expects, for a home/away pair as of a
    given date. Returns (feature_dict, notes). Factored out of predict_match_winner so the
    explanation layer (explain.py) can build the same features without duplicating this logic.
    """
    notes = []
    home_form = _team_form_asof(home, d)
    away_form = _team_form_asof(away, d)
    h2h = _h2h_asof(home, away, d)
    away_state = TEAM_STATE.get(away)
    home_state = TEAM_STATE.get(home)
    away_is_interstate = int(away_state != home_state) if (away_state and home_state) else None
    if away_is_interstate is None:
        notes.append("Could not resolve interstate travel flag for one of these teams; defaulting to 0.")
        away_is_interstate = 0

    row = {
        'form_win_rate_last5_home': home_form['form_win_rate_last5'],
        'form_avg_score_last5_home': home_form['form_avg_score_last5'],
        'form_avg_margin_last5_home': home_form['form_avg_margin_last5'],
        'win_streak_home': home_form['win_streak'],
        'days_rest_home': home_form['days_rest'],
        'ladder_pos_before_home': home_form['ladder_pos_before'],
        'h2h_win_rate_prior_home': h2h,
        'form_win_rate_last5_away': away_form['form_win_rate_last5'],
        'form_avg_score_last5_away': away_form['form_avg_score_last5'],
        'form_avg_margin_last5_away': away_form['form_avg_margin_last5'],
        'win_streak_away': away_form['win_streak'],
        'days_rest_away': away_form['days_rest'],
        'ladder_pos_before_away': away_form['ladder_pos_before'],
        'h2h_win_rate_prior_away': 1 - h2h if not np.isnan(h2h) else np.nan,
        'away_is_interstate': away_is_interstate,
    }
    return row, notes


def predict_match_winner(team_a, team_b, date):
    """
    Predict the outcome of a hypothetical match between team_a (home) and team_b (away) on `date`.

    Parameters
    ----------
    team_a : str   Home team name (e.g. "Hawthorn Hawks"). Case/whitespace-tolerant.
    team_b : str   Away team name.
    date   : str or datetime   Match date, e.g. "2025-08-20". Must be after DATE_MIN; a date far
             past DATE_MAX is allowed (treated as "using data up to the end of the dataset").

    Returns
    -------
    dict: {
        'winner': 'HOME_WIN' | 'AWAY_WIN' | 'DRAW',
        'probabilities': {'HOME_WIN': float, 'AWAY_WIN': float, 'DRAW': float},
        'home_team': str, 'away_team': str, 'date': str,
        'notes': list[str]   # any caveats, e.g. limited history
    }

    Raises
    ------
    TeamNotFoundError, DateOutOfRangeError, InsufficientHistoryError
    """
    home = _normalize_team(team_a)
    away = _normalize_team(team_b)
    if home == away:
        raise ValueError("Home and away team must be different.")
    d = _parse_date(date)

    notes = []
    if d > DATE_MAX:
        notes.append(f"Date is after the last match in training data ({DATE_MAX.date()}); "
                      f"using each team's most recent known form as a stand-in for current form.")

    row, extra_notes = build_match_features(home, away, d)
    notes.extend(extra_notes)

    X = pd.DataFrame([row])[NUMERIC_MATCH_FEATURES]
    proba = _match_model.predict_proba(X)[0]
    proba_map = dict(zip(_match_model.classes_, proba))
    winner = max(proba_map, key=proba_map.get)

    return {
        'winner': winner,
        'probabilities': {k: round(float(v), 4) for k, v in proba_map.items()},
        'home_team': home, 'away_team': away, 'date': str(d.date()),
        'notes': notes,
        'feature_row': row,
    }


def predict_top_player(team, stat_type='fantasy_points', date=None, top_k=5):
    """
    Predict the top-k likely performers for `team`'s next match, ranked by predicted `stat_type`.

    Parameters
    ----------
    team      : str   Team name.
    stat_type : str   One of 'fantasy_points' (trained regression model), 'disposals', 'goals'
                       (rolling-average estimate — no dedicated regression model trained for
                       these in Day 2; see notebook Task 3 for why fantasy_points was prioritized).
    date      : str or datetime   Reference date; defaults to the latest date in the dataset.
    top_k     : int   Number of players to return.

    Returns
    -------
    list[dict]: [{'player_id': ..., 'player_name': ..., 'predicted_value': float}, ...]
                 sorted descending by predicted_value.

    Raises
    ------
    TeamNotFoundError, DateOutOfRangeError, InsufficientHistoryError
    """
    if stat_type not in ('fantasy_points', 'disposals', 'goals'):
        raise ValueError("stat_type must be one of 'fantasy_points', 'disposals', 'goals'")

    team_n = _normalize_team(team)
    d = _parse_date(date) if date is not None else DATE_MAX

    roster_hist = _player_hist[(_player_hist['team'] == team_n) & (_player_hist['match_date'] < d)]
    if roster_hist.empty:
        raise InsufficientHistoryError(f"No player history found for '{team_n}' before {d.date()}.")

    # roster proxy: players who appeared in this team's most recent match before `date`
    last_match_date = roster_hist['match_date'].max()
    roster = roster_hist[roster_hist['match_date'] == last_match_date]['player_id'].unique()

    team_form = _team_form_asof(team_n, d)

    rows = []
    for pid in roster:
        phist = roster_hist[roster_hist['player_id'] == pid].sort_values('match_date').tail(5)
        if phist.empty:
            continue
        rows.append({
            'player_id': pid,
            'player_avg_disposals_last5': phist['disposals'].mean(),
            'player_avg_goals_last5': phist['goals'].mean(),
            'player_avg_fantasy_points_last5': phist['fantasy_points'].mean(),
            'team_form': team_form['form_win_rate_last5'],
            'team_ladder': team_form['ladder_pos_before'],
            'is_home': 1,  # unknown at prediction time without a fixture; documented assumption
        })
    if not rows:
        raise InsufficientHistoryError(f"No usable player rows for '{team_n}' before {d.date()}.")

    roster_df = pd.DataFrame(rows)

    if stat_type == 'fantasy_points':
        X = roster_df[['player_avg_disposals_last5', 'player_avg_goals_last5',
                        'player_avg_fantasy_points_last5', 'team_form', 'team_ladder', 'is_home']]
        roster_df['predicted_value'] = _player_model.predict(X)
    else:
        col = f'player_avg_{stat_type}_last5'
        roster_df['predicted_value'] = roster_df[col]

    roster_df = roster_df.merge(_players_lookup, left_on='player_id', right_on='id', how='left')
    roster_df = roster_df.sort_values('predicted_value', ascending=False).head(top_k)

    return [
        {'player_id': r['player_id'], 'player_name': r.get('player_name', 'Unknown'),
         'predicted_value': round(float(r['predicted_value']), 2)}
        for _, r in roster_df.iterrows()
    ]


if __name__ == '__main__':
    # smoke test
    print(predict_match_winner('Hawthorn Hawks', 'Carlton Blues', '2025-08-20'))
    print(predict_top_player('Hawthorn Hawks', stat_type='fantasy_points', date='2025-08-20'))
