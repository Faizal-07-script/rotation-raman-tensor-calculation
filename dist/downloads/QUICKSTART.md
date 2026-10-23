# Version 4 — first run and numbered tools

**Revision 2026-10-23-r2 — Silicon (500) startup**

Run Cell 1 first. Its first output must read:

```text
Version 4 | Revision 2026-10-23-r2 | Silicon (500) default
```

Open the newly downloaded notebook whose filename begins `Raman_Tensor_V4_Si500_`. If this revision line is missing, compare the file you opened with the current download. Restart its kernel and run all 22 cells. The success messages appear below each executed cell; the Silicon polar plot appears in Cell 22.

Use **Jupyter Notebook / JupyterLab or Google Colab** with a Python kernel and widget support. The `.ipynb` is the recommended entry point; running the `.py` with an ordinary terminal does not provide the notebook interface. Install the packages in `requirements.txt` in the same kernel if an import is missing.

1. Open the current `Raman_Tensor_V4_Si500_…ipynb` notebook and choose **Restart kernel and Run All**. Run all **22 code cells in order**. Do not start from Cell 17 or Cell 22 in a fresh kernel.
2. Each code cell prints **“Run completed successfully.”**, its cell number, what is ready and which cell to run next. The explanation above each code cell states its role, what to enter and what to expect. Cells 1–21 primarily define functions or controls; their message confirms execution, while the numerical/model checks are reported separately.
3. Cell 22 checks **silicon (500), VV** and displays its polar plot directly above the application. The **Silicon (500), VV reference frame** example is loaded automatically, and the **Polar plots** result tab is selected. No typing, `input()` prompt, external data file or coefficient editing is required for this first run.
4. Inspect the silicon image, **Intensity values** and **Validation**. The first result has **one T2g channel**, combining the intensities of three unresolved orthogonal phonon partners, and **721 samples** from 0° through 360°. Cell 22 compares every sample with the reference equation below before displaying the image. The inline image records the initial test; later results appear in the application tabs.
5. For a different run, follow numbered tools **1 → 2 → 3 → 4 → 5 → 6**, then **7** to export. A selected example changes the form only after **1.4 Load selected example**. Example loading replaces inputs; review its selected model and optics afterward. The notebook automatically calculates only the initial example; press **6** after later changes.
6. **8** reruns model validation, **9** saves and compares calculated runs, and **10** is the separate silicon benchmark. These optional tools are not required to run the first example.

## Tool numbers and what to enter

| Tool | Action / input | First-run example | Units / format / scope |
| --- | --- | --- | --- |
| **1. Model, optics & example** | 1.1 choose tensor model; 1.2 choose optics; 1.3 choose an example; 1.4 load it; 1.5–1.6 label and note | Full 3D crystal; VV reference (`CUBIC_VV`); Silicon (500) | Model and optics are separate choices. Labels/notes are exported text. Choose the paired linear profile (`LINEAR_PAIR`) when you want both VV and VH. |
| **2. Material & tensor coefficients** | 2.1 material; 2.2 point group; 2.3 modes; 2.4 optional Ag equality; 2.5 each coefficient's magnitude and phase; 2.6 custom tensor | Si; Oh; T2g; shared d=1 with zero phase | Magnitudes ≥0 in one consistent relative scale; phases in degrees. A custom tensor is a 3×3 JSON array of numbers or strings such as `"1+0.2j"`. Named materials fix their stated point group. For another group, choose General. |
| **3. Orientation & lattice** | 3.2 surface; 3.3 h,k,l; 3.4 u,v,w; 3.5 automatic X; 3.6 normal side; 3.7 frame angle; 3.8 lengths; 3.9 lattice angles | (500); hkl=(5,0,0); uvw=(0,-5,0); automatic X off; normal +1; ψ=0; lengths=(1,1,1); angles=(90,90,90) | Indices are integers and must satisfy hu+kv+lw=0. Lengths >0 use one common unit; angles/ψ use degrees. Equal lengths describe the cubic silicon reference; replace ratios for a noncubic sample. Web tool 3.1 also permits a proper manual frame. |
| **4. Jones states & optical controls** | Set only fields active for the selected optical profile; inspect its equations and actual states | VV uses co-rotating parallel linear states; θ₀=0°; direct/circular-rule fields are inactive | Angles/phases are degrees. Direct Jones uses (cos θ, exp(iβ) sin θ). Conditional circular-rule charges are integers; phonon charges use comma-separated integers, e.g. `0, 1`; optional absorption charge may be blank. Those rule fields do not rescale the intensity. |
| **5. Display settings** | 5.1 angular grid; 5.2 normalization; 5.3 Cartesian plots; 5.4 frame; 5.5 notebook mathematical steps | 0.5° / 721 samples; normalization off; Cartesian off; frame and steps on | Normalization is one common scale per mode. Raw CSV retains the unnormalized intensities. |
| **6. Calculate** | Press after changing any input or loading another example | Initial example is calculated automatically | Confirm “Calculation complete” and inspect the current result. An edited form needs a new calculation. |
| **7. Results & downloads** | Inspect result tabs; 7.1 complete result archive; 7.2 symbolic LaTeX (web also offers raw CSV) | One silicon T2g curve, full derivation, tables and measurement frame | Downloads become available after a successful calculation. Notebook archive: press 7.1, then follow the link in Downloads. Components are diagnostic powers of one Ag phonon and are not summed in the main plots. |
| **8. Validation** | Rerun the model/source checks | Automatically run on initial notebook startup | Passing software checks does not establish independent colleague review or sample calibration. |
| **9. Comparisons** | Save a successful run, change inputs, calculate again, save another, select a common channel | Optional | Snapshots preserve their own inputs. Comparison data are session-local; export before restarting. |
| **10. Silicon benchmark** | Shared \|d\|=1; choose grid; calculate 18 cases; select a surface/protocol; inspect/export | Six surfaces (500)–(550), VV/VH/σ reference | A separate reference calculation. Its coefficient scale is shared across all 18 cases. |

In the original effective 2D model, tool 2 instead takes real a=1, A=0.4, δ=60° and φ=60°. Crystal orientation is inactive in that model. These are reference inputs, not a crystal tensor inferred from a material.

## Expected output for the unchanged first example

For d=1 and the declared (500) frame, the silicon VV reference is

$$I_{\mathrm{VV}}(\theta)=\sin^2(2\theta).$$

| Check | Expected unnormalized T2g intensity |
| --- | --- |
| θ=0° and 360° | 0 |
| θ=45° | 1 |
| θ=90° and 270° | 0 (within floating-point tolerance) |
| Maximum on the 0.5° grid | 1 |
| Continuous maximum | 1 |

Use an absolute tolerance of 1e-10 for the sampled values and reference curve. The 0.5° grid contains the maxima, so the sampled and continuous maxima agree. Intensities use the relative scale d=1; they are not measured counts. All 22 cells must finish, Cell 22 must report that the silicon startup check passed, and Validation must report passed.

The first run shows VV. To compare VV and VH, choose the paired linear profile (`LINEAR_PAIR`) in 1.2, then press 6. The other examples remain available through 1.3 and 1.4.

`silicon_startup_input_v4.json` and `example_input_v4.json` contain the same Silicon (500), VV starting inputs for Python and the website. The other material examples remain available. The (500) label follows the cubic benchmark; its surface-normal direction is parallel to (100).

## Read the derivation

Open **Mathematical derivation** in the notebook or **Mathematical steps** on the website. Each equation is followed immediately by a **Symbols and units** table and a **Derivation / source** note. The same notes are included in the full, symbolic and numerical LaTeX exports, `calculation_steps.md` and the result ZIP. `Symbols_And_References.md` collects the definitions and reference locations.

Angles in equations are radians; inputs and angular CSV columns are degrees. Matrix superscript ᵀ means transpose, while the standalone T is the frame matrix. The projector P is distinct from physical polarization density. Unit Jones states are dimensionless; reduced response amplitudes use tensor-coefficient units and their squared magnitudes give the plotted relative intensity (a.u.). Physical SI tensor units depend on the declared normal-coordinate convention. No absolute field strength or detector calibration is supplied by the example.

Reference principles are distinguished from intermediate program algebra: Pimenta et al. (2021), Eqs. (1)–(4), for the physical Raman tensor; Paukatong et al. (2026), Eqs. (1)–(6), (9), (11), for Si tensors, frames and polarization; and the supplied original Kumar notebook for its QWP convention. NIST and IUPAC definitions support the unit notes.

## What the last cells need

- **Cell 17** creates the numbered widgets. Run it unchanged; it does not ask you to type data into Python.
- **Cell 18** defines handlers that check and update the widgets. Run it unchanged.
- **Cell 19** defines calculate/export/compare/validate actions. Run it unchanged; button clicks in Cell 22 call these functions.
- **Cells 20–21** define validation functions. Run them unchanged. Their completion message means the functions are ready; the tests themselves run in Cell 22 or when you press 8.
- **Cell 22** loads silicon (500), calculates VV, checks the reference equation, displays a PNG polar plot outside the widgets, runs model validation and displays the interface. Enter your own data only in this interface. The demonstration values and formats are listed above.

## If the result looks unchanged

Check the revision printed by Cell 1 and use a fresh kernel. For the same material, orientation, coefficients and optical states, the numerical intensity curve should remain the same: this revision adds visible execution messages and documentation without changing the scattering calculation. `raman_engine.py` is a reusable library; run the main `.ipynb` to see the notebook messages and controls. The notebooks under `references/` are preserved source documents.

## If output is missing

- A red exception means the cell did not finish; fix the first exception before continuing. For a missing package, install the matching requirement in the active kernel, then restart and Run All.
- A `NameError` in a later cell usually means earlier cells were skipped or the kernel restarted. Run All from Cell 1.
- If only text such as `VBox(...)` appears, use a notebook frontend with ipywidgets enabled. An ordinary Python terminal does not render the interface.
- Wait for Cell 22 to finish its calculation/validation. Text messages in Cells 1–21 are expected. The silicon PNG appears directly in Cell 22, including in a static notebook preview; the interactive controls require widget support.
- A disabled download button needs a successful fresh calculation. After 7.1, open the Downloads tab and click its generated file link.

## Reproducibility check by another person

Share the current notebook or program ZIP and this guide with a colleague. Ask them to start a fresh kernel, run the notebook unchanged, compare the silicon values and the polar plot above, check the 22 messages and Validation status, then export a result. Record tester name, date, Python/frontend versions, exact file SHA-256 and any error. This checklist is prepared; an independent person's run and Kumar-san's documentation review are still pending.

## Symbols

| Symbol | Meaning |
| --- | --- |
| α | Analyzer or detection-state scan angle |
| θ | Linear polarization angle |
| β, β′ | Relative Jones-state phases in the reference convention |
| βᵢ, βₛ | Incident and detected Jones-state phases in the direct controls |
| ψ | In-plane frame rotation |
| δ, φ | Effective-source phases |
| σ⁺, σ⁻; σ⁺α | Circular basis states; circular-input analyzer scan |
| Γ; Δ; ∑ | Brillouin-zone center; a difference; summation |

Greek letters are case-sensitive. Internal names such as `theta_i_deg` remain valid Python/JSON identifiers; the interface displays θᵢ. A and a are different source amplitudes.
