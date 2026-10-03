"""Generate a realistic Student Performance dataset (1000 rows).
Matches the Kaggle 'Student Performance Factors' structure + classic
StudentsPerformance.csv subject columns, so the analysis notebook works
with either the real Kaggle file or this file.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 1000

student_id = np.arange(1, N + 1)
gender = rng.choice(["Male", "Female"], size=N, p=[0.52, 0.48])
age = rng.integers(15, 20, size=N)
parental_edu = rng.choice(
    ["High School", "Some College", "Associate", "Bachelor's", "Master's"],
    size=N, p=[0.25, 0.20, 0.15, 0.25, 0.15]
)
test_prep = rng.choice(["Completed", "Not Completed"], size=N, p=[0.35, 0.65])

attendance = np.clip(rng.normal(75, 12, N), 50, 100).round(1)
study_hours = np.clip(rng.normal(6.0, 2.5, N), 0, 15).round(1)
previous = np.clip(rng.normal(68, 12, N), 35, 100).round(1)

prep_boost = np.where(test_prep == "Completed", 5.0, 0.0)
noise_m = rng.normal(0, 7, N)
noise_r = rng.normal(0, 6, N)
noise_w = rng.normal(0, 6.5, N)

math = 12 + 0.45 * previous + 0.22 * attendance + 0.9 * study_hours + prep_boost + noise_m
reading = 15 + 0.42 * previous + 0.20 * attendance + 0.8 * study_hours + prep_boost + noise_r
writing = 14 + 0.43 * previous + 0.21 * attendance + 0.85 * study_hours + prep_boost + noise_w

math = np.clip(math, 0, 100).round(1)
reading = np.clip(reading, 0, 100).round(1)
writing = np.clip(writing, 0, 100).round(1)
final = ((math + reading + writing) / 3).round(2)

def to_grade(s):
    if s >= 85: return "A"
    if s >= 70: return "B"
    if s >= 55: return "C"
    if s >= 40: return "D"
    return "F"

grades = [to_grade(s) for s in final]

df = pd.DataFrame({
    "Student_ID": student_id,
    "Gender": gender,
    "Age": age,
    "Parental_Education": parental_edu,
    "Test_Preparation": test_prep,
    "Attendance": attendance,
    "Study_Hours": study_hours,
    "Previous_Score": previous,
    "Math_Score": math,
    "Reading_Score": reading,
    "Writing_Score": writing,
    "Final_Score": final,
    "Grade": grades,
})

# ---- Inject realistic dirt for the cleaning demo (do NOT remove before analysis) ----
# 2% missing in 3 columns
for col in ["Attendance", "Study_Hours", "Parental_Education"]:
    idx = rng.choice(df.index, size=int(0.02 * N), replace=False)
    df.loc[idx, col] = np.nan

# inconsistent text entries
idx = rng.choice(df.index, size=8, replace=False)
df.loc[idx[:3], "Gender"] = ["male", "FEMALE", " Female "][:3]
idx2 = rng.choice(df.index, size=6, replace=False)
df.loc[idx2, "Test_Preparation"] = [" completed", "not completed ", "NOT COMPLETED",
                                     " completed", " completed", "not completed "]

# a few invalid values
df.loc[rng.choice(df.index, size=3, replace=False), "Attendance"] = [105.0, -5.0, 999.0][:3]
df.loc[rng.choice(df.index, size=3, replace=False), "Study_Hours"] = [-2.0, 40.0, -1.0][:3]

# 10 exact duplicate rows
dups = df.sample(10, random_state=7)
df = pd.concat([df, dups], ignore_index=True)

# shuffle
df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

df.to_csv("data/StudentPerformanceFactors.csv", index=False)
print(f"Saved data/StudentPerformanceFactors.csv with shape {df.shape}")
print(df.head(3).to_string())
print("\nMissing values:\n", df.isnull().sum())
print(f"\nDuplicates: {df.duplicated().sum()}")
