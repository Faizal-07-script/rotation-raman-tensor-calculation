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
notebook_path=SOURCE/'notebook_v5.ipynb'
notebook=json.loads(notebook_path.read_text())
revision=notebook['metadata']['rotation_raman_revision']['download_revision']
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
(DATA/'cells.json').write_text(json.dumps(dict(version='5',revision=revision,source_sha256=source_hash,cells=content)))

selected=[i for i in range(2,23) if i not in [17,18,19,22]]
prefix='''# Generated from the scientific cells of notebook version 5.
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
reference_report=ns['reference_analytic_report']()
reference_report['engine_sha256']=hashlib.sha256(engine.encode()).hexdigest()
(DATA/'reference-equation-checks.json').write_text(json.dumps(reference_report,indent=2,ensure_ascii=False)+'\n')
(DOWNLOADS/'Reference_Equation_Checks.md').write_text(ns['reference_analytic_markdown'](reference_report))
(DOWNLOADS/'Reference_Equation_Checks.json').write_text(json.dumps(reference_report,indent=2,ensure_ascii=False)+'\n')
catalog=ns['web_catalog']()
example=ns['web_calculate'](json.dumps(catalog['examples'][catalog['default_example']]['config']))
canonical_startup=json.loads(example)['configuration']
catalog['examples'][catalog['default_example']]['config']=canonical_startup
(DATA/'catalog.json').write_text(ns['web_json'](catalog))
for name in ['example_input_v5.json','silicon_startup_input_v5.json']:
    (SOURCE/name).write_text(json.dumps(canonical_startup,indent=2)+'\n')
(DATA/'reference-example.json').write_text(example)
print('Native reference example generated.',flush=True)
guide_figure=ns['optical_profile_comparison_figure']()
guide_figure.savefig(DIST/'optical_profile_comparison.svg',format='svg',bbox_inches='tight',transparent=False,facecolor='white')
ns['plt'].close(guide_figure)
(DOWNLOADS/'Optical_Methods_Guide.md').write_text(ns['optical_methods_overview_markdown']()+'\n\n'+'\n\n'.join(ns['optical_method_markdown'](key) for key in ns['LAB_PROFILE_LABELS']))
(DOWNLOADS/'Symbols_And_References.md').write_text(ns['symbols_and_references_markdown']())
shutil.copy2(PROJECT/'QUICKSTART.md',DOWNLOADS/'QUICKSTART.md')
feedback_path=PROJECT/'Saito-sensei feedback.md'
if not feedback_path.is_file():
    feedback_path=PROJECT/'SAITO_FEEDBACK_AUDIT.md'
shutil.copy2(feedback_path,DOWNLOADS/'SAITO_FEEDBACK_AUDIT.md')
shutil.copy2(SOURCE/'example_input_v5.json',DOWNLOADS/'example_input_v5.json')
shutil.copy2(SOURCE/'silicon_startup_input_v5.json',DOWNLOADS/'silicon_startup_input_v5.json')
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
intro=''.join(notebook['cells'][0]['source'])
full_python='# %% [markdown]\n'+ '\n'.join('# '+line if line else '#' for line in intro.splitlines())+'\n\n'
full_python+='\n\n'.join(f'# %% Code cell {item["number"]}: {item["title"]}\n'+item['source'] for item in content)
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
readme='''ROTATION RAMAN TENSOR CALCULATION — VERSION 5

Open 261024 - Raman Tensor Rotation Ver 5.0.ipynb. Run all 22 cells in order.
Each cell prints a success message. Cell 22 opens Si (500), VV.

Choose one model:
1. My PPT slide model.
2. New-san — Paukatong et al.: VV, VH, or σ⁺α; Si T₂g and GaAs TO/LO.
3. Dr. Kumar: the original 2×2 tensor and QWP sequence.

New-san order: original tensors, surface axes, transformed tensors, Jones states,
intensity, and polar plot. Analytical tensor and intensity expressions are red.
Other steps and short symbol definitions use the normal text color.
Intermediate K₀/Kc/C/D calculation aliases are not displayed.

The notebook, Python script, engine and tutorial use the same current scientific
functions. Result ZIPs include the steps, symbolic LaTeX, raw curves and figures.
Read QUICKSTART.md for the inputs and source conventions. Original uploaded
notebooks remain separate source records. Independent laboratory review is pending.
'''
(DOWNLOADS/'README.txt').write_text(
    f'Version 5 | Revision {revision} | Silicon (500) default\n\n'
    'Open 261024 - Raman Tensor Rotation Ver 5.0.ipynb.\n'
    'Cell 1 prints this same revision before preparing the environment.\n'
    'Open the newly downloaded file, then restart its kernel and Run All.\n'
    'The .py source has 22 # %% cell boundaries for editors that support Python cells.\n\n'+readme)
with zipfile.ZipFile(DOWNLOADS/'All_Python_Programs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for name in ['ROTATION_RAMAN_TENSOR_CALCULATION.ipynb','ROTATION_RAMAN_TENSOR_CALCULATION.py','raman_engine.py','web_bridge.py','sci.mplstyle','requirements.txt','README.txt','Optical_Methods_Guide.md','Symbols_And_References.md','QUICKSTART.md','SAITO_FEEDBACK_AUDIT.md','example_input_v5.json','silicon_startup_input_v5.json','Silicon_Startup_Polar_Plot.png','Reference_Equation_Checks.md','Reference_Equation_Checks.json']:
        archive.write(DOWNLOADS/name,name)
    # Original third-party reference notebooks remain separate from the project ZIP.

# Each published revision has a separate filename. Keep the stable names as
# compatibility copies, but use the named revision for the website's main links.
stem='261024 - Raman Tensor Rotation Ver 5.0'
named_files={
    'notebook':(stem+'.ipynb','ROTATION_RAMAN_TENSOR_CALCULATION.ipynb'),
    'python':(stem+'.py','ROTATION_RAMAN_TENSOR_CALCULATION.py'),
}
for filename,canonical in named_files.values():
    shutil.copy2(DOWNLOADS/canonical,DOWNLOADS/filename)
bundle_names={canonical:filename for filename,canonical in named_files.values()}
bundle_path=DOWNLOADS/(stem+'.zip')
with zipfile.ZipFile(DOWNLOADS/'All_Python_Programs.zip') as original:
    with zipfile.ZipFile(bundle_path,'w',zipfile.ZIP_DEFLATED) as bundle:
        for entry in original.infolist():
            bundle.writestr(bundle_names.get(entry.filename,entry.filename),original.read(entry.filename))
named_files['bundle']=(bundle_path.name,'All_Python_Programs.zip')
release=dict(version='5',revision=revision,source_sha256=source_hash,code_cells=22,
    default_input=dict(material='Si',hkl=[5,0,0],optics='CUBIC_VV'),files={})
for key,(filename,canonical) in named_files.items():
    payload=(DOWNLOADS/filename).read_bytes()
    release['files'][key]=dict(filename=filename,canonical=canonical,
        sha256=hashlib.sha256(payload).hexdigest(),size_bytes=len(payload))
release['assets']={path.name:hashlib.sha256(path.read_bytes()).hexdigest()
    for path in DOWNLOADS.iterdir() if path.is_file() and path.name!='RELEASE_MANIFEST.json'}
(DATA/'release.json').write_text(json.dumps(release,indent=2)+'\n')
(DOWNLOADS/'RELEASE_MANIFEST.json').write_text(json.dumps(release,indent=2)+'\n')
readme_path=PROJECT/'README.md'
readme_text=readme_path.read_text()
for label,key in [('Download the current Python notebook','notebook'),('Download all Python programs','bundle')]:
    record=release['files'][key]
    pattern=r'(\['+re.escape(label)+r'\]\()([^\n)]+/downloads/)[^\n)]+(\))'
    readme_text=re.sub(pattern,lambda match:match[1]+match[2]+record['filename'].replace(' ','%20')+'?sha='+record['sha256'][:12]+match[3],readme_text)
readme_path.write_text(readme_text)

# Browser caches must see a new URL whenever first-party JavaScript or CSS changes.
worker_fingerprint=hashlib.sha256((DIST/'engine-worker.js').read_bytes()).hexdigest()[:12]
app_path=DIST/'app.js'
app_text=app_path.read_text()
app_text=re.sub(r'\./engine-worker\.js(?:\?[^\x27\x22\s]*)?', './engine-worker.js?v=5-'+worker_fingerprint, app_text)
app_path.write_text(app_text)
index=(DIST/'index.html').read_text()
index=re.sub(r' data-(?:full-site|calculator-site)="[^"]*"', '', index)
index=index.replace('<body class="desktop-nav-hidden">', '<body class="desktop-nav-hidden" data-full-site="https://faizal-07-script.github.io/rotation-raman-tensor-calculation/" data-calculator-site="https://faizal-07-script.github.io/raman-tensor-calculator/">')
for name in ('app.js','content.js','optical-guide.js','user-guide.js','styles.css','user-guide.css','calculator-ui.js','calculator.css'):
    fingerprint=hashlib.sha256((DIST/name).read_bytes()).hexdigest()[:12]
    index=re.sub(re.escape('./'+name)+r'(?:\?[^"\s]*)?', './'+name+'?v=5-'+fingerprint,index)
(DIST/'index.html').write_text(index)
calculator_page=index.replace('<title>Rotation Raman Tensor Calculation</title>', '<title>Raman Tensor Calculator</title>')
calculator_page=calculator_page.replace('<body class="desktop-nav-hidden"', '<body class="desktop-nav-hidden calculator-only" data-calculator-only="true"')
(DIST/'calculator.html').write_text(calculator_page)
print('Prepared 22 cells,',sum(len(x['blocks']) for x in annotations),'annotated code blocks and Python downloads.',flush=True)
