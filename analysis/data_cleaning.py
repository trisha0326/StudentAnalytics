"""Data cleaning + intelligent column detection.

The uploaded CSV may use many different column names, so we:
1. Normalise every header (case-insensitive, ignore _, -, extra spaces).
2. Map common variations to one canonical name.
3. Never invent data -- if a column is absent, that metric/chart is hidden.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Column normalisation + matching
# ---------------------------------------------------------------------------

def normalize(name):
    """'Attendance %' -> 'attendance %' ; 'Study_Hours' -> 'study hours'."""
    s = str(name).strip().lower().replace("_", " ").replace("-", " ")
    s = s.replace("%", " % ").replace("(", " ").replace(")", " ")
    return " ".join(s.split())


def find_column(df, candidates):
    """Return the actual df column matching any candidate (case-insensitive).

    Example: find_column(df, ["attendance", "attendance %", "attendance percentage"])
    """
    norm_map = {normalize(c): c for c in df.columns}
    for cand in candidates:
        key = normalize(cand)
        if key in norm_map:
            return norm_map[key]
    # fallback: whole-word match (all candidate words appear as full words
    # in the header). Word-based so "age" never matches "percentAGE".
    for cand in candidates:
        cw = normalize(cand).split()
        if not cw:
            continue
        for norm_col, orig_col in norm_map.items():
            col_words = norm_col.split()
            if all(w in col_words for w in cw):
                return orig_col
    return None


# Candidate name lists -------------------------------------------------------

CANDIDATES = {
    "student_id": ["student id", "student_id", "id", "roll no", "roll number", "admission no"],
    "name": ["name", "student name", "full name"],
    "gender": ["gender", "sex"],
    "age": ["age"],
    "attendance": [
        "attendance", "attendance %", "attendance percentage", "attendance percent",
        "attendance_percentage", "attendance_percent", "attendance rate", "present %",
        "attend", "att", "presence", "present",
    ],
    "study_hours": [
        "study hours", "study_hours", "study hrs", "hours studied",
        "study time", "study hours per week", "study hours/week", "hours",
    ],
    "previous_score": ["previous score", "previous scores", "prev score", "prior score", "last year score"],
    "final_score": [
        "final score", "final_score", "exam score", "average score", "overall score",
        "total marks", "total score", "marks", "score", "percentage", "result", "final marks",
    ],
    "grade": ["grade"],
    "test_prep": [
        "test preparation", "test preparation course", "test prep",
        "test_preparation", "prep course", "preparation",
    ],
    "parental_education": [
        "parental education", "parental level of education",
        "parental education level", "parent education", "parents education",
    ],
}

# Known subject keywords -> pretty label
SUBJECT_KEYWORDS = {
    "math": "Math",
    "reading": "Reading",
    "writing": "Writing",
    "science": "Science",
    "english": "English",
    "computer": "Computer Science",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "biology": "Biology",
    "history": "History",
    "hindi": "Hindi",
    "social": "Social Science",
}


def detect_columns(df):
    """Inspect uploaded columns and return a mapping of canonical -> actual name.

    Returns dict like:
    {"attendance": "Attendance", "final_score": "Final_Score",
     "subjects": ["Math_Score", ...], ...}
    Missing concepts are simply absent from the dict.
    """
    mapping = {}
    used = set()

    for key, cands in CANDIDATES.items():
        # avoid stealing a column already claimed (e.g. "score" matching a subject col)
        available = [c for c in df.columns if c not in used]
        temp = df[available] if available else df.iloc[:, 0:0]
        found = find_column(temp, cands)
        if found is not None:
            # guard: generic "score"/"marks" should not grab a subject column
            if key == "final_score" and found not in df.columns:
                continue
            mapping[key] = found
            used.add(found)

    # subjects: any column whose normalised name contains a subject keyword
    subjects = []
    for col in df.columns:
        if col in used:
            continue
        n = normalize(col)
        for kw, label in SUBJECT_KEYWORDS.items():
            if kw in n and ("score" in n or "mark" in n or n == kw or n.endswith(" " + kw) or n.startswith(kw + " ")):
                subjects.append(col)
                used.add(col)
                break
    mapping["subjects"] = subjects
    return mapping


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def _score_scale(series):
    """Detect 0-100 vs 0-10 (GPA) scale from data. Returns (lo, hi)."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return (0, 100)
    if s.quantile(0.9) <= 10 and s.max() <= 10.5:
        return (0, 10)
    return (0, 100)


def clean_dataframe(df_raw):
    """Clean an uploaded dataframe. Returns (df_clean, colmap, quality)."""
    df = df_raw.copy()
    # strip header whitespace
    df.columns = [str(c).strip() for c in df.columns]
    rows_uploaded = int(df.shape[0])

    # drop fully-empty rows/cols first
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    if df.empty:
        raise ValueError("The CSV appears to be empty after removing blank rows.")

    colmap = detect_columns(df)
    missing_before = int(df.isnull().sum().sum())
    dup_before = int(df.duplicated().sum())

    numeric_cols = []
    categorical_cols = []
    for key in ["attendance", "study_hours", "previous_score", "final_score", "age"]:
        if key in colmap:
            numeric_cols.append(colmap[key])
    for subj in colmap.get("subjects", []):
        numeric_cols.append(subj)

    # coerce numerics
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # ---- standardise text columns ----------------------------------------
    if "gender" in colmap:
        c = colmap["gender"]
        df[c] = df[c].astype(str).str.strip().str.title()
        df.loc[~df[c].isin(["Male", "Female"]), c] = np.nan
    if "test_prep" in colmap:
        c = colmap["test_prep"]
        s = df[c].astype(str).str.strip().str.lower()
        s = s.replace({
            "completed": "Completed", "not completed": "Not Completed",
            "none": "Not Completed", "notcompleted": "Not Completed",
            "nan": np.nan, "none ": "Not Completed", "": np.nan,
        })
        s = s.str.strip().str.title().replace(
            {"Not_Completed": "Not Completed", "Notcompleted": "Not Completed",
             "None": "Not Completed", "Nan": np.nan})
        df[c] = s
        df.loc[~df[c].isin(["Completed", "Not Completed"]), c] = np.nan
    if "parental_education" in colmap:
        c = colmap["parental_education"]
        df[c] = df[c].astype(str).str.strip()
        df.loc[df[c].str.lower().isin(["nan", "none", "null", ""]), c] = np.nan
    if "grade" in colmap:
        c = colmap["grade"]
        df[c] = df[c].astype(str).str.strip().str.upper()
        df.loc[~df[c].isin(["A", "B", "C", "D", "E", "F"]), c] = np.nan

    # ---- invalid numerics -> NaN ------------------------------------------
    if "attendance" in colmap:
        c = colmap["attendance"]
        bad = ((df[c] < 0) | (df[c] > 100)).sum()
        df.loc[(df[c] < 0) | (df[c] > 100), c] = np.nan
    else:
        bad = 0
    for key in ["study_hours", "previous_score", "final_score", "age"]:
        if key not in colmap:
            continue
        c = colmap[key]
        if key == "study_hours":
            df.loc[(df[c] < 0) | (df[c] > 24), c] = np.nan
        elif key == "age":
            df.loc[(df[c] < 5) | (df[c] > 60), c] = np.nan
        else:
            lo, hi = _score_scale(df[c])
            df.loc[(df[c] < lo) | (df[c] > hi), c] = np.nan

    for subj in colmap.get("subjects", []):
        lo, hi = _score_scale(df[subj])
        df.loc[(df[subj] < lo) | (df[subj] > hi), subj] = np.nan

    # ---- derive Final_Score from subjects when absent ----------------------
    if "final_score" not in colmap and len(colmap.get("subjects", [])) >= 1:
        subs = colmap["subjects"]
        df["__Derived_Final"] = df[subs].mean(axis=1, skipna=True).round(2)
        colmap["final_score"] = "__Derived_Final"
        colmap["final_derived"] = True
        numeric_cols.append("__Derived_Final")

    # ---- fill missing -------------------------------------------------------
    filled_numeric, filled_categorical = {}, {}
    for c in df.select_dtypes(include="number").columns:
        if df[c].isnull().any():
            med = df[c].median()
            if pd.isna(med):
                med = 0
            df[c] = df[c].fillna(med)
            filled_numeric[c] = round(float(med), 2)
    for key in ["gender", "test_prep", "parental_education", "grade"]:
        if key in colmap:
            c = colmap[key]
            if df[c].isnull().any():
                try:
                    mode = df[c].mode().iloc[0]
                except Exception:
                    mode = "Unknown"
                df[c] = df[c].fillna(mode)
                filled_categorical[c] = str(mode)

    # ---- duplicates ---------------------------------------------------------
    n_dup = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)

    # ---- derive Grade when absent but score present -------------------------
    if "grade" not in colmap and "final_score" in colmap:
        s = df[colmap["final_score"]]
        scale_hi = 100 if not (s.quantile(0.9) <= 10) else 10
        if scale_hi == 100:
            def _grade(x):
                if x >= 85:
                    return "A"
                if x >= 70:
                    return "B"
                if x >= 55:
                    return "C"
                if x >= 40:
                    return "D"
                return "F"
        else:
            def _grade(x):
                if x >= 8.5:
                    return "A"
                if x >= 7:
                    return "B"
                if x >= 5.5:
                    return "C"
                if x >= 4:
                    return "D"
                return "F"
        df["__Derived_Grade"] = s.apply(_grade)
        colmap["grade"] = "__Derived_Grade"
        colmap["grade_derived"] = True

    # ---- outlier report (IQR, report only) -----------------------------------
    outlier_counts = {}
    for c in df.select_dtypes(include="number").columns:
        s = df[c].dropna()
        if len(s) < 8:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_counts[c] = int(((s < lo) | (s > hi)).sum())

    quality = {
        "rows_uploaded": rows_uploaded,
        "rows_after": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_values": missing_before,
        "duplicate_rows": dup_before,
        "duplicates_removed": n_dup,
        "numeric_columns": int(len(df.select_dtypes(include="number").columns)),
        "categorical_columns": int(len(df.select_dtypes(exclude="number").columns)),
        "filled_numeric": filled_numeric,
        "filled_categorical": filled_categorical,
        "outliers": outlier_counts,
        "detected": {k: (v if k != "subjects" else list(v)) for k, v in colmap.items()},
    }
    return df, colmap, quality
