/* Version 4: optional, contextual tours. Never calculate or change scientific inputs. */
(() => {
  'use strict';
  const q = (s, root = document) => root.querySelector(s);
  const qa = (s, root = document) => [...root.querySelectorAll(s)];
  const escape = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const host = () => window.RamanGuideHost;
  const key = 'rotation-raman-guide-v4';
  const defaults = () => ({welcomeDismissed:false,offerSections:false,visited:[],progress:{}});
  let prefs;
  try { prefs = {...defaults(), ...JSON.parse(localStorage.getItem(key) || '{}')}; }
  catch { prefs = defaults(); }
  if (!prefs.progress || typeof prefs.progress !== 'object') prefs.progress = {};
  if (!Array.isArray(prefs.visited)) prefs.visited = [];
  let active = null, index = 0, target = null, layer = null, panel = null, hub = null;
  let invite = null, internalNavigation = false, transition = 0, savedFocus = null, originalMenu = false;
  let positionFrame = null, firstOfferMade = false;
  const openedDetails = new Map();
  const save = () => { try { localStorage.setItem(key, JSON.stringify(prefs)); } catch { /* Session use still works. */ } };
  const frame = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const step = (title, selector, text, extra = {}) => ({title,selector,text,...extra});
  const tour = (id, title, route, steps, description = '') => ({id,title,route,steps,description});
  const route = () => location.hash || '#home';
  const introCopy = {
    'tensor-model':'Choose the full 3D crystal model for material calculations. The original effective 2D source is a separate reference model; its missing crystal-orientation controls are intentional.',
    'optical-method':'The optical profile defines prepared and detected polarization states and the scanned angle. Use VV or VH for co-rotating linear states, and select a circular profile only when its actual optics match your comparison.',
    'examples':'Selecting an example does not load it. Use Load selected example, review all populated inputs, and calculate. Loading replaces the current form, so export useful results first.',
    'material-tensor':'A material preset supplies a stated symmetry and axis convention. It does not infer measured complex coefficients, sample temperature, microscopic resonance, or lattice constants.',
    'coefficients':'Magnitude and phase define complex tensor entries. Optional equality constraints copy both. The Ag(xx), Ag(yy), and Ag(zz) plots remain separate Cartesian contribution powers.',
    'orientation':'Specify the reciprocal-lattice surface normal, a valid in-plane reference, and lattice metric. The program forms a proper orthonormal frame before rotating the full tensor.',
    'jones-controls':'Jones angles and relative phases describe the actual optical states. Fields are active only for relevant profiles; the conditional circular selection check is separate from the intensity calculation.',
    'display':'Choose an angular sampling grid and optional display normalization. Raw CSV keeps the original intensities. A display choice does not alter the tensor or optical states.',
    'results':'Read the input/result status before interpreting a plot. The tabs separate figures, mathematics, values, frame, checks, and exports. Recalculate after changing inputs.',
    'validation':'Use checks to assess algebra and implementation within their stated scope. Passing reference identities does not establish the calibration or microscopic correctness of experimental inputs.',
    'comparisons':'Freeze calculated inputs as session snapshots, then compare compatible channels and declared scales. The optional normalized comparison answers a shape question.',
    'benchmark':'The silicon benchmark computes six surfaces and three profiles using one coefficient scale. It reproduces the specified reference states, rather than all experimental optical chains.',
    'checking-procedures':'Each procedure records its purpose, expected identity, scope, status, and evidence. Source-specific checks and current-material generalizations must be interpreted separately.',
    'optical-comparison':'Follow preparation, Raman response, return optics, and detection. Distinct detector states can produce distinct curves for the same tensor; their physical configuration determines the reference.'
  };

  function overview() {
    return tour('overview','Start here: the workspace','#home',[
      step('Your Home workspace','.hero','Start from the crystal-to-intensity workflow. Home introduces the model, links to the calculator and Python source, and explains why optical profiles can give different curves.',{tip:'This tour changes only the displayed page, menu, and explanatory panels. It does not edit coefficients or run Python.',route:'#home'}),
      step('Open navigation with the three lines','#menu-toggle','The menu stays closed when the website first opens. Press this button whenever you want to reveal or hide the section list.',{menu:true}),
      step('Find a tool or Python cell','.nav-search','Search words such as orientation, VV, QWP, or Cell 6. Search results link directly to relevant explanations and source cells.',{menu:true}),
      step('Introduction: understand each input','#navigation a[href="#introduction"]','Introduction explains model choice, optical profiles, examples, material tensors, coefficients, orientation, display choices, results, comparisons, and validation. Expand its arrow to see individual topics.',{menu:true}),
      step('Python tutorial: inspect all 22 cells','#navigation a[href="#tutorial"]','The tutorial displays the actual current notebook code. Each block includes an explanation, its purpose, and a checking point. VV/VH definitions start in Cell 5 and the shared scattering engine is in Cell 6.',{menu:true}),
      step('Calculator: enter your physical configuration','#navigation a[href="#calculator"]','Choose a model, material, optical profile, coefficients, orientation, and display options. Calculate explicitly, then inspect the resulting figures, equations, and data.',{menu:true}),
      step('Physics & equations: inspect assumptions','#navigation a[href="#physics"]','Read the tensor-rotation convention, Jones states, coherent amplitude, interference, and scientific limits. The page-specific guide highlights the actual topics available.',{menu:true}),
      step('References & downloads: inspect sources','#navigation a[href="#references"]','Find primary physics references, the current notebook, complete Python code, runtime adapter, plot style, and original implementation references.',{menu:true}),
      step('Choose the optical reference','.optical-guide','Home compares the physical meaning of all nine optical profiles. Match the actual preparation, detector state, angle zero, and geometry before comparing polar plots.',{route:'#home',menu:false}),
      step('Guidance whenever you need it','#user-guide-open','This button opens all tours, the guide for your current page, saved progress, and optional section prompts. Each page also has a Guide this page button.',{tip:'Use Next and Back, jump to any step, or close the guide at any time. Nothing starts automatically after you dismiss an offer.'})
    ],'A short tour of Home, the hamburger menu, and all six main sections.');
  }

  function homeTour() {
    return tour('page:#home','Home in detail','#home',[
      step('From crystal orientation to intensity','.hero','The opening panel describes the complete calculation: rotate the crystal tensor, prepare the actual optical states, contract the complex amplitude, and form its squared modulus.'),
      step('Open the calculator','.hero a[href="#calculator"]','This opens the input form and a stored reference example. A saved example is identified as such; press Calculate rotation + Raman to generate a result in this browser.'),
      step('Inspect the Python code','.hero a[href="#tutorial"]','Read the current notebook cell by cell. The website tutorial and Python downloads are generated from the same source and record its fingerprint.'),
      step('Understand the library scope','.stats-row','The counters describe 21 point-group templates, nine optical profiles, and 22 code cells. They do not mean that every material has experimentally determined tensor coefficients.'),
      step('Why the optical profiles differ','.optical-guide','The optical guide distinguishes incoming preparation, scattering tensor, return optics, and detection. Selection of a different physical state can legitimately change a curve.'),
      step('Inspect one of the nine profiles','#guide-profile','This selector changes the explanation on Home. It does not change calculator inputs. Read the selected profile’s effective states, scan meaning, equations, and source scope.'),
      step('Compare a fixed tensor','.guide-comparison','The side-by-side example holds the tensor and intensity scale fixed while changing detection. It isolates the role of the detector and interference.'),
      step('Choose your next section','.paths','Use Introduction for tool meanings, the Python tutorial for implementation, and Physics & equations for conventions. The hamburger menu provides the same destinations.'),
      step('Follow the calculation stages','.workflow-strip','The four stages connect lattice and surface geometry to the rotated 3D tensor, optical amplitude, intensity, and exported evidence.'),
      step('Open or dismiss help','#user-guide-open','Start another guide, resume a paused one, or change section-prompt preferences. Guidance stays optional; Home and the calculator work without it.')
    ],'Home controls, optical comparison, library scope, and navigation.');
  }

  function calculatorTour() {
    const r = '#calculator';
    return tour('calculator-inputs','Calculator: inputs and workflow',r,[
      step('1.1 Choose the tensor model','#tensor-model','General crystal uses a full complex 3×3 Raman tensor. The original 2D optical reference is a separate model with its own source parameters.'),
      step('1.2 Choose the optical method','#optical-method','VV means parallel linear input and detection; VH means crossed linear detection. Both linear states co-rotate. Circular, elliptical, QWP, and custom Jones profiles represent different actual states.',{tip:'A material name does not choose the experimental optics for you.'}),
      step('1.3–1.4 Select and load an example','#example','Choose an example here, then press Load selected example when you want to replace the form. This tour never presses that loading button.'),
      step('1.5–1.6 Label and document the run','#case-label','Give the run a useful case label and record experimental context in Input note. The exported configuration carries these values.'),
      step('2.1–2.2 Material and point group','#material','A material fixes its stated parent symmetry. Select General point group / custom tensor if you need another symmetry or an explicit custom tensor.',{optional:true}),
      step('2.3 Select phonon modes','.modes-grid','Choose the Raman modes or branches to compute. Orthogonal unresolved degenerate partners add as intensities; this differs from adding entries within one coherent phonon tensor.',{optional:true}),
      step('2.4–2.5 Set magnitudes and phases','.coefficient-row','Enter supplied or fitted complex coefficients using magnitude and phase in degrees. Negative magnitudes are not a substitute for phase. Optional Ag equality constraints copy both.',{optional:true}),
      step('2. Original source parameters','[data-section-key="02"]','The effective 2D source exposes its source parameters in this section. A material frame is intentionally absent in that model.',{only:()=>!!q('#source-a')}),
      step('3.1 Choose the orientation input','#orientation-kind','Use surface hkl plus in-plane uvw, or a proper manual frame. A manual frame must be real, orthonormal, and have determinant +1.',{optional:true}),
      step('3.2–3.5 Surface and in-plane reference','#surface','Choose a surface preset or enter custom integer h,k,l. Use automatic X or supply a valid in-plane u,v,w satisfying hu+kv+lw=0.',{optional:true}),
      step('3.6–3.7 Normal side and frame angle','#frame-angle','The normal sign and in-plane frame angle define the measurement axes. Matching only hkl is insufficient when comparing an angular pattern with another convention.',{optional:true}),
      step('3.8–3.9 Supply the lattice metric','#lattice-0','Lengths use one common unit and lattice angles use degrees. A tilted noncubic plane normal is a reciprocal-lattice quantity; unity ratios are only the declared reference geometry.',{optional:true}),
      step('4. Jones states and active controls','[data-section-key="04"]','Expand this section to see the selected incident/detection states and relevant zero angles or phases. The controls change with the profile. Conditional circular-rule fields do not determine the intensity scale.'),
      step('5. Sampling and normalization','#angular-grid','The angular grid sets the plotted samples. Optional normalization uses a declared common scale. Raw CSV remains unnormalized, and continuous extrema are calculated separately.'),
      step('6. Calculate the current inputs','[data-calculate]','Press this button after reviewing the inputs. The first run loads scientific Python in the browser. Stop terminates that worker and clears its session snapshots.',{tip:'The interactive guide never runs a calculation on your behalf.'}),
      step('Check result freshness','#calculation-status','A stored example or a previous run is not automatically the result of edited inputs. Review the status and recalculate after changes before exporting or comparing.'),
      step('7. Inspect the result tabs','.result-tabs','Use plots for figures, Mathematical steps for the derivation, Intensity values for numerical summaries, and 3D frame for axes. Checks and benchmarks have separate scopes.'),
      step('7. Export results with their inputs','.results-toolbar','Download the complete result archive, unnormalized CSV, or a comparison snapshot after calculating. Disabled controls explain which outputs require a fresh runtime result.')
    ],'Every input group, the physical configuration, calculation, result status, and exports.');
  }

  function resultsTour() {
    const tabs = [
      ['plots','Polar plots','Main Ag curves show separate Cartesian powers. Each figure offers SVG, PNG, and PDF export after a fresh calculation. The complete coherent-mode response remains in the audit.'],
      ['math','Mathematical steps','Follow the frame construction, tensor rotation, Jones states, amplitude contraction, conjugation, and intensity. Expand individual calculation blocks as needed.'],
      ['values','Intensity values','Inspect the calculated continuous extrema and channel summaries. The raw CSV export contains angular samples rather than only fitted extrema.'],
      ['frame','3D frame','Inspect crystal and measurement axes, the selected surface normal, and the orientation matrix. This view requires the relevant 3D geometry output.'],
      ['procedures','Checking procedures','Read each procedure’s purpose, scope, expected equation, and evidence. A stored reference report is identified until a new calculation regenerates current evidence.'],
      ['checks','Protocol checks','Independent reconstructions check the current amplitude, circular-basis transformation, frame orthogonality, and interference bookkeeping. Small floating-point residuals are expected.'],
      ['latex','LaTeX','Copy or download symbolic intensity and the complete mathematical derivation. These are calculated source equations, not a screenshot of a formula.'],
      ['validation','Validation','The full model suite runs only when you press Run full validation. It checks implementation identities within stated assumptions; it does not calibrate experimental optics.'],
      ['comparisons','Comparisons','Save at least two fresh calculated snapshots to compare results from frozen inputs. Changing a form later does not modify an existing snapshot.'],
      ['benchmark','Silicon benchmark','Compute the six reference surfaces with VV, VH, and the declared σ⁺α reference. All 18 cases use a shared coefficient scale and independent source identities.']
    ];
    return tour('calculator-results','Calculator: every result tab','#calculator',tabs.map(([tab,title,text])=>step(title,'#result-pane',text,{tab})), 'Figures, derivations, values, frame, checks, LaTeX, comparisons, and the benchmark.');
  }

  function sectionTour(r) {
    const ctx = host().context(), parts = r.slice(1).split('/'), root = parts[0];
    if (root === 'home') return homeTour();
    if (root === 'calculator') {
      if (!parts[1]) return calculatorTour();
      const descriptions = {
        procedures:['Checking procedures','Review purpose, procedure, expected identity, scope, status, and actual evidence for each source check and its current-run generalization.'],
        validation:['Reference validation','Run the model/source validation explicitly, then inspect counts, failures, and downloaded evidence. A stored example report is not a new execution.'],
        comparisons:['Comparison snapshots','Save fresh calculations before comparing them. Snapshots are kept in this browser worker session and are cleared when you Stop or reload.'],
        benchmark:['Silicon benchmark','Calculate six surfaces with three optical profiles, inspect a selected case, and export the reference data using one shared coefficient scale.']
      };
      const [title,text] = descriptions[parts[1]] || ['Calculator output','Inspect the current output and its assumptions.'];
      return tour('page:'+r,title,r,[step(title,'#result-pane',text),step('Inputs remain explicit','#calculator-form','These controls still define the next main calculation. A benchmark inspection loads a case only when its explicit button is used.'),step('Scope and evidence','#result-pane','Read the explanation and status before using the result. Actions that start Python are optional; this guide never activates them.'),step('Download and retain your work','.results-toolbar','Export useful current results before reloading or stopping the worker. Guide progress is stored separately from calculation data.')],text);
    }
    if (root === 'tutorial') {
      const number = parts[1] === 'cell' ? Number(parts[2]) : null;
      if (!number) return tour('page:'+r,'Python tutorial overview',r,[
        step('The exact 22-cell program','.page-title-row','Each card opens the actual code of one notebook cell with a line-mapped explanation. These numbers are code-cell order, not Jupyter execution counters.'),
        step('Find a code cell','.tutorial-grid','Choose a cell by title and purpose. Cell 5 defines optical states, Cell 6 applies the scattering engine, Cell 12 explains mathematical steps, and Cell 14 implements the silicon reference.'),
        step('VV and VH definitions','a[href="#tutorial/cell/5"]','Start here to see parallel/crossed linear Jones vectors and what changes during the scan.'),
        step('Amplitude and intensity engine','a[href="#tutorial/cell/6"]','Continue here for the full 3D rotation, transverse restriction, complex contraction, and intensity harmonics.'),
        step('Guide on every cell','.guide-page-help','Open any of the 22 cells and choose Guide this page. It walks through that cell’s actual title, source, explanation blocks, checking points, and navigation.')
      ],'Find source cells and understand the tutorial layout.');
      const c = ctx.cells.find(x=>x.number === number);
      return tour('page:'+r,'Python Cell '+number+': '+(c?.title || 'source'),r,[
        step('Cell '+number+': '+(c?.title || 'source'),'.page-title-row','This page displays the current source of this code cell, followed by purpose and line-mapped explanations. Read the execution sequence before individual blocks.'),
        step('Execution sequence','.workflow-list','Follow what this cell defines, what it calls, and which objects later cells use. In Jupyter, execute prerequisite cells in the notebook order.'),
        step('Complete source and fingerprint','.full-source','Expand this panel to inspect or copy every source line and the cell SHA-256 fingerprint. The downloadable notebook is the recommended executable entry point.'),
        step('Read one code block','.walkthrough-block','Each block maps an actual source-line interval to an explanation. Expand a block to see its purpose, checking point, and matching code.'),
        step('Why this code is written','.walkthrough-body','Use the purpose and checking point to distinguish physical assumptions, numerical operations, and UI/export behavior. The displayed source lines are not an alternative calculation.'),
        step('Expand, collapse, or print','.content-section-tools','Expand all blocks to read the complete explanation, collapse them for navigation, or print this page. Printing is an explicit action.'),
        step('Download or copy this cell','.page-title-row .button-row','Use Download cell .py or Copy full cell when you need this particular source. A single cell may depend on definitions in earlier cells.'),
        step('Move through the notebook','.prev-next','Use Previous and Next to continue in code-cell order, or return to the full tutorial using the menu.')
      ],'A contextual walkthrough of this exact source cell.');
    }
    if (root === 'introduction' || root === 'physics') {
      const docs = root === 'introduction' ? ctx.tools : ctx.physics;
      const doc = docs[parts[1]];
      if (doc) {
        const steps = [step(doc.title,'.page-title-row',introCopy[parts[1]] || doc.lead)];
        doc.sections.forEach((s,i)=>{
          const paragraphs = (s.paragraphs || []).slice(0,2).join(' ');
          steps.push(step(s.title,'#doc-'+i,paragraphs || 'Read the equations, ordered procedure, or comparison table in this section. The accompanying source links define its reference scope.',{tip:s.note || (s.equations?.length ? 'Equations use the frame, phase, and normalization conventions stated on this page.' : undefined)}));
        });
        steps.push(step('Continue to the next topic','.prev-next','Use the neighboring topic links to continue the explanation, or open the calculator when the relevant inputs and conventions are clear.'));
        return tour('page:'+r,doc.title,r,steps,doc.lead);
      }
      return tour('page:'+r,root === 'introduction' ? 'Introduction: tool-by-tool' : 'Physics & equations',r,[
        step(root === 'introduction' ? 'Understand the tool workflow' : 'Understand the mathematical workflow','.page-title-row',root === 'introduction' ? 'Follow the tool explanations before entering experimental inputs. This is the guide to what each control means.' : 'The physics section explains assumptions and derivations that connect the material tensor to measured intensity.'),
        ...Object.entries(docs).map(([id,d])=>step(d.title,'.tutorial-grid a[href="#'+root+'/'+id+'"]',introCopy[id] || d.lead)),
        step('A detailed guide on every topic','.guide-page-help','Open a topic and choose Guide this page for a section-by-section tour of its actual explanation, equations, tables, and references.')
      ],root === 'introduction' ? 'Understand every tool topic before using its controls.' : 'Explore each mathematical topic and its scientific limits.');
    }
    return tour('page:'+r,'References & Python downloads',r,[
      step('Identify the primary sources','.page-title-row','References identify the physics papers, optical conventions, software documentation, and original implementation notebooks used by the project.'),
      step('Read what each source supports','.reference-item','Each reference includes authors, publication details, a link, and the particular calculation or convention it supports. An implementation reference is not a measured tensor assignment.'),
      step('Download the current notebook','#downloads','The Version 4 notebook is the recommended Python entry point. Run all 22 code cells in order in a Jupyter or Colab environment with the listed requirements.'),
      step('Choose the right Python file','#downloads a[href="./downloads/All_Python_Programs.zip"]','The complete program archive includes the notebook, matching source, reusable engine, browser adapter, style, requirements, and preserved original references.'),
      step('Original references stay attributable','#ref-kumar-original','The original uploaded implementation is retained as a source reference. Its own historical metadata is preserved; the application release is Version 4.'),
      step('Check source correspondence','#main-content > .card:last-child','The notebook fingerprint connects the live tutorial and scientific functions to their source. Guide settings and guide progress are separate from scientific data.')
    ],'Primary sources, notebook downloads, original references, and source correspondence.');
  }

  function allTours() {
    if (!host()?.ready()) return [overview()];
    const ctx = host().context();
    const routes = ['#home','#introduction','#tutorial','#physics','#references',
      ...Object.keys(ctx.tools).map(x=>'#introduction/'+x),
      ...Object.keys(ctx.physics).map(x=>'#physics/'+x),
      ...ctx.cells.map(x=>'#tutorial/cell/'+x.number),
      '#calculator/procedures','#calculator/validation','#calculator/comparisons','#calculator/benchmark'];
    return [overview(),calculatorTour(),resultsTour(),...routes.map(sectionTour)];
  }

  function closeInvite() {
    if (invite) invite.remove(); invite = null;
    prefs.welcomeDismissed = true; save();
  }

  function renderPageHelp() {
    const main = q('#main-content');
    if (!main || !host()?.ready()) return;
    q('.guide-page-help',main)?.remove();
    const bar = document.createElement('div'); bar.className = 'guide-page-help';
    bar.innerHTML = '<span>Optional interactive help for this page</span><button type="button" data-guide-current>Guide this page <span aria-hidden="true">↗</span></button>';
    main.prepend(bar);
    const r = route(), fresh = !prefs.visited.includes(r);
    if (fresh) { prefs.visited.push(r); save(); }
    if (active || internalNavigation || hub?.open) return;
    const offer = (!prefs.welcomeDismissed && !firstOfferMade && r === '#home') || (prefs.offerSections && fresh);
    if (offer) {
      firstOfferMade = true;
      if (invite) invite.remove();
      invite = document.createElement('aside'); invite.className = 'guide-invite'; invite.setAttribute('aria-label','Optional user guide');
      invite.innerHTML = '<h2>'+(!prefs.welcomeDismissed?'Would you like a quick tour?':'Explore this page?')+'</h2><p>See where to find the inputs, results and Python code. You can reopen User guide from the header.</p><div class="button-row"><button type="button" class="button small" data-guide-offer-start>'+(!prefs.welcomeDismissed?'Start workspace tour':'Guide this page')+'</button><button type="button" class="guide-dismiss" data-guide-offer-dismiss>Not now</button></div>';
      invite.dataset.overview = String(!prefs.welcomeDismissed);
      document.body.append(invite);
    }
  }

  function option(t, resume = false) {
    const p = prefs.progress[t.id];
    const status = p?.completed ? 'Completed · replay anytime' : p ? 'Paused at step '+(p.index+1)+' · resume available' : t.steps.length+' explained steps';
    return '<button type="button" class="guide-tour-option" data-guide-tour="'+escape(t.id)+'" '+(resume?'data-guide-resume':'')+'><strong>'+escape(t.title)+'</strong><span>'+escape(t.description)+'</span><small>'+escape(status)+'</small></button>';
  }

  function openHub() {
    if (!host()?.ready()) return;
    if (active) stop(false,false);
    closeInvite();
    hub?.remove(); hub = document.createElement('dialog'); hub.className = 'guide-hub'; hub.setAttribute('aria-labelledby','guide-hub-title');
    const current = sectionTour(route()), tours = allTours();
    const progress = tours.filter(t=>prefs.progress[t.id] && !prefs.progress[t.id].completed);
    hub.innerHTML = '<div class="guide-hub-head"><div><span class="kicker">VERSION 4 · OPTIONAL USER GUIDE</span><h2 id="guide-hub-title">User guide</h2><p>Choose a tour or get help with the current page. You can close the guide at any time.</p></div><button type="button" class="guide-close" data-guide-hub-close aria-label="Close user guide">×</button></div><div class="guide-hub-body"><h3>Start or continue</h3><div class="guide-tour-grid">'+option(overview())+option(current)+option(calculatorTour())+option(resultsTour())+'</div>'+(progress.length?'<h3>Resume a paused guide</h3><div class="guide-tour-grid">'+progress.map(t=>option(t,true)).join('')+'</div>':'')+'<h3>Guides for every section and Python cell</h3><div class="guide-tour-grid">'+tours.filter(t=>!['overview','calculator-inputs','calculator-results'].includes(t.id)).map(t=>option(t)).join('')+'</div><div class="guide-settings"><label class="guide-setting"><input type="checkbox" id="guide-offer-sections" '+(prefs.offerSections?'checked':'')+'><span>Offer a guide when I first visit a new page. Tours start only when I choose to use them.</span></label><p class="guide-storage-note">This browser stores only guide preferences, visited guide pages, and step progress. Scientific inputs and results are not saved by the guide. Storage may be unavailable in private browser modes.</p><button type="button" class="guide-reset" data-guide-reset>Reset guide progress and preferences</button></div></div>';
    document.body.append(hub); hub.showModal();
    hub.addEventListener('click',event=>{if(event.target===hub)hub.close();});
    hub.addEventListener('close',()=>q('#user-guide-open')?.focus());
  }

  async function navigate(r) {
    if (!r || route() === r) { await frame(); return; }
    internalNavigation = true;
    try {
      await new Promise(resolve=>{
        const done=()=>{if(route()===r){document.removeEventListener('raman:route',done);resolve();}};
        document.addEventListener('raman:route',done);location.hash=r;
      });
      await frame();
    } finally { internalNavigation = false; }
  }

  function reveal(node) {
    for (let p=node;p;p=p.parentElement) if (p.tagName==='DETAILS'&&!p.open) { if(!openedDetails.has(p))openedDetails.set(p,false);p.open=true; }
  }

  async function start(t, resume = false) {
    if (host()?.busy()) { window.alert('Please wait for the current calculation to finish before starting a guide.'); return; }
    if (active) stop(false,false);
    hub?.close();closeInvite();savedFocus=document.activeElement;
    originalMenu=q('#menu-toggle')?.getAttribute('aria-expanded')==='true';
    active=t;
    const token=++transition;
    await navigate(t.route);
    if(token!==transition||active!==t)return;
    active={...t,steps:t.steps.filter(s=>(!s.only||s.only())&&(!s.optional||q(s.selector)))};
    index=resume?Math.min(prefs.progress[t.id]?.index||0,active.steps.length-1):0;
    layer=document.createElement('div');layer.className='guide-layer';
    layer.innerHTML='<div class="guide-shade" data-shade="top"></div><div class="guide-shade" data-shade="bottom"></div><div class="guide-shade" data-shade="left"></div><div class="guide-shade" data-shade="right"></div><div class="guide-spotlight"></div><section class="guide-panel" role="dialog" aria-modal="true" aria-labelledby="guide-step-title" aria-describedby="guide-step-copy"></section><div class="guide-live" role="status" aria-live="polite"></div>';
    document.body.append(layer);panel=q('.guide-panel',layer);
    await show(index);
  }

  function persist(completed=false) {
    if(!active)return;
    prefs.progress[active.id]={index,completed};save();
  }

  async function show(next) {
    if(!active)return;
    const direction=next<index?-1:1;
    const token=++transition;
    index=Math.max(0,Math.min(next,active.steps.length-1));
    const s=active.steps[index];
    await navigate(s.route||active.route);
    if(token!==transition||!active)return;
    host().setMenu(s.menu===true);
    if(s.tab)q('[data-result-tab="'+s.tab+'"]')?.click();
    await frame();if(token!==transition||!active)return;
    if(s.only&&!s.only()) { if(index+direction>=0&&index+direction<active.steps.length){await show(index+direction);return;} }
    target=q(s.selector);
    if(s.optional&&!target) { if(index+direction>=0&&index+direction<active.steps.length){await show(index+direction);return;} }
    if(target){reveal(target);target.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});}
    const missing=!target;
    panel.innerHTML='<div class="guide-panel-head"><span class="guide-step-meta">'+escape(active.title)+' · '+(index+1)+' / '+active.steps.length+'</span><button type="button" class="guide-close" data-guide-stop aria-label="Close tour">×</button></div><h2 id="guide-step-title" tabindex="-1">'+escape(s.title)+'</h2><div id="guide-step-copy"><p>'+escape(s.text)+'</p>'+(s.tip?'<div class="guide-tip">'+escape(s.tip)+'</div>':'')+(missing?'<p class="guide-missing">This control is not shown in the current configuration or result. The explanation still describes when it is available.</p>':'')+'</div><progress max="'+active.steps.length+'" value="'+(index+1)+'" aria-label="Tour progress"></progress><label class="guide-target-description" for="guide-step-jump">Jump to a step</label><select id="guide-step-jump">'+active.steps.map((x,i)=>'<option value="'+i+'" '+(i===index?'selected':'')+'>'+(i+1)+'. '+escape(x.title)+'</option>').join('')+'</select><div class="guide-panel-controls"><button type="button" class="button secondary" data-guide-back '+(index===0?'disabled':'')+'>Back</button><button type="button" class="button guide-finish" data-guide-next>'+(index===active.steps.length-1?'Finish':'Next')+' <span aria-hidden="true">→</span></button></div><div class="guide-panel-links"><button type="button" data-guide-hub>All guides / pause</button><button type="button" data-guide-stop>Skip / close tour</button></div>';
    persist();await frame();if(token!==transition||!active)return;
    position();q('#guide-step-title',panel).focus({preventScroll:true});
    q('.guide-live',layer).textContent='Step '+(index+1)+' of '+active.steps.length+': '+s.title;
  }

  function position() {
    if(!layer||!panel)return;
    const w=innerWidth,h=innerHeight,pad=7;
    let r=target?.getBoundingClientRect();
    if(!r||!r.width||!r.height||r.right<=0||r.bottom<=0)r={left:w/2,top:h/3,right:w/2,bottom:h/3,width:0,height:0};
    const left=Math.max(4,r.left-pad),top=Math.max(4,r.top-pad),right=Math.min(w-4,r.right+pad),bottom=Math.min(h-4,r.bottom+pad);
    const rect=(s,x,y,ww,hh)=>Object.assign(q(s,layer).style,{left:x+'px',top:y+'px',width:Math.max(0,ww)+'px',height:Math.max(0,hh)+'px'});
    rect('[data-shade="top"]',0,0,w,top);rect('[data-shade="bottom"]',0,bottom,w,h-bottom);rect('[data-shade="left"]',0,top,left,bottom-top);rect('[data-shade="right"]',right,top,w-right,bottom-top);rect('.guide-spotlight',left,top,right-left,bottom-top);
    const pw=panel.offsetWidth,ph=panel.offsetHeight,margin=12,gap=18;
    let x,y;
    if(w<=620){x=margin;y=top>h/2?margin:h-ph-margin;}
    else if(w-right>=pw+gap+margin){x=right+gap;y=Math.min(top,h-ph-margin);}
    else if(left>=pw+gap+margin){x=left-pw-gap;y=Math.min(top,h-ph-margin);}
    else if(h-bottom>=ph+gap){x=Math.min(left,w-pw-margin);y=bottom+gap;}
    else if(top>=ph+gap){x=Math.min(left,w-pw-margin);y=top-ph-gap;}
    else{x=w-pw-margin;y=h-ph-margin;}
    Object.assign(panel.style,{left:Math.max(margin,x)+'px',top:Math.max(margin,y)+'px'});
  }

  function stop(completed=false,returnFocus=true) {
    if(!active)return;
    persist(completed);++transition;
    layer?.remove();layer=panel=target=null;active=null;
    for(const [d,wasOpen]of openedDetails)if(d.isConnected)d.open=wasOpen;
    openedDetails.clear();host()?.setMenu(originalMenu);
    if(returnFocus)(savedFocus?.isConnected&&savedFocus.getClientRects().length?savedFocus:q('#user-guide-open'))?.focus({preventScroll:true});
  }

  document.addEventListener('click',event=>{
    const b=event.target.closest('button');if(!b)return;
    if(b.id==='user-guide-open'||b.hasAttribute('data-guide-hub')){openHub();return;}
    if(b.hasAttribute('data-guide-current')){start(sectionTour(route()));return;}
    if(b.hasAttribute('data-guide-offer-start')){const useOverview=invite?.dataset.overview==='true';start(useOverview?overview():sectionTour(route()));return;}
    if(b.hasAttribute('data-guide-offer-dismiss')){closeInvite();return;}
    if(b.hasAttribute('data-guide-hub-close')){hub?.close();return;}
    if(b.dataset.guideTour){const t=allTours().find(x=>x.id===b.dataset.guideTour)||sectionTour(route());start(t,b.hasAttribute('data-guide-resume'));return;}
    if(b.hasAttribute('data-guide-reset')){prefs=defaults();prefs.welcomeDismissed=true;save();openHub();return;}
    if(b.hasAttribute('data-guide-stop')){stop();return;}
    if(b.hasAttribute('data-guide-back')){show(index-1);return;}
    if(b.hasAttribute('data-guide-next')){if(index===active.steps.length-1)stop(true);else show(index+1);}
  });
  document.addEventListener('change',event=>{
    if(event.target.id==='guide-step-jump')show(Number(event.target.value));
    if(event.target.id==='guide-offer-sections'){prefs.offerSections=event.target.checked;save();}
  });
  document.addEventListener('keydown',event=>{
    if(!active)return;
    if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();stop();return;}
    if(event.key==='Tab'){
      const nodes=qa('button:not(:disabled),select',panel),first=nodes[0],last=nodes.at(-1);
      if(event.shiftKey&&(document.activeElement===first||!panel.contains(document.activeElement))){event.preventDefault();last?.focus();}
      else if(!event.shiftKey&&(document.activeElement===last||!panel.contains(document.activeElement))){event.preventDefault();first?.focus();}
    }
  },true);
  document.addEventListener('raman:route',()=>{
    if(active&&!internalNavigation)stop(false,false);
    renderPageHelp();
  });
  const schedule=()=>{if(positionFrame)cancelAnimationFrame(positionFrame);positionFrame=requestAnimationFrame(position);};
  addEventListener('resize',schedule);addEventListener('scroll',schedule,true);
  if(host()?.ready())renderPageHelp();
})();
