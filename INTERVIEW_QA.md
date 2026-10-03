# Interview / Viva Q&A — Student Performance & Attendance Analysis

Short, confident answers. Numbers refer to this repo's data (they recompute if you use the full Kaggle file).

1. **Why this project?** Colleges record attendance and marks separately. I joined them to answer: who is slipping, in which subject, and which habit/preparation factor is actually associated with marks — so support can be targeted, not generic.
2. **Why Pandas?** Single tool for load → inspect → clean → groupby → reshape. `groupby`, `cut`, `isnull`, `describe` cover 90% of analyst EDA faster than SQL+Excel round-trips.
3. **Why NumPy?** Vectorised math under Pandas (means, clipping, correlations) plus controlled synthetic-data generation with a seeded RNG for reproducibility.
4. **Why Matplotlib + Seaborn?** Matplotlib for control (titles/labels/savefig), Seaborn for statistical plots in one line (`histplot`, `regplot`, `boxplot`, `heatmap`). No need for Plotly here — static PNGs are portfolio/GitHub-friendly.
5. **Dataset?** Kaggle Student Performance Factors (Attendance, Study Hours, Previous Scores, Test Prep, Final Score) + fallback to classic StudentsPerformance (math/reading/writing). Repo ships a 1,000-row file with the same schema; loader auto-maps either.
6. **Missing values?** Numeric → median (robust to skew), categorical → mode. Preserves N; mean would be pulled by extremes. Documented per column with before/after counts.
7. **Duplicates?** `df.duplicated().sum()` → 10 found → `drop_duplicates`. Same student twice would inflate N and bias means.
8. **Inconsistent text?** Stripped whitespace, normalised case (`male`/`FEMALE` → Male/Female; ` completed` → Completed), coerced unknowns to NaN then mode-filled. Otherwise group-bys create phantom categories.
9. **Invalid values?** Attendance outside 0–100 and Study_Hours <0/>24 → NaN → median. Impossible values would corrupt means and correlations.
10. **Outliers?** IQR bounds reported per numeric column; kept all (a real 95 or 42 is signal). Deleting without domain reason destroys information.
11. **What is correlation?** Pearson r in [-1, +1]: direction + strength of linear co-movement. Ours: attendance–final 0.34 (modest-moderate), study–final 0.27, previous–final 0.71 (strong).
12. **Does correlation imply causation?** No. Attendance coincides with marks but motivation/prior ability confound it. I state association + show regression as descriptive, and recommend tracking/intervention rather than claiming cause.
13. **What did you find on attendance?** Mean 75.2%; High (>80%) averages 6.9 points above Low (<60%); r=0.34. Justifies using <60% as an early-alert trigger, not proof attending harder causes +6.9.
14. **Study hours finding?** Intensive (>8h) +6.0 over Light (<4h), r=0.27; study↔attendance r≈0, so they are independent levers.
15. **Most important insight?** Previous_Score (r=0.71) dominates; test-prep gap (+5.3, p<0.0001) is the most actionable lever; regression R²=0.67 for the three inputs together.
16. **Why these visualisations?** Each answers one question: hist = shape/centre, count = grade mix, scatter+reg = relationship strength, box = spread by group, bar = means compared, heatmap = all pairwise r at once. No chart without a question.
17. **Thresholds justification?** Attendance bands from the common 75% college minimum (<60 at-risk, 60–80 borderline, >80 safe); study bands as light/typical/intensive; segments aligned to grade cutoffs (55 = C floor, 75 = strong-B). All stated in the notebook.
18. **Statistical tests?** Welch t-test for test-prep means (t=11.1, p<0.0001 → gap unlikely by luck) + multiple regression for joint explanatory power (R²=0.67, per-unit coefficients reported as descriptive).
19. **Challenges?** (a) The string 'None' being auto-parsed as NaN by read_csv — fixed with keep_default_na=False + explicit na_values and canonical 'Not Completed' label; (b) manual notebook JSON escaping — fixed by building the .ipynb programmatically; (c) %-format vs literal % — fixed with pct wording/%% escapes. All verified by headless execution of all 15 code cells.
20. **How would a college use this?** Fortnightly list: Attendance<60 AND Previous<60 (or Needs Attention segment) → counsellor call; prep classes for that list; tutor lowest-mean subject; re-run each term and track migrations between bands as the KPI.
21. **How would you improve it?** Add term trends, socio-economic controls, a calibrated flag model (precision/recall), and a Streamlit dashboard + intervention A/B tracking.
