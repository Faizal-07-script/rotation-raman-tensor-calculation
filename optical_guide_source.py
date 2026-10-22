"""Optical-profile documentation derived from the common Jones contraction.

The catalog explains the implemented experiments. It never generates or changes
a material intensity. Explicit source equations and program-derived identities
are distinguished in each record.
"""

OPTICAL_GUIDE_REFERENCES = {
    "jones": ("Jones calculus", "https://doi.org/10.1364/JOSA.31.000488"),
    "complex": ("Complex Raman tensors: Eq. (3), Eqs. (13a-d)", "https://doi.org/10.1039/D1CP03626B"),
    "cubic": ("Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)", "https://doi.org/10.1002/jrs.70113"),
    "circular": ("Circular selection rules: Eqs. (21-24)", "https://doi.org/10.1039/D1CP02209A"),
    "optical-source": ("Uploaded QWP implementation reference", "Original optical-reference notebook"),
    "kumar-original": ("Uploaded Version 3 QWP implementation reference", "Included Version 3 source notebook"),
}


def optical_method_catalog():
    """Describe all nine choices using states at the sample, not menu shorthand."""
    v = r"v(t)=(\cos t,\sin t)^T"
    w = r"w(t)=(-\sin t,\cos t)^T"
    sigma = r"\sigma_s=(1,is)^T/\sqrt{2},\quad s=\pm1"
    linear_note = (
        "Both linear states rotate together in the fixed-tensor coordinates. "
        "This represents a sample-angle experiment with a declared sign convention; "
        "do not also rotate the tensor by the same scan angle."
    )
    data = {
        "CUBIC_VV": dict(family="Co-rotating linear states", scan="theta: common incident/detector angle",
            preparation="Linear input v(t), t=theta+theta0", return_path="Identity: no extra return plate",
            detection="Linear analyzer parallel to the input", states=[v, r"E_i=v(t),\quad e_s=v(t),\quad B=I_2"],
            amplitude=r"\mathcal A_{VV}=v(t)^\dagger R_\perp v(t)",
            intensity=r"I_{VV}=|r_{xx}\cos^2t+(r_{xy}+r_{yx})\sin t\cos t+r_{yy}\sin^2t|^2",
            invariant="The paired VV/VH choice must reproduce this VV channel with identical inputs.",
            use_for="Parallel linear measurements and the VV member of the cubic benchmark.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Direct specialization of the cited contraction and linear states."),
        "CUBIC_VH": dict(family="Co-rotating linear states", scan="theta: common incident/detector angle",
            preparation="Linear input v(t), t=theta+theta0", return_path="Identity: no extra return plate",
            detection="Linear analyzer perpendicular to the input", states=[v, w, r"E_i=v(t),\quad e_s=w(t),\quad B=I_2"],
            amplitude=r"\mathcal A_{VH}=w(t)^\dagger R_\perp v(t)",
            intensity=r"I_{VH}=|r_{yx}\cos^2t-r_{xy}\sin^2t+(r_{yy}-r_{xx})\sin t\cos t|^2",
            invariant="The paired VV/VH choice must reproduce this VH channel with identical inputs.",
            use_for="Crossed linear measurements and the VH member of the cubic benchmark.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Direct specialization of the cited contraction and crossed states."),
        "LINEAR_PAIR": dict(family="Co-rotating linear states", scan="theta: one common angle for both channels",
            preparation="One linear input and one shared coefficient set", return_path="Identity for both channels",
            detection="Calculate parallel and perpendicular analyzers separately", states=[v, w, r"E_i=v(t),\quad e_s^{VV}=v(t),\quad e_s^{VH}=w(t)"],
            amplitude=r"\mathcal A_{VV}=v^\dagger R_\perp v,\quad\mathcal A_{VH}=w^\dagger R_\perp v",
            intensity=r"I_{VV}=|\mathcal A_{VV}|^2,\quad I_{VH}=|\mathcal A_{VH}|^2",
            invariant="This is a paired output, not a third polarization law. Each raw curve equals its standalone channel.",
            use_for="Comparing VV and VH for the same phonon coefficients, surface and angular zero.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Two instances of the same Jones engine; powers are not added to define a new channel."),
        "CIRCULAR_LINEAR": dict(family="Circular input / linear detector", scan="alpha: linear-analyzer angle only",
            preparation="Fixed circular input sigma_s", return_path="Identity: the detector state at the sample is linear",
            detection="v(alpha+alpha0), with a calibrated analyzer zero", states=[sigma, r"E_i=\sigma_s,\quad e_s=v(\alpha+\alpha_0),\quad B=I_2"],
            amplitude=r"\mathcal A_{CL}=\frac{p e^{it}+q e^{-it}}{\sqrt{2}},\quad t=\alpha+\alpha_0",
            intensity=r"I_{CL}=\frac{|p|^2+|q|^2}{2}+\operatorname{Re}(p q^*e^{2it})",
            invariant="For sigma+ input it equals custom Jones with theta_i=45, beta_i=90, theta_s0=alpha0 and beta_s=0 degrees.",
            use_for="Circular illumination with a linear effective detector at the sample.",
            caution="A bare linear-analyzer scan does not select pure sigma+ or sigma- endpoints. A return QWP changes the effective detector.",
            sources=["jones", "circular"], provenance="Program Jones-calculus extension. The circular selection-rule paper does not prescribe this continuous scan or its quantitative intensity."),
        "CUBIC_SIGMA": dict(family="Circular input / elliptical detector", scan="alpha: effective detection-state parameter",
            preparation="Fixed sigma+ input", return_path="Identity in the effective-state representation",
            detection="j(pi/4+alpha, pi/2), elliptical except at special angles",
            states=[r"E_i=\sigma_+,\quad e_s=(\cos(\pi/4+\alpha),i\sin(\pi/4+\alpha))^T", r"e_s=\cos\alpha\,\sigma_+-\sin\alpha\,\sigma_-"],
            amplitude=r"\mathcal A_E=p\cos\alpha-q\sin\alpha",
            intensity=r"I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\operatorname{Re}(p q^*)\sin\alpha\cos\alpha",
            invariant="It equals custom Jones at theta_i=45, beta_i=90, theta_s0=45, beta_s=90 degrees; source QWP endpoints agree up to phase, intermediate states generally differ.",
            use_for="The cubic paper sigma+alpha equations, its Fig. 1(c) benchmark and the declared slide-frame example.",
            caution="This implements Eq. (11) at theta=pi/4 and beta=beta'=pi/2. The paper calls alpha a polarizer angle, but its effective detector is not a bare linear state at the sample. An apparatus must be calibrated before identifying the two.",
            sources=["cubic", "jones"], provenance="Cited effective Jones parameterization; the p/q expansion is derived here from that state."),
        "QWP": dict(family="Circular input / explicit return optics", scan="alpha: physical linear analyzer after the return plate",
            preparation="Lab-X input through Q=Rot(-pi/4) diag(1,i) Rot(-pi/4)^T",
            return_path="B=Q.T in the uploaded source basis convention",
            detection="Linear analyzer (-sin alpha, cos alpha) after B; effective detector B.H times analyzer",
            states=[r"Q=\frac12\begin{pmatrix}1+i&-1+i\\-1+i&1+i\end{pmatrix},\quad E_i=Qe_X=e^{i\pi/4}\sigma_+", r"e_{an}=(-\sin\alpha,\cos\alpha)^T,\quad B=Q^T,\quad e_s=B^\dagger e_{an}", r"e_s\sim\cos\alpha\,\sigma_+-i\sin\alpha\,\sigma_-"],
            amplitude=r"\mathcal A_Q\sim p\cos\alpha+i q\sin\alpha",
            intensity=r"I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\operatorname{Im}(p q^*)\sin\alpha\cos\alpha",
            invariant="At alpha=0 and pi/2 the circular endpoints equal the elliptical reference in power; intermediate intensities generally need not match.",
            use_for="The uploaded QWP optical sequence, after its axes, return-path convention and analyzer zero are verified.",
            caution="Q.T is a declared source convention, not a universal reverse-path rule. Keep either the explicit B or its effective detector, never both. The crystal tensor remains 3x3 before transverse restriction.",
            sources=["kumar-original", "jones"], provenance="Exact uploaded optical chain plus a program-derived p/q identity valid for any supplied R_perp under that chain."),
        "CIRCULAR_SAME": dict(family="Fixed circular channels", scan="None: both sample states are fixed",
            preparation="Fixed sigma_s input", return_path="Identity in the effective-state representation",
            detection="Fixed sigma_s detector", states=[sigma, r"E_i=\sigma_s,\quad e_s=\sigma_s"],
            amplitude=r"\mathcal A_{same}=\sigma_s^\dagger R_\perp\sigma_s",
            intensity=r"I_{same}=|\sigma_s^\dagger R_\perp\sigma_s|^2",
            invariant="The curve is constant when tensor, orientation and optical states remain fixed; a polar circle is a display of that constant.",
            use_for="A fixed same-basis circular channel; compare helicity labels only after reconciling beam directions.",
            caution="Same fixed XY circular label is not automatically conserved propagation-relative helicity in backscattering. This profile does not rotate the sample.",
            sources=["circular", "jones"], provenance="Fixed-state tensor contraction; the separate angular-momentum rule is conditional and does not set curve heights."),
        "CIRCULAR_OPPOSITE": dict(family="Fixed circular channels", scan="None: both sample states are fixed",
            preparation="Fixed sigma_s input", return_path="Identity in the effective-state representation",
            detection="Fixed sigma_-s detector", states=[sigma, r"E_i=\sigma_s,\quad e_s=\sigma_{-s}"],
            amplitude=r"\mathcal A_{opposite}=\sigma_{-s}^\dagger R_\perp\sigma_s",
            intensity=r"I_{opposite}=|\sigma_{-s}^\dagger R_\perp\sigma_s|^2",
            invariant="The curve is constant under this fixed experiment. Its power is the opposite-basis circular channel, not an alpha sweep.",
            use_for="A fixed opposite-basis circular channel, with an explicit propagation convention.",
            caution="Opposite fixed XY circular labels can represent conserved physical helicity for counterpropagating beams. Match the reference's basis before assigning conserved/changing names.",
            sources=["circular", "jones"], provenance="Fixed-state tensor contraction, distinct from a spatial vortex-intensity calculation."),
        "DIRECT_JONES": dict(family="Custom effective states", scan="alpha: theta_s0+alpha; input and phase controls fixed",
            preparation="j(theta_i,beta_i), selected by the user", return_path="Identity: any return optics must already be included in e_s",
            detection="j(theta_s0+alpha,beta_s)", states=[r"j(t,\beta)=(\cos t,e^{i\beta}\sin t)^T", r"E_i=j(\theta_i,\beta_i),\quad e_s=j(\theta_{s0}+\alpha,\beta_s),\quad B=I_2"],
            amplitude=r"\mathcal A_J=j(\theta_{s0}+\alpha,\beta_s)^\dagger R_\perp j(\theta_i,\beta_i)",
            intensity=r"I_J=|\mathcal A_J|^2",
            invariant="It reproduces a preset only when both effective states and their scan laws agree up to global phase; an arbitrary waveplate path need not fit this restricted constant-beta scan.",
            use_for="Calibrated effective states or exact checks of the matching preset parameters.",
            caution="Changing beta_s changes relative phase and interference. This custom profile keeps the input fixed, so it does not in general reproduce co-rotating VV/VH scans.",
            sources=["jones", "complex"], provenance="User-defined specialization of the common contraction, not a separate material law."),
    }
    return {key: dict(key=key, label=GENERAL_PROFILES[key], **value) for key, value in data.items()}


def optical_method_markdown(kind):
    """Explain a selected profile with equations and traceable source roles."""
    guide = optical_method_catalog()[kind]
    lines = ["### " + guide["label"], "**Family:** " + guide["family"],
        "**Scan:** " + guide["scan"], "**Preparation:** " + guide["preparation"],
        "**Return optics:** " + guide["return_path"], "**Detection:** " + guide["detection"],
        r"$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$",
        r"$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$"]
    lines += ["$$" + equation + "$$" for equation in guide["states"] + [guide["amplitude"], guide["intensity"]]]
    lines += ["**Use for:** " + guide["use_for"], "**Equality check:** " + guide["invariant"],
        "**Physical distinction:** " + guide["caution"], "**Source scope:** " + guide["provenance"],
        "**References:** " + "; ".join("[" + OPTICAL_GUIDE_REFERENCES[k][0] + "](" + OPTICAL_GUIDE_REFERENCES[k][1] + ")"
            if OPTICAL_GUIDE_REFERENCES[k][1].startswith("https:") else OPTICAL_GUIDE_REFERENCES[k][0] + " (included original notebook)"
            for k in guide["sources"]),
        "The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration."]
    return "\n\n".join(lines)


def optical_methods_overview_markdown():
    """Summarize how to select an experiment, with no change to tensor coefficients."""
    lines = ["## Choose the optical experiment before comparing curves",
        "All choices use the same complex-amplitude law. Changing a preparation, detector or scan changes the measured quantity. Select the profile that matches calibrated optics, or the exact states of a reference figure.",
        "| Profile | Scanned quantity | Detection at the sample |", "|---|---|---|"]
    lines += ["| " + g["label"] + " | " + g["scan"] + " | " + g["detection"] + " |" for g in optical_method_catalog().values()]
    lines += ["", "### Same tensor, different interference",
        r"$$p=\sigma_+^\dagger R_\perp\sigma_+,\quad q=\sigma_-^\dagger R_\perp\sigma_+$$",
        r"$$I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\mathrm{Re}(p q^*)\sin\alpha\cos\alpha$$",
        r"$$I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\mathrm{Im}(p q^*)\sin\alpha\cos\alpha$$",
        r"$$I_{CL}=\tfrac12(|p|^2+|q|^2)+\mathrm{Re}(p q^*e^{2i(\alpha+\alpha_0)})$$",
        "These equations are derived from the implemented sample states. The continuous circular-input/linear-detector scan is a Jones extension, not a quantitative prediction of the vortex selection-rule paper.",
        "### What is a reference?",
        "Use the elliptical reference for the cubic paper Fig. 1(c) and the declared slide-frame example; use the explicit QWP chain for the uploaded optical notebook; use VV/VH for the corresponding linear measurements. A CaNb2O6 material label alone does not determine a detector state. Keep lattice metric, surface axes, coefficients, angle zeros and Ag component/coherent-mode policy identical when comparing results.",
        "### Fixed labels and physical helicity",
        r"$$\mathbf k_i=-k_i\hat Z,\quad\mathbf k_s=+k_s\hat Z,\quad S_3=2\mathrm{Im}(E_X^*E_Y),\quad h_i=-S_3(E_i),\quad h_s=S_3(e_s)$$",
        "The physical sign above uses exp[i(k.r-omega t)] and fixed laboratory XY components. Reference papers can attach conserved/changing names to different beam-coordinate conventions. Match those conventions before comparing names. Fixed circular states give constant intensity when the sample is not rotated.",
        "### Ag presentation",
        "Ag(xx), Ag(yy) and Ag(zz) remain separate contribution powers in the main plots. A complete single-phonon intensity is the squared sum of its component amplitudes; orthogonal unresolved phonon partners instead contribute a sum of powers. These are separate choices from the optical profile."]
    return "\n\n".join(lines)


def optical_profile_example():
    """Compute a transparent same-tensor example through the actual optical engine."""
    tensor = sp.diag(1, 2)
    grid = np.linspace(0, 2 * np.pi, 361)
    result = {}
    for kind in ["CIRCULAR_LINEAR", "CUBIC_SIGMA", "QWP"]:
        optical = optical_chain(kind, paper=dict(s_in=1, analyzer_zero_deg=0))
        amplitude = tidy((optical["effective_analyzer"].H * tensor * optical["Ein"])[0])
        intensity = sp.simplify(sp.expand_complex(amplitude * sp.conjugate(amplitude)))
        curve = np.asarray(sp.lambdify(alpha, intensity, "numpy")(grid), dtype=float)
        if curve.ndim == 0:
            curve = np.full(grid.shape, float(curve))
        result[kind] = dict(intensity=intensity, curve=curve,
            at_45_degrees=sp.simplify(intensity.subs(alpha, sp.pi / 4)))
    return dict(tensor=tensor, angles=grid, profiles=result,
        scope="Illustrative R_perp=diag(1,2), one coherent tensor, sigma+ input, common raw units; no material is assigned.")


def optical_profile_comparison_figure():
    """Plot three engine-calculated curves on one declared radial scale."""
    data = optical_profile_example()
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.2), subplot_kw=dict(projection="polar"))
    labels = ["Direct linear detector", "Elliptical reference", "Return QWP + analyzer"]
    colors = ["#285b75", "#671d28", "#98682e"]
    for axis, (key, entry), label, color in zip(axes, data["profiles"].items(), labels, colors):
        axis.plot(data["angles"], entry["curve"], color=color, linewidth=2)
        axis.set_ylim(0, 2.5)
        axis.set_yticks([0.5, 1.5, 2.5])
        axis.set_thetagrids([0, 90, 180, 270])
        axis.tick_params(labelsize=10)
        axis.set_title(label, fontsize=12, pad=24)
    figure.suptitle(r"Same $R_\perp=\mathrm{diag}(1,2)$; different detector states", fontsize=14)
    figure.tight_layout(rect=(0, 0, 1, 0.91))
    return figure


def validate_optical_method_guide():
    """Check the displayed identities for a general complex, nonsymmetric tensor."""
    entries = sp.symbols("rxx rxy ryx ryy", complex=True)
    tensor = sp.Matrix(2, 2, entries)
    p = (sig_p.H * tensor * sig_p)[0]
    q = (sig_m.H * tensor * sig_p)[0]
    c, s = sp.cos(alpha), sp.sin(alpha)
    expected = {
        "CUBIC_VV": entries[0]*c*c + (entries[1]+entries[2])*s*c + entries[3]*s*s,
        "CUBIC_VH": entries[2]*c*c - entries[1]*s*s + (entries[3]-entries[0])*s*c,
        "CUBIC_SIGMA": p * c - q * s,
        "QWP": p * c + sp.I * q * s,
        "CIRCULAR_LINEAR": (p * sp.exp(sp.I * alpha) + q * sp.exp(-sp.I * alpha)) / sp.sqrt(2),
    }
    for kind, target in expected.items():
        optical = optical_chain(kind, paper=dict(s_in=1, analyzer_zero_deg=0))
        actual = (optical["effective_analyzer"].H * tensor * optical["Ein"])[0]
        residual = sp.expand_complex(actual * sp.conjugate(actual) - target * sp.conjugate(target))
        check(zero(sp.Matrix([sp.trigsimp(sp.expand(residual))])), kind + ": guide intensity identity differs from the engine.")
    for kind, beta_s, theta_s in [("CUBIC_SIGMA", 90, 45), ("CIRCULAR_LINEAR", 0, 0)]:
        direct = optical_chain("DIRECT_JONES", dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=theta_s, beta_s_deg=beta_s))
        preset = optical_chain(kind, paper=dict(s_in=1, analyzer_zero_deg=0))
        check(zero(direct["Ein"] - preset["Ein"]), kind + ": matching custom incident state failed.")
        check(zero(direct["effective_analyzer"] - preset["effective_analyzer"]), kind + ": matching custom detector failed.")
    for kind in ["CIRCULAR_SAME", "CIRCULAR_OPPOSITE"]:
        for spin in [-1, 1]:
            optical = optical_chain(kind, paper=dict(s_in=spin))
            actual = (optical["effective_analyzer"].H * tensor * optical["Ein"])[0]
            check(zero(sp.Matrix([sp.diff(actual, alpha)])), "A fixed circular channel unexpectedly scans.")
    for kind, target in [("CIRCULAR_LINEAR", (sp.cos(2*alpha),sp.sin(2*alpha),0)),
                         ("CUBIC_SIGMA", (-sp.sin(2*alpha),0,sp.cos(2*alpha))),
                         ("QWP", (0,-sp.sin(2*alpha),sp.cos(2*alpha)))]:
        state = optical_chain(kind, paper=dict(s_in=1,analyzer_zero_deg=0))["effective_analyzer"]
        x,y = state
        stokes = [x*sp.conjugate(x)-y*sp.conjugate(y), 2*sp.re(sp.conjugate(x)*y), 2*sp.im(sp.conjugate(x)*y)]
        check(all(zero(sp.Matrix([sp.trigsimp(sp.expand_complex(actual-wanted))])) for actual,wanted in zip(stokes,target)), kind+": detector Stokes trajectory differs from the guide.")
    values = [entry["intensity"].subs(alpha, sp.pi / 6) for entry in optical_profile_example()["profiles"].values()]
    check(all(not zero(sp.Matrix([a - b])) for i, a in enumerate(values) for b in values[i+1:]), "The declared same-tensor example does not distinguish the three scans.")
    check(set(optical_method_catalog()) == set(GENERAL_PROFILES), "The optical guide does not cover every menu choice.")
    return ["Optical-profile guide: general-complex-tensor VV/VH and interference identities, detector Stokes trajectories, matching custom states, fixed circular limits and a distinct same-tensor example pass."]
