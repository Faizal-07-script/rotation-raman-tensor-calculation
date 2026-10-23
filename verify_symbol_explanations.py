"""Check local symbol definitions, SI/relative units, sources and matching exports."""
import io
import json
import os
import runpy
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if os.environ.get('RAMAN_PYTHON_DEPENDENCY_PATH'):
    sys.path.insert(0,os.environ['RAMAN_PYTHON_DEPENDENCY_PATH'])
ns=runpy.run_path(str(ROOT/'dist/raman_engine.py'))
exec((ROOT/'web_bridge.py').read_text(),ns)
np=ns['np']
catalog=ns['web_catalog']()
assert catalog['default_example']=='SI_500'
assert catalog['examples']['SI_500']['config']['hkl']==[5,0,0]

def definitions(value,scope='algebra',**kwargs):
    return {row['id']:row for row in ns['equation_symbol_definitions'](value,scope=scope,**kwargs)}

# Deliberately overloaded notation must resolve to the actual physical role.
assert 'source_A' not in definitions(r'\mathcal A=e_s^\dagger R_\perp E_i')
assert 'frame' not in definitions(r'L^{-T}=\begin{pmatrix}1&0&0\\0&1&0\\0&0&1\end{pmatrix}',scope='geometry')
assert 'frame' in definitions(r'T^{-1}=T^T')
assert 'source_A' in definitions(r'R_{ref}=\begin{pmatrix}a&Ae^{i\delta}\\-Ae^{i\delta}&ae^{i\phi}\end{pmatrix}')
assert 'coefficients' not in definitions(r'S_3(e)=2\operatorname{Im}(e_X^*e_Y)',scope='optics')
assert 'coefficients' not in definitions(r'\frac{dI}{d\theta}=-2I_c\sin2\theta',scope='final')
physical=definitions(r'\mathbf P_R^{phys,(m)}=\epsilon_0R_\chi^{(m)}\mathbf E_{i,c}^{phys}u_m')
assert 'coefficients' not in physical and 'imaginary_unit' not in physical
assert physical['physical_polarization']['units']=='C m^-2 in SI'
assert physical['physical_electric_field']['units']=='V m^-1 in SI'
assert physical['vacuum_permittivity']['units']=='F m^-1 in SI'
assert 'incident_state' not in physical
assert 'projector' in definitions(r'R_\perp=PR_{lab}P^T')
assert 'projector' not in definitions(r'\mathcal P_c=R_cE_{i,c}')
assert 'norm' not in definitions(r'R_{\chi,ij}^{(m)}=\left.\partial\chi_{ij}/\partial u_m\right|_0')
assert 'equilibrium_evaluation' in definitions(r'R_{\chi,ij}^{(m)}=\left.\partial\chi_{ij}/\partial u_m\right|_0')
assert definitions(r'\theta_{max}\ (\mathrm{degree})=45')['linear_angle']['units'].startswith('degree')

equation_count=0
examples=[]
for key,item in catalog['examples'].items():
    run=ns['calculate_general'](ns['web_configuration'](item['config']))
    trace=ns['detailed_calculation'](run)
    equations=[entry for entry in trace['entries'] if entry['kind']=='equation']
    assert equations and all(entry['symbols'] for entry in equations)
    for entry in equations:
        assert entry['derivation_note'] and entry['reference_ids']
        assert all(ref in ns['DERIVATION_REFERENCES'] for ref in entry['reference_ids'])
        assert all(row['meaning'] and row['units'] for row in entry['symbols'])
        assert len({row['id'] for row in entry['symbols']})==len(entry['symbols'])
    assert trace['markdown'].count('**Symbols and units**')==len(equations)
    tex=ns['paper_intensity_latex'](run,trace)
    assert tex['full'].count('Symbols and units')==len(equations)
    assert 'Symbols and units' in tex['symbolic'] and 'Symbols and units' in tex['numerical']
    equation_count+=len(equations)
    examples.append(dict(key=key,equations=len(equations),definitions=sum(len(e['symbols']) for e in equations)))

    if key=='SI_500':
        np.testing.assert_allclose(run['display_curves']['T2g'],np.sin(2*run['angles'])**2,atol=1e-12,rtol=0)
        archive=ns['make_general_archive'](run,[],trace)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            assert z.testzip() is None
            assert json.loads(z.read('mathematical_steps.json'))==trace['entries']
            assert z.read('calculation_steps.md').decode()==trace['markdown']
            assert z.read('calculation_full.tex').decode()==tex['full']
            assert json.loads(z.read('derivation_references.json'))==ns['DERIVATION_REFERENCES']
            assert z.read('symbols_and_references.md').decode()==ns['symbols_and_references_markdown']()

# All nine optical profiles must preserve the same annotation contract.
profiles=[]
for profile in catalog['profiles']:
    cfg=ns['cubic_fig1_config'](0,'VV')
    cfg['optics']=profile
    cfg['paper_parameters']={**ns['default_paper_parameters']('CIRCULAR'),'theta0_deg':0,'analyzer_zero_deg':0}
    run=ns['calculate_general'](cfg)
    trace=ns['detailed_calculation'](run)
    assert all(e['symbols'] and e['reference_ids'] for e in trace['entries'] if e['kind']=='equation')
    if profile in ['CUBIC_VV','CUBIC_VH']:
        expected=np.sin(2*run['angles'])**2 if profile=='CUBIC_VV' else np.cos(2*run['angles'])**2
        np.testing.assert_allclose(run['display_curves']['T2g'],expected,atol=1e-12,rtol=0)
    profiles.append(profile)

record=dict(status='passed',version='4',startup=dict(material='Si',surface=[5,0,0],optics='CUBIC_VV'),
    examples=examples,total_example_equations=equation_count,profiles=profiles,
    overloaded_symbols='Calligraphic amplitude/source A; unit Jones/physical E; projection/response/physical P; phase, transpose and equilibrium evaluation.',
    units='Local meanings and unit conventions checked for every calculated equation across all examples and profiles.',
    exports='Markdown, JSON and all three LaTeX documents preserve the same definitions and reference ledger.')
(ROOT/'symbol_explanations_verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
