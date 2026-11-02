# Reference analytical equation checks — Version 5



Revision: 2026-11-02-r1

**Reference:** Helicity-Dependent Raman Spectroscopy of Diamond and Zinc-Blende Crystal Structures; https://doi.org/10.1002/jrs.70113

**Result:** 22/22 defined checks passed.

Checked main-text algebra and 18 Si (5,k,0) configurations. The (5,k,0) formulas are derived reductions using the paper conventions, not quotations of unavailable SI equations. Other surfaces, every SI expression, other materials and experimental agreement are outside this report. Independent lab-member review remains pending.

The general Eq. (13) comparison assumes real symmetric tensor entries, as in the checked formula. The calculator retains full complex conjugation for complex coefficients. Frame angle, phase signs and scan-angle zero must agree before comparing polar plots.



## Eq. (13): general real symmetric 2×2 tensor

Exact polynomial reduction of |es† R ei|² minus the fully substituted paper expression is zero for arbitrary real a,b,c and θ,α,β,β′.

Residual: 0.0

$$\frac{a^{2}}{4} + \frac{b^{2}}{4} + \frac{c^{2}}{2} + \left(\frac{a^{2}}{2} - \frac{b^{2}}{2}\right) \cos{\left(\alpha \right)} \cos{\left(\alpha + 2 \theta \right)} + \left(\frac{a c}{2} - \frac{b c}{2}\right) \left(\sin{\left(2 \theta \right)} \cos{\left(\beta \right)} \cos{\left(2 \alpha + 2 \theta \right)} + \sin{\left(2 \alpha + 2 \theta \right)} \cos{\left(\beta^{\prime} \right)} \cos{\left(2 \theta \right)}\right) + \left(\frac{a c}{2} + \frac{b c}{2}\right) \left(\sin{\left(2 \theta \right)} \cos{\left(\beta \right)} + \sin{\left(2 \alpha + 2 \theta \right)} \cos{\left(\beta^{\prime} \right)}\right) + \left(\frac{a^{2}}{8} - \frac{a b \cos{\left(\beta - \beta^{\prime} \right)}}{4} + \frac{b^{2}}{8} - \frac{c^{2} \cos{\left(\beta + \beta^{\prime} \right)}}{4} - \frac{c^{2}}{4}\right) \cos{\left(2 \alpha + 4 \theta \right)} + \left(\frac{a^{2}}{8} + \frac{a b \cos{\left(\beta - \beta^{\prime} \right)}}{4} + \frac{b^{2}}{8} + \frac{c^{2} \cos{\left(\beta + \beta^{\prime} \right)}}{4} - \frac{c^{2}}{4}\right) \cos{\left(2 \alpha \right)}$$



## Eq. (11): conjugated detection state

Two independent complex-state substitutions check the signs of the incident and detected phases.

Residual: 0.0



## Eq. (14): (001) off-diagonal limit

Exact identity with d=1; a common complex d multiplies the intensity by |d|².

Residual: 0.0

$$\frac{\sin{\left(2 \theta \right)} \sin{\left(2 \alpha + 2 \theta \right)} \cos{\left(\beta + \beta^{\prime} \right)}}{2} - \frac{\cos{\left(2 \theta \right)} \cos{\left(2 \alpha + 2 \theta \right)}}{2} + \frac{1}{2}$$



## Si (500), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 0.0

$$\sin^{2}{\left(2 \theta \right)}$$



## Si (500), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 0.0

$$\cos^{2}{\left(2 \theta \right)}$$



## Si (500), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 0.0

$$\sin^{2}{\left(\alpha \right)}$$



## Si (510), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\sin^{2}{\left(2 \theta \right)} + \frac{25 \cos^{4}{\left(\theta \right)}}{169}$$



## Si (510), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\frac{25 \sin^{2}{\left(2 \theta \right)}}{676} + \cos^{2}{\left(2 \theta \right)}$$



## Si (510), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(\alpha \right)} - \frac{25 \sin{\left(2 \alpha \right)}}{676} + \frac{25}{676}$$



## Si (520), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\sin^{2}{\left(2 \theta \right)} + \frac{400 \cos^{4}{\left(\theta \right)}}{841}$$



## Si (520), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\frac{100 \sin^{2}{\left(2 \theta \right)}}{841} + \cos^{2}{\left(2 \theta \right)}$$



## Si (520), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\sin^{2}{\left(\alpha \right)} - \frac{100 \sin{\left(2 \alpha \right)}}{841} + \frac{100}{841}$$



## Si (530), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(2 \theta \right)} + \frac{225 \cos^{4}{\left(\theta \right)}}{289}$$



## Si (530), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\frac{225 \sin^{2}{\left(2 \theta \right)}}{1156} + \cos^{2}{\left(2 \theta \right)}$$



## Si (530), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 3.3306690738754696e-16

$$\sin^{2}{\left(\alpha \right)} - \frac{225 \sin{\left(2 \alpha \right)}}{1156} + \frac{225}{1156}$$



## Si (540), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(2 \theta \right)} + \frac{1600 \cos^{4}{\left(\theta \right)}}{1681}$$



## Si (540), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 2.220446049250313e-16

$$\frac{400 \sin^{2}{\left(2 \theta \right)}}{1681} + \cos^{2}{\left(2 \theta \right)}$$



## Si (540), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(\alpha \right)} - \frac{400 \sin{\left(2 \alpha \right)}}{1681} + \frac{400}{1681}$$



## Si (550), VV

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(2 \theta \right)} + \cos^{4}{\left(\theta \right)}$$



## Si (550), VH

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 3.3306690738754696e-16

$$\frac{\sin^{2}{\left(2 \theta \right)}}{4} + \cos^{2}{\left(2 \theta \right)}$$



## Si (550), SIGMA

Exact matrix-to-closed-form identity plus 361 numerical angles; paper axes and optical states, d=1, no normalization.

Residual: 4.440892098500626e-16

$$\sin^{2}{\left(\alpha \right)} - \frac{\sin{\left(2 \alpha \right)}}{4} + \frac{1}{4}$$



## Eqs. (4)-(6): all six measurement frames

Six exact comparisons with the paper frame; each satisfies TᵀT=I and det(T)=+1.

Residual: 0.0
