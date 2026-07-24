# AFL Match Context Integration 

## Overview
This notebook enriches the AFL round-by-round player performance dataset with match context — **home/away status, venue, and crowd attendance** — by merging it with a separate team matches dataset. It then uses that enriched data to test whether match conditions actually influence player performance.

## Data
| File | Description |
|---|---|
| `afl_players_round_by_round_stats_raw.csv` | Raw match-by-match player statistics (one row per player per match) |
| `team_matches_home_away_raw.csv` | Raw team-level match data — home/away status, venue, crowd (one row per team per match) |

Both files are cleaned inside this notebook; neither is assumed pre-cleaned.

## Data Cleaning Summary
**Round-by-round dataset** (same treatment as the Day 4 notebook):
- Removed duplicate rows, dropped the empty `score` column
- Recalculated `disposals` as `kicks + handballs` where both were present, fixing invalid/negative values
- Filled missing counting stats with 0; imputed `percentage_of_game_played` per-player, then league-wide as a fallback
- Parsed `round` into a sortable `round_number`, mapping finals codes (EF/QF/SF/PF/GF)
- Excluded pre-season trial matches

**Team matches dataset:**
- Fixed inconsistent whitespace/tab characters in `team_name` and `opponent`
- Standardized `"W. Bulldogs"` → `"Western Bulldogs"` to match the round-by-round dataset
- Fixed inconsistent casing in `opponent` (e.g. `"richmond tigers"` → `"Richmond Tigers"`)
- Removed trailing newline characters from `venue`, which had been splitting single venues into duplicate categories
- Left `crowd` missing values as `NaN` (398 matches, concentrated around the COVID-affected 2020/2021 seasons) rather than guessing a figure

## Merge Strategy
- **Relationship Discovery:** no single column (`match_date`, `round`, or `team_name`) is unique on its own. `team_name + year + round` was tested first but failed with 6 duplicate combinations, traced to drawn finals being replayed and a rescheduled fixture landing in the same round as another match.
- **Final merge key:** `team_name + match_date` (matches side) → `team + match_date` (round-by-round side) — confirmed unique with zero duplicate combinations.
- **Join type:** left merge, keeping every player-match row regardless of whether context was found, with `indicator=True` used to make validation straightforward.

## Merge Validation
- Row count unchanged before vs. after merge (273,803 → 273,803)
- Zero unmatched player rows
- Zero duplicate rows introduced by the merge
- `home_away` and `venue` have no missing values post-merge; `crowd` carries forward its original ~8,955 missing player-rows (from the 398 missing matches)

## Key Findings
- **Home vs. away:** players average ~66.5 fantasy points at home vs. ~64.0 away — a modest but consistent ~2.5-point home advantage
- **Crowd size:** correlation with fantasy points is 0.0129 — effectively no relationship
- **Venue:** a real spread exists among venues with sufficient sample size (≥1,000 player-rows) — UTAS Stadium, ENGIE Stadium, and Marvel Stadium rank highest (~67–68 avg); Princes Park, WACA, and Waverley Park rank lowest (~58–59 avg)

Full reasoning, code walkthroughs, and charts for each finding are in the notebook itself.

## Notebook Structure
1. Data Loading
2. Round-by-Round Cleaning (recap from Day 4)
3. Team Matches — Initial Data Quality Assessment
4. Task 1 — Relationship Discovery (merge key investigation)
5. Cleaning the Team Matches Dataset
6. Task 2 — Context Enrichment (the merge itself + spot-check validation)
7. Task 3 — Merge Validation
8. Task 4 — Contextual Analysis (home/away, crowd, venue)
9. Task 5 — Data Quality Report
10. Summary: Business Insights

## Requirements
```
pandas
numpy
matplotlib
seaborn
```

## How to Run
1. Place `afl_players_round_by_round_stats_raw.csv` and `team_matches_home_away_raw.csv` in the same directory as the notebook
2. Run all cells top to bottom
3. Charts are saved to `day5_charts/` as they're generated
