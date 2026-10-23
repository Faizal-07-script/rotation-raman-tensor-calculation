"""Browser adapter for the unchanged scientific functions in notebook version 4.

The notebook supplies all tensors, rotations, Jones states, amplitudes,
mathematical traces, validation and scientific figures. This adapter validates
JSON inputs and returns browser-readable results; it does not supply any
reference intensity formula or fit a curve.
"""

WEB_STATE = dict(run=None, derivation=None, figures=[], comparisons=[], benchmark=None, validation=None)


def web_progress(message):
    try:
        from js import pythonProgress
        pythonProgress(str(message))
    except ImportError:
        pass


def web_json(value):
    return json.dumps(serializable(value), ensure_ascii=False, allow_nan=False)


def web_form(cfg):
    """Convert an actual notebook configuration to explicit visible form values."""
    data = copy.deepcopy(cfg)
    data['mode_values'] = {
        name: {str(symbol): dict(magnitude=float(sp.N(sp.Abs(value))),
                                  phase=float(sp.N(sp.arg(value)*180/sp.pi)) if value != 0 else 0)
               for symbol, value in values.items()}
        for name, values in cfg.get('mode_values', {}).items()
    }
    if cfg.get('custom_tensor') is not None:
        data['custom_tensor'] = [[str(complex(sp.N(x))) for x in row]
                                 for row in sp.Matrix(cfg['custom_tensor']).tolist()]
    data['lattice'] = [float(x) for x in cfg.get('lattice', [1,1,1,90,90,90])]
    data['T_manual'] = [[float(x) for x in row] for row in sp.Matrix(cfg.get('T_manual', sp.eye(3))).tolist()]
    if cfg.get('direct_jones'):
        data['direct_jones'] = {key: float(value) for key, value in cfg['direct_jones'].items()}
    data['paper_parameters'] = {
        **default_paper_parameters('CIRCULAR'), 'theta0_deg': 0,
        'analyzer_zero_deg': 0 if cfg['optics'].startswith('CIRCULAR_') else 45,
        **(cfg.get('paper_parameters') or {}),
    }
    return serializable(data)


def web_mode_definition(definition):
    return dict(irrep=definition['irrep'], parameters=[str(s) for s in parameters_for(definition)],
                tensors=[sp.latex(R) for R in definition['partners']],
                partners=len(definition['partners']), note=definition.get('note',''))


def web_catalog():
    materials = {}
    for key, material in MATERIALS.items():
        materials[key] = {**material,
            'definitions': {name:web_mode_definition(item) for name,item in definitions_for(key, material['group']).items()},
            'defaults': web_form(general_config(key))}
    groups = {}
    for key, group in POINT_GROUPS.items():
        definitions = definitions_for('GENERAL', key)
        groups[key] = {k:v for k,v in group.items() if k != 'tensors'}
        groups[key]['definitions'] = {name:web_mode_definition(item) for name,item in definitions.items()}
    examples = {
        'SLIDE': ('Slide-frame Ag components (211)', slide_component_config()),
        'QWP_3D': ('3D crystal with QWP optics', physical_start_config()),
        'QWP_2D': ('Original complex 2D optical reference', qwp_source_config()),
        'LINEAR_BP': ('Complex linear BP reference', linear_bp_reference_config()),
        'CIRCULAR_MOS2': ('Circular-channel monolayer MoS2 example', circular_mos2_reference_config()),
        'SI_500': ('Silicon (500), VV startup example', cubic_fig1_config(0,'VV')),
        'SI_530': ('Silicon (530), VV reference frame', cubic_fig1_config(3,'VV')),
    }
    demo = optical_profile_example()
    example_guide = dict(scope=demo['scope'], tensor=sp.latex(demo['tensor']),
        angles=[0,30,45,90], profiles={key:dict(intensity=sp.latex(value['intensity']),
        values=[float(value['intensity'].subs(alpha,deg(angle))) for angle in [0,30,45,90]])
        for key,value in demo['profiles'].items()})
    return dict(version=AUDIT_VERSION, default_example='SI_500', materials=materials, groups=groups, optical_example=example_guide,
        profiles=GENERAL_PROFILES, optical_guide=optical_method_catalog(),
        derivation_references=DERIVATION_REFERENCES,
        home_equation=annotate_equation(r'R_{lab}=T^TR_cT,\qquad \mathcal A=e_s^\dagger R_\perp E_i,\qquad I=|\mathcal A|^2',scope='record'),
        examples={key:dict(label=value[0],config=web_form(value[1])) for key,value in examples.items()},
        surfaces={**SURFACES, **{f'(5{k}0)':((5,k,0),(k,-5,0)) for k in range(6)}},
        style=PLOT_STYLE_STATUS, sources=UPGRADE_SOURCES,
        validation_procedures=checking_procedure_catalog(),validation_source=OPTICAL_REFERENCE_SOURCE,
        parameter_defaults={str(symbol):dict(magnitude=float(sp.Abs(value)),phase=0) for symbol,value in DEFAULT_VALUES.items()})


def web_configuration(data):
    """Accept finite numerical inputs only; never evaluate source from the form."""
    if data.get('tensor_model') == 'QWP_SOURCE_2D':
        cfg = qwp_source_config()
        cfg['source_parameters'] = {key:exact(real_number(data.get('source_parameters',{}).get(key, value), key))
                                    for key,value in cfg['source_parameters'].items()}
    else:
        cfg = general_config(data.get('material','Si'), data.get('optics','CUBIC_VV'))
        group = data.get('point_group', cfg['point_group'])
        definitions = definitions_for(cfg['material'], group)
        modes = data.get('modes', list(definitions))
        if not isinstance(modes, list) or not modes:
            raise ValueError('Select at least one mode or branch.')
        if any(name not in definitions for name in modes):
            raise ValueError('A selected mode does not belong to the current material or point group.')
        values = {}
        for name in modes:
            values[name] = {}
            for symbol in parameters_for(definitions[name]):
                pair = data.get('mode_values',{}).get(name,{}).get(str(symbol))
                if not isinstance(pair,dict):
                    raise ValueError(f'Enter magnitude and phase for {name}: {symbol}.')
                values[name][symbol] = complex_parameter(pair.get('magnitude'), pair.get('phase'))
        lattice = data.get('lattice',cfg['lattice'])
        if not isinstance(lattice,list) or len(lattice)!=6:
            raise ValueError('Enter three lattice lengths and three lattice angles.')
        hkl = [circular_integer(v,'Miller index') for v in data.get('hkl',[2,1,1])]
        if len(hkl)!=3:
            raise ValueError('Miller indices require three integers.')
        uvw = data.get('uvw')
        if uvw is not None:
            uvw = [circular_integer(v,'In-plane index') for v in uvw]
            if len(uvw)!=3:raise ValueError('The in-plane direction requires three integers.')
        paper = {**default_paper_parameters('CIRCULAR'), 'theta0_deg':0, 'analyzer_zero_deg':45}
        supplied = data.get('paper_parameters') or {}
        paper['theta0_deg'] = exact(supplied.get('theta0_deg',0))
        paper['analyzer_zero_deg'] = exact(supplied.get('analyzer_zero_deg',45))
        # Rule-only fields are validated only for a selected circular profile.
        # An inactive hidden field cannot block VV, VH, QWP or direct Jones.
        if cfg['optics'].startswith('CIRCULAR_'):
            paper.update({key:supplied[key] for key in paper if key in supplied})
            if paper['s_in'] not in [-1,1]:raise ValueError('Choose a circular basis label of +1 or -1.')
            paper['N'] = circular_integer(paper['N'],'Cyclic order')
            paper['ell_i'] = circular_integer(paper['ell_i'],'Incident orbital charge')
            if not isinstance(paper['m_ph'],list) or not paper['m_ph']:
                raise ValueError('Enter at least one integer phonon charge for the conditional rule check.')
            paper['m_ph'] = [circular_integer(x,'Phonon charge') for x in paper['m_ph']]
            if paper.get('absorption_delta_m') is not None:
                paper['absorption_delta_m'] = circular_integer(paper['absorption_delta_m'],'Absorption charge')
        custom = None
        if group=='CUSTOM':
            raw = data.get('custom_tensor')
            if not isinstance(raw,list) or len(raw)!=3 or any(not isinstance(row,list) or len(row)!=3 for row in raw):
                raise ValueError('The custom tensor requires a 3 by 3 JSON array.')
            custom = sp.Matrix([[parse_complex(x) for x in row] for row in raw])
        direct = data.get('direct_jones') or dict(theta_i_deg=45,beta_i_deg=90,theta_s0_deg=45,beta_s_deg=0)
        direct = {key:exact(direct[key]) for key in ['theta_i_deg','beta_i_deg','theta_s0_deg','beta_s_deg']}
        orientation = data.get('orientation','hkl')
        matrix = sp.eye(3)
        if orientation=='matrix':
            raw = data.get('T_manual')
            if not isinstance(raw,list) or len(raw)!=3 or any(len(row)!=3 for row in raw):
                raise ValueError('A manual frame requires a real 3 by 3 matrix.')
            matrix = sp.Matrix([[exact(x) for x in row] for row in raw])
        cfg.update(point_group=group,modes=modes,mode_values=values,custom_tensor=custom,
            lattice=tuple(exact(x) for x in lattice),hkl=tuple(hkl),uvw=tuple(uvw) if uvw is not None else None,
            orientation=orientation,T_manual=matrix,normal_sign=circular_integer(data.get('normal_sign',-1),'Normal side'),
            azimuth_deg=exact(data.get('azimuth_deg',0)),paper_parameters=paper,direct_jones=direct)
    points = circular_integer(data.get('plot_points',721),'Angular sample count')
    if points not in [361,721,3601]:raise ValueError('Choose a supported angular grid.')
    label = str(data.get('case_label','Raman tensor calculation')).strip()[:180]
    if not label:label='Raman tensor calculation'
    cfg.update(case_label=label,input_note=str(data.get('input_note',''))[:1200],
               plot_points=points,normalize=bool(data.get('normalize',False)),
               cartesian_plots=bool(data.get('cartesian_plots',False)),
               show_geometry=bool(data.get('show_geometry',True)),show_steps=True)
    return cfg


def web_figure_view(name, figure):
    svg=io.StringIO();figure.savefig(svg,format='svg',bbox_inches='tight',transparent=True)
    png=io.BytesIO();figure.savefig(png,format='png',dpi=115,bbox_inches='tight',transparent=False,facecolor='white')
    return dict(name=name,svg=svg.getvalue(),png='data:image/png;base64,'+base64.b64encode(png.getvalue()).decode())


def web_result(run, derivation, figures):
    rows=[]
    for name,item in run['display_channels'].items():
        rows.append(dict(name=name,kind=item['kind'],component=item['component'],summary=item['summary'],
            points=item['curve'],optics=item['optical']['kind'],
            scale=channel_display_scales(run)[item['normalization_group']] if run['config'].get('normalize') else 1))
    tex=paper_intensity_latex(run,derivation)
    states={name:{key:value for key,value in profile.items() if key not in ['effective_incident','effective_detection','return_optics']}
            for name,profile in run['physics']['optical_states'].items()}
    frame=None
    if run['geometry'] is not None:
        g=run['geometry'];T=g['T']
        frame=dict(T=numeric(T).real,T_inverse=numeric(T.T).real,
            determinant=float(sp.N(T.det())),orthogonality_error=float(np.max(np.abs(numeric(T.T*T)-np.eye(3)))),
            lattice=sp.latex(g['L']),tensor_frame=sp.latex(T),notes=g.get('notes',[]))
    return dict(version=AUDIT_VERSION,case=run['config']['case_label'],
        configuration=web_form(run['config']),channels=rows,
        angles=np.rad2deg(run['angles']),scan_label=run['scan_label'],scan_basis=run['optical']['scan_basis'],
        figures=[web_figure_view(name,figure) for name,figure in figures],
        equations=derivation['entries'],equation_count=sum(x['kind']=='equation' for x in derivation['entries']),
        derivation_references=DERIVATION_REFERENCES,
        latex=tex,csv=csv_from_curves(run['angles'],run['display_curves'],'theta_deg' if run['optical']['scan_basis']=='SECOND' else 'alpha_deg'),
        checks=matching_protocol_audit(run),protocols=protocol_state_comparison(),states=states,
        interference=[dict(mode=name,maximum_cross_term=float(np.max(np.abs(item['interference']))),
            absolute_error=item.get('absolute_difference_from_selected'),roundoff_bound=item.get('power_roundoff_bound'))
            for name,item in run['physics']['interference'].items()],
        frame=frame,style=run['style'],assumptions=run['assumptions'],policy=run['presentation_policy'],
        circular=run.get('circular'),checking_report=run["checking_procedures"])


def web_calculate(input_json):
    data=json.loads(input_json)
    cfg=web_configuration(data)
    web_progress('Calculating the rotated tensor and intensity…')
    run=calculate_general(cfg)
    web_progress('Checking the result…')
    run["checking_procedures"]=checking_procedures_for_run(run)
    web_progress('Preparing the equations…')
    derivation=detailed_calculation(run)
    web_progress('Drawing the figures…')
    figures=publication_figures(run)
    if cfg.get('show_geometry'):
        frame=publication_orientation(run)
        if frame is not None:figures.append(('measurement_frame',frame))
    for _,figure in WEB_STATE['figures']:plt.close(figure)
    WEB_STATE.update(run=run,derivation=derivation,figures=figures)
    result=web_result(run,derivation,figures)
    for _,figure in figures:plt.close(figure)
    return web_json(result)


def web_export():
    if WEB_STATE['run'] is None:raise ValueError('Calculate the current inputs before downloading results.')
    web_progress('Exporting raw data, full mathematics and PDF/SVG/600-dpi PNG figures…')
    validation=WEB_STATE["validation"] or dict(
        status="full suite not run",scope="Current-run checks are separate from the complete reference suite.",
        checks=matching_protocol_audit(WEB_STATE['run']))
    return make_general_archive(WEB_STATE['run'],WEB_STATE['figures'],WEB_STATE['derivation'],
        validation,WEB_STATE['comparisons'])


def web_download_figure(index, extension):
    if extension not in ['png','pdf','svg']:raise ValueError('Choose PNG, PDF or SVG.')
    if not isinstance(index,int) or not 0<=index<len(WEB_STATE['figures']):raise ValueError('Select a calculated figure.')
    name,figure=WEB_STATE['figures'][index]
    output=io.BytesIO();figure.savefig(output,format=extension,dpi=600,bbox_inches='tight',transparent=True)
    return output.getvalue()


def web_validate():
    web_progress('Checking tensor symmetry, complex amplitudes, reference equations and numerical limits…')
    first=run_self_checks()
    web_progress('Checking all point groups and general optical profiles…')
    second=validate_general_upgrade()+validate_optical_method_guide()
    web_progress('Running QWP source reference checking procedures and recording their purposes and residuals…')
    reference=validate_optical_reference()
    report=dict(status=reference["status"],version=AUDIT_VERSION,checks=first+second,
                optical_reference=reference)
    WEB_STATE["validation"]=report
    return web_json(report)


def web_add_comparison():
    if WEB_STATE['run'] is None:raise ValueError('Calculate a case first.')
    if len(WEB_STATE['comparisons'])>=6:raise ValueError('Six snapshots are already saved. Clear comparisons to start a new set.')
    WEB_STATE['comparisons'].append(copy.deepcopy(WEB_STATE['run']))
    return web_json([dict(label=run['config']['case_label'],optics=run['config']['optics'],channels=list(run['display_channels']))
                     for run in WEB_STATE['comparisons']])


def web_clear_comparisons():
    WEB_STATE['comparisons']=[]
    return '[]'


def web_compare(channel, normalized):
    figure=publication_comparison(WEB_STATE['comparisons'],channel,normalized)
    try:return web_json(web_figure_view('comparison',figure))
    finally:plt.close(figure)


def web_benchmark(magnitude, points):
    web_progress('Calculating and independently checking all 18 silicon reference cases…')
    study=calculate_cubic_fig1(magnitude,points)
    checks=validate_cubic_fig1(study)
    figure=publication_cubic_figure(study)
    try:view=web_figure_view('silicon_six_surfaces',figure)
    finally:plt.close(figure)
    WEB_STATE['benchmark']=study
    return web_json(dict(status='passed',checks=checks,figure=view,
        cases=[dict(protocol=protocol,k=k,config=web_form(run['config']))
               for protocol,runs in study['runs'].items() for k,run in enumerate(runs)]))


def web_export_benchmark():
    if WEB_STATE['benchmark'] is None:raise ValueError('Calculate the silicon benchmark first.')
    study=WEB_STATE['benchmark']
    return make_cubic_origin_archive(study,dict(status='passed',checks=validate_cubic_fig1(study)))
