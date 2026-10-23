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
    message = f"Cell {i:02d}/22 — Run completed successfully."
    assert message in source
    stdout = "".join(o.get("text", "") if isinstance(o.get("text", ""), str) else "".join(o["text"])
                     for o in [c for c in book["cells"] if c["cell_type"] == "code"][i-1].get("outputs", [])
                     if o.get("output_type") == "stream" and o.get("name") == "stdout")
    assert message in stdout, (i, "Missing executed cell confirmation")
    assert 'Ready:' in stdout and 'Next:' in stdout
digest = hashlib.sha256("\n\n".join(code).encode()).hexdigest()
cells = json.loads((DIST / "data/cells.json").read_text())
assert cells["version"] == VERSION
assert cells["source_sha256"] == digest
assert [c["source"] for c in cells["cells"]] == code
assert (DOWNLOADS / "ROTATION_RAMAN_TENSOR_CALCULATION.ipynb").read_bytes() == notebook_bytes
assert 'AUDIT_VERSION = "4"' in "\n".join(code)
release = json.loads((DIST / 'data/release.json').read_text())
revision = book['metadata']['rotation_raman_revision']['download_revision']
assert release['version'] == VERSION and release['revision'] == revision
assert release['source_sha256'] == digest
assert f'NOTEBOOK_REVISION = "{revision}"' in code[0]
assert release['default_input'] == dict(material='Si',hkl=[5,0,0],optics='CUBIC_VV')
for name, record in release['files'].items():
    payload = (DOWNLOADS / record['filename']).read_bytes()
    assert record['filename'].startswith('Raman_Tensor_V4_Si500_')
    assert hashlib.sha256(payload).hexdigest() == record['sha256']
    assert len(payload) == record['size_bytes']
    if name != 'bundle':
        assert payload == (DOWNLOADS / record['canonical']).read_bytes()
with zipfile.ZipFile(DOWNLOADS / release['files']['bundle']['filename']) as named_bundle:
    assert named_bundle.testzip() is None
    for name in ['notebook','python']:
        record = release['files'][name]
        assert named_bundle.read(record['filename']) == (DOWNLOADS / record['filename']).read_bytes()
    assert 'ROTATION_RAMAN_TENSOR_CALCULATION.ipynb' not in named_bundle.namelist()
assert (DOWNLOADS / 'RELEASE_MANIFEST.json').read_bytes() == (DIST / 'data/release.json').read_bytes()
python_source = (DOWNLOADS / release['files']['python']['filename']).read_text()
assert len(re.findall(r'^# %% Code cell \d+:', python_source, re.M)) == 22
for name in ['app.js','content.js','optical-guide.js','user-guide.js','styles.css','user-guide.css']:
    fingerprint = hashlib.sha256((DIST / name).read_bytes()).hexdigest()[:12]
    assert f'./{name}?v=4-{fingerprint}' in (DIST / 'index.html').read_text()
assert "VERSION 4" in (DIST / "index.html").read_text()
assert "version: '4'" in (DIST / "engine-worker.js").read_text()

startup = book['metadata']['rotation_raman_revision']['validation']['startup_test']
assert startup['material'] == 'Si' and startup['optics'] == 'CUBIC_VV'
assert startup['hkl'] == [5, 0, 0] and startup['samples'] == 721
assert startup['maximum_residual'] < 1e-10 and not startup['inline_png_before_interface']
assert startup['short_guide_before_interface'] and startup['polar_plot_in_result_tab']
last = [c for c in book['cells'] if c['cell_type'] == 'code'][-1]
startup_images = [o for o in last['outputs'] if 'raman_startup_plot' in o.get('metadata', {})]
assert not startup_images
guide = next(o for o in last['outputs'] if o.get('metadata', {}).get('raman_quick_start'))
guide_text = guide['data']['text/markdown']
guide_text = guide_text if isinstance(guide_text,str) else ''.join(guide_text)
assert '**Goal:**' in guide_text
assert len(guide_text.split()) < 100
assert (DOWNLOADS / 'Silicon_Startup_Polar_Plot.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')

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
    for name in ["QUICKSTART.md", "SAITO_FEEDBACK_AUDIT.md", "example_input_v4.json", "silicon_startup_input_v4.json", "Silicon_Startup_Polar_Plot.png", "Symbols_And_References.md"]:
        assert archive.read(name) == (DOWNLOADS / name).read_bytes()

silicon = json.loads((DOWNLOADS / "silicon_startup_input_v4.json").read_text())
assert silicon == json.loads((ROOT / "sources/silicon_startup_input_v4.json").read_text())
assert silicon['material'] == 'Si' and silicon['optics'] == 'CUBIC_VV'
assert silicon['hkl'] == [5, 0, 0] and silicon['modes'] == ['T2g']

assert (DOWNLOADS / "example_input_v4.json").read_bytes() == (ROOT / "sources/example_input_v4.json").read_bytes()
sample = json.loads((DOWNLOADS / "example_input_v4.json").read_text())
reference = json.loads((DIST / "data/reference-example.json").read_text())
assert sample == reference["configuration"]
assert len(reference["angles"]) == 721
assert reference['configuration']==silicon
assert [c["name"] for c in reference["channels"]] == ["T2g"]
assert abs(max(reference['channels'][0]['points'])-1)<1e-10
assert abs(reference['channels'][0]['points'][90]-1)<1e-10
assert abs(reference['channels'][0]['points'][180])<1e-10
equations=[entry for entry in reference['equations'] if entry['kind']=='equation']
assert len(equations)==reference['equation_count']
assert all(entry.get('symbols') and entry.get('reference_ids') for entry in equations)
assert all(s['meaning'] and s['units'] for entry in equations for s in entry['symbols'])
catalog=json.loads((DIST/'data/catalog.json').read_text())
assert catalog['default_example']=='SI_500'
assert catalog['examples']['SI_500']['config']==silicon
assert reference['latex']['full'].count('Symbols and units')==len(equations)
assert 'Run completed successfully.' not in (DIST/'raman_engine.py').read_text()

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
