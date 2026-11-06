# Raman Tensor Rotation — Version 5

Open **261024 - Raman Tensor Rotation Ver 5.0.ipynb** in Jupyter or Colab.
Run all 22 cells in order. Each cell prints its number, a success message, and the next action.
Cell 22 opens the calculator and the Si (500) example.

## Choose a calculation model

1. **My PPT slide model** — the slide frame and polarization convention.
   Ag Cartesian contributions are displayed separately.
2. **New-san — Paukatong et al.** — Si T₂g and GaAs TO/LO with **VV**, **VH**, or **σ⁺α**.
3. **Dr. Kumar model** — the supplied original 2×2 tensor and QWP optical sequence.

These are the three selectable models in Python and both websites.

## First calculation: New-san

1. Select **New-san**, **Si**, **T₂g**, and **VV**.
2. Keep **d=1** and surface **(500)**.
3. Select **Review inputs**. Check X, Y, Z, T, the tensors, and polarization states.
4. Select **Run calculation**.
5. Open **Step-by-step calculation** or **Polar plots**.

For this example, \(I(\theta)=\sin^2(2\theta)\). The maximum relative intensity is 1.
Choose VH to obtain \(\cos^2(2\theta)\), or σ⁺α to obtain \(\sin^2\alpha\).
The raw intensity and the equation use the same coefficient values.

## Read the mathematical steps

The New-san calculation follows:

1. Original Raman tensors — paper (1)–(3).
2. Surface axes and T — paper (4), SI (S1)–(S2).
3. Rotated tensors — paper (5), SI (S7)–(S9).
   GaAs also uses the phonon-polarization projection, paper (8).
4. Incident and detected Jones states — paper (11).
5. Raman amplitude and intensity — paper (9)–(13), SI (S17)–(S18).
6. Substitute d and draw the polar plot.

Red marks the **analytical expression for the Raman tensor** and the
**analytical expression for the Raman intensity**. Other steps and short
symbol definitions use the normal text color.
The calculation does not display intermediate K₀, Kc, C, or D aliases.

## Surface convention

New-san uses the positive (hkl) normal,
X parallel to [k −h 0], and Y=Z×X. The (001) case uses the original axes.
These axes determine the plot's zero angle. Review inputs shows the actual unit vectors.

For the PPT model, the slide example retains its declared frame.
Enter measured lattice ratios when defining a physical noncubic surface.
Dr. Kumar's original 2×2 source model has no surface input.

## Files

The website downloads contain the same notebook code and scientific functions:
the notebook, Python script, engine, input examples, and documentation.
The result ZIP contains the calculation steps, symbolic LaTeX, curves, and figures.

Full website:
https://faizal-07-script.github.io/rotation-raman-tensor-calculation/

Calculator:
https://faizal-07-script.github.io/raman-tensor-calculator/

Reference: P. Paukatong et al., *Journal of Raman Spectroscopy* **57** (2026),
809–820, DOI **10.1002/jrs.70113**, and its supplementary information.

The GaAs projection uses paper (8) and Cartesian SI (S14)–(S16).
For the SI (S10) YY entry, direct projection gives S₂pC₂q; the printed polar form
has S₂pC₂p. The intensity is obtained from the matrix contraction.
