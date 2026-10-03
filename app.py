"""EduMetrics -- Student Performance Analytics web app.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000

Flow: CSV upload (runtime) -> pandas -> validate -> clean ->
        analyse -> /dashboard (Plotly charts) -> insights -> HTML report.
"""
import io
import os
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from analysis.analytics import compute_dashboard
from analysis.data_cleaning import clean_dataframe
from analysis.insights import generate_insights, generate_recommendations

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SAMPLE_PATH = os.path.join(BASE_DIR, "data", "StudentPerformanceFactors.csv")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# Simple single-user state (beginner-friendly; use a DB for multi-user prod).
STATE = {"filename": None, "quality": None, "summary": None,
         "insights": [], "recommendations": [], "df": None, "colmap": None}


def _process_dataframe(df_raw, filename):
    """Clean + analyse. Raises ValueError with a friendly message on failure."""
    if df_raw.shape[1] < 2:
        raise ValueError("Need at least 2 columns (e.g. attendance + score).")
    if len(df_raw) < 3:
        raise ValueError("Need at least 3 student rows for analysis.")
    df, colmap, quality = clean_dataframe(df_raw)
    summary = compute_dashboard(df, colmap)
    if not summary["has"].get("score") and not summary["has"].get("attendance"):
        raise ValueError(
            "Could not find a score/marks column or an attendance column. "
            f"Detected columns: {', '.join(map(str, df_raw.columns))}")
    STATE.update({
        "filename": filename, "quality": quality, "summary": summary,
        "insights": generate_insights(summary, colmap),
        "recommendations": generate_recommendations(summary),
        "df": df, "colmap": colmap,
    })
    return quality, summary


def _read_csv_storage(file_storage):
    try:
        raw = file_storage.read()
        text = raw.decode("utf-8-sig")
    except Exception:
        raise ValueError("Could not read the file. Please upload a valid UTF-8 CSV file.")
    try:
        # keep_default_na=False so a category literally called "None" is not eaten as NaN
        return pd.read_csv(io.StringIO(text), keep_default_na=False,
                           na_values=["", " ", "NA", "N/A", "NaN", "nan", "NULL", "null", "#NA"])
    except Exception:
        raise ValueError("Could not parse the CSV. Check it has a header row and comma separators.")


# ---------------------------------------------------------------- pages ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload")
def upload_page():
    return render_template("upload.html")


@app.route("/dashboard")
def dashboard_page():
    if STATE["summary"] is None:
        return redirect(url_for("upload_page"))
    return render_template("dashboard.html", filename=STATE["filename"])


@app.route("/about")
def about_page():
    return render_template("about.html")


# ---------------------------------------------------------------- api -----
@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file received. Please choose a CSV file."}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"ok": False, "error": "No file selected."}), 400
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"ok": False, "error": "Please upload a valid CSV file (.csv only)."}), 400
    try:
        df_raw = _read_csv_storage(f)
        # keep a copy for audit
        safe = "".join(c for c in f.filename if c.isalnum() or c in ("-", "_", "."))[-60:] or "upload.csv"
        df_raw.to_csv(os.path.join(UPLOAD_DIR, safe), index=False)
        quality, _ = _process_dataframe(df_raw, f.filename)
        return jsonify({"ok": True, "redirect": url_for("dashboard_page"),
                        "rows": quality["rows_after"], "columns": quality["columns"]})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception:
        return jsonify({"ok": False, "error": "Unexpected error while processing. Try the sample CSV first."}), 500


@app.route("/api/demo", methods=["POST"])
def api_demo():
    try:
        if not os.path.exists(SAMPLE_PATH):
            return jsonify({"ok": False, "error": "Sample file not found in data/."}), 404
        df_raw = pd.read_csv(SAMPLE_PATH, keep_default_na=False,
                             na_values=["", " ", "NA", "N/A", "NaN", "nan", "NULL", "null", "#NA"])
        quality, _ = _process_dataframe(df_raw, "StudentPerformanceFactors.csv (demo)")
        return jsonify({"ok": True, "redirect": url_for("dashboard_page"),
                        "rows": quality["rows_after"], "columns": quality["columns"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/dashboard-data")
def api_dashboard_data():
    if STATE["summary"] is None:
        return jsonify({"ok": False, "error": "No dataset loaded. Upload a CSV first."}), 404
    return jsonify({"ok": True, "filename": STATE["filename"], "quality": STATE["quality"],
                    "summary": STATE["summary"], "insights": STATE["insights"],
                    "recommendations": STATE["recommendations"]})


# --------------------------------------------------------------- report ---
@app.route("/download-report")
def download_report():
    if STATE["summary"] is None:
        return redirect(url_for("upload_page"))
    s, q = STATE["summary"], STATE["quality"]
    k = s["kpis"]
    rows = [
        f"<tr><td>Total students</td><td>{k.get('total_students', '-')}</td></tr>",
        f"<tr><td>Average score</td><td>{k.get('avg_score', '-')}</td></tr>",
        f"<tr><td>Average attendance</td><td>{k.get('avg_attendance', '-')}</td></tr>",
        f"<tr><td>Average study hours/week</td><td>{k.get('avg_study_hours', '-')}</td></tr>",
        f"<tr><td>Pass percentage</td><td>{k.get('pass_pct', '-')}</td></tr>",
    ]
    ins = "".join(f"<li>{x}</li>" for x in STATE["insights"])
    rec = "".join(f"<li>{x}</li>" for x in STATE["recommendations"])
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>EduMetrics Analysis Report</title>
<style>body{{font-family:Arial,sans-serif;max-width:800px;margin:32px auto;padding:0 16px;color:#1f2937}}
h1{{color:#1d4ed8}}h2{{color:#1d4ed8;border-bottom:2px solid #dbeafe;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #e5e7eb;padding:8px}}li{{margin:6px 0}}
.badge{{background:#dbeafe;color:#1d4ed8;padding:2px 10px;border-radius:999px;font-size:12px}}</style></head>
<body><h1>EduMetrics Analysis Report</h1>
<p>File: <b>{STATE['filename']}</b> &nbsp;<span class="badge">{datetime.now():%Y-%m-%d %H:%M}</span></p>
<h2>Dataset summary</h2>
<p>Rows uploaded: {q['rows_uploaded']} | Rows after cleaning: {q['rows_after']} |
Missing values: {q['missing_values']} | Duplicates removed: {q['duplicates_removed']}</p>
<h2>KPIs</h2><table>{''.join(rows)}</table>
<h2>Key insights</h2><ol>{ins}</ol>
<h2>Recommendations</h2><ol>{rec}</ol>
<p><i>Correlation does not imply causation. Generated by EduMetrics.</i></p></body></html>"""
    path = os.path.join(BASE_DIR, "reports", "EduMetrics_Report.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return send_file(path, as_attachment=True, download_name="EduMetrics_Report.html")


if __name__ == "__main__":
    app.run(debug=True)
