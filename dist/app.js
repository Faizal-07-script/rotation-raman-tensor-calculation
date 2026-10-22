'use strict';
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone = value => JSON.parse(JSON.stringify(value));
const math = value => '<div class="equation" data-tex="' + esc(value) + '"></div>';
const rich = value => esc(value).replace(/\x60([^\x60]+)\x60/g, '<code>$1</code>').replace(/\n/g, '<br>');
const compact = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)) ? Number(Number(value).toPrecision(7)).toString() : '—';
const S = {catalog:null,cells:[],tutorial:[],form:null,result:null,dirty:false,busy:false,tab:'plots',
  error:null,comparisons:[],comparison:null,benchmark:null,validation:null,runtimeHasRun:false,
  selectedExample:'SLIDE',relation:'free',lastCrystal:null,openGroups:new Set(['introduction']),searchIndex:[]};
let toastTimer,preparedDownloadUrl;

class PythonEngine {
  constructor(){this.worker=null;this.pending=new Map();this.sequence=0;this.ready=false;this.loading=null;}
  create(){
    this.worker=new Worker('./engine-worker.js');
    this.worker.onmessage=event=>{
      const data=event.data;
      if(data.kind==='progress'){$('#operation-message').textContent=data.message;return;}
      if(data.kind==='log'){console.info('[Python]',data.message);return;}
      const pending=this.pending.get(data.id);if(!pending)return;
      this.pending.delete(data.id);
      if(data.kind==='error')pending.reject(new Error(data.message));
      else pending.resolve(data.binary?data.buffer:data.result);
    };
    this.worker.onerror=event=>{for(const item of this.pending.values())item.reject(new Error(event.message||'The Python worker could not start.'));this.pending.clear();this.worker?.terminate();this.worker=null;this.ready=false;this.loading=null;clearRuntimeRecords();setEngineStatus('Engine needs restart','error');};
  }
  send(type,payload){if(!this.worker)this.create();const id=++this.sequence;return new Promise((resolve,reject)=>{this.pending.set(id,{resolve,reject});this.worker.postMessage({id,type,payload});});}
  async ensure(){if(this.ready)return;if(!this.loading){setEngineStatus('Starting Python…','busy');this.loading=this.send('init',{}).then(()=>{this.ready=true;setEngineStatus('Python ready','');}).catch(error=>{this.worker?.terminate();this.worker=null;this.loading=null;clearRuntimeRecords();setEngineStatus('Python needs retry','error');throw error;});}return this.loading;}
  async request(type,payload={}){await this.ensure();return this.send(type,payload);}
  stop(){if(this.worker)this.worker.terminate();this.worker=null;this.ready=false;this.loading=null;for(const item of this.pending.values())item.reject(new Error('Operation stopped. Runtime snapshots were cleared. Calculate again to restart Python.'));this.pending.clear();clearRuntimeRecords();setEngineStatus('Python stopped','neutral');}
}
const engine=new PythonEngine();
function clearRuntimeRecords(){S.runtimeHasRun=false;S.comparisons=[];S.comparison=null;S.benchmark=null;S.validation=null;}

function setEngineStatus(text,kind=''){const host=$('#engine-indicator');host.innerHTML='<span class="status-dot '+esc(kind)+'"></span>'+esc(text);}
function toast(message){clearTimeout(toastTimer);const node=$('#toast');node.textContent=message;node.hidden=false;toastTimer=setTimeout(()=>node.hidden=true,4200);}
function download(content,name,type='text/plain'){if(preparedDownloadUrl)URL.revokeObjectURL(preparedDownloadUrl);const blob=content instanceof Blob?content:new Blob([content],{type});preparedDownloadUrl=URL.createObjectURL(blob);const a=$('#download-link');a.href=preparedDownloadUrl;a.download=name;$('#download-name').textContent=name;$('#download-ready').hidden=false;if(navigator.userActivation?.isActive)a.click();else toast('File ready. Select Save file to download it.');}
async function copyText(text){try{await navigator.clipboard.writeText(text);toast('Copied to clipboard.');}catch{const area=document.createElement('textarea');area.value=text;document.body.append(area);area.select();document.execCommand('copy');area.remove();toast('Copied to clipboard.');}}
function sourceLinks(ids=[]){return ids.length?'<div class="citations">Sources: '+ids.map(id=>{const r=RAMAN_DOCS.references.find(x=>x.id===id);return r?'<a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">['+r.number+'] '+esc(r.authors)+'</a>':'';}).join(' · ')+'</div>':'';}
function typeset(root=document){
  $$('[data-tex]',root).forEach(node=>{if(node.dataset.rendered)return;try{katex.render(node.dataset.tex,node,{displayMode:true,throwOnError:false,strict:false,trust:false});node.dataset.rendered='true';}catch{node.textContent=node.dataset.tex;}});
  $$('code.language-python',root).forEach(node=>{if(!node.dataset.highlighted)hljs.highlightElement(node);});
}
function slug(value){return String(value).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');}
function heading(kicker,title,lead,actions=''){return '<div class="page-title-row"><div><span class="kicker">'+esc(kicker)+'</span><h1>'+esc(title)+'</h1><p class="page-lead">'+esc(lead)+'</p></div>'+actions+'</div>';}

function renderNavigation(){
  const groups=[
    ['introduction','1','Introduction',Object.entries(RAMAN_DOCS.tools).map(([key,d])=>['#introduction/'+key,d.title])],
    ['tutorial','3','Python tutorial',S.cells.map(c=>['#tutorial/cell/'+c.number,'Cell '+c.number+' · '+c.title])],
    ['calculator','4','Calculator',[['#calculator','Inputs & results'],['#calculator/procedures','Checking procedures'],['#calculator/validation','Reference validation'],['#calculator/benchmark','Silicon benchmark'],['#calculator/comparisons','Comparison snapshots']]],
    ['physics','5','Physics & equations',Object.entries(RAMAN_DOCS.physics).map(([key,d])=>['#physics/'+key,d.title])],
    ['references','6','References & downloads',[['#references','Sources'],['#references/downloads','Python downloads']]]
  ];
  $('#navigation').innerHTML='<a class="nav-link" href="#home">Home</a>'+groups.map(([key,n,title,children])=>{
    const expanded=S.openGroups.has(key);
    return '<div class="nav-group"><div class="nav-row"><a class="nav-link" href="#'+key+'">'+title+'</a><button class="nav-chevron" data-nav-toggle="'+key+'" aria-label="'+(expanded?'Collapse ':'Expand ')+title+'" aria-expanded="'+expanded+'">›</button></div><div class="nav-children" '+(expanded?'':'hidden')+'>'+children.map(([href,label])=>'<a href="'+href+'">'+esc(label)+'</a>').join('')+'</div></div>';
  }).join('');
  markNavigation();
}
function markNavigation(){const hash=location.hash||'#home';$$('#navigation a').forEach(a=>{if(a.getAttribute('href')===hash)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});}
function setMenu(open){
  if(matchMedia('(max-width:850px)').matches){document.body.classList.toggle('mobile-nav-open',open);$('#menu-toggle').setAttribute('aria-expanded',String(open));}
  else{document.body.classList.toggle('desktop-nav-hidden',!open);$('#menu-toggle').setAttribute('aria-expanded',String(open));}
}
$('#menu-toggle').addEventListener('click',()=>{const mobile=matchMedia('(max-width:850px)').matches;setMenu(mobile?!document.body.classList.contains('mobile-nav-open'):document.body.classList.contains('desktop-nav-hidden'));});
$('#nav-backdrop').addEventListener('click',()=>setMenu(false));
document.addEventListener('keydown',event=>{if(event.key==='Escape'){setMenu(false);$('#site-search').value='';$('#search-results').hidden=true;}});
$('#cancel-operation').addEventListener('click',()=>engine.stop());
$('.skip-link').addEventListener('click',event=>{event.preventDefault();$('#main-content').focus();$('#main-content').scrollIntoView({block:'start'});});
$('#dismiss-download').addEventListener('click',()=>{$('#download-ready').hidden=true;if(preparedDownloadUrl)URL.revokeObjectURL(preparedDownloadUrl);preparedDownloadUrl=null;});

function renderHome(){
  return '<section class="hero"><div><span class="kicker">A COMPUTATIONAL RAMAN WORKSPACE</span><h1>From crystal orientation<br>to Raman intensity.</h1><p class="lead">Rotate the full tensor. Define the actual optical states. Follow the mathematics from a complex amplitude to a reproducible polar plot.</p><div class="button-row"><a class="button" href="#calculator">Open the calculator <span aria-hidden="true">→</span></a><a class="text-link" href="#tutorial">Explore the Python code ↗</a></div></div><div class="hero-visual"><img src="./polar_Ag_xx.svg" alt="Calculated Ag(xx) polar intensity on the reference (211) frame"><div class="figure-label"><strong>A calculated reference, not an illustration</strong>CaNb₂O₆ · (211) reference XY frame<br>Separate Ag(xx) contribution</div></div></section>'+
    '<div class="stats-row"><div class="stat"><strong>21</strong><span>Point-group templates<br>with explicit Cartesian axes</span></div><div class="stat"><strong>9</strong><span>Optical profiles<br>selected independently of material</span></div><div class="stat"><strong>22</strong><span>Python code cells<br>fully displayed and explained</span></div></div>'+
    renderOpticalGuide()+
    '<div class="section-heading"><h2>A connected path through the program</h2></div><div class="grid-3 paths"><a class="path-card" href="#introduction"><span class="path-number">UNDERSTAND THE TOOLS</span><h3>Know what each input means.</h3><p>Tensor models, optical methods, crystal axes, coefficients and output conventions.</p><span class="path-action">Read the introduction →</span></a><a class="path-card" href="#tutorial"><span class="path-number">INSPECT THE CODE</span><h3>Follow every Python cell.</h3><p>Read the exact source beside its purpose, call sequence, mathematics and checks.</p><span class="path-action">Open the tutorial →</span></a><a class="path-card" href="#physics"><span class="path-number">CHECK THE PHYSICS</span><h3>Trace the model to its sources.</h3><p>Jones vectors, full tensor rotations, coherent interference and independent validation.</p><span class="path-action">Explore the equations →</span></a></div>'+
    '<div class="section-heading"><h2>One calculation, visible at every stage</h2></div><div class="card"><div class="workflow-strip"><div class="workflow-item"><strong>Crystal frame</strong><p>Lattice → surface normal → T</p></div><div class="workflow-item"><strong>Rotated tensor</strong><p>Full 3×3 response in the measurement frame</p></div><div class="workflow-item"><strong>Optical amplitude</strong><p>Incident state → tensor → detected state</p></div><div class="workflow-item"><strong>Intensity & export</strong><p>Polar plots, mathematical steps and raw data</p></div></div>'+math(String.raw`R_{lab}=T^TR_cT,\qquad \mathcal A=e_s^\dagger R_\perp E_i,\qquad I=|\mathcal A|^2`)+'</div>'+
    '<div class="feature-kernel"><div><h3>Start with an inspectable reference.</h3><p>The initial (211) example keeps Ag(xx), Ag(yy) and Ag(zz) separate. Every figure has matching raw data and calculated equations.</p></div><a class="button secondary" href="#calculator">Calculate the reference</a></div>'+
    '<p class="small-note" style="margin-top:22px">Ideal transverse plane-wave model. Coefficients and noncubic lattice ratios are declared inputs; the program does not infer them from a material name.</p>';
}
function renderIntroduction(){
  return heading('INTRODUCTION','An inspectable Raman calculation.','This program connects crystallographic orientation, symmetry-allowed Raman tensors and explicit Jones optical states in one calculation. It is designed for checking derivations, comparing configurations and exporting reproducible scientific results.')+
    '<div class="card"><h2>What the program is built to do</h2><ol class="instruction-list"><li>Define the full crystal tensor and its complex coefficients for a selected phonon branch.</li><li>Construct a proper measurement frame from lattice parameters, surface indices and an in-plane direction.</li><li>Rotate the tensor, propagate the selected optical states and calculate the detected amplitude.</li><li>Show its mathematical expansion, independent checking points and separate Ag contribution plots.</li><li>Export the declared inputs, raw intensities, source equations and scientific figures together.</li></ol>'+sourceLinks(['complex','cubic'])+'</div>'+
    '<div class="section-heading"><h2>Tool-by-tool guide</h2></div><div class="tutorial-grid">'+Object.entries(RAMAN_DOCS.tools).map(([key,d],i)=>'<a class="cell-card plain-card" href="#introduction/'+key+'"><div><h3>'+esc(d.title)+'</h3><p>'+esc(d.lead)+'</p></div></a>').join('')+'</div>'+
    '<div class="callout warning"><strong>Consistency depends on the physical inputs.</strong>The same tensor, frame, coefficients and actual Jones states must give the same intensity. A different optical chain or lattice metric can correctly produce a different polar plot.</div>';
}
function opticsTable(){
  const rows=[
    ['VV','Parallel linear input and detection; both scan theta.','CUBIC_VV'],
    ['VH','Crossed linear input and detection; both scan theta.','CUBIC_VH'],
    ['VV and VH together','Both channels use one coefficient set and common geometry.','LINEAR_PAIR'],
    ['Circular input / direct linear analyzer','Circular input; a directly rotating linear detector, with its explicit zero.','CIRCULAR_LINEAR'],
    ['sigma+alpha reference','Circular input; the declared elliptical detection-state scan.','CUBIC_SIGMA'],
    ['Input QWP / tensor / return QWP / analyzer','Original optical chain, with sample detection state determined by the return QWP.','QWP'],
    ['Same fixed circular basis label','A fixed circular input/output basis-label channel.','CIRCULAR_SAME'],
    ['Opposite fixed circular basis label','A fixed channel with the opposite outgoing circular basis label.','CIRCULAR_OPPOSITE'],
    ['Custom direct Jones','User-supplied input and detector weight/phase angles.','DIRECT_JONES']
  ];return table(['Profile','Physical definition','Internal key'],rows.map(r=>[esc(r[0]),esc(r[1]),'<code>'+r[2]+'</code>']),'optics-table');
}
function table(head,rows,extra=''){return '<div class="table-wrap '+extra+'"><table><thead><tr>'+head.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';}
function renderDocument(doc,category,key){
  const sections=doc.sections.map((section,index)=>{
    const id='doc-'+index;
    return '<section class="card doc-section" id="'+id+'"><h2>'+esc(section.title)+'</h2>'+
      (section.paragraphs||[]).map(x=>'<p>'+rich(x)+'</p>').join('')+
      (section.equations||[]).map(math).join('')+
      (section.steps?'<ol class="instruction-list">'+section.steps.map(x=>'<li>'+rich(x)+'</li>').join('')+'</ol>':'')+
      (section.table?table(section.table.head,section.table.rows.map(row=>row.map(rich))):'')+
      (section.opticsTable?opticsTable():'')+
      (section.opticalGuide?renderOpticalGuide():'')+
      (section.procedureCatalog?renderProcedureRows(S.catalog.validation_procedures,true):'')+
      (section.note?'<div class="callout warning">'+rich(section.note)+'</div>':'')+sourceLinks(section.sources)+'</section>';
  }).join('');
  const items=Object.entries(category==='introduction'?RAMAN_DOCS.tools:RAMAN_DOCS.physics);
  const current=items.findIndex(([id])=>id===key);
  return heading(category==='introduction'?'INTRODUCTION':'PHYSICS & EQUATIONS',doc.title,doc.lead)+
    '<div class="doc-layout"><div class="doc-main">'+sections+
    '<div class="prev-next">'+(current>0?'<a href="#'+category+'/'+items[current-1][0]+'">← '+esc(items[current-1][1].title)+'</a>':'<span></span>')+(current<items.length-1?'<a href="#'+category+'/'+items[current+1][0]+'">'+esc(items[current+1][1].title)+' →</a>':'<a href="#calculator">Open calculator →</a>')+'</div></div><aside class="on-this-page"><strong>On this page</strong>'+doc.sections.map((section,index)=>'<a href="#'+category+'/'+key+'" data-scroll="doc-'+index+'">'+esc(section.title)+'</a>').join('')+'<hr><a href="#calculator">Open calculator ↗</a></aside></div>';
}
function renderPhysics(){return heading('PHYSICS & EQUATIONS','The mathematics behind the result.','Follow the physical assumptions and matrix derivations that connect a crystal tensor to a detected intensity. Each topic links to the primary references used by the implementation.')+
  '<div class="card">'+math(String.raw`\chi\longrightarrow R_c\longrightarrow T^TR_cT\longrightarrow e_s^\dagger R_\perp E_i\longrightarrow|\mathcal A|^2`)+'<p class="small-note">The calculator’s Mathematical steps tab specializes this same sequence to the current inputs, including all rotated matrix entries and complex conjugates.</p></div>'+
  '<div class="tutorial-grid">'+Object.entries(RAMAN_DOCS.physics).map(([key,d],i)=>'<a class="cell-card plain-card" href="#physics/'+key+'"><div><h3>'+esc(d.title)+'</h3><p>'+esc(d.lead)+'</p></div></a>').join('')+'</div>';
}
function codeBox(source,start=1,label='Python source'){
  const lines=source.replace(/\n$/,'').split('\n');
  return '<div class="code-box"><div class="code-header"><span>'+esc(label)+' · lines '+start+'–'+(start+lines.length-1)+'</span><button data-copy-code>Copy code</button></div><div class="code-surface"><div class="line-numbers" aria-hidden="true">'+lines.map((_,i)=>start+i).join('<br>')+'</div><pre><code class="language-python">'+esc(source.replace(/\n$/,''))+'</code></pre></div></div>';
}
function renderTutorial(number){
  if(!number)return heading('PYTHON TUTORIAL','Read the program, cell by cell.','All 22 source cells are displayed exactly as they appear in version 2. Each logical block explains what is called, what runs next, why it is written that way and how to check it.')+
    '<div class="callout"><strong>A source-linked walkthrough.</strong>The cell source, line numbers, downloadable notebook and browser scientific functions are generated from the same Python edition. Notebook widget callbacks are explained separately from the reusable calculation engine.</div>'+
    '<div class="tutorial-grid">'+S.cells.map(c=>'<a class="cell-card" href="#tutorial/cell/'+c.number+'"><span class="cell-number">'+String(c.number).padStart(2,'0')+'</span><div><h3>'+esc(c.title)+'</h3><p>'+c.lines+' source lines · '+S.tutorial.find(x=>x.cell===c.number).blocks.length+' explained blocks</p></div></a>').join('')+'</div>';
  const c=S.cells.find(x=>x.number===number),d=S.tutorial.find(x=>x.cell===number);if(!c||!d)return notFound();
  const sourceLines=c.source.split('\n');
  return heading('PYTHON TUTORIAL / CELL '+number,c.title,d.overview,'<div class="button-row"><button class="button secondary small" data-download-cell="'+number+'">Download cell .py</button><button class="button secondary small" data-copy-cell="'+number+'">Copy full cell</button></div>')+
    '<div class="tutorial-meta"><span class="tag">Code cell '+number+' of 22</span><span class="tag">'+c.lines+' source lines</span><span class="tag">'+d.blocks.length+' explained blocks</span><span class="tag success">Version 2 source</span></div>'+
    '<div class="card" style="margin-top:22px"><h2>Execution sequence</h2><ol class="workflow-list">'+d.workflow.map(x=>'<li>'+rich(x)+'</li>').join('')+'</ol></div>'+
    '<details class="full-source"><summary>Show the complete Cell '+number+' source</summary>'+codeBox(c.source,1,'Complete Cell '+number)+'<p class="small-note" style="padding:12px">Cell SHA-256: '+esc(c.sha256)+'</p></details>'+
    '<div class="section-heading"><h2>Code walkthrough</h2></div><div class="content-section-tools"><button class="icon-button" data-expand-walkthrough>Expand all blocks</button><button class="icon-button" data-collapse-walkthrough>Collapse all blocks</button><button class="icon-button" data-print>Print this page</button></div>'+
    d.blocks.map((block,i)=>'<details class="walkthrough-block" '+(i===0?'open':'')+'><summary>'+esc(block.title)+'<span class="tag">Lines '+block.start_line+'–'+block.end_line+'</span></summary><div class="walkthrough-body"><p>'+rich(block.explanation)+'</p><p class="why-label">Why this is written</p><p>'+rich(block.why)+'</p><div class="callout"><strong>Checking point</strong>'+rich(block.check)+'</div>'+codeBox(sourceLines.slice(block.start_line-1,block.end_line).join('\n'),block.start_line,'Cell '+number+' · '+block.title)+'</div></details>').join('')+
    (d.pitfalls.length?'<div class="card" style="margin-top:25px"><h2>Conventions and things to check</h2><ul class="compact-list">'+d.pitfalls.map(x=>'<li>'+rich(x)+'</li>').join('')+'</ul></div>':'')+
    '<div class="prev-next">'+(number>1?'<a href="#tutorial/cell/'+(number-1)+'">← Cell '+(number-1)+': '+esc(S.cells[number-2].title)+'</a>':'<a href="#tutorial">← All cells</a>')+(number<22?'<a href="#tutorial/cell/'+(number+1)+'">Cell '+(number+1)+': '+esc(S.cells[number].title)+' →</a>':'<a href="#calculator">Open calculator →</a>')+'</div>';
}

function renderReferences(downloadOnly=false){
  const downloads=[
    ['IPYNB','Current Python notebook','Version 2 · all 22 code cells and notebook controls','ROTATION_RAMAN_TENSOR_CALCULATION.ipynb'],
    ['ZIP','All Python programs','Version 2 notebook, scientific engine, browser adapter, stylesheet and original references','All_Python_Programs.zip'],
    ['PY','Complete Python cell source','Matching version 2 source for an IPython/Jupyter kernel','ROTATION_RAMAN_TENSOR_CALCULATION.py'],
    ['PY','Reusable scientific engine','The same scientific functions without notebook-only rich-display imports','raman_engine.py'],
    ['PY','Browser JSON adapter','Validated input/output adapter used by this website','web_bridge.py'],
    ['IPYNB','QWP source reference','Unmodified uploaded notebook · source of the checking procedures','Dr_Kumar_Version_2.ipynb'],
    ['MD','Optical methods: physics and equations','Nine profiles, exact state definitions, equality conditions and references','Optical_Methods_Guide.md'],
    ['STYLE','Scientific plot style','The supplied sci.mplstyle, embedded in the Python program','sci.mplstyle'],
    ['TXT','Python requirements','Packages for the notebook environment','requirements.txt']
  ];
  const downloadHtml='<section class="card doc-section" id="downloads"><div class="card-header"><div><h2>Python programs & supporting files</h2><p>The current notebook is the recommended Python entry point.</p></div><span class="tag success">Version 2</span></div>'+downloads.map(([type,title,desc,file])=>'<div class="download-item"><span class="download-icon">'+type+'</span><div><h3>'+title+'</h3><p>'+desc+'</p></div><a class="button secondary small" href="./downloads/'+file+'" download>Download ↓</a></div>').join('')+
    '<p class="small-note">Original optical implementation sources are preserved in the references folder of the program archive.</p></section>';
  const refs='<section class="card"><h2>Primary references & implementation sources</h2>'+RAMAN_DOCS.references.map(r=>'<article class="reference-item" id="ref-'+r.id+'"><div class="reference-number">['+r.number+']</div><div><h3>'+esc(r.title)+'</h3><p>'+esc(r.authors)+'<br>'+esc(r.publication)+'</p><a href="'+esc(r.url)+'" target="_blank" rel="noopener noreferrer">'+esc(r.url)+' ↗</a>'+(r.extra?'<div class="source-link-row">'+r.extra.map(([name,url])=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(name)+' ↗</a>').join('')+'</div>':'')+'<p style="margin-top:12px">'+esc(r.role)+'</p></div></article>').join('')+'</section>';
  return heading('REFERENCES & DOWNLOADS',downloadOnly?'The complete Python programs.':'Sources you can inspect.','Primary references, source notebooks and matching program downloads are kept together so the equations and implementation can be checked.')+
    (downloadOnly?downloadHtml+refs:refs+downloadHtml)+
    '<div class="card"><h2>Source correspondence</h2><p class="small-note">Every tutorial cell shows its own source fingerprint. Scientific functions are extracted from that same notebook; only notebook display imports are omitted in the worker. The web adapter validates JSON and formats outputs without introducing an alternative intensity law.</p><p class="small-note">Notebook code SHA-256</p><code style="display:block;word-break:break-all">'+esc(S.sourceHash)+'</code><div class="callout"><strong>Version 2 maintenance</strong>Inactive circular-rule fields no longer block noncircular notebook calculations. Ambiguous equation-number labels now identify the cubic reference Section 2.2. Tensor rotations and intensity formulas are preserved.</div></div>';
}

function optionList(options,selected){return options.map(([value,label])=>'<option value="'+esc(value)+'" '+(value===selected?'selected':'')+'>'+esc(label)+'</option>').join('');}
function selectField(id,label,options,value,help='',disabled=false){return '<div class="field"><label for="'+id+'">'+label+'</label><select id="'+id+'" '+(disabled?'disabled':'')+'>'+optionList(options,value)+'</select>'+(help?'<span class="field-help">'+help+'</span>':'')+'</div>';}
function numberField(id,label,value,opts={}){return '<div class="field"><label for="'+id+'">'+label+'</label><input id="'+id+'" type="number" value="'+esc(value)+'" step="'+(opts.integer?'1':'any')+'" '+(opts.min!==undefined?'min="'+opts.min+'"':'')+' '+(opts.disabled?'disabled':'')+'></div>';}
function textField(id,label,value,help=''){return '<div class="field"><label for="'+id+'">'+label+'</label><input id="'+id+'" type="text" value="'+esc(value)+'">'+(help?'<span class="field-help">'+help+'</span>':'')+'</div>';}
function checkbox(id,label,value){return '<label class="checkbox-row" for="'+id+'"><input id="'+id+'" type="checkbox" '+(value?'checked':'')+'><span>'+label+'</span></label>';}
function section(number,title,html,open=false,full=false){return '<details data-section-key="'+esc(number)+'" class="form-section '+(full?'full-width':'')+'" '+(open?'open':'')+'><summary>'+title+'</summary><div class="form-section-body">'+html+'</div></details>';}
function definitions(form=S.form){
  if(form.tensor_model==='QWP_SOURCE_2D')return {};
  if(form.point_group==='CUSTOM')return {Custom:{irrep:'Custom',parameters:[],tensors:[],partners:1,note:'User-supplied Cartesian tensor.'}};
  return form.material==='GENERAL'?S.catalog.groups[form.point_group].definitions:S.catalog.materials[form.material].definitions;
}
function ensureValues(form){
  const defs=definitions(form);form.mode_values=form.mode_values||{};
  for(const [name,def] of Object.entries(defs)){
    if(!form.mode_values[name])form.mode_values[name]={};
    for(const p of def.parameters)if(!form.mode_values[name][p])form.mode_values[name][p]=clone(S.catalog.parameter_defaults[p]);
  }
}
function opticalPreview(form){
  const a='\\alpha',theta='\\theta';let ei='',es='';
  if(['CUBIC_VV','CUBIC_VH','LINEAR_PAIR'].includes(form.optics)){
    ei='(\\cos\\theta,\\sin\\theta)^T';
    es=form.optics==='CUBIC_VV'?ei:form.optics==='CUBIC_VH'?'(-\\sin\\theta,\\cos\\theta)^T':'e_s^{VV}=e_i,\\quad e_s^{VH}=(-\\sin\\theta,\\cos\\theta)^T';
  }else if(form.optics==='CUBIC_SIGMA'){ei='\\sigma_+';es='(\\cos(\\pi/4+\\alpha),\\ i\\sin(\\pi/4+\\alpha))^T';}
  else if(form.optics==='QWP'){ei='Qe_X';es='(Q^T)^\\dagger(-\\sin\\alpha,\\cos\\alpha)^T';}
  else if(form.optics==='CIRCULAR_LINEAR'){ei='\\sigma_{s_{in}}';es='(\\cos(\\alpha+\\alpha_0),\\sin(\\alpha+\\alpha_0))^T';}
  else if(form.optics==='CIRCULAR_SAME'){ei='\\sigma_{s_{in}}';es='\\sigma_{s_{in}}';}
  else if(form.optics==='CIRCULAR_OPPOSITE'){ei='\\sigma_{s_{in}}';es='\\sigma_{-s_{in}}';}
  else{ei='(\\cos\\theta_i,e^{i\\beta_i}\\sin\\theta_i)^T';es='(\\cos(\\theta_{s0}+\\alpha),e^{i\\beta_s}\\sin(\\theta_{s0}+\\alpha))^T';}
  return '<div class="tensor-preview">'+math('E_i='+ei)+math('e_s='+es)+'</div><p class="field-help">States are defined at the sample. The calculated derivation shows their exact matrices and active angle values.</p>';
}
function renderControls(){
  const f=S.form,source=f.tensor_model==='QWP_SOURCE_2D';ensureValues(f);
  let start=selectField('tensor-model','Tensor model',[['CRYSTAL_3D','General crystal: full 3D tensor'],['QWP_SOURCE_2D','Original effective 2D optical reference']],f.tensor_model)+
    selectField('optical-method','Optical method',Object.entries(S.catalog.profiles),f.optics,'Choose actual optical states independently of material.',source)+
    opticalSelectionSummary(f)+
    selectField('example','Example',Object.entries(S.catalog.examples).map(([key,x])=>[key,x.label]),S.selectedExample)+
    '<button type="button" class="button secondary small" data-load-example>Load selected example</button><hr>'+
    textField('case-label','Case label',f.case_label)+
    '<div class="field"><label for="input-note">Input note</label><textarea id="input-note" rows="2">'+esc(f.input_note||'')+'</textarea></div>';
  let material='';
  if(source){
    const p=f.source_parameters||{a:1,A:.4,delta_deg:60,phi_deg:60};
    material='<p class="small-note">This effective source has no crystal-orientation input.</p><div class="field-row two">'+numberField('source-a','Real source a',p.a)+numberField('source-A','Real source A',p.A)+'</div><div class="field-row two">'+numberField('source-delta','Delta (degree)',p.delta_deg)+numberField('source-phi','Phi (degree)',p.phi_deg)+'</div>';
  }else{
    const info=S.catalog.materials[f.material],groupInfo=S.catalog.groups[f.point_group];
    material=selectField('material','Material',Object.entries(S.catalog.materials).map(([key,m])=>[key,m.label]),f.material)+
      selectField('point-group','Point group',Object.entries(S.catalog.groups).map(([key,g])=>[key,key+' / '+g.symbol]).concat([['CUSTOM','Custom Cartesian 3×3 tensor']]),f.point_group,'The material preset fixes its stated point group.',f.material!=='GENERAL')+
      '<p class="small-note">'+esc(info.note)+'</p>'+(groupInfo?'<p class="small-note"><strong>Axes:</strong> '+esc(groupInfo.axes)+'</p>':'')+
      '<span class="field-label">Modes / phonon branches</span><div class="modes-grid">'+Object.keys(definitions(f)).map(name=>'<label class="checkbox-row"><input type="checkbox" data-mode-select="'+esc(name)+'" '+(f.modes.includes(name)?'checked':'')+'><span>'+esc(name)+'</span></label>').join('')+'</div>';
    if(f.point_group==='D2h'&&Object.values(definitions(f)).some(x=>x.irrep==='Ag'))material+=selectField('ag-relation','D2h Ag relation',[['free','Independent a, b, c'],['equal','a = b = c'],['ab','a = b'],['bc','b = c'],['ac','a = c']],S.relation,'Copies magnitude and phase; this is an optional input constraint.');
    if(f.point_group==='CUSTOM')material+='<div class="field"><label for="custom-tensor">Custom 3×3 tensor JSON</label><textarea id="custom-tensor" rows="5">'+esc(JSON.stringify(f.custom_tensor||[['1','0','0'],['0','0.8','0'],['0','0','0.6']],null,2))+'</textarea><span class="field-help">Numeric entries or strings such as \"1+0.2j\". Source code is never evaluated.</span></div>';
    else material+=f.modes.map(name=>{
      const def=definitions(f)[name];if(!def)return '';
      return '<div class="mode-card"><h4>'+esc(name)+' <span class="tag">'+def.partners+' tensor partner'+(def.partners===1?'':'s')+'</span></h4><div class="tensor-preview">'+def.tensors.map(math).join('')+'</div>'+
      def.parameters.map(symbol=>{const value=f.mode_values[name][symbol],locked=def.irrep==='Ag'&&f.point_group==='D2h'&&((S.relation==='equal'&&symbol!=='a')||(S.relation==='ab'&&symbol==='b')||(S.relation==='bc'&&symbol==='c')||(S.relation==='ac'&&symbol==='c'));return '<div class="coefficient-row"><span class="coefficient-symbol">'+esc(symbol)+'</span><div class="field"><label>Magnitude</label><input aria-label="'+esc(name+' '+symbol+' magnitude')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="magnitude" type="number" min="0" step="any" value="'+esc(value.magnitude)+'" '+(locked?'disabled':'')+'></div><div class="field"><label>Phase (degree)</label><input aria-label="'+esc(name+' '+symbol+' phase in degrees')+'" data-coefficient="'+esc(symbol)+'" data-mode="'+esc(name)+'" data-part="phase" type="number" step="any" value="'+esc(value.phase)+'" '+(locked?'disabled':'')+'></div></div>';}).join('')+'</div>';
    }).join('');
  }
  let orientation='';
  if(!source){
    const manual=f.orientation==='matrix',surface=Object.entries(S.catalog.surfaces).find(([,v])=>v[0].every((x,i)=>x===f.hkl[i]))?.[0]||'Custom hkl';
    orientation=selectField('orientation-kind','Orientation input',[['hkl','Surface hkl and in-plane uvw'],['matrix','Manual proper frame T']],f.orientation||'hkl');
    if(manual)orientation+='<div class="field"><label for="manual-frame">Frame columns X, Y, Z in crystal coordinates</label><textarea id="manual-frame" rows="5">'+esc(JSON.stringify(f.T_manual||[[1,0,0],[0,1,0],[0,0,1]],null,2))+'</textarea><span class="field-help">Real, orthonormal, determinant +1. hkl, uvw and psi are inactive.</span></div>';
    else orientation+=selectField('surface','Surface preset',Object.keys(S.catalog.surfaces).concat('Custom hkl').map(x=>[x,x]),surface)+
      '<div class="field-row">'+['h','k','l'].map((name,i)=>numberField('index-'+name,name,f.hkl[i],{integer:true})).join('')+'</div>'+
      checkbox('automatic-x','Automatic in-plane X reference',f.uvw===null)+
      '<div class="field-row">'+['u','v','w'].map((name,i)=>numberField('index-'+name,name,f.uvw?.[i]??[0,1,-1][i],{integer:true,disabled:f.uvw===null})).join('')+'</div>'+
      '<p class="field-help">Zone condition: h·u + k·v + l·w = 0.</p>'+
      selectField('normal-side','Normal side',[['1','+ reciprocal normal'],['-1','− reciprocal normal']],String(f.normal_sign))+
      numberField('frame-angle','Frame angle psi (degree)',f.azimuth_deg);
    orientation+='<hr><span class="field-label">Lattice lengths · one common unit</span><div class="field-row">'+['a₀','b₀','c₀'].map((name,i)=>numberField('lattice-'+i,name,f.lattice[i],{min:0})).join('')+'</div><span class="field-label">Lattice angles · degrees</span><div class="field-row">'+['alpha','beta','gamma'].map((name,i)=>numberField('lattice-'+(i+3),name,f.lattice[i+3])).join('')+'</div><p class="field-help">Illustrative ratios must be replaced for a physical tilted noncubic surface.</p>';
  }
  const p=f.paper_parameters||{},dj=f.direct_jones||{theta_i_deg:45,beta_i_deg:90,theta_s0_deg:45,beta_s_deg:0};
  let optics=opticalPreview(f);
  if(f.optics==='DIRECT_JONES')optics+='<div class="field-row two">'+numberField('direct-theta_i_deg','Input thetaᵢ (degree)',dj.theta_i_deg)+numberField('direct-beta_i_deg','Input betaᵢ (degree)',dj.beta_i_deg)+numberField('direct-theta_s0_deg','Detector thetaₛ₀ (degree)',dj.theta_s0_deg)+numberField('direct-beta_s_deg','Detector betaₛ (degree)',dj.beta_s_deg)+'</div>';
  if(['CUBIC_VV','CUBIC_VH','LINEAR_PAIR'].includes(f.optics))optics+=numberField('theta-zero','Linear scan zero (degree)',p.theta0_deg||0);
  if(f.optics==='CIRCULAR_LINEAR')optics+=numberField('analyzer-zero','Direct analyzer zero (degree)',p.analyzer_zero_deg??45);
  if(f.optics.startsWith('CIRCULAR_'))optics+=selectField('circular-spin','Input circular basis label',[['1','s_in = +1: (1, +i)/√2'],['-1','s_in = −1: (1, −i)/√2']],String(p.s_in||1))+
    '<hr><span class="field-label">Conditional rule · separate from intensity</span>'+
    selectField('circular-order','Cyclic order N',[2,3,4,6].map(x=>[String(x),String(x)]),String(p.N||2))+
    numberField('circular-ell','Incident orbital charge (rule only)',p.ell_i||0,{integer:true})+
    textField('circular-charges','Phonon charges (comma separated)',(p.m_ph||[0]).join(', '))+
    textField('circular-absorption','Absorption charge (optional)',p.absorption_delta_m??'')+
    checkbox('circular-scope','Declare the thin-2D / electronic assumptions for the separate rule check',p.thin_2d_assumptions)+
    '<p class="field-help">Curves remain ell = 0 plane-wave calculations. The rule never masks or rescales them.</p>';
  const display=selectField('angular-grid','Angular grid',[['721','0.5 degree · 721 samples'],['361','1 degree · 361 samples'],['3601','0.1 degree · 3601 samples']],String(f.plot_points||721))+
    checkbox('normalize','Use one common maximum per mode, including components and paired VV/VH',f.normalize)+
    checkbox('cartesian','Also generate Cartesian plots',f.cartesian_plots)+
    checkbox('show-frame','Show the 3D measurement frame',f.show_geometry!==false)+
    '<p class="field-help">Raw CSV is unnormalized. Mathematical steps and continuous extrema are always calculated.</p>';
  return '<div class="calc-controls"><fieldset id="calculator-form" '+(S.busy?'disabled':'')+'>'+
    section('01','Model, optics & example',start,true,true)+
    section('02',source?'Source tensor parameters':'Material & tensor coefficients',material,true)+
    (!source?section('03','Orientation & lattice',orientation,false):'')+
    section('04','Jones states & optical controls',optics,false)+
    section('05','Display settings',display,false)+
    '<div class="calc-action-bar"><button class="button" type="button" data-calculate '+(S.busy?'disabled':'')+'>Calculate rotation + Raman <span aria-hidden="true">→</span></button></div></fieldset>'+
    '<p class="small-note">The first calculation starts scientific Python in your browser. Navigation stays responsive while equations are calculated.</p></div>';
}

function valueNumber(id,fallback,integer=false){
  const element=$('#'+id);if(!element)return fallback;
  if(element.value.trim()===''||!Number.isFinite(element.valueAsNumber))throw new Error('Enter a finite number for '+(element.getAttribute('aria-label')||$('label[for="'+id+'"]')?.textContent||id)+'.');
  const number=element.valueAsNumber;if(integer&&!Number.isInteger(number))throw new Error(id+' must be an integer.');return number;
}
function readForm(){
  const f=clone(S.form);f.tensor_model=$('#tensor-model')?.value||f.tensor_model;f.optics=$('#optical-method')?.value||f.optics;
  f.case_label=$('#case-label')?.value||'Raman tensor calculation';f.input_note=$('#input-note')?.value||'';
  f.plot_points=Number($('#angular-grid')?.value||f.plot_points);f.normalize=!!$('#normalize')?.checked;f.cartesian_plots=!!$('#cartesian')?.checked;f.show_geometry=!!$('#show-frame')?.checked;
  if(f.tensor_model==='QWP_SOURCE_2D'){
    f.source_parameters={a:valueNumber('source-a',1),A:valueNumber('source-A',.4),delta_deg:valueNumber('source-delta',60),phi_deg:valueNumber('source-phi',60)};return f;
  }
  f.material=$('#material')?.value||f.material;f.point_group=$('#point-group')?.value||f.point_group;
  f.modes=$$('[data-mode-select]:checked').map(x=>x.dataset.modeSelect);
  $$('[data-coefficient]').forEach(input=>{const mode=input.dataset.mode,symbol=input.dataset.coefficient;f.mode_values[mode]=f.mode_values[mode]||{};f.mode_values[mode][symbol]=f.mode_values[mode][symbol]||{};if(input.value===''||!Number.isFinite(input.valueAsNumber))throw new Error('Enter a finite coefficient value for '+mode+' '+symbol+'.');f.mode_values[mode][symbol][input.dataset.part]=input.valueAsNumber;});
  f.orientation=$('#orientation-kind')?.value||'hkl';f.lattice=f.lattice.map((x,i)=>valueNumber('lattice-'+i,x));
  if(f.orientation==='matrix')f.T_manual=JSON.parse($('#manual-frame').value);
  else{
    f.hkl=['h','k','l'].map((id,i)=>valueNumber('index-'+id,f.hkl[i],true));
    f.uvw=$('#automatic-x')?.checked?null:['u','v','w'].map((id,i)=>valueNumber('index-'+id,f.uvw?.[i]??[0,1,-1][i],true));
    f.normal_sign=Number($('#normal-side')?.value||f.normal_sign);f.azimuth_deg=valueNumber('frame-angle',f.azimuth_deg||0);
  }
  if(f.point_group==='CUSTOM')f.custom_tensor=JSON.parse($('#custom-tensor').value);
  f.paper_parameters=f.paper_parameters||{};
  if(['CUBIC_VV','CUBIC_VH','LINEAR_PAIR'].includes(f.optics))f.paper_parameters.theta0_deg=valueNumber('theta-zero',0);
  if(f.optics==='CIRCULAR_LINEAR')f.paper_parameters.analyzer_zero_deg=valueNumber('analyzer-zero',45);
  if(f.optics.startsWith('CIRCULAR_')){
    Object.assign(f.paper_parameters,{s_in:Number($('#circular-spin').value),N:Number($('#circular-order').value),ell_i:valueNumber('circular-ell',0,true),
      m_ph:$('#circular-charges').value.split(',').filter(x=>x.trim()!=='').map(x=>{const n=Number(x);if(!Number.isFinite(n)||!Number.isInteger(n))throw new Error('Each phonon charge must be an integer.');return n;}),
      absorption_delta_m:$('#circular-absorption').value.trim()===''?null:Number($('#circular-absorption').value),
      thin_2d_assumptions:$('#circular-scope').checked});
  }
  if(f.optics==='DIRECT_JONES')f.direct_jones=Object.fromEntries(['theta_i_deg','beta_i_deg','theta_s0_deg','beta_s_deg'].map(k=>[k,valueNumber('direct-'+k,f.direct_jones?.[k])]));
  return f;
}
function applyRelation(form){
  if(form.point_group!=='D2h'||S.relation==='free')return;
  for(const [name,def] of Object.entries(definitions(form)))if(def.irrep==='Ag'){
    const v=form.mode_values[name];if(!v)continue;
    if(S.relation==='equal'){v.b=clone(v.a);v.c=clone(v.a);}
    if(S.relation==='ab')v.b=clone(v.a);
    if(S.relation==='bc')v.c=clone(v.b);
    if(S.relation==='ac')v.c=clone(v.a);
  }
}
function invalidate(){S.dirty=true;S.error=null;S.runtimeHasRun=false;updateStaleStatus();}
function updateStaleStatus(){
  const status=$('#calculation-status');if(status&&S.dirty)status.innerHTML='<strong>Inputs changed — calculate to update the result.</strong><p>Any previous figures describe the previous declared inputs. Current-result downloads are disabled.</p>';
  $$('[data-result-download],[data-add-comparison],[data-figure-export],[data-figure-svg]').forEach(button=>button.disabled=S.dirty||S.busy||(!S.runtimeHasRun&&(button.dataset.resultDownload==='zip'||button.hasAttribute('data-figure-export')||button.hasAttribute('data-add-comparison'))));
}
function replaceControls(){const node=$('.calc-controls');if(node){const opened=new Set($$('.form-section[open]',node).map(x=>x.dataset.sectionKey));node.outerHTML=renderControls();$$('.calc-controls .form-section').forEach(x=>x.open=opened.has(x.dataset.sectionKey));typeset($('.calc-controls'));}}
function readAndInvalidate(){try{S.form=readForm();applyRelation(S.form);}catch{/* Keep incomplete edits visible until calculate validates them. */}invalidate();}
function materialChange(material){
  const old=clone(S.form),info=S.catalog.materials[material];const group=material==='GENERAL'&&S.catalog.groups[old.point_group]?old.point_group:info.group;
  S.form={...old,material,point_group:group,lattice:material==='GENERAL'?(['trigonal','hexagonal'].includes(S.catalog.groups[group]?.system)?[1,1,1,90,90,120]:[1,1,1,90,90,90]):clone(info.lattice),case_label:material+' / selected surface and optical states',input_note:'Illustrative tensor coefficients and lattice ratios; replace with sample-specific inputs.'};
  S.form.modes=Object.keys(definitions(S.form));S.form.mode_values=material==='GENERAL'?{}:clone(info.defaults.mode_values);S.relation='free';ensureValues(S.form);invalidate();replaceControls();
}
function groupChange(group){
  S.form.point_group=group;const system=S.catalog.groups[group]?.system;
  S.form.lattice=['trigonal','hexagonal'].includes(system)?[1,1,1,90,90,120]:[1,1,1,90,90,90];
  S.form.modes=Object.keys(definitions(S.form));S.form.mode_values={};S.relation='free';ensureValues(S.form);invalidate();replaceControls();
}

function resultFigures(figures,frameOnly=false){
  return figures.map((figure,index)=>({figure,index})).filter(({figure})=>frameOnly?figure.name==='measurement_frame':figure.name!=='measurement_frame').map(({figure,index})=>
    '<figure class="result-figure"><figcaption><strong>'+esc(figure.name.replaceAll('_',' '))+'</strong><div class="figure-actions"><button data-figure-svg="'+index+'" '+(S.dirty?'disabled':'')+'>SVG ↓</button><button data-figure-export="'+index+'" data-extension="png" '+(!S.runtimeHasRun||S.dirty?'disabled':'')+'>PNG 600 dpi ↓</button><button data-figure-export="'+index+'" data-extension="pdf" '+(!S.runtimeHasRun||S.dirty?'disabled':'')+'>PDF ↓</button></div></figcaption><img src="'+figure.png+'" alt="'+esc(figure.name.replaceAll('_',' '))+'"></figure>').join('')||'<div class="empty-state"><p>No 3D frame applies to this optical-source model.</p></div>';
}
function derivationHtml(entries){
  const groups=[];for(const entry of entries){if(entry.kind==='section')groups.push({title:entry.value,entries:[]});else{if(!groups.length)groups.push({title:'Mathematical derivation',entries:[]});groups.at(-1).entries.push(entry);}}
  return '<div class="content-section-tools"><button class="icon-button" data-expand-math>Expand all steps</button><button class="icon-button" data-collapse-math>Collapse all steps</button></div>'+
    groups.map((group,i)=>'<details class="result-math-section" '+(i<3?'open':'')+'><summary>'+esc(group.title)+'</summary><div class="result-math-body">'+group.entries.map(entry=>entry.kind==='equation'?math(entry.value):'<p>'+rich(entry.value)+'</p>').join('')+'</div></details>').join('');
}
function renderValues(result){
  const rows=result.channels.map(c=>[esc(c.name),compact(c.summary.Imin),compact(c.summary.Imax),c.summary.alpha_max===null?'constant / zero':compact(c.summary.alpha_max)+'°']);
  const indices=Array.from({length:25},(_,i)=>Math.round(i*(result.angles.length-1)/24));
  return '<div class="card"><h3>Continuous extrema</h3>'+table(['Channel','Imin','Imax','Maximum angle'],rows)+'<p class="small-note" style="margin-top:15px">Extrema come from the harmonic equations. The values below are raw intensities, even when figures are normalized.</p></div>'+
    table(['Angle (degree)',...result.channels.map(x=>x.name)],indices.map(i=>[compact(result.angles[i]),...result.channels.map(x=>compact(x.points[i]))]))+
    '<p class="small-note" style="margin-top:12px">Preview: 15-degree intervals. Download CSV for every point on the selected grid.</p>';
}
function renderChecks(result){
  return '<div class="card"><h3>Independent current-result reconstructions</h3>'+table(['Channel','Direct error','Circular-basis error'],result.checks.map(x=>[esc(x.channel),compact(x.direct_error),compact(x.circular_error)]))+
    (result.frame?'<div class="chip-row" style="margin-top:18px"><span class="tag success">det(T) = '+compact(result.frame.determinant)+'</span><span class="tag">Orthogonality error '+compact(result.frame.orthogonality_error)+'</span></div>':'')+'</div>'+
    '<div class="card"><h3>Different detection-state scans</h3><p class="small-note">Projector distances at 0°, 45°, 90° and 135°. Zero identifies the same pure state up to global phase.</p>'+table(['Profiles','Distances','Same scan'],result.protocols.map(x=>[esc(x.first+' / '+x.second),x.projector_distances.map(compact).join(', '),x.same_states?'yes':'no']))+'</div>'+
    '<div class="card"><h3>Complete-mode interference audit</h3><p class="small-note">These complete tensors retain within-mode interference. Main Ag plots remain separate component powers.</p>'+table(['Mode','Maximum |cross term|','Independent error'],result.interference.map(x=>[esc(x.mode),compact(x.maximum_cross_term),compact(x.absolute_error)]))+'</div>'+
    '<div class="card"><h3>Actual state convention and Stokes checks</h3><pre class="result-json">'+esc(JSON.stringify(result.states,null,2))+'</pre></div>'+
    (result.circular?'<div class="card"><h3>Conditional circular-selection record</h3><pre class="result-json">'+esc(JSON.stringify(result.circular,null,2))+'</pre></div>':'')+
    '<div class="card"><h3>Model assumptions</h3><ul class="compact-list">'+result.assumptions.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'+sourceLinks(['complex','circular','cubic'])+'</div>';
}
function renderLatex(result){return '<div class="card"><h3>Symbolic intensity source</h3><p class="small-note">Before numerical coefficient substitution. The complete archive also contains the numerical and full-derivation documents.</p><textarea class="latex-source" readonly aria-label="Symbolic intensity LaTeX source">'+esc(result.latex.symbolic)+'</textarea><div class="button-row" style="margin-top:16px"><button class="button secondary small" data-copy-latex>Copy LaTeX</button><button class="button secondary small" data-result-download="symbolic" '+(S.dirty?'disabled':'')+'>Download symbolic .tex</button><button class="button secondary small" data-result-download="full" '+(S.dirty?'disabled':'')+'>Download full derivation .tex</button></div></div>';}
function renderProcedureRows(rows,catalogOnly=false){
  return rows.map((r,index)=>{
    const state=catalogOnly?'not run':r.status,style=state==='passed'?'success':state==='failed'?'failed':'neutral';
    let evidence='';
    if(!catalogOnly&&r.evidence){
      const e=r.evidence;
      if(e.kind==='symbolic')evidence='<p class="procedure-evidence"><strong>Measured evidence:</strong> '+e.identities+' symbolic residual'+(e.identities===1?'':'s')+': '+esc(e.residuals.join(', '))+'</p>';
      else if(e.kind==='numerical')evidence=table(['Maximum absolute residual','Allowed absolute error','Comparisons','Finite'],[[compact(e.maximum_absolute_residual),compact(e.allowed_absolute_error),String(e.comparisons),String(e.all_finite)]])+'<p class="small-note">Scale '+compact(e.scale)+' · absolute tolerance '+compact(e.absolute_tolerance)+' · relative tolerance '+compact(e.relative_tolerance)+'</p>';
      else if(e.kind==='negative-controls')evidence='<p class="procedure-evidence"><strong>Deliberately wrong controls rejected:</strong> '+e.rejected.filter(Boolean).length+' / '+e.rejected.length+'</p>';
      else evidence='<p class="procedure-evidence">'+esc(e.reason||JSON.stringify(e))+'</p>';
      evidence+='<details class="raw-evidence"><summary>Full evidence record</summary><pre class="result-json">'+esc(JSON.stringify(e,null,2))+'</pre></details>';
    }
    return '<details class="checking-procedure" data-procedure-id="'+esc(r.id)+'" '+(index===0?'open':'')+'><summary><span class="procedure-id">'+esc(r.id)+'</span><strong>'+esc(r.title)+'</strong><span class="tag '+style+'">'+esc(state)+'</span></summary><div class="procedure-body"><p class="small-note">'+esc(r.source)+' · '+esc(r.scope)+'</p><h4>Purpose</h4><p>'+esc(r.purpose)+'</p><h4>Checking procedure</h4><p>'+esc(r.procedure)+'</p>'+(r.expected_latex?'<h4>Expected mathematical result</h4>'+math(r.expected_latex):'')+(r.assumption?'<p class="inline-notice">'+esc(r.assumption)+'</p>':'')+evidence+'</div></details>';
  }).join('');
}
function renderCheckingReport(report,reference=false){
  if(!report)return '<div class="empty-state"><p>Calculate a case to generate its checking procedures.</p></div>';
  return '<div class="card"><div class="card-header"><div><h3>'+esc(report.kind)+'</h3><p>'+esc(report.case||'Reference identities from the uploaded notebook')+'</p></div><span class="tag '+(report.status==='passed'?'success':'failed')+'">'+esc(report.status)+' · '+report.passed+'/'+report.total+'</span></div><p class="small-note">'+esc(report.scope)+'</p>'+(!reference&&(S.dirty||!S.runtimeHasRun)?'<div class="callout warning">'+(S.dirty?'This evidence belongs to the previous calculated inputs. Calculate to update it.':'Stored result. Calculate to regenerate this evidence in the current browser session.')+'</div>':'')+(report.not_applicable?'<p class="small-note">'+report.not_applicable+' source/model-specific check'+(report.not_applicable===1?' is':'s are')+' explicitly not applicable.</p>':'')+(report.notation_note?'<div class="callout warning">'+esc(report.notation_note)+'</div>':'')+'<div class="button-row">'+(reference?'<button class="button secondary small" data-download-validation '+(S.busy?'disabled':'')+'>Download reference validation JSON</button>':'<button class="button secondary small" data-result-download="checking" '+(S.dirty?'disabled':'')+'>Download checking report JSON</button>')+'<a class="text-link" href="#introduction/checking-procedures">Read the validation guide →</a></div>'+sourceLinks(['kumar-v2','sympy-validation'])+'</div>'+renderProcedureRows(report.rows);
}
function renderValidation(){
  return '<div class="card"><h3>Run the full model-validation suite</h3><p class="small-note">Checks source algebra, symmetry, complex rotations, independent reference equations, all implemented point groups and numerical edge cases. It also executes 25 procedures based on QWP source reference, including explicitly identified extensions, and records their purpose, expected identity and measured residual.</p><div class="button-row"><button class="button secondary" data-run-validation '+(S.busy?'disabled':'')+'>Run full validation</button><a class="text-link" href="#introduction/checking-procedures">Procedures and purposes →</a></div>'+
    (S.validation?'<div style="margin-top:22px"><span class="tag '+(S.validation.status==='passed'?'success':'failed')+'">'+esc(S.validation.status)+'</span>'+S.validation.checks.map(x=>'<div class="check-item">'+esc(x)+'</div>').join('')+'</div>':'<p class="small-note" style="margin-top:16px">The reference procedures have not run in this browser session. The catalog describes expectations, not test results.</p>')+'</div>'+
    (S.validation?.optical_reference?renderCheckingReport(S.validation.optical_reference,true):'<details class="card"><summary>Inspect the 25 procedures before running</summary>'+renderProcedureRows(S.catalog.validation_procedures,true)+'</details>');
}
function renderComparisons(){
  const channels=[...new Set(S.comparisons.flatMap(x=>x.channels))];
  return '<div class="card"><div class="card-header"><div><h3>Comparison snapshots</h3><p>Keep up to six calculated cases with their original physical inputs.</p></div><button class="button secondary small" data-clear-comparisons '+(!S.comparisons.length||S.busy?'disabled':'')+'>Clear</button></div>'+
    '<div class="snapshot-list">'+S.comparisons.map((x,i)=>'<div><strong>'+(i+1)+'. '+esc(x.label)+'</strong><small>'+esc(x.optics)+'</small></div>').join('')+'</div>'+
    (channels.length?selectField('comparison-channel','Common channel',channels.map(x=>[x,x]),S.comparisonChannel||channels[0])+checkbox('comparison-normalized','Use common per-mode normalization',true)+'<button class="button secondary small" data-render-comparison '+(S.busy?'disabled':'')+'>Render comparison</button>':'<p class="small-note">Calculate a case, then use Save comparison above the result.</p>')+'</div>'+
    (S.comparison?'<figure class="result-figure"><figcaption><strong>Frozen input snapshots</strong><button class="text-button" data-download-comparison>SVG ↓</button></figcaption><img src="'+S.comparison.png+'" alt="Polar overlay of saved calculation snapshots"></figure>':'');
}
function renderBenchmark(){
  return '<div class="card"><h3>Silicon · six surfaces · three protocols</h3><p class="small-note">The benchmark locks Si T2g, the reference frame and one common d for all 18 cases.</p><div class="field-row two">'+numberField('benchmark-d','Shared |d|',S.benchmarkMagnitude??1,{min:0})+selectField('benchmark-grid','Angular grid',[['721','0.5 degree'],['361','1 degree'],['3601','0.1 degree']],'721')+'</div><div class="button-row"><button class="button" data-run-benchmark '+(S.busy?'disabled':'')+'>Calculate all 18 cases</button><button class="button secondary" data-export-benchmark '+(!S.benchmark||S.busy?'disabled':'')+'>Download OriginLab ZIP</button></div></div>'+
    (S.benchmark?'<div class="card"><span class="tag success">18 cases checked</span>'+S.benchmark.checks.map(x=>'<div class="check-item">'+esc(x)+'</div>').join('')+'<hr><div class="field-row two">'+selectField('benchmark-surface','Inspect surface',Array.from({length:6},(_,k)=>[String(k),'(5'+k+'0)']),'3')+selectField('benchmark-protocol','Inspect protocol',[['VV','VV'],['VH','VH'],['SIGMA','sigma+alpha reference']],'VV')+'</div><button class="button secondary small" data-inspect-benchmark>Load selected case into calculator</button></div><figure class="result-figure wide"><figcaption><strong>Si T2g · common I/|d|² scale</strong></figcaption><img src="'+S.benchmark.figure.png+'" alt="Calculated six-surface VV, VH and sigma+alpha silicon benchmark"></figure>':'<div class="empty-state"><p>Calculate to compare (500), (510), (520), (530), (540) and (550).</p><a class="text-link" href="#introduction/benchmark">Read the benchmark guide →</a></div>');
}
function resultBody(){
  if(S.tab==='benchmark')return renderBenchmark();
  if(S.tab==='comparisons')return renderComparisons();
  if(S.tab==='validation')return renderValidation();
  const result=S.result;if(!result)return '<div class="empty-state"><h3>Your calculation will appear here.</h3><p>Choose the physical inputs, then calculate the rotation and Raman response.</p></div>';
  if(S.tab==='math')return '<div class="callout"><strong>'+result.equation_count+' calculated equations</strong>These expressions are generated from the current matrices and optical states. '+sourceLinks(['complex','cubic','optical-source'])+'</div>'+derivationHtml(result.equations);
  if(S.tab==='values')return renderValues(result);
  if(S.tab==='frame')return resultFigures(result.figures,true)+(result.frame?'<div class="card"><h3>Measurement frame</h3>'+math('T='+result.frame.tensor_frame)+table(['Quantity','Value'],[['det(T)',compact(result.frame.determinant)],['Orthogonality error',compact(result.frame.orthogonality_error)]])+'</div>':'');
  if(S.tab==='checks')return renderChecks(result);
  if(S.tab==='procedures')return renderCheckingReport(result.checking_report);
  if(S.tab==='latex')return renderLatex(result);
  const agNote=result.channels.some(x=>x.kind==='Cartesian contribution of one Ag phonon')?'<div class="callout"><strong>Separate Ag Cartesian contributions</strong>No Ag component-power sum is plotted. Complete coherent modes are retained separately in the audit export.</div>':'';
  return agNote+resultFigures(result.figures);
}
function renderCalculator(section){
  const r=S.result;
  return heading('CALCULATOR','Rotate. Calculate. Inspect.','Set the crystal and optical inputs, then follow the calculated response. The same Python engine supplies the figures, equations and downloads.')+
    '<div class="calc-layout">'+renderControls()+'<section class="calc-results" id="calculator-results"><div class="calc-status" id="calculation-status">'+(S.dirty?'<strong>Inputs changed — calculate to update the result.</strong><p>Previous figures describe previous inputs. Current-result downloads are disabled.</p>':r?'<strong>'+esc(r.case)+'</strong><p>'+esc(S.catalog.profiles[r.configuration.optics]||r.configuration.optics)+' · '+r.channels.length+' displayed channels · '+r.equation_count+' equations'+(!S.runtimeHasRun?' · saved reference example':'')+'</p>':'<strong>Ready for your inputs.</strong><p>Start a calculation to generate all outputs.</p>')+'</div>'+
    (S.error?'<div class="engine-error"><strong>Calculation could not complete.</strong><p>'+esc(S.error.split('\n').filter(Boolean).at(-1))+'</p><details><summary>Show diagnostic details</summary><pre>'+esc(S.error)+'</pre></details></div>':'')+
    '<div class="results-toolbar"><div class="button-row"><button class="button small" data-result-download="zip" '+(!S.runtimeHasRun||S.dirty||S.busy?'disabled':'')+'>Download complete result ↓</button><button class="button secondary small" data-result-download="csv" '+(!r||S.dirty||S.busy?'disabled':'')+'>Raw CSV ↓</button><button class="button secondary small" data-add-comparison '+(!S.runtimeHasRun||S.dirty||S.busy?'disabled':'')+'>Save comparison</button></div></div>'+
    '<div class="result-tabs" role="tablist" aria-label="Calculation outputs">'+[['plots','Polar plots'],['math','Mathematical steps'],['values','Intensity values'],['frame','3D frame'],['procedures','Checking procedures'],['checks','Protocol checks'],['latex','LaTeX'],['validation','Validation'],['comparisons','Comparisons'],['benchmark','Silicon benchmark']].map(([key,label])=>'<button class="result-tab" role="tab" data-result-tab="'+key+'" aria-selected="'+(S.tab===key)+'" tabindex="'+(S.tab===key?'0':'-1')+'">'+label+'</button>').join('')+'</div><div class="result-pane" role="tabpanel" id="result-pane">'+resultBody()+'</div></section></div>';
}
function syncCalculatorTabRoute(){
  if(!location.hash.startsWith('#calculator'))return;
  const suffix=['procedures','validation','benchmark','comparisons'].includes(S.tab)?'/'+S.tab:'';
  history.replaceState(null,'','#calculator'+suffix);markNavigation();
}

async function runOperation(type,payload,title,onSuccess){
  if(S.busy)return;
  S.busy=true;S.error=null;$('#operation-status').hidden=false;$('#operation-title').textContent=title;$('#operation-message').textContent='Preparing the scientific engine…';
  const form=$('#calculator-form');if(form)form.disabled=true;$$('[data-result-download],[data-run-validation],[data-run-benchmark],[data-export-benchmark],[data-add-comparison]').forEach(x=>x.disabled=true);
  try{const result=await engine.request(type,payload);await onSuccess(result);}
  catch(error){S.error=String(error.message||error);toast(S.error.split('\n').filter(Boolean).at(-1));}
  finally{S.busy=false;$('#operation-status').hidden=true;if((location.hash||'#home').startsWith('#calculator')){syncCalculatorTabRoute();renderRoute(false);}if(engine.ready)setEngineStatus('Python ready','');}
}
function notFound(){return heading('WORKSPACE','Page not found.','Choose a section from the navigation to continue.')+'<a class="button" href="#home">Return home</a>';}
function renderRoute(scroll=true){
  if(!S.catalog)return;
  const parts=(location.hash||'#home').slice(1).split('/').filter(Boolean),page=parts[0]||'home';let html,breadcrumb;
  if(page==='home'){html=renderHome();breadcrumb='Home';}
  else if(page==='introduction'){S.openGroups.add(page);const doc=RAMAN_DOCS.tools[parts[1]];html=doc?renderDocument(doc,page,parts[1]):renderIntroduction();breadcrumb='Introduction'+(doc?' / '+doc.title:'');}
  else if(page==='tutorial'){S.openGroups.add(page);const number=parts[1]==='cell'?Number(parts[2]):null;html=renderTutorial(number);breadcrumb='Python tutorial'+(number?' / Cell '+number:'');}
  else if(page==='physics'){S.openGroups.add(page);const doc=RAMAN_DOCS.physics[parts[1]];html=doc?renderDocument(doc,page,parts[1]):renderPhysics();breadcrumb='Physics & equations'+(doc?' / '+doc.title:'');}
  else if(page==='calculator'){S.openGroups.add(page);if(scroll&&['benchmark','comparisons','procedures','validation'].includes(parts[1]))S.tab=parts[1];html=renderCalculator(parts[1]);breadcrumb='Calculator';}
  else if(page==='references'){S.openGroups.add(page);html=renderReferences(parts[1]==='downloads');breadcrumb='References & downloads';}
  else{html=notFound();breadcrumb='Not found';}
  const previousScroll=window.scrollY;$('#main-content').innerHTML=html;$('#breadcrumbs').textContent='Workspace / '+breadcrumb;renderNavigation();typeset($('#main-content'));updateStaleStatus();
  if(scroll){window.scrollTo({top:0,behavior:'instant'});if(matchMedia('(max-width:850px)').matches)setMenu(false);}else window.scrollTo({top:previousScroll,behavior:'instant'});
  document.title=(page==='home'?'':breadcrumb+' · ')+'Rotation Raman Tensor Calculation';
}
window.addEventListener('hashchange',()=>renderRoute());

document.addEventListener('input',event=>{
  const target=event.target;
  const structural=['example','tensor-model','material','point-group','surface','ag-relation','automatic-x','optical-method','orientation-kind'];
  if(target.closest('#calculator-form')&&!structural.includes(target.id)&&!target.hasAttribute('data-mode-select'))readAndInvalidate();
  if(target.id==='site-search')search(target.value);
});
document.addEventListener('change',event=>{
  const target=event.target;if(!target.closest('#calculator-form'))return;
  if(target.id==='example'){S.selectedExample=target.value;return;}
  if(target.id==='tensor-model'){
    const next=target.value;
    if(next==='QWP_SOURCE_2D'){S.lastCrystal=clone(S.form);S.form=clone(S.catalog.examples.QWP_2D.config);}
    else S.form=clone(S.lastCrystal||S.catalog.examples.SLIDE.config);
    invalidate();replaceControls();return;
  }
  if(target.id==='material'){materialChange(target.value);return;}
  if(target.id==='point-group'){groupChange(target.value);return;}
  if(target.id==='surface'){
    try{S.form=readForm();}catch{}
    if(target.value!=='Custom hkl'){S.form.hkl=clone(S.catalog.surfaces[target.value][0]);S.form.uvw=clone(S.catalog.surfaces[target.value][1]);}
    invalidate();replaceControls();return;
  }
  if(target.id==='ag-relation'){S.relation=target.value;try{S.form=readForm();}catch{}applyRelation(S.form);invalidate();replaceControls();return;}
  if(target.id==='automatic-x'){try{S.form=readForm();}catch{}if(!target.checked&&S.form.uvw===null)S.form.uvw=[1,0,0];invalidate();replaceControls();return;}
  if(target.id==='optical-method'){S.form.optics=target.value;invalidate();replaceControls();return;}
  if(target.id==='orientation-kind'){S.form.orientation=target.value;invalidate();replaceControls();return;}
  if(target.hasAttribute('data-mode-select')){try{S.form=readForm();}catch{}invalidate();replaceControls();return;}
  if(target.hasAttribute('data-coefficient')&&S.relation!=='free'){try{S.form=readForm();applyRelation(S.form);}catch{}replaceControls();}
});

document.addEventListener('click',async event=>{
  const button=event.target.closest('button,a');if(!button)return;
  if(button.dataset.navToggle){const key=button.dataset.navToggle;if(S.openGroups.has(key))S.openGroups.delete(key);else S.openGroups.add(key);renderNavigation();return;}
  if(button.dataset.scroll){event.preventDefault();$('#'+button.dataset.scroll)?.scrollIntoView({behavior:'smooth',block:'start'});return;}
  if(button.hasAttribute('data-copy-code')){await copyText($('code',button.closest('.code-box')).textContent);return;}
  if(button.dataset.copyCell){await copyText(S.cells[Number(button.dataset.copyCell)-1].source);return;}
  if(button.dataset.downloadCell){const c=S.cells[Number(button.dataset.downloadCell)-1];download(c.source,'Cell_'+c.number+'_'+c.tag+'.py');return;}
  if(button.hasAttribute('data-expand-walkthrough')){$$('.walkthrough-block').forEach(x=>x.open=true);return;}
  if(button.hasAttribute('data-collapse-walkthrough')){$$('.walkthrough-block').forEach(x=>x.open=false);return;}
  if(button.hasAttribute('data-expand-math')){$$('.result-math-section').forEach(x=>x.open=true);return;}
  if(button.hasAttribute('data-collapse-math')){$$('.result-math-section').forEach(x=>x.open=false);return;}
  if(button.hasAttribute('data-print')){$$('.walkthrough-block,.full-source').forEach(x=>x.open=true);window.print();return;}
  if(button.hasAttribute('data-load-example')){S.form=clone(S.catalog.examples[S.selectedExample].config);S.relation='free';if(S.form.tensor_model==='CRYSTAL_3D')S.lastCrystal=clone(S.form);invalidate();renderRoute(false);toast('Example loaded. Review inputs, then calculate.');return;}
  if(button.dataset.resultTab){S.tab=button.dataset.resultTab;syncCalculatorTabRoute();$$('.result-tab').forEach(x=>{const active=x.dataset.resultTab===S.tab;x.setAttribute('aria-selected',String(active));x.tabIndex=active?0:-1;});$('#result-pane').innerHTML=resultBody();typeset($('#result-pane'));return;}
  if(button.hasAttribute('data-calculate')){
    try{S.form=readForm();applyRelation(S.form);}catch(error){S.error=error.message;renderRoute(false);return;}
    await runOperation('calculate',S.form,'Calculating rotation + Raman',result=>{S.result=result;S.dirty=false;S.runtimeHasRun=true;S.tab='plots';toast(result.channels.length+' channels and '+result.equation_count+' equations calculated.');});return;
  }
  if(button.dataset.resultDownload){
    if(S.dirty||!S.result)return;
    if(button.dataset.resultDownload==='zip'){await runOperation('export',{},'Preparing the complete result archive',buffer=>download(buffer,'Rotation_Raman_Result.zip','application/zip'));return;}
    if(button.dataset.resultDownload==='csv')download(S.result.csv,'intensity_raw.csv','text/csv');
    if(button.dataset.resultDownload==='symbolic')download(S.result.latex.symbolic,'intensity_symbolic.tex');
    if(button.dataset.resultDownload==='full')download(S.result.latex.full,'calculation_full.tex');
    if(button.dataset.resultDownload==='checking')download(JSON.stringify(S.result.checking_report,null,2),'checking_procedures.json','application/json');
    return;
  }
  if(button.hasAttribute('data-copy-latex')&&S.result){await copyText(S.result.latex.symbolic);return;}
  if(button.dataset.figureSvg!==undefined&&S.result&&!S.dirty){const figure=S.result.figures[Number(button.dataset.figureSvg)];download(figure.svg,figure.name+'.svg','image/svg+xml');return;}
  if(button.dataset.figureExport!==undefined&&S.result&&!S.dirty){const index=Number(button.dataset.figureExport),extension=button.dataset.extension;await runOperation('figure',{index,extension},'Exporting a scientific figure',buffer=>download(buffer,S.result.figures[index].name+'.'+extension,extension==='png'?'image/png':'application/pdf'));return;}
  if(button.hasAttribute('data-run-validation')){await runOperation('validate',{},'Running the full validation suite',result=>{S.validation=result;S.tab='validation';toast(result.status==='passed'?'Model and source-reference procedures passed.':'Validation contains failed or unresolved checks.');});return;}
  if(button.hasAttribute('data-download-validation')&&S.validation){download(JSON.stringify(S.validation,null,2),'optical_reference_validation.json','application/json');return;}
  if(button.hasAttribute('data-add-comparison')&&!S.dirty){await runOperation('addComparison',{},'Saving a calculation snapshot',result=>{S.comparisons=result;S.tab='comparisons';});return;}
  if(button.hasAttribute('data-clear-comparisons')){await runOperation('clearComparisons',{},'Clearing comparison snapshots',()=>{S.comparisons=[];S.comparison=null;S.tab='comparisons';});return;}
  if(button.hasAttribute('data-render-comparison')){S.comparisonChannel=$('#comparison-channel').value;const normalized=$('#comparison-normalized').checked;await runOperation('compare',{channel:S.comparisonChannel,normalized},'Comparing frozen input snapshots',result=>{S.comparison=result;S.tab='comparisons';});return;}
  if(button.hasAttribute('data-download-comparison')&&S.comparison){download(S.comparison.svg,'comparison.svg','image/svg+xml');return;}
  if(button.hasAttribute('data-run-benchmark')){
    let magnitude;try{magnitude=valueNumber('benchmark-d',1);}catch(error){toast(error.message);return;}const points=Number($('#benchmark-grid').value);S.benchmarkMagnitude=magnitude;
    await runOperation('benchmark',{magnitude,points},'Calculating the 18-case silicon benchmark',result=>{S.benchmark=result;S.tab='benchmark';});return;
  }
  if(button.hasAttribute('data-export-benchmark')){await runOperation('exportBenchmark',{},'Exporting the silicon benchmark',buffer=>download(buffer,'Silicon_Fig1_OriginLab.zip','application/zip'));return;}
  if(button.hasAttribute('data-inspect-benchmark')){
    const protocol=$('#benchmark-protocol').value,k=Number($('#benchmark-surface').value),entry=S.benchmark.cases.find(x=>x.protocol===protocol&&x.k===k);S.form=clone(entry.config);S.relation='free';invalidate();
    await runOperation('calculate',S.form,'Inspecting the selected silicon case',result=>{S.result=result;S.dirty=false;S.runtimeHasRun=true;S.tab='math';});return;
  }
});
document.addEventListener('keydown',event=>{
  if(!event.target.matches('.result-tab')||!['ArrowLeft','ArrowRight'].includes(event.key))return;
  event.preventDefault();const tabs=$$('.result-tab'),i=tabs.indexOf(event.target),next=tabs[(i+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length];next.click();next.focus();
});
function search(query){
  const node=$('#search-results');query=query.trim().toLowerCase();if(!query){node.hidden=true;return;}
  const words=query.split(/\s+/),matches=S.searchIndex.filter(x=>words.every(w=>x.text.includes(w))).slice(0,9);
  node.innerHTML=matches.length?matches.map(x=>'<a href="'+x.href+'">'+esc(x.label)+'<small>'+esc(x.category)+'</small></a>').join(''):'<p class="small-note" style="padding:12px;color:#becbd3">No matches. Try orientation, QWP, tensor or Cell 12.</p>';node.hidden=false;
}
async function initialize(){
  try{
    const [catalog,cells,tutorial,example]=await Promise.all(['catalog','cells','tutorial','reference-example'].map(async name=>{const response=await fetch('./data/'+name+'.json',{cache:'no-cache'});if(!response.ok)throw new Error('Unable to load '+name+'.');return response.json();}));
    S.catalog=catalog;S.cells=cells.cells;S.sourceHash=cells.source_sha256;S.tutorial=tutorial;S.form=clone(catalog.examples.SLIDE.config);S.result=example;S.lastCrystal=clone(S.form);
    S.searchIndex=[...Object.entries(RAMAN_DOCS.tools).map(([key,d])=>({href:'#introduction/'+key,label:d.title,category:'Introduction',text:(d.title+' '+d.lead+' '+JSON.stringify(d.sections)).toLowerCase()})),
      ...S.cells.map(c=>({href:'#tutorial/cell/'+c.number,label:'Cell '+c.number+' · '+c.title,category:'Python tutorial',text:('cell '+c.number+' cell'+c.number+' '+c.title+' '+c.source).toLowerCase()})),
      ...Object.entries(RAMAN_DOCS.physics).map(([key,d])=>({href:'#physics/'+key,label:d.title,category:'Physics & equations',text:(d.title+' '+d.lead+' '+JSON.stringify(d.sections)).toLowerCase()}))];
    renderNavigation();setMenu(!matchMedia('(max-width:850px)').matches);renderRoute();
  }catch(error){$('#main-content').innerHTML='<div class="card"><h1>Workspace could not load.</h1><p>'+esc(error.message)+'</p><button class="button" onclick="location.reload()">Reload workspace</button></div>';}
}
initialize();
