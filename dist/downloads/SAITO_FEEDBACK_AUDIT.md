# Saito-sensei feedback — Version 4 audit

Audit date: 2026-10-23. Baseline notebook: the preceding release before the feedback changes (GitHub main b670372fe576531d6c5bd1e11ae73adab2386e8e).

| Recommendation | Present before this update | Current status / evidence |
| --- | --- | --- |
| 1. Ask other people to run the unchanged program | Automated and browser checks existed; no independent person's test record was found. | **Pending independent review.** QUICKSTART.md now gives a fresh-kernel checklist, expected values and the information a tester should record. Automated checks here do not count as another person's review. |
| 2. Ask Kumar-san how to document it | The supplied original Kumar notebook and source links existed. No documentation consultation record was found. | **Pending consultation.** No message has been sent to Kumar-san and no approval is claimed. Preserve the original reference notebook unchanged. |
| 3. Print a completion message for every cell | Cells 1–21 had no saved visible output; Cell 22 displayed the interface and validation. | **Implemented.** Every one of the 22 code cells now prints its number and “This cell runs correctly.” after execution. The text distinguishes loaded function definitions from executed model checks. |
| 4. Explain what to input in the last cells | One-sentence cell introductions, UI field labels, a website tutorial and interactive guides existed. Notebook startup/input instructions were brief. | **Expanded.** The notebook and QUICKSTART.md now explain Cells 17–22, numbered actions, data types, units, active controls, calculation/export sequence and missing-output troubleshooting. |
| 5. Include example data so newcomers can just run it | Cell 22 already loaded, calculated and validated slide_component_config(); six selectable examples existed. | **Retained and made explicit.** The same example still runs on initial startup. A complete sample JSON, expected channel maxima and a no-edit first-run walkthrough are now included. |

## Numbered tools

1. Model, optical method and explicit example loading.
2. Material, point group, modes and complex coefficients (or effective-source inputs).
3. Orientation and lattice metric.
4. Jones states and active optical controls.
5. Display and angular sampling.
6. Calculate the current inputs.
7. Inspect/export a successful result.
8. Optional model/source validation.
9. Optional frozen-input comparisons.
10. Optional 18-case silicon benchmark.

The same main numbers are used in notebook controls and calculator input groups. Subnumbers identify fields/actions; h,k,l, u,v,w and lattice triples share their group number. Navigation labels remain separate from input-step numbers.

## Scope of the change

No tensor forms, coordinate rotations, Jones contractions or intensity equations are changed. Notebook completion prints are omitted from the extracted browser engine; the tensor and Jones calculations keep the same numerical behavior. Version 4 updates text and mathematical notation. The source notebook, downloadable notebook, full Python source, website tutorial and program ZIP are regenerated together. A completion message establishes execution of that cell, not experimental validation or independent review.
