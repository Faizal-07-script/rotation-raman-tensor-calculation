"""On-screen plots use the notebook's numerical results; reports are built on demand."""

# The notebook and full adapter remain the source of truth for scientific output.
_web_standard_calculate = web_calculate
_web_standard_export = web_export
_web_standard_figure = web_download_figure


def web_plot_payload(run):
    scales = channel_display_scales(run) if run['config'].get('normalize') else {}
    scan_basis = run['optical']['scan_basis']
    variable = sp.Symbol('theta', real=True) if scan_basis == 'SECOND' else alpha
    channels, equations = [], []
    for name, item in run['display_channels'].items():
        channels.append(dict(name=name, kind=item['kind'], component=item['component'],
            summary=item['summary'], points=item['curve'], optics=item['optical']['kind'],
            scale=scales.get(item['normalization_group'], 1)))
        equation = display_intensity(item['summary'], variable)
        equations.append(dict(channel=name, numerical='I(' + raman_latex(variable) +
            r')\approx ' + raman_latex(equation)))
    figures = []
    for item in channels:
        name = ''.join(ch if ch.isalnum() else '_' for ch in item['name']).strip('_')
        figures.append(dict(name='polar_' + name))
        if run['config'].get('cartesian_plots'):
            figures.append(dict(name='cartesian_' + name))
    return dict(preview=True, case=run['config']['case_label'],
        configuration=web_form(run['config']), channels=channels, figures=figures,
        angles=np.rad2deg(run['angles']), scan_label=run['scan_label'], scan_basis=scan_basis,
        analytical_intensity=equations, csv=csv_from_curves(
            run['angles'], run['display_curves'], 'theta_deg' if scan_basis == 'SECOND' else 'alpha_deg'))


def web_fast_ag_sum(run):
    # The same incoherent component sum as web_include_ag_sum in the full adapter.
    names = [f'Ag({axis})' for axis in WEB_AG_COMPONENTS]
    parts = [run['display_channels'][name] for name in names]
    records = [record for part in parts for record in part['records']]
    summed = evaluate_terms(dict(terms=records), parts[0]['values'], run['angles'])
    channel = dict(parts[0], name=WEB_AG_SUM, component=None,
        kind='Ag component intensity sum', records=records, curve=summed['total'],
        summary=summed['summary'], partner_curves=summed['components'])
    run['display_channels'][WEB_AG_SUM] = channel
    run['display_curves'][WEB_AG_SUM] = channel['curve']
    run['display_summaries'][WEB_AG_SUM] = channel['summary']


def web_quick_calculate(input_json):
    cfg = web_configuration(json.loads(input_json))
    web_progress('Calculating the rotated tensor and intensity…')
    run = calculate_general(cfg)
    for _, figure in WEB_STATE['figures']:
        plt.close(figure)
    # Keep the notebook run without the extra display-only Ag sum for its derivation.
    display = dict(run, **{key: dict(run[key]) for key in
                   ('display_channels', 'display_curves', 'display_summaries', 'presentation_policy')})
    if cfg.get('show_ag_sum'):
        web_fast_ag_sum(display)
    result = web_json(web_plot_payload(display))
    WEB_STATE.update(run=display, base_run=run, derivation=None, figures=[], detail_result=None)
    return result


def web_calculate(input_json):
    result = _web_standard_calculate(input_json)
    WEB_STATE.update(base_run=None, detail_result=None)
    return result


def web_prepare_details():
    if WEB_STATE['run'] is None:
        raise ValueError('Calculate the current inputs first.')
    if WEB_STATE['derivation'] is None:
        web_progress('Preparing the equations…')
        # Work on fresh maps so cancelling or retrying a failed report cannot
        # leave a partially augmented Ag sum in the symbolic notebook input.
        original = WEB_STATE['base_run']
        base = dict(original, **{key: dict(original[key]) for key in
                    ('display_channels', 'display_curves', 'display_summaries', 'presentation_policy')})
        derivation = detailed_calculation(base)
        web_include_ag_sum(base, derivation)
        web_progress('Checking the result…')
        base['checking_procedures'] = checking_procedures_for_run(base)
        WEB_STATE.update(run=base, derivation=derivation)


def web_calculation_details():
    web_prepare_details()
    if WEB_STATE.get('detail_result') is None:
        WEB_STATE['detail_result'] = web_json(web_result(WEB_STATE['run'], WEB_STATE['derivation'], []))
    return WEB_STATE['detail_result']


def web_prepare_figures():
    run = WEB_STATE['run']
    if run is None:
        raise ValueError('Calculate the current inputs first.')
    if not WEB_STATE['figures']:
        web_progress('Drawing the figures…')
        figures = publication_figures(run)
        if run['config'].get('show_geometry'):
            frame = publication_orientation(run)
            if frame is not None:
                figures.append(('measurement_frame', frame))
        WEB_STATE['figures'] = figures
        for _, figure in figures:
            plt.close(figure)


def web_export():
    web_prepare_details()
    web_prepare_figures()
    return _web_standard_export()


def web_download_figure(index, extension):
    web_prepare_figures()
    return _web_standard_figure(index, extension)


_web_notebook_amplitude = amplitude_record


@lru_cache(maxsize=128)
def web_cached_amplitude(tensor, frame, incident, analyzer, return_matrix, basis):
    return _web_notebook_amplitude(tensor, frame,
        dict(Ein=incident, analyzer=analyzer, B=return_matrix, scan_basis=basis))


def amplitude_record(crystal_tensor, frame, optical):
    """Reuse the symbolic rotation and projection when only coefficient values change."""
    record = web_cached_amplitude(*(sp.ImmutableMatrix(v) for v in
        (crystal_tensor, frame, optical['Ein'], optical['analyzer'], optical['B'])),
        optical.get('scan_basis', 'FIRST'))
    return copy.deepcopy(record)
