"""Execute all 22 cells and verify the visible silicon startup and inactive fields."""
import base64
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
    expected_message=f"Cell {cell.metadata['code_cell_number']:02d}/22 — Run completed successfully."
    assert expected_message in captured.stdout,(expected_message,captured.stdout)
    assert 'Ready:' in captured.stdout and 'Next:' in captured.stdout
    cell.execution_count=shell.execution_count-1;cell.outputs=[]
    for name,value in [('stdout',captured.stdout),('stderr',captured.stderr)]:
        if value:cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=value))
    for output in captured.outputs:cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
ns=shell.user_ns
assert ns['state']['validation']['status']=='passed', ns['state']['validation']
startup=ns['state']['run']
cfg=startup['config']
assert (cfg['material'],cfg['point_group'],cfg['optics'])==('Si','Oh','CUBIC_VV')
assert tuple(cfg['hkl'])==(5,0,0) and tuple(cfg['uvw'])==(0,-5,0)
assert cfg['normal_sign']==1 and not cfg['normalize']
assert cfg['modes']==['T2g'] and cfg['mode_values']['T2g'][ns['d']]==1
assert list(startup['display_channels'])==['T2g']
assert len(startup['angles'])==721
assert ns['example_pick'].value=='SI_500'
assert ns['tabs'].selected_index==ns['tab_index']['Polar plots']
theta=startup['angles'];curve=startup['display_curves']['T2g']
reference=ns['np'].sin(2*theta)**2
ns['np'].testing.assert_allclose(curve,reference,rtol=0,atol=1e-10)
ns['np'].testing.assert_allclose(curve[[0,90,180,540,720]],
                               [0,1,0,0,0],rtol=0,atol=1e-10)
last=next(c for c in reversed(book.cells) if c.cell_type=='code')
images=[o for o in last.outputs if 'raman_startup_plot' in o.get('metadata',{})]
assert len(images)==1 and 'image/png' in images[0]['data'], [(list(o.get('data',{})),o.get('metadata',{})) for o in last.outputs if o.get('output_type')=='display_data']
assert images[0]['metadata']['raman_startup_plot']==dict(material='Si',surface=[5,0,0],optics='CUBIC_VV',channel='T2g')
png=base64.b64decode(images[0]['data']['image/png'])
assert png.startswith(b'\x89PNG\r\n\x1a\n')
app_outputs=[i for i,o in enumerate(last.outputs) if 'application/vnd.jupyter.widget-view+json' in o.get('data',{})
             and o['data']['application/vnd.jupyter.widget-view+json']['model_id']==ns['app_view'].model_id]
assert app_outputs and last.outputs.index(images[0])<app_outputs[0]
equations=[item for item in ns['state']['derivation']['entries'] if item['kind']=='equation']
assert all(item.get('symbols') and item.get('reference_ids') and item.get('derivation_note') for item in equations)
assert all(symbol['meaning'] and symbol['units'] for item in equations for symbol in item['symbols'])
assert ns['state']['derivation']['markdown'].count('**Symbols and units**')==len(equations)
with capture_output():ns['start_application']()
assert ns['state']['run'] is startup, 'Redisplay must preserve the current calculation.'
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
    ns['load_configuration'](ns['cubic_fig1_config'](0,'VV'));ns['on_run']()
    ns['tabs'].selected_index=ns['tab_index']['Polar plots']
assert ns['state']['last_error'] is None
book.metadata['widgets']={'application/vnd.jupyter.widget-state+json':embed_data([ns['app_view']],state=dependency_state([ns['app_view']]))['manager_state']}
(P.parents[1]/'dist/downloads/Silicon_Startup_Polar_Plot.png').write_bytes(png)
record=dict(status='passed',version='4',checks=ns['state']['validation']['checks'],
    cell_completion_messages=22,
    example_input='Built-in cubic_fig1_config(0, "VV"): Si (500), T2g, d=1; no edits or external file required.',
    startup_test=dict(material='Si',point_group='Oh',hkl=[5,0,0],uvw=[0,-5,0],
        optics='CUBIC_VV',mode='T2g',coefficient_d=1,samples=721,
        reference_equation='sin(2θ)^2',absolute_tolerance=1e-10,
        maximum_residual=float(ns['np'].max(ns['np'].abs(curve-reference))),
        sampled_maximum=float(curve.max()),continuous_maximum=1,
        inline_png_before_interface=True,selected_result_tab='Polar plots',
        redisplay_preserves_calculation=True),
    success_output='Each of 22 cells prints Run completed successfully., a Ready explanation and a Next action.',
    annotated_derivation=dict(equations=len(equations),all_symbols_have_meanings_and_units=True,
                              source_notes_per_equation=True,shared_notebook_web_and_latex=True),
    optical_reference=ns['state']['validation']['optical_reference'],
    inactive_circular_rule_fields='Noncircular profiles ignore inactive charge fields; circular profiles still reject invalid charges.',
    elapsed_seconds=round(time.time()-started,2))
book.metadata['rotation_raman_revision']['validation']=record
nbformat.validate(book);nbformat.write(book,P)
(Path(__file__).resolve().parent/'notebook_verification.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2),flush=True)
