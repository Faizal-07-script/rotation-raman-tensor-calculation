Version 4 | Revision 2026-10-23-r2 | Silicon (500) default

The recommended notebook filename includes V4, Si500, the revision and its source fingerprint.
Cell 1 prints this same revision before preparing the environment.
Open the newly downloaded file, then restart its kernel and Run All.
The .py source has 22 # %% cell boundaries for editors that support Python cells.

ROTATION RAMAN TENSOR CALCULATION — PYTHON DOWNLOADS

Current version: 4. Run all 22 cells of the .ipynb in Jupyter or Colab.
The matching .py file contains the complete notebook source for an IPython kernel.
raman_engine.py contains the same scientific functions without notebook-only
display imports; web_bridge.py supplies validated JSON/browser interfaces.

Version 4 uses Greek symbols in the controls, guides and exports, and shorter
instructions. The scientific calculations are unchanged. Optional website guides
remain available from the User guide button.

Newcomers: read QUICKSTART.md and use Restart kernel and Run All.
Every code cell prints "Run completed successfully.", its number, what is ready
and which cell to run next. Each cell also explains its role, inputs and outputs.
Cell 22 loads silicon (500), T2g, d=1, VV, checks its 721-point curve against
the reference equation and displays its polar PNG directly above the controls.
No external input or manual code edit is needed. The Polar plots tab opens first.
Tools are numbered 1-7 for the main workflow, with optional validation (8),
comparisons (9), and the silicon benchmark (10). silicon_startup_input_v4.json
records the Python startup inputs; Silicon_Startup_Polar_Plot.png is the checked
startup figure. The website also starts with Si (500); example_input_v4.json
records the same input configuration. Other material examples remain available.
Symbols_And_References.md collects the symbol definitions, unit conventions and
sources shown directly below every calculated equation in the notebook and website.
The full, symbolic and numerical LaTeX exports include those explanations.
SAITO_FEEDBACK_AUDIT.md distinguishes implemented changes from the still-pending
independent colleague review and documentation consultation with Kumar-san.

The checking-procedures extension records purpose, procedure, expected equation,
status, symbolic residuals or numerical tolerances. Cell 21 implements the
25 source-reference procedures from QWP source reference and their generalization
to the actual selected crystal/Jones run. Cells 16 and 19 export and display
the same reports. Main Ag components and all existing intensity laws are unchanged.
The uploaded original reference notebook is included as a separate, unmodified reference.

The references folder contains the unmodified optical implementation sources.
The live website tutorial displays the exact current Version 4 code.

The site self-hosts its Python WebAssembly runtime and mathematical typesetting.
Its first calculator start downloads the runtime into your browser. A web worker
keeps navigation responsive while the original Python engine calculates.

Model: ideal transverse plane-wave Raman scattering, supplied complex coefficients,
normal backscattering, explicit crystal orientation and actual Jones states.
Material coefficients and noncubic lattice ratios are illustrative until replaced.
Separate Ag Cartesian powers are diagnostics of one phonon and are not summed
in the main figures. A coherent full-mode audit is exported separately.
