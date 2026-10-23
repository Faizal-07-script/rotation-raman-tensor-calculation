"""Keep the new checks inside the single notebook and update its tutorial ranges."""
import ast
import difflib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
path=ROOT/"sources/notebook_v2.ipynb"
book=json.loads(path.read_text())
cells=[c for c in book["cells"] if c["cell_type"]=="code"]
original={i:"".join(c["source"]) for i,c in enumerate(cells,1)}
updated=dict(original)

updated[4]=updated[4].replace('"filename": "Imported optical reference notebook"',
                             '"filename": "Raman_intensity_Kumar_Version_2.ipynb"').replace(
    '"sha256": "c1fa022ce24803c411a24e9aed8152743da6a8feb29cd7ea3cd69885c31aeee0"',
    '"sha256": "661989475b7bd39b1ab57bc4d9d59285ccf903baa24b58a78017d841feba8ec7"')

needle='        js("complete_mode_physics_audit.json", run["physics"])\n'
assert needle in updated[16]
updated[16]=updated[16].replace(needle,needle+'''        procedures = run.get("checking_procedures") or checking_procedures_for_run(run)
        js("checking_procedures.json", procedures)
        archive.writestr("checking_procedures.md", checking_report_markdown(procedures))
        if validation and validation.get("optical_reference"):
            js("optical_reference_validation.json", validation["optical_reference"])
            archive.writestr(
                "optical_reference_validation.md", checking_report_markdown(validation["optical_reference"])
            )
''')
updated[19]=updated[19].replace(
    '        run = calculate_general(collect_config())\n',
    '        run = calculate_general(collect_config())\n        run["checking_procedures"] = checking_procedures_for_run(run)\n')
updated[19]=updated[19].replace(
    '        with physics_out:\n            display(Markdown(protocol_check_markdown(run)))',
    '        with physics_out:\n            display(Markdown(checking_report_markdown(run["checking_procedures"])))\n            display(Markdown(protocol_check_markdown(run)))')
updated[19]=updated[19].replace(
    '            checks = run_self_checks() + validate_general_upgrade()\n',
    '''            checks = run_self_checks() + validate_general_upgrade()
            source_report = validate_optical_reference()
            check(source_report["status"] == "passed", "QWP source reference checks failed.")
            checks.append(
                f"QWP source reference: {source_report['passed']}/{source_report['total']} checking procedures pass."
            )
''')
updated[19]=updated[19].replace(
    'status="passed", software_version=AUDIT_VERSION, checks=checks\n',
    'status="passed", software_version=AUDIT_VERSION, checks=checks, optical_reference=source_report\n')
updated[19]=updated[19].replace(
    '            for line in checks:\n                print("PASS:", line)\n',
    '            for line in checks:\n                print("PASS:", line)\n            display(Markdown(checking_report_markdown(source_report)))\n')
extension=(ROOT/"checking_procedures_source.py").read_text()
assert "OPTICAL_REFERENCE_SOURCE" not in original[21], "This integration has already been applied."
updated[21]=original[21].rstrip()+"\n\n\n"+extension

for number,source in updated.items():
    ast.parse(source)
    if source!=original[number]:
        cells[number-1]["source"]=source.splitlines(keepends=True)
        cells[number-1]["execution_count"]=None
        cells[number-1]["outputs"]=[]
book["metadata"]["rotation_raman_revision"]["checking_procedures_extension"]={
    "source":"QWP source reference","date":"2026-10-22",
    "source_sha256":"661989475b7bd39b1ab57bc4d9d59285ccf903baa24b58a78017d841feba8ec7",
    "main_calculation_functions":"unchanged",
}
path.write_text(json.dumps(book,indent=1))

def remap_blocks(document,old,new):
    a,b=old.splitlines(),new.splitlines()
    opcodes=difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes()
    line_map={}
    inserts=[]
    for kind,i,j,k,l in opcodes:
        if kind=="equal":
            line_map.update({q+1:q-i+k+1 for q in range(i,j)})
        elif kind=="replace":
            for q in range(i,j):line_map[q+1]=k+1+min(q-i,max(l-k-1,0))
        elif kind=="insert":inserts.append((i,k+1,l))
    for block in document["blocks"]:
        start,end=block["start_line"],block["end_line"]
        mapped=[line_map[q] for q in range(start,end+1) if q in line_map]
        if mapped:block["start_line"],block["end_line"]=min(mapped),max(mapped)
        for before,ns,ne in inserts:
            if start<=max(before,1)<=end:
                block["end_line"]=max(block["end_line"],ne)

for suffix in ["1_8","9_16","17_22"]:
    p=ROOT/f"sources/tutorial_{suffix}.json"
    annotations=json.loads(p.read_text())
    for document in annotations:
        number=document["cell"]
        if number not in [4,16,19,21]:continue
        if number!=21:
            remap_blocks(document,original[number],updated[number])
        if number==4:
            document["pitfalls"].append("QWP source provenance now identifies the supplied QWP source reference notebook by its byte SHA-256; it is distinct from the crystal tensor library.")
        if number==16:
            document["workflow"].append("Export the current checking procedures with purposes, expected equations and measured evidence. Include the optical source reference report when validation has run.")
            for block in document["blocks"]:
                if block["start_line"]<=220<=block["end_line"]:
                    block["explanation"]+=" The archive now also contains checking_procedures.json/.md and, after reference validation, optical_reference_validation.json/.md."
                    block["why"]+=" These records preserve what was checked, its purpose and the actual residual instead of an unsupported success label."
        if number==19:
            document["workflow"].append("Calculate a current-run checking report and render its purpose/procedure/evidence; Run validation also executes the 25 source-reference procedures.")
            for block in document["blocks"]:
                if block["title"].startswith("Calculate once"):
                    block["explanation"]+=" checking_procedures_for_run uses the same frozen run to generate an evidence record. checking_report_markdown displays each check's purpose and mathematical expectation above the existing protocol comparisons."
                if block["title"].startswith("Run the full regression"):
                    block["explanation"]+=" validate_optical_reference executes the uploaded Version 2 identities, limits, four circular channels and appendix convention. The full report is retained in state and rendered with its purposes."
                    block["check"]+=" A source-reference report must have status passed; otherwise this callback records a validation failure."
        if number==21:
            document["overview"]+=" The final part implements QWP source reference checking procedures with explicit purposes and measured evidence, then generalizes the testing pattern to the current crystal/Jones run."
            document["workflow"] += [
                "Describe K01-K25 before execution; a procedure catalog does not imply that any test passed.",
                "Evaluate symbolic differences and independent numeric matrix paths, special limits, four circular channels and deliberate mistakes.",
                "Apply the same checking pattern to the actual current tensor and optical states. Mark source-only identities not applicable for a different crystal tensor.",
                "Return purpose, procedure, expected equation, status and measured evidence to both notebook and web views."]
            tree=ast.parse(updated[21])
            new_nodes=[n for n in tree.body if n.lineno>len(original[21].splitlines())]
            function_notes={
                "checking_procedure_catalog":("Define what is checked and why","This catalog maps every K01-K25 procedure to the source's numbered code section, purpose, method and expected equation. It contains no preassigned pass status.","A visitor can understand the validation before running it.","Verify the output-input index convention and distinguish original checks from explicit extensions."),
                "checking_numeric_evidence":("Measure numerical residuals","Broadcast both independent results, reject nonfinite data, calculate their maximum residual and compare it with atol+rtol*scale.","A computed tolerance makes numerical agreement assessable and allows errors to fail.","Changing one intensity by 1e-5 must be rejected."),
                "checking_symbolic_evidence":("Test exact symbolic identities","Expand exponential forms and simplify each residual. Only all-zero residuals pass; an unresolved expression remains inconclusive.","Symbolic structural equality alone does not establish equality of algebraic expressions.","Read the actual reduced residual list rather than trusting a printed True."),
                "circular_input_contrast":("Define four powers and a safe contrast","Transform a numeric response into the circular basis; sum each input column and form the difference and optional CID.","Output and input indices must stay distinct. A dark response has no defined normalized contrast.","For a zero matrix, total_power=0 and cid=None."),
                "validate_optical_reference":("Execute the source-reference checking sequence","Rebuild the main optical chain, compare independent hand equations, repeat seeded numeric samples, test limits and all four circular channels, then verify the appendix and negative controls.","The source formula is an independent reference, never the curve generator for another material.","Every K01-K25 item must contain measured evidence; three deliberately wrong controls must be rejected."),
                "checking_procedures_for_run":("Generalize checks to the current calculation","Use the frozen run's actual matrices and Jones vectors to test norms, return optics, explicit propagation, circular reconstruction, complete output power, rotation and projection.","The general model must be validated with its own tensor. The source special antisymmetric tensor is not imposed on orthorhombic crystals.","The special source closed-form comparison is not applicable for CRYSTAL_3D; it is tested for QWP_SOURCE_2D."),
                "checking_report_markdown":("Export the same validation explanation","Format each purpose, procedure, expected mathematical identity, status and evidence in Markdown for notebook display and result archives.","Human-readable reports and JSON records must describe the same checks.","Confirm report counts and residuals agree with the web report and exported JSON."),
            }
            old_end=len(original[21].splitlines())
            first_function=next(n.lineno for n in new_nodes if isinstance(n,ast.FunctionDef))
            document["blocks"].append(dict(start_line=old_end+1,end_line=first_function-1,
                title="Identify the supplied reference and its scope",
                explanation="OPTICAL_REFERENCE_SOURCE records the exact uploaded file fingerprint and fixes the output-input circular index convention.",
                why="A reference check needs traceable provenance and an explicit material-model boundary.",
                check="The source hash must match Raman_intensity_Kumar_Version_2.ipynb; the original upload is preserved."))
            for node in new_nodes:
                if not isinstance(node,ast.FunctionDef):continue
                title,explanation,why,check=function_notes[node.name]
                start=node.lineno
                if node.decorator_list:start=min(n.lineno for n in node.decorator_list)
                document["blocks"].append(dict(start_line=start,end_line=node.end_lineno,title=title,
                    explanation=explanation,why=why,check=check))
    p.write_text(json.dumps(annotations,indent=2))
print("Integrated checking procedures into the existing 22-cell program and remapped tutorial line ranges.")
