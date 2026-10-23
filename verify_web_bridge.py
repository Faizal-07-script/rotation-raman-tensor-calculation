"""Integration checks for the browser's JSON adapter and scientific downloads."""
import copy
import hashlib
import io
import json
import csv
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if os.environ.get("RAMAN_PYTHON_DEPENDENCY_PATH"):
    sys.path.insert(0, os.environ["RAMAN_PYTHON_DEPENDENCY_PATH"])
ns = {}
exec(compile((ROOT/"dist/raman_engine.py").read_text(), "raman_engine.py", "exec"), ns)
exec(compile((ROOT/"web_bridge.py").read_text(), "web_bridge.py", "exec"), ns)
catalog = ns["web_catalog"]()
started = time.monotonic()
checks = []

def run(config):
    original = copy.deepcopy(config)
    result = json.loads(ns["web_calculate"](json.dumps(config)))
    assert config == original
    assert result["version"] == "4"
    assert result["equation_count"] > 0
    assert result["checks"]
    for channel in result["channels"]:
        assert len(channel["points"]) == len(result["angles"])
        assert all(ns["np"].isfinite(channel["points"]))
        assert min(channel["points"]) >= -1e-13
    return result

sample = json.loads((ROOT / "dist/downloads/example_input_v4.json").read_text())
sample_result = run(sample)
expected_sample = json.loads((ROOT / "dist/data/reference-example.json").read_text())
assert sample_result["equation_count"] == expected_sample["equation_count"]
assert sample_result['configuration']['material']=='Si'
assert sample_result['configuration']['hkl']==[5,0,0]
assert [channel['name'] for channel in sample_result['channels']]==['T2g']
assert len(sample_result["angles"]) == 721
for actual, expected in zip(sample_result["channels"], expected_sample["channels"]):
    assert actual["name"] == expected["name"]
    assert ns["np"].allclose(actual["points"], expected["points"], rtol=1e-12, atol=1e-13)
checks.append("Published example input JSON runs unchanged and reproduces the documented reference output.")

for name, example in catalog["examples"].items():
    result = run(example["config"])
    if name=='SLIDE':
        for channel,maximum in zip(result['channels'],[1/18,2/15,0.075]):
            assert abs(max(channel['points'])-maximum)<1e-10
    checks.append(f"Example {name}: {len(result['channels'])} channels; JSON result, figures and calculated equations.")
    print(checks[-1], flush=True)

for profile in catalog["profiles"]:
    cfg = copy.deepcopy(catalog["examples"]["SLIDE"]["config"])
    cfg.update(optics=profile, show_geometry=False, plot_points=361)
    result = run(cfg)
    checks.append(f"Optical profile {profile}: finite intensities and consistent raw data.")
    print(checks[-1], flush=True)

base = copy.deepcopy(catalog["examples"]["SLIDE"]["config"])
base["paper_parameters"]["m_ph"] = []
base["paper_parameters"]["absorption_delta_m"] = "inactive invalid field"
base["optics"] = "LINEAR_PAIR"
result = run(base)
assert len(result["channels"]) == 6
checks.append("Inactive conditional fields cannot block the paired VV/VH profile.")

invalid = copy.deepcopy(base)
invalid["orientation"] = "matrix"
invalid["T_manual"] = [[-1,0,0],[0,1,0],[0,0,1]]
try:
    run(invalid)
    raise AssertionError("An improper reflection frame was accepted.")
except ValueError:
    checks.append("A reflected manual frame is rejected.")

result = run(catalog["examples"]["SLIDE"]["config"])
for extension, magic in [("png",b"\x89PNG"),("pdf",b"%PDF"),("svg",b"<?xml")]:
    raw = ns["web_download_figure"](0, extension)
    assert raw.startswith(magic), extension
checks.append("Scientific PNG, PDF and SVG figure downloads have valid file signatures.")
ns["web_add_comparison"]()
cfg = copy.deepcopy(catalog["examples"]["SLIDE"]["config"])
cfg["azimuth_deg"] = 20
run(cfg)
ns["web_add_comparison"]()
comparison = json.loads(ns["web_compare"]("Ag(xx)", False))
assert "<svg" in comparison["svg"]
archive = ns["web_export"]()
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert any(name.endswith(".csv") for name in names)
    assert any(name.endswith(".tex") for name in names)
    assert any(name.endswith(".pdf") for name in names)
    assert any(name.endswith(".svg") for name in names)
    assert any(name.endswith(".png") for name in names)
    assert any("comparison" in name.lower() for name in names)
checks.append(f"Full result ZIP: {len(names)} valid entries, including figures, data, mathematics and comparison inputs.")
print(checks[-1], flush=True)

benchmark = json.loads(ns["web_benchmark"](1,361))
assert len(benchmark["cases"]) == 18
with zipfile.ZipFile(io.BytesIO(ns["web_export_benchmark"]())) as z:
    assert z.testzip() is None
    for name in ["Fig1a_VV.csv","Fig1b_VH.csv","Fig1c_sigma_plus_alpha.csv"]:
        rows = list(csv.reader(io.StringIO(z.read(name).decode())))
        assert len(rows[0]) == 7
        assert len(rows) == 362
checks.append("Silicon benchmark: 18 calculated cases pass their independent identities and OriginLab export.")

record = dict(status="passed", version="4", checks=checks,
              elapsed_seconds=round(time.monotonic()-started,2),
              engine_sha256=hashlib.sha256((ROOT/"dist/raman_engine.py").read_bytes()).hexdigest())
(ROOT/"dist/data/web-verification.json").write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2),flush=True)
