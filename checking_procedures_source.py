"""Integrated into Cell 21: procedures, purposes and measured validation evidence."""

OPTICAL_REFERENCE_SOURCE = dict(
    filename="Dr_Kumar_Original.ipynb",
    sha256="661989475b7bd39b1ab57bc4d9d59285ccf903baa24b58a78017d841feba8ec7",
    date="2026-10-15", notebook_cells=38, code_cells=20,
    notation="R[out,in]: first index = detected circular label; second = incident label.",
    scope="The source is an effective complex 2x2 optical model. Its antisymmetric off-diagonal pair is not substituted for a D2h material tensor.",
)


def checking_procedure_catalog():
    """Describe the source checks before any test has run; no status is implied."""
    items = [
        ("K01","Circular-basis orthonormality","Cell 3",
         "Exclude incorrect normalization and missing complex conjugation.",
         "Form the Gram matrix of the two circular vectors.",
         r"U_\sigma^\dagger U_\sigma=I_2"),
        ("K02","Explicit quarter-wave-plate matrix","Cell 4",
         "Detect an axis-angle or retardance sign error before scattering.",
         "Compare the implemented plate with the matrix printed in the source.",
         r"Q=\frac12\begin{pmatrix}1+i&-1+i\\-1+i&1+i\end{pmatrix}"),
        ("K03","Lossless and symmetric plate","Cell 4",
         "Check norm preservation by this ideal plate and its symmetry in the adopted basis.",
         "Compute Q dagger Q and Q transpose. This is not a unitarity requirement on the Raman tensor.",
         r"Q^\dagger Q=I_2,\qquad Q^T=Q"),
        ("K04","Incident circular state","Cell 5",
         "Confirm the selected plate actually prepares the intended incident state.",
         "Propagate x-polarized input and compare vectors including the unit global phase.",
         r"Qe_x=e^{i\pi/4}\sigma_+"),
        ("K05","General circular amplitudes","Cell 6",
         "Check the output-input index order and the signs of all Cartesian entries.",
         "Contract a general complex 2x2 tensor and compare independent entry formulas.",
         r"R_{++}=\frac{R_{xx}+R_{yy}+i(R_{xy}-R_{yx})}{2},\quad R_{-+}=\frac{R_{xx}-R_{yy}+i(R_{xy}+R_{yx})}{2}"),
        ("K06","Modified source tensor","Cell 6",
         "Verify the extra yy phase and the cancellation of antisymmetric off-diagonal entries in the flipped channel.",
         "Substitute the source tensor into the circular contractions.",
         r"R_{++}=\frac{a(1+e^{i\phi})}{2}+iAe^{i\delta},\quad R_{-+}=\frac{a(1-e^{i\phi})}{2}"),
        ("K07","Scattered-field reconstruction","Cell 7",
         "Ensure no circular amplitude is lost before return propagation.",
         "Compare Cartesian scattering with its complete circular expansion.",
         r"RQe_x=e^{i\pi/4}(R_{++}\sigma_++R_{-+}\sigma_-)"),
        ("K08","Return plate and physical angle zero","Cell 8",
         "Detect a wrong return matrix or an arbitrary analyzer reference that would rotate or mirror a plot.",
         "Reconstruct the two returned circular states, their real axes and their relative phase.",
         r"Q_b=Q^T,\quad e_{\rm ref}=e_y,\quad e_\perp=-e_x,\quad p_2/p_1=i"),
        ("K09","Analyzer endpoint calibration","Cell 9",
         "Establish what alpha=0 and alpha=90 degrees detect in this optical chain.",
         "Transmit each returned circular state through both calibrated analyzer endpoints.",
         r"\mathcal T_{0,+}=1,\quad\mathcal T_{0,-}=0,\quad\mathcal T_{90,+}=0,\quad\mathcal T_{90,-}=1"),
        ("K10","Matrix chain versus circular amplitude","Cell 10",
         "Check matrix ordering and the relative phase that sets the interference sign.",
         "Compare the production amplitude with the independent circular-channel expansion.",
         r"\mathcal A=e^{i\pi/4}p_1(R_{++}\cos\alpha+iR_{-+}\sin\alpha)"),
        ("K11","Three intensity pieces","Cell 11",
         "Identify an incorrect complex conjugate or an incorrect sign in the interference term.",
         "Independently evaluate the two powers and Im(R++ R-+ conjugate).",
         r"I=P_+\cos^2\alpha+P_-\sin^2\alpha+2K\sin\alpha\cos\alpha,\quad K=\operatorname{Im}(R_{++}R_{-+}^*)"),
        ("K12","Symbolic squared-modulus identity","Cell 11",
         "Prove the hand formula agrees with the matrix result without inserting it into the plotting engine.",
         "Reduce the symbolic difference between A times A conjugate and the source closed form to zero.",
         r"\operatorname{simplify}(I_{\rm matrix}-I_{\rm hand})=0"),
        ("K13","Seeded numerical intensity comparison","Cell 11",
         "Cross-check symbolic processing against independent complex NumPy propagation.",
         "Repeat the source's four seed-1 parameter samples, then 64 phase/sign/zero cases.",
         r"\max_j\lvert I_{{\rm chain},j}-I_{{\rm hand},j}\rvert\le\epsilon_{\rm abs}+\epsilon_{\rm rel}S"),
        ("K14","Fourier reconstruction","Cell 11",
         "Check the harmonic representation used to determine continuous extrema.",
         "Reconstruct the intensity from independently derived constant, cosine and sine coefficients.",
         r"I=I_0+I_c\cos2\alpha+I_s\sin2\alpha,\quad I_0=(P_++P_-)/2,\quad I_c=(P_+-P_-)/2,\quad I_s=K"),
        ("K15","Old-tensor limit","Cell 12",
         "Recover the earlier model when the new relative yy phase vanishes.",
         "Set phi=0 and compare the complete angular law, not only one angle.",
         r"I_{\phi=0}=(a^2+A^2-2aA\sin\delta)\cos^2\alpha"),
        ("K16","Diagonal-tensor phase limit","Cell 12",
         "Check that a relative diagonal phase shifts the analyzer pattern with the correct sign.",
         "Set A=0 and compare with the independently shifted cosine law.",
         r"I_{A=0}=a^2\cos^2(\alpha-\phi/2)"),
        ("K17","Pure flipped-channel limit","Cell 12",
         "Confirm extinction of the same-label channel in a known limiting tensor.",
         "Set A=0 and phi=pi.",
         r"I=a^2\sin^2\alpha"),
        ("K18","All four circular channels","Cell 15, part 1",
         "Check both input labels and prevent interchange of incident and detected indices.",
         "Derive all four circular amplitudes and compare their squared moduli with the source formulas.",
         r"R_{\mu\nu}=\sigma_\mu^\dagger R\sigma_\nu,\quad I_{\mu\nu}=\lvert R_{\mu\nu}\rvert^2"),
        ("K19","Four channels through real optical chains","Cell 15, part 2",
         "Validate the physical preparation and detection path rather than relying only on a basis transform.",
         "Prepare each input with its own +/-45-degree plate and compare same/flip endpoint powers; use the source's five seed-5 samples plus a zero case.",
         r"I_{\nu\nu}^{\rm chain}=I_{\nu\nu}^{\rm circular},\quad I_{-\nu,\nu}^{\rm chain}=I_{-\nu,\nu}^{\rm circular}"),
        ("K20","Circular-input difference and dissymmetry","Cell 15, part 3",
         "Check the source's contrast definition and its denominator; do not infer material chirality from this algebraic test.",
         "Subtract complete powers for the two incident labels and compare the analytic difference.",
         r"\Delta I=4aA\cos(\phi/2)\sin(\phi/2-\delta),\quad {\rm CID}=\Delta I/[2(a^2+A^2)]"),
        ("K21","Zero-contrast limits","Cell 15, part 3",
         "Detect a spurious circular-input difference in limiting cases where it must vanish.",
         "Substitute A=0, phi=pi and delta=phi/2 separately into the computed difference.",
         r"\Delta I_{A=0}=\Delta I_{\phi=\pi}=\Delta I_{\delta=\phi/2}=0"),
        ("K22","Alternative-convention mirror check","Appendix",
         "Identify a documented change of optical convention without forcing different experiments to share one curve.",
         "Use the appendix return plate and lab-x analyzer, then compare with the main source law at -alpha.",
         r"I_{\rm appendix}(\alpha)=I_{\rm main}(-\alpha)\quad\text{for the declared source tensor}"),
        ("K23","Angular periodicity","Cell 13; added explicit check",
         "Ensure that the plotted first-harmonic amplitude gives a 180-degree intensity period.",
         "Translate the source scan by pi and reduce the difference symbolically.",
         r"I(\alpha+\pi)=I(\alpha)"),
        ("K24","Dark source and undefined contrast","Extension of Cell 15",
         "Avoid reporting a finite dissymmetry for a completely dark source.",
         "Set a=A=0 and require all powers to vanish while CID is explicitly undefined.",
         r"I_{\mu\nu}=0,\quad {\rm CID}=\mathrm{undefined}\quad(a=A=0)"),
        ("K25","Deliberately incorrect controls","Validation extension",
         "Demonstrate that the checker can detect conjugation, interference-sign and intensity errors.",
         "Require rejection of three injected mistakes at declared nontrivial parameters.",
         r"\epsilon_{\rm wrong}>\epsilon_{\rm allowed}\quad\text{for each injected error}"),
    ]
    return [dict(id=i,title=t,source=s,purpose=p,procedure=m,expected_latex=e,
                 scope="QWP source reference model")
            for i,t,s,p,m,e in items]


def checking_numeric_evidence(left, right, rtol=1e-10, atol=1e-13):
    """Measure a residual with a declared scale; nonfinite values never pass."""
    left,right=np.broadcast_arrays(np.asarray(left,complex),np.asarray(right,complex))
    finite=bool(np.all(np.isfinite(left)) and np.all(np.isfinite(right)))
    scale=float(max(np.max(np.abs(left)),np.max(np.abs(right)))) if finite else 0.0
    residual=float(np.max(np.abs(left-right))) if finite else None
    tolerance=float(atol+rtol*scale)
    return dict(status="passed" if finite and residual<=tolerance else "failed",
                evidence=dict(kind="numerical",maximum_absolute_residual=residual,
                              scale=scale,absolute_tolerance=atol,relative_tolerance=rtol,
                              allowed_absolute_error=tolerance,comparisons=int(left.size),
                              all_finite=finite))


def checking_symbolic_evidence(residuals):
    """Require every symbolic residual to reduce to zero; unresolved is not passed."""
    residuals=list(sp.Matrix(residuals))
    reduced=[sp.simplify(sp.expand(z.rewrite(sp.exp))) for z in residuals]
    passed=all(z==0 for z in reduced)
    return dict(status="passed" if passed else "inconclusive",
                evidence=dict(kind="symbolic",identities=len(reduced),
                              residuals=[str(z) for z in reduced],
                              residual_latex=[sp.latex(z) for z in reduced]))


def circular_input_contrast(matrix):
    """Return a fixed-lab circular power matrix and a safely defined input contrast."""
    U=numeric(sp.Matrix.hstack(sig_p,sig_m))
    R=np.asarray(matrix,complex)
    powers=np.abs(U.conj().T@R@U)**2
    plus,minus=float(np.sum(powers[:,0])),float(np.sum(powers[:,1]))
    total=plus+minus
    return dict(powers=powers,difference=plus-minus,total_power=total,
                cid=(plus-minus)/total if total>0 else None,
                cid_defined=bool(total>0),index_order="output,input")


def validate_optical_reference():
    """Run exact, numerical, limiting-case and convention checks from the uploaded V2."""
    definitions={r["id"]:r for r in checking_procedure_catalog()}
    rows=[]
    def symbolic(key,residuals):
        rows.append({**definitions[key],**checking_symbolic_evidence(residuals)})
    def numerical(key,left,right):
        rows.append({**definitions[key],**checking_numeric_evidence(left,right)})
    def power(z):
        return sp.simplify(sp.expand_complex(sp.expand(z*sp.conjugate(z))))
    aa,bb,dd,pp=ref_a,ref_A,ref_delta,ref_phi
    R=QWP_SOURCE_TENSOR
    Q,Qb=QWP_QWP,QWP_RETURN_QWP
    U=sp.Matrix.hstack(sig_p,sig_m)
    phase=(1+sp.I)/sp.sqrt(2)
    expected_Q=sp.Matrix([[1+sp.I,-1+sp.I],[-1+sp.I,1+sp.I]])/2
    Ein=Q*x_hat
    rpp=(sig_p.H*R*sig_p)[0];rmp=(sig_m.H*R*sig_p)[0]
    hp=aa*(1+sp.exp(sp.I*pp))/2+sp.I*bb*sp.exp(sp.I*dd)
    hm=aa*(1-sp.exp(sp.I*pp))/2
    p1=(-1+sp.I)/sp.sqrt(2);p2=-(1+sp.I)/sp.sqrt(2)
    reference,perpendicular=y_hat,-x_hat
    analyzer=reference*sp.cos(alpha)+perpendicular*sp.sin(alpha)
    chain=(analyzer.H*Qb*R*Ein)[0]
    production=transverse_amplitude_record(R,optical_chain("QWP"))["amplitude"]
    Pp=aa**2*sp.cos(pp/2)**2+bb**2+2*aa*bb*sp.cos(pp/2)*sp.sin(pp/2-dd)
    Pm=aa**2*sp.sin(pp/2)**2
    K=aa**2*sp.sin(pp)/2+aa*bb*sp.sin(pp/2)*sp.sin(pp/2-dd)
    hand=Pp*sp.cos(alpha)**2+Pm*sp.sin(alpha)**2+2*K*sp.sin(alpha)*sp.cos(alpha)
    raw=power(production)
    symbolic("K01",U.H*U-sp.eye(2))
    symbolic("K02",Q-expected_Q)
    symbolic("K03",list(Q.H*Q-sp.eye(2))+list(Q.T-Q))
    symbolic("K04",Ein-phase*sig_p)
    xx,xy,yx,yy=sp.symbols("check_xx check_xy check_yx check_yy",complex=True)
    G=sp.Matrix([[xx,xy],[yx,yy]])
    symbolic("K05",[(sig_p.H*G*sig_p)[0]-(xx+yy+sp.I*(xy-yx))/2,
                     (sig_m.H*G*sig_p)[0]-(xx-yy+sp.I*(xy+yx))/2])
    symbolic("K06",[rpp-hp,rmp-hm])
    symbolic("K07",R*Ein-phase*(hp*sig_p+hm*sig_m))
    symbolic("K08",list(Qb-Q.T)+list(Qb*sig_p-p1*reference)+
             list(Qb*sig_m-p2*perpendicular)+[p2/p1-sp.I])
    transmissions=[power((analyzer.subs(alpha,t).H*Qb*s)[0])
                   for t in [0,sp.pi/2] for s in [sig_p,sig_m]]
    symbolic("K09",[x-y for x,y in zip(transmissions,[1,0,0,1])])
    symbolic("K10",[production-chain,chain-phase*p1*(hp*sp.cos(alpha)+sp.I*hm*sp.sin(alpha))])
    symbolic("K11",[power(rpp)-Pp,power(rmp)-Pm,
                      sp.im(sp.expand_complex(rpp*sp.conjugate(rmp)))-K])
    symbolic("K12",[raw-hand])
    rng=np.random.default_rng(1)
    samples=[[rng.uniform(.2,2),rng.uniform(.2,2),rng.uniform(0,2*np.pi),
              rng.uniform(0,2*np.pi),rng.uniform(0,2*np.pi)] for _ in range(4)]
    samples += [[rng.uniform(-2,2),rng.uniform(-2,2),rng.uniform(-np.pi,np.pi),
                 rng.uniform(-np.pi,np.pi),rng.uniform(-np.pi,np.pi)] for _ in range(60)]
    samples += [[0,0,0,0,0],[1,0,0,np.pi,np.pi/2],[1,1,np.pi/2,0,0],[1,.4,0,2*np.pi,.3]]
    hand_fn=sp.lambdify((aa,bb,dd,pp,alpha),hand,"numpy",cse=True)
    q=numeric(Q);qb=numeric(Qb)
    direct_values=[];hand_values=[]
    for av,bv,dv,pv,tv in samples:
        matrix=np.array([[av,bv*np.exp(1j*dv)],[-bv*np.exp(1j*dv),av*np.exp(1j*pv)]])
        e=np.array([-np.sin(tv),np.cos(tv)])
        direct_values.append(abs(e.conj()@qb@matrix@q@np.array([1,0]))**2)
        hand_values.append(hand_fn(av,bv,dv,pv,tv))
    numerical("K13",direct_values,hand_values)
    symbolic("K14",[(Pp+Pm)/2+(Pp-Pm)/2*sp.cos(2*alpha)+K*sp.sin(2*alpha)-hand])
    symbolic("K15",[raw.subs(pp,0)-(aa**2+bb**2-2*aa*bb*sp.sin(dd))*sp.cos(alpha)**2])
    symbolic("K16",[raw.subs(bb,0)-aa**2*sp.cos(alpha-pp/2)**2])
    symbolic("K17",[raw.subs({bb:0,pp:sp.pi})-aa**2*sp.sin(alpha)**2])
    circular=U.H*R*U
    hands=sp.Matrix([[hp,hm],[hm,aa*(1+sp.exp(sp.I*pp))/2-sp.I*bb*sp.exp(sp.I*dd)]])
    expected_powers=[Pp,Pm,Pm,aa**2*sp.cos(pp/2)**2+bb**2-2*aa*bb*sp.cos(pp/2)*sp.sin(pp/2-dd)]
    symbolic("K18",list(circular-hands)+[power(x)-y for x,y in zip(circular,expected_powers)])
    rng=np.random.default_rng(5)
    channel_samples=[[rng.uniform(.2,2),rng.uniform(.2,2),rng.uniform(0,6.28),rng.uniform(0,6.28)] for _ in range(5)]
    channel_samples += [[0,0,0,0]]
    basis=numeric(U);optical_powers=[];basis_powers=[];preparation_residuals=[]
    for av,bv,dv,pv in channel_samples:
        matrix=np.array([[av,bv*np.exp(1j*dv)],[-bv*np.exp(1j*dv),av*np.exp(1j*pv)]])
        for j,spin in enumerate([1,-1]):
            plate=numeric(waveplate(-spin*sp.pi/4,sp.pi/2))
            incident=plate@np.array([1,0]);sigma=basis[:,j]
            input_phase=incident[0]/sigma[0]
            preparation_residuals.extend(incident-input_phase*sigma)
            preparation_residuals.append(abs(input_phase)-1)
            returned=plate.T@sigma;k=int(np.argmax(np.abs(returned)))
            ref=returned/(returned[k]/abs(returned[k]))
            preparation_residuals.extend(np.imag(ref))
            orth=np.array([[0,-1],[1,0]])@ref
            for out,axis in [(j,ref),(1-j,orth)]:
                optical_powers.append(abs(axis.conj()@plate.T@matrix@incident)**2)
                basis_powers.append(abs(basis[:,out].conj()@matrix@sigma)**2)
    numerical("K19",optical_powers+list(preparation_residuals),basis_powers+[0]*len(preparation_residuals))
    delta=power(circular[0,0])+power(circular[1,0])-power(circular[0,1])-power(circular[1,1])
    expected_delta=4*aa*bb*sp.cos(pp/2)*sp.sin(pp/2-dd)
    total=sum(power(z) for z in circular)
    symbolic("K20",[delta-expected_delta,total-2*(aa**2+bb**2)])
    rows[-1]["assumption"]="CID is defined only when a^2+A^2>0; its formula uses the source's fixed-lab convention."
    symbolic("K21",[delta.subs(bb,0),delta.subs(pp,sp.pi),delta.subs(dd,pp/2)])
    appendix_return=waveplate(sp.pi/4,sp.pi/2)
    appendix_analyzer=sp.Matrix([sp.cos(alpha),sp.sin(alpha)])
    appendix=power((appendix_analyzer.H*appendix_return*R*Ein)[0])
    symbolic("K22",[appendix-raw.subs(alpha,-alpha)])
    symbolic("K23",[raw.subs(alpha,alpha+sp.pi)-raw])
    dark=circular_input_contrast(np.zeros((2,2),complex))
    rows.append({**definitions["K24"],"status":"passed" if dark["cid"] is None and dark["total_power"]==0 else "failed",
                 "evidence":dict(kind="defined-domain",total_power=dark["total_power"],cid=dark["cid"],cid_defined=dark["cid_defined"])})
    probe=np.array([[1,.4*np.exp(.7j)],[-.4*np.exp(.7j),np.exp(1.1j)]])
    ei=np.array([1,1j])/np.sqrt(2);es=np.array([.6,.8j])
    correct=abs(es.conj()@probe@ei)**2
    wrong_transpose=abs(es@probe@ei)**2
    t=.47;rp=(basis.conj().T@probe@basis)[0,0];rm=(basis.conj().T@probe@basis)[1,0]
    good=abs(rp*np.cos(t)+1j*rm*np.sin(t))**2
    wrong_cross=abs(rp)**2*np.cos(t)**2+abs(rm)**2*np.sin(t)**2-2*np.imag(rp*rm.conjugate())*np.sin(t)*np.cos(t)
    probes=[checking_numeric_evidence(wrong_transpose,correct),
            checking_numeric_evidence(wrong_cross,good),
            checking_numeric_evidence(1e-5,0)]
    rows.append({**definitions["K25"],"status":"passed" if all(x["status"]=="failed" for x in probes) else "failed",
                 "evidence":dict(kind="negative-controls",rejected=[x["status"]=="failed" for x in probes],
                                 residuals=[x["evidence"] for x in probes])})
    return dict(status="passed" if all(r["status"]=="passed" for r in rows) else "failed",
                kind="QWP source reference validation",source=OPTICAL_REFERENCE_SOURCE,
                software_version=AUDIT_VERSION,
                rows=rows,passed=sum(r["status"]=="passed" for r in rows),total=len(rows),
                scope="Reference identities and implementation checks. Passing does not certify material coefficients, experimental propagation or chirality.",
                notation_note="Cells 6-11 intermittently call <sigma-|R|sigma+> R+-; this report consistently writes R-+. The contracted vector, not the ambiguous label, defines the channel.")


def checking_procedures_for_run(run):
    """Apply the source's checking pattern to the actual selected optical states."""
    rows=[];angles=run["angles"]
    def row(key,title,purpose,procedure,expected,left,right,scope="Current calculation"):
        rows.append(dict(id=key,title=title,source="Generalization of the optical source reference",
                         purpose=purpose,procedure=procedure,expected_latex=expected,scope=scope,
                         **checking_numeric_evidence(left,right)))
    U=numeric(sp.Matrix.hstack(sig_p,sig_m))
    row("G01","Circular basis","Check a complete orthonormal optical basis.",
        "Calculate the circular Gram matrix.",r"U_\sigma^\dagger U_\sigma=I_2",U.conj().T@U,np.eye(2))
    if run["geometry"] is not None:
        T=numeric(run["geometry"]["T"]).real
        row("G02","Proper measurement frame","Detect a reflected or nonorthonormal frame before interpreting an orientation.",
            "Test orthogonality and determinant using the declared frame.",r"T^TT=I_3,\quad\det T=1",
            np.r_[((T.T@T)-np.eye(3)).ravel(),np.linalg.det(T)-1],np.zeros(10))
    else:
        rows.append(dict(id="G02",title="Proper measurement frame",source="3D extension",scope="Current calculation",
            purpose="A source effective 2x2 tensor has no crystal frame to test.",
            procedure="Inspect the active tensor model.",expected_latex="",status="not applicable",
            evidence=dict(kind="scope",reason="QWP_SOURCE_2D has no crystal orientation.")))
    for index,(name,ch) in enumerate(run["display_channels"].items(),1):
        optical=ch["optical"];values=ch["values"]
        ei=vector_samples(optical["Ein"],angles)
        es=vector_samples(optical["effective_analyzer"],angles)
        analyzer=vector_samples(optical["analyzer"],angles)
        B=numeric(optical["B"])
        prefix=f"G{index+2:02d}"
        scope="Current displayed channel: "+name
        row(prefix+"a",name+": normalized states","Detect state normalization or complex-conjugation errors.",
            "Evaluate the incident and effective detection norms on the actual angular grid.",
            r"E_i^\dagger E_i=e_s^\dagger e_s=1",
            np.r_[np.sum(abs(ei)**2,axis=0),np.sum(abs(es)**2,axis=0)],np.ones(2*len(angles)),scope)
        row(prefix+"b",name+": return optics","Check norm preservation by the declared return element; B may be identity.",
            "Form B dagger B in the current profile.",r"B^\dagger B=I_2",B.conj().T@B,np.eye(2),scope)
        raw=np.zeros(len(angles));circular=np.zeros_like(raw)
        rotation_actual=[];rotation_expected=[];norm_circular=[];norm_cartesian=[]
        for rec in ch["records"]:
            R=numeric(rec["Rperp"].subs(values));scattered=R@ei
            chain=np.sum(analyzer.conj()*(B@scattered),axis=0)
            transformed=U.conj().T@R@U
            circ=np.sum((U.conj().T@es).conj()*(transformed@(U.conj().T@ei)),axis=0)
            raw+=abs(chain)**2;circular+=abs(circ)**2
            norm_circular.extend(np.sum(abs(U.conj().T@scattered)**2,axis=0))
            norm_cartesian.extend(np.sum(abs(scattered)**2,axis=0))
            if "Rc" in rec:
                Rc=numeric(rec["Rc"].subs(values));Rl=numeric(rec["Rlab"].subs(values))
                rotation_actual.extend(Rl.ravel());rotation_expected.extend((T.T@Rc@T).ravel())
                rotation_actual.extend(R.ravel());rotation_expected.extend((numeric(P)@Rl@numeric(P).T).ravel())
        row(prefix+"c",name+": explicit chain","Check the plotted arrays against independent complex matrix propagation.",
            "Propagate E_i through each tensor and B, project with analyzer dagger, and sum only partner powers.",
            r"I_{\rm plot}=\sum_j\lvert e_{\rm an}^\dagger B R_{\perp,j}E_i\rvert^2",
            ch["curve"],raw,scope)
        row(prefix+"d",name+": circular reconstruction","Ensure basis changes preserve the same physical states and intensity.",
            "Transform tensor and both actual optical vectors into the circular basis.",
            r"I_{\rm Cartesian}=I_{\rm circular}",raw,circular,scope)
        row(prefix+"e",name+": complete output power","Check circular-basis completeness without assuming Raman scattering is lossless.",
            "Sum both outgoing circular powers and compare with the squared scattered-field norm.",
            r"\sum_{\mu=\pm}\lvert\sigma_\mu^\dagger R_\perp E_i\rvert^2=\lVert R_\perp E_i\rVert^2",
            norm_circular,norm_cartesian,scope)
        if rotation_actual:
            row(prefix+"f",name+": rotation and projection","Confirm that the full 3D rotation precedes transverse projection.",
                "Independently reconstruct R_lab and R_perp with the declared real frame.",
                r"R_{\rm lab}=T^TR_cT,\quad R_\perp=PR_{\rm lab}P^T",
                rotation_actual,rotation_expected,scope)
    if run["config"]["tensor_model"]=="QWP_SOURCE_2D":
        vals=qwp_source_values(run["config"]["source_parameters"])
        expression=qwp_source_algebra()["source_intensity"].subs(vals)
        fn=sp.lambdify(alpha,expression,"numpy")
        reference=np.broadcast_to(np.asarray(fn(angles),float),angles.shape)
        row("G-SOURCE","Source closed-form comparison","Check this run against the source model-specific expression.",
            "Compare the computed source curve with the independent hand formula after substituting these four inputs.",
            r"I_{\rm matrix}(\alpha)=I_{\rm hand}(\alpha)",
            next(iter(run["display_channels"].values()))["curve"],reference,
            "Only the effective optical source model")
    else:
        rows.append(dict(id="G-SOURCE",title="Source closed-form comparison",source="Optical source reference, Cell 11",
            scope="Only the effective optical source model",status="not applicable",
            purpose="Do not impose a special antisymmetric 2x2 response on a different material tensor.",
            procedure="Check the selected tensor model before applying its source-specific formula.",
            expected_latex="",evidence=dict(kind="scope",reason="The current crystal uses its own full tensor; general contraction checks apply.")))
    applicable=[r for r in rows if r["status"]!="not applicable"]
    return dict(status="passed" if all(r["status"]=="passed" for r in applicable) else "failed",
        kind="Checking procedures for the current calculation",case=run["config"]["case_label"],
        software_version=AUDIT_VERSION,configuration=copy.deepcopy(run["config"]),
        angular_samples=len(angles),scan_basis=run["optical"]["scan_basis"],
        rows=rows,passed=sum(r["status"]=="passed" for r in applicable),total=len(applicable),
        not_applicable=sum(r["status"]=="not applicable" for r in rows),
        scope="The reference testing pattern is generalized to the current states and tensors. Source-only identities are explicitly scoped.",
        source=OPTICAL_REFERENCE_SOURCE)


def checking_report_markdown(report):
    """Export the same purpose, procedure, equation and measured evidence shown in the UI."""
    lines=["## "+report["kind"],"",report["scope"],"",
           f"Status: **{report['status']}**. Passed: {report['passed']}/{report['total']}.",""]
    if report.get("notation_note"):lines += [report["notation_note"],""]
    for item in report["rows"]:
        lines += [f"### {item['id']} — {item['title']}","",
                  "**Source:** "+item["source"],"**Scope:** "+item["scope"],
                  "**Purpose:** "+item["purpose"],"**Procedure:** "+item["procedure"]]
        if item.get("expected_latex"):lines += ["","$$"+item["expected_latex"]+"$$",""]
        lines += ["**Result:** "+item["status"],"",
                  "Evidence: "+json.dumps(serializable(item["evidence"]),ensure_ascii=False,allow_nan=False),""]
    return "\n\n".join(lines)
