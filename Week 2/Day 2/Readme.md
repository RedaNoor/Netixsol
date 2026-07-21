# AFL Data Visualization Fundamentals

Week 2 · Data Visualization Fundamentals (Matplotlib)

## Overview

This notebook builds the 6 core chart types that cover most real-world exploratory data analysis (EDA) needs — line, bar, histogram, boxplot, scatter, and heatmap — using the cleaned and merged AFL players dataset. Each chart is paired with a plain-English caption explaining what the visual actually tells us about AFL players and the game.

## Files

| File | Description |
|---|---|
| `AFL_Data_Visualization_Fundamentals.ipynb` | Main deliverable — 6 labeled charts, captions, and concept-check answers |
| `merged_players.csv` | Cleaned, fully-merged dataset used for all charts (25,081 rows, 70 columns, 0 missing values) |
| `players_info.csv` | Cleaned player demographics dataset |
| `seasonal_stats.csv` | Cleaned player season-by-season stats dataset |
| `Afl_data_cleaning.ipynb` | Upstream notebook that produced the 3 cleaned CSVs above |

## Data Source

`merged_players.csv` is the output of `Afl_data_cleaning.ipynb`, which:
- Removed duplicate records from both raw source files
- Fixed invalid `player_id` formats and `games_played` sign errors
- Standardized `team` name casing
- Imputed invalid `weight = 0` values with the dataset median
- Filled missing numeric stats (e.g. goals, kicks) with 0, since a blank stat means the action didn't occur
- Used an **inner join** to merge stats with demographics, so every row has complete information, no missing values anywhere in the final dataset

Dataset covers **1983–2025**.

## Requirements

```
pandas
numpy
matplotlib
seaborn
```

Install if needed:
```bash
pip install pandas numpy matplotlib seaborn
```

## How to Run

1. Keep `merged_players.csv` in the same folder as the notebook (the notebook loads it with a relative path).
2. Open `AFL_Data_Visualization_Fundamentals.ipynb` in Jupyter.
3. Run all cells top to bottom — charts are already rendered inline, but re-running regenerates them from the CSV.

## Chart Summary

| # | Chart | Best for | Key insight |
|---|---|---|---|
| 1 | Line | Trends over time | Average disposals per game nearly doubled, 1983 → 2025 |
| 2 | Bar | Comparing categories | Scoring is fairly even across current-era teams; expansion clubs lag behind |
| 3 | Histogram | Distribution of one variable | Player height is roughly normal, centered near 187 cm |
| 4 | Boxplot | Comparing distributions across groups | Median individual scoring has declined every decade as squads rotate more players |
| 5 | Scatter | Relationship between two variables | Height and weight are strongly correlated (r = 0.81) |
| 6 | Heatmap | Many correlations at once | Disposal-related stats move together; hit-outs stand apart as a ruck-specific skill |
