# Models and polarization

1. **New-san:** tensor rotation and polarization conventions from the paper and supplementary information.
2. **My PPT slide:** the slide calculation, with separate Ag Cartesian contributions.
3. **Dr. Kumar:** Jones matrix multiplication, extended to the XY block of the rotated crystal tensor.

Every model offers the same material list, orientation inputs, VV, VH and σ⁺α.
Changing the model keeps these inputs. For identical inputs, the complete-mode intensity must agree.
X, Y and Z are measurement axes, not Jones vectors. Review them and T before calculating intensity.


### VV: parallel linear states, scan θ

**Family:** Co-rotating linear states

**Scan:** θ: common incident/detector angle

**Preparation:** Linear input v(t), t=θ+θ₀

**Return optics:** Identity: no extra return plate

**Detection:** Linear analyzer parallel to the input

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=(\sigma^{+})^\dagger R_\perp E_i,\quad q=(\sigma^{-})^\dagger R_\perp E_i$$

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

### VH: crossed linear states, scan θ

**Family:** Co-rotating linear states

**Scan:** θ: common incident/detector angle

**Preparation:** Linear input v(t), t=θ+θ₀

**Return optics:** Identity: no extra return plate

**Detection:** Linear analyzer perpendicular to the input

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=(\sigma^{+})^\dagger R_\perp E_i,\quad q=(\sigma^{-})^\dagger R_\perp E_i$$

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

### σ⁺α reference: elliptical detection-state scan

**Family:** Circular input / elliptical detector

**Scan:** α: effective detection-state parameter

**Preparation:** Fixed σ⁺ input

**Return optics:** Identity in the effective-state representation

**Detection:** j(π/4+α, π/2), elliptical except at special angles

$$R_\perp=PT^TR_cTP^T,\quad e_s=B^\dagger e_{an},\quad I=|e_{an}^\dagger B R_\perp E_i|^2=|e_s^\dagger R_\perp E_i|^2$$

$$p=(\sigma^{+})^\dagger R_\perp E_i,\quad q=(\sigma^{-})^\dagger R_\perp E_i$$

$$E_i=\sigma^{+},\quad e_s=(\cos(\pi/4+\alpha),i\sin(\pi/4+\alpha))^T$$

$$e_s=\cos\alpha\,\sigma^{+}-\sin\alpha\,\sigma^{-}$$

$$\mathcal A_E=p\cos\alpha-q\sin\alpha$$

$$I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\operatorname{Re}(p q^*)\sin\alpha\cos\alpha$$

**Use for:** The cubic paper σ⁺α equations, its Fig. 1(c) benchmark and the declared slide-frame example.

**Equality check:** It equals custom Jones at θᵢ=45, βᵢ=90, θₛ₀=45, βₛ=90 degrees; source QWP endpoints agree up to phase, intermediate states generally differ.

**Physical distinction:** This implements Eq. (11) at θ=π/4 and β=β'=π/2. The paper calls α a polarizer angle, but its effective detector is not a bare linear state at the sample. An apparatus must be calibrated before identifying the two.

**Source scope:** Cited effective Jones parameterization; the p/q expansion is derived here from that state.

**References:** [Cubic Raman reference: Sec. 2.2, Eqs. (9), (11)](https://doi.org/10.1002/jrs.70113); [Jones calculus](https://doi.org/10.1364/JOSA.31.000488)

The actual current angles and Jones matrices are shown in the optical-state preview and calculated mathematical steps. A guide identity is not an experimental calibration.