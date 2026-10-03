"""Automatic insight + recommendation generation.

Every sentence is computed from the actual uploaded data.
If a column is missing, the related insight is simply skipped --
insights are never hardcoded or fabricated.
"""


def generate_insights(summary, colmap):
    ins = []
    kpis = summary.get("kpis", {})
    stats = summary.get("stats", {})
    has = summary.get("has", {})

    if has.get("score") and "performance" in stats:
        p = stats["performance"]
        ins.append(
            f"Overall performance: mean score {p['mean']:.1f} "
            f"(median {p['median']:.1f}, SD {p['std']:.1f}). "
            f"{p['pass_pct']:.1f}% of students meet the pass mark of {p['pass_mark']:g}."
        )

    if has.get("attendance") and "attendance" in stats:
        a = stats["attendance"]
        ins.append(
            f"Attendance averages {a['mean']:.1f}%: "
            f"{a['low_pct']:.1f}% of students are below 60% (at-risk zone) "
            f"while {a['high_pct']:.1f}% are above 80% (engaged zone)."
        )

    r = summary.get("correlation_att_score")
    if r is not None:
        strength = "weak" if abs(r) < 0.2 else ("modest" if abs(r) < 0.4 else ("moderate" if abs(r) < 0.6 else "strong"))
        direction = "positive" if r >= 0 else "negative"
        ins.append(
            f"Attendance vs score correlation is {r:.2f} ({strength} {direction} association). "
            "Higher attendance tends to coincide with higher scores in this dataset "
            "(association only -- this does not prove attendance causes higher marks)."
        )
        bands = (summary.get("charts", {}).get("att_band_means") or {}).get("values", [])
        if len(bands) == 3 and all(v is not None for v in bands):
            ins.append(
                f"Students with high attendance (>80%) average {bands[2]:.1f}, "
                f"which is {bands[2] - bands[0]:.1f} points above the low-attendance (<60%) group ({bands[0]:.1f})."
            )

    r = summary.get("correlation_study_score")
    if r is not None:
        ins.append(
            f"Study hours vs score correlation is {r:.2f}. "
            + ("Students who study more tend to score higher in this dataset."
               if r > 0.1 else "Study hours show little linear relationship with scores here -- "
                              "study quality/schedule may matter more than raw hours.")
        )

    r = summary.get("correlation_prev_score")
    if r is not None and r >= 0.5:
        ins.append(
            f"Previous score is the strongest single predictor (r = {r:.2f}): "
            "prior attainment carries forward, so early support for low prior scorers pays off."
        )

    tp = summary.get("groups", {}).get("test_prep")
    if tp and len(tp["values"]) >= 2:
        labels, values = tp["labels"], tp["values"]
        try:
            ci = labels.index("Completed")
            ni = labels.index("Not Completed")
            gap = values[ci] - values[ni]
            ins.append(
                f"Test preparation: students who completed prep average {values[ci]:.1f} "
                f"vs {values[ni]:.1f} without prep (gap {gap:+.1f} points)."
            )
        except ValueError:
            best = max(zip(values, labels))
            ins.append(f"Test-preparation group '{best[1]}' averages highest ({best[0]:.1f}).")

    subj = (summary.get("charts", {}).get("subject_avgs")) or {}
    if subj.get("labels"):
        pairs = list(zip(subj["labels"], subj["values"]))
        best = max(pairs, key=lambda x: x[1])
        worst = min(pairs, key=lambda x: x[1])
        ins.append(
            f"Subjects: '{best[0]}' has the highest average ({best[1]:.1f}); "
            f"'{worst[0]}' has the lowest ({worst[1]:.1f}) and is the priority for tutoring support."
        )

    gen = summary.get("groups", {}).get("gender")
    if gen and len(gen["values"]) >= 2:
        pairs = sorted(zip(gen["labels"], gen["values"]), key=lambda x: -x[1])
        ins.append(
            f"Gender comparison: {pairs[0][0]} averages {pairs[0][1]:.1f}, "
            + ", ".join(f"{l} {v:.1f}" for l, v in pairs[1:]) + ". Treat gaps as descriptive, not stereotypes."
        )

    seg = summary.get("segments")
    if seg:
        rows = {r["segment"]: r for r in seg["rows"]}
        need = rows.get("Needs Attention", {})
        high = rows.get("High Performer", {})
        ins.append(
            f"Segmentation ({seg['criteria']}): {need.get('pct', 0):.1f}% need attention "
            f"(avg {need.get('avg_score', 0):.1f}), {high.get('pct', 0):.1f}% are high performers "
            f"(avg {high.get('avg_score', 0):.1f}). The Needs Attention list is the counselling priority."
        )

    r = summary.get("correlation_study_att")
    if r is not None and abs(r) < 0.2:
        ins.append(
            f"Study hours and attendance are nearly independent (r = {r:.2f}), "
            "so they are two separate levers: a student can attend regularly yet study little, or vice versa."
        )

    if not ins:
        ins.append("Dataset loaded. Upload columns with scores, attendance or study hours to unlock deeper insights.")
    return ins


def generate_recommendations(summary):
    recs = []
    stats = summary.get("stats", {})
    has = summary.get("has", {})

    if has.get("attendance") and "attendance" in stats:
        a = stats["attendance"]
        if a["low_pct"] >= 5:
            recs.append(
                f"Flag the {a['low_pct']:.1f}% of students below 60% attendance for fortnightly check-ins; "
                "contact a student after 2 consecutive absences -- attendance is the cheapest leading signal."
            )
        else:
            recs.append("Attendance is broadly healthy; keep routine monitoring and recognise consistently high attenders.")

    subj = (summary.get("charts", {}).get("subject_avgs")) or {}
    if subj.get("labels"):
        worst = min(zip(subj["labels"], subj["values"]), key=lambda x: x[1])
        recs.append(
            f"Prioritise tutoring for '{worst[0]}' (lowest average, {worst[1]:.1f}); "
            "run small-group clinics and re-test after 4 weeks."
        )

    tp = summary.get("groups", {}).get("test_prep")
    if tp and "Completed" in tp["labels"] and "Not Completed" in tp["labels"]:
        gap = tp["values"][tp["labels"].index("Completed")] - tp["values"][tp["labels"].index("Not Completed")]
        if gap > 2:
            recs.append(
                f"Expand free pre-exam preparation (completers score {gap:+.1f} points higher); "
                "offer it first to the Needs Attention segment."
            )

    if has.get("study"):
        recs.append("Encourage steady 4-8 h/week study routines via peer study halls; track study-band migration each term.")

    seg = summary.get("segments")
    if seg:
        need = next((r for r in seg["rows"] if r["segment"] == "Needs Attention"), None)
        if need and need["pct"] > 0:
            recs.append(
                f"Build an early-alert counselling list from the {need['count']} Needs Attention students "
                f"({need['pct']:.1f}%); pair each with a mentor and review monthly."
            )

    if has.get("previous"):
        recs.append("Use previous scores for early flagging in week 1 -- do not wait for the first internal exam.")
    recs.append("Re-run this dashboard each term and track band migrations (Low->Moderate->High) as the KPI.")
    return recs
