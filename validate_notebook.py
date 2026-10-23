"""Execute the current notebook and check the corrected inactive-field path."""
import base64
import copy
import io
import json
import os
import time
from pathlib import Path
os.environ['MPLBACKEND']='Agg'
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from ipywidgets.embed import dependency_state,embed_data
P=Path(__file__).resolve().parent/'sources/notebook_v4.ipynb'
book=nbformat.read(P,as_version=4);shell=InteractiveShell.instance();started=time.time()
for cell in book.cells:
    if cell.cell_type!='code':continue
    with capture_output() as captured:result=shell.run_cell(cell.source,store_history=True)
    assert result.success,(cell.metadata['code_cell_number'],captured.stdout,captured.stderr)
    expected_message=f"Cell {cell.metadata['code_cell_number']:02d}/22 — This cell runs correctly."
    assert expected_message in captured.stdout,(expected_message,captured.stdout)
    cell.execution_count=shell.execution_count-1;cell.outputs=[]
    for name,value in [('stdout',captured.stdout),('stderr',captured.stderr)]:
        if value:cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=value))
    for output in captured.outputs:cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
ns=shell.user_ns
assert ns['state']['validation']['status']=='passed', ns['state']['validation']
assert len(ns['state']['run']['display_channels'])==3
assert len(ns['state']['run']['angles'])==721
with capture_output():
    ns['optics_pick'].value='CIRCULAR_SAME';ns['circular_charges'].value='';ns['on_run']()
assert ns['state']['last_error'] is not None
with capture_output():
    ns['circular_dm'].value='not-an-integer';ns['optics_pick'].value='CUBIC_VV';ns['on_run']()
assert ns['state']['last_error'] is None,ns['state']['last_error']
with capture_output():
    ns['optics_pick'].value='CIRCULAR_SAME';ns['on_run']()
assert ns['state']['last_error'] is not None
with capture_output():
    ns['load_configuration'](ns['slide_component_config']());ns['on_run']()
assert ns['state']['last_error'] is None
book.metadata['widgets']={'application/vnd.jupyter.widget-state+json':embed_data([ns['app_view']],state=dependency_state([ns['app_view']]))['manager_state']}
last=next(c for c in reversed(book.cells) if c.cell_type=='code')
for name,figure in ns['state']['figures']:
    if name.startswith('polar_'):
        b=io.BytesIO();figure.savefig(b,format='png',dpi=110,bbox_inches='tight',transparent=False,facecolor='white')
        last.outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(b.getvalue()).decode()},metadata={}))
record=dict(status='passed',version='4',checks=ns['state']['validation']['checks'],
    cell_completion_messages=22,
    example_input='Built-in slide_component_config(): no user edits or external input file required.',
    optical_reference=ns['state']['validation']['optical_reference'],
    inactive_circular_rule_fields='Noncircular profiles ignore inactive charge fields; circular profiles still reject invalid charges.',
    elapsed_seconds=round(time.time()-started,2))
book.metadata['rotation_raman_revision']['validation']=record
nbformat.validate(book);nbformat.write(book,P)
(Path(__file__).resolve().parent/'notebook_verification.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2),flush=True)
