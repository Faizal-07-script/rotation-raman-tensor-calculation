"""Verify explicit displayed formulas against the sampled matrix calculation."""
from pathlib import Path
import copy
import hashlib
import json
import re
import runpy
import time
import numpy as np

ROOT=Path(__file__).resolve().parent
ns=runpy.run_path(str(ROOT/'dist/raman_engine.py'))
exec((ROOT/'web_bridge.py').read_text(),ns)
sp=ns['sp']
started=time.time()
reports=[]
profiles=list(ns['GENERAL_PROFILES'])

def check_case(label,cfg):
    cfg=copy.deepcopy(cfg)
    cfg['plot_points']=361
    original=ns['serializable'](copy.deepcopy(cfg))
    before=ns['WEB_STATE']['run']
    review=ns['prepare_input_review'](cfg)
    assert ns['serializable'](cfg)==original
    assert ns['WEB_STATE']['run'] is before, 'Input review replaced a calculated result'
    if review['geometry'] is not None:
        T=ns['numeric'](review['geometry']['T']).real
        np.testing.assert_allclose(T.T@T,np.eye(3),atol=2e-12)
        np.testing.assert_allclose(np.linalg.det(T),1,atol=2e-12)
    run=ns['calculate_general'](cfg)
    derivation=ns['detailed_calculation'](run)
    bad=re.compile(r'K_(?:\{[0cs]\}|[0cs])|(?<![A-Za-z])[CD](?![A-Za-z])')
    for entry in derivation['entries']:
        if entry['kind']=='equation':
            assert not bad.search(entry['value']), (label,entry['value'])
            assert entry.get('explanation') and entry.get('step')
    residual=0.0
    for final in derivation['finals']:
        values=sp.lambdify(final['variable'],final['substituted'],'numpy')(run['angles'])
        values=np.broadcast_to(np.asarray(values,dtype=complex),run['angles'].shape)
        expected=run['display_curves'][final['channel']]
        scale=max(float(np.max(np.abs(expected))),1e-12)
        error=float(np.max(np.abs(values-expected)))/scale
        assert error<2e-9, (label,final['channel'],error)
        residual=max(residual,error)
    reports.append(dict(case=label,channels=len(derivation['finals']),equations=sum(e['kind']=='equation' for e in derivation['entries']),maximum_relative_residual=residual))
    print(label,'passed',flush=True)

for profile in profiles:
    cfg=ns['general_config']('CaNb2O6',profile)
    cfg.update(hkl=(2,1,1),uvw=(0,1,-1),modes=['Ag','B1g'])
    for name,values in cfg['mode_values'].items():
        for index,symbol in enumerate(values):values[symbol]=sp.Rational(index+2,2)*(sp.I if index%2 else 1)
    check_case('Complex Ag/B1g (211): '+profile,cfg)

for k in range(6):
    cfg=ns['cubic_fig1_config'](k,'VV',1,361)
    check_case('Silicon (5'+str(k)+'0), VV',cfg)
check_case('Original effective 2D optical source',ns['qwp_source_config']())

# Invalid geometry must fail in the preparation stage, before an intensity scan.
cfg=ns['general_config']('Si','CUBIC_VV')
cfg.update(hkl=(1,0,0),uvw=(1,0,0))
try:ns['prepare_input_review'](cfg)
except ValueError:invalid_rejected=True
else:raise AssertionError('Invalid in-plane direction passed input review')

report=dict(status='passed',revision='2026-11-02-r1',cases=reports,
            engine_sha256=hashlib.sha256((ROOT/'dist/raman_engine.py').read_bytes()).hexdigest(),
            total_cases=len(reports),invalid_geometry_rejected_before_intensity=invalid_rejected,
            scope='Displayed expressions, input preparation, and unchanged matrix-response arrays. This is not new experimental validation.',
            elapsed_seconds=round(time.time()-started,2))
(ROOT/'explicit_derivation_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}),flush=True)
