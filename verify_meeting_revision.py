"""Regression checks for the November 2 tensor-entry and derivation revision."""
import copy
import hashlib
import json
import runpy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
ns = runpy.run_path(str(ROOT/'dist/raman_engine.py'))
exec((ROOT/'web_bridge.py').read_text(),ns)
sp=ns['sp']
checks=[]

catalog=ns['web_catalog']()
assert catalog['materials']['Si']['definitions']['T2g']['components']==['yz/zy','xz/zx','xy/yx']
checks.append('Si matrices are named by their original Cartesian entries.')

cfg=ns['cubic_fig1_config'](0,'VV')
run=ns['calculate_general'](cfg)
trace=ns['detailed_calculation'](run)
np.testing.assert_allclose(run['curves']['T2g'],np.sin(2*run['angles'])**2,atol=2e-12,rtol=0)
for phase in [0,90,180,-90,360]:
    trial=copy.deepcopy(cfg)
    trial['mode_values']['T2g'][ns['d']]=ns['complex_parameter'](1,phase)
    value=ns['calculate_general'](trial)
    np.testing.assert_allclose(value['curves']['T2g'],run['curves']['T2g'],atol=2e-12,rtol=0)
    review=ns['prepare_input_review'](trial)
    actual=[e for e in review['entries'] if e.get('explanation')=='This is the actual complex value inserted into the tensor.']
    assert actual and actual[0]['value']=='d='+ns['raman_latex'](trial['mode_values']['T2g'][ns['d']])
checks.append('Coefficient phases 0°, ±90°, 180°, 360° are retained in the review; a common Si tensor phase preserves intensity.')
assert ns['complex_parameter'](1,90)==sp.I
assert ns['complex_parameter'](1,180)==-1
assert ns['complex_parameter'](0,37)==0
checks.append('The displayed examples 1, i, −1 and the zero-size limit match the complex inputs.')

for entry in trace['entries']:
    if entry['kind']=='section':assert 'partner' not in entry['value'].lower()
    if entry['kind']=='equation':
        assert 'partner' not in entry['explanation'].lower()
        assert r'R_{lab}\ne |T^TR_cT|^2' not in entry['value']
        if entry['step']=='02.04':assert 'inputs' in entry['explanation']
phase_definition=ns['equation_symbol_definitions'](r'd=|d|e^{i\phi_{d}}')
assert next(x for x in phase_definition if x['id']=='coefficient_phase')['latex']==r'\phi_{d}'
checks.append('Definitions precede use; selected phases have local labels, and surface indices are identified as inputs.')

# Full Ag amplitude must retain interference even when separate component plots
# hide it. Compare the new displayed complete-tensor formula with engine arrays.
ag=ns['general_config']('GENERAL','CUBIC_VV')
ag.update(point_group='D2h',hkl=(1,0,0),uvw=(0,1,0),normal_sign=1,modes=['Ag'])
ag['mode_values']['Ag']={ns['a']:1,ns['b']:1,ns['c']:-1}
ag_run=ns['calculate_general'](ag)
ag_trace=ns['detailed_calculation'](ag_run)
final=ag_trace['complete_finals'][0]
actual=sp.lambdify(final['variable'],final['substituted'],'numpy')(ag_run['angles'])
np.testing.assert_allclose(actual,ag_run['curves']['Ag'],atol=2e-12,rtol=0)
np.testing.assert_allclose(actual,np.cos(2*ag_run['angles'])**2,atol=2e-12,rtol=0)
component_sum=sum(ag_run['display_curves'].values())
assert np.max(np.abs(actual-component_sum))>0.4
checks.append('The complete Ag equation retains destructive interference; separate Cartesian powers remain separate.')

report=ns['reference_analytic_report']()
assert report['status']=='passed' and report['passed']==report['total']==22
published=json.loads((ROOT/'dist/data/reference-equation-checks.json').read_text())
assert published['engine_sha256']==hashlib.sha256((ROOT/'dist/raman_engine.py').read_bytes()).hexdigest()
assert published['checks']==report['checks']
checks.append('All 22 paper-equation checks pass; the published evidence identifies the current engine.')

record=dict(status='passed',revision='2026-11-02-r1',checks=checks,
            engine_sha256=hashlib.sha256((ROOT/'dist/raman_engine.py').read_bytes()).hexdigest(),
            scope='Input meanings, source equations, coherent Ag derivation and unchanged Si response. No independent colleague or experimental review is claimed.')
(ROOT/'meeting_revision_verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
