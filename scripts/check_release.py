"""Check release identity, exact source correspondence and portable static assets."""
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DOWNLOADS = DIST / "downloads"
VERSION = "4"

notebook_bytes = (ROOT / "sources/notebook_v4.ipynb").read_bytes()
book = json.loads(notebook_bytes)
code = ["".join(c["source"]) for c in book["cells"] if c["cell_type"] == "code"]
assert len(code) == 22
for i, source in enumerate(code, 1):
    message = f"Cell {i:02d}/22 — This cell runs correctly."
    assert message in source
    stdout = "".join(o.get("text", "") if isinstance(o.get("text", ""), str) else "".join(o["text"])
                     for o in [c for c in book["cells"] if c["cell_type"] == "code"][i-1].get("outputs", [])
                     if o.get("output_type") == "stream" and o.get("name") == "stdout")
    assert message in stdout, (i, "Missing executed cell confirmation")
digest = hashlib.sha256("\n\n".join(code).encode()).hexdigest()
cells = json.loads((DIST / "data/cells.json").read_text())
assert cells["version"] == VERSION
assert cells["source_sha256"] == digest
assert [c["source"] for c in cells["cells"]] == code
assert (DOWNLOADS / "ROTATION_RAMAN_TENSOR_CALCULATION.ipynb").read_bytes() == notebook_bytes
assert 'AUDIT_VERSION = "4"' in "\n".join(code)
assert "VERSION 4" in (DIST / "index.html").read_text()
assert "version: '4'" in (DIST / "engine-worker.js").read_text()

tutorial = json.loads((DIST / "data/tutorial.json").read_text())
assert sorted(c["cell"] for c in tutorial) == list(range(1, 23))
for cell in tutorial:
    source_lines = code[cell["cell"] - 1].splitlines()
    covered = set()
    for block in cell["blocks"]:
        assert 1 <= block["start_line"] <= block["end_line"] <= len(source_lines)
        covered.update(range(block["start_line"], block["end_line"] + 1))
    assert all(i in covered for i, line in enumerate(source_lines, 1) if line.strip())

with zipfile.ZipFile(DOWNLOADS / "All_Python_Programs.zip") as archive:
    assert archive.testzip() is None
    assert archive.read("ROTATION_RAMAN_TENSOR_CALCULATION.ipynb") == notebook_bytes
    for name in ["ROTATION_RAMAN_TENSOR_CALCULATION.py", "raman_engine.py", "web_bridge.py"]:
        assert archive.read(name) == (DOWNLOADS / name).read_bytes()
    for name in ["QUICKSTART.md", "SAITO_FEEDBACK_AUDIT.md", "example_input_v4.json"]:
        assert archive.read(name) == (DOWNLOADS / name).read_bytes()

assert (DOWNLOADS / "example_input_v4.json").read_bytes() == (ROOT / "sources/example_input_v4.json").read_bytes()
sample = json.loads((DOWNLOADS / "example_input_v4.json").read_text())
reference = json.loads((DIST / "data/reference-example.json").read_text())
assert sample == reference["configuration"]
assert len(reference["angles"]) == 721
assert reference["equation_count"] == 271
assert [c["name"] for c in reference["channels"]] == ["Ag(xx)", "Ag(yy)", "Ag(zz)"]
for c, expected in zip(reference["channels"], [1/18, 2/15, 0.075]):
    assert abs(max(c["points"]) - expected) < 1e-10

for name in ["index.html", "app.js", "styles.css", "engine-worker.js", "user-guide.js", "user-guide.css"]:
    text = (DIST / name).read_text()
    assert not re.search(r'''(?:src|href)=["']/[^/]''', text), name
    assert not re.search(r'''(?:fetch|Worker|importScripts)\(["']/[^/]''', text), name
for name in ["raman_engine.py", "web_bridge.py", "vendor/pyodide/pyodide.js", "vendor/pyodide/pyodide.asm.wasm"]:
    assert (DIST / name).is_file(), name

assert (DIST / "user-guide.js").is_file()
assert (DIST / "user-guide.css").is_file()
assert 'id="user-guide-open"' in (DIST / "index.html").read_text()
assert "user-guide.js?v=4" in (DIST / "index.html").read_text()
assert 'aria-expanded="false"' in (DIST / "index.html").read_text()
for name in ["index.html", "app.js", "content.js", "optical-guide.js", "engine-worker.js"]:
    assert not re.search(r"(?i)version[ _]*2(?:\b|[._])", (DIST / name).read_text()), name
for name in ["index.html", "app.js", "content.js", "optical-guide.js", "engine-worker.js", "user-guide.js"]:
    assert not re.search(r"(?i)version[ _]*3(?:\b|[._])", (DIST / name).read_text()), name
assert not (ROOT / "sources/notebook_v3.ipynb").exists()
assert not (DOWNLOADS / "example_input_v3.json").exists()
print(f"Version {VERSION}: 22 cells, exact notebook/download/ZIP correspondence and portable static paths passed.")
