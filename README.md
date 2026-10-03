# EduMetrics — Student Performance Analytics (Flask Web App)

A real-world data analytics **web application** for colleges: upload any student CSV at runtime →
automatic cleaning → KPIs → interactive Plotly dashboard → auto-generated insights → downloadable report.

**Stack:** Python · Flask · Pandas · NumPy · Plotly · HTML · CSS · Vanilla JS (no React/Django/Streamlit).

## Run it

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

| Page | URL | What it does |
|---|---|---|
| Landing | `/` | Hero + Upload CSV / View Demo |
| Upload | `/upload` | Drag-and-drop CSV, validation, loading state |
| Dashboard | `/dashboard` | KPIs, charts, segments, insights, data quality |
| About | `/about` | Stack, column support, 60-sec interview pitch |

**Try without a file:** click `View Demo` (uses `data/StudentPerformanceFactors.csv`)
or upload `data/sample_students.csv`.

## CSV upload — flexible columns

Headers are normalised (case-insensitive, `_`/`-`/spaces ignored) and mapped, e.g.:

- Attendance ← `Attendance`, `attendance_percentage`, `attendance %`, …
- Score ← `Final Score`, `Marks`, `Total Marks`, `Score`, …
- Study Hours ← `Study Hours`, `hours studied`, …
- Plus Gender, Age, Previous Score, Grade, Test Preparation, Parental Education,
  and subjects by keyword (Math, Science, English, Reading, Writing, Computer Science, …).

Missing concept ⇒ that KPI/chart is hidden. **Missing data is never fabricated.**
If `Final Score` is absent but subject columns exist, it is derived as their mean.

## What the app computes

- **Cleaning:** drops empty rows, coerces numerics, invalid→NaN (attendance 0–100, scores 0–100/0–10 auto-scale),
  median/mode imputation, duplicate removal, IQR outlier report, derived score/grade.
- **Analytics:** mean/median/min/max/SD, pass % (≥40, or ≥4.0 on GPA scale),
  attendance bands, subject means, gender/test-prep/parental groups, Pearson correlations,
  segmentation (High ≥75 / Average 50–74 / Needs Attention <50, auto-scaled for GPA).
- **Insights:** every sentence computed from the upload (band gaps, prep gap, strongest predictor, …);
  correlation is always described as association, never causation.
- **Report:** `Download Analysis Report` → styled HTML with KPIs, insights, recommendations.

## Structure

```
├── app.py                  # Flask routes, upload handling, report export
├── analysis/
│   ├── data_cleaning.py    # find_column(), detect_columns(), clean_dataframe()
│   ├── analytics.py        # compute_dashboard() — KPIs, stats, chart payloads
│   └── insights.py         # generate_insights(), generate_recommendations()
├── templates/              # index, upload, dashboard, about
├── static/css/style.css    # EduMetrics theme (blue primary, red accent)
├── static/js/dashboard.js  # fetches JSON, renders Plotly charts
├── data/                   # StudentPerformanceFactors.csv + sample_students.csv
├── uploads/  reports/
```

## Interview line

> "Users upload any student CSV. I normalise headers to canonical fields, clean with
> median/mode imputation, compute KPIs/correlations/segments in Pandas, serve JSON from
> Flask, render responsive Plotly charts, and generate insights plus an HTML report —
> all dynamic, nothing hardcoded."
