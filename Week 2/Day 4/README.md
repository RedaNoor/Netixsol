# AFL Player Performance Investigation — Week 2, Day 4

## Overview
This notebook analyzes AFL player and team performance using round-by-round match statistics to identify the most valuable players, the most consistent performers, in-season form trends, team-level strength, and a final shortlist of 5 recruitment recommendations for the upcoming season.

## Data
| File | Description |
|---|---|
| `players_info.csv` | Cleaned player demographics (id, name, height, weight, last age) — output of the Day 2 cleaning notebook |
| `afl_players_round_by_round_stats_raw.csv` | Raw match-by-match player statistics (disposals, goals, tackles, fantasy points, etc.) |

The round-by-round file is cleaned inside this notebook (see Section 0) since it wasn't cleaned in the earlier data-prep stage.

## Data Cleaning Summary
- Removed 10 exact duplicate rows
- Dropped the `score` column (100% missing)
- Recalculated `disposals` as `kicks + handballs` wherever both were present, fixing all negative/invalid values
- Filled missing counting stats (goals, tackles, hit-outs, etc.) with 0 — a blank stat means the action didn't occur
- Imputed missing `percentage_of_game_played` using each player's own median, falling back to the competition median
- Parsed the `round` column into a sortable `round_number`, mapping finals codes (EF, QF, SF, PF, GF) after round 24
- Flagged and excluded 276 pre-season trial matches (`round == '0'`) from performance analysis

All analysis is scoped to the **2025 home-and-away season** (the most recently completed full season), with a minimum games-played threshold applied per task to avoid small-sample distortion.

## Notebook Structure
1. **Data Preparation & Quality Checks** — load, clean, and merge the datasets
2. **Task 5 — Feature Engineering** *(moved here since Tasks 1 & 2 depend on these columns)*
   - `goals_per_game`, `fantasy_per_game`, `disposal_efficiency`, `contested_ball_rate`, `score_involvement_per_game`, `consistency_score`
3. **Task 1 — Top 10 Most Valuable Players**: weighted composite (z-scored) of avg disposals (20%), goals (20%), tackles (15%), contested possessions (15%), and fantasy points (30%)
4. **Task 2 — Most Consistent Players**: ranked by coefficient of variation (CV) of round-by-round fantasy points, min. 40 avg fantasy points
5. **Task 3 — Performance Trends**: first-half vs. second-half (2025) average fantasy points, min. 5 games in each half
6. **Task 4 — Team Performance Analysis**: teams ranked by average fantasy points across qualified players
7. **Supporting visualizations**: value vs. consistency scatter, feature correlation heatmap
8. **Task 6 — Final Recommendations**: blended recruit score — 40% performance, 25% consistency, 20% trend, 15% youth

## Key Findings
- Matt Rowell (Gold Coast Suns) leads the Performance Index, driven by elite disposals, tackles, and contested ball
- Tom McCarthy is the most consistent qualifying player (CV 0.12)
- Lachlan Cowan is the season's biggest improver (+37.7 fantasy points/game, first half to second)
- Geelong Cats rank #1 for average player output; West Coast Eagles rank last, roughly 18% behind
- **Final 5 recruitment recommendations**: Matt Rowell, Harry Sheezel, Finn Callaghan, Nasiah Wanganeen-Milera, Josh Dunkley

Full reasoning and supporting visualizations for each finding are in the notebook itself.

## Requirements
```
pandas
numpy
matplotlib
seaborn
```
