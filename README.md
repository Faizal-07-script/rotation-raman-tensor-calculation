# Rotation Raman Tensor Calculation — Version 5

Current revision: **6 November 2026 — three laboratory models**: My PPT slides; New-san (VV, VH, σ⁺α); Dr. Kumar. Paper-order mathematical steps; analytical tensor and intensity expressions in red. See [revision notes](LAB_MODEL_REVISION.md).

**Release Version 5: Clearer Calculator and Complete Mathematical Steps**

[Full website](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/)
· [Calculator-only website](https://faizal-07-script.github.io/raman-tensor-calculator/)

[Download the current Python notebook](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/261024%20-%20Raman%20Tensor%20Rotation%20Ver%205.0.ipynb?sha=6526c64fb8ce)
· [Download all Python programs](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/261024%20-%20Raman%20Tensor%20Rotation%20Ver%205.0.zip?sha=80033bb09849)

The full website contains the introduction, optical-method notes, references,
22-cell Python tutorial and calculator. The separate `raman-tensor-calculator`
repository publishes a simpler page that opens directly in the calculator.

## First run

Open **261024 - Raman Tensor Rotation Ver 5.0.ipynb** in Jupyter or Colab and
run all 22 cells in order. Each cell prints its number and a completion message.
The initial example is silicon (500), VV, with T2g coefficient d=1. Its polar
plot appears in Cell 22. The matching Python file and input JSON are in the ZIP.

In the website, choose the crystal, tensor, surface, in-plane X direction and
polarization. Y is calculated from Z × X. Select **Review inputs** to inspect
the axes, frame matrix, rotated tensors and Jones states before calculating.
Then select **Run calculation**.

## Mathematical results

Numbered steps show the direct and reciprocal lattice, X/Y/Z axes, frame
checks, complete tensor rotation, optical matrix products, detected amplitude
and final intensity. Tensor coefficients stay explicit; intermediate K, C
and D aliases are not used. The English explanation and new symbol definitions
appear on the left, with the mathematics on the right. On a phone, the two
columns stack. A mathematics-only view is also available.

Cartesian and polar plots use the same sampled intensities and normalization.
The result ZIP contains CSV data, figures, both derivation views and symbolic
LaTeX. Individual equations can be copied as LaTeX. Separate Ag Cartesian
powers are shown as contributions of one phonon; their powers are not added
as if they were separate modes. Unresolved orthogonal phonon components are
summed as intensities.

## Program and sources

- `sources/notebook_v5.ipynb`: current notebook, including saved outputs.
- `dist/downloads/`: matching notebook, complete Python source and program ZIP.
- `dist/raman_engine.py`: scientific functions extracted from the notebook.
- `web_bridge.py`: browser input validation and result exports.
- `QUICKSTART.md`: input instructions, default values and a colleague test checklist.
- `Saito-sensei feedback.md`: completed improvements and pending external review.

The reference notebooks supplied for this project remain attributed and
available separately as `sources/dr_kumar_original.ipynb` and
`sources/original_optical_reference.ipynb`. They are not included in the new
program ZIP. Physical references and conventions are listed in the website
and `Symbols_And_References.md`.

The calculation assumes ideal transverse plane waves, normal backscattering
and the supplied complex tensor coefficients. Unknown material coefficients
and lattice ratios must be entered from the experiment or a suitable source.
Numerical agreement checks test the stated model and conventions.

## Build and check

```bash
python validate_notebook.py
python prepare_content.py
python verify_web_bridge.py
python verify_explicit_derivation.py
python scripts/check_release.py
node scripts/check_notation.cjs
```

The GitHub Pages workflow publishes `dist/`. To prepare the separate calculator
checkout from this release, run `python scripts/prepare_calculator_site.py
--output /path/to/raman-tensor-calculator` on one line.
