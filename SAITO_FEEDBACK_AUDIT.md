# Saito-sensei feedback — Version 4 audit

Audit date: 2026-10-23. Baseline notebook: the preceding release before the feedback changes (GitHub main b670372fe576531d6c5bd1e11ae73adab2386e8e).

| Recommendation | Present before this update | Current status / evidence |
| --- | --- | --- |
| 1. Ask other people to run the unchanged program | Automated and browser checks existed; no independent person's test record was found. | **Pending independent review.** QUICKSTART.md now gives a fresh-kernel checklist, expected values and the information a tester should record. Automated checks here do not count as another person's review. |
| 2. Ask Kumar-san how to document it | The supplied original Kumar notebook and source links existed. No documentation consultation record was found. | **Pending consultation.** No message has been sent to Kumar-san and no approval is claimed. Preserve the original reference notebook unchanged. |
| 3. Print a completion message for every cell | Cells 1–21 had no saved visible output; Cell 22 displayed the interface and validation. | **Implemented.** Every one of the 22 code cells now prints its number and “Run completed successfully.” after execution. The text distinguishes loaded function definitions from executed model checks. |
| 4. Explain what to input in the last cells | One-sentence cell introductions, UI field labels, a website tutorial and interactive guides existed. Notebook startup/input instructions were brief. | **Expanded.** Each of the 22 cells has Role, What to enter and After running explanations. The notebook and QUICKSTART.md explain numbered actions, input formats and units. Every calculated equation now carries symbol definitions and a source/algebra note in the notebook, website and exports. |
| 5. Include example data so newcomers can just run it | Cell 22 already loaded, calculated and validated slide_component_config(); six selectable examples existed. | **Implemented; Python startup updated to silicon.** Cell 22 now loads Si (500), T2g, d=1, VV, checks all 721 samples against the reference equation and displays its polar PNG directly. The matching silicon JSON, expected values and no-edit walkthrough are included. The website uses the same Silicon (500) starting example. |

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

The silicon revision changes the Python startup example and its display, documentation and checks. The website starts with Silicon (500), VV, and shows a symbol/unit table beneath every calculated equation. The existing navigation and page layout are retained. No tensor forms, coordinate rotations, Jones contractions or intensity equations are changed. Notebook-only display and completion messages are omitted from the extracted browser engine. The source notebook, downloadable notebook, full Python source, matching tutorial and program ZIP are regenerated together. A completion message establishes execution of that cell; model checks and independent review have separate evidence.
