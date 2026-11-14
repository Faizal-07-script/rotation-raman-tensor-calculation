"""Prepare the calculator repository from the tested full-website release."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
target = args.output.resolve()
if target == SOURCE:
    raise SystemExit('Choose the separate calculator checkout as --output.')
target.mkdir(parents=True, exist_ok=True)
shutil.copytree(SOURCE / 'dist', target / 'dist', dirs_exist_ok=True, copy_function=shutil.copy)
shutil.copy(SOURCE / 'dist/calculator.html', target / 'dist/index.html')
# Keep the browsable Python sources and checks current in both repositories.
shutil.copytree(SOURCE / 'sources', target / 'sources', dirs_exist_ok=True, copy_function=shutil.copy)
for name in ['scripts', 'validation']:
    shutil.copytree(SOURCE / name, target / name, dirs_exist_ok=True, copy_function=shutil.copy)
for pattern in ['*.py', '*verification.json', 'QUICKSTART.md', 'Saito-sensei feedback.md', 'LAB_MODEL_REVISION.md']:
    for path in SOURCE.glob(pattern):
        shutil.copy(path, target / path.name)
release = json.loads((SOURCE / 'dist/data/release.json').read_text())
assert release['version'] == '5'
for filename in ['raman_engine.py', 'web_bridge.py', 'calculator-ui.js']:
    assert (target / 'dist' / filename).read_bytes() == (SOURCE / 'dist' / filename).read_bytes()
(target / 'README.md').write_text('''# Raman Tensor Calculator — Version 5

[Open the calculator](https://faizal-07-script.github.io/raman-tensor-calculator/)
· [Full website and documentation](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/)

This website opens directly in the calculator. Choose the crystal, surface
(hkl) for the normal Z, in-plane X reference [uvw], and polarization. In
**A · Input review**, select **Check current inputs** to check the axes,
rotated tensors and Jones states. Select **Run calculation** for
**B · Polar plots** and **C · Step-by-step calculation**.

The results include polar plots, the final intensity equation and numbered
matrix steps. English explanations and new symbol definitions appear on the
left; the complete mathematics appears on the right. The two columns stack
on narrow screens. Silicon (500), VV, is the starting example.

The Python notebook is **261024 - Raman Tensor Rotation Ver 5.0**.
The scientific engine and downloads match the full website. Run its 22 cells
in order; each cell prints a completion message. The program ZIP includes
the input examples, documentation and both mathematical export views.

Source and reference notes are available in the full website and the notebook.
See `Saito-sensei feedback.md` for completed work and pending independent review.

## Update

Prepare and test the full release first. From that checkout, run:

```bash
python scripts/prepare_calculator_site.py --output /path/to/raman-tensor-calculator
```

Commit the resulting files in this repository. GitHub Pages publishes `dist/`.
''')
manifest = dict(version='5', source_code_sha256=release['source_sha256'],
                engine_sha256=hashlib.sha256((target/'dist/raman_engine.py').read_bytes()).hexdigest(),
                full_website='https://faizal-07-script.github.io/rotation-raman-tensor-calculation/',
                calculator_website='https://faizal-07-script.github.io/raman-tensor-calculator/')
(target/'calculator-release.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Calculator-only website prepared at', target)
