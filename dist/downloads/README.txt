ROTATION RAMAN TENSOR CALCULATION — PYTHON DOWNLOADS

Current version: 3. Run all 22 cells of the .ipynb in Jupyter or Colab.
The matching .py file contains the complete notebook source for an IPython kernel.
raman_engine.py contains the same scientific functions without notebook-only
display imports; web_bridge.py supplies validated JSON/browser interfaces.

Version 3 adds optional interactive website guides and updates release identity.
The guide is separate from the scientific Python engine.
The scientific tensor, rotation and Jones intensity functions are preserved.

The checking-procedures extension records purpose, procedure, expected equation,
status, symbolic residuals or numerical tolerances. Cell 21 implements the
25 source-reference procedures from QWP source reference and their generalization
to the actual selected crystal/Jones run. Cells 16 and 19 export and display
the same reports. Main Ag components and all existing intensity laws are unchanged.
The uploaded original reference notebook is included as a separate, unmodified reference.

The references folder contains the unmodified optical implementation sources.
The live website tutorial displays the exact current Version 3 code.

The site self-hosts its Python WebAssembly runtime and mathematical typesetting.
Its first calculator start downloads the runtime into your browser. A web worker
keeps navigation responsive while the original Python engine calculates.

Model: ideal transverse plane-wave Raman scattering, supplied complex coefficients,
normal backscattering, explicit crystal orientation and actual Jones states.
Material coefficients and noncubic lattice ratios are illustrative until replaced.
Separate Ag Cartesian powers are diagnostics of one phonon and are not summed
in the main figures. A coherent full-mode audit is exported separately.
