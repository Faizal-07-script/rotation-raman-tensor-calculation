# Version 3 — first run and numbered tools

Use **Jupyter Notebook / JupyterLab or Google Colab** with a Python kernel and widget support. The `.ipynb` is the recommended entry point; running the `.py` with an ordinary terminal does not provide the notebook interface. Install the packages in `requirements.txt` in the same kernel if an import is missing.

1. Open `ROTATION_RAMAN_TENSOR_CALCULATION.ipynb` and choose **Restart kernel and Run All**. Run all **22 code cells in order**. Do not start from Cell 17 or Cell 22 in a fresh kernel.
2. Each code cell now prints **“This cell runs correctly.”**, its cell number and what became ready. Cells 1–21 primarily define functions or controls; their message confirms execution, while the numerical/model checks are reported separately.
3. Wait for Cell 22 to show the application. The **Slide-frame Ag(xx), Ag(yy), Ag(zz) on (211)** example is already loaded, calculated and validated. No typing, `input()` prompt, external data file or coefficient editing is required for this first run.
4. Inspect **Polar plots**, **Intensity values** and **Validation**. The default has **3 separate Ag component channels**, **721 samples** from 0° through 360°, and **271 equations**. The table below gives numerical comparisons. They test the declared demonstration inputs, not a calibrated CaNb2O6 experiment.
5. For a different run, follow numbered tools **1 → 2 → 3 → 4 → 5 → 6**, then **7** to export. A selected example changes the form only after **1.4 Load selected example**. Example loading replaces inputs; review its selected model and optics afterward. The notebook automatically calculates only the initial example; press **6** after later changes.
6. **8** reruns model validation, **9** saves and compares calculated runs, and **10** is the separate silicon benchmark. These optional tools are not required to run the first example.

## Tool numbers and what to enter

| Tool | Action / input | First-run example | Units / format / scope |
| --- | --- | --- | --- |
| **1. Model, optics & example** | 1.1 choose tensor model; 1.2 choose optics; 1.3 choose an example; 1.4 load it; 1.5–1.6 label and note | Full 3D crystal; sigma+alpha reference (`CUBIC_SIGMA`); Slide-frame example | Model and optics are separate choices. Labels/notes are exported text. Choose the paired linear profile (`LINEAR_PAIR`) when you want both VV and VH. |
| **2. Material & tensor coefficients** | 2.1 material; 2.2 point group; 2.3 modes; 2.4 optional Ag equality; 2.5 each coefficient's magnitude and phase; 2.6 custom tensor | CaNb2O6; D2h; Ag; independent a,b,c; a=1, b=0.8, c=0.6 with zero phases | Magnitudes ≥0 in one consistent relative scale; phases in degrees. A custom tensor is a 3×3 JSON array of numbers or strings such as `"1+0.2j"`. Named materials fix their stated point group. For another group, choose General. |
| **3. Orientation & lattice** | 3.2 surface; 3.3 h,k,l; 3.4 u,v,w; 3.5 automatic X; 3.6 normal side; 3.7 frame angle; 3.8 lengths; 3.9 lattice angles | (211); hkl=(2,1,1); uvw=(0,1,-1); automatic X off; normal −1; psi=0; lengths=(1,1,1); angles=(90,90,90) | Indices are integers and must satisfy hu+kv+lw=0. Lengths >0 use one common unit; angles/psi use degrees. The unity metric is a slide-reference illustration: replace it with sample-specific ratios for physical tilted noncubic geometry. Web tool 3.1 also permits a proper manual frame. |
| **4. Jones states & optical controls** | Set only fields active for the selected optical profile; inspect its equations and actual states | The sigma+alpha profile fixes its reference states; leave inactive direct/circular-rule fields alone | Angles/phases are degrees. Direct Jones uses (cos θ, exp(iβ) sin θ). Conditional circular-rule charges are integers; phonon charges use comma-separated integers, e.g. `0, 1`; optional absorption charge may be blank. Those rule fields do not rescale the intensity. |
| **5. Display settings** | 5.1 angular grid; 5.2 normalization; 5.3 Cartesian plots; 5.4 frame; 5.5 notebook mathematical steps | 0.5° / 721 samples; normalization off; Cartesian off; frame and steps on | Normalization is one common scale per mode. Raw CSV retains the unnormalized intensities. |
| **6. Calculate** | Press after changing any input or loading another example | Initial example is calculated automatically | Confirm “Calculation complete” and inspect the current result. An edited form needs a new calculation. |
| **7. Results & downloads** | Inspect result tabs; 7.1 complete result archive; 7.2 symbolic LaTeX (web also offers raw CSV) | Three component curves, full derivation, tables and measurement frame | Downloads become available after a successful calculation. Notebook archive: press 7.1, then follow the link in Downloads. Components are diagnostic powers of one Ag phonon and are not summed in the main plots. |
| **8. Validation** | Rerun the model/source checks | Automatically run on initial notebook startup | Passing software checks does not establish independent colleague review or sample calibration. |
| **9. Comparisons** | Save a successful run, change inputs, calculate again, save another, select a common channel | Optional | Snapshots preserve their own inputs. Comparison data are session-local; export before restarting. |
| **10. Silicon benchmark** | Shared \|d\|=1; choose grid; calculate 18 cases; select a surface/protocol; inspect/export | Six surfaces (500)–(550), VV/VH/sigma reference | A separate reference calculation. Its coefficient scale is shared across all 18 cases. |

In the original effective 2D model, tool 2 instead takes real a=1, A=0.4, delta=60° and phi=60°. Crystal orientation is inactive in that model. These are reference inputs, not a crystal tensor inferred from a material.

## Expected output for the unchanged first example

| Channel | Maximum unnormalized intensity | Samples |
| --- | --- | --- |
| Ag(xx) | 0.05555555555555555 | 721 |
| Ag(yy) | 0.13333333333333333 | 721 |
| Ag(zz) | 0.075 | 721 |

Use an absolute tolerance of 1e-10 for these maxima. The intensities are in the consistent relative coefficient scale of this example. All 22 cells must execute without an exception; Validation must report passed. The first example's sigma+alpha scan is **not a VV/VH pair**. To practice VV and VH, keep the tensor and frame, choose the paired linear optical profile in 1.2, then press 6.

## What the last cells need

- **Cell 17** creates the numbered widgets. Run it unchanged; it does not ask you to type data into Python.
- **Cell 18** defines handlers that check and update the widgets. Run it unchanged.
- **Cell 19** defines calculate/export/compare/validate actions. Run it unchanged; button clicks in Cell 22 call these functions.
- **Cells 20–21** define validation functions. Run them unchanged. Their completion message means the functions are ready; the tests themselves run in Cell 22 or when you press 8.
- **Cell 22** displays the interface, loads the demonstration, calculates it and runs validation on initial startup. Enter your own data only in this interface. The demonstration values and formats are listed above.

## If output is missing

- A red exception means the cell did not finish; fix the first exception before continuing. For a missing package, install the matching requirement in the active kernel, then restart and Run All.
- A `NameError` in a later cell usually means earlier cells were skipped or the kernel restarted. Run All from Cell 1.
- If only text such as `VBox(...)` appears, use a notebook frontend with ipywidgets enabled. An ordinary Python terminal does not render the interface.
- Wait for Cell 22 to finish its calculation/validation. Text messages in Cells 1–21 are expected; plots are shown by the application and saved inline with the distributed notebook.
- A disabled download button needs a successful fresh calculation. After 7.1, open the Downloads tab and click its generated file link.

## Reproducibility check by another person

Share the current notebook or program ZIP and this guide with a colleague. Ask them to start a fresh kernel, run the notebook unchanged, compare all three maxima above, check the 22 messages and Validation status, then export a result. Record tester name, date, Python/frontend versions, exact file SHA-256 and any error. This checklist is prepared; an independent person's run and Kumar-san's documentation review are still pending.
