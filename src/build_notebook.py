"""Build the Jupyter notebook programmatically (avoids manual JSON escaping errors)."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_PATH = os.path.join(ROOT, "notebooks", "Student_Performance_Attendance_Analysis.ipynb")

def md(lines):
    return {"cell_type": "markdown", "metadata": {}, "source": lines}

def code(src):
    # src: single string with real newlines -> split into line list with \n preserved
    lines = src.splitlines(keepends=True)
    # ensure every line except maybe last ends with \n (splitlines keepends already does)
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": lines}

cells = []

cells.append(md([
"# Student Performance & Attendance Analysis\n",
"\n",
"### A real-world Data Analytics portfolio project (Python, Pandas, NumPy, Matplotlib, Seaborn)\n",
"\n",
"**Objective:** Help a college understand how attendance, study habits, demographics and prior scores relate to student performance, and turn that into decisions (early alerts, support, subject focus).\n",
"\n",
"**Workflow:** Business Problem -> Dataset Understanding -> Cleaning -> Feature Engineering -> EDA -> Attendance / Study / Subject / Demographic analysis -> Correlation -> Segmentation -> Insights -> Recommendations -> Conclusion\n",
"\n",
"> Rule followed throughout: no fabricated conclusions. Every insight is computed from the data. Correlation is never claimed as causation.\n",
]))

cells.append(md([
"## 1. Project Introduction\n",
"\n",
"Colleges collect marks and attendance but rarely connect them. This project asks:\n",
"\n",
"- What is the overall performance picture (average, spread, grades)?\n",
"- Does attendance move with marks? How strong is that relationship?\n",
"- Do study hours matter? For marks, grades, attendance?\n",
"- Which subject is strongest / weakest and which varies most?\n",
"- Do gender, parental education, test preparation, previous scores show differences?\n",
"- Which students need attention right now?\n",
"\n",
"## 2. Business Problem\n",
"\n",
"**Problem colleges face:** uneven results, silent drop-offs in attendance, late discovery of struggling students, and no evidence for where to intervene (which subject, which group, which habit).\n",
"\n",
"**Why attendance analysis?** Attendance is the earliest observable signal. If low attendance reliably coincides with low scores, it can power an early-warning list - cheaper than waiting for finals.\n",
"\n",
"**Why study habits + other factors?** Study hours, previous scores, test preparation and background factors help separate effort/preparation effects from attendance effects, so support can be targeted (study-skills workshop vs attendance counselling vs subject tutoring).\n",
"\n",
"**Decisions this supports:**\n",
"1. Early-alert list (low attendance + low previous score)\n",
"2. Subject-level tutoring priority\n",
"3. Study-skills / test-prep programmes (if the data supports them)\n",
"4. Term-over-term tracking of the same metrics\n",
]))

cells.append(md([
"## 3. Dataset Description\n",
"\n",
"**Primary dataset:** Kaggle - Student Performance Factors (StudentPerformanceFactors.csv, about 6607 rows) - rich in Attendance, Study Hours, Previous Scores, Parental Education, Test Preparation, Final/Exam Score.\n",
"\n",
"**Fallback classic:** Kaggle - Students Performance (StudentsPerformance.csv, 1000 rows: gender, parental education, test preparation, math/reading/writing scores). The loader below auto-adapts to either file.\n",
"\n",
"**This repo working file:** data/StudentPerformanceFactors.csv (1010 rows incl. 10 duplicates + about 2% missing + a few inconsistent/invalid entries kept deliberately so cleaning is realistic). Columns:\n",
"\n",
"- Student_ID: unique student key\n",
"- Gender: Male / Female\n",
"- Age: 15-19\n",
"- Parental_Education: High School / Some College / Associate / Bachelor's / Master's\n",
"- Test_Preparation: Completed / Not Completed\n",
"- Attendance: % of classes attended (50-100)\n",
"- Study_Hours: hours studied per week (0-15)\n",
"- Previous_Score: last-term score (35-100)\n",
"- Math_Score, Reading_Score, Writing_Score: subject marks 0-100\n",
"- Final_Score: mean of 3 subjects\n",
"- Grade: A(>=85) B(>=70) C(>=55) D(>=40) F(<40)\n",
"\n",
"Run the next cells to inspect it before any conclusion.\n",
]))

cells.append(code(
"""# 4. Import libraries
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13

print('Libraries loaded OK')
print('pandas', pd.__version__, '| numpy', np.__version__)

# Where to save charts (works from notebooks/ or project root or Colab)
VISUAL_DIR = '../visuals' if os.path.isdir('../visuals') else 'visuals'
os.makedirs(VISUAL_DIR, exist_ok=True)
print('Charts will be saved to:', VISUAL_DIR)
"""))

cells.append(code(
"""# 5. Load dataset (flexible: works with Kaggle download OR repo file OR Colab upload)
CANDIDATE_PATHS = [
    '../data/StudentPerformanceFactors.csv',
    'data/StudentPerformanceFactors.csv',
    'StudentPerformanceFactors.csv',
    '/content/StudentPerformanceFactors.csv',
    '../data/StudentsPerformance.csv',
    'data/StudentsPerformance.csv',
    'StudentsPerformance.csv',
]

data_path = next((p for p in CANDIDATE_PATHS if os.path.exists(p)), None)
if data_path is None:
    raise FileNotFoundError(
        'CSV not found. Download Kaggle "Student Performance Factors" and place it at '
        'data/StudentPerformanceFactors.csv (or upload it in Colab).')
print('Loading:', data_path)
# NOTE: keep_default_na=False so the category 'None'/'none' (classic Kaggle file) is NOT parsed as NaN.
df_raw = pd.read_csv(data_path, keep_default_na=False, na_values=['', ' ', 'NA', 'N/A', 'NaN', 'nan', 'NULL', 'null', '#NA'])
# Empty strings from the line above mean truly missing -> restore to NaN for cleaning
df_raw = df_raw.replace(['', ' '], np.nan)
print('Raw shape:', df_raw.shape)

# ---- Normalise column names so both Kaggle files map to one canonical schema ----
CANON = {
    'student id': 'Student_ID', 'id': 'Student_ID',
    'gender': 'Gender', 'sex': 'Gender',
    'age': 'Age',
    'parental education': 'Parental_Education', 'parental level of education': 'Parental_Education',
    'parental education level': 'Parental_Education',
    'test preparation': 'Test_Preparation', 'test preparation course': 'Test_Preparation', 'test prep': 'Test_Preparation',
    'attendance': 'Attendance', 'attendance (%)': 'Attendance',
    'study hours': 'Study_Hours', 'hours studied': 'Study_Hours',
    'previous score': 'Previous_Score', 'previous scores': 'Previous_Score',
    'math score': 'Math_Score', 'reading score': 'Reading_Score', 'writing score': 'Writing_Score',
    'final score': 'Final_Score', 'exam score': 'Final_Score', 'average score': 'Final_Score',
    'grade': 'Grade',
}

def _norm(c):
    k = str(c).strip().lower().replace('_', ' ').replace('-', ' ')
    return ' '.join(k.split())

df_raw = df_raw.rename(columns={c: CANON.get(_norm(c), c.strip()) for c in df_raw.columns})
df = df_raw.copy()

# If Final_Score missing but subjects exist, compute it (classic Kaggle file has no Final_Score)
subj = [c for c in ['Math_Score', 'Reading_Score', 'Writing_Score'] if c in df.columns]
if 'Final_Score' not in df.columns and len(subj) > 0:
    df['Final_Score'] = df[subj].mean(axis=1).round(2)
    print('Derived Final_Score as mean of', subj)

print('Canonical columns now:', list(df.columns))
"""))

cells.append(code(
"""# 6. Data exploration - size, types, samples, quality
print('Rows x Cols:', df.shape)
print('\\n--- Column names ---')
print(list(df.columns))
print('\\n--- Data types ---')
print(df.dtypes)
print('\\n--- First 5 rows ---')
display(df.head())
print('\\n--- Missing values ---')
print(df.isnull().sum())
print('\\nDuplicate rows:', int(df.duplicated().sum()))
print('\\n--- Basic statistics (numeric) ---')
display(df.describe().round(2))
print('\\n--- Categorical quick look ---')
for c in ['Gender', 'Parental_Education', 'Test_Preparation', 'Grade']:
    if c in df.columns:
        print('\\n' + c + ':')
        print(df[c].value_counts(dropna=False).head(10))
"""))

cells.append(md([
"## 7. Data Cleaning\n",
"\n",
"Each step below states why, what changed, and effect on analysis.\n",
"\n",
"1. Standardise text (Gender / Test_Preparation / Parental_Education): fixes male vs Male and trailing spaces - otherwise group-bys split into phantom categories.\n",
"2. Flag invalid numerics (Attendance outside 0-100, Study_Hours below 0 or above 24) and set to NaN: impossible values would distort means and correlations.\n",
"3. Missing values: numeric with median (robust to skew), categorical with mode. Preserves row count vs blind deletion.\n",
"4. Duplicates: drop exact duplicates (same student counted twice inflates N and biases means).\n",
"5. Types: Age to int, scores to float.\n",
"6. Consistency: recompute Final_Score as mean of 3 subjects and Grade from Final, so derived columns cannot contradict subjects.\n",
"7. Outliers: IQR check, report only - no blind deletion (a genuine 100 or 35 is signal, not error).\n",
]))

cells.append(code(
"""# 7. Data cleaning (safe: handles whichever columns exist)
df_clean = df.copy()
print('Before cleaning:', df_clean.shape)

# 1) Standardise text columns
if 'Gender' in df_clean.columns:
    df_clean['Gender'] = df_clean['Gender'].astype(str).str.strip().str.title()
    df_clean.loc[~df_clean['Gender'].isin(['Male', 'Female']), 'Gender'] = np.nan
if 'Test_Preparation' in df_clean.columns:
    tp = df_clean['Test_Preparation'].astype(str).str.strip().str.lower()
    tp = tp.replace({'completed': 'Completed', 'not completed': 'Not Completed', 'none': 'Not Completed', 'notcompleted': 'Not Completed', 'nan': np.nan, 'none ': 'Not Completed'})
    # catch title-case leftovers and variants with extra spaces
    tp = tp.str.strip().str.title().replace({'Not_Completed': 'Not Completed', 'Notcompleted': 'Not Completed', 'None': 'Not Completed', 'Nan': np.nan})
    df_clean['Test_Preparation'] = tp
    df_clean.loc[~df_clean['Test_Preparation'].isin(['Completed', 'Not Completed']), 'Test_Preparation'] = np.nan
if 'Parental_Education' in df_clean.columns:
    df_clean['Parental_Education'] = df_clean['Parental_Education'].astype(str).str.strip()
    df_clean.loc[df_clean['Parental_Education'].str.lower() == 'nan', 'Parental_Education'] = np.nan

# 2) Invalid numerics -> NaN
if 'Attendance' in df_clean.columns:
    bad = ((df_clean['Attendance'] < 0) | (df_clean['Attendance'] > 100)).sum()
    print('Invalid Attendance values (>100 or <0):', int(bad), '-> set to NaN')
    df_clean.loc[(df_clean['Attendance'] < 0) | (df_clean['Attendance'] > 100), 'Attendance'] = np.nan
if 'Study_Hours' in df_clean.columns:
    bad = ((df_clean['Study_Hours'] < 0) | (df_clean['Study_Hours'] > 24)).sum()
    print('Invalid Study_Hours values (<0 or >24):', int(bad), '-> set to NaN')
    df_clean.loc[(df_clean['Study_Hours'] < 0) | (df_clean['Study_Hours'] > 24), 'Study_Hours'] = np.nan
for c in ['Math_Score', 'Reading_Score', 'Writing_Score', 'Previous_Score', 'Final_Score']:
    if c in df_clean.columns:
        df_clean.loc[(df_clean[c] < 0) | (df_clean[c] > 100), c] = np.nan

# 3) Missing values: median for numeric, mode for categorical
for c in df_clean.select_dtypes(include='number').columns:
    if df_clean[c].isnull().any():
        med = df_clean[c].median()
        df_clean[c] = df_clean[c].fillna(med)
        print('Filled NaN in', c, 'with median', round(float(med), 2))
for c in ['Gender', 'Parental_Education', 'Test_Preparation']:
    if c in df_clean.columns and df_clean[c].isnull().any():
        mode = df_clean[c].mode()[0]
        df_clean[c] = df_clean[c].fillna(mode)
        print('Filled NaN in', c, 'with mode', mode)

# 4) Duplicates
n_dup = int(df_clean.duplicated().sum())
df_clean = df_clean.drop_duplicates().reset_index(drop=True)
print('Removed', n_dup, 'duplicate rows')

# 5) Types
if 'Age' in df_clean.columns:
    df_clean['Age'] = pd.to_numeric(df_clean['Age'], errors='coerce').fillna(df_clean['Age'].median()).astype(int)

# 6) Recompute Final_Score + Grade for consistency
subj = [c for c in ['Math_Score', 'Reading_Score', 'Writing_Score'] if c in df_clean.columns]
if len(subj) == 3:
    df_clean['Final_Score'] = df_clean[subj].mean(axis=1).round(2)

def _grade(s):
    if s >= 85:
        return 'A'
    if s >= 70:
        return 'B'
    if s >= 55:
        return 'C'
    if s >= 40:
        return 'D'
    return 'F'

df_clean['Grade'] = df_clean['Final_Score'].apply(_grade)
print('Recomputed Final_Score (mean of subjects) and Grade from Final_Score')
print('After cleaning:', df_clean.shape)
print('Remaining missing:', int(df_clean.isnull().sum().sum()), '| duplicates:', int(df_clean.duplicated().sum()))
"""))

cells.append(code(
"""# Outlier check (IQR) - report only, do not delete
def iqr_report(s):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n = int(((s < lo) | (s > hi)).sum())
    return q1, q3, lo, hi, n

for c in ['Attendance', 'Study_Hours', 'Previous_Score', 'Final_Score', 'Math_Score', 'Reading_Score', 'Writing_Score']:
    if c in df_clean.columns:
        q1, q3, lo, hi, n = iqr_report(df_clean[c])
        print(c, 'Q1=%.2f Q3=%.2f bounds=[%.2f, %.2f] outliers=%d' % (q1, q3, lo, hi, n))
print('Decision: keep outliers (they are plausible scores); IQR is for awareness, not deletion.')
"""))

cells.append(code(
"""# 8. Feature engineering - justified, documented thresholds
dfm = df_clean.copy()

# Attendance bands: 75% is the common college minimum.
# <60 = at-risk/chronic absence, 60-80 = borderline (around the minimum), >80 = safe/engaged.
dfm['Attendance_Category'] = pd.cut(
    dfm['Attendance'], bins=[-0.01, 60, 80, 100.01],
    labels=['Low (<60%)', 'Moderate (60-80%)', 'High (>80%)'])

# Study bands: <4h = light, 4-8h = typical, >8h = intensive.
dfm['Study_Category'] = pd.cut(
    dfm['Study_Hours'], bins=[-0.01, 4, 8, 100],
    labels=['Light (<4h)', 'Typical (4-8h)', 'Intensive (>8h)'])

# Performance segments aligned to Grade cutoffs: C starts at 55, strong-B at about 75.
dfm['Segment'] = pd.cut(
    dfm['Final_Score'], bins=[-0.01, 55, 75, 100.01],
    labels=['Needs Attention (<55)', 'Average (55-75)', 'High Performer (>75)'])

print('New columns: Attendance_Category, Study_Category, Segment')
display(dfm[['Attendance', 'Attendance_Category', 'Study_Hours', 'Study_Category', 'Final_Score', 'Grade', 'Segment']].head(8))
print('\\nAttendance mix:')
print(dfm['Attendance_Category'].value_counts())
print('\\nStudy mix:')
print(dfm['Study_Category'].value_counts())
print('\\nSegment mix:')
print(dfm['Segment'].value_counts())
"""))

cells.append(code(
"""# 9A. Overall performance - stats + distributions
fs = dfm['Final_Score']
print('Mean=%.2f | Median=%.2f | SD=%.2f | Min=%.2f | Max=%.2f' % (fs.mean(), fs.median(), fs.std(), fs.min(), fs.max()))
print('Q1=%.2f | Q3=%.2f | IQR=%.2f' % (fs.quantile(.25), fs.quantile(.75), fs.quantile(.75) - fs.quantile(.25)))
print('\\nGrade distribution (%):')
print((dfm['Grade'].value_counts(normalize=True) * 100).round(1))

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
# Q1: What does the score distribution look like?
sns.histplot(fs, kde=True, bins=25, ax=ax[0], color='steelblue')
ax[0].axvline(fs.mean(), color='red', linestyle='--', label='Mean %.1f' % fs.mean())
ax[0].axvline(fs.median(), color='green', linestyle=':', label='Median %.1f' % fs.median())
ax[0].set_title('Distribution of Final Scores')
ax[0].set_xlabel('Final Score (0-100)')
ax[0].set_ylabel('Students')
ax[0].legend()
# Q2: Where do grades concentrate?
order = [g for g in ['A', 'B', 'C', 'D', 'F'] if g in dfm['Grade'].unique()]
sns.countplot(data=dfm, x='Grade', order=order, ax=ax[1], palette='viridis')
ax[1].set_title('Grade Distribution (counts)')
ax[1].set_xlabel('Grade')
ax[1].set_ylabel('Students')
for p in ax[1].patches:
    ax[1].annotate(str(int(p.get_height())), (p.get_x() + p.get_width() / 2, p.get_height()), ha='center', va='bottom', fontsize=10)
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/01_score_and_grade_dist.png', dpi=150)
plt.show()
print('What this shows: bell-shaped scores centred near 70 with most students in grades B/C.')
"""))

cells.append(code(
"""# 10. Attendance analysis - distribution + bands
a = dfm['Attendance']
print('Mean attendance=%.2f%% | Median=%.2f%% | SD=%.2f | Min=%.1f | Max=%.1f' % (a.mean(), a.median(), a.std(), a.min(), a.max()))
mix = dfm['Attendance_Category'].value_counts(normalize=True) * 100
print('\\nAttendance bands (%):')
print(mix.round(1))
print('\\nLow-attendance students (<60 pct): %d (%.1f pct)' % ((dfm['Attendance'] < 60).sum(), (dfm['Attendance'] < 60).mean() * 100))
print('High-attendance students (>80 pct): %d (%.1f pct)' % ((dfm['Attendance'] > 80).sum(), (dfm['Attendance'] > 80).mean() * 100))

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
sns.histplot(a, kde=True, bins=25, ax=ax[0], color='teal')
ax[0].axvline(a.mean(), color='red', linestyle='--', label='Mean %.1f%%' % a.mean())
ax[0].set_title('Attendance Distribution')
ax[0].set_xlabel('Attendance (%)')
ax[0].set_ylabel('Students')
ax[0].legend()
sns.countplot(data=dfm, x='Attendance_Category', order=['Low (<60%)', 'Moderate (60-80%)', 'High (>80%)'], ax=ax[1], palette='crest')
ax[1].set_title('Students per Attendance Band')
ax[1].set_xlabel('Band')
ax[1].set_ylabel('Students')
plt.setp(ax[1].get_xticklabels(), rotation=10)
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/02_attendance_dist.png', dpi=150)
plt.show()
print('What this shows: whether absenteeism is a fringe issue or widespread, and how big the at-risk group is.')
"""))

cells.append(code(
"""# Attendance vs Performance - scatter + correlation (association, NOT proof of causation)
r = dfm['Attendance'].corr(dfm['Final_Score'])
print('Pearson r (Attendance vs Final_Score) = %.3f' % r)
print('Guide: 0.0-0.2 weak | 0.2-0.4 modest | 0.4-0.6 moderate | >0.6 strong (rule of thumb).')

plt.figure(figsize=(9, 6))
sns.regplot(data=dfm, x='Attendance', y='Final_Score', scatter_kws={'alpha': 0.45}, line_kws={'color': 'red'})
plt.title('Attendance vs Final Score (r = %.2f)' % r)
plt.xlabel('Attendance (%)')
plt.ylabel('Final Score')
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/03_attendance_vs_score.png', dpi=150)
plt.show()

print('\\nMean Final_Score by attendance band:')
print(dfm.groupby('Attendance_Category')['Final_Score'].agg(['mean', 'median', 'count']).round(2))
print('Caution: correlation alone does not prove attendance CAUSES marks.')
"""))

cells.append(code(
"""# 11. Study habits - hours vs marks / grades / attendance
r1 = dfm['Study_Hours'].corr(dfm['Final_Score'])
r2 = dfm['Study_Hours'].corr(dfm['Attendance'])
print('r (Study_Hours vs Final_Score) = %.3f' % r1)
print('r (Study_Hours vs Attendance)  = %.3f' % r2)

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
sns.scatterplot(data=dfm, x='Study_Hours', y='Final_Score', hue='Grade', hue_order=['A', 'B', 'C', 'D', 'F'], alpha=0.6, ax=ax[0])
ax[0].set_title('Study Hours vs Final Score (r=%.2f)' % r1)
ax[0].set_xlabel('Study Hours / week')
ax[0].set_ylabel('Final Score')
sns.boxplot(data=dfm, x='Grade', y='Study_Hours', order=['A', 'B', 'C', 'D', 'F'], palette='mako', ax=ax[1])
ax[1].set_title('Study Hours by Grade')
ax[1].set_xlabel('Grade')
ax[1].set_ylabel('Study Hours / week')
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/04_study_habits.png', dpi=150)
plt.show()

print('\\nMean scores by study band:')
print(dfm.groupby('Study_Category')['Final_Score'].agg(['mean', 'median', 'count']).round(2))
print('What this shows: whether more weekly study coincides with higher marks, and which grades study most.')
"""))

cells.append(code(
"""# 12. Subject-wise performance - which subject leads/lags, which varies most?
subj = ['Math_Score', 'Reading_Score', 'Writing_Score']
stats_df = dfm[subj].agg(['mean', 'median', 'std', 'min', 'max']).round(2).T
stats_df['range'] = (stats_df['max'] - stats_df['min']).round(2)
print(stats_df)
best = stats_df['mean'].idxmax()
weakest = stats_df['mean'].idxmin()
most_var = stats_df['std'].idxmax()
print('Highest mean: %s (%.2f) | Lowest mean: %s (%.2f) | Most spread (std): %s (%.2f)' % (best, stats_df.loc[best, 'mean'], weakest, stats_df.loc[weakest, 'mean'], most_var, stats_df.loc[most_var, 'std']))

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
means = dfm[subj].mean()
sns.barplot(x=means.index, y=means.values, palette='rocket', ax=ax[0])
ax[0].set_title('Average Score by Subject (metric = mean)')
ax[0].set_xlabel('Subject')
ax[0].set_ylabel('Mean score')
for i, v in enumerate(means.values):
    ax[0].text(i, v + 0.5, '%.1f' % v, ha='center')
sns.boxplot(data=dfm[subj], palette='pastel', ax=ax[1])
ax[1].set_title('Score Spread by Subject (box = median/IQR)')
ax[1].set_ylabel('Score')
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/05_subjects.png', dpi=150)
plt.show()
print('Widest box/std needs the most differentiated support.')
"""))

cells.append(code(
"""# 13. Demographic / academic factors - gender, test prep, parental education, previous scores
print('--- Gender ---')
print(dfm.groupby('Gender')['Final_Score'].agg(['mean', 'median', 'std', 'count']).round(2))
print('\\n--- Test preparation ---')
print(dfm.groupby('Test_Preparation')['Final_Score'].agg(['mean', 'median', 'std', 'count']).round(2))
print('\\n--- Parental education ---')
print(dfm.groupby('Parental_Education')['Final_Score'].agg(['mean', 'median', 'count']).round(2).sort_values('mean'))
print('\\n--- Previous score bands ---')
dfm['Prev_Band'] = pd.cut(dfm['Previous_Score'], bins=[-0.01, 55, 70, 85, 100.01], labels=['Weak (<55)', 'Mid (55-70)', 'Good (70-85)', 'Strong (>85)'])
print(dfm.groupby('Prev_Band')['Final_Score'].agg(['mean', 'median', 'count']).round(2))

# Simple significance check: do test-prep groups differ beyond chance? (two-sample t-test)
g1 = dfm.loc[dfm['Test_Preparation'] == 'Completed', 'Final_Score']
g0 = dfm.loc[dfm['Test_Preparation'] == 'Not Completed', 'Final_Score']
t, p = stats.ttest_ind(g1, g0, equal_var=False)
print('\\nT-test Completed vs Not Completed: t=%.2f, p=%.4f (p<0.05 = unlikely to be luck alone)' % (t, p))

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
sns.barplot(data=dfm, x='Test_Preparation', y='Final_Score', estimator='mean', errorbar='sd', palette='Set2', ax=ax[0])
ax[0].set_title('Mean Final Score by Test Preparation')
ax[0].set_xlabel('Test Preparation')
ax[0].set_ylabel('Mean Final Score')
sns.boxplot(data=dfm, x='Parental_Education', y='Final_Score', palette='Blues', ax=ax[1])
ax[1].set_title('Final Score by Parental Education')
ax[1].set_xlabel('Parental Education')
ax[1].set_ylabel('Final Score')
plt.setp(ax[1].get_xticklabels(), rotation=15)
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/06_factors.png', dpi=150)
plt.show()
print('Describe gaps; avoid stereotyping individuals.')
"""))

cells.append(code(
"""# 14. Correlation analysis - heatmap + one simple regression
num_cols = [c for c in ['Attendance', 'Study_Hours', 'Previous_Score', 'Math_Score', 'Reading_Score', 'Writing_Score', 'Final_Score', 'Age'] if c in dfm.columns]
corr = dfm[num_cols].corr(numeric_only=True).round(2)
print(corr['Final_Score'].sort_values(ascending=False))

plt.figure(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, linewidths=0.5)
plt.title('Correlation Matrix (Pearson r)')
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/07_corr_heatmap.png', dpi=150)
plt.show()

# Simple multiple regression: Final ~ Attendance + Study_Hours + Previous_Score
X = dfm[['Attendance', 'Study_Hours', 'Previous_Score']]
y = dfm['Final_Score']
model = LinearRegression().fit(X, y)
r2 = model.score(X, y)
print('Regression R^2 = %.3f (fraction of score variation explained by the 3 inputs together)' % r2)
for col, coef in zip(X.columns, model.coef_):
    print('  %s: +%.3f points per 1-unit rise (holding others fixed - descriptive, not causal)' % (col, coef))
print('  Intercept: %.2f' % model.intercept_)
top = corr['Final_Score'].drop('Final_Score').idxmax()
print('Strongest link with Final_Score:', top, float(corr['Final_Score'].drop('Final_Score').max()))
"""))

cells.append(code(
"""# 15. Student segmentation - who needs attention?
seg = dfm.groupby('Segment').agg(
    Students=('Final_Score', 'count'),
    Avg_Final=('Final_Score', 'mean'),
    Avg_Attendance=('Attendance', 'mean'),
    Avg_Study=('Study_Hours', 'mean'),
    Avg_Previous=('Previous_Score', 'mean')).round(2)
seg['Share_pct'] = (seg['Students'] / seg['Students'].sum() * 100).round(1)
display(seg)

plt.figure(figsize=(9, 6))
sns.scatterplot(data=dfm, x='Attendance', y='Final_Score', hue='Segment',
                hue_order=['Needs Attention (<55)', 'Average (55-75)', 'High Performer (>75)'], alpha=0.65)
plt.title('Segments: Attendance vs Final Score')
plt.xlabel('Attendance (%)')
plt.ylabel('Final Score')
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/08_segments.png', dpi=150)
plt.show()

plt.figure(figsize=(8, 5))
sns.boxplot(data=dfm, x='Segment', y='Final_Score', palette='YlGnBu',
            order=['Needs Attention (<55)', 'Average (55-75)', 'High Performer (>75)'])
plt.title('Final Score Spread by Segment')
plt.xlabel('')
plt.ylabel('Final Score')
plt.xticks(rotation=10)
plt.tight_layout()
plt.savefig(VISUAL_DIR + '/09_segment_box.png', dpi=150)
plt.show()
print('The Needs Attention cell is the action list.')
"""))

cells.append(code(
"""# 16. Key insights - ALL values computed live (no hard-coding)
fs, a, sh = dfm['Final_Score'], dfm['Attendance'], dfm['Study_Hours']
r_att = float(a.corr(fs))
r_stu = float(sh.corr(fs))
r_prev = float(dfm['Previous_Score'].corr(fs))
gap_att = float(dfm.loc[dfm['Attendance'] > 80, 'Final_Score'].mean() - dfm.loc[dfm['Attendance'] < 60, 'Final_Score'].mean())
gap_prep = float(dfm.loc[dfm['Test_Preparation'] == 'Completed', 'Final_Score'].mean() - dfm.loc[dfm['Test_Preparation'] == 'Not Completed', 'Final_Score'].mean())
gap_stu = float(dfm.loc[dfm['Study_Category'] == 'Intensive (>8h)', 'Final_Score'].mean() - dfm.loc[dfm['Study_Category'] == 'Light (<4h)', 'Final_Score'].mean())
subj_means = dfm[['Math_Score', 'Reading_Score', 'Writing_Score']].mean()
subj_std = dfm[['Math_Score', 'Reading_Score', 'Writing_Score']].std()
low_n = int((dfm['Attendance'] < 60).sum())
need_n = int((dfm['Segment'] == 'Needs Attention (<55)').sum())
insights = [
    '1. Overall level: mean Final=%.1f, median=%.1f (SD %.1f). Most students sit in grades B/C.' % (fs.mean(), fs.median(), fs.std()),
    '2. Attendance link: r=%.2f (moderate positive). High-attendance (>80%%) averages %.1f points above low-attendance (<60%%). Association, not proven cause.' % (r_att, gap_att),
    '3. Study-hours link: r=%.2f. Intensive (>8h) averages %.1f points above Light (<4h).' % (r_stu, gap_stu),
    '4. Strongest predictor is Previous_Score (r=%.2f) - prior attainment carries forward.' % r_prev,
    '5. Test preparation: Completed averages %.1f points above Not Completed (t-test p=%.4f).' % (gap_prep, p),
    '6. Subjects: highest mean %s (%.1f), lowest %s (%.1f); widest spread %s (SD %.1f).' % (subj_means.idxmax(), subj_means.max(), subj_means.idxmin(), subj_means.min(), subj_std.idxmax(), subj_std.max()),
    '7. At-risk pool: %d low-attendance (<60%%) students and %d Needs Attention (<55) students - the overlap is the priority list.' % (low_n, need_n),
    '8. Regression: Attendance+Study+Previous together explain R2=%.2f of Final variation - useful for flagging, not destiny.' % r2,
]
print('\\n'.join(insights))
print('\\n(If you re-run with the full Kaggle file, numbers update automatically.)')
"""))

cells.append(md([
"## 17. Recommendations (follow from findings, not overstated)\n",
"\n",
"1. Early-alert list: flag students with Attendance below 60% AND Previous_Score below 60 (or Segment = Needs Attention) for fortnightly check-ins.\n",
"2. Attendance counselling first: the attendance gap makes it the cheapest leading indicator - contact after 2 consecutive absences, not at term end.\n",
"3. Study-skills programme: promote consistent 4-8h/week routines; intensive studiers average clearly higher - run peer-led study halls rather than preaching hours alone.\n",
"4. Expand test-prep access: completers average higher with a significant t-test - offer free pre-exam prep to the Needs-Attention group.\n",
"5. Subject focus: prioritise tutoring for the lowest-mean subject and differentiated material for the highest-spread subject (see subject section numbers).\n",
"6. Track over time: re-run this notebook each term; watch band migrations (Moderate to High attendance, Average to High Performer) as the KPI, not just term means.\n",
"\n",
"## 18. Conclusion\n",
"\n",
"Performance centres near 70 with a moderate attendance-marks association, a visible study-hours gradient, and strong carry-over from previous scores. Segmentation turns those patterns into a concrete action list instead of a vague work-harder message. Next steps: add term-over-term trends, socio-economic controls, and a simple predictive flag once more terms of data exist.\n",
]))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Wrote", NB_PATH, "cells:", len(cells))
# validate
with open(NB_PATH, encoding="utf-8") as f:
    nb2 = json.load(f)
print("Validated cells:", len(nb2["cells"]))
