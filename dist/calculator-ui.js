'use strict';

// Both Pages entry points use the same controls, worker and scientific source.
const calculatorOnly = document.body.dataset.calculatorOnly === 'true';
const fullWebsiteUrl = document.body.dataset.fullSite || './index.html';
const calculatorWebsiteUrl = document.body.dataset.calculatorSite || './calculator.html';
const originalControls = renderControls;
const originalCalculator = renderCalculator;
const originalResultBody = resultBody;
const originalRoute = renderRoute;
const originalInvalidate = invalidate;
const originalNumberedControl = numberedControl;
const originalHome = renderHome;
S.derivationMode = 'explained';
S.preview = null;
S.previewDirty = false;


// Color identifies a defined scientific term; the text always supplies its meaning.
function technicalTerm(text, kind='tensor', definition='') {
  return '<span class="technical-term term-'+kind+'" title="'+esc(definition)+'">'+esc(text)+'</span>';
}
function coefficientHelp(name) {
  return '<p class="field-help">Each letter is a Raman tensor entry. Size and phase set its value.</p><details class="coefficient-help"><summary>What do the two inputs mean?</summary><p>'+technicalTerm('Coefficient size','size','The nonnegative modulus of a tensor entry')+' is the size of a tensor entry. '+technicalTerm('Coefficient phase','phase','The angle of a complex tensor entry, entered in degrees')+' gives its angle in the complex plane.</p>'+
    math(String.raw`d=|d|e^{i\phi_d}`)+'<p>Size 1 with phase 0° gives d = 1; 180° gives d = −1; 90° gives d = i. Use 1 and 0° for the simple real example. Other letters follow the same rule. These are relative tensor values, not a sample-rotation angle.</p><p>A common phase of a whole tensor does not change intensity. Phase differences between entries of the same tensor can change interference. At size zero, phase has no effect.</p></details>';
}
function complexValueText(symbol, size, phase) {
  if(!Number.isFinite(size)||!Number.isFinite(phase)||size<0)return 'Enter a zero or positive size and a finite phase.';
  const angle=phase*Math.PI/180;
  const clean=value=>Math.abs(value)<1e-12?0:Number(value.toPrecision(10));
  const real=clean(size*Math.cos(angle)),imag=clean(size*Math.sin(angle));
  const imaginary=value=>value===1?'i':value===-1?'−i':String(value)+'i';
  return symbol+' = '+(imag===0?String(real):real===0?imaginary(imag):String(real)+(imag<0?' − ':' + ')+imaginary(Math.abs(imag)));
}
function coefficientEntryHtml(name,symbol,value,locked) {
  const id='coefficient-'+name.replace(/[^a-z0-9]/gi,'_')+'-'+symbol;
  return '<div class="coefficient-entry"><div class="coefficient-row"><span class="coefficient-symbol">'+esc(symbol)+'</span><div class="field"><label class="term-size" for="'+id+'-size">2.5 Size |'+esc(symbol)+'|</label><input id="'+id+'-size" aria-label="'+esc(name+' '+symbol+' coefficient size')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="magnitude" type="number" min="0" step="any" value="'+esc(value.magnitude)+'" '+(locked?'disabled':'')+'></div><div class="field"><label class="term-phase" for="'+id+'-phase">2.5 Phase φ'+esc(symbol)+' (°)</label><input id="'+id+'-phase" aria-label="'+esc(name+' '+symbol+' coefficient phase in degrees')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="phase" type="number" step="any" value="'+esc(value.phase)+'" '+(locked?'disabled':'')+'></div></div><p class="coefficient-value" aria-live="polite" data-coefficient-value>Used in the tensor: <strong>'+esc(complexValueText(symbol,Number(value.magnitude),Number(value.phase)))+'</strong></p><p class="field-help">Size: relative tensor units. Phase: degrees; 0° gives a positive real entry when size is positive.</p></div>';
}
function calculationExplanation() {
  return '<details class="card common-calculation"><summary>How does the calculation work?</summary><ol><li><b>Set the axes.</b> The surface, in-plane X and lattice determine X, Y, Z and the matrix T. Y = Z × X.</li><li><b>Choose the tensor.</b> The material symmetry and Raman mode determine its allowed entries; you supply their values.</li><li><b>Transform the tensor.</b> '+math(String.raw`R_{\mathrm{lab}}=T^{\mathsf T}R_{\mathrm c}T`)+'</li><li><b>Set polarization.</b> The optical method supplies the incident and detection Jones states at the sample.</li><li><b>Calculate the amplitude, then intensity.</b> '+math(String.raw`\mathcal A=\mathbf e_s^\dagger R_\perp\mathbf E_i,\qquad I=|\mathcal A|^2`)+'</li></ol><p>Changing the surface rebuilds T. Changing the material or mode replaces the tensor. Changing the optical method replaces the polarization states. X/Y/Z describe geometry; Jones vectors describe polarization.</p><p>Within one tensor, add amplitudes before squaring. For unresolved orthogonal components of a degenerate mode, add their intensities.</p><div class="term-key"><span>Defined terms:</span>'+technicalTerm('Tensor components','tensor')+technicalTerm('Coefficient size','size')+technicalTerm('Coefficient phase','phase')+technicalTerm('Measurement axes','geometry')+'</div></details>';
}
function referenceEquationChecks() {
  const report=S.referenceChecks;
  if(!report)return '';
  return '<section class="card reference-equation-checks"><h3>New-san reference: analytical equation checks</h3><p>Build-time checks for Paukatong et al., '+esc(report.reference.doi)+'. These are algebra and numerical checks of the stated model, not an independent laboratory review.</p><span class="tag success">'+report.passed+' / '+report.total+' checks passed</span>'+table(['Equation or case','What was checked','Residual'],report.checks.map(row=>[esc(row.label),esc(row.detail),esc(String(row.residual))]))+'<p class="small-note">'+esc(report.scope)+'</p><a class="text-link" href="./downloads/Reference_Equation_Checks.md" download>Read the analytical comparison ↓</a> · <a class="text-link" href="./data/reference-equation-checks.json" download>Download evidence JSON ↓</a></section>';
}


renderHome = () => {
  const host=document.createElement('div');host.innerHTML=originalHome();
  host.querySelector('.hero .button-row')?.insertAdjacentHTML('beforeend','<a class="button secondary" href="'+esc(calculatorWebsiteUrl)+'">Calculator-only website ↗</a>');
  return host.innerHTML;
};

numberedControl = (id, label) => originalNumberedControl(id, label).replace(/^(\d+\.\d+)\s+/, '<span class="control-number">$1</span> ');
section = (number, title, content, open = false, full = false) =>
  '<details data-section-key="' + esc(number) + '" class="form-section setup-card ' + (full ? 'full-width' : '') + '" open><summary><span class="setup-number">' + esc(number) + '</span><span>' + title + '</span></summary><div class="form-section-body">' + content + '</div></details>';

function tuckAway(nodes, label, open = false) {
  const items = nodes.filter(Boolean);
  if (!items.length) return;
  const details = document.createElement('details');
  details.className = 'advanced-inputs';
  details.open = open;
  const summary = document.createElement('summary');
  summary.textContent = label;
  details.append(summary);
  items[0].before(details);
  items.forEach(node => details.append(node));
}

renderControls = () => {
  const host = document.createElement('div');
  host.innerHTML = originalControls();
  const first = host.querySelector('[data-section-key="01"] .form-section-body');
  if (first) {
    tuckAway([first.querySelector('#case-label')?.closest('.field'), first.querySelector('#input-note')?.closest('.field')], 'Label and notes');
    tuckAway([first.querySelector('.optical-choice-note')], 'About this optical method');
  }
  host.querySelectorAll('.mode-card .tensor-preview').forEach(node => tuckAway([node], 'View tensor matrices'));
  const orientation = host.querySelector('[data-section-key="03"] .form-section-body');
  if (orientation) {
    const lengths = orientation.querySelector('#lattice-0')?.closest('.field-row');
    if (lengths) {
      const nodes = [lengths.previousElementSibling, lengths, lengths.nextElementSibling, lengths.nextElementSibling?.nextElementSibling, orientation.lastElementChild];
      tuckAway([...new Set(nodes)], 'Crystal lattice and units', !['Oh', 'Td'].includes(S.form.point_group));
    }
    orientation.insertAdjacentHTML('afterbegin','<p class="field-help">These inputs define measurement axes, not polarization vectors. For silicon, (500) and (100) have the same normal direction.</p>');
    const automatic = orientation.querySelector('[for="automatic-x"]');
    if (automatic) automatic.insertAdjacentHTML('afterend', '<p class="field-help">The surface sets Z. Choose X within that surface, or let Automatic X choose a Cartesian reference. It does not read an axis from a paper. Y = Z × X is calculated automatically. Grey u/v/w fields are inactive while Automatic X is on.</p>');
  }
  const optical = host.querySelector('[data-section-key="04"] .form-section-body');
  const conditional = optical?.querySelector('.field-label');
  if (conditional) {
    const nodes = [];
    let current = conditional;
    while (current) { nodes.push(current); current = current.nextElementSibling; }
    tuckAway(nodes, 'Optional angular-momentum rule');
  }
  const displayCard = host.querySelector('[data-section-key="05"]');
  if (displayCard) displayCard.open = false;
  const action = host.querySelector('[data-calculate]');
  if (action) action.innerHTML = 'Run calculation <span aria-hidden="true">→</span>';
  return host.innerHTML;
};

function calculationToolbar() {
  return '<div class="calculator-toolbar" aria-label="Calculation actions"><div><strong>Set inputs. Review the axes. Calculate.</strong><small>Default example: Silicon (500), VV</small></div><div class="button-row">' +
    '<button class="button secondary" data-preview-inputs ' + (S.busy ? 'disabled' : '') + '>Review inputs</button>' +
    '<button class="button" data-calculate ' + (S.busy ? 'disabled' : '') + '><span aria-hidden="true">▶</span> Run calculation</button>' +
    '<button class="button secondary" data-reset-defaults ' + (S.busy ? 'disabled' : '') + '>Reset example</button>' +
    '<button class="button secondary" data-result-download="csv" ' + (!S.result || S.dirty || S.busy ? 'disabled' : '') + '>Export CSV</button></div></div>';
}

function calculationPipeline() {
  return calculationExplanation()+'<div class="calculation-pipeline" aria-label="Calculation stages">' +
    [['01', 'Model'], ['02', 'Tensor'], ['03', 'Measurement axes'], ['04', 'Polarization'], ['05', 'Sampling'], ['06', 'Intensity']].map(([number, label]) =>
      '<div><span>' + number + '</span><strong>' + label + '</strong></div>').join('') + '</div>';
}

function finalIntensityCard(result) {
  if (!result?.analytical_intensity?.length) return '';
  return '<section class="card final-intensity-card"><div class="card-header"><div><span class="kicker">FINAL ANALYTICAL INTENSITY</span><h3>Final intensity equation</h3></div><button class="text-button" data-show-math>See the calculation →</button></div>' +
    [...(result.complete_mode_intensity||[]),...result.analytical_intensity].map(row => '<div class="final-intensity-row"><div><strong>' + esc(row.channel) + '</strong><small>Relative intensity before plot normalization</small></div>' + math(row.numerical) + '<button class="text-button" data-copy-equation="' + esc(row.numerical) + '">Copy LaTeX</button></div>').join('') + '</section>';
}

function extremaCards(result) {
  if (!result?.channels?.length) return '';
  const channel = result.channels.find(c => c.name === S.focusChannel) || result.channels[0];
  const summary = channel.summary;
  return '<section class="extrema-summary"><div class="summary-label"><strong>Continuous extrema</strong><select id="summary-channel" aria-label="Channel for the intensity extrema">' + result.channels.map(c => '<option ' + (c.name === channel.name ? 'selected' : '') + ' value="' + esc(c.name) + '">' + esc(c.name) + '</option>').join('') + '</select></div><div class="extrema-grid">' +
    [['Maximum intensity', compact(summary.Imax)], ['Minimum intensity', compact(summary.Imin)], ['Maximum at', summary.alpha_max === null ? 'Every angle' : compact(summary.alpha_max) + '°'], ['Minimum at', summary.alpha_min === null ? 'Every angle' : compact(summary.alpha_min) + '°']].map(([label, value]) => '<div><span>' + label + '</span><strong>' + value + '</strong></div>').join('') + '</div></section>';
}

const curveColors = ['#7c2638', '#117f88', '#b27938', '#536f9a', '#74618a', '#39745a'];
function cartesianPlotSvg(result) {
  const series=result.channels.map(channel=>({name:channel.name, values:channel.points.map(value=>value/(channel.scale>0?channel.scale:1))}));
  const maximum=series.reduce((largest,channel)=>channel.values.reduce((m,value)=>Math.max(m,value),largest),0);
  const top=maximum>0?maximum*1.06:1;
  const x=value=>65+value/360*550, y=value=>330-value/top*300;
  let grid='';
  for(let i=0;i<=4;i++) {
    const angle=i*90, value=top*i/4;
    grid+='<path d="M'+x(angle)+' 30V330M65 '+y(value)+'H615" stroke="#e3eaf0" fill="none"/><text x="'+x(angle)+'" y="351" text-anchor="middle">'+angle+'°</text><text x="53" y="'+(y(value)+4)+'" text-anchor="end">'+esc(compact(value))+'</text>';
  }
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img" aria-label="Cartesian Raman intensity plot"><title>Raman intensity versus scan angle</title><desc>The same samples and normalization used by the polar plots.</desc><rect width="640" height="400" fill="white"/><g font-family="Arial,sans-serif" font-size="13" fill="#6c7f8c">'+grid+'<text x="340" y="385" text-anchor="middle">Scan angle '+(result.scan_basis==='SECOND'?'θ':'α')+' (degree)</text><text x="17" y="180" text-anchor="middle" transform="rotate(-90 17 180)">'+(result.configuration.normalize?'Normalized intensity':'Relative intensity (a.u.)')+'</text></g><path d="M65 30V330H615" fill="none" stroke="#9aabb6"/>'+series.map((channel,i)=>'<path aria-label="'+esc(channel.name)+'" d="'+channel.values.map((value,j)=>(j?'L':'M')+x(result.angles[j]).toFixed(3)+' '+y(value).toFixed(3)).join(' ')+'" fill="none" stroke="'+curveColors[i%curveColors.length]+'" stroke-width="2.5"/>').join('')+'</svg>';
}
function cartesianPlotCard(result) {
  if(!result?.channels?.length)return '';
  return '<figure class="result-figure cartesian-figure"><figcaption><strong>Cartesian plot</strong><div class="figure-actions"><button data-cartesian-svg '+(S.dirty?'disabled':'')+'>SVG ↓</button></div></figcaption>'+cartesianPlotSvg(result)+'<div class="curve-legend">'+result.channels.map((channel,i)=>'<span><i style="background:'+curveColors[i%curveColors.length]+'"></i>'+esc(channel.name)+'</span>').join('')+'</div><p class="small-note">Same samples and normalization as the polar plots.</p></figure>';
}

function localDefinitions(symbols, seen) {
  return (symbols || []).filter(symbol => {
    const key = JSON.stringify([symbol.id, symbol.latex, symbol.meaning, symbol.units]);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).map(symbol => '<div class="worked-definition"><span class="technical-term term-'+(symbol.id.includes('phase')?'phase':symbol.id==='coefficient_magnitude'?'size':['frame','frame_axes'].includes(symbol.id)?'geometry':'tensor')+'" data-inline data-tex="' + esc(symbol.latex) + '"></span><p>' + esc(symbol.meaning) + '<small>' + esc(symbol.units) + '</small></p></div>').join('');
}

derivationHtml = (entries, explained = true) => {
  const groups = [];
  const seen = new Set();
  for (const entry of entries) {
    if (entry.kind === 'section') groups.push({ title: entry.value, step: entry.step || String(groups.length + 1).padStart(2, '0'), entries: [] });
    else { if (!groups.length) groups.push({ title: 'Calculation', step: '01', entries: [] }); groups.at(-1).entries.push(entry); }
  }
  return '<div class="worked-navigation">'+(groups.some(group=>group.title.startsWith('Final intensity'))?'<button class="button secondary small" data-open-final>Jump to final intensity</button>':'')+'<button class="text-button" data-expand-math>Expand all steps</button><button class="text-button" data-collapse-math>Collapse all steps</button></div>' +
    '<div class="worked-columns-label"><span>Explanation and symbol definitions</span><span>Complete mathematical calculation</span></div>' +
    groups.map(group => '<details class="result-math-section worked-section ' + (group.title.startsWith('Final intensity') ? 'is-final' : '') + '" id="worked-step-' + esc(group.step) + '" open><summary><span class="step-badge">' + esc(group.step) + '</span>' + esc(group.title) + '</summary><div class="result-math-body">' +
      group.entries.map(entry => entry.kind === 'equation' ? '<article class="worked-row ' + (explained ? '' : 'mathematics-only') + '">' +
        (explained ? '<div class="worked-explanation"><span class="operation-number">STEP ' + esc(entry.step || '') + '</span><p>' + esc(entry.explanation || 'Evaluate the displayed expression using the selected inputs.') + '</p>' + localDefinitions(entry.symbols, seen) +
          '<details class="worked-source"><summary>Source and conventions</summary><p>' + esc(entry.derivation_note || '') + '</p>' + sourceLinks(entry.reference_ids) + '</details></div>' : '') +
        '<div class="worked-mathematics">' + math(entry.value) + '<button class="text-button copy-step" data-copy-equation="' + esc(entry.value) + '">Copy LaTeX</button></div></article>' : '<p class="worked-note">' + rich(entry.value) + '</p>').join('') + '</div></details>').join('') +
    (explained || !S.result ? '' : derivationLegendHtml(S.result));
};

derivationModeHtml = () => '<div class="derivation-view-picker"><div class="button-row" role="group" aria-label="Derivation view">' +
  [['explained', 'Explanation + mathematics'], ['mathematics', 'Mathematics only']].map(([key, label]) => '<button class="button ' + (S.derivationMode === key ? '' : 'secondary ') + 'small" data-derivation-mode="' + key + '" aria-pressed="' + (S.derivationMode === key) + '">' + label + '</button>').join('') + '</div><p class="small-note">Read each numbered operation from left to right. The original tensor coefficients are kept in the equations.</p></div>';

function renderInputReview() {
  const preview = S.preview || (!S.dirty ? S.result?.input_review : null);
  if (!preview || S.previewDirty) return '<div class="card input-review-empty"><span class="kicker">BEFORE CALCULATING</span><h3>Review your measurement frame</h3><p>Check the surface normal, the in-plane axes, the rotated tensors and the actual Jones states.</p><button class="button secondary" data-preview-inputs ' + (S.busy ? 'disabled' : '') + '>Review current inputs</button></div>';
  return '<section class="card"><div class="card-header"><div><span class="kicker">INPUT REVIEW</span><h3>Measurement axes and optical states</h3></div><span class="tag success">Geometry checked</span></div><p>Check these axes, tensors and polarization states before running the intensity calculation.</p>' +
    (preview.axes?.length ? '<div class="axes-preview">' + preview.axes.map(axis => '<div><strong>' + esc(axis.label) + '</strong>' + math(axis.latex) + '</div>').join('') + '</div><p class="small-note">Measurement unit axes expressed in crystal Cartesian coordinates. These are not Jones vectors. Y = Z × X. T has these axes as columns; TᵀT = I and det(T) = +1.</p>' : '<p>This effective 2D source has no crystal-orientation input.</p>') + '</section>' + derivationHtml(preview.equations, true);
}

resultBody = () => {
  if (S.tab === 'inputs') return renderInputReview();
  if (S.tab === 'validation') return referenceEquationChecks()+originalResultBody();
  if (S.tab === 'benchmark') return referenceEquationChecks()+originalResultBody();
  if (S.tab === 'math' && S.result) return finalIntensityCard(S.result) + derivationModeHtml() + derivationHtml(S.result.equations, S.derivationMode === 'explained');
  if (S.tab === 'plots' && S.result) return extremaCards(S.result) + finalIntensityCard(S.result) + '<div class="visualization-grid">'+cartesianPlotCard(S.result)+'<div class="polar-figures">'+originalResultBody()+'</div></div>';
  return originalResultBody();
};

renderCalculator = sectionName => {
  if (!S.dirty && S.result?.input_review) { S.preview=S.result.input_review;S.previewDirty=false; }
  const host = document.createElement('div');
  host.innerHTML = originalCalculator(sectionName);
  const headingNode = host.querySelector('.page-title-row');
  if (headingNode) {
    headingNode.querySelector('.page-lead').textContent = 'Choose the crystal, surface and polarization. Review the axes, then run the calculation.';
    headingNode.insertAdjacentHTML('beforeend', '<a class="text-link calculator-page-link" href="' + esc(calculatorOnly ? fullWebsiteUrl : calculatorWebsiteUrl) + '">' + (calculatorOnly ? 'Full website ↗' : 'Calculator-only website ↗') + '</a>');
  }
  const quickstart = host.querySelector('#calculator-quickstart');
  if (quickstart) quickstart.remove();
  const layout = host.querySelector('.calc-layout');
  layout.insertAdjacentHTML('beforebegin', calculationToolbar());
  const results = host.querySelector('.calc-results');
  results.insertAdjacentHTML('afterbegin', calculationPipeline());
  const tabs = host.querySelector('.result-tabs');
  const inputTab = document.createElement('button');
  inputTab.className = 'result-tab'; inputTab.dataset.resultTab = 'inputs'; inputTab.textContent = 'Input review';
  inputTab.setAttribute('role', 'tab'); inputTab.setAttribute('aria-selected', String(S.tab === 'inputs')); inputTab.tabIndex = S.tab === 'inputs' ? 0 : -1;
  tabs.children[1].before(inputTab);
  tabs.querySelector('[data-result-tab="math"]').textContent = 'Step-by-step calculation';
  const advanced = document.createElement('details'); advanced.className = 'advanced-results';
  advanced.innerHTML = '<summary>Checks, comparisons and benchmark</summary><div class="result-tabs" role="tablist" aria-label="Additional calculation outputs"></div>';
  const extraTabs = advanced.querySelector('.result-tabs');
  for (const tab of [...tabs.children]) {
    if (!['plots', 'inputs', 'math', 'values', 'frame'].includes(tab.dataset.resultTab)) extraTabs.append(tab);
  }
  advanced.open = [...extraTabs.children].some(tab => tab.dataset.resultTab === S.tab);
  tabs.after(advanced);
  return host.innerHTML;
};

invalidate = () => { originalInvalidate(); S.previewDirty = true; };
renderRoute = (scroll = true) => {
  if (calculatorOnly && !location.hash.startsWith('#calculator')) {
    if (location.hash && location.hash !== '#home') { location.href = fullWebsiteUrl + location.hash; return; }
    history.replaceState(null, '', '#calculator');
  }
  originalRoute(scroll);
};

document.addEventListener('click', async event => {
  const button = event.target.closest('button'); if (!button) return;
  if (button.hasAttribute('data-preview-inputs')) {
    try { S.form = readForm(); } catch (error) { toast(error.message); return; }
    await runOperation('preflight', S.form, 'Reviewing axes and optical states', result => { S.preview = result; S.previewDirty = false; S.tab = 'inputs'; });
  } else if (button.hasAttribute('data-reset-defaults')) {
    S.form = clone(S.catalog.examples[S.catalog.default_example].config); S.selectedExample = S.catalog.default_example; S.relation = 'free'; S.preview = null; invalidate(); renderRoute(false); toast('Silicon (500), VV inputs restored. Review or calculate to update the result.');
  } else if (button.hasAttribute('data-show-math')) {
    S.tab = 'math'; renderRoute(false); $('#result-pane')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (button.hasAttribute('data-open-final')) {
    const section = $('.worked-section.is-final'); if (section) { section.open = true; section.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  } else if (button.hasAttribute('data-cartesian-svg') && S.result && !S.dirty) download(cartesianPlotSvg(S.result),'Raman_Intensity_Cartesian.svg','image/svg+xml');
  else if (button.hasAttribute('data-copy-equation')) await copyText(button.dataset.copyEquation);
});
document.addEventListener('change', event => { if (event.target.id === 'summary-channel') { S.focusChannel = event.target.value; renderRoute(false); } });
if (calculatorOnly) {
  document.body.classList.add('calculator-only');
  $('.brand').href = fullWebsiteUrl;
  $('.brand').setAttribute('aria-label', 'Open the full Raman Tensor Lab website');
  $('.header-calculator').href = fullWebsiteUrl; $('.header-calculator').textContent = 'Full website ↗';
}
if (S.catalog) renderRoute(false);

document.addEventListener('input', event=>{
  const input=event.target.closest('[data-coefficient]');
  if(!input)return;
  const row=input.closest('.coefficient-entry');
  const size=Number(row.querySelector('[data-part="magnitude"]').value);
  const phase=Number(row.querySelector('[data-part="phase"]').value);
  row.querySelector('[data-coefficient-value]').textContent='Used in the tensor: '+complexValueText(input.dataset.coefficient,size,phase);
});


// The three named laboratory models share this interface in both Pages sites.
function labFramework(form=S.form) {
  return form.framework || (form.tensor_model==='QWP_SOURCE_2D'?'DR_KUMAR':
    ['Si','GaAs'].includes(form.material)&&form.optics.startsWith('CUBIC_')?'NEW_SAN':'USER_PPT');
}
const labReadForm=readForm;
readForm=()=>{const result=labReadForm();result.framework=labFramework(S.form);return result;};
const labRenderControls=renderControls;
renderControls=()=>{
  const host=document.createElement('div');host.innerHTML=labRenderControls();
  const key=labFramework();
  const model=host.querySelector('#tensor-model')?.closest('.field');
  if(model)model.outerHTML=selectField('framework','Calculation model',
    Object.entries(S.catalog.frameworks).map(([k,v])=>[k,v.label]),key);
  const optics=host.querySelector('#optical-method');
  if(optics){
    optics.innerHTML=optionList(S.catalog.frameworks[key].profiles.map(k=>[k,S.catalog.profiles[k]]),S.form.optics);
    optics.disabled=S.catalog.frameworks[key].profiles.length===1;
    const help=optics.closest('.field')?.querySelector('.field-help');
    if(help)help.textContent=key==='NEW_SAN'?'VV and VH scan θ. σ⁺α scans α, following paper equation (11).':'Use the polarization sequence of this model.';
  }
  const material=host.querySelector('#material');
  if(material){
    for(const option of [...material.options]){
      if(key==='NEW_SAN'&&!['Si','GaAs'].includes(option.value))option.remove();
      else if(key==='USER_PPT'&&option.value==='GaAs')option.remove();
    }
  }
  const examples=host.querySelector('#example');
  if(examples){
    const wanted={USER_PPT:'SLIDE',NEW_SAN:'SI_500',DR_KUMAR:'QWP_2D'}[key];
    for(const option of [...examples.options])if(option.value!==wanted)option.remove();
    examples.value=wanted;
  }
  if(key==='NEW_SAN'){
    for(const id of ['orientation-kind','automatic-x','normal-side','frame-angle']){
      const element=host.querySelector('#'+id);if(element)element.closest('.field,.checkbox-row')?.remove();
    }
    for(const input of host.querySelectorAll('#index-u,#index-v,#index-w,[id^="matrix-"],[id^="lattice-"],#theta-zero')){
      input.closest('.field')?.remove();
    }
    const orient=host.querySelector('[data-section-key="03"] .form-section-body');
    if(orient){
      // Only h,k,l are inputs in the paper model. X,Y,Z are outputs of SI (S1).
      for(const child of [...orient.children]){
        if(child.matches('p,.advanced-inputs,hr,.field-label'))child.remove();
      }
      orient.insertAdjacentHTML('afterbegin','<p class="field-help">Paper convention: Z is the positive surface normal, X ∥ [k −h 0], and Y = Z × X. Review inputs shows all three axes. For (001), use the original axes.</p>');
    }
    for(const input of host.querySelectorAll('[data-part="phase"]')){input.value=0;input.disabled=true;input.closest('.field')?.classList.add('paper-hidden-input');}
    host.querySelectorAll('.coefficient-help').forEach(n=>n.remove());
    host.querySelectorAll('.coefficient-entry .field-help').forEach(n=>n.textContent='d: common real Raman tensor element. Use 1 for the relative-intensity example.');
  }
  const first=host.querySelector('[data-section-key="01"] summary');
  if(first)first.innerHTML='<span class="setup-number">01</span><span>Calculation model and polarization</span>';
  return host.innerHTML;
};
document.addEventListener('change',event=>{
  if(event.target.id==='framework'){
    S.form=clone(S.catalog.frameworks[event.target.value].config);
    S.selectedExample={USER_PPT:'SLIDE',NEW_SAN:'SI_500',DR_KUMAR:'QWP_2D'}[event.target.value];
    S.preview=null;invalidate();replaceControls();event.stopImmediatePropagation();
  }
},true);
const labMaterialChange=materialChange;
materialChange=key=>{const framework=labFramework();labMaterialChange(key);S.form.framework=framework;replaceControls();};
const labDerivationHtml=derivationHtml;
derivationHtml=(entries,explained=true)=>{
  const host=document.createElement('div');host.innerHTML=labDerivationHtml(entries,explained);
  const rows=[...host.querySelectorAll('.worked-row')];
  entries.filter(e=>e.kind==='equation').forEach((entry,i)=>{
    if(entry.analytical_kind){rows[i]?.classList.add('analytical-expression');rows[i]?.setAttribute('data-analytical',entry.analytical_kind);}
    const note=rows[i]?.querySelector('.worked-source');
    if(note)note.outerHTML=entry.source_equation?'<small class="paper-equation-ref">'+esc(entry.source_equation)+'</small>':'';
  });
  return '<p class="analytical-color-key">Red: analytical expressions for the Raman tensor and Raman intensity.</p>'+host.innerHTML;
};
derivationModeHtml=()=>'<div class="derivation-view-picker"><div class="button-row">'+
  [['explained','Steps and short definitions'],['mathematics','Mathematics only']].map(([key,label])=>
    '<button class="button '+(S.derivationMode===key?'':'secondary ')+'small" data-derivation-mode="'+key+'">'+label+'</button>').join('')+
  '</div><p class="small-note">Follow the numbered stages. Equation labels refer to the paper or supplementary information.</p></div>';
calculationExplanation=()=>'<details class="card common-calculation"><summary>Calculation sequence</summary><p>Tensor → measurement axes → transformed tensor → polarization states → amplitude → intensity → polar plot.</p></details>';
calculationPipeline=()=>'<div class="calculation-pipeline" aria-label="Calculation stages">'+
  ['Tensor','Measurement axes','Transformed tensor','Polarization','Intensity','Polar plot'].map((title,i)=>'<div><span>0'+(i+1)+'</span><strong>'+title+'</strong></div>').join('')+'</div>';
const labIntensityCard=finalIntensityCard;
finalIntensityCard=result=>{const h=document.createElement('div');h.innerHTML=labIntensityCard(result);h.querySelector('.final-intensity-card')?.classList.add('analytical-expression');return h.innerHTML;};

RAMAN_DOCS.tools['tensor-model']={
  title:'Calculation model',lead:'Choose one of the three laboratory models.',
  sections:[
    {title:'1. My PPT slide model',paragraphs:['Use the slide geometry and polarization convention. Ag Cartesian contributions are shown separately.']},
    {title:'2. New-san — Paukatong et al.',paragraphs:['Si T₂g and GaAs TO/LO, with VV, VH and σ⁺α. The calculation follows the paper and supplementary information. The surface fixes the paper axes; the intensity is calculated from the transformed tensors and Jones vectors.'],sources:['cubic']},
    {title:'3. Dr. Kumar model',paragraphs:['Use the supplied original 2×2 tensor and input-QWP, Raman-tensor, return-QWP, analyzer sequence.'],sources:['optical-source']}
  ]};
RAMAN_DOCS.tools['optical-method']={title:'Polarization',lead:'The available polarization choices belong to the selected model.',
 sections:[{title:'New-san: VV, VH, σ⁺α',paragraphs:['VV: parallel linear states, scan θ. VH: crossed linear states, scan θ. σ⁺α: θ=π/4 and β=β′=π/2, scan α.'],sources:['cubic']},
 {title:'PPT and Dr. Kumar',paragraphs:['The PPT model retains the slide polarization states. Dr. Kumar retains the QWP matrices and analyzer convention of the supplied notebook.']}]};
for(const key of Object.keys(RAMAN_DOCS.tools))if(/circular|conditional|interference|selection-rules|optical-comparison/.test(key))delete RAMAN_DOCS.tools[key];
RAMAN_DOCS.tools.examples={title:'Examples',lead:'Each model opens with its own example.',sections:[
 {title:'My PPT slide model',paragraphs:['The (211) slide frame and separate Ag Cartesian contributions.']},
 {title:'New-san',paragraphs:['Si (500), T₂g, d=1, VV. Change to VH or σ⁺α to reproduce the other configurations. GaAs provides the TO and LO modes.'],sources:['cubic']},
 {title:'Dr. Kumar',paragraphs:['The original 2×2 source tensor, with a=1, A=0.4 and δ=φ=60°.'],sources:['optical-source']}]};
RAMAN_DOCS.tools['jones-controls']={title:'Polarization states',lead:'Use the states of the selected model.',sections:[
 {title:'New-san equation (11)',paragraphs:['θ is the linear-polarization angle; α is the detection-state scan angle. β and β′ are relative Jones-state phases. VV: α=0 and β=β′=0. VH: α=π/2 and β=β′=0. σ⁺α: θ=π/4 and β=β′=π/2.'],sources:['cubic']},
 {title:'Dr. Kumar',paragraphs:['The input and return quarter-wave plates and analyzer follow the supplied notebook.'],sources:['optical-source']}]};
RAMAN_DOCS.physics={
 'paper-order':{title:'New-san calculation sequence',lead:'The tensor and intensity equations used in the calculator.',sections:[
 {title:'Original tensors and measurement frame',paragraphs:['Paper (1)–(4), SI (S1)–(S2): define Rˣ, Rʸ, Rᶻ and X, Y, Z.']},
 {title:'Analytical Raman tensor',paragraphs:['Paper (5): Rⁱ′=TᵀRⁱT. For GaAs, apply the phonon projection in paper (8).']},
 {title:'Jones states and Raman intensity',paragraphs:['Use paper (11), then (9) for Si or (10) for GaAs. Expand the squared moduli using the original tensor coefficient d; insert its selected value to generate the plot.'],sources:['cubic']}
 ]}};
renderHome=()=>heading('RAMAN TENSOR LAB · VERSION 5','Rotation Raman Tensor Calculation','Three calculation models used in the laboratory.')+
 '<div class="button-row"><a class="button" href="#calculator">Open calculator →</a><a class="button secondary" href="'+esc(calculatorWebsiteUrl)+'">Calculator-only website ↗</a><a class="text-link" href="#tutorial">Python tutorial</a></div>'+
 '<div class="cards-grid">'+Object.values(S.catalog.frameworks).map(model=>'<section class="card"><h2>'+esc(model.label)+'</h2><p>'+esc(model.config.input_note||model.config.case_label)+'</p></section>').join('')+'</div>'+
 '<section class="card"><h2>Calculation steps</h2><p>Tensor → measurement axes → transformed tensor → polarization → intensity → polar plot.</p><p>Analytical tensor and intensity expressions are marked red in the results.</p></section>';
const sidebarNote=document.querySelector('.sidebar-footer small');if(sidebarNote)sidebarNote.textContent='My PPT slides · New-san · Dr. Kumar';
renderOpticalGuide=()=>'<section class="card optical-guide"><h2>Three laboratory models</h2><p>My PPT slides use the slide frame and polarization convention. New-san uses VV, VH or σ⁺α from paper (11). Dr. Kumar uses the original QWP sequence.</p><p>Choose the model first. The calculator then shows its available polarization choices.</p>'+sourceLinks(['cubic','optical-source'])+'</section>';
const labRenderCalculator=renderCalculator;
renderCalculator=sectionName=>{
  const host=document.createElement('div');host.innerHTML=labRenderCalculator(sectionName);
  if(labFramework()==='DR_KUMAR'){
    const lead=host.querySelector('.page-lead');if(lead)lead.textContent='Set the source tensor coefficients and phases, then calculate.';
    const stages=host.querySelector('.calculation-pipeline');
    if(stages)stages.innerHTML=['Source tensor','Input QWP','Raman field','Return QWP','Analyzer','Intensity'].map((label,i)=>'<div><span>0'+(i+1)+'</span><strong>'+label+'</strong></div>').join('');
  }
  return host.innerHTML;
};
