"""Descriptive analytics over the cleaned dataframe.

Every function checks whether its required columns exist first and
returns None / skips gracefully when data is absent. Nothing is fabricated.
"""
import numpy as np
import pandas as pd

PASS_MARK = 40  # on a 0-100 scale; scaled automatically for 0-10 data


def _scale_info(score_series):
    """Return (pass_mark, seg_high, seg_low) adapted to 0-100 or 0-10 scales."""
    s = pd.to_numeric(score_series, errors="coerce").dropna()
    if not s.empty and s.quantile(0.9) <= 10 and s.max() <= 10.5:
        return (4.0, 7.5, 5.0)
    return (40.0, 75.0, 50.0)


def _clean_list(values, limit=2000):
    """Round + downsample a series for JSON payloads (keeps dashboard fast)."""
    s = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if len(s) > limit:
        s = s.sample(limit, random_state=42).sort_index()
    return [round(float(x), 2) for x in s.tolist()]


def compute_dashboard(df, colmap):
    """Build the full dashboard payload. Returns a JSON-serialisable dict."""
    out = {"has": {}, "kpis": {}, "stats": {}, "charts": {},
           "segments": None, "correlation": None, "groups": {}}

    has_score = "final_score" in colmap
    has_att = "attendance" in colmap
    has_study = "study_hours" in colmap
    has_gender = "gender" in colmap
    has_prep = "test_prep" in colmap
    has_parent = "parental_education" in colmap
    has_prev = "previous_score" in colmap
    subjects = list(colmap.get("subjects", []))

    out["has"] = {
        "score": bool(has_score), "attendance": bool(has_att),
        "study": bool(has_study), "gender": bool(has_gender),
        "test_prep": bool(has_prep), "parental": bool(has_parent),
        "previous": bool(has_prev), "subjects": len(subjects) > 0,
        "subject_list": subjects,
    }

    total = int(len(df))
    out["kpis"]["total_students"] = total

    score_col = colmap.get("final_score")
    att_col = colmap.get("attendance")
    stu_col = colmap.get("study_hours")

    # ---- KPIs --------------------------------------------------------------
    if has_score:
        s = pd.to_numeric(df[score_col], errors="coerce").dropna()
        pass_mark, seg_high, seg_low = _scale_info(s)
        out["kpis"]["avg_score"] = round(float(s.mean()), 2)
        out["kpis"]["pass_pct"] = round(float((s >= pass_mark).mean() * 100), 1)
        out["kpis"]["pass_mark"] = pass_mark
        out["stats"]["performance"] = {
            "mean": round(float(s.mean()), 2), "median": round(float(s.median()), 2),
            "min": round(float(s.min()), 2), "max": round(float(s.max()), 2),
            "std": round(float(s.std()), 2),
            "pass_mark": pass_mark, "pass_pct": round(float((s >= pass_mark).mean() * 100), 1),
        }
        out["charts"]["scores"] = _clean_list(s)
        if "grade" in colmap:
            gc = df[colmap["grade"]].value_counts()
            order = [g for g in ["A", "B", "C", "D", "E", "F"] if g in gc.index]
            order += [g for g in gc.index if g not in order]
            out["charts"]["grades"] = {
                "labels": list(order), "values": [int(gc[g]) for g in order]}
        out["segments"] = _segmentation(df, colmap, seg_high, seg_low)

    if has_att:
        a = pd.to_numeric(df[att_col], errors="coerce").dropna()
        out["kpis"]["avg_attendance"] = round(float(a.mean()), 2)
        out["stats"]["attendance"] = {
            "mean": round(float(a.mean()), 2), "median": round(float(a.median()), 2),
            "min": round(float(a.min()), 2), "max": round(float(a.max()), 2),
            "std": round(float(a.std()), 2),
            "low_pct": round(float((a < 60).mean() * 100), 1),
            "high_pct": round(float((a > 80).mean() * 100), 1),
        }
        out["charts"]["attendance"] = _clean_list(a)
        bands = pd.cut(a, bins=[-0.01, 60, 80, 100.01],
                       labels=["Low (<60%)", "Moderate (60-80%)", "High (>80%)"])
        bc = bands.value_counts()
        out["charts"]["attendance_bands"] = {
            "labels": ["Low (<60%)", "Moderate (60-80%)", "High (>80%)"],
            "values": [int(bc.get(l, 0)) for l in ["Low (<60%)", "Moderate (60-80%)", "High (>80%)"]],
        }

    if has_study:
        h = pd.to_numeric(df[stu_col], errors="coerce").dropna()
        out["kpis"]["avg_study_hours"] = round(float(h.mean()), 2)
        out["stats"]["study"] = {
            "mean": round(float(h.mean()), 2), "median": round(float(h.median()), 2),
            "min": round(float(h.min()), 2), "max": round(float(h.max()), 2),
        }
        out["charts"]["study_hours"] = _clean_list(h)

    # ---- paired relationships ----------------------------------------------
    if has_att and has_score:
        paired = pd.DataFrame({
            "a": pd.to_numeric(df[att_col], errors="coerce"),
            "s": pd.to_numeric(df[score_col], errors="coerce")}).dropna()
        if len(paired) > 2000:
            paired = paired.sample(2000, random_state=42)
        r = float(paired["a"].corr(paired["s"])) if len(paired) > 2 else None
        out["correlation_att_score"] = round(r, 3) if r is not None and not np.isnan(r) else None
        out["charts"]["att_vs_score"] = {
            "x": [round(float(v), 2) for v in paired["a"].tolist()],
            "y": [round(float(v), 2) for v in paired["s"].tolist()],
        }
        g = paired.groupby(pd.cut(paired["a"], bins=[-0.01, 60, 80, 100.01],
                                  labels=["Low (<60%)", "Moderate (60-80%)", "High (>80%)"]),
                           observed=True)["s"].mean()
        out["charts"]["att_band_means"] = {
            "labels": ["Low (<60%)", "Moderate (60-80%)", "High (>80%)"],
            "values": [round(float(g.get(l, float("nan"))), 2) if pd.notna(g.get(l)) else None
                       for l in ["Low (<60%)", "Moderate (60-80%)", "High (>80%)"]],
        }

    if has_study and has_score:
        paired = pd.DataFrame({
            "h": pd.to_numeric(df[stu_col], errors="coerce"),
            "s": pd.to_numeric(df[score_col], errors="coerce")}).dropna()
        if len(paired) > 2000:
            paired = paired.sample(2000, random_state=42)
        r = float(paired["h"].corr(paired["s"])) if len(paired) > 2 else None
        out["correlation_study_score"] = round(r, 3) if r is not None and not np.isnan(r) else None
        out["charts"]["study_vs_score"] = {
            "x": [round(float(v), 2) for v in paired["h"].tolist()],
            "y": [round(float(v), 2) for v in paired["s"].tolist()],
        }
    if has_study and has_att:
        paired = pd.DataFrame({
            "h": pd.to_numeric(df[stu_col], errors="coerce"),
            "a": pd.to_numeric(df[att_col], errors="coerce")}).dropna()
        r = float(paired["h"].corr(paired["a"])) if len(paired) > 2 else None
        out["correlation_study_att"] = round(r, 3) if r is not None and not np.isnan(r) else None

    if has_prev and has_score:
        paired = pd.DataFrame({
            "p": pd.to_numeric(df[colmap["previous_score"]], errors="coerce"),
            "s": pd.to_numeric(df[score_col], errors="coerce")}).dropna()
        r = float(paired["p"].corr(paired["s"])) if len(paired) > 2 else None
        out["correlation_prev_score"] = round(r, 3) if r is not None and not np.isnan(r) else None

    # ---- subjects ------------------------------------------------------------
    if subjects:
        avgs = {}
        for subj in subjects:
            s = pd.to_numeric(df[subj], errors="coerce").dropna()
            if len(s):
                avgs[subj] = round(float(s.mean()), 2)
        out["charts"]["subject_avgs"] = {
            "labels": list(avgs.keys()), "values": list(avgs.values())}
        out["stats"]["subjects"] = avgs

    # ---- group comparisons ----------------------------------------------------
    if has_gender and has_score:
        g = df.groupby(colmap["gender"])[score_col].mean().round(2)
        out["groups"]["gender"] = {"labels": list(g.index.astype(str)), "values": [float(v) for v in g.values]}
    if has_prep and has_score:
        g = df.groupby(colmap["test_prep"])[score_col].agg(["mean", "count"]).round(2)
        out["groups"]["test_prep"] = {
            "labels": list(g.index.astype(str)),
            "values": [float(v) for v in g["mean"].values],
            "counts": [int(v) for v in g["count"].values],
        }
    if has_parent and has_score:
        g = df.groupby(colmap["parental_education"])[score_col].mean().round(2).sort_values()
        out["groups"]["parental"] = {"labels": list(g.index.astype(str)), "values": [float(v) for v in g.values]}

    # ---- correlation matrix of numerics ---------------------------------------
    num_df = df.select_dtypes(include="number")
    # drop helper columns that would confuse beginners
    num_df = num_df[[c for c in num_df.columns if not str(c).startswith("__")]]
    if num_df.shape[1] >= 2:
        corr = num_df.corr(numeric_only=True).round(2)
        corr = corr.fillna(0)
        out["correlation"] = {
            "labels": list(corr.columns),
            "matrix": corr.values.tolist(),
        }

    return out


def _segmentation(df, colmap, seg_high, seg_low):
    """Split students into High / Average / Needs Attention by score."""
    s = pd.to_numeric(df[colmap["final_score"]], errors="coerce")
    labels = pd.cut(s, bins=[-0.01, seg_low - 0.001, seg_high - 0.001, 1000],
                    labels=["Needs Attention", "Average", "High Performer"])
    tmp = df.copy()
    tmp["__seg"] = labels
    rows = []
    for seg in ["Needs Attention", "Average", "High Performer"]:
        sub = tmp[tmp["__seg"] == seg]
        row = {"segment": seg, "count": int(len(sub)),
               "pct": round(len(sub) / len(tmp) * 100, 1) if len(tmp) else 0,
               "avg_score": round(float(sub[colmap["final_score"]].mean()), 2) if len(sub) else 0}
        if "attendance" in colmap and len(sub):
            row["avg_attendance"] = round(float(pd.to_numeric(sub[colmap["attendance"]], errors="coerce").mean()), 2)
        if "study_hours" in colmap and len(sub):
            row["avg_study"] = round(float(pd.to_numeric(sub[colmap["study_hours"]], errors="coerce").mean()), 2)
        rows.append(row)
    return {"rows": rows, "low": seg_low, "high": seg_high,
            "criteria": f"High Performer: score >= {seg_high:g} | "
                        f"Average: {seg_low:g}–{seg_high - 1:g} | "
                        f"Needs Attention: score < {seg_low:g}"}
