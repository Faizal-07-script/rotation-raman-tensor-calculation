/* Documentation from the notebook catalog; material curves use the Python engine. */
'use strict';

function opticalGuideDetails(key){
  const g=S.catalog.optical_guide[key];
  return '<div class="guide-profile" data-guide-profile="'+esc(key)+'">'+
    '<div class="card-header"><div><span class="tag">'+esc(g.family)+'</span><h3>'+esc(g.label)+'</h3></div></div>'+
    '<div class="optical-chain" aria-label="Optical path"><div><small>Preparation</small><strong>'+esc(g.preparation)+'</strong></div><span aria-hidden="true">→</span><div><small>Raman response</small>'+math(String.raw`R_\perp=PT^TR_cTP^T`)+'</div><span aria-hidden="true">→</span><div><small>Return path</small><strong>'+esc(g.return_path)+'</strong></div><span aria-hidden="true">→</span><div><small>Detection</small><strong>'+esc(g.detection)+'</strong></div></div>'+
    '<p><strong>What changes during the scan:</strong> '+esc(g.scan)+'.</p>'+
    '<div class="guide-equations">'+g.states.map(math).join('')+(['CIRCULAR_LINEAR','CUBIC_SIGMA','QWP'].includes(key)?math(String.raw`p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i`):'')+math(g.amplitude)+math(g.intensity)+'</div>'+
    '<p><strong>Use for:</strong> '+esc(g.use_for)+'</p><p><strong>Equality to check:</strong> '+esc(g.invariant)+'</p>'+
    '<div class="callout warning"><strong>Physical interpretation</strong>'+esc(g.caution)+'</div>'+
    '<p class="small-note"><strong>Source scope:</strong> '+esc(g.provenance)+'</p>'+sourceLinks(g.sources)+'</div>';
}

function opticalSelectionSummary(form){
  const g=S.catalog.optical_guide?.[form.optics];if(!g)return '';
  return '<div class="optical-choice-note" data-selected-optics="'+esc(form.optics)+'"><strong>'+esc(g.family)+'</strong><p>'+esc(g.scan)+'. '+esc(g.detection)+'.</p><p>'+esc(g.use_for)+'</p><a href="#introduction/optical-comparison">Compare states, physics and references →</a></div>';
}

function renderOpticalGuide(){
  const catalog=S.catalog.optical_guide;if(!catalog)return '';
  const selected=S.guideProfile||'CUBIC_SIGMA';
  const demo=S.catalog.optical_example;
  const targets=[
    ['Parallel / crossed linear experiment','VV, VH, or VV and VH together','Both linear states scan theta; one shared coefficient set.'],
    ['Cubic paper Fig. 1(a), (b), (c)','VV, VH, elliptical sigma+alpha reference','Use its measurement frame, coefficients and effective states; Fig. 1(c) uses Eq. (11), beta=beta\u2032=90 degrees.'],
    ['Declared slide-frame component reference','Elliptical sigma+alpha reference','Also match the reference XY axes, lattice metric, normal sign and separate Ag components.'],
    ['Uploaded QWP calculation','Input QWP / tensor / return QWP / analyzer','Match both QWPs, return-path convention and the analyzer zero.'],
    ['An actual measured helicity experiment','The profile matching calibrated sample states','A material name does not identify the optics. Check the plates, beam directions, axes and detected states first.']
  ];
  return '<section class="optical-guide" id="optical-guide"><div class="section-heading"><div><span class="kicker">OPTICAL PROFILES & PHYSICAL REFERENCE</span><h2>Why does changing the method change the polar plot?</h2></div></div>'+
    '<div class="card"><p class="page-lead">Every choice uses one Raman amplitude law. The menu specifies which light enters, which state is detected, and what is rotated.</p>'+
    math(String.raw`e_s=B^\dagger e_{an},\qquad\mathcal A=e_{an}^\dagger B R_\perp E_i=e_s^\dagger R_\perp E_i,\qquad I=|\mathcal A|^2`)+
    '<p>The same material and surface can give different curves when the preparation, detector, relative phase or scan changes. A change of basis with the same physical states must preserve the intensity.</p>'+
    '<div class="optical-families"><article><h3>Linear input</h3><p><strong>VV · VH · paired VV/VH</strong></p><p>Incident and detected linear states rotate together. The scan can contain second and fourth intensity harmonics.</p></article><article><h3>Circular input</h3><p><strong>Linear · elliptical · return-QWP · fixed circular detection</strong></p><p>The effective detector changes between these choices. A fixed circular channel has no angle scan when the sample stays fixed.</p></article><article><h3>Custom effective states</h3><p><strong>Direct Jones parameters</strong></p><p>The input is fixed and the detector component angle scans at fixed relative phase. Matching preset states gives matching intensity.</p></article></div>'+sourceLinks(['jones','complex','cubic','circular'])+'</div>'+
    '<details class="card guide-detail"><summary><strong>All nine profiles side by side</strong></summary>'+table(['Menu choice','Scanned quantity','Detection at the sample'],Object.values(catalog).map(g=>[esc(g.label),esc(g.scan),esc(g.detection)]))+'</details>'+
    '<div class="card"><h3>Which choice should be the reference?</h3>'+table(['Comparison target','Optical choice','Inputs that must agree'],targets.map(row=>row.map(rich)))+
    '<div class="callout"><strong>Experimental reference</strong>Use a calibrated optical path to choose the profile for your data. Paper reproduction uses the paper\u2019s explicit states. A successful software check establishes algebraic consistency; it does not calibrate a microscope.</div>'+sourceLinks(['complex','cubic','kumar-original'])+'</div>'+
    '<div class="card"><label class="field-label" for="guide-profile">Inspect any of the nine choices</label><select id="guide-profile" class="guide-select">'+Object.values(catalog).map(g=>'<option value="'+esc(g.key)+'" '+(g.key===selected?'selected':'')+'>'+esc(g.label)+'</option>').join('')+'</select><p class="small-note">This documentation selector does not change calculator inputs or result plots.</p><div id="guide-profile-details">'+opticalGuideDetails(selected)+'</div></div>'+
    '<div class="card"><h3>The decisive difference: detector phase and interference</h3><p>For a fixed circular input, define output amplitudes in the same fixed XY circular basis:</p>'+
    math(String.raw`\sigma_\pm=(1,\pm i)^T/\sqrt2,\qquad p=\sigma_+^\dagger R_\perp\sigma_+,\quad q=\sigma_-^\dagger R_\perp\sigma_+`)+
    math(String.raw`p=\tfrac12[r_{xx}+r_{yy}+i(r_{xy}-r_{yx})],\quad q=\tfrac12[r_{xx}-r_{yy}+i(r_{xy}+r_{yx})]`)+
    table(['Detector at the sample','Amplitude','Intensity contribution carrying interference'],[
      ['Elliptical reference',math(String.raw`p\cos\alpha-q\sin\alpha`),math(String.raw`-2\operatorname{Re}(p q^*)\sin\alpha\cos\alpha`)],
      ['Return QWP, then linear analyzer',math(String.raw`p\cos\alpha+i q\sin\alpha\quad(\text{up to global phase})`),math(String.raw`+2\operatorname{Im}(p q^*)\sin\alpha\cos\alpha`)],
      ['Direct linear analyzer, t=alpha+alpha0',math(String.raw`(p e^{it}+q e^{-it})/\sqrt2`),math(String.raw`\operatorname{Re}(p q^*e^{2it})`)]])+
    '<p>The first two include the same diagonal terms '+rich('`|p|² cos²(alpha) + |q|² sin²(alpha)`')+'. The direct-linear scan has a constant diagonal term '+rich('`(|p|²+|q|²)/2`')+'. These equations are derived from the implemented Jones states. Agreement of the two circular endpoints does not force agreement at intermediate angles.</p><p><strong>A linear analyzer after a return QWP is a different sample detector from a bare linear analyzer.</strong> Its linear setting belongs to '+rich('`e_an`')+'; the scattering contraction uses '+rich('`e_s=B†e_an`')+'.</p>'+sourceLinks(['cubic','jones','kumar-original'])+'</div>'+
    '<div class="card"><h3>A calculated example with the tensor held fixed</h3><p>'+esc(demo.scope)+'</p>'+math(String.raw`R_{lab}=\operatorname{diag}(1,2,3),\quad P=\begin{pmatrix}1&0&0\\0&1&0\end{pmatrix},\quad PR_{lab}P^T=\operatorname{diag}(1,2)`)+ '<p class="small-note">This transverse example can be embedded in the full 3D tensor shown above. The general material calculation rotates all 3x3 entries before applying P.</p><figure class="guide-comparison"><img src="./optical_profile_comparison.svg" loading="lazy" alt="Engine-calculated polar plots for the same diagonal tensor with direct linear, elliptical and return-QWP detection"><figcaption>Common radial range 0\u20132.5. Each curve is calculated by optical_chain and the common Jones contraction. No alignment or separate normalization is applied.</figcaption></figure>'+
    table(['Analyzer / state angle','Direct linear','Elliptical reference','Return QWP'],demo.angles.map((a,i)=>[a+'\u00b0',...['CIRCULAR_LINEAR','CUBIC_SIGMA','QWP'].map(k=>compact(demo.profiles[k].values[i]))]))+
    '<p class="small-note">This example is a complete illustrative tensor. The main material plots continue to show separate Ag(xx), Ag(yy) and Ag(zz) contribution powers.</p></div>'+
    '<details class="card guide-detail"><summary><strong>Polarization trajectories and helicity conventions</strong></summary><p>With '+rich('`S1=|Ex|²\u2212|Ey|², S2=2 Re(Ex*Ey), S3=2 Im(Ex*Ey)`')+', the normalized effective detector follows these distinct trajectories:</p>'+
    table(['Detection scan','S1','S2','S3'],[['Direct linear','cos(2t)','sin(2t)','0'],['Elliptical reference','−sin(2alpha)','0','cos(2alpha)'],['Return QWP','0','−sin(2alpha)','cos(2alpha)']].map(r=>r.map(rich)))+
    math(String.raw`\mathbf k_i=-k_i\hat Z,\quad\mathbf k_s=+k_s\hat Z,\quad h_i=-S_3(E_i),\quad h_s=S_3(e_s)`)+
    '<p>The last signs use '+rich('`exp[i(k·r−omega t)]`')+' and the program\u2019s common fixed laboratory XY basis. For elliptical or linear states these h values are helicity expectations; definite circular eigenstates have h=±1. Same fixed circular labels therefore mean opposite propagation-relative helicity for these counterpropagating beams. A paper can name channels in beam-attached axes; reconcile its convention before comparing conserved/changing names.</p>'+sourceLinks(['jones','circular','cubic'])+'</details>'+
    '<details class="card guide-detail"><summary><strong>Which results must agree, and which may differ?</strong></summary>'+table(['Comparison','Required result'],[
      ['Standalone VV vs the VV member of paired VV/VH','Equal raw arrays for the same tensor, frame, zero angle and scan. The same holds for VH.'],
      ['Elliptical reference vs custom Jones (45,90,45,90 degrees)','Equal states and intensities at every angle.'],
      ['Circular input / linear detector vs custom Jones (45,90,alpha0,0 degrees)','Equal for sigma+ input and the same analyzer zero.'],
      ['Elliptical reference vs explicit source QWP','Circular endpoint powers agree at 0 and 90 degrees; intermediate states generally differ. Special tensor coefficients can conceal that difference.'],
      ['Fixed circular channels vs analyzer scans','Fixed channels are constants; they are not sample-rotation measurements.'],
      ['Different states accidentally giving the same curve','Possible for a particular tensor or incoherent partner sum. Equal curves alone do not prove equal experiments.']].map(r=>r.map(rich)))+
    math(String.raw`\Pi_i=E_iE_i^\dagger,\quad\Pi_s=e_se_s^\dagger,\qquad I=\operatorname{Tr}(\Pi_s R_\perp\Pi_i R_\perp^\dagger)`)+
    '<p>Identical normalized projectors and scan laws give identical raw intensities for any tensor. The Validation tab tests the guide identities for a general complex, nonsymmetric tensor, as well as special limits.</p><p><strong>Compare raw CSV values first.</strong> Figure normalization depends on the displayed channel family. Adding a paired channel can change the shared maximum without changing either raw curve. Match the normalization, angle zero and positive-angle convention when comparing figures.</p>'+math(String.raw`I_j^{plot}(\alpha)=I_j^{raw}(\alpha)/M_{\mathcal F},\quad M_{\mathcal F}=\max_{\alpha,\,j\in\mathcal F}I_j^{raw}(\alpha)`)+sourceLinks(['jones','complex'])+'</details>'+
    '<details class="card guide-detail"><summary><strong>What the circular-selection-rule reference establishes</strong></summary><p>The cited rule combines optical absorption, phonon emission and scattered-photon emission under its rotational-symmetry and electronic assumptions. With the stated outgoing-orbital assumption, its necessary condition is</p>'+math(String.raw`s_s-s_i-\ell_i=-m_{ph}+Np,\qquad p\in\mathbb Z`)+
    '<p>Spin labels and phonon charges must use the reference\u2019s conventions consistently. Satisfying this congruence does not supply a Raman tensor, its complex phases, or a quantitative vortex-intensity curve. In this program the optional rule check is separate from the plotted plane-wave intensities, which use '+rich('`ell=0`')+'. The absorption and phonon selection conditions must also be satisfied.</p>'+sourceLinks(['circular'])+'</details>'+
    '<details class="card guide-detail"><summary><strong>Keep optics, tensor symmetry and Ag presentation distinct</strong></summary><p>Changing material changes symmetry-allowed tensor entries and physical coefficients; it can also change the lattice metric. Changing the surface changes the rotation. Changing the optical profile changes the states or scan. None of these alone determines the other inputs.</p>'+
    math(String.raw`\mathcal A_{Ag}=\mathcal A_{xx}+\mathcal A_{yy}+\mathcal A_{zz},\quad I_{Ag}^{full}=|\mathcal A_{Ag}|^2,\qquad I_j=|\mathcal A_j|^2`)+
    '<p>Separate Ag component powers are retained in the main figures as requested. A measured complete single-phonon intensity can contain cross terms; inspect the complete-mode audit when making that comparison. Orthogonal unresolved phonon partners are a sum of complete-mode powers instead.</p>'+sourceLinks(['complex','cubic'])+'</details>'+
    '<div class="button-row"><a class="button secondary" href="./downloads/Optical_Methods_Guide.md" download>Download the mathematical guide</a><a class="text-link" href="#calculator">Open calculator →</a><a class="text-link" href="#references">Read full references →</a></div></section>';
}

document.addEventListener('change',event=>{
  if(event.target.id!=='guide-profile')return;
  S.guideProfile=event.target.value;
  $('#guide-profile-details').innerHTML=opticalGuideDetails(S.guideProfile);
  typeset($('#guide-profile-details'));
});
