"""Execute all code cells of the notebook headlessly to verify no errors."""
import json, os, sys, traceback
import matplotlib
matplotlib.use("Agg")

NB = "notebooks/Student_Performance_Attendance_Analysis.ipynb"
WORKDIR = "notebooks"
os.makedirs("visuals", exist_ok=True)

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
print(f"Found {len(code_cells)} code cells")

# minimal jupyter shim
def display(x=None, *a, **k):
    try:
        print(str(x)[:2000])
    except Exception:
        pass

ns = {"display": display, "__name__": "__main__"}
os.chdir(WORKDIR)
failures = 0
for i, cell in enumerate(code_cells):
    src = "".join(cell["source"])
    print(f"\n===== CELL {i+1}/{len(code_cells)} =====")
    try:
        exec(compile(src, f"<cell-{i+1}>", "exec"), ns)
        print(f"CELL {i+1} OK")
    except Exception:
        failures += 1
        print(f"CELL {i+1} FAILED")
        traceback.print_exc()
        break

print(f"\nDone. failures={failures}")
print("VISUALS:", sorted(os.listdir(ns.get("VISUAL_DIR", "../visuals"))))
sys.exit(1 if failures else 0)
