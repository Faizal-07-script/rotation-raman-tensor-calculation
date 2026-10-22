"""Verify the original upload, new evidence reports, failure detection and exports."""
import ast
import copy
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
QA=ROOT/"validation"
QA.mkdir(exist_ok=True)
if os.environ.get("RAMAN_PYTHON_DEPENDENCY_PATH"):
    sys.path.insert(0,os.environ["RAMAN_PYTHON_DEPENDENCY_PATH"])
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

started=time.monotonic()
original=json.loads((ROOT/"sources/dr_kumar_original.ipynb").read_text())
shell=InteractiveShell.instance()
executed=0
source_prints=[]
for index,cell in enumerate(original["cells"],1):
    if cell["cell_type"]!="code":continue
    with capture_output() as captured:
        result=shell.run_cell("".join(cell["source"]),store_history=False)
    assert result.success,(index,captured.stdout,captured.stderr)
    assert "False" not in captured.stdout,(index,captured.stdout)
    source_prints.append(f"Notebook cell {index}:\n"+captured.stdout)
    executed+=1
    shell.user_ns.get("plt").close("all")
assert executed==20
(QA/"original_notebook_execution.txt").write_text("\n".join(source_prints))
print("Executed all 20 code cells of the unmodified QWP source reference upload.",flush=True)

ns={}
exec(compile((ROOT/"dist/raman_engine.py").read_text(),"engine.py","exec"),ns)
exec(compile((ROOT/"web_bridge.py").read_text(),"web_bridge.py","exec"),ns)
reference=ns["validate_optical_reference"]()
assert reference["status"]=="passed" and reference["passed"]==reference["total"]==25
assert reference["rows"][-1]["evidence"]["rejected"]==[True,True,True]
checks=["All 20 original code cells execute; no printed False check.",
        "25 structured reference procedures pass, including exact identities and seeded independent numerical paths.",
        "Missing conjugation, wrong interference sign and injected dark intensity are all rejected."]
print(checks[-2],flush=True)

for optics in ns["GENERAL_PROFILES"]:
    cfg=ns["slide_component_config"]()
    cfg.update(optics=optics,plot_points=361,show_geometry=False)
    run=ns["calculate_general"](cfg)
    report=ns["checking_procedures_for_run"](run)
    assert report["status"]=="passed",(optics,report)
    assert any(r["id"]=="G-SOURCE" and r["status"]=="not applicable" for r in report["rows"])
checks.append("Current-run checks pass for all nine optical profiles without imposing the source-only law on a crystal.")

for builder in ["qwp_source_config","linear_bp_reference_config","circular_mos2_reference_config"]:
    run=ns["calculate_general"](ns[builder]())
    assert ns["checking_procedures_for_run"](run)["status"]=="passed"
checks.append("Source 2D, complex BP and degenerate MoS2 examples pass their applicable checking procedures.")

cfg=ns["slide_component_config"]()
for symbol in cfg["mode_values"]["Ag"]:cfg["mode_values"]["Ag"][symbol]*=1000000
large=ns["checking_procedures_for_run"](ns["calculate_general"](cfg))
assert large["status"]=="passed"
checks.append("Large coefficient scale passes the norm/completeness audit with a scale-aware tolerance.")

good=ns["calculate_general"](ns["slide_component_config"]())
bad=copy.deepcopy(good)
next(iter(bad["display_channels"].values()))["curve"][0]+=1e-5
tampered=ns["checking_procedures_for_run"](bad)
assert tampered["status"]=="failed"
assert any(r["status"]=="failed" and r["id"].endswith("c") for r in tampered["rows"])
reflected=copy.deepcopy(good)
reflected["geometry"]["T"]=reflected["geometry"]["T"]*ns["sp"].diag(-1,1,1)
assert ns["checking_procedures_for_run"](reflected)["status"]=="failed"
return_backup=ns["QWP_RETURN_QWP"]
try:
    ns["QWP_RETURN_QWP"]=ns["sp"].eye(2)
    assert ns["validate_optical_reference"]()["status"]=="failed"
finally:
    ns["QWP_RETURN_QWP"]=return_backup
checks.append("Actual tampering is detected: altered plotted point, reflected frame and wrong return QWP all fail.")
assert ns["validate_optical_reference"]()["status"]=="passed"

catalog=ns["web_catalog"]()
result=json.loads(ns["web_calculate"](json.dumps(catalog["examples"]["SLIDE"]["config"])))
assert result["checking_report"]["status"]=="passed"
full=json.loads(ns["web_validate"]())
assert full["status"]=="passed" and full["optical_reference"]["passed"]==25
checks.append(f"The existing {len(full['checks'])} model checks and all new source-reference procedures pass together.")
archive=ns["web_export"]()
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    assert z.testzip() is None
    for name in ["checking_procedures.json","checking_procedures.md",
                 "optical_reference_validation.json","optical_reference_validation.md"]:
        assert name in z.namelist(),name
    assert json.loads(z.read("checking_procedures.json"))==result["checking_report"]
    assert json.loads(z.read("optical_reference_validation.json"))==full["optical_reference"]
checks.append("The result ZIP contains identical UI/export evidence in JSON and Markdown, with unchanged scientific figure formats.")

baseline=ROOT/"browser_verification.json"
old_curve=ROOT/"validation/reference_intensity.csv"
assert result["csv"].splitlines()==old_curve.read_text().splitlines()
checks.append("The separate Ag reference intensity arrays are unchanged.")
record=dict(status="passed",checks=checks,source_sha256=hashlib.sha256((ROOT/"sources/dr_kumar_original.ipynb").read_bytes()).hexdigest(),
            elapsed_seconds=round(time.monotonic()-started,2),reference=reference)
(QA/"verification.json").write_text(json.dumps(ns["serializable"](record),indent=2))
(ROOT/"checking_procedures_verification.json").write_text(json.dumps(ns["serializable"](record),indent=2))
print(json.dumps({k:v for k,v in record.items() if k!="reference"},indent=2),flush=True)
