"""Convert notebook code cells to a standalone analysis.py (no Jupyter needed)."""
import json, pathlib
nb = json.loads(pathlib.Path("notebooks/Student_Performance_Attendance_Analysis.ipynb").read_text(encoding="utf-8"))
codes = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]
header = '"""Student Performance & Attendance Analysis - standalone (no Jupyter needed).\nRun: python analysis.py\nCharts -> visuals/ folder.\n"""\nimport matplotlib\nmatplotlib.use("Agg")  # no popups; charts saved to visuals/\n'
# display() shim for plain python
shim = 'def display(x=None, *a, **k):\n    print(x)\n'
body = "\n\n# ---------- next cell ----------\n".join(codes)
pathlib.Path("analysis.py").write_text(header + shim + body + '\nprint("\\nDONE. Charts in:", VISUAL_DIR)\n', encoding="utf-8")
print("wrote analysis.py,", len(codes), "cells")
