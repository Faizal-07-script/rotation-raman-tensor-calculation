# Raman Tensor Rotation — Version 5

Run the 22 notebook cells in order. Each cell prints its number, a completion message, what is ready and the next action. Cell 22 opens Silicon (500), T₂g, d = 1, VV and checks the result.

## Choose inputs

1. Choose **Model 1 — New-san**, **Model 2 — My PPT slide**, or **Model 3 — Dr. Kumar**.
2. Choose **VV**, **VH**, or **σ⁺α**. These choices are available in every model.
3. Select a material, Raman mode and tensor values. Silicon and GaAs are separate cubic materials; GaAs is not a silicon variant. All models share the same material list.
4. Enter the surface **hkl**, an in-plane **uvw** direction, normal side, frame angle **ψ** and lattice. Use one common unit for a₀, b₀, c₀; lattice angles and controls use degrees. The in-plane direction must satisfy hu + kv + ℓw = 0. Automatic X projects a stable Cartesian reference into the surface. A manually supplied T must have orthonormal columns and determinant +1.
5. Check **X, Y, Z and T** in the frame panel. These are measurement axes, not Jones vectors. **Y = Z × X**. The panel updates before an intensity scan.
6. Select **Review inputs** to inspect the frame checks, crystal and transformed tensors and actual Jones states without calculating intensity.
7. Run the calculation. Read the numbered mathematical steps or inspect the polar plots. Download the result ZIP for equations, LaTeX, raw CSV and figures.

The redundant Example selector and Load selected example button have been removed. The first-run example and reproducible input JSON files are still supplied. Changing the calculation model keeps the selected material, optical method and geometry.

## Models and source conventions

**Model 1 — New-san.** Follow Paukatong et al., DOI 10.1002/jrs.70113: original cubic tensors, the measurement frame, Rⁱ′ = TᵀRⁱT, Jones states and intensity. With the source cubic axes, X ∥ [k −h 0], Y = Z × X and Z ∥ [h k ℓ]. Other in-plane references and noncubic materials use the entered lattice metric and are extensions of the source examples. The program does not silently reset those controls.

**Model 2 — My PPT slide.** Use the slide calculation with the selected material and frame. For the supplied CaNb₂O₆ slide case, choose Ag, (211), [0 1 −1], negative normal and the slide lattice convention. Actual noncubic lattice ratios are required for a physical tilted-surface normal. The separate Ag(xx), Ag(yy), Ag(zz) plots are Cartesian contributions; their powers are not added as independent phonons. The complete coherent Ag intensity is also derived for comparison.

**Model 3 — Dr. Kumar.** Apply Jones matrix multiplication to the XY block of each rotated crystal tensor. The displayed derivation explains why removing the zero Z components gives the same amplitude as the 3D contraction. This is the program's 3D extension; the unchanged original 2D/QWP notebook remains a separate source download. The selected VV/VH/σ⁺α states are used in the public calculator.

For identical crystal tensors, measurement axes and polarization states, the complete-mode intensity agrees across all three routes. A model name does not by itself change the physical experiment.

## Expected first result

For Silicon (500), X = (0, −1, 0), Y = (0, 0, −1), Z = (1, 0, 0), and d = 1:

- VV: I(θ) = sin²(2θ).
- VH: I(θ) = cos²(2θ).
- σ⁺α: I(α) = sin²α.

VV and VH scan θ. The σ⁺α option uses θ = π/4 and β = β′ = π/2 in New-san equation (11), then scans α. This is the paper's detection-state scan. Keep the same axes and angular zero when comparing plots; a different in-plane reference can rotate an angular pattern.

## Read the mathematical output

The left column gives a short explanation and definitions; the right column gives the equation. Stages follow crystal tensor → surface axes and T → transformed tensor → Jones states → explicit tensor/vector products → amplitude times conjugate → coefficient substitution and polar plot. Red is reserved for analytical Raman tensor and Raman intensity expressions. No K₀/Kc/C/D calculation aliases are introduced.

For GaAs, the phonon projection follows paper (8) and SI (S14): TO combines X and Y intensities; LO uses Z. The output identifies the difference between the printed polar entry in SI (S10) and this direct Cartesian projection.

## Review with a colleague

Restart the kernel and Run All. Record the printed revision, chosen model/material/mode, hkl, uvw, lattice, normal side, ψ, polarization, tensor values and the exported result. First check the Silicon expressions above; then change one input at a time. Automated checks do not constitute an independent colleague review. Consultation with Dr. Kumar and discussion with lab members remain tasks for the laboratory.
