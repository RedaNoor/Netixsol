"""
LangChain tool registrations for the structured query functions in tools.py, plus the
semantic search tool over the derived match-description corpus in knowledge_base.py.
"""
from typing import Optional
from langchain_core.tools import tool

import tools as t
import knowledge_base as kb

import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_MODEL = "openai/gpt-4o-mini"
GROQ_MODEL = "openai/gpt-oss-120b"

def build_llm():
    primary = ChatOpenAI(
        model=OPENROUTER_MODEL,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        temperature=0,
    )
    fallback = ChatOpenAI(
        model=GROQ_MODEL,
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
        temperature=0,
    )
    return primary.with_fallbacks([fallback])


@tool
def team_head_to_head(team_a: str, team_b: str) -> dict:
    """Get the all-time head-to-head record between two AFL teams, including total wins for
    each side, draws, and their last 5 meetings with scores and dates. Use this for any
    question about how two teams have historically matched up against each other."""
    return t.get_team_head_to_head(team_a, team_b)


@tool
def player_season_stats(player_name: str, year: int, team: Optional[str] = None, include_finals: bool = False) -> dict:
    """Get a player's aggregated stats for a single AFL season: games played, total and
    average disposals, total and average goals, average fantasy points, and Brownlow votes.
    Defaults to home-and-away season only; set include_finals=True to fold finals in. Use this
    for questions like 'how did X perform in the 2022 season'. If the player name is ambiguous,
    pass the team to disambiguate."""
    return t.get_player_season_stats(player_name, year, team=team, include_finals=include_finals)


@tool
def player_finals_stats(player_name: str, year: int, team: Optional[str] = None) -> dict:
    """Get a player's stats across finals games only (Elimination/Qualifying/Semi/Preliminary/
    Grand Final) for a given season. Use this specifically for finals-form questions, kept
    separate from the regular season since finals performance is often discussed on its own."""
    return t.get_player_finals_stats(player_name, year, team=team)


@tool
def player_recent_games(player_name: str, n: int = 1, team: Optional[str] = None) -> dict:
    """Get a player's most recent N games (most recent first) with full per-game stats:
    disposals, goals, fantasy points, opponent, and result. Use this for 'last round',
    'last game', or 'last N games' style questions."""
    return t.get_player_recent_games(player_name, n=n, team=team)


@tool
def player_career_stats(player_name: str, team: Optional[str] = None) -> dict:
    """Get a player's career totals and per-game averages across every season in the dataset:
    career games, career average disposals/goals/fantasy points, career goal total, and
    career Brownlow votes. Use this for 'career average' comparison questions."""
    return t.get_player_career_stats(player_name, team=team)


@tool
def player_bio(player_name: str, team: Optional[str] = None) -> dict:
    """Get a player's biographical details: full name, birth date, height, weight, debut date,
    last played date, and every AFL team they've played for. Use this for non-stat questions
    like 'how tall is X', 'when did X debut', or 'which teams has X played for' — not for
    performance stats, use the other player tools for those."""
    return t.get_player_bio(player_name, team=team)


@tool
def team_season_record(team: str, year: int) -> dict:
    """Get a team's win/loss/draw record for a given season, including points scored,
    points conceded, and percentage. Use this for ladder/season-record questions."""
    return t.get_team_season_record(team, year)


@tool
def match_score_breakdown(team_a: str, team_b: str, year: Optional[int] = None, round: Optional[str] = None) -> dict:
    """Get the quarter-by-quarter running score and goals/behinds breakdown for a specific
    match between two teams. Use this for in-match detail questions like 'what was the
    quarter-time score', 'how many goals vs behinds did they kick', or 'how did the game
    unfold'. If year/round aren't given, returns the most recent meeting between the two teams
    and notes if there were other meetings to choose from instead."""
    return t.get_match_score_breakdown(team_a, team_b, year=year, round=round)


@tool
def round_matches(year: int, round: str) -> list:
    """Get all matches played in a given year and round, with final scores, winners, and
    venue. round can be a regular round number as a string ('1', '12') or a finals code:
    'EF', 'QF', 'SF', 'PF', 'GF' (Grand Final). Use this for 'who won the year Grand Final',
    'what happened in round N of year', or any specific-round result question."""
    return t.get_round_matches(year, round)


@tool
def season_leaderboard(year: int, stat: str = "fantasy_points", team: Optional[str] = None,
                        top_n: int = 10, mode: str = "total", min_games: int = 5,
                        include_finals: bool = False) -> list:
    """Get the top N players for a season ranked by a stat. stat is one of 'disposals',
    'goals', 'fantasy_points', 'brownlow_votes', or 'wins'. mode is 'total' (season sum —
    the usual meaning of 'leading goalkicker'/'most disposals') or 'average' (per-game, only
    for players with at least min_games games). Pass team to restrict to one club. Use this
    for any 'top N players', 'who led the league in X', or 'best player by X' question — do
    NOT try to answer these from memory, always call this tool."""
    return t.get_season_leaderboard(year, stat=stat, team=team, top_n=top_n, mode=mode,
                                     min_games=min_games, include_finals=include_finals)


@tool
def team_roster(team: str, year: Optional[int] = None) -> dict:
    """Get every player who played at least one game for a team in a season, sorted by games
    played, with the total roster size. If year isn't given, uses the most recent season in
    the dataset. Use this for 'who plays for X', 'list the players on X', or roster questions."""
    return t.get_team_roster(team, year=year)


@tool
def search_match_history(query: str, k: int = 5) -> list:
    """Semantic search over AFL match descriptions for narrative or exploratory questions
    that don't map to a single exact lookup — e.g. 'find close finishes between these two
    teams' or 'matches with a big comeback'. Do NOT use this for exact stat questions; use
    the structured tools above for anything involving a specific number."""
    return kb.search_match_descriptions(query, k=k)


ALL_TOOLS = [
    team_head_to_head,
    player_season_stats,
    player_finals_stats,
    player_recent_games,
    player_career_stats,
    player_bio,
    team_season_record,
    match_score_breakdown,
    round_matches,
    season_leaderboard,
    team_roster,
    search_match_history,
]
