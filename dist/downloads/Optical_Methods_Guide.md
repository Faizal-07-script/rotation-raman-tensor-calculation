## Choose the optical experiment before comparing curves

All choices use the same complex-amplitude law. Changing a preparation, detector or scan changes the measured quantity. Select the profile that matches calibrated optics, or the exact states of a reference figure.

| Profile | Scanned quantity | Detection at the sample |

|---|---|---|

| VV: parallel linear states, scan theta | theta: common incident/detector angle | Linear analyzer parallel to the input |

| VH: crossed linear states, scan theta | theta: common incident/detector angle | Linear analyzer perpendicular to the input |

| VV and VH together, one coefficient set | theta: one common angle for both channels | Calculate parallel and perpendicular analyzers separately |

| Circular input / direct linear analyzer, scan alpha | alpha: linear-analyzer angle only | v(alpha+alpha0), with a calibrated analyzer zero |

| sigma+alpha reference: elliptical detection-state scan | alpha: effective detection-state parameter | j(pi/4+alpha, pi/2), elliptical except at special angles |

| Input QWP / Raman tensor / return QWP / linear analyzer | alpha: physical linear analyzer after the return plate | Linear analyzer (-sin alpha, cos alpha) after B; effective detector B.H times analyzer |

| Same fixed circular basis label | None: both sample states are fixed | Fixed sigma_s detector |

| Opposite fixed circular basis label | None: both sample states are fixed | Fixed sigma_-s detector |

| Custom direct Jones input and detection states | alpha: theta_s0+alpha; input and phase controls fixed | j(theta_s0+alpha,beta_s) |



### Same tensor, different interference

$$p=\sigma_+^\dagger R_\perp\sigma_+,\quad q=\sigma_-^\dagger R_\perp\sigma_+$$

$$I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\mathrm{Re}(p q^*)\sin\alpha\cos\alpha$$

$$I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\mathrm{Im}(p q^*)\sin\alpha\cos\alpha$$

$$I_{CL}=\tfrac12(|p|^2+|q|^2)+\mathrm{Re}(p q^*e^{2i(\alpha+\alpha_0)})$$

These equations are derived from the implemented sample states. The continuous circular-input/linear-detector scan is a Jones extension, not a quantitative prediction of the vortex selection-rule paper.

### What is a reference?

Use the elliptical reference for the cubic paper Fig. 1(c) and the declared slide-frame example; use the explicit QWP chain for the uploaded optical notebook; use VV/VH for the corresponding linear measurements. A CaNb2O6 material label alone does not determine a detector state. Keep lattice metric, surface axes, coefficients, angle zeros and Ag component/coherent-mode policy identical when comparing results.

### Fixed labels and physical helicity

$$\mathbf k_i=-k_i\hat Z,\quad\mathbf k_s=+k_s\hat Z,\quad S_3=2\mathrm{Im}(E_X^*E_Y),\quad h_i=-S_3(E_i),\quad h_s=S_3(e_s)$$

The physical sign above uses exp[i(k.r-omega t)] and fixed laboratory XY components. Reference papers can attach conserved/changing names to different beam-coordinate conventions. Match those conventions before comparing names. Fixed circular states give constant intensity when the sample is not rotated.

### Ag presentation

Ag(xx), Ag(yy) and Ag(zz) remain separate contribution powers in the main plots. A complete single-phonon intensity is the squared sum of its component amplitudes; orthogonal unresolved phonon partners instead contribute a sum of powers. These are separate choices from the optical profile.

### VV: parallel linear states, scan theta

**Family:** Co-rotating linear states

**Scan:** theta: common incident/detector angle

**Preparation:** Linear input v(t), t=theta+theta0

**Return optics:** Identity: no extra return plate

**Detection:** Linear analyzer parallel to the input

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$v(t)=(\cos t,\sin t)^T$$

$$E_i=v(t),\quad e_s=v(t),\quad B=I_2$$

$$\mathcal A_{VV}=v(t)^\dagger R_\perp v(t)$$

$$I_{VV}=|r_{xx}\cos^2t+(r_{xy}+r_{yx})\sin t\cos t+r_{yy}\sin^2t|^2$$

**Use for:** Parallel linear measurements and the VV member of the cubic benchmark.

**Equality check:** The paired VV/VH choice must reproduce this VV channel with identical inputs.

**Physical distinction:** Both linear states rotate together in the fixed-tensor coordinates. This represents a sample-angle experiment with a declared sign convention; do not also rotate the tensor by the same scan angle.

**Source scope:** Direct specialization of the cited contraction and linear states.

**References:** [Complex Raman tensors: Eq. (3), Eqs. (13a-d)](https://doi.org/10.1039/D1CP03626B); [Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)](https://doi.org/10.1002/jrs.70113)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### VH: crossed linear states, scan theta

**Family:** Co-rotating linear states

**Scan:** theta: common incident/detector angle

**Preparation:** Linear input v(t), t=theta+theta0

**Return optics:** Identity: no extra return plate

**Detection:** Linear analyzer perpendicular to the input

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$v(t)=(\cos t,\sin t)^T$$

$$w(t)=(-\sin t,\cos t)^T$$

$$E_i=v(t),\quad e_s=w(t),\quad B=I_2$$

$$\mathcal A_{VH}=w(t)^\dagger R_\perp v(t)$$

$$I_{VH}=|r_{yx}\cos^2t-r_{xy}\sin^2t+(r_{yy}-r_{xx})\sin t\cos t|^2$$

**Use for:** Crossed linear measurements and the VH member of the cubic benchmark.

**Equality check:** The paired VV/VH choice must reproduce this VH channel with identical inputs.

**Physical distinction:** Both linear states rotate together in the fixed-tensor coordinates. This represents a sample-angle experiment with a declared sign convention; do not also rotate the tensor by the same scan angle.

**Source scope:** Direct specialization of the cited contraction and crossed states.

**References:** [Complex Raman tensors: Eq. (3), Eqs. (13a-d)](https://doi.org/10.1039/D1CP03626B); [Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)](https://doi.org/10.1002/jrs.70113)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### VV and VH together, one coefficient set

**Family:** Co-rotating linear states

**Scan:** theta: one common angle for both channels

**Preparation:** One linear input and one shared coefficient set

**Return optics:** Identity for both channels

**Detection:** Calculate parallel and perpendicular analyzers separately

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$v(t)=(\cos t,\sin t)^T$$

$$w(t)=(-\sin t,\cos t)^T$$

$$E_i=v(t),\quad e_s^{VV}=v(t),\quad e_s^{VH}=w(t)$$

$$\mathcal A_{VV}=v^\dagger R_\perp v,\quad\mathcal A_{VH}=w^\dagger R_\perp v$$

$$I_{VV}=|\mathcal A_{VV}|^2,\quad I_{VH}=|\mathcal A_{VH}|^2$$

**Use for:** Comparing VV and VH for the same phonon coefficients, surface and angular zero.

**Equality check:** This is a paired output, not a third polarization law. Each raw curve equals its standalone channel.

**Physical distinction:** Both linear states rotate together in the fixed-tensor coordinates. This represents a sample-angle experiment with a declared sign convention; do not also rotate the tensor by the same scan angle.

**Source scope:** Two instances of the same Jones engine; powers are not added to define a new channel.

**References:** [Complex Raman tensors: Eq. (3), Eqs. (13a-d)](https://doi.org/10.1039/D1CP03626B); [Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)](https://doi.org/10.1002/jrs.70113)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### Circular input / direct linear analyzer, scan alpha

**Family:** Circular input / linear detector

**Scan:** alpha: linear-analyzer angle only

**Preparation:** Fixed circular input sigma_s

**Return optics:** Identity: the detector state at the sample is linear

**Detection:** v(alpha+alpha0), with a calibrated analyzer zero

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$\sigma_s=(1,is)^T/\sqrt{2},\quad s=\pm1$$

$$E_i=\sigma_s,\quad e_s=v(\alpha+\alpha_0),\quad B=I_2$$

$$\mathcal A_{CL}=\frac{p e^{it}+q e^{-it}}{\sqrt{2}},\quad t=\alpha+\alpha_0$$

$$I_{CL}=\frac{|p|^2+|q|^2}{2}+\operatorname{Re}(p q^*e^{2it})$$

**Use for:** Circular illumination with a linear effective detector at the sample.

**Equality check:** For sigma+ input it equals custom Jones with theta_i=45, beta_i=90, theta_s0=alpha0 and beta_s=0 degrees.

**Physical distinction:** A bare linear-analyzer scan does not select pure sigma+ or sigma- endpoints. A return QWP changes the effective detector.

**Source scope:** Program Jones-calculus extension. The circular selection-rule paper does not prescribe this continuous scan or its quantitative intensity.

**References:** [Jones calculus](https://doi.org/10.1364/JOSA.31.000488); [Circular selection rules: Eqs. (21-24)](https://doi.org/10.1039/D1CP02209A)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### sigma+alpha reference: elliptical detection-state scan

**Family:** Circular input / elliptical detector

**Scan:** alpha: effective detection-state parameter

**Preparation:** Fixed sigma+ input

**Return optics:** Identity in the effective-state representation

**Detection:** j(pi/4+alpha, pi/2), elliptical except at special angles

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$E_i=\sigma_+,\quad e_s=(\cos(\pi/4+\alpha),i\sin(\pi/4+\alpha))^T$$

$$e_s=\cos\alpha\,\sigma_+-\sin\alpha\,\sigma_-$$

$$\mathcal A_E=p\cos\alpha-q\sin\alpha$$

$$I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\operatorname{Re}(p q^*)\sin\alpha\cos\alpha$$

**Use for:** The cubic paper sigma+alpha equations, its Fig. 1(c) benchmark and the declared slide-frame example.

**Equality check:** It equals custom Jones at theta_i=45, beta_i=90, theta_s0=45, beta_s=90 degrees; source QWP endpoints agree up to phase, intermediate states generally differ.

**Physical distinction:** This implements Eq. (11) at theta=pi/4 and beta=beta'=pi/2. The paper calls alpha a polarizer angle, but its effective detector is not a bare linear state at the sample. An apparatus must be calibrated before identifying the two.

**Source scope:** Cited effective Jones parameterization; the p/q expansion is derived here from that state.

**References:** [Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)](https://doi.org/10.1002/jrs.70113); [Jones calculus](https://doi.org/10.1364/JOSA.31.000488)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### Input QWP / Raman tensor / return QWP / linear analyzer

**Family:** Circular input / explicit return optics

**Scan:** alpha: physical linear analyzer after the return plate

**Preparation:** Lab-X input through Q=Rot(-pi/4) diag(1,i) Rot(-pi/4)^T

**Return optics:** B=Q.T in the uploaded source basis convention

**Detection:** Linear analyzer (-sin alpha, cos alpha) after B; effective detector B.H times analyzer

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$Q=\frac12\begin{pmatrix}1+i&-1+i\\-1+i&1+i\end{pmatrix},\quad E_i=Qe_X=e^{i\pi/4}\sigma_+$$

$$e_{an}=(-\sin\alpha,\cos\alpha)^T,\quad B=Q^T,\quad e_s=B^\dagger e_{an}$$

$$e_s\sim\cos\alpha\,\sigma_+-i\sin\alpha\,\sigma_-$$

$$\mathcal A_Q\sim p\cos\alpha+i q\sin\alpha$$

$$I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\operatorname{Im}(p q^*)\sin\alpha\cos\alpha$$

**Use for:** The uploaded QWP optical sequence, after its axes, return-path convention and analyzer zero are verified.

**Equality check:** At alpha=0 and pi/2 the circular endpoints equal the elliptical reference in power; intermediate intensities generally need not match.

**Physical distinction:** Q.T is a declared source convention, not a universal reverse-path rule. Keep either the explicit B or its effective detector, never both. The crystal tensor remains 3x3 before transverse restriction.

**Source scope:** Exact uploaded optical chain plus a program-derived p/q identity valid for any supplied R_perp under that chain.

**References:** Uploaded Version 2 QWP implementation reference (included original notebook); [Jones calculus](https://doi.org/10.1364/JOSA.31.000488)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### Same fixed circular basis label

**Family:** Fixed circular channels

**Scan:** None: both sample states are fixed

**Preparation:** Fixed sigma_s input

**Return optics:** Identity in the effective-state representation

**Detection:** Fixed sigma_s detector

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$\sigma_s=(1,is)^T/\sqrt{2},\quad s=\pm1$$

$$E_i=\sigma_s,\quad e_s=\sigma_s$$

$$\mathcal A_{same}=\sigma_s^\dagger R_\perp\sigma_s$$

$$I_{same}=|\sigma_s^\dagger R_\perp\sigma_s|^2$$

**Use for:** A fixed same-basis circular channel; compare helicity labels only after reconciling beam directions.

**Equality check:** The curve is constant when tensor, orientation and optical states remain fixed; a polar circle is a display of that constant.

**Physical distinction:** Same fixed XY circular label is not automatically conserved propagation-relative helicity in backscattering. This profile does not rotate the sample.

**Source scope:** Fixed-state tensor contraction; the separate angular-momentum rule is conditional and does not set curve heights.

**References:** [Circular selection rules: Eqs. (21-24)](https://doi.org/10.1039/D1CP02209A); [Jones calculus](https://doi.org/10.1364/JOSA.31.000488)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### Opposite fixed circular basis label

**Family:** Fixed circular channels

**Scan:** None: both sample states are fixed

**Preparation:** Fixed sigma_s input

**Return optics:** Identity in the effective-state representation

**Detection:** Fixed sigma_-s detector

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$\sigma_s=(1,is)^T/\sqrt{2},\quad s=\pm1$$

$$E_i=\sigma_s,\quad e_s=\sigma_{-s}$$

$$\mathcal A_{opposite}=\sigma_{-s}^\dagger R_\perp\sigma_s$$

$$I_{opposite}=|\sigma_{-s}^\dagger R_\perp\sigma_s|^2$$

**Use for:** A fixed opposite-basis circular channel, with an explicit propagation convention.

**Equality check:** The curve is constant under this fixed experiment. Its power is the opposite-basis circular channel, not an alpha sweep.

**Physical distinction:** Opposite fixed XY circular labels can represent conserved physical helicity for counterpropagating beams. Match the reference's basis before assigning conserved/changing names.

**Source scope:** Fixed-state tensor contraction, distinct from a spatial vortex-intensity calculation.

**References:** [Circular selection rules: Eqs. (21-24)](https://doi.org/10.1039/D1CP02209A); [Jones calculus](https://doi.org/10.1364/JOSA.31.000488)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.

### Custom direct Jones input and detection states

**Family:** Custom effective states

**Scan:** alpha: theta_s0+alpha; input and phase controls fixed

**Preparation:** j(theta_i,beta_i), selected by the user

**Return optics:** Identity: any return optics must already be included in e_s

**Detection:** j(theta_s0+alpha,beta_s)

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=\sigma_+^\dagger R_\perp E_i,\quad q=\sigma_-^\dagger R_\perp E_i$$

$$j(t,\beta)=(\cos t,e^{i\beta}\sin t)^T$$

$$E_i=j(\theta_i,\beta_i),\quad e_s=j(\theta_{s0}+\alpha,\beta_s),\quad B=I_2$$

$$\mathcal A_J=j(\theta_{s0}+\alpha,\beta_s)^\dagger R_\perp j(\theta_i,\beta_i)$$

$$I_J=|\mathcal A_J|^2$$

**Use for:** Calibrated effective states or exact checks of the matching preset parameters.

**Equality check:** It reproduces a preset only when both effective states and their scan laws agree up to global phase; an arbitrary waveplate path need not fit this restricted constant-beta scan.

**Physical distinction:** Changing beta_s changes relative phase and interference. This custom profile keeps the input fixed, so it does not in general reproduce co-rotating VV/VH scans.

**Source scope:** User-defined specialization of the common contraction, not a separate material law.

**References:** [Jones calculus](https://doi.org/10.1364/JOSA.31.000488); [Complex Raman tensors: Eq. (3), Eqs. (13a-d)](https://doi.org/10.1039/D1CP03626B)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.