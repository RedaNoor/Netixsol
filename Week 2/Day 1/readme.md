# AFL Player Statistics Data Cleaning and Observation Report

## Project Overview

This project focuses on cleaning, validating, and analyzing Australian Football League (AFL) player statistics using Python and Pandas. The objective is to transform raw datasets into a clean, consistent, and analysis-ready dataset while documenting the data quality observations and key findings.

The project demonstrates a complete data preprocessing workflow including data cleaning, merging datasets, handling missing values, removing duplicates, and validating the final dataset before analysis.

---

## Project Objectives

- Clean and preprocess raw AFL datasets.
- Standardize inconsistent values.
- Handle missing and invalid data.
- Merge player information with seasonal statistics.
- Validate data quality after cleaning.
- Produce an observation report summarizing the dataset.

---

## Project Structure

```
AFL-Data-Cleaning/
│
├── players_info.csv                 # Player information dataset
├── seasonal_stats.csv               # Seasonal player statistics
├── merged_players.csv               # Final cleaned merged dataset
│
├── AFL_Data_Cleaning.ipynb          # Data cleaning notebook
├── Observations_Report.ipynb        # Observation and data quality report
│
└── README.md
```
---

## Dataset Description

### 1. Player Information Dataset

Contains player demographic information such as:

- Player ID
- Name
- Date of Birth
- Height
- Weight
- Playing Position

### 2. Seasonal Statistics Dataset

Contains season-wise player performance including:

- Games Played
- Goals
- Behinds
- Kicks
- Handballs
- Marks
- Tackles
- Hit Outs
- Clearances
- Contested Possessions
- Team
- Season

---

## Data Cleaning Process

The following preprocessing steps were performed:

### Missing Values

- Identified missing values.
- Filled historical statistical fields with appropriate defaults where necessary.
- Preserved missing demographic information that could not be recovered.

### Duplicate Records

- Detected duplicate player-season records.
- Removed duplicates to prevent inflated career statistics.

### Team Name Standardization

Standardized inconsistent team names by:

- Removing leading/trailing spaces
- Correcting capitalization
- Consolidating naming variations

### Data Type Validation

Verified and corrected data types for:

- Numeric columns
- Date columns
- Text columns

### Dataset Merge

Merged player information with seasonal statistics using the Player ID field.

### Data Validation

Performed validation checks after cleaning to ensure:

- No unintended duplicate records
- Consistent team names
- Correct merge results
- Reliable player statistics

---

## Observation Report

The observation report summarizes the quality of the cleaned dataset and highlights important findings, including:

- Historical data coverage
- Player games and scoring trends
- Team standardization
- Missing player information
- Overall data quality assessment

---

## Key Findings

- Historical AFL datasets naturally contain missing advanced statistics because these metrics were not officially recorded during earlier seasons.
- Duplicate player-season records were successfully removed.
- Team names were standardized into official AFL club names.
- A small number of players appearing in seasonal statistics do not have matching demographic records.
- The final dataset is suitable for further exploratory data analysis and visualization.

---

## Technologies Used

- Python
- Pandas
- NumPy
- Jupyter Notebook

---

## Skills Demonstrated

- Data Cleaning
- Data Wrangling
- Data Validation
- Data Merging
- Missing Value Handling
- Duplicate Detection
- Data Quality Assessment
- Exploratory Data Analysis (EDA)

---

## How to Run

1. Clone this repository.

```bash
git clone <repository-url>
```

2. Install dependencies.

```bash
pip install pandas numpy jupyter
```

3. Open Jupyter Notebook.

```bash
jupyter notebook
```

4. Run:

- `AFL_Data_Cleaning.ipynb`
- `Observations_Report.ipynb`

---

## Future Improvements

- Add exploratory data visualization using Matplotlib and Seaborn.
- Build interactive dashboards using Plotly or Power BI.
- Perform statistical analysis on player performance.
- Develop predictive models for player performance using machine learning.

---

## License

This project is intended for educational and portfolio purposes.
