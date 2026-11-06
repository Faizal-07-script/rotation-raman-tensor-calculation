# Saito-sensei’s Feedback — Version 5

Updated 2 November 2026. Version 5, revision 2026-11-02-r1.

| Feedback | Status and where to check |
| --- | --- |
| Print a message after every cell | Done. All 22 cells print “Run completed successfully.”, the cell number, what is ready and the next step. |
| Explain what to enter, especially in the last cells | Done. Each cell has short input and output notes. QUICKSTART.md lists the controls, units and expected starting values. |
| Supply an example that runs without editing the code | Done. Cell 22 loads silicon (500), T2g, d=1, VV and shows its polar plot. Matching input JSON files are included. |
| Show X, Y and Z, and construct the complete transformation matrix | Done. X is selected in the surface; Y is calculated from Z × X. Input review shows all three axes, T, TᵀT and det(T)=+1. |
| Show the preparation before the long intensity calculation | Done. Review inputs checks the geometry, tensors and optical states without running an intensity scan. |
| Number the operations so they can be discussed in a meeting | Done. Input groups and mathematical operations have step numbers. |
| Define symbols before they are used | Done. The explained view defines new symbols beside their first equation. The complete symbol list is also exported. |
| Make the analytical intensity easy to find | Done. The final equation appears beside the plots and in the last mathematical section. The derivation uses the original tensor coefficients, without K/C/D aliases. |
| Compare numerical and analytical results | Exact symbolic checks compare the main-text general real-tensor intensity and (001) limit with the matrix contraction. All 18 Si (5,k,0) cases are checked symbolically and at 361 numerical angles. Open Checks, comparisons and benchmark → Validation or Silicon benchmark, or download Reference_Equation_Checks.md. A comparison with every supporting-information expression remains pending. |
| Ask other people to test the program | Pending independent review. QUICKSTART.md contains the fresh-kernel test and the information each tester should record. Automated checks do not replace a colleague’s run. |
| Ask Kumar-san about program documentation | Pending consultation. The current documentation is ready for review; no consultation or approval is claimed. |

The two websites and Python download use the same scientific functions.
The calculator-only website has the numbered input cards, optional guide,
input review, plots and both mathematical views. The full website also keeps
the introduction, tutorials and references.


## Feedback from 2 November

| Request | Implementation or next action |
| --- | --- |
| Explain d before continuing | Material / tensors: d is a Raman tensor entry. Size and coefficient phase are defined beside the inputs; the actual complex value is displayed below them. Input review defines each value before it enters a matrix. |
| Clarify coefficient phase | d = abs(d) exp(iφd). Size 1 with 0°, 180°, 90° gives 1, −1, i. These phases are not sample-rotation angles. At zero size, phase is undefined and has no effect. |
| Replace unclear terminology | Si matrices are labeled yz/zy, xz/zx and xy/yx in crystal coordinates. Standard terms have short definitions. Color distinguishes tensor components, coefficient size, coefficient phase and measurement axes; wording supplies the meaning too. |
| Distinguish geometry from polarization | Input review and 3D frame identify X, Y, Z as measurement axes in crystal coordinates. Jones states describe polarization. T is real orthogonal; TᵀT=I and det(T)=+1. |
| Show amplitude-to-intensity algebra | Step-by-step calculation shows tensor products, fields, analyzer contraction, amplitude, conjugate, product and final angular law. Complete coherent Ag derivations accompany its separate Cartesian contribution diagnostics. |
| Explain the common calculation | “How does the calculation work?” shows what changes when material, surface or polarization changes. The same explanation is in Python and Physics & equations. |
| Discuss with lab members before the next meeting | Pending a real discussion and independent run. Share the current notebook and test checklist before the 9 November meeting. No colleague review is claimed by this software. |
| Present only the updates | Suggested order: coefficient input; axes; one complete intensity derivation; reference-equation comparison. Show one example of each. |

Internal JSON keys used by older saved inputs are preserved for compatibility.
They are implementation details, not names for new physical quantities.


## 6 November 2026 revision

Exactly three calculation models: My PPT slides, New-san, and Dr. Kumar. New-san uses VV, VH and σ⁺α and follows the paper/SI order. Analytical transformed tensors and intensity expressions are red; symbol definitions are brief. Python, both websites and their downloads use the same calculation functions. See LAB_MODEL_REVISION.md.
