# Version 4 - symbols, units and derivation references



Choose Full mathematics for all equations with one short symbol list at the end. Explained derivation keeps the detailed definitions and sources below each equation. This file collects the complete definitions for reference.



Angles are evaluated in radians; controls and angle CSV columns use degrees. Numerical Raman tensors use a declared relative coefficient scale, and plotted intensities use its square (a.u.). The physical susceptibility derivative has units set by the chosen phonon normal coordinate; no absolute detector calibration is inferred.



## $L;\ \mathbf a_0,\mathbf b_0,\mathbf c_0$

Direct-lattice matrix and its three column vectors, written in the crystal Cartesian basis. Unity values denote relative lattice lengths.

**Unit / convention:** one common length unit; or dimensionless relative lengths



## $h,k,l$

Surface Miller indices. They label a reciprocal-lattice normal; they are not Cartesian distances or wave numbers.

**Unit / convention:** dimensionless integers



## $u,v,w$

Direct-lattice direction indices defining the in-plane reference. The zone condition is hu+kv+lw=0.

**Unit / convention:** dimensionless integers



## $\mathbf g_{hkl}$

Unnormalized surface normal obtained from the reciprocal metric L to the power -T. This definition omits the conventional reciprocal-lattice factor 2 pi, which cancels on normalization.

**Unit / convention:** inverse common lattice-length unit



## $\mathbf t$

In-plane reference before normalization. With explicit uvw it is L(u,v,w); automatic X instead uses a projected unit reference.

**Unit / convention:** lattice-length unit for explicit uvw; dimensionless for automatic X



## $\mathbf X,\mathbf Y,\mathbf Z;\ \mathbf X_0,\mathbf Y_0$

Unit measurement axes written in crystal coordinates. Subscript 0 denotes the frame before the in-plane rotation.

**Unit / convention:** dimensionless



## $\hat{\mathbf Z}_{lab}$

The same measurement-normal direction expressed in measurement coordinates: (0,0,1). Use this representation with the measurement-frame projector P.

**Unit / convention:** dimensionless unit vector



## $s_n$

Chosen side of the reciprocal surface normal, +1 or -1.

**Unit / convention:** dimensionless



## $\psi$

In-plane rotation of the measurement axes about Z. It changes the frame rather than the optical scan state.

**Unit / convention:** rad in formulas; degree in the input form



## $T$

Real proper orthogonal matrix whose columns are X, Y, Z in crystal coordinates. It maps measurement components to crystal components; its inverse is its transpose.

**Unit / convention:** dimensionless



## $\Pi(\psi)$

Three-dimensional rotation about the measurement Z axis used to update the frame.

**Unit / convention:** dimensionless matrix



## $\mathbf v_c,\mathbf v_{lab}$

Components of the same arbitrary vector in crystal and measurement coordinates.

**Unit / convention:** same units as the vector being represented



## $\mathbf e_{ref};\ \mathbf e_x,\mathbf e_y,\mathbf e_z;\ \hat x$

Cartesian unit basis vectors. The ref label is the reference used by automatic X; x,y,z refer to crystal axes in the tensor decomposition.

**Unit / convention:** dimensionless



## $R_c,R_{lab},R_\perp,R_{ref}$

Raman tensor in crystal, measurement, transverse or effective-reference coordinates. Matrix subscripts give entries; j labels the phonon partner. R_perp is 2 by 2 after the full 3 by 3 rotation.

**Unit / convention:** relative tensor-coefficient units in this program



## $R_\chi^{(m)}$

Physical Raman tensor defined by the derivative of susceptibility with respect to the declared normal coordinate of mode m. Its units depend on that coordinate's normalization.

**Unit / convention:** reciprocal unit of the normal coordinate u_m



## $P$

2 by 3 transverse selector [[1,0,0],[0,1,0]] in measurement coordinates. Its transpose embeds a Jones vector in three dimensions.

**Unit / convention:** dimensionless



## $I_3$

3 by 3 identity matrix; this I is not Raman intensity.

**Unit / convention:** dimensionless



## $E_i,E_{i,lab},E_{i,c}$

Normalized incident Jones state and its three-dimensional embeddings in measurement and crystal coordinates. Overall incident field strength is omitted.

**Unit / convention:** dimensionless



## $e,e_s,e_{an}$

Unit Jones polarization state; s is the effective detector at the sample and an is the analyzer after return optics. The amplitude uses the conjugate transpose of the detection state.

**Unit / convention:** dimensionless



## $B$

Jones matrix of the return optical path. The effective detector is B dagger times e_an.

**Unit / convention:** dimensionless



## $Q;\ \mathrm{Rot}$

Quarter-wave-plate Jones matrix and real transverse rotation matrix. For the supplied Kumar convention the plate angle is -pi/4 and the return matrix is Q transpose.

**Unit / convention:** dimensionless matrices; their angle arguments are in rad



## $\sigma^+,\sigma^-$

Normalized fixed-XY circular basis vectors (1,+i)/sqrt(2) and (1,-i)/sqrt(2). A superscript sign labels a state rather than a charge with SI units.

**Unit / convention:** dimensionless



## $\vartheta$

Jones mixing angle setting the magnitudes of the two transverse components. For a real linear state it is the polarization angle.

**Unit / convention:** rad in formulas; degree in direct-state inputs



## $\theta;\ \theta_i,\theta_s$

Theta is the common linear-polarization scan angle for VV/VH. In the general direct-state product, theta_i and theta_s instead denote the incident and detection mixing angles.

**Unit / convention:** rad in formulas; degree in input and angle CSV columns



## $\alpha$

Detection-state scan angle of the selected optical profile. A direct linear analyzer, the return-QWP chain and the elliptical reference use different Jones-state definitions.

**Unit / convention:** rad in formulas; degree in input and angle CSV columns



## $\beta,\beta^\prime;\ \beta_i,\beta_s$

Relative phase of Y with respect to X. The reference uses beta for the incident state and beta prime for the detected state; direct controls use the i and s subscripts.

**Unit / convention:** rad in formulas; degree in the input form



## $\delta,\phi$

Phases in the supplied effective 2D source tensor. Delta belongs to its off-diagonal term; phi belongs to its yy term.

**Unit / convention:** rad in formulas; degree in the effective-source controls



## $\phi_a,\phi_b$

Phase of the indicated complex tensor coefficient, relative to the chosen reference phase.

**Unit / convention:** rad in formulas; degree in coefficient controls



## $\rho_a,\rho_b$

Nonnegative magnitude of the indicated complex tensor coefficient.

**Unit / convention:** same relative units as its tensor coefficient



## $a,b,c,d,e,f$

Independent complex tensor coefficients in the selected symmetry form. Only symbols actually used in this equation are active. For Si T2g the three partner tensors share d.

**Unit / convention:** relative tensor-coefficient units



## $A$

Real off-diagonal reference amplitude in Kumar's effective 2D tensor; it is distinct from the detected amplitude written as calligraphic A.

**Unit / convention:** same relative coefficient units as source a



## $a$

Real diagonal reference amplitude in Kumar's effective 2D tensor. It is distinct from a generally complex crystal coefficient named a.

**Unit / convention:** relative source tensor-coefficient units



## $q$

Coefficient of the selected Ag rank-one Cartesian contribution: a for xx, b for yy or c for zz. It is not a phonon normal coordinate.

**Unit / convention:** relative tensor-coefficient units



## $\mathbf p;\ \mathbf v,v_x,v_y$

Crystal unit axis expressed in measurement coordinates, then restricted to XY. The projected vector need not have unit length.

**Unit / convention:** dimensionless



## $G,G_i,G_s;\ \eta_i,\eta_s$

Eta denotes an incident or detector overlap amplitude. G is its nonnegative squared magnitude; active means evaluated with the actual selected optical chain.

**Unit / convention:** dimensionless



## $E_{sc},E_{out};\ \mathcal P_c,\mathcal P_{lab}$

Reduced scattered/returned field and induced-response amplitudes calculated from a relative tensor and unit Jones state. These are not calibrated SI electric fields or polarization densities.

**Unit / convention:** relative tensor-coefficient units



## $\mathcal A,\mathcal A_j$

Detected complex Raman scattering amplitude. A j subscript identifies one orthogonal phonon partner; a Cartesian label identifies one tensor contribution.

**Unit / convention:** relative tensor-coefficient units



## $C,D;\ K_0,K_c,K_s$

Complex coefficients of the first-harmonic or second-harmonic amplitude expansion. Subscripts 0,c,s mean constant, cosine and sine; a further j denotes a partner.

**Unit / convention:** same units as the detected amplitude



## $I,I_j;\ I_0,I_c,I_s,I_{4c},I_{4s};\ I_{min},I_{max}$

Relative intensity, its real harmonic coefficients and extrema. The final j sum adds intensities of unresolved orthogonal phonon partners. Coherent tensor terms within one partner are added before squaring.

**Unit / convention:** squared relative tensor-coefficient units, plotted as a.u.



## $\alpha_{max},\theta_{max}$

An angle at a continuous intensity maximum, obtained from the harmonic expression. It need not fall on the sampled grid; a constant curve has no unique extremum angle.

**Unit / convention:** degree when explicitly labeled degree; otherwise rad



## $\Delta$

Nonnegative modulation magnitude sqrt(I_c squared + I_s squared) for a first-harmonic scan. This uppercase Delta is distinct from the source phase delta.

**Unit / convention:** same relative units as intensity



## $u_1,u_2;\ z$

Complex intensity-harmonic coefficients used only to find second-harmonic stationary points, and the unit-circle variable z=exp(2 i theta). These u symbols are not phonon coordinates.

**Unit / convention:** u_1,u_2: intensity units; z: dimensionless



## $\chi_{ij},\chi_{ij}^{(0)}$

Electric susceptibility component and its equilibrium value. Cartesian indices identify the field and induced-polarization components.

**Unit / convention:** dimensionless in SI



## $u_m$

Generalized phonon normal coordinate for branch m, equivalent to the q^mu notation in Pimenta Eq. (2). The program does not prescribe its displacement or mass normalization.

**Unit / convention:** chosen normal-coordinate unit; e.g. m for a displacement, or kg^(1/2) m if mass weighted



## $\epsilon_0$

Vacuum electric permittivity in the physical susceptibility relation.

**Unit / convention:** F m^-1 in SI



## $\mathbf E_{i,c}^{\mathrm{phys}}$

Physical incident electric-field amplitude expressed in crystal coordinates. It includes the incident field magnitude omitted from the unit Jones vector.

**Unit / convention:** V m^-1 in SI



## $\mathbf E$

Optical electric field in the transversality condition k dot E = 0. The same orthogonality condition holds for its normalized polarization direction.

**Unit / convention:** V m^-1 for the physical field; a unit polarization direction is dimensionless



## $\mathbf P_R^{\mathrm{phys},(m)}$

Physical Raman-induced electric polarization density of phonon m. It includes epsilon_0, the physical field and the normal-coordinate displacement.

**Unit / convention:** C m^-2 in SI



## $I_m^{\mathrm{physical}};\ \kappa_m$

Physical measured intensity and its proportionality factor relative to the squared reduced amplitude. Kappa includes omitted field, phonon and collection factors and is not calculated here.

**Unit / convention:** chosen measured-intensity unit; kappa: that unit divided by squared relative coefficient units



## $\mathbf k_i,\mathbf k_s;\ k_i,k_s$

Incident and scattered propagation vectors and their nonnegative magnitudes, written in measurement coordinates. Only their directions are used in this plane-wave calculation.

**Unit / convention:** m^-1 for physical wavevectors; not numerically predicted here



## $S_3;\ h_i,h_s$

Normalized circular Stokes component and propagation-relative helicity expectation. With incident propagation along -Z and detection along +Z, h_i=-S_3 and h_s=+S_3.

**Unit / convention:** dimensionless; pure circular states have values +1 or -1



## $\epsilon_{direct},\epsilon_{circular}$

Maximum absolute intensity residual between equivalent matrix/basis representations, evaluated using the same tensor and actual optical states. These epsilon symbols are not epsilon_0.

**Unit / convention:** same relative units as unnormalized intensity



## $i,j,k,l;\ m,n$

In matrix entries and contraction sums, indices run over Cartesian components. In an amplitude/partner sum, j labels a phonon partner and m,n label coherent terms. These index roles are local, not extra fitted parameters.

**Unit / convention:** dimensionless labels or integer indices



## $i$

Imaginary unit, i squared = -1. It is distinct from the incident-state subscript i and Cartesian summation indices.

**Unit / convention:** dimensionless



## $\pi$

Circle constant used in angle conversion and special-angle states.

**Unit / convention:** dimensionless; angle multiples are in rad



## $\exp$

Complex exponential. The e in an exponential is Euler's number, distinct from a tensor coefficient named e. Its exponent is dimensionless.

**Unit / convention:** dimensionless



## ${}^T;\ {}^{-T};\ {}^{-1}$

Matrix transpose, inverse transpose and inverse. A superscript T is an operation; a standalone T is the frame matrix.

**Unit / convention:** operation; dimensions follow the operand



## ${}^*,\overline{\phantom a};\ {}^\dagger$

Complex conjugation and conjugate transpose. The detection state must be conjugated before contraction.

**Unit / convention:** operation; conjugation preserves units



## $|\cdot|;\ \|\cdot\|$

Complex modulus or Euclidean vector norm. Squaring a modulus squares the units of its argument.

**Unit / convention:** same units as the argument before squaring



## $\cdot;\ \times;\ \sum$

Dot product, vector cross product and explicit sum. Their domains are given by the adjacent vector definitions or index limits.

**Unit / convention:** products multiply units; sums require matching units



## $\operatorname{Re},\operatorname{Im};\ \arg$

Real part, imaginary part and complex phase. The argument of a nonzero coefficient is its relative phase.

**Unit / convention:** Re/Im: operand units; arg: rad



## $d/d\theta;\ d/d\alpha;\ \partial$

Derivative with respect to the indicated angle or normal coordinate. A derivative divides the numerator's units by the differentiation variable's units.

**Unit / convention:** intensity per rad for dI/dangle; reciprocal coordinate unit for dchi/du



## $\det$

Determinant. A proper frame has det(T)=+1 and T transpose times T equals the identity.

**Unit / convention:** dimensionless for a rotation matrix



## $O(u^2)$

Terms of second and higher order in the normal-coordinate expansion, omitted in the first-order Raman model.

**Unit / convention:** same susceptibility units as the retained Taylor series



## $\left.\cdot\right|_0$

Evaluate the derivative at the equilibrium normal coordinate u_m=0. This vertical bar denotes evaluation, not a modulus.

**Unit / convention:** operation; preserves the derivative's units



## $\operatorname{atan2};\ \pmod\pi$

Quadrant-aware inverse tangent and angular equivalence modulo pi, used for a first-harmonic extremum.

**Unit / convention:** rad; modulo-pi angles repeat after 180 degrees



## Reference map



### Pimenta et al. (2021)

Polarized Raman spectroscopy in low-symmetry 2D materials: angle-resolved experiments and complex number tensor elements

Section 1.1, Eqs. (1)-(4); Section 1.2; linear-polarization discussion in Section 2

Physical susceptibility derivative, mode-specific Raman tensors, relative intensity and complex coefficients. Supplied PDF pp. 3-5 checked directly.

https://doi.org/10.1039/D1CP03626B



### Paukatong et al. (2026)

Helicity-Dependent Raman Spectroscopy of Diamond and Zinc-Blende Crystal Structures

Section 2.1, Eqs. (1)-(6); Section 2.2, Eqs. (9) and (11)

Si T2g tensors, cubic surface axes, tensor rotation, summed orthogonal partners and complex polarization states. Supplied PDF pp. 2-4 checked directly.

https://doi.org/10.1002/jrs.70113



### Kumar-san, supplied original notebook (2026-10-15)

Raman intensity with the modified Raman tensor, original Version 2.0

Original Cells 2-11 and the separately labeled appendix

Jones basis, quarter-wave plate, return-optic convention, conjugate detection and the effective 2D reference. This supplied notebook is a project source, not a journal article.

https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/Dr_Kumar_Original.ipynb



### NIST, Guide to the SI, Section 7.10

Values of quantities expressed simply as numbers: the unit one

Section 7.10: dimension-one quantities and the radian

Unit conventions; the form converts degrees to radians before evaluation.

https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-7-rules-and-style-conventions-expressing-values



### IUPAC Gold Book, polarization density

Polarization density

Definition P = epsilon_0 chi E

SI polarization density, electric field and dimensionless electric susceptibility.

https://goldbook.iupac.org/terms/view/08856



### Program coordinate derivation, Cells 3 and 12

Reciprocal metric, orthonormal frame and component transformation

Displayed matrix definitions and their direct products

L^-T is the dual-basis construction. The general noncubic metric and explicit substitutions are program derivations; they are not quoted equations from the cubic paper.



### Program algebra, Cells 6, 11 and 12

Contraction, conjugate product, harmonics and stationary points

Algebra of the displayed tensors and Jones states

Matrix products, rank-one overlap factors, trigonometric expansions and extrema are derived here from the stated definitions. They are checked against direct numerical contractions.

