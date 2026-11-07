# Saito-sensei’s feedback and laboratory discussion — Version 5

Revision 2026-11-07-r1. The table separates implemented software from consultation or independent review that still requires a person.

| Request from Saito-sensei | Implementation and location |
| --- | --- |
| Ask other people to test the program and its output. | **Pending independent review.** QUICKSTART.md gives a fresh-kernel test and the inputs/results to record. Automated checks are reported separately. |
| Ask Dr. Kumar how to document the program. | **Pending consultation.** The current QUICKSTART, per-cell tutorial and mathematical explanations are ready for review; no consultation is claimed. |
| Print a success message whenever a cell finishes. | All 22 code cells print their number, “Run completed successfully.”, what is ready and the next action. |
| Clarify the required inputs, especially in the final cells. | Python cells 17–19 and 22, the website Python tutorial, numbered controls and QUICKSTART explain the controls, units and run order. |
| Supply a runnable starting example. | Silicon (500), T₂g, d=1, VV runs in Cell 22 without editing code. The matching JSON inputs remain in the download. The redundant Example/Load controls are removed. |
| Show X, Y and Z, calculate Y from Z × X, and form T. | A visible measurement-frame panel updates X, Y, Z and T before intensity. Orientation/lattice controls and the 3D frame remain available in every model. Python cells 3 and 18 contain the frame construction and preview. |
| Show the preparation before the long intensity calculation. | Review inputs shows original tensors, the actual frame, TᵀT=I, det(T)=+1, transformed tensors and Jones states without an intensity scan. Python cell 12 defines the review; cell 19 displays it. |
| Give the steps numbers so they can be discussed. | Input cards and every mathematical operation are numbered in Python and both websites. |
| Define symbols before using them and explain the results. | Definitions and units appear beside first use. Tensor/vector products show the intermediate matrices and the amplitude-to-intensity conjugate product. |
| Make the analytical intensity easy to find and compare it with New-san. | The final equation is beside the plots. Analytical tensor/intensity expressions are red. Si/GaAs reference cases are checked by independent matrix contractions. Source notes distinguish paper benchmarks, geometry extensions and the SI(S10)/SI(S14) difference. |

## Additional requests in the later laboratory discussion

| Request | Implementation or next action |
| --- | --- |
| Explain the coefficient before continuing; do not say “normal phase”. | The input shows d = abs(d) exp(iφd), the actual complex value and short examples: size 1 with 0°, 180°, 90° gives 1, −1, i. Coefficient phase is distinguished from sample/frame rotation. |
| Replace “tensor partner” with names people recognize. | Visible cubic matrices use yz/zy, xz/zx and xy/yx. Other tensors use their material/mode and displayed nonzero components. Internal compatibility keys are not presented as physical terminology. |
| Show the analytical intensity derivation, not just its final value. | Cell 12 and Step-by-step calculation show R′eᵢ, then eₛ*R′eᵢ, the conjugate product, the appropriate orthogonal-component sum, coefficient substitution and sample plot angles. |
| Explain the common program steps. | Surface/lattice/reference build T; material and mode supply R; the optical method supplies Jones states. The same physical contraction is used. The Dr. Kumar presentation explicitly connects the 3D tensor to its 2D XY block. |
| Discuss updates with lab members before a group meeting. | **Pending a real discussion.** Share the notebook, input case and exported evidence before the meeting. No colleague’s approval is claimed. |
| Present only the changes. | Suggested order: shared model/material/optical controls; restored X–Y–Z/T panel; one connected intensity derivation; reference comparison. |

## Controls restored in this revision

1. Model 1 — New-san; Model 2 — My PPT slide; Model 3 — Dr. Kumar.
2. VV, VH and σ⁺α in every model.
3. One shared material list, with Silicon and GaAs as separate cubic entries.
4. hkl, uvw, automatic X, normal side, ψ, lattice lengths/angles and manual proper T in every model.
5. X, Y, Z, T and pre-intensity checks; source definitions; complete coherent Ag comparison; per-cell messages, examples, documentation, exports and optional user guides.

The notebook, Python downloads and both websites use the same current scientific functions.
