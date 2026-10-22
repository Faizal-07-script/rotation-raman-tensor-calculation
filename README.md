# Rotation Raman Tensor Calculation — Version 3

[**Open the live website on GitHub Pages**](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/)

[Download the current Python notebook](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/ROTATION_RAMAN_TENSOR_CALCULATION.ipynb)
· [Download all Python programs](https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/All_Python_Programs.zip)

An English Raman tensor workspace with nested navigation, an exact 22-cell
Python tutorial, the original scientific calculation engine, calculated
derivations, polar plots and scientific exports.

## Structure

- dist/: complete buildless static application.
- sources/notebook_v3.ipynb: current notebook, including executed outputs.
- sources/tutorial_*.json: explanations covering every nonblank source line.
- sources/reference notebooks: unmodified implementation references.
- prepare_content.py: extracts the tutorial, scientific functions and downloads.
- web_bridge.py: strict JSON input adapter and calculated-output formatting.
- verify_web_bridge.py: scientific adapter/export integration checks.
- notebook_verification.json, browser_verification.json and
  dist/data/web-verification.json: validation records and their scope.

The public directory needs no JavaScript build or server-side Python.
A browser worker loads self-hosted Pyodide, NumPy, SymPy and Matplotlib.
The first scientific calculation downloads about 29 MB of runtime dependencies.
Navigation and documentation work before Python starts.

Install dist/downloads/requirements.txt in a Python environment before
regenerating assets with python prepare_content.py. If dependencies are
installed in a separate directory, set RAMAN_PYTHON_DEPENDENCY_PATH to it.
Rebuilding preserves the original function source; only rich notebook display
imports are omitted in the browser engine.

## Optional interactive user guide

The header's **User guide** button opens a workspace tour, the current-page
walkthrough, calculator input and result tours, and guides for every Introduction,
Physics and Python-cell page. **Guide this page** is available on each page.
Guidance supports Next/Back, step selection, close/skip, replay and resume.
Guide progress and optional section prompts are stored only in this browser.
A tour never changes coefficients, loads an example, runs Python, exports data,
or alters a scientific result. It can open a menu, explanatory panel or result tab.
The application remains usable without taking a tour.

## Optical-profile guide

Home includes the physics comparison of all nine profiles, explicit sample Jones
states, return-optic matrices, scan meanings, interference terms and a table for
choosing a reference. The guide is generated from Cell 5 of the same notebook.
The notebook shows the overview and a calculated common-tensor comparison in
an expandable panel; the selected-profile guide follows the optical control.
Cell 16 exports the selected guide and effective parameters with each result.
The guide separates equations reproduced from the references from program
derivations and from experimental calibration. Fixed laboratory circular labels
are distinguished from propagation-relative helicity. The core intensity law
and separate Ag component presentation are preserved.

## Scientific contract

The crystal tensor is 3 by 3. Frame columns are the measurement axes in crystal
coordinates, so R_lab = T.T * R_crystal * T. A transverse restriction follows
the full rotation. The complex amplitude uses the conjugate detection state.
Actual Jones states determine which optical profiles agree.

The main Ag figures show separate Cartesian contribution powers as requested.
The coherent complete-mode response and its interference terms remain in the
audit exports. These components are not independent phonons. Orthogonal
unresolved degenerate partners are combined as intensities.

Material presets describe the stated parent phase and axes; complex
coefficients and noncubic lattice ratios remain declared sample inputs.
The model is an ideal transverse plane-wave calculation. It does not include
finite numerical aperture, birefringent propagation or a microscopic
resonance calculation inferred from a material name.

## Validation

The checking-procedures extension follows the supplied QWP source reference
notebook (20 code cells, all executed in verification). Cell 21 contains
25 structured reference procedures, including explicitly identified
periodicity, dark-source and deliberate-error extensions. Every report
states purpose, procedure, expected equation, scope, status and evidence.
The current-run generalization checks the actual material/Jones inputs.
Source-specific identities are not applied to another crystal tensor.

Cell 19 displays the reports and Cell 16 exports matching JSON/Markdown.
The website has Checking procedures and Reference validation views plus
an introduction guide. The original upload is preserved as
sources/dr_kumar_original.ipynb and a separate downloadable reference.
checking_procedures_verification.json records the source execution,
all-nine-profile checks, false-result injection tests and export equality.

The notebook and extracted source share a recorded SHA-256. All 22 cells run
successfully. The independent model suite checks tensor symmetry, full 3D
complex contractions, reference equations, state conventions, interference,
the implemented 21 point groups, symbolic equations and numerical edge cases.

The web adapter additionally checks six presets, nine optical profiles,
inactive conditional fields, rejection of a reflected frame, frozen-input
comparison, ZIP integrity and PNG/PDF/SVG signatures.

Browser QA covers every introduction, tutorial and physics page, direct
calculations, model/material/surface controls, the full validation suite and
the 18-case silicon benchmark. A browser-generated VV/VH CSV was downloaded
and inspected. ZIP retrieval through the cloud-browser download harness timed
out; archive contents and scientific figure formats were independently
validated in native Python. Origin execution requires an Origin installation
and was not performed here.

Runtime snapshots are session-local. Stop terminates the Python worker and
clears its comparisons, benchmark and validation records. A new calculation
starts a fresh worker. Downloaded results are independent files.

## GitHub Pages

The `.github/workflows/pages.yml` workflow checks the Version 3 release and
publishes `dist/` to GitHub Pages. See [GITHUB_PAGES.md](GITHUB_PAGES.md) for
repository configuration. The scientific runtime and all assets use relative
paths and support a repository subdirectory.

## Third-party software

The application self-hosts Pyodide 0.29.3, KaTeX 0.16.22 and highlight.js
11.11.1. Their notices are retained under dist/vendor/; scientific wheels
retain their own distribution metadata and licenses. Primary physics
references are linked from the website.
