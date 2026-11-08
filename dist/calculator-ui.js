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
function coefficientHelp() {
  return '<details class="coefficient-help"><summary>Modulus and phase</summary>'+
    math(String.raw`d=|d|e^{i\phi_d}`)+'<p>Enter |d| in relative tensor units and φ<sub>d</sub> in degrees. For |d| = 1, the phases 0°, 180°, and 90° give d = 1, −1, and i, respectively. The same rule applies to the other tensor coefficients.</p></details>';
}
function complexValueText(symbol, size, phase) {
  if(!Number.isFinite(size)||!Number.isFinite(phase)||size<0)return 'Enter a nonnegative modulus and a finite phase.';
  const angle=phase*Math.PI/180;
  const clean=value=>Math.abs(value)<1e-12?0:Number(value.toPrecision(10));
  const real=clean(size*Math.cos(angle)),imag=clean(size*Math.sin(angle));
  const imaginary=value=>value===1?'i':value===-1?'−i':String(value)+'i';
  return symbol+' = '+(imag===0?String(real):real===0?imaginary(imag):String(real)+(imag<0?' − ':' + ')+imaginary(Math.abs(imag)));
}
function coefficientEntryHtml(name,symbol,value,locked) {
  const id='coefficient-'+name.replace(/[^a-z0-9]/gi,'_')+'-'+symbol;
  return '<div class="coefficient-entry"><div class="coefficient-row"><span class="coefficient-symbol">'+esc(symbol)+'</span><div class="field"><label class="term-size" for="'+id+'-size">2.5 |'+esc(symbol)+'|</label><input id="'+id+'-size" aria-label="'+esc(name+' |'+symbol+'|')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="magnitude" type="number" min="0" step="any" value="'+esc(value.magnitude)+'" '+(locked?'disabled':'')+'></div><div class="field"><label class="term-phase" for="'+id+'-phase">2.5 φ<sub>'+esc(symbol)+'</sub> (°)</label><input id="'+id+'-phase" aria-label="'+esc(name+' '+symbol+' coefficient phase in degrees')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="phase" type="number" step="any" value="'+esc(value.phase)+'" '+(locked?'disabled':'')+'></div></div><p class="coefficient-value" aria-live="polite" data-coefficient-value><strong>'+esc(complexValueText(symbol,Number(value.magnitude),Number(value.phase)))+'</strong></p></div>';
}
function calculationExplanation() {
  return '<details class="card common-calculation"><summary>How does the calculation work?</summary><ol><li><b>Set the axes.</b> The surface, in-plane X and lattice determine X, Y, Z and the matrix T. Y = Z × X.</li><li><b>Choose the tensor.</b> The material symmetry and Raman mode determine its allowed entries; you supply their values.</li><li><b>Transform the tensor.</b> '+math(String.raw`R_{\mathrm{lab}}=T^{\mathsf T}R_{\mathrm c}T`)+'</li><li><b>Set polarization.</b> The optical method supplies the incident and detection Jones states at the sample.</li><li><b>Calculate the amplitude, then intensity.</b> '+math(String.raw`\mathcal A=\mathbf e_s^\dagger R_\perp\mathbf E_i,\qquad I=|\mathcal A|^2`)+'</li></ol><p>Changing the surface rebuilds T. Changing the material or mode replaces the tensor. Changing the optical method replaces the polarization states. X/Y/Z describe geometry; Jones vectors describe polarization.</p><p>Within one tensor, add amplitudes before squaring. For unresolved orthogonal components of a degenerate mode, add their intensities.</p><div class="term-key"><span>Defined terms:</span>'+technicalTerm('Tensor components','tensor')+technicalTerm('Coefficient size','size')+technicalTerm('Coefficient phase','phase')+technicalTerm('Measurement axes','geometry')+'</div></details>';
}
function referenceEquationChecks() {
  const report=S.referenceChecks;
  if(!report)return '';
  return '<section class="card reference-equation-checks"><h3>Reference equation checks</h3><p>Build-time checks for Paukatong et al., '+esc(report.reference.doi)+'. These are algebra and numerical checks of the stated model, not an independent laboratory review.</p><span class="tag success">'+report.passed+' / '+report.total+' checks passed</span>'+table(['Equation or case','What was checked','Residual'],report.checks.map(row=>[esc(row.label),esc(row.detail),esc(String(row.residual))]))+'<p class="small-note">'+esc(report.scope)+'</p><a class="text-link" href="./downloads/Reference_Equation_Checks.md" download>Read the analytical comparison ↓</a> · <a class="text-link" href="./data/reference-equation-checks.json" download>Download evidence JSON ↓</a></section>';
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
  host.querySelectorAll('.mode-card .tensor-preview').forEach(node => tuckAway([node], 'View tensor matrices'));
  const orientation = host.querySelector('[data-section-key="03"] .form-section-body');
  if (orientation) {
    const lengths = orientation.querySelector('#lattice-0')?.closest('.field-row');
    if (lengths) {
      const nodes = [lengths.previousElementSibling, lengths, lengths.nextElementSibling, lengths.nextElementSibling?.nextElementSibling, orientation.lastElementChild];
      tuckAway([...new Set(nodes)], 'Crystal lattice and units', !['Oh', 'Td'].includes(S.form.point_group));
    }
    orientation.insertAdjacentHTML('afterbegin','<p class="field-help">For Si, (500) and (100) have the same surface normal.</p>');
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
  return '<div class="calculator-toolbar" aria-label="Calculation actions"><div><strong>Review the inputs, then calculate.</strong><small>Default: Si (500), VV</small></div><div class="button-row">' +
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
  return '<section class="extrema-summary"><div class="summary-label"><strong>Maximum and minimum intensity</strong><select id="summary-channel" aria-label="Raman mode or tensor component">' + result.channels.map(c => '<option ' + (c.name === channel.name ? 'selected' : '') + ' value="' + esc(c.name) + '">' + esc(c.name) + '</option>').join('') + '</select></div><div class="extrema-grid">' +
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
  advanced.innerHTML = '<summary>Checks and comparisons</summary><div class="result-tabs" role="tablist" aria-label="Additional calculation outputs"></div>';
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
  $('.brand').setAttribute('aria-label', 'Open the full Rotation Raman Tensor Calculation website');
  $('.header-calculator').href = fullWebsiteUrl; $('.header-calculator').textContent = 'Full website ↗';
}
if (S.catalog) renderRoute(false);

document.addEventListener('input', event=>{
  const input=event.target.closest('[data-coefficient]');
  if(!input)return;
  const row=input.closest('.coefficient-entry');
  const size=Number(row.querySelector('[data-part="magnitude"]').value);
  const phase=Number(row.querySelector('[data-part="phase"]').value);
  row.querySelector('[data-coefficient-value]').textContent=complexValueText(input.dataset.coefficient,size,phase);
});



// A model selects the calculation presentation; crystal and optical inputs stay independent.
const labReadForm=readForm;
readForm=()=>{const f=labReadForm();f.tensor_model='CRYSTAL_3D';f.case_label=resultLabel(f);f.input_note='';return f;};
const labRenderControls=renderControls;
renderControls=()=>{
  const host=document.createElement('div');host.innerHTML=labRenderControls();
  const material=host.querySelector('#material');
  if(material){
    const order=['Si','GaAs',...Object.keys(S.catalog.materials).filter(k=>!['Si','GaAs'].includes(k))];
    const options=keys=>optionList(keys.map(key=>[key,S.catalog.materials[key].label]),S.form.material);
    material.innerHTML='<optgroup label="Cubic crystals">'+options(order.slice(0,2))+'</optgroup><optgroup label="Other materials and custom tensors">'+options(order.slice(2))+'</optgroup>';
  }
  const orientation=host.querySelector('[data-section-key="03"] .form-section-body');
  if(orientation)orientation.insertAdjacentHTML('beforeend','<p class="field-help">X, Y, Z and T update in the measurement-frame panel before intensity is calculated.</p>');
  return host.innerHTML;
};
document.addEventListener('change',event=>{
  if(event.target.id!=='framework')return;
  try{S.form=readForm();
    S.preview=null;invalidate();replaceControls();renderLiveFrame();}
  catch(error){toast(error.message);}
  event.stopImmediatePropagation();
},true);

// Numeric frame preview only. The Python preflight independently checks this frame,
// rotated tensors and Jones states before any intensity scan.
function measurementFrame(form){
  const dot=(a,b)=>a.reduce((sum,x,i)=>sum+x*b[i],0);
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const scale=(a,k)=>a.map(x=>x*k),plus=(a,b)=>a.map((x,i)=>x+b[i]);
  const unit=a=>{const n=Math.hypot(...a);if(!Number.isFinite(n)||n<1e-13)throw Error('A frame axis cannot be zero.');return scale(a,1/n);};
  let T;
  if(form.orientation==='matrix'){
    T=form.T_manual;
    if(!Array.isArray(T)||T.length!==3||T.some(r=>!Array.isArray(r)||r.length!==3||r.some(x=>!Number.isFinite(x))))throw Error('Enter a real 3 × 3 frame matrix.');
  }else{
    const [a,b,c,ad,bd,gd]=form.lattice;
    if(![a,b,c,ad,bd,gd].every(Number.isFinite)||Math.min(a,b,c)<=0||[ad,bd,gd].some(x=>x<=0||x>=180))throw Error('Check the lattice lengths and angles.');
    const rad=Math.PI/180,ca=Math.cos(ad*rad),cb=Math.cos(bd*rad),cg=Math.cos(gd*rad),sg=Math.sin(gd*rad);
    const cy=(ca-cb*cg)/sg,cz2=1-cb*cb-cy*cy;
    if(cz2<=1e-14)throw Error('The lattice angles give a zero or invalid cell volume.');
    const L=[[a,b*cg,c*cb],[0,b*sg,c*cy],[0,0,c*Math.sqrt(cz2)]];
    const [h,k,l]=form.hkl;
    const gx=h/a,gy=(k-L[0][1]*gx)/L[1][1],gz=(l-L[0][2]*gx-L[1][2]*gy)/L[2][2];
    const Z=scale(unit([gx,gy,gz]),form.normal_sign);
    const uvw=form.uvw;
    if(!Array.isArray(uvw)||uvw.length!==3||!uvw.every(Number.isInteger)||uvw.every(value=>value===0))throw Error('Enter a nonzero integer direction [uvw].');
    if(Math.abs(dot(form.hkl,uvw))>1e-10)throw Error('The in-plane direction must satisfy hu + kv + ℓw = 0.');
    const tangent=L.map(row=>dot(row,uvw));
    const X0=unit(tangent),Y0=cross(Z,X0),angle=(form.azimuth_deg||0)*rad;
    const X=plus(scale(X0,Math.cos(angle)),scale(Y0,Math.sin(angle)));
    const Y=plus(scale(X0,-Math.sin(angle)),scale(Y0,Math.cos(angle)));
    T=[0,1,2].map(i=>[X[i],Y[i],Z[i]]);
  }
  const axes=[0,1,2].map(j=>T.map(row=>row[j]));
  const error=Math.max(...axes.flatMap((a,i)=>axes.map((b,j)=>Math.abs(dot(a,b)-(i===j?1:0)))));
  const determinant=dot(axes[0],cross(axes[1],axes[2]));
  if(error>1e-9||Math.abs(determinant-1)>1e-9)throw Error('T must have orthonormal columns and determinant +1.');
  return {T,axes,error,determinant};
}
function liveFrameContents(form){
  try{
    const frame=measurementFrame(form),fmt=x=>Math.abs(x)<5e-11?'0':Number(x.toPrecision(5)).toString();
    const matrix=rows=>String.raw`\begin{pmatrix}`+rows.map(row=>row.map(fmt).join('&')).join(String.raw`\\`)+String.raw`\end{pmatrix}`;
    return '<div class="card-header"><div><h3>X, Y, Z and T</h3></div><span class="tag success">Frame checked</span></div>'+
      '<div class="live-frame-grid"><div class="live-axis-list">'+frame.axes.map((axis,i)=>'<div>'+math('XYZ'[i]+'='+matrix(axis.map(value=>[value])))+'</div>').join('')+'</div><div>'+math(String.raw`T=[X\ Y\ Z]=`+matrix(frame.T))+'</div></div>'+
      '<p class="small-note">Measurement axes in crystal coordinates. Y = Z × X. Checked: TᵀT = I and det(T) = +1.</p>'+
      '<button class="text-button" data-preview-inputs>Review tensors and Jones states before calculating →</button><span hidden data-frame-matrix="'+esc(JSON.stringify(frame.T))+'"></span>';
  }catch(error){return '<h3>X, Y, Z and T</h3><p role="status">'+esc(error.message)+'</p><p class="small-note">Correct the geometry before calculating intensity.</p>';}
}
function renderLiveFrame(){const host=document.querySelector('#live-frame');if(!host)return;try{host.innerHTML=liveFrameContents(readForm());typeset(host);}catch(error){host.innerHTML='<p role="status">'+esc(error.message)+'</p>';}}
document.addEventListener('input',event=>{if(event.target.closest('#calculator-form'))renderLiveFrame();});
document.addEventListener('change',event=>{if(event.target.closest('#calculator-form'))renderLiveFrame();});
const labRenderCalculator=renderCalculator;
renderCalculator=sectionName=>{
  const host=document.createElement('div');host.innerHTML=labRenderCalculator(sectionName);
  const pipeline=host.querySelector('.calculation-pipeline');
  if(pipeline)pipeline.insertAdjacentHTML('afterend','<section class="card live-frame" id="live-frame">'+liveFrameContents(S.form)+'</section>');
  return host.innerHTML;
};

// Keep the established left explanation / right mathematics layout.
derivationHtml=(entries,explained=true)=>{
  const groups=[],seen=new Set();
  for(const entry of entries){if(entry.kind==='section')groups.push({title:entry.value,step:entry.step,entries:[]});else{if(!groups.length)groups.push({title:'Calculation',step:'01',entries:[]});groups.at(-1).entries.push(entry);}}
  return '<div class="worked-navigation"><button class="text-button" data-expand-math>Expand all steps</button><button class="text-button" data-collapse-math>Collapse all steps</button></div>'+
    '<p class="analytical-color-key">Red equations: analytical Raman tensor and Raman intensity.</p>'+
    (explained?'<div class="worked-columns-label"><span>Explanation and definitions</span><span>Mathematical steps</span></div>':'')+
    groups.map(group=>'<details class="result-math-section worked-section" open id="worked-step-'+esc(group.step)+'"><summary><span class="step-badge">'+esc(group.step)+'</span>'+esc(group.title)+'</summary><div class="result-math-body">'+group.entries.map(entry=>{
      if(entry.kind!=='equation')return '<p class="worked-note">'+rich(entry.value)+'</p>';
      return '<article class="worked-row '+(explained?'':'mathematics-only ')+(entry.analytical_kind?'analytical-expression':'')+'"'+(entry.analytical_kind?' data-analytical="'+esc(entry.analytical_kind)+'"':'')+'>'+
       (explained?'<div class="worked-explanation"><span class="operation-number">STEP '+esc(entry.step)+'</span><p>'+esc(entry.explanation)+'</p>'+localDefinitions(entry.symbols,seen)+'<small class="paper-equation-ref">'+esc(entry.source_equation||entry.derivation_note||'')+'</small></div>':'')+
       '<div class="worked-mathematics">'+math(entry.value)+'<button class="text-button copy-step" data-copy-equation="'+esc(entry.value)+'">Copy LaTeX</button></div></article>';
    }).join('')+'</div></details>').join('')+(explained||!S.result?'':derivationLegendHtml(S.result));
};
derivationModeHtml=()=>'<div class="derivation-view-picker"><div class="button-row" role="group" aria-label="Derivation view">'+[['explained','Explanation + mathematics'],['mathematics','Mathematics only']].map(([key,label])=>'<button class="button '+(S.derivationMode===key?'':'secondary ')+'small" data-derivation-mode="'+key+'" aria-pressed="'+(S.derivationMode===key)+'">'+label+'</button>').join('')+'</div></div>';
const labIntensityCard=finalIntensityCard;
finalIntensityCard=result=>{const host=document.createElement('div');host.innerHTML=labIntensityCard(result);host.querySelector('.final-intensity-card')?.classList.add('analytical-expression');return host.innerHTML;};
calculationExplanation=()=>'<details class="card common-calculation"><summary>Common calculation</summary><p>Material → crystal tensor. Surface and in-plane reference → X, Y, Z and T. Rotate the tensor, insert the incident and detected states, multiply the amplitude by its conjugate, then draw I at each angle.</p><p>Changing the model keeps the declared material, orientation and optical method. For identical inputs, the complete-mode intensity agrees.</p></details>';
calculationPipeline=()=>'<div class="calculation-pipeline" aria-label="Calculation stages">'+['Raman tensor','X, Y, Z and T','Rotated tensor','Polarization','Intensity','Polar plot'].map((label,i)=>'<div><span>0'+(i+1)+'</span><strong>'+label+'</strong></div>').join('')+'</div>';
RAMAN_DOCS.tools['tensor-model']={title:'Calculation model',lead:'All three models use the selected material, orientation and polarization.',sections:[
 {title:modelLabel('NEW_SAN'),paragraphs:['Raman tensor rotation and polarization states for Si and GaAs. See Eqs. (4), (5), and (11) and the supplementary information.'],sources:['cubic']},
 {title:modelLabel('USER_PPT'),paragraphs:['Raman tensor rotation with separate Ag(xx), Ag(yy), and Ag(zz) contributions.']},
 {title:modelLabel('DR_KUMAR'),paragraphs:['Multiply the Jones vectors using the XY block of the rotated Raman tensor. The original two-component calculation is available in the references.'],sources:['optical-source']}]};
RAMAN_DOCS.tools['optical-method']={title:'Polarization',lead:'VV, VH and σ⁺α are available in every model.',sections:[
 {title:'VV and VH',paragraphs:['VV uses parallel linear polarization states; VH uses crossed linear states. Both scan θ.'],sources:['cubic']},
 {title:'σ⁺α',paragraphs:['Use θ=π/4 and β=β′=π/2 in Eq. (11), then scan α.'],sources:['cubic']}]};
RAMAN_DOCS.tools.examples={title:'Starting inputs',lead:'Silicon (500), T₂g, d=1, VV is ready on the first run.',sections:[{title:'Choose your own case',paragraphs:['Select the model and optical method, material, mode, tensor coefficients, surface and in-plane reference. Check the axes and T before calculating. The input JSON files in the download provide reproducible examples.']}]};
RAMAN_DOCS.tools['jones-controls']={title:'Jones vectors',lead:'Incident and detected polarizations.',sections:[{title:'Equation (11)',paragraphs:['θ is the linear-polarization angle; α is the detection-state angle; β and β′ are the relative Jones phases. Their selected values are shown before intensity is calculated.'],sources:['cubic']}]};
for(const key of Object.keys(RAMAN_DOCS.tools))if(/circular|conditional|interference|selection-rules|optical-comparison/.test(key))delete RAMAN_DOCS.tools[key];
RAMAN_DOCS.physics={'paper-order':{title:'Tensor rotation and intensity',lead:'Follow the same connected sequence used in the results.',sections:[
 {title:'Frame and tensor',paragraphs:['Start with the crystal Raman tensors. Construct X, Y, Z and T from the chosen surface, in-plane reference and lattice, then check TᵀT=I and det(T)=+1. Calculate R′=TᵀRT.'],sources:['cubic']},
 {title:'Amplitude and intensity',paragraphs:['Insert the Jones states. Show R′eᵢ, then eₛ*R′eᵢ. Multiply the complete amplitude by its complex conjugate. Sum intensities only for orthogonal unresolved phonon components, then evaluate the angular expression for the polar plot.'],sources:['cubic']}]}};
const descriptions={NEW_SAN:'Tensor rotation and polarization states from the paper and supplementary information.',USER_PPT:'Separate Ag(xx), Ag(yy), and Ag(zz) contributions.',DR_KUMAR:'Jones vectors and the XY block of the rotated Raman tensor.'};
renderHome=()=>heading('VERSION 5','Rotation Raman Tensor Calculation','Calculate Raman intensity for a selected material, orientation, and polarization.')+
 '<div class="button-row"><a class="button" href="#calculator">Open calculator →</a><a class="button secondary" href="'+esc(calculatorWebsiteUrl)+'">Calculator-only website ↗</a><a class="text-link" href="#tutorial">Python tutorial</a></div><div class="cards-grid">'+Object.keys(S.catalog.frameworks).map(key=>'<section class="card"><h2>'+esc(modelLabel(key))+'</h2><p>'+esc(descriptions[key])+'</p></section>').join('')+'</div>';
renderOpticalGuide=()=>'<section class="card optical-guide"><h2>VV, VH and σ⁺α</h2><p>Each model offers all three polarization choices. Review X, Y, Z, T, the rotated tensors and the Jones states before intensity is calculated.</p>'+sourceLinks(['cubic','optical-source'])+'</section>';
