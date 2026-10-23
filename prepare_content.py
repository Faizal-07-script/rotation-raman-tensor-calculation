"""Extract the source of truth and build reproducible website data assets."""
import ast
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
SOURCE=PROJECT/'sources'
DIST=PROJECT/'dist'
DATA=DIST/'data'
DOWNLOADS=DIST/'downloads'
DATA.mkdir(exist_ok=True);DOWNLOADS.mkdir(exist_ok=True)
notebook_path=SOURCE/'notebook_v4.ipynb'
notebook=json.loads(notebook_path.read_text())
cells=[c for c in notebook['cells'] if c['cell_type']=='code']
assert len(cells)==22
for cell in cells:
    source=''.join(cell['source']).replace('Cubic reference Eq. 11 states','Cubic reference Section 2.2 states')
    cell['source']=source.splitlines(keepends=True)
source_hash=hashlib.sha256('\n\n'.join(''.join(c['source']) for c in cells).encode()).hexdigest()
notebook['metadata']['rotation_raman_revision']['source_sha256']=source_hash
notebook_path.write_text(json.dumps(notebook,indent=1))

titles=[]
for cell in notebook['cells']:
    if cell['cell_type']=='markdown':
        text=''.join(cell['source'])
        match=re.search(r'^## Cell (\d+) [—–-] (.+)',text)
        if match:titles.append(match[2])
assert len(titles)==22
content=[]
for i,cell in enumerate(cells,1):
    source=''.join(cell['source'])
    tree=ast.parse(source)
    nodes=[dict(name=node.name,start=node.lineno,end=node.end_lineno,kind=type(node).__name__,
                docstring=ast.get_docstring(node) or '')
           for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
    content.append(dict(number=i,title=titles[i-1],tag=cell['metadata']['tags'][0],source=source,
        lines=len(source.splitlines()),symbols=nodes,sha256=hashlib.sha256(source.encode()).hexdigest()))
(DATA/'cells.json').write_text(json.dumps(dict(version='4',source_sha256=source_hash,cells=content)))

selected=[i for i in range(2,23) if i not in [17,18,19,22]]
prefix='''# Generated from the scientific cells of notebook version 4.
# Rich notebook display imports are omitted; scientific functions are unchanged.
import os
os.environ['MPLBACKEND']='Agg'
import matplotlib
matplotlib.use('Agg',force=True)
def display(*args,**kwargs): pass
def clear_output(*args,**kwargs): pass
HTML=Markdown=Math=lambda value: value
'''
parts=[]
for i in selected:
    source=content[i-1]['source']
    source=re.sub(r'^from IPython\.display import .*\n','',source,flags=re.M)
    source=re.sub(r'^print\("Cell \d{2}/22 — Run completed successfully\.[^\n]*\n?', '', source, flags=re.M)
    parts.append(f'\n# ==== Notebook code cell {i}: {titles[i-1]} ====\n'+source)
engine=(prefix+'\n\n'.join(parts)).rstrip()+'\n'
compile(engine,'raman_engine.py','exec')
(DIST/'raman_engine.py').write_text(engine)
shutil.copy2(PROJECT/'web_bridge.py',DIST/'web_bridge.py')
if os.environ.get('RAMAN_PYTHON_DEPENDENCY_PATH'):
    sys.path.insert(0,os.environ['RAMAN_PYTHON_DEPENDENCY_PATH'])
ns={}
exec(compile(engine,'raman_engine.py','exec'),ns)
exec(compile((PROJECT/'web_bridge.py').read_text(),'web_bridge.py','exec'),ns)
catalog=ns['web_catalog']()
example=ns['web_calculate'](json.dumps(catalog['examples'][catalog['default_example']]['config']))
canonical_startup=json.loads(example)['configuration']
catalog['examples'][catalog['default_example']]['config']=canonical_startup
(DATA/'catalog.json').write_text(ns['web_json'](catalog))
for name in ['example_input_v4.json','silicon_startup_input_v4.json']:
    (SOURCE/name).write_text(json.dumps(canonical_startup,indent=2)+'\n')
(DATA/'reference-example.json').write_text(example)
print('Native reference example generated.',flush=True)
guide_figure=ns['optical_profile_comparison_figure']()
guide_figure.savefig(DIST/'optical_profile_comparison.svg',format='svg',bbox_inches='tight',transparent=False,facecolor='white')
ns['plt'].close(guide_figure)
(DOWNLOADS/'Optical_Methods_Guide.md').write_text(ns['optical_methods_overview_markdown']()+'\n\n'+'\n\n'.join(ns['optical_method_markdown'](key) for key in ns['GENERAL_PROFILES']))
(DOWNLOADS/'Symbols_And_References.md').write_text(ns['symbols_and_references_markdown']())
shutil.copy2(PROJECT/'QUICKSTART.md',DOWNLOADS/'QUICKSTART.md')
shutil.copy2(PROJECT/'SAITO_FEEDBACK_AUDIT.md',DOWNLOADS/'SAITO_FEEDBACK_AUDIT.md')
shutil.copy2(SOURCE/'example_input_v4.json',DOWNLOADS/'example_input_v4.json')
shutil.copy2(SOURCE/'silicon_startup_input_v4.json',DOWNLOADS/'silicon_startup_input_v4.json')
for name,figure in ns['WEB_STATE']['figures']:
    if name.startswith('polar_'):
        figure.savefig(DIST/(name+'.svg'),format='svg',bbox_inches='tight',transparent=True)

annotations=[]
for suffix in ['1_8','9_16','17_22']:
    path=SOURCE/f'tutorial_{suffix}.json'
    if not path.exists():raise FileNotFoundError(path)
    value=json.loads(path.read_text())
    annotations.extend(value if isinstance(value,list) else value.get('cells',value.get('tutorials',[])))
assert sorted(item['cell'] for item in annotations)==list(range(1,23))
for item in annotations:
    lines=content[item['cell']-1]['source'].splitlines()
    covered=set()
    for block in item['blocks']:
        assert 1<=block['start_line']<=block['end_line']<=len(lines),(item['cell'],block)
        covered.update(range(block['start_line'],block['end_line']+1))
    missing=[i for i,line in enumerate(lines,1) if line.strip() and i not in covered]
    assert not missing,(item['cell'],missing)
(DATA/'tutorial.json').write_text(json.dumps(annotations))

shutil.copy2(notebook_path,DOWNLOADS/'ROTATION_RAMAN_TENSOR_CALCULATION.ipynb')
full_python='''"""Complete notebook source, version 4.
Run with an IPython/Jupyter kernel for the interactive widget application.
The .ipynb notebook is the recommended entry point.
"""\n\n'''+ '\n\n'.join(f'# Code cell {item["number"]}: {item["title"]}\n'+item['source'] for item in content)
(DOWNLOADS/'ROTATION_RAMAN_TENSOR_CALCULATION.py').write_text(full_python)
shutil.copy2(DIST/'raman_engine.py',DOWNLOADS/'raman_engine.py')
shutil.copy2(PROJECT/'web_bridge.py',DOWNLOADS/'web_bridge.py')
(DOWNLOADS/'sci.mplstyle').write_text(ns['SCI_STYLE_TEXT'])
(DOWNLOADS/'requirements.txt').write_text('numpy\nsympy\nmatplotlib\nipywidgets\nIPython\n')
archive_paths={
    'original_optical_reference.ipynb':SOURCE/'original_optical_reference.ipynb',
    'Dr_Kumar_Original.ipynb':SOURCE/'dr_kumar_original.ipynb',
}
for name,path in archive_paths.items():shutil.copy2(path,DOWNLOADS/name)
readme='''ROTATION RAMAN TENSOR CALCULATION — PYTHON DOWNLOADS

Current version: 4. Run all 22 cells of the .ipynb in Jupyter or Colab.
The matching .py file contains the complete notebook source for an IPython kernel.
raman_engine.py contains the same scientific functions without notebook-only
display imports; web_bridge.py supplies validated JSON/browser interfaces.

Version 4 uses Greek symbols in the controls, guides and exports, and shorter
instructions. The scientific calculations are unchanged. Optional website guides
remain available from the User guide button.

Newcomers: read QUICKSTART.md and use Restart kernel and Run All.
Every code cell prints "Run completed successfully.", its number, what is ready
and which cell to run next. Each cell also explains its role, inputs and outputs.
Cell 22 loads silicon (500), T2g, d=1, VV, checks its 721-point curve against
the reference equation and displays its polar PNG directly above the controls.
No external input or manual code edit is needed. The Polar plots tab opens first.
Tools are numbered 1-7 for the main workflow, with optional validation (8),
comparisons (9), and the silicon benchmark (10). silicon_startup_input_v4.json
records the Python startup inputs; Silicon_Startup_Polar_Plot.png is the checked
startup figure. The website also starts with Si (500); example_input_v4.json
records the same input configuration. Other material examples remain available.
Symbols_And_References.md collects the symbol definitions, unit conventions and
sources shown directly below every calculated equation in the notebook and website.
The full, symbolic and numerical LaTeX exports include those explanations.
SAITO_FEEDBACK_AUDIT.md distinguishes implemented changes from the still-pending
independent colleague review and documentation consultation with Kumar-san.

The checking-procedures extension records purpose, procedure, expected equation,
status, symbolic residuals or numerical tolerances. Cell 21 implements the
25 source-reference procedures from QWP source reference and their generalization
to the actual selected crystal/Jones run. Cells 16 and 19 export and display
the same reports. Main Ag components and all existing intensity laws are unchanged.
The uploaded original reference notebook is included as a separate, unmodified reference.

The references folder contains the unmodified optical implementation sources.
The live website tutorial displays the exact current Version 4 code.

The site self-hosts its Python WebAssembly runtime and mathematical typesetting.
Its first calculator start downloads the runtime into your browser. A web worker
keeps navigation responsive while the original Python engine calculates.

Model: ideal transverse plane-wave Raman scattering, supplied complex coefficients,
normal backscattering, explicit crystal orientation and actual Jones states.
Material coefficients and noncubic lattice ratios are illustrative until replaced.
Separate Ag Cartesian powers are diagnostics of one phonon and are not summed
in the main figures. A coherent full-mode audit is exported separately.
'''
(DOWNLOADS/'README.txt').write_text(readme)
with zipfile.ZipFile(DOWNLOADS/'All_Python_Programs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['ROTATION_RAMAN_TENSOR_CALCULATION.ipynb','ROTATION_RAMAN_TENSOR_CALCULATION.py','raman_engine.py','web_bridge.py','sci.mplstyle','requirements.txt','README.txt','Optical_Methods_Guide.md','Symbols_And_References.md','QUICKSTART.md','SAITO_FEEDBACK_AUDIT.md','example_input_v4.json','silicon_startup_input_v4.json','Silicon_Startup_Polar_Plot.png']:
        archive.write(DOWNLOADS/name,name)
    for name in archive_paths:archive.write(DOWNLOADS/name,'references/'+name)
print('Prepared 22 cells,',sum(len(x['blocks']) for x in annotations),'annotated code blocks and Python downloads.',flush=True)
