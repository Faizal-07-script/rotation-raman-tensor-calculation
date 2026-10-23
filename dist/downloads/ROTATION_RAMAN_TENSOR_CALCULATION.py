"""261024 - Raman Tensor Rotation Ver 4.0.
Complete notebook source, version 4.
Run with an IPython/Jupyter kernel for the interactive widget application.
The .ipynb notebook is the recommended entry point.
"""

# %% Code cell 1: Setup
PROGRAM_VERSION = "4"
NOTEBOOK_REVISION = "2026-10-24-r1"
print(f"Version {PROGRAM_VERSION} | Revision {NOTEBOOK_REVISION} | Silicon (500) default", flush=True)
print("This notebook has 22 code cells. Run them in order; each completed cell reports its own success.", flush=True)

# Prepare packages only when the current kernel does not already provide them.
import importlib.util
import subprocess
import sys

required = ["sympy", "numpy", "matplotlib", "ipywidgets"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
try:
    from google.colab import output as colab_output

    colab_output.enable_custom_widget_manager()
except ImportError:
    pass
try:
    get_ipython().run_line_magic("matplotlib", "inline")
except (NameError, NotImplementedError):
    pass

print("Cell 01/22 — Run completed successfully.\nReady: The Python environment and notebook display are ready.\nNext: Run Cell 02.", flush=True)


# %% Code cell 2: Numerical helpers and figure style
"""Shared symbols and small numerical helpers. No material model is selected here."""

import base64
import copy
import csv
import html
import io
import json
import math
import traceback
import zipfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from IPython.display import HTML, Markdown, Math, clear_output, display
from matplotlib.ticker import MaxNLocator

sp.init_printing()
plt.rcParams.update({"figure.dpi": 115, "font.size": 10})

# α is the detection scan angle. ψ, introduced by the geometry input,
# rotates the in-plane measurement frame and is a different operation.
alpha = sp.symbols("alpha", real=True)
a, b, c, d, e, f = sp.symbols("a b c d e f", complex=True)


def real_number(value, name="Value"):
    """Convert a real, finite scalar to float; reject unresolved or complex input."""
    try:
        number = complex(sp.N(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a numerical scalar.") from exc
    if not np.isfinite(number) or abs(number.imag) > 1e-12:
        raise ValueError(f"{name} must be real and finite.")
    return number.real


def exact(value):
    """Preserve a finite decimal input as a rational number for symbolic work."""
    number = real_number(value)
    return sp.Rational(str(number))


def deg(value):
    """Convert degrees to radians without discarding exact special angles."""
    return sp.sympify(value) * sp.pi / 180


def numeric(matrix):
    """Evaluate a resolved SymPy matrix as a complex NumPy array."""
    return np.asarray(sp.Matrix(matrix).evalf(), dtype=complex)


def zero(matrix):
    """Check an exact symbolic identity; used for algebraic validation."""
    return all(sp.simplify(sp.expand(value)) == 0 for value in sp.Matrix(matrix))


def tidy(expression):
    """Apply local expansion/factoring, avoiding costly global trig searches."""
    if isinstance(expression, sp.MatrixBase):
        return expression.applyfunc(tidy)
    return sp.factor_terms(sp.expand(expression))


def complex_parameter(magnitude, phase_deg):
    """Build a complex tensor coefficient from magnitude and phase in degrees."""
    magnitude = real_number(magnitude, "Coefficient magnitude")
    phase_deg = real_number(phase_deg, "Coefficient phase")
    if magnitude < 0:
        raise ValueError("Coefficient magnitudes must be nonnegative.")
    return exact(magnitude) * sp.exp(sp.I * deg(exact(phase_deg)))


def parse_complex(value):
    """Read a numerical custom-tensor entry, e.g. '1+0.2j'; never evaluate code."""
    try:
        number = complex(str(value).replace("I", "j"))
    except ValueError as exc:
        raise ValueError(f"Invalid complex tensor entry: {value!r}.") from exc
    if not np.isfinite(number):
        raise ValueError("Custom tensor entries must be finite.")
    return exact(number.real) + sp.I * exact(number.imag)


def serializable(value):
    """Convert a configuration/result to JSON-safe, explicitly named data."""
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serializable(item) for item in value]
    if isinstance(value, sp.MatrixBase):
        return [[str(item) for item in row] for row in value.tolist()]
    if isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, np.ndarray):
        return serializable(value.tolist())
    if isinstance(value, np.generic):
        return serializable(value.item())
    if isinstance(value, complex):
        return {"real": value.real, "imaginary": value.imag}
    return value


def check(condition, message):
    """Raise an informative validation error even when Python runs with -O."""
    if not condition:
        raise AssertionError(message)


"""The supplied sci.mplstyle, with explicit local-font provenance."""
import tempfile
import matplotlib as mpl
from matplotlib import font_manager

SCI_STYLE_TEXT = r"""# Transcribed from the four supplied sci.mplstyle screenshots.
figure.figsize: 6.5, 5
font.family: Arial
font.size: 22
mathtext.default: regular
axes.titlesize: medium
axes.titlepad: 10
axes.titleweight: normal
axes.linewidth: 2
axes.labelpad: 10
axes.prop_cycle: cycler(color=['1f77b4','d62728','2ca02c','ff7f0e','9467bd','8c564b','e377c2','7f7f7f','bcbd22','17becf'])
xtick.top: True
xtick.direction: in
xtick.major.size: 9
xtick.major.width: 2
xtick.major.pad: 4
xtick.minor.visible: True
xtick.minor.size: 6
xtick.minor.width: 2
xtick.minor.pad: 4
ytick.right: True
ytick.direction: in
ytick.major.size: 9
ytick.major.width: 2
ytick.major.pad: 4
ytick.minor.visible: True
ytick.minor.size: 6
ytick.minor.width: 2
ytick.minor.pad: 4
lines.linewidth: 2
lines.markersize: 10
legend.framealpha: 1
legend.frameon: False
legend.fontsize: 19
savefig.dpi: 600
savefig.format: pdf
savefig.bbox: tight
savefig.transparent: True
"""


def apply_scientific_style():
    """Load the exact supplied style and report any necessary font fallback.

    The style is embedded, so the notebook is self-contained. Its temporary
    copy is loaded through Matplotlib's documented style.use(path) interface.
    The unchanged style text is also included in every result archive.
    """
    folder = Path(tempfile.gettempdir()) / "rotation_raman_tensor_style"
    folder.mkdir(parents=True, exist_ok=True)
    style_path = folder / "sci.mplstyle"
    style_path.write_text(SCI_STYLE_TEXT, encoding="utf-8")
    plt.style.use(str(style_path))
    selected, font_path = None, None
    for candidate in ["Arial", "Liberation Sans", "DejaVu Sans"]:
        try:
            font_path = font_manager.findfont(candidate, fallback_to_default=False)
            selected = candidate
            break
        except ValueError:
            continue
    if selected is None:
        raise RuntimeError("No supported sans-serif font is available for the plots.")
    mpl.rcParams["font.family"] = [selected]
    # Display rasterization is separate from the supplied 600-dpi export setting.
    mpl.rcParams["figure.dpi"] = 110
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["svg.fonttype"] = "none"
    return dict(
        requested_font="Arial",
        actual_font=selected,
        font_fallback=selected != "Arial",
        font_file=font_path,
        style_file=str(style_path),
        export_dpi=600,
        source="Four supplied sci.mplstyle screenshots",
        documentation="https://matplotlib.org/stable/users/explain/customizing.html",
    )


PLOT_STYLE_STATUS = apply_scientific_style()

def raman_latex(expression, **settings):
    """Print notation such as β′ while preserving the symbolic variable names."""
    names = dict(settings.pop("symbol_names", {}))
    for symbol in getattr(expression, "free_symbols", set()):
        if symbol.name == "beta_prime":
            names[symbol] = r"\beta^{\prime}"
    return sp.latex(expression, symbol_names=names, **settings)


print("Cell 02/22 — Run completed successfully.\nReady: Numerical helpers, complex-coefficient input and the figure style are ready.\nNext: Run Cell 03.", flush=True)


# %% Code cell 3: Crystal orientation
"""Build a proper 3D frame using the direct and reciprocal lattice metrics."""


def trig_deg(value):
    """Keep exact radicals for special angles; evaluate other numeric angles."""
    angle = deg(value)
    sine, cosine = sp.sin(angle), sp.cos(angle)
    if sine.has(sp.sin, sp.cos) or cosine.has(sp.sin, sp.cos):
        sine, cosine = sine.evalf(15), cosine.evalf(15)
    return sine, cosine


def lattice_matrix(parameters):
    """Return L=(a,b,c) in an orthonormal Cartesian crystal coordinate system.

    The first direct-lattice vector lies along Cartesian x, and the second
    lies in the xy plane. The six inputs are a0,b0,c0,α,β,γ.
    Tensor components always refer to Cartesian axes, even for a skew cell.
    """
    if len(parameters) != 6:
        raise ValueError("Lattice input requires three lengths and three angles.")
    length_a, length_b, length_c, angle_a, angle_b, angle_g = map(sp.sympify, parameters)
    if any(real_number(item, "Lattice length") <= 0 for item in parameters[:3]):
        raise ValueError("Lattice lengths must be positive.")
    if any(not 0 < real_number(item, "Lattice angle") < 180 for item in parameters[3:]):
        raise ValueError("Lattice angles must lie between 0 and 180 degrees.")
    _, cos_a = trig_deg(angle_a)
    _, cos_b = trig_deg(angle_b)
    sin_g, cos_g = trig_deg(angle_g)
    c_y = (cos_a - cos_b * cos_g) / sin_g
    c_z_squared = sp.simplify(1 - cos_b**2 - c_y**2)
    if real_number(c_z_squared, "Lattice volume factor") <= 1e-14:
        raise ValueError("The lattice angles produce a zero or invalid cell volume.")
    return sp.simplify(
        sp.Matrix(
            [
                [length_a, length_b * cos_g, length_c * cos_b],
                [0, length_b * sin_g, length_c * c_y],
                [0, 0, length_c * sp.sqrt(c_z_squared)],
            ]
        )
    )


def real_vector(vector, name):
    """Require a finite, nonzero three-component Cartesian/index vector."""
    result = sp.Matrix(vector)
    if result.shape != (3, 1):
        raise ValueError(f"{name} must contain three components.")
    for item in result:
        real_number(item, name)
    if np.linalg.norm(numeric(result)) < 1e-14:
        raise ValueError(f"{name} must not be the zero vector.")
    return result


def unit(vector):
    """Normalize a nonzero real vector using the Cartesian Euclidean metric."""
    return sp.simplify(vector / sp.sqrt((vector.T * vector)[0]))


def validate_frame(matrix):
    """Require orthonormal columns and determinant +1; reflections are rejected."""
    matrix = sp.Matrix(matrix)
    if matrix.shape != (3, 3):
        raise ValueError("The orientation matrix must be 3×3.")
    for item in matrix:
        real_number(item, "Orientation matrix")
    evaluated = numeric(matrix).real
    if not np.allclose(evaluated.T @ evaluated, np.eye(3), atol=1e-10, rtol=0):
        raise ValueError("The orientation columns must form an orthonormal frame.")
    if not np.isclose(np.linalg.det(evaluated), 1, atol=1e-10, rtol=0):
        raise ValueError("A proper rotation requires det(T)=+1; a reflected frame is invalid.")
    return matrix


def build_orientation(config):
    """Return the frame T with v_crystal = T v_lab and R_lab = T.T R_crystal T.

    Positive ψ rotates the measurement axes X toward Y around Z.
    It is a frame-angle convention; an active sample rotation has the
    opposite sign when the laboratory optics are kept fixed.
    """
    lattice = lattice_matrix(config["lattice"])
    if config.get("allow_reflection", False):
        raise ValueError("Reflections are not accepted as crystal rotations.")
    if config.get("orientation", "hkl") == "matrix":
        frame = validate_frame(config["T_manual"])
        return dict(
            L=lattice,
            T=frame,
            notes=["A manual proper frame was used; hkl, uvw and ψ were not reapplied."],
        )
    if config.get("orientation", "hkl") != "hkl":
        raise ValueError("Orientation must be 'hkl' or 'matrix'.")
    normal_sign = config.get("normal_sign", 1)
    if normal_sign not in (-1, 1):
        raise ValueError("The normal-side sign must be +1 or -1.")
    indices = real_vector(config["hkl"], "Miller indices")
    reciprocal_normal = sp.simplify(lattice.inv().T * indices)
    normal = normal_sign * unit(reciprocal_normal)
    notes = []
    if config["uvw"] is None:
        # Select a stable reference axis, then project it into the surface.
        index = int(np.argmin(np.abs(numeric(normal).ravel())))
        reference = sp.eye(3)[:, index]
        tangent = sp.simplify(reference - normal * (normal.T * reference)[0])
        notes.append(
            f"Automatic X reference: projected Cartesian {'xyz'[index]} axis. "
            "This is a coordinate reference, not a measured in-plane direction."
        )
    else:
        direction = real_vector(config["uvw"], "Direct-lattice direction [uvw]")
        tangent = sp.simplify(lattice * direction)
        zone_residual = abs(complex(sp.N((reciprocal_normal.T * tangent)[0])))
        zone_residual /= np.linalg.norm(numeric(reciprocal_normal)) * np.linalg.norm(
            numeric(tangent)
        )
        if zone_residual > 1e-10:
            raise ValueError("[uvw] must lie in (hkl): h*u+k*v+l*w must equal zero.")
    x_initial = unit(tangent)
    y_initial = sp.simplify(normal.cross(x_initial))
    real_number(config["azimuth_deg"], "In-plane frame angle ψ")
    sine, cosine = trig_deg(config["azimuth_deg"])
    x_axis = sp.simplify(cosine * x_initial + sine * y_initial)
    y_axis = sp.simplify(-sine * x_initial + cosine * y_initial)
    frame = validate_frame(sp.Matrix.hstack(x_axis, y_axis, normal))
    return dict(
        L=lattice,
        g=reciprocal_normal,
        t=tangent,
        X0=x_initial,
        Y0=y_initial,
        T=frame,
        normal_sign=normal_sign,
        notes=notes,
    )

print("Cell 03/22 — Run completed successfully.\nReady: The lattice, reciprocal-normal and measurement-frame functions are ready.\nNext: Run Cell 04.", flush=True)


# %% Code cell 4: Tensor and material library
# First-order symmetric electric-dipole Raman tensor library.
# Components are expressed in orthonormal Cartesian axes, not a skew lattice basis.
def symmetric(xx=0, yy=0, zz=0, xy=0, xz=0, yz=0):
    """Construct a symmetric Cartesian 3×3 tensor from its six independent entries."""
    return sp.Matrix([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])


def family(partners, note="", channels=None):
    """Store one tensor or a set of symmetry-related degenerate phonon partners."""
    return dict(
        partners=[sp.Matrix(R) for R in partners],
        note=note,
        channels=channels or [str(i + 1) for i in range(len(partners))],
    )


DIAG = symmetric(a, b, c)
MONO_A = symmetric(a, b, c, xz=d)
MONO_B = symmetric(xy=e, yz=f)
AXIAL = symmetric(a, a, b)
OUTPLANE = [symmetric(xz=e), symmetric(yz=e)]
TRIGONAL = [symmetric(c, -c, yz=d), symmetric(xy=-c, xz=-d)]
CUBIC_E = [symmetric(-b, -b, 2 * b), symmetric(sp.sqrt(3) * b, -sp.sqrt(3) * b)]
CUBIC_T = [symmetric(yz=d), symmetric(xz=d), symmetric(xy=d)]

POINT_GROUPS = {}


def add_group(name, symbol, system, axes, tensors):
    """Register a point group, its axis convention and its allowed symmetric tensor families."""
    POINT_GROUPS[name] = dict(symbol=symbol, system=system, axes=axes, tensors=tensors)


add_group(
    "C1", "1", "triclinic", "Cartesian x,y,z", {"A": family([symmetric(a, b, c, xy=d, xz=e, yz=f)])}
)
add_group(
    "Ci",
    "-1",
    "triclinic",
    "Cartesian x,y,z",
    {"Ag": family([symmetric(a, b, c, xy=d, xz=e, yz=f)])},
)
for name, symbol, labels in [
    ("C2", "2", ("A", "B")),
    ("Cs", "m", ("A'", "A''")),
    ("C2h", "2/m", ("Ag", "Bg")),
]:
    add_group(
        name,
        symbol,
        "monoclinic",
        "C2 || y where present; mirror plane xz where present",
        {labels[0]: family([MONO_A]), labels[1]: family([MONO_B])},
    )
for name, symbol, labels in [
    ("D2", "222", ("A", "B1", "B2", "B3")),
    ("C2v", "mm2", ("A1", "A2", "B1", "B2")),
    ("D2h", "mmm", ("Ag", "B1g", "B2g", "B3g")),
]:
    add_group(
        name,
        symbol,
        "orthorhombic",
        "x || a, y || b, z || c; C2v: C2 || z",
        {
            labels[0]: family([DIAG]),
            labels[1]: family([symmetric(xy=d)]),
            labels[2]: family([symmetric(xz=e)]),
            labels[3]: family([symmetric(yz=f)]),
        },
    )
for name, symbol, labels in [
    ("D3", "32", ("A1", "E")),
    ("C3v", "3m", ("A1", "E")),
    ("D3d", "-3m", ("A1g", "Eg")),
]:
    add_group(
        name,
        symbol,
        "trigonal",
        "C3 || z; D3/D3d: C2 || x; C3v: mirror plane yz",
        {
            labels[0]: family([AXIAL]),
            labels[1]: family(
                TRIGONAL,
                "Both partners share c,d; partner signs follow the stated Cartesian basis.",
            ),
        },
    )
for name, symbol, labels in [
    ("D4", "422", ("A1", "B1", "B2", "E")),
    ("C4v", "4mm", ("A1", "B1", "B2", "E")),
    ("D2d", "-42m", ("A1", "B1", "B2", "E")),
    ("D4h", "4/mmm", ("A1g", "B1g", "B2g", "Eg")),
]:
    add_group(
        name,
        symbol,
        "tetragonal",
        "Principal axis || z; x,y are basal Cartesian axes",
        {
            labels[0]: family([AXIAL]),
            labels[1]: family([symmetric(c, -c)]),
            labels[2]: family([symmetric(xy=d)]),
            labels[3]: family(OUTPLANE),
        },
    )
for name, symbol, labels in [
    ("D6", "622", ("A1", "E1", "E2")),
    ("C6v", "6mm", ("A1", "E1", "E2")),
    ("D6h", "6/mmm", ("A1g", "E1g", "E2g")),
    ("D3h", "-6m2", ("A1'", "E''", "E'")),
]:
    add_group(
        name,
        symbol,
        "hexagonal",
        "z || c; x || a; y is perpendicular to x within the basal plane",
        {
            labels[0]: family([AXIAL]),
            labels[1]: family([symmetric(xz=c), symmetric(yz=c)]),
            labels[2]: family([symmetric(d, -d), symmetric(xy=d)]),
        },
    )
for name, symbol, labels in [
    ("Td", "-43m", ("A1", "E", "T2")),
    ("Oh", "m-3m", ("A1g", "Eg", "T2g")),
]:
    add_group(
        name,
        symbol,
        "cubic",
        "x || [100], y || [010], z || [001]",
        {
            labels[0]: family([a * sp.eye(3)]),
            labels[1]: family(
                CUBIC_E,
                "The two partners have equal Frobenius norm. Their overall normalization is absorbed into b.",
            ),
            labels[2]: family(CUBIC_T, channels=["yz", "xz", "xy"]),
        },
    )

# Point groups specify symmetry-allowed tensor forms. The atomic structure determines
# which irreducible representations occur and how many phonon branches they contain.
SOURCES = {
    "tensor_reference": dict(
        title="The Raman effect in crystals, Advances in Physics 13, 423–482 (1964)",
        url="https://doi.org/10.1080/00018736400101051",
        role="Symmetric tensor forms and Raman selection rules",
    ),
    "silicon": dict(
        title="Helicity-Dependent Raman Spectroscopy of Diamond and Zinc-Blende Crystal Structures, J. Raman Spectrosc. 57, 809–820 (2026)",
        url="https://doi.org/10.1002/jrs.70113",
        role="Silicon T2g tensor rotations and surface geometry",
    ),
    "tmd": dict(
        title="Polarized Raman Spectroscopy of 2H-NbSe2 and 1T-VSe2 Single Crystals, J. Raman Spectrosc. 57, 11–22 (2026)",
        url="https://doi.org/10.1002/jrs.70004",
        role="First-order NbSe2/VSe2 modes; second-order features are distinguished",
    ),
    "tis2": dict(
        title="Breit-Wigner-Fano Raman characteristics in semimetallic 1T-Ti1.03S2, Phys. Rev. B 114, 165426 (2026)",
        url="https://doi.org/10.1103/tdg3-1yg2",
        role="First-order Eg and A1g modes; the shoulder is not treated as a single Γ-point phonon",
    ),
    "tis2_parent": dict(
        title="Thickness-Dependent Characterization of Chemically Exfoliated TiS2 Nanosheets (2018)",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6645014/",
        role="Parent 1T-TiS2 structure, P-3m1; D3d for Ti1.03S2 is a parent-symmetry model",
    ),
}

MATERIALS = {
    "CaNb2O6": dict(
        label="CaNb₂O₆ — orthorhombic",
        group="D2h",
        space_group="Pbcn (#60)",
        modes={"Ag": "Ag", "B1g": "B1g", "B2g": "B2g", "B3g": "B3g"},
        lattice=(1, 1, 1, 90, 90, 90),
        surface="(211)",
        note="The unity lattice metric reproduces the slide reference geometry. Enter actual lattice lengths for a physical tilted (hkl) normal. The general interface plots Ag Cartesian contributions separately and retains the coherent complete-mode response in its audit record.",
        sources=["tensor_reference"],
    ),
    "Si": dict(
        label="Silicon — diamond / cubic benchmark",
        group="Oh",
        space_group="Fd-3m (#227)",
        modes={"T2g": "T2g"},
        lattice=(1, 1, 1, 90, 90, 90),
        surface="(500)",
        note="The first-order silicon mode is the T2g triplet, also called F2g. Three orthogonal partners are summed as intensities. A unity cubic lattice gives the correct (hkl) direction without the absolute lattice length.",
        sources=["silicon", "tensor_reference"],
    ),
    "Ti1.03S2": dict(
        label="1T-Ti₁.₀₃S₂ — parent 1T model",
        group="D3d",
        space_group="P-3m1 (#164), parent model",
        modes={"A1g": "A1g", "Eg": "Eg"},
        lattice=(1, 1, 1, 90, 90, 120),
        surface="(001)",
        note="D3d represents the parent 1T structure; excess Ti may require a lower local-symmetry model. A first-order Γ-point tensor does not calculate shoulder, two-phonon or BWF line shapes. The c/a ratio is illustrative.",
        sources=["tis2", "tis2_parent", "tensor_reference"],
    ),
    "2H-NbSe2": dict(
        label="2H-NbSe₂ — bulk parent phase",
        group="D6h",
        space_group="P63/mmc (#194)",
        modes={"A1g": "A1g", "E1g": "E1g", "E2g_low": "E2g", "E2g_high": "E2g"},
        lattice=(1, 1, 1, 90, 90, 120),
        surface="(001)",
        note="Bulk 2H: the two E2g branches have independent coefficients. Monolayer 1H uses D3h. A CDW or supercell requires the appropriate phase symmetry. The c/a ratio is illustrative.",
        sources=["tmd", "tensor_reference"],
    ),
    "1T-VSe2": dict(
        label="1T-VSe₂ — parent phase",
        group="D3d",
        space_group="P-3m1 (#164)",
        modes={"A1g": "A1g", "Eg": "Eg"},
        lattice=(1, 1, 1, 90, 90, 120),
        surface="(001)",
        note="Only first-order Γ-point modes of the parent phase are included. The feature near 250 cm⁻¹ is not automatically assigned to Eg; the cited study discuss two-phonon combinations. The c/a ratio is illustrative.",
        sources=["tmd", "tensor_reference"],
    ),
    "GENERAL": dict(
        label="General point group / custom tensor",
        group="D2h",
        space_group="specified by the user",
        modes=None,
        lattice=(1, 1, 1, 90, 90, 90),
        surface="(001)",
        note="Symmetry-allowed tensor forms. Frequencies, phonon counts and material coefficients are not inferred.",
        sources=["tensor_reference"],
    ),
}

DEFAULT_VALUES = {a: 1, b: sp.Rational(4, 5), c: sp.Rational(3, 5), d: 1, e: 1, f: 1}


def definitions_for(material, group):
    """Return the actual material mode list or the general point-group tensor templates."""
    if material not in MATERIALS:
        raise ValueError("Unknown material preset.")
    if group == "CUSTOM" and material != "GENERAL":
        raise ValueError(
            "Select General point group / custom tensor before supplying a custom tensor."
        )
    if group == "CUSTOM":
        return {
            "Custom": dict(
                irrep="Custom",
                partners=[],
                channels=["1"],
                note="User-supplied Cartesian 3×3 tensor.",
            )
        }
    if group not in POINT_GROUPS:
        raise ValueError("The point group is not present in this library.")
    if material not in MATERIALS:
        raise ValueError("Unknown material preset.")
    info = MATERIALS[material]
    mode_map = (
        info["modes"] if material != "GENERAL" else {x: x for x in POINT_GROUPS[group]["tensors"]}
    )
    if material != "GENERAL" and group != info["group"]:
        raise ValueError("The point group does not match the selected material preset.")
    return {
        name: dict(irrep=irrep, **POINT_GROUPS[group]["tensors"][irrep])
        for name, irrep in mode_map.items()
    }


def parameters_for(definition):
    """Find the independent tensor coefficients required by a mode family."""
    return sorted(set().union(*(R.free_symbols for R in definition["partners"])), key=str)


def experiment_families(cfg):
    """Validate coefficients and select the explicit intensity-combination policy for each mode."""
    group = cfg["point_group"]
    definitions = definitions_for(cfg["material"], group)
    if not cfg["modes"]:
        raise ValueError("Select at least one phonon mode.")
    answer = {}
    for name in cfg["modes"]:
        if name not in definitions:
            raise ValueError("The mode is not available in this preset: " + name)
        item = copy.deepcopy(definitions[name])
        if group == "CUSTOM":
            R = sp.Matrix(cfg["custom_tensor"])
            if R.shape != (3, 3):
                raise ValueError("A custom tensor must be 3×3.")
            if R.free_symbols:
                raise ValueError("A custom tensor must be numerical.")
            item["partners"] = [R]
        values = cfg["mode_values"].get(name, {})
        numeric_partners = []
        for R in item["partners"]:
            Rn = R.subs(values)
            if Rn.free_symbols:
                raise ValueError(f"Coefficients remain unspecified for {name}: {Rn.free_symbols}")
            if not np.all(np.isfinite(numeric(Rn))):
                raise ValueError("Tensor elements must be finite.")
            numeric_partners.append(Rn)
        item["values"] = values
        item["numeric_partners"] = numeric_partners
        # The REFERENCE decomposition belongs ONLY to the component reference workflow.
        # Quarter-wave-plate always contracts the complete tensor before taking |A|².
        if (
            cfg["calculation_method"] == "COMPONENT_REFERENCE"
            and group == "D2h"
            and item["irrep"] == "Ag"
        ):
            item["rule"] = "COMPONENT_POWER_SUM"
            item["calculation_tensors"] = [sp.diag(a, 0, 0), sp.diag(0, b, 0), sp.diag(0, 0, c)]
            item["calculation_labels"] = ["Ag(x²)", "Ag(y²)", "Ag(z²)"]
            item["combination_reason"] = (
                "User-prescribed sum of Cartesian Ag component intensities; not a claim that these are distinct phonons."
            )
        else:
            item["rule"] = (
                "DEGENERATE_PARTNER_SUM" if len(item["partners"]) > 1 else "SINGLE_TENSOR"
            )
            item["calculation_tensors"] = item["partners"]
            item["calculation_labels"] = item["channels"]
            item["combination_reason"] = (
                "Sum over orthogonal unresolved phonon partners."
                if len(item["partners"]) > 1
                else "One tensor; its elements interfere coherently before the modulus square."
            )
        answer[name] = item
    return answer


# The component reference is an explicit coordinate choice, not a fitted rotation.
# Choosing the negative normal keeps the reference X,Y signs right handed.
# It does not establish the outward normal of an experimental sample.
COMPONENT_REFERENCE_GEOMETRY = dict(
    lattice=(1, 1, 1, 90, 90, 90),
    orientation="hkl",
    hkl=(2, 1, 1),
    uvw=(0, 1, -1),
    azimuth_deg=0,
    normal_sign=-1,
    allow_reflection=False,
    T_manual=sp.eye(3),
)
SURFACES = {
    "(001)": ((0, 0, 1), (1, 0, 0)),
    "(100)": ((1, 0, 0), (0, 1, 0)),
    "(010)": ((0, 1, 0), (1, 0, 0)),
    "(110)": ((1, 1, 0), (0, 0, 1)),
    "(111)": ((1, 1, 1), (1, -1, 0)),
    "(211)": ((2, 1, 1), (0, 1, -1)),
    "(500)": ((5, 0, 0), (0, -5, 0)),
}
RULE_LABELS = {
    "COMPONENT_POWER_SUM": "Component reference Ag component-intensity sum",
    "DEGENERATE_PARTNER_SUM": "Unresolved phonon partner-intensity sum",
    "SINGLE_TENSOR": "Single coherent tensor",
}
AUDIT_VERSION = "4"
QWP_SOURCE = {
    "filename": "Dr_Kumar_Original.ipynb",
    "sha256": "661989475b7bd39b1ab57bc4d9d59285ccf903baa24b58a78017d841feba8ec7",
    "adopted_method": "Quarter-wave-plate main calculation: source complex 2×2 model, Q, Q.T, circular basis, analyzer reference, coherent amplitude and squared-modulus intensity",
    "material_tensor_policy": "The selectable 3D rotation model is an explicit extension. It supplies a projected crystal tensor to the unchanged Quarter-wave-plate optical/coherent intensity sequence. The original source does not contain a crystal-orientation library.",
    "appendix_policy": "The alternative appendix convention is not substituted for the Quarter-wave-plate main calculation.",
}
SOURCES["birefringence"] = dict(
    title="Raman tensor elements of β-Ga2O3, Scientific Reports 6, 35964 (2016)",
    url="https://doi.org/10.1038/srep35964",
    role="Demonstrates that anisotropic internal propagation can require a modified Raman formalism.",
)

print("Cell 04/22 — Run completed successfully.\nReady: Material presets and symmetry-allowed Raman tensors are ready.\nNext: Run Cell 05.", flush=True)


# %% Code cell 5: Jones states and optical protocols
"""Jones states and the optical sequence adopted from the Quarter-wave-plate notebook."""

x_hat = sp.Matrix([1, 0])
y_hat = sp.Matrix([0, 1])
sig_p = sp.Matrix([1, sp.I]) / sp.sqrt(2)
sig_m = sp.Matrix([1, -sp.I]) / sp.sqrt(2)

# P selects external transverse XY components for collinear normal backscattering.
# It is applied after the 3D tensor rotation, never to the unrotated crystal tensor.
P = sp.Matrix([[1, 0, 0], [0, 1, 0]])


def rot(angle):
    """Return the active two-dimensional Cartesian rotation matrix."""
    return sp.Matrix([[sp.cos(angle), -sp.sin(angle)], [sp.sin(angle), sp.cos(angle)]])


def waveplate(axis_angle, retardance):
    """Return an ideal waveplate matrix in the adopted fixed laboratory basis."""
    rotation = rot(axis_angle)
    return sp.simplify(rotation * sp.diag(1, sp.exp(sp.I * retardance)) * rotation.T)


QWP_QWP = waveplate(-sp.pi / 4, sp.pi / 2)
QWP_RETURN_QWP = QWP_QWP.T


def jones(theta, beta):
    """Return a normalized Jones state; θ and β are real angles in radians."""
    return sp.Matrix([sp.cos(theta), sp.exp(sp.I * beta) * sp.sin(theta)])


OPTICS_LABELS = {
    "QWP": "Quarter-wave-plate: input QWP, Raman tensor, return QWP, analyzer",
    "COMPONENT_SIGMA_ALPHA": "REFERENCE σ⁺α: θ=45°, β=β′=90°",
    "DIRECT_JONES": "Direct Jones input and detection states",
    "CIRCULAR_LINEAR": "Circular-channel model: circular input, direct linear-angle scan (Jones extension)",
    "CIRCULAR_SAME": "Circular-channel model: same circular basis label",
    "CIRCULAR_OPPOSITE": "Circular-channel model: opposite circular basis label",
    "LINEAR_PARALLEL": "Complex linear model: co-rotating parallel linear states",
    "LINEAR_CROSSED": "Complex linear model: co-rotating crossed linear states",
    "LINEAR_PAIR": "Complex linear model: parallel and crossed linear scans",
    "CUBIC_VV": "Cubic reference Section 2.2: VV, sample-angle parameter θ",
    "CUBIC_VH": "Cubic reference Section 2.2: VH, sample-angle parameter θ",
    "CUBIC_SIGMA": "Cubic reference Section 2.2: σ⁺α, θ=45 degrees, β=β′=90 degrees",
}


def optical_chain(kind, direct=None, paper=None):
    """Build the actual incident field, return optics, and detection vector.

    The Quarter-wave-plate profile adopts Q_back=Q.T and the α=0 reference from
    the uploaded notebook. The REFERENCE profile specifies effective Jones states;
    it is not assumed identical to a rotating linear analyzer after a QWP.
    Fixed profiles report their actual parameters instead of reading disabled
    user controls. No curve fitting or angular alignment takes place here.
    """
    basis = "FIRST"
    analyzers = None
    if kind == "QWP":
        incident = sp.simplify(QWP_QWP * x_hat)
        return_matrix = QWP_RETURN_QWP
        analyzer = sp.Matrix([-sp.sin(alpha), sp.cos(alpha)])
        parameters = {
            "theta_i_deg": 45,
            "beta_i_deg": 90,
            "analyzer_reference": "+Y at α=0; -X at α=90°, after return QWP",
        }
    elif kind in ["COMPONENT_SIGMA_ALPHA", "CUBIC_SIGMA"]:
        incident = sig_p
        return_matrix = sp.eye(2)
        analyzer = jones(sp.pi / 4 + alpha, sp.pi / 2)
        parameters = dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=45, beta_s_deg=90)
    elif kind == "DIRECT_JONES":
        required = ["theta_i_deg", "beta_i_deg", "theta_s0_deg", "beta_s_deg"]
        if direct is None or any(key not in direct for key in required):
            raise ValueError("Direct Jones input requires θᵢ, βᵢ, θₛ₀ and βₛ.")
        parameters = {key: sp.sympify(direct[key]) for key in required}
        for value in parameters.values():
            real_number(value, "Jones angle")
        incident = jones(deg(parameters["theta_i_deg"]), deg(parameters["beta_i_deg"]))
        return_matrix = sp.eye(2)
        analyzer = jones(deg(parameters["theta_s0_deg"]) + alpha, deg(parameters["beta_s_deg"]))
    elif kind.startswith("CIRCULAR_"):
        paper = paper or {}
        spin = paper.get("s_in", 1)
        if spin not in [-1, 1]:
            raise ValueError("The incident circular basis label must be +1 or -1.")
        incident = sig_p if spin == 1 else sig_m
        return_matrix = sp.eye(2)
        if kind == "CIRCULAR_LINEAR":
            analyzer_offset = exact(
                real_number(paper.get("analyzer_zero_deg", 0), "Direct analyzer zero")
            )
            analyzer = jones(alpha + deg(analyzer_offset), 0)
        elif kind in ["CIRCULAR_SAME", "CIRCULAR_OPPOSITE"]:
            outgoing_spin = spin if kind == "CIRCULAR_SAME" else -spin
            analyzer = sig_p if outgoing_spin == 1 else sig_m
            basis = "CONSTANT"
        else:
            raise ValueError("Unknown Circular-channel model optical scan.")
        parameters = dict(s_in=spin, curve_orbital_charge=0, basis="fixed laboratory XY", scan=kind)
        if kind == "CIRCULAR_LINEAR":
            parameters["analyzer_zero_deg"] = analyzer_offset
    elif kind.startswith("LINEAR_") or kind in ["CUBIC_VV", "CUBIC_VH"]:
        paper = paper or {}
        offset = exact(real_number(paper.get("theta0_deg", 0), "Linear angle zero"))
        angle = alpha + deg(offset)
        incident = jones(angle, 0)
        return_matrix = sp.eye(2)
        analyzers = dict(
            parallel=jones(angle, 0), crossed=sp.Matrix([-sp.sin(angle), sp.cos(angle)])
        )
        analyzer = (
            analyzers["crossed"]
            if kind in ["LINEAR_CROSSED", "CUBIC_VH"]
            else analyzers["parallel"]
        )
        basis = "SECOND"
        parameters = dict(
            theta0_deg=offset,
            scan="co-rotating linear states",
            channels="both" if kind == "LINEAR_PAIR" else kind.split("_")[-1].lower(),
        )
    else:
        raise ValueError(f"Unknown optical profile: {kind!r}.")
    return dict(
        kind=kind,
        label=OPTICS_LABELS[kind],
        parameters=parameters,
        Ein=incident,
        B=return_matrix,
        analyzer=analyzer,
        effective_analyzer=sp.simplify(return_matrix.H * analyzer),
        scan_basis=basis,
        analyzers=analyzers,
    )


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
    "kumar-original": ("Uploaded original QWP implementation reference", "Included original source notebook"),
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
        "CUBIC_VV": dict(family="Co-rotating linear states", scan="θ: common incident/detector angle",
            preparation="Linear input v(t), t=θ+θ₀", return_path="Identity: no extra return plate",
            detection="Linear analyzer parallel to the input", states=[v, r"E_i=v(t),\quad e_s=v(t),\quad B=I_2"],
            amplitude=r"\mathcal A_{VV}=v(t)^\dagger R_\perp v(t)",
            intensity=r"I_{VV}=|r_{xx}\cos^2t+(r_{xy}+r_{yx})\sin t\cos t+r_{yy}\sin^2t|^2",
            invariant="The paired VV/VH choice must reproduce this VV channel with identical inputs.",
            use_for="Parallel linear measurements and the VV member of the cubic benchmark.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Direct specialization of the cited contraction and linear states."),
        "CUBIC_VH": dict(family="Co-rotating linear states", scan="θ: common incident/detector angle",
            preparation="Linear input v(t), t=θ+θ₀", return_path="Identity: no extra return plate",
            detection="Linear analyzer perpendicular to the input", states=[v, w, r"E_i=v(t),\quad e_s=w(t),\quad B=I_2"],
            amplitude=r"\mathcal A_{VH}=w(t)^\dagger R_\perp v(t)",
            intensity=r"I_{VH}=|r_{yx}\cos^2t-r_{xy}\sin^2t+(r_{yy}-r_{xx})\sin t\cos t|^2",
            invariant="The paired VV/VH choice must reproduce this VH channel with identical inputs.",
            use_for="Crossed linear measurements and the VH member of the cubic benchmark.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Direct specialization of the cited contraction and crossed states."),
        "LINEAR_PAIR": dict(family="Co-rotating linear states", scan="θ: one common angle for both channels",
            preparation="One linear input and one shared coefficient set", return_path="Identity for both channels",
            detection="Calculate parallel and perpendicular analyzers separately", states=[v, w, r"E_i=v(t),\quad e_s^{VV}=v(t),\quad e_s^{VH}=w(t)"],
            amplitude=r"\mathcal A_{VV}=v^\dagger R_\perp v,\quad\mathcal A_{VH}=w^\dagger R_\perp v",
            intensity=r"I_{VV}=|\mathcal A_{VV}|^2,\quad I_{VH}=|\mathcal A_{VH}|^2",
            invariant="This is a paired output, not a third polarization law. Each raw curve equals its standalone channel.",
            use_for="Comparing VV and VH for the same phonon coefficients, surface and angular zero.",
            caution=linear_note, sources=["complex", "cubic"], provenance="Two instances of the same Jones engine; powers are not added to define a new channel."),
        "CIRCULAR_LINEAR": dict(family="Circular input / linear detector", scan="α: linear-analyzer angle only",
            preparation="Fixed circular input σₛ", return_path="Identity: the detector state at the sample is linear",
            detection="v(α+α₀), with a calibrated analyzer zero", states=[sigma, r"E_i=\sigma_s,\quad e_s=v(\alpha+\alpha_0),\quad B=I_2"],
            amplitude=r"\mathcal A_{CL}=\frac{p e^{it}+q e^{-it}}{\sqrt{2}},\quad t=\alpha+\alpha_0",
            intensity=r"I_{CL}=\frac{|p|^2+|q|^2}{2}+\operatorname{Re}(p q^*e^{2it})",
            invariant="For σ⁺ input it equals custom Jones with θᵢ=45, βᵢ=90, θₛ₀=α₀ and βₛ=0 degrees.",
            use_for="Circular illumination with a linear effective detector at the sample.",
            caution="A bare linear-analyzer scan does not select pure σ⁺ or σ⁻ endpoints. A return QWP changes the effective detector.",
            sources=["jones", "circular"], provenance="Program Jones-calculus extension. The circular selection-rule paper does not prescribe this continuous scan or its quantitative intensity."),
        "CUBIC_SIGMA": dict(family="Circular input / elliptical detector", scan="α: effective detection-state parameter",
            preparation="Fixed σ⁺ input", return_path="Identity in the effective-state representation",
            detection="j(π/4+α, π/2), elliptical except at special angles",
            states=[r"E_i=\sigma^{+},\quad e_s=(\cos(\pi/4+\alpha),i\sin(\pi/4+\alpha))^T", r"e_s=\cos\alpha\,\sigma^{+}-\sin\alpha\,\sigma^{-}"],
            amplitude=r"\mathcal A_E=p\cos\alpha-q\sin\alpha",
            intensity=r"I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\operatorname{Re}(p q^*)\sin\alpha\cos\alpha",
            invariant="It equals custom Jones at θᵢ=45, βᵢ=90, θₛ₀=45, βₛ=90 degrees; source QWP endpoints agree up to phase, intermediate states generally differ.",
            use_for="The cubic paper σ⁺α equations, its Fig. 1(c) benchmark and the declared slide-frame example.",
            caution="This implements Eq. (11) at θ=π/4 and β=β'=π/2. The paper calls α a polarizer angle, but its effective detector is not a bare linear state at the sample. An apparatus must be calibrated before identifying the two.",
            sources=["cubic", "jones"], provenance="Cited effective Jones parameterization; the p/q expansion is derived here from that state."),
        "QWP": dict(family="Circular input / explicit return optics", scan="α: physical linear analyzer after the return plate",
            preparation="Lab-X input through Q=Rot(-π/4) diag(1,i) Rot(-π/4)^T",
            return_path="B=Q.T in the uploaded source basis convention",
            detection="Linear analyzer (-sin α, cos α) after B; effective detector B.H times analyzer",
            states=[r"Q=\frac12\begin{pmatrix}1+i&-1+i\\-1+i&1+i\end{pmatrix},\quad E_i=Qe_X=e^{i\pi/4}\sigma^{+}", r"e_{an}=(-\sin\alpha,\cos\alpha)^T,\quad B=Q^T,\quad e_s=B^\dagger e_{an}", r"e_s\sim\cos\alpha\,\sigma^{+}-i\sin\alpha\,\sigma^{-}"],
            amplitude=r"\mathcal A_Q\sim p\cos\alpha+i q\sin\alpha",
            intensity=r"I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\operatorname{Im}(p q^*)\sin\alpha\cos\alpha",
            invariant="At α=0 and π/2 the circular endpoints equal the elliptical reference in power; intermediate intensities generally need not match.",
            use_for="The uploaded QWP optical sequence, after its axes, return-path convention and analyzer zero are verified.",
            caution="Q.T is a declared source convention, not a universal reverse-path rule. Keep either the explicit B or its effective detector, never both. The crystal tensor remains 3x3 before transverse restriction.",
            sources=["kumar-original", "jones"], provenance="Exact uploaded optical chain plus a program-derived p/q identity valid for any supplied R_perp under that chain."),
        "CIRCULAR_SAME": dict(family="Fixed circular channels", scan="None: both sample states are fixed",
            preparation="Fixed σₛ input", return_path="Identity in the effective-state representation",
            detection="Fixed σₛ detector", states=[sigma, r"E_i=\sigma_s,\quad e_s=\sigma_s"],
            amplitude=r"\mathcal A_{same}=\sigma_s^\dagger R_\perp\sigma_s",
            intensity=r"I_{same}=|\sigma_s^\dagger R_\perp\sigma_s|^2",
            invariant="The curve is constant when tensor, orientation and optical states remain fixed; a polar circle is a display of that constant.",
            use_for="A fixed same-basis circular channel; compare helicity labels only after reconciling beam directions.",
            caution="Same fixed XY circular label is not automatically conserved propagation-relative helicity in backscattering. This profile does not rotate the sample.",
            sources=["circular", "jones"], provenance="Fixed-state tensor contraction; the separate angular-momentum rule is conditional and does not set curve heights."),
        "CIRCULAR_OPPOSITE": dict(family="Fixed circular channels", scan="None: both sample states are fixed",
            preparation="Fixed σₛ input", return_path="Identity in the effective-state representation",
            detection="Fixed σ₋ₛ detector", states=[sigma, r"E_i=\sigma_s,\quad e_s=\sigma_{-s}"],
            amplitude=r"\mathcal A_{opposite}=\sigma_{-s}^\dagger R_\perp\sigma_s",
            intensity=r"I_{opposite}=|\sigma_{-s}^\dagger R_\perp\sigma_s|^2",
            invariant="The curve is constant under this fixed experiment. Its power is the opposite-basis circular channel, not an α sweep.",
            use_for="A fixed opposite-basis circular channel, with an explicit propagation convention.",
            caution="Opposite fixed XY circular labels can represent conserved physical helicity for counterpropagating beams. Match the reference's basis before assigning conserved/changing names.",
            sources=["circular", "jones"], provenance="Fixed-state tensor contraction, distinct from a spatial vortex-intensity calculation."),
        "DIRECT_JONES": dict(family="Custom effective states", scan="α: θₛ₀+α; input and phase controls fixed",
            preparation="j(θᵢ,βᵢ), selected by the user", return_path="Identity: any return optics must already be included in e_s",
            detection="j(θₛ₀+α,βₛ)", states=[r"j(t,\beta)=(\cos t,e^{i\beta}\sin t)^T", r"E_i=j(\theta_i,\beta_i),\quad e_s=j(\theta_{s0}+\alpha,\beta_s),\quad B=I_2"],
            amplitude=r"\mathcal A_J=j(\theta_{s0}+\alpha,\beta_s)^\dagger R_\perp j(\theta_i,\beta_i)",
            intensity=r"I_J=|\mathcal A_J|^2",
            invariant="It reproduces a preset only when both effective states and their scan laws agree up to global phase; an arbitrary waveplate path need not fit this restricted constant-β scan.",
            use_for="Calibrated effective states or exact checks of the matching preset parameters.",
            caution="Changing βₛ changes relative phase and interference. This custom profile keeps the input fixed, so it does not in general reproduce co-rotating VV/VH scans.",
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
        r"$$p=(\sigma^{+})^\dagger R_\perp E_i,\quad q=(\sigma^{-})^\dagger R_\perp E_i$$"]
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
        r"$$p=(\sigma^{+})^\dagger R_\perp\sigma^{+},\quad q=(\sigma^{-})^\dagger R_\perp\sigma^{+}$$",
        r"$$I_E=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha-2\mathrm{Re}(p q^*)\sin\alpha\cos\alpha$$",
        r"$$I_Q=|p|^2\cos^2\alpha+|q|^2\sin^2\alpha+2\mathrm{Im}(p q^*)\sin\alpha\cos\alpha$$",
        r"$$I_{CL}=\tfrac12(|p|^2+|q|^2)+\mathrm{Re}(p q^*e^{2i(\alpha+\alpha_0)})$$",
        "These equations are derived from the implemented sample states. The continuous circular-input/linear-detector scan is a Jones extension, not a quantitative prediction of the vortex selection-rule paper.",
        "### What is a reference?",
        "Use the elliptical reference for the cubic paper Fig. 1(c) and the declared slide-frame example; use the explicit QWP chain for the uploaded optical notebook; use VV/VH for the corresponding linear measurements. A CaNb2O6 material label alone does not determine a detector state. Keep lattice metric, surface axes, coefficients, angle zeros and Ag component/coherent-mode policy identical when comparing results.",
        "### Fixed labels and physical helicity",
        r"$$\mathbf k_i=-k_i\hat Z,\quad\mathbf k_s=+k_s\hat Z,\quad S_3=2\mathrm{Im}(E_X^*E_Y),\quad h_i=-S_3(E_i),\quad h_s=S_3(e_s)$$",
        "The physical sign above uses exp[i(k.r-ω t)] and fixed laboratory XY components. Reference papers can attach conserved/changing names to different beam-coordinate conventions. Match those conventions before comparing names. Fixed circular states give constant intensity when the sample is not rotated.",
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
        scope="Illustrative R_perp=diag(1,2), one coherent tensor, σ⁺ input, common raw units; no material is assigned.")


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

print("Cell 05/22 — Run completed successfully.\nReady: Jones polarization states and optical-protocol functions are ready.\nNext: Run Cell 06.", flush=True)


# %% Code cell 6: Amplitude and intensity engine
"""One matrix-based scattering engine for every material and point group."""


def transverse_amplitude_record(tensor, optical):
    """Apply one 2×2 tensor to a Jones state, return optics, then the analyzer.

    This is shared linear algebra, not a choice of intensity-combination rule.
    It has no access to the component reference, material library, or UI state.
    """
    tensor = sp.Matrix(tensor)
    if tensor.shape != (2, 2):
        raise ValueError("The optical Raman tensor must be 2×2.")
    scattered = tidy(tensor * optical["Ein"])
    outgoing = tidy(optical["B"] * scattered)
    basis = optical.get("scan_basis", "FIRST")
    if basis in ["SECOND", "CONSTANT"]:
        full = tidy((optical["analyzer"].H * outgoing)[0])
        if basis == "CONSTANT":
            return dict(
                Rperp=tensor,
                Esc=scattered,
                Eout=outgoing,
                K0=full,
                amplitude=full,
                scan_basis=basis,
            )
        # Both polarization vectors rotate. Amplitude harmonics are 0 and 2;
        # their squared modulus contains intensity harmonics 0, 2 and 4.
        at_zero = tidy(full.subs(alpha, 0))
        at_half_pi = tidy(full.subs(alpha, sp.pi / 2))
        k0 = tidy((at_zero + at_half_pi) / 2)
        kc = tidy((at_zero - at_half_pi) / 2)
        ks = tidy(full.subs(alpha, sp.pi / 4) - k0)
        return dict(
            Rperp=tensor,
            Esc=scattered,
            Eout=outgoing,
            K0=k0,
            Kc=kc,
            Ks=ks,
            amplitude=k0 + kc * sp.cos(2 * alpha) + ks * sp.sin(2 * alpha),
            scan_basis=basis,
        )
    coefficient_c = tidy((optical["analyzer"].subs(alpha, 0).H * outgoing)[0])
    coefficient_d = tidy((optical["analyzer"].subs(alpha, sp.pi / 2).H * outgoing)[0])
    return dict(
        Rperp=tensor,
        Esc=scattered,
        Eout=outgoing,
        C=coefficient_c,
        D=coefficient_d,
        amplitude=coefficient_c * sp.cos(alpha) + coefficient_d * sp.sin(alpha),
        scan_basis=basis,
    )


def amplitude_record(crystal_tensor, frame, optical):
    """Rotate a 3D tensor and propagate its amplitude through the selected optics.

    Fixed-input scans have first-harmonic amplitudes. Co-rotating linear
    states have zeroth/second-harmonic amplitudes. All coefficients follow
    from the declared matrices; none is fitted to a polar curve.
    """
    crystal_tensor = sp.Matrix(crystal_tensor)
    if crystal_tensor.shape != (3, 3):
        raise ValueError("The crystal Raman tensor must be 3×3.")
    lab_tensor = tidy(frame.T * crystal_tensor * frame)
    transverse_tensor = tidy(P * lab_tensor * P.T)
    incident_3d = tidy(P.T * optical["Ein"])
    # This vector is proportional to Raman-induced polarization. Its Z
    # component is not a longitudinal external radiated electric field.
    induced_3d = tidy(lab_tensor * incident_3d)
    record = transverse_amplitude_record(transverse_tensor, optical)
    record.update(
        Rc=crystal_tensor,
        Rlab=lab_tensor,
        Ein3=incident_3d,
        Einduced3=induced_3d,
    )
    return record


def numeric_terms(result, values):
    """Substitute coefficients once and return the declared amplitude basis per channel."""
    pairs = []
    for record in result["terms"]:
        keys = {"FIRST": ["C", "D"], "SECOND": ["K0", "Kc", "Ks"], "CONSTANT": ["K0"]}[
            record.get("scan_basis", "FIRST")
        ]
        expressions = [record[key].subs(values) for key in keys]
        if any(expression.free_symbols for expression in expressions):
            raise ValueError("Some tensor coefficients remain unspecified.")
        pair = np.array([complex(sp.N(expression)) for expression in expressions])
        if not np.all(np.isfinite(pair)):
            raise ValueError("The evaluated scattering amplitudes are not finite.")
        pairs.append(pair)
    if not pairs:
        raise ValueError("At least one scattering channel is required.")
    return np.asarray(pairs)


def summary_from_second_harmonic_amplitudes(pairs):
    """Calculate all 0/2/4 intensity harmonics and continuous-angle extrema."""
    with np.errstate(over="raise", invalid="raise"):
        k0, kc, ks = pairs.T
        i0 = float(np.sum(np.abs(k0) ** 2 + (np.abs(kc) ** 2 + np.abs(ks) ** 2) / 2))
        ic = float(2 * np.real(np.sum(k0 * kc.conj())))
        iss = float(2 * np.real(np.sum(k0 * ks.conj())))
        i4c = float(np.sum(np.abs(kc) ** 2 - np.abs(ks) ** 2) / 2)
        i4s = float(np.real(np.sum(kc * ks.conj())))
    if not np.all(np.isfinite([i0, ic, iss, i4c, i4s])):
        raise ValueError("The intensity exceeds floating-point range; rescale the tensor.")
    constant = max(abs(ic), abs(iss), abs(i4c), abs(i4s)) <= 1e-12 * max(i0, np.finfo(float).tiny)
    if constant:
        return dict(
            I0=i0, Ic=ic, Is=iss, I4c=i4c, I4s=i4s, Imax=i0, Imin=i0, alpha_max=None, alpha_min=None
        )
    # With z=exp(2i*angle), stationary points satisfy a quartic on |z|=1.
    # No sampled-curve fit or target polar pattern is involved.
    u1, u2 = (ic - 1j * iss) / 2, (i4c - 1j * i4s) / 2
    coefficients = np.trim_zeros(
        np.array([2 * u2, u1, 0, -u1.conjugate(), -2 * u2.conjugate()], complex), "f"
    )
    roots = np.roots(coefficients)
    stationary = sorted((np.angle(root) / 2) % np.pi for root in roots if abs(abs(root) - 1) < 1e-5)
    if not stationary:
        raise ArithmeticError("Could not resolve the continuous-angle intensity extrema.")
    values = np.array(
        [
            i0
            + ic * np.cos(2 * t)
            + iss * np.sin(2 * t)
            + i4c * np.cos(4 * t)
            + i4s * np.sin(4 * t)
            for t in stationary
        ]
    )
    maximum, minimum = float(values.max()), float(values.min())
    tolerance = 128 * np.finfo(float).eps * max(i0, maximum, np.finfo(float).tiny)
    if minimum < -tolerance:
        raise ArithmeticError("The calculated intensity violates positivity.")
    return dict(
        I0=i0,
        Ic=ic,
        Is=iss,
        I4c=i4c,
        I4s=i4s,
        Imax=maximum,
        Imin=max(0.0, minimum),
        alpha_max=float(np.rad2deg(stationary[int(values.argmax())])),
        alpha_min=float(np.rad2deg(stationary[int(values.argmin())])),
    )


def summary_for_amplitudes(pairs):
    """Select the exact harmonic summary for the declared amplitude basis."""
    if pairs.shape[1] == 3:
        return summary_from_second_harmonic_amplitudes(pairs)
    if pairs.shape[1] == 1:
        value = float(np.sum(np.abs(pairs[:, 0]) ** 2))
        if not np.isfinite(value):
            raise ValueError("The intensity is not finite; rescale the tensor.")
        return dict(
            I0=value, Ic=0.0, Is=0.0, Imax=value, Imin=value, alpha_max=None, alpha_min=None
        )
    return summary_from_pairs(pairs)


def intensity_expression(summary, variable=alpha):
    """Build the displayed expression from every computed harmonic, including 4θ."""
    return (
        summary["I0"]
        + summary["Ic"] * sp.cos(2 * variable)
        + summary["Is"] * sp.sin(2 * variable)
        + summary.get("I4c", 0) * sp.cos(4 * variable)
        + summary.get("I4s", 0) * sp.sin(4 * variable)
    )


def summary_from_pairs(pairs):
    """Calculate harmonic coefficients and extrema without fitting sampled data."""
    try:
        with np.errstate(over="raise", invalid="raise"):
            cosine_power = float(np.sum(np.abs(pairs[:, 0]) ** 2))
            sine_power = float(np.sum(np.abs(pairs[:, 1]) ** 2))
            i0 = cosine_power / 2 + sine_power / 2
            ic = cosine_power / 2 - sine_power / 2
            iss = float(np.real(np.sum(pairs[:, 0] * pairs[:, 1].conj())))
            radius = float(np.hypot(ic, iss))
            maximum = i0 + radius
    except FloatingPointError as exc:
        raise ValueError(
            "The intensity exceeds floating-point range; rescale the input coefficients."
        ) from exc
    if not np.all(np.isfinite([i0, ic, iss, radius, maximum])):
        raise ValueError("The intensity coefficients are not finite; rescale the tensor.")
    minimum = i0 - radius
    roundoff = 64 * np.finfo(float).eps * max(i0, radius, np.finfo(float).tiny)
    if minimum < -roundoff:
        raise ArithmeticError("The intensity extrema violate positivity beyond numerical roundoff.")
    # A tiny negative minimum can result from cancellation at an exact extinction.
    minimum = max(0.0, minimum)
    constant = radius <= 1e-12 * max(i0, np.finfo(float).tiny)
    peak = None if constant else float(np.rad2deg(np.arctan2(iss, ic)) / 2 % 180)
    return dict(
        I0=i0,
        Ic=ic,
        Is=iss,
        Imax=maximum,
        Imin=minimum,
        alpha_max=peak,
        alpha_min=None if peak is None else (peak + 90) % 180,
    )


def evaluate_terms(result, values, angles):
    """Evaluate channel intensities as |A_j|², then sum the requested channels."""
    pairs = numeric_terms(result, values)
    try:
        with np.errstate(over="raise", invalid="raise"):
            if pairs.shape[1] == 3:
                basis = np.array([np.ones_like(angles), np.cos(2 * angles), np.sin(2 * angles)])
            elif pairs.shape[1] == 1:
                basis = np.ones((1, len(angles)))
            else:
                basis = np.array([np.cos(angles), np.sin(angles)])
            amplitudes = pairs @ basis
            components = np.abs(amplitudes) ** 2
            total = np.sum(components, axis=0)
    except FloatingPointError as exc:
        raise ValueError("The intensity exceeds floating-point range; rescale the tensor.") from exc
    if not np.all(np.isfinite(total)):
        raise ValueError("The intensity curve contains non-finite values.")
    return dict(
        pairs=pairs, components=components, total=total, summary=summary_for_amplitudes(pairs)
    )


def numeric_curve(result, values, angles):
    """Convenience wrapper used by independent tests and small scripted examples."""
    return evaluate_terms(result, values, np.asarray(angles))["total"]


def numeric_summary(result, values):
    """Return exact harmonic extrema after numerical coefficient substitution."""
    return summary_for_amplitudes(numeric_terms(result, values))

print("Cell 06/22 — Run completed successfully.\nReady: Tensor rotation, detected amplitude and intensity functions are ready.\nNext: Run Cell 07.", flush=True)


# %% Code cell 7: Optical reference model
"""The Quarter-wave-plate main-source model, with no REFERENCE channel or intensity rules."""

# Separate REAL symbols reproduce the assumptions in Quarter-wave-plate's source.
# They must not reuse the general library's complex a,b,c symbols.
ref_a, ref_A, ref_delta, ref_phi = sp.symbols("a A delta phi", real=True)
QWP_SOURCE_TENSOR = sp.Matrix(
    [
        [ref_a, ref_A * sp.exp(sp.I * ref_delta)],
        [-ref_A * sp.exp(sp.I * ref_delta), ref_a * sp.exp(sp.I * ref_phi)],
    ]
)
QWP_MODE = "Quarter-wave-plate source model"
METHOD_LABELS = {
    "GENERAL": "General tensor / Jones calculation",
    "COMPONENT_REFERENCE": "Component reference",
    "QWP": "Quarter-wave-plate",
    "CIRCULAR": "Circular-channel model",
    "LINEAR": "Complex linear model",
    "CUBIC_REF": "Cubic reference",
}
TENSOR_MODEL_LABELS = {
    "QWP_SOURCE_2D": "Original Quarter-wave-plate 2×2 model",
    "CRYSTAL_3D": "Rotated crystal 3×3 tensor",
}


@lru_cache(maxsize=1)
def qwp_source_algebra():
    """Recompute the source's main sequence and independent analytic checks.

    The matrix-chain record supplies the plotted intensity. The handwritten
    closed form below is an independent regression check, never a curve input.
    The source's alternative-convention appendix is not an active optical path.
    """
    optical = optical_chain("QWP")
    record = transverse_amplitude_record(QWP_SOURCE_TENSOR, optical)
    r_pp = sp.simplify((sig_p.H * QWP_SOURCE_TENSOR * sig_p)[0])
    r_mp = sp.simplify((sig_m.H * QWP_SOURCE_TENSOR * sig_p)[0])
    v_plus = sp.simplify(QWP_RETURN_QWP * sig_p)
    v_minus = sp.simplify(QWP_RETURN_QWP * sig_m)
    # Follow the source's reference-axis construction, including its global phase.
    index = int(np.argmax([abs(complex(sp.N(item))) for item in v_plus]))
    p1 = sp.simplify(
        v_plus[index] / sp.sqrt(sp.simplify(v_plus[index] * sp.conjugate(v_plus[index])))
    )
    e_ref = sp.simplify(v_plus / p1)
    e_perp = sp.Matrix([[0, -1], [1, 0]]) * e_ref
    p2 = sp.simplify((e_perp.T * v_minus)[0])
    analyzer = e_ref * sp.cos(alpha) + e_perp * sp.sin(alpha)
    check(
        zero(analyzer - optical["analyzer"]),
        "The Quarter-wave-plate analyzer origin differs from the source.",
    )
    i_pp = sp.simplify(sp.expand_complex(r_pp * sp.conjugate(r_pp)))
    i_mp = sp.simplify(sp.expand_complex(r_mp * sp.conjugate(r_mp)))
    i_cross = sp.simplify(sp.im(sp.expand_complex(r_pp * sp.conjugate(r_mp))))
    # Independent source equation, retained only for reporting and tests.
    reference_pp = (
        ref_a**2 * sp.cos(ref_phi / 2) ** 2
        + ref_A**2
        + 2 * ref_a * ref_A * sp.cos(ref_phi / 2) * sp.sin(ref_phi / 2 - ref_delta)
    )
    reference_mp = ref_a**2 * sp.sin(ref_phi / 2) ** 2
    reference_cross = ref_a**2 * sp.sin(ref_phi) / 2 + ref_a * ref_A * sp.sin(
        ref_phi / 2
    ) * sp.sin(ref_phi / 2 - ref_delta)
    reference_intensity = (
        reference_pp * sp.cos(alpha) ** 2
        + reference_mp * sp.sin(alpha) ** 2
        + 2 * reference_cross * sp.sin(alpha) * sp.cos(alpha)
    )
    return dict(
        record=record,
        Rpp=r_pp,
        Rmp=r_mp,
        v_plus=v_plus,
        v_minus=v_minus,
        p1=p1,
        p2=p2,
        e_ref=e_ref,
        e_perp=e_perp,
        Ipp=i_pp,
        Imp=i_mp,
        Icross=i_cross,
        source_intensity=reference_intensity,
        source_pieces=(reference_pp, reference_mp, reference_cross),
    )


def qwp_source_values(parameters):
    """Validate four real source inputs and convert phase degrees to radians."""
    required = ["a", "A", "delta_deg", "phi_deg"]
    if parameters is None or any(key not in parameters for key in required):
        raise ValueError("The Quarter-wave-plate source model requires real a,A,delta_deg,phi_deg.")
    values = {key: exact(real_number(parameters[key], key)) for key in required}
    return {
        ref_a: values["a"],
        ref_A: values["A"],
        ref_delta: deg(values["delta_deg"]),
        ref_phi: deg(values["phi_deg"]),
    }

print("Cell 07/22 — Run completed successfully.\nReady: The supplied effective 2D optical-reference functions are ready.\nNext: Run Cell 08.", flush=True)


# %% Code cell 8: Circular and complex-linear models
"""Paper-specific conventions, examples and conditional selection diagnostics.

The circular-selection reference supply selection rules, not a quantitative vortex intensity model.
Pimenta et al. discuss coherent, phase-sensitive linear-polarization scans.
The functions below keep those two roles distinct.
"""

theta_scan = sp.symbols("theta", real=True)
PAPER_SOURCES = {
    "circular": dict(
        title="Selection rule for Raman spectra of two-dimensional materials using circularly-polarized vortex light",
        journal="Physical Chemistry Chemical Physics 23, 17271–17278 (2021)",
        doi="10.1039/D1CP02209A",
        url="https://doi.org/10.1039/D1CP02209A",
        read_pages="All 8 PDF pages, including Tables 1–6 and references",
        equations="11 (Jones basis); 17,21–24 (selection); Sections 4–5 (scope)",
    ),
    "linear": dict(
        title="Polarized Raman spectroscopy in low-symmetry 2D materials: angle-resolved experiments and complex number tensor elements",
        journal="Physical Chemistry Chemical Physics 23, 27103–27123 (2021)",
        doi="10.1039/D1CP03626B",
        url="https://doi.org/10.1039/D1CP03626B",
        read_pages="All 21 PDF pages, including Figures 1–12, Table 1 and references",
        equations="2–4 (tensor contraction); 7–10 (complex response); 11–16 (linear scans)",
    ),
}
SOURCES.update(PAPER_SOURCES)

# Paper examples use illustrative cell lengths. Tensor ratios are entered
# explicitly by the reference factory; they are not material-name predictions.
MATERIALS.update(
    {
        "BP": dict(
            label="Black phosphorus / D2h (Complex linear model example)",
            group="D2h",
            space_group="D2h axis convention used in Pimenta et al.: layer plane xz, normal y",
            lattice=(1, 1, 1, 90, 90, 90),
            surface="(010)",
            modes={"Ag(1)": "Ag", "B2g": "B2g", "Ag(2)": "Ag"},
            note="Paper Fig. 5 ratios can be loaded explicitly. Unity cell lengths are sufficient for this principal-plane example; they are not measured BP lattice constants.",
            sources=["linear"],
        ),
        "MoS2-1L": dict(
            label="Monolayer MoS2 / D3h (Circular-channel model example)",
            group="D3h",
            space_group="Monolayer D3h; correct labels A1-prime and E-prime",
            lattice=(1, 1, 1, 90, 90, 120),
            surface="(001)",
            modes={"A1'": "A1'", "E'": "E'"},
            note="Plane-wave Jones example. The supplied Circular paper uses bulk-like A1g/E2g labels in one D3h passage; this preset uses A1-prime/E-prime.",
            sources=["circular"],
        ),
        "Graphene": dict(
            label="Graphene / D6h (Circular-channel model G-mode example)",
            group="D6h",
            space_group="D6h monolayer model",
            lattice=(1, 1, 1, 90, 90, 120),
            surface="(001)",
            modes={"G (E2g)": "E2g"},
            note="Illustrative E2g tensor. No electronic band calculation or vortex intensity is inferred.",
            sources=["circular"],
        ),
        "MoTe2-1Tprime": dict(
            label="1T-prime MoTe2 / C2h (Complex linear model example)",
            group="C2h",
            space_group="C2h, unique axis y; paper Section 2.2",
            lattice=(1, 1, 1, 90, 100, 90),
            surface="(001)",
            modes={"Ag": "Ag", "Bg": "Bg"},
            note="Illustrative monoclinic metric and tensor coefficients; not the measured Fig. 6 fit parameters.",
            sources=["linear"],
        ),
        "ReSe2": dict(
            label="ReSe2 / Ci (Complex linear model example)",
            group="Ci",
            space_group="Ci, Cartesian tensor axes",
            lattice=(1, 1, 1, 90, 90, 90),
            surface="(001)",
            modes={"Ag": "Ag"},
            note="Illustrative Cartesian Ci tensor; measured triclinic lattice and mode-specific coefficients must be supplied for a sample calculation.",
            sources=["linear"],
        ),
    }
)


def default_paper_parameters(method):
    """Return explicit paper controls without borrowing another workflow's optics."""
    if method == "CIRCULAR":
        return dict(
            s_in=1, N=2, ell_i=0, m_ph=[0], absorption_delta_m=None, thin_2d_assumptions=False
        )
    if method == "LINEAR":
        return dict(theta0_deg=0)
    if method == "CUBIC_REF":
        return dict(theta0_deg=0)
    return None


def paper_demo_config(method, material="CaNb2O6"):
    """Build a declared paper-workflow example using the existing tensor library."""
    if method not in ["CIRCULAR", "LINEAR"]:
        raise ValueError("Choose CIRCULAR or LINEAR.")
    config = demonstration_config(material, "COMPONENT_SIGMA_ALPHA")
    config.update(
        calculation_method=method,
        ag_rule="COHERENT_SINGLE_TENSOR",
        optics="CIRCULAR_LINEAR" if method == "CIRCULAR" else "LINEAR_PAIR",
        paper_parameters=default_paper_parameters(method),
        case_label=METHOD_LABELS[method] + " / " + material,
        input_note="Illustrative tensor coefficients. The selected paper supplies the stated formalism, not these sample-specific coefficients.",
    )
    return config


def linear_bp_reference_config():
    """Use the ratios printed in Fig. 5, with a declared xz angle convention."""
    config = paper_demo_config("LINEAR", "BP")
    config.update(
        normal_sign=-1,
        case_label="Complex linear model BP: Fig. 5 ratios, Eq. 13 scans",
        input_note="Fig. 5 prints c/a=1.96 and phi_ac=0 degrees for Ag(1), c/a=1.32 and phi_ac=94 degrees for Ag(2), and an off-diagonal reference magnitude 1.30. a=1 fixes an arbitrary scale for each illustrative branch. Curves reproduce Eq. 13 with the displayed angle zero, not digitized experimental data.",
    )
    config["mode_values"]["Ag(1)"] = {a: 1, b: 1, c: sp.Rational(196, 100)}
    config["mode_values"]["Ag(2)"] = {a: 1, b: 1, c: sp.Rational(132, 100) * sp.exp(sp.I * deg(94))}
    # The library calls the xz entry e; the review calls that entry f.
    config["mode_values"]["B2g"] = {e: sp.Rational(130, 100)}
    return config


def circular_mos2_reference_config():
    """Declare the non-vortex A1-prime/E-prime circular-channel example."""
    config = paper_demo_config("CIRCULAR", "MoS2-1L")
    config.update(
        case_label="Circular-channel model: monolayer MoS2, ell_i=0",
        input_note="D3h plane-wave Jones tensors and circular channels; the α scan is a direct Jones extension. Intensities use illustrative coefficients, not a prediction of the vortex paper.",
    )
    config["paper_parameters"].update(N=3, m_ph=[0, 2, -2], thin_2d_assumptions=True)
    return config


def circular_integer(value, label):
    """Require a finite integer charge/order and reject Boolean substitutes."""
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(label + " must be an integer, not a Boolean.")
    number = real_number(value, label)
    if int(number) != number:
        raise ValueError(label + " must be an integer.")
    return int(number)


def circular_congruence(N, s_i, s_s, ell_i, phonon_charges, delta_m=None):
    """Check Eq. 24 and optional absorption Eq. 21 as necessary conditions.

    Each charge is tested separately. Passing is not an intensity prediction
    and does not establish the intermediate electronic-state assumptions.
    The scattered OAM is zero, as assumed in the supplied paper.
    """
    N, s_i, s_s = [
        circular_integer(value, label)
        for value, label in [
            (N, "Cyclic order N"),
            (s_i, "Incident circular label"),
            (s_s, "Scattered circular label"),
        ]
    ]
    if N not in [2, 3, 4, 6] or s_i not in [-1, 1] or s_s not in [-1, 1]:
        raise ValueError("Use N=2,3,4,6 and circular basis labels +/-1.")
    ell_i = circular_integer(ell_i, "Orbital charge ell_i")
    if not phonon_charges:
        raise ValueError("Enter at least one integer phonon pseudo-angular-momentum charge.")
    phonon_charges = [circular_integer(q, "Phonon charge") for q in phonon_charges]
    matching = [int(q) for q in phonon_charges if (s_s - s_i - int(ell_i) + int(q)) % N == 0]
    if delta_m is None:
        absorption = None
    else:
        delta_m = circular_integer(delta_m, "Optical electronic charge difference")
        absorption = (int(delta_m) - s_i - int(ell_i)) % N == 0
    return dict(
        eq24_pass=bool(matching),
        matching_m_ph=matching,
        eq21_pass=absorption,
        combined_necessary_pass=None if absorption is None else bool(matching) and absorption,
        absorption_condition_checked=absorption is not None,
    )


def circular_basis_matrix(tensor):
    """Return U-dagger R U in the fixed laboratory circular Jones basis."""
    circular = sp.Matrix.hstack(sig_p, sig_m)
    return tidy(circular.H * sp.Matrix(tensor) * circular)


def circular_diagnostics(run):
    """Keep plane-wave tensor channels and the paper's conditional rule side by side."""
    parameters = run["config"]["paper_parameters"]
    output = {
        "parameters": copy.deepcopy(parameters),
        "rule_checks": [],
        "channels": {},
        "intensity_scope": "Plane-wave Jones intensity (ℓ=0). Requested vortex charge enters the separate Eq. 24 check only.",
        "scope": (
            "Conditional 2D rule"
            if parameters["thin_2d_assumptions"]
            else "Diagnostic only: the paper's thin-2D/electronic assumptions have not been established for this sample."
        ),
    }
    for outgoing in [1, -1]:
        condition = circular_congruence(
            parameters["N"],
            parameters["s_in"],
            outgoing,
            parameters["ell_i"],
            parameters["m_ph"],
            parameters.get("absorption_delta_m"),
        )
        output["rule_checks"].append(dict(s_i=parameters["s_in"], s_s=outgoing, **condition))
    for name, result in run["results"].items():
        values = run["families"][name]["values"]
        matrices = [circular_basis_matrix(record["Rperp"]) for record in result["terms"]]
        powers = np.zeros((2, 2), float)
        for matrix in matrices:
            powers += np.abs(numeric(matrix.subs(values))) ** 2
        output["channels"][name] = dict(
            matrices=matrices,
            powers=powers,
            row_labels=["s_s=+1", "s_s=-1"],
            column_labels=["s_i=+1", "s_i=-1"],
        )
    # Check the axis directly for the user's orthorhombic case. A tilted (211)
    # normal is not one of the D2h C2 axes. No N-fold rule is assigned from hkl alone.
    if run["config"]["point_group"] in ["D2h", "D2"]:
        z = numeric(run["geometry"]["T"][:, 2]).real.reshape(3)
        axis = bool(np.max(np.abs(z)) > 1 - 1e-10)
        output["axis_check"] = dict(
            known=True,
            compatible=axis and parameters["N"] == 2,
            note="For this orthorhombic setting, test N=2 on a principal Cartesian axis. A general tilted surface normal is not a C2 axis.",
        )
    elif run["config"]["point_group"] in ["C2v", "C2h", "C2"]:
        z = numeric(run["geometry"]["T"][:, 2]).real.reshape(3)
        index = 2 if run["config"]["point_group"] == "C2v" else 1
        output["axis_check"] = dict(
            known=True,
            compatible=bool(abs(z[index]) > 1 - 1e-10 and parameters["N"] == 2),
            note="Check the unique C2 axis in the stated library convention.",
        )
    elif run["config"]["point_group"] in [
        "D3h",
        "D3d",
        "D6h",
        "D6",
        "D3",
        "C3v",
        "C6v",
        "D4",
        "D4h",
        "C4v",
    ]:
        z = numeric(run["geometry"]["T"][:, 2]).real.reshape(3)
        order = (
            3
            if run["config"]["point_group"] in ["D3h", "D3d", "D3", "C3v"]
            else 4 if run["config"]["point_group"] in ["D4", "D4h", "C4v"] else 6
        )
        output["axis_check"] = dict(
            known=True,
            compatible=bool(abs(z[2]) > 1 - 1e-10 and order % parameters["N"] == 0),
            note="Check the declared cyclic order about the crystallographic z axis.",
        )
    else:
        output["axis_check"] = dict(
            known=False,
            compatible=False,
            note="No automatic axis certification is supplied for this point-group setting; establish it independently.",
        )
    output["rule_applicable"] = bool(
        parameters["thin_2d_assumptions"] and output["axis_check"]["compatible"]
    )
    if not output["axis_check"]["compatible"]:
        output["scope"] = (
            "Formal congruence only: the selected normal/order is not certified as the required cyclic axis. Do not use it as an extinction prediction."
        )
    return output


def resonance_element(excitation_ev, phonon_ev, contributions):
    """Evaluate a supplied finite sum of third-order terms in Linear Eq. 9.

    Each term contains Ecv, Ecprime_v, Gamma_c, Gamma_cprime and a complex
    numerator weight. These inputs stand in for electronic/phonon matrix
    elements; they are not inferred from crystal symmetry or a band gap.
    """
    laser = np.asarray(excitation_ev, dtype=float)
    phonon = real_number(phonon_ev, "Phonon energy")
    if phonon < 0 or not np.all(np.isfinite(laser)):
        raise ValueError("Use finite laser energies and a nonnegative phonon energy.")
    result = np.zeros_like(laser, dtype=complex)
    for term in contributions:
        gap = real_number(term["Ecv"], "Transition energy")
        final_gap = real_number(term.get("Ecprime_v", gap), "Second transition energy")
        gamma = real_number(term["Gamma_c"], "Damping")
        final_gamma = real_number(term.get("Gamma_cprime", gamma), "Second damping")
        weight = complex(term["weight"])
        if gamma <= 0 or final_gamma <= 0 or not np.isfinite(weight):
            raise ValueError("Positive damping and finite complex numerator weights are required.")
        result += weight / (
            (laser - gap + 1j * gamma) * (laser - phonon - final_gap + 1j * final_gamma)
        )
    return result

print("Cell 08/22 — Run completed successfully.\nReady: Complex linear, circular-state and reference-example functions are ready.\nNext: Run Cell 09.", flush=True)


# %% Code cell 9: Polarization and interference checks
"""Independent polarization-state and within-mode interference diagnostics.

The diagnostics do not choose coefficients, align a polar plot, or replace
the selected intensity curve. They make the consequences of that selection
visible and test the coherent result by a second, entry-wise calculation.
"""

PAPER_EQUATION_MAP = "### Equation references\n\nThe tensor amplitude and coherent intensity follow the complex-response reference, Eqs. 3–4 and 12–13 (DOI 10.1039/D1CP03626B). The separate conditional circular-selection check follows Eq. 24 (DOI 10.1039/D1CP02209A). See the companion guides for conventions and limits."


def vector_samples(vector, angles):
    """Evaluate a Jones/Cartesian vector as dimension-by-angle complex samples."""
    angles = np.asarray(angles, dtype=float)
    rows = []
    for entry in sp.Matrix(vector):
        value = np.asarray(sp.lambdify(alpha, entry, "numpy")(angles), dtype=complex)
        rows.append(np.broadcast_to(value, angles.shape))
    answer = np.vstack(rows)
    if not np.all(np.isfinite(answer)):
        raise ValueError("The polarization-state samples must be finite.")
    return answer


def normalized_stokes(vector):
    """Describe one nonzero Jones state, using S3=2 Im(Ex* Ey)/S0.

    This sign is defined here; it is not an unqualified LCP/RCP name.
    Under exp[i(k.r-ω.t)], propagation-relative helicity of a pure
    circular transverse state is sign(k_z)*S3 in this laboratory frame.
    """
    vector = np.asarray(vector, dtype=complex).reshape(2)
    power = float(np.vdot(vector, vector).real)
    if power <= 0 or not np.isfinite(power):
        raise ValueError("A Jones state must have finite nonzero norm.")
    product = vector[0].conjugate() * vector[1]
    s1 = float((abs(vector[0]) ** 2 - abs(vector[1]) ** 2) / power)
    s2 = float(2 * product.real / power)
    s3 = float(2 * product.imag / power)
    kind = "circular" if abs(abs(s3) - 1) < 1e-10 else "linear" if abs(s3) < 1e-10 else "elliptical"
    return dict(S0=power, S1=s1, S2=s2, S3=s3, kind=kind)


def optical_state_audit(optical):
    """Inspect the effective incident/detection states at the sample, not after a QWP."""
    sample_angles = np.deg2rad([0, 45, 90])
    incident = vector_samples(optical["Ein"], sample_angles)
    detection = vector_samples(optical["effective_analyzer"], sample_angles)
    rows = []
    for index, angle in enumerate([0, 45, 90]):
        before = normalized_stokes(incident[:, index])
        after = normalized_stokes(detection[:, index])
        rows.append(
            dict(
                scan_angle_deg=angle,
                incident=before,
                detection=after,
                h_incident_expectation=-before["S3"],
                h_detection_expectation=after["S3"],
            )
        )
    return dict(
        effective_incident=optical["Ein"],
        effective_detection=optical["effective_analyzer"],
        return_optics=optical["B"],
        rows=rows,
        convention="Fixed laboratory XY; time dependence exp[i(k.r-ω.t)]; ki=-Z, ks=+Z.",
        helicity_note="h is an expectation for an elliptical state and a +/-1 eigenvalue only for a circular state. These h values are not substituted for the paper's s labels in Eq. 24.",
    )


def tensor_interference_audit(run):
    """Independently reconstruct complete-tensor intensities from Cartesian entries.

    Entries of each single phonon tensor are summed as amplitudes. Only after
    that operation are powers summed across orthogonal phonon partners. The
    component reference keeps its own selected curve; its coherent comparison uses
    exactly the same full tensor, orientation, states and coefficients.
    """
    angles = run["angles"]
    output, states = {}, {}
    for name, family_data in run["families"].items():
        optical = run["results"][name]["optical"]
        key = (optical["kind"], json.dumps(serializable(optical["parameters"]), sort_keys=True))
        if key not in states:
            if run["geometry"] is None:
                incident, detection = optical["Ein"], optical["effective_analyzer"]
            else:
                transform = run["geometry"]["T"] * P.T
                incident = transform * optical["Ein"]
                detection = transform * optical["effective_analyzer"]
            states[key] = vector_samples(incident, angles), vector_samples(detection, angles)
        incident, detection = states[key]
        coherent, self_power = np.zeros(len(angles)), np.zeros(len(angles))
        entries, entry_labels = [], []
        with np.errstate(over="raise", invalid="raise"):
            for partner, tensor in enumerate(family_data["numeric_partners"], 1):
                tensor = numeric(tensor)
                amplitude = np.zeros(len(angles), dtype=complex)
                for row, column in np.ndindex(tensor.shape):
                    if tensor[row, column] == 0:
                        continue
                    entry = detection[row].conjugate() * tensor[row, column] * incident[column]
                    entries.append(entry)
                    entry_labels.append(f"Partner {partner}: R_{'xyz'[row]}{'xyz'[column]}")
                    amplitude += entry
                    self_power += np.abs(entry) ** 2
                coherent += np.abs(amplitude) ** 2
        cross = coherent - self_power
        selected = run["curves"][name]
        scale = max(float(coherent.max()), float(selected.max()), np.finfo(float).tiny)
        discrepancy = float(np.max(np.abs(coherent - selected)) / scale)
        absolute_discrepancy = float(np.max(np.abs(coherent - selected)))
        # At an exact extinction, separately evaluated Cartesian amplitudes
        # can cancel to O(eps) rather than exact symbolic zero. A relative
        # comparison against the nearly zero power is then ill-conditioned.
        # Bound the amplitude roundoff by the uncancelled entry self-powers;
        # propagate it through |A+dA|^2 without altering either intensity.
        sensitivity = max(float(self_power.max()), scale)
        amplitude_roundoff = (
            128 * np.finfo(float).eps * np.sqrt(max(len(entries), 1)) * np.sqrt(sensitivity)
        )
        power_roundoff = 2 * np.sqrt(scale) * amplitude_roundoff + amplitude_roundoff**2
        reference = run["results"][name]["rule"] == "COMPONENT_POWER_SUM"
        if not reference and absolute_discrepancy > 2e-9 * scale + power_roundoff:
            raise ArithmeticError(
                "The complete-tensor curve fails its independent entry-wise contraction."
            )
        if not np.all(np.isfinite(coherent)) or not np.all(np.isfinite(self_power)):
            raise ValueError("The interference audit overflowed; rescale the tensor coefficients.")
        output[name] = dict(
            coherent_intensity=coherent,
            entry_self_power=self_power,
            interference=cross,
            selected_intensity=selected,
            entry_amplitudes=np.asarray(entries, dtype=complex).reshape(-1, len(angles)),
            entry_labels=entry_labels,
            relative_difference_from_selected=discrepancy,
            absolute_difference_from_selected=absolute_discrepancy,
            power_roundoff_bound=float(power_roundoff),
            selected_is_component_prescription=reference,
            interpretation="Entry self-powers are an algebraic diagnostic, not separate phonon intensities. Interference can be negative. Self-power and cross terms depend on the chosen component basis; the complete coherent intensity does not.",
        )
    return output


def attach_physics_audit(run):
    """Add explicit state and interference records without altering any calculated curve."""
    profiles = {}
    for result in run["results"].values():
        optical = result["optical"]
        profiles.setdefault(optical["kind"], optical_state_audit(optical))
    run["physics"] = dict(
        optical_states=profiles,
        interference=tensor_interference_audit(run),
        uses_coherent_intensity=not any(
            result["rule"] == "COMPONENT_POWER_SUM" for result in run["results"].values()
        ),
        validation_scope="Algebra/model consistency only; not experimental certification or a microscopic tensor prediction.",
    )
    return run


def physics_audit_markdown(run):
    """Explain Jones-state conventions and demonstrate retained within-mode interference."""
    lines = [
        "## Polarization and interference checks",
        "This record uses the active tensor, geometry, coefficients and optics. It does not alter the selected curve.",
    ]
    if not run["physics"]["uses_coherent_intensity"]:
        lines.append(
            "**Component reference:** the requested Ag component-intensity curve is preserved. The coherent column below is a separately calculated comparison for the same complete tensor and states. Linear Eqs. 3–4 prescribe the coherent column for one phonon, unless incoherent averaging is independently justified."
        )
    if run["geometry"] is None:
        lines.append(
            "**Original Quarter-wave-plate source:** the Jones chain and coherent law are reproduced. Its antisymmetric off-diagonal model is not certified as a reciprocal nonmagnetic crystal tensor by the Linear review. Select the 3D crystal extension for the symmetry-allowed material tensors."
        )
    variable = theta_scan if run["optical"].get("scan_basis") == "SECOND" else alpha
    for name, profile in run["physics"]["optical_states"].items():
        lines += [
            "### " + OPTICS_LABELS[name],
            r"$$e_{s,\mathrm{sample}}=B^\dagger e_{\mathrm{analyzer}}="
            + raman_latex(profile["effective_detection"].subs(alpha, variable))
            + "$$",
        ]
        table = [
            "| Scan angle (degrees) | Input state | Input S3 | Detection at sample | Detection S3 |",
            "|---:|---|---:|---|---:|",
        ]
        for row in profile["rows"]:
            table.append(
                f"| {row['scan_angle_deg']} | {row['incident']['kind']} | {row['incident']['S3']:.5g} | {row['detection']['kind']} | {row['detection']['S3']:.5g} |"
            )
        lines.append("\n".join(table))
    lines += [
        "S3=2 Im(Ex* Ey)/S0 refers to one fixed laboratory XY basis. With exp[i(k.r-ω.t)], ki=-Z and ks=+Z, propagation-relative circular helicity is hi=-S3i and hs=+S3s. Thus equal laboratory circular labels are not automatically equal propagation-relative helicities. The paper's Eq. 11 labels are retained explicitly in the separate Eq. 24 checker.",
        r"$$I_{\mathrm{coherent}}=\sum_\nu\left|\sum_j A_{\nu j}\right|^2=\sum_{\nu,j}|A_{\nu j}|^2+2\operatorname{Re}\sum_\nu\sum_{j<k}A_{\nu j}A_{\nu k}^*.$$",
        "Here ν labels orthogonal unresolved phonon partners, while j labels tensor-entry contributions within one partner. Negative cross terms describe destructive interference; they are not negative measured intensities.",
    ]
    table = [
        "| Mode / channel | Angle (degrees) | Entry self-powers | Interference | Complete coherent I | Selected curve I |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, item in run["physics"]["interference"].items():
        for angle in [0, 45, 90]:
            index = int(np.argmin(np.abs(np.rad2deg(run["angles"]) - angle)))
            fields = [
                item[key][index]
                for key in [
                    "entry_self_power",
                    "interference",
                    "coherent_intensity",
                    "selected_intensity",
                ]
            ]
            table.append(
                f"| {name} | {np.rad2deg(run['angles'][index]):.4g} | "
                + " | ".join(f"{value:.7g}" for value in fields)
                + " |"
            )
    lines.append("\n".join(table))
    lines.append(
        "The entry split is an algebraic explanation, not a decomposition into independent phonons. Only the complete intensity is invariant under a change of Cartesian basis. Raw angle-resolved audit data are included in the result ZIP."
    )
    return "\n\n".join(lines)

print("Cell 09/22 — Run completed successfully.\nReady: Polarization-state and interference diagnostics are ready.\nNext: Run Cell 10.", flush=True)


# %% Code cell 10: Common calculation pipeline
"""Validate one declared experiment and run the same scattering engine for all modes."""


def validate_lattice_for_group(config):
    """Check consistency between the conventional cell setting and tensor axes.

    Trigonal presets use a conventional hexagonal cell, not rhombohedral
    primitive indices. A custom Cartesian tensor can use a general cell.
    """
    lattice = np.array(config["lattice"], dtype=float)
    if lattice.shape != (6,) or not np.all(np.isfinite(lattice)):
        raise ValueError("The lattice requires six finite numerical parameters.")
    if config["point_group"] not in POINT_GROUPS:
        return
    system = POINT_GROUPS[config["point_group"]]["system"]
    close = lambda actual, expected: np.allclose(actual, expected, rtol=0, atol=1e-9)
    if system in ["orthorhombic", "tetragonal", "cubic"] and not close(lattice[3:], 90):
        raise ValueError("This conventional tensor setting requires α=β=γ=90°.")
    if system in ["trigonal", "hexagonal"]:
        if not close(lattice[3:], [90, 90, 120]) or not close(lattice[0], lattice[1]):
            raise ValueError(
                "Use the conventional hexagonal setting: a0=b0, α=β=90°, γ=120°."
            )
    if system in ["tetragonal", "cubic"] and not close(lattice[0], lattice[1]):
        raise ValueError("This symmetry requires a0=b0 in the selected setting.")
    if system == "cubic" and not close(lattice[1], lattice[2]):
        raise ValueError("Cubic symmetry requires a0=b0=c0.")
    if system == "monoclinic" and not close(lattice[[3, 5]], 90):
        raise ValueError("The unique-y setting requires α=γ=90°; β may differ.")


def demonstration_config(material="Si", optics="CUBIC_VV"):
    """Build an explicitly illustrative starting configuration, without running it."""
    if material not in MATERIALS:
        raise ValueError("Unknown material preset.")
    info = MATERIALS[material]
    definitions = definitions_for(material, info["group"])
    hkl, uvw = SURFACES[info["surface"]]
    method = (
        "CUBIC_REF"
        if optics.startswith("CUBIC_")
        else (
            "CIRCULAR"
            if optics.startswith("CIRCULAR_")
            else (
                "LINEAR"
                if optics.startswith("LINEAR_")
                else "QWP" if optics == "QWP" else "COMPONENT_REFERENCE"
            )
        )
    )
    return dict(
        calculation_method=method,
        paper_parameters=default_paper_parameters(method),
        tensor_model="CRYSTAL_3D",
        source_parameters=None,
        case_label=f"{material} demonstration",
        input_note="Illustrative coefficients and lattice ratios; replace with sample-specific inputs.",
        material=material,
        point_group=info["group"],
        modes=list(definitions),
        mode_values={
            name: {symbol: DEFAULT_VALUES[symbol] for symbol in parameters_for(item)}
            for name, item in definitions.items()
        },
        custom_tensor=None,
        lattice=info["lattice"],
        orientation="hkl",
        hkl=hkl,
        uvw=uvw,
        azimuth_deg=0,
        normal_sign=1,
        allow_reflection=False,
        T_manual=sp.eye(3),
        optics=optics,
        direct_jones=dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=45, beta_s_deg=0),
        ag_rule=(
            "REFERENCE_AG_COMPONENT_SUM"
            if method == "COMPONENT_REFERENCE"
            else "COHERENT_SINGLE_TENSOR"
        ),
        normalize=False,
        show_steps=True,
        show_components=True,
        show_geometry=True,
        plot_points=721,
    )


def component_reference_config():
    """Declare the user's slides 12–14 as a named, fully visible reference case."""
    config = demonstration_config("CaNb2O6", "COMPONENT_SIGMA_ALPHA")
    config.update(copy.deepcopy(COMPONENT_REFERENCE_GEOMETRY))
    config.update(
        case_label="Component reference Ag reference (211), slides 12–14",
        input_note="Unity lattice metric and the explicit reference frame from the REFERENCE reconstruction; coefficients are illustrative.",
        modes=["Ag"],
        direct_jones=dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=45, beta_s_deg=90),
    )
    return config


def qwp_source_config():
    """Create a faithful original-source case, without inactive crystal/REFERENCE inputs."""
    return dict(
        calculation_method="QWP",
        tensor_model="QWP_SOURCE_2D",
        source_parameters=dict(a=1, A=0.4, delta_deg=60, phi_deg=60),
        case_label="Original Quarter-wave-plate source model",
        input_note="Main calculation of the supplied Quarter-wave-plate notebook; a=1, A=0.4, δ=φ=60 degrees is an illustrative source example.",
        material=None,
        point_group=None,
        optics="QWP",
        direct_jones=None,
        ag_rule="COHERENT_SINGLE_TENSOR",
        normalize=False,
        show_steps=True,
        show_components=True,
        show_geometry=False,
        plot_points=721,
    )


def physical_start_config():
    """Start with coherent circular-input optics on a principal CaNb2O6 surface."""
    config = demonstration_config("CaNb2O6", "QWP")
    config.update(
        hkl=(1, 0, 0),
        uvw=(0, 1, 0),
        case_label="Coherent CaNb2O6 (100): Quarter-wave-plate 3D extension",
        input_note="Symmetry-allowed full 3×3 D2h tensors and unchanged Quarter-wave-plate optics. Coefficients are illustrative. The principal (100) orientation does not require an assumed tilted-surface lattice ratio.",
    )
    return config


def validate_method_policy(config):
    """Reject hybrid configurations instead of silently mixing the two methods."""
    method = config.get("calculation_method")
    if method not in METHOD_LABELS:
        raise ValueError("Select a declared calculation workflow explicitly.")
    model = config.get("tensor_model")
    if model not in TENSOR_MODEL_LABELS:
        raise ValueError("Select a declared tensor model.")
    if method == "GENERAL":
        if model != "CRYSTAL_3D" or config.get("optics") not in OPTICS_LABELS:
            raise ValueError(
                "General calculations require a crystal 3D tensor and a declared optical profile."
            )
        if config.get("ag_rule", "COHERENT_SINGLE_TENSOR") != "COHERENT_SINGLE_TENSOR":
            raise ValueError(
                "The complete phonon tensor remains coherent; Cartesian plots are separate diagnostics."
            )
        config["ag_rule"] = "COHERENT_SINGLE_TENSOR"
        config["paper_parameters"] = {
            **default_paper_parameters("CIRCULAR"),
            "theta0_deg": 0,
            **(config.get("paper_parameters") or {}),
        }
        return
    if method == "QWP":
        if config.get("optics") != "QWP":
            raise ValueError(
                "The Quarter-wave-plate workflow requires the original Quarter-wave-plate optical chain."
            )
        expected_rule = "COHERENT_SINGLE_TENSOR"
    elif method == "COMPONENT_REFERENCE":
        if config.get("optics") not in ["COMPONENT_SIGMA_ALPHA", "DIRECT_JONES"]:
            raise ValueError(
                "The component reference workflow requires its direct Jones states, without a Quarter-wave-plate return QWP."
            )
        if model != "CRYSTAL_3D":
            raise ValueError("The component reference workflow requires its 3×3 crystal tensors.")
        expected_rule = "REFERENCE_AG_COMPONENT_SUM"
    else:
        permitted = (
            ["CUBIC_VV", "CUBIC_VH", "CUBIC_SIGMA"]
            if method == "CUBIC_REF"
            else (
                ["CIRCULAR_LINEAR", "CIRCULAR_SAME", "CIRCULAR_OPPOSITE"]
                if method == "CIRCULAR"
                else ["LINEAR_PARALLEL", "LINEAR_CROSSED", "LINEAR_PAIR"]
            )
        )
        if config.get("optics") not in permitted or model != "CRYSTAL_3D":
            raise ValueError(
                "The selected paper workflow requires its own crystal/Jones configuration."
            )
        expected_rule = "COHERENT_SINGLE_TENSOR"
        config["paper_parameters"] = {
            **default_paper_parameters(method),
            **(config.get("paper_parameters") or {}),
        }
    if config.get("ag_rule", expected_rule) != expected_rule:
        raise ValueError("The Ag combination rule conflicts with the selected calculation method.")
    config["ag_rule"] = expected_rule
    if method not in ["CIRCULAR", "LINEAR", "CUBIC_REF"]:
        config["paper_parameters"] = None


def assemble_calculated_run(config, geometry, optical, families, record_builder, assumptions):
    """Evaluate already-selected channels; this helper cannot choose a method policy."""
    angles = np.linspace(0, 2 * np.pi, config["plot_points"])
    results, curves, summaries, component_curves, circular_projections = {}, {}, {}, {}, {}
    for name, family_data in families.items():
        selected_optical = family_data.get("optical", optical)
        records = [
            record_builder(tensor, selected_optical)
            for tensor in family_data["calculation_tensors"]
        ]
        result = dict(terms=records, rule=family_data["rule"], optical=selected_optical)
        evaluated = evaluate_terms(result, family_data["values"], angles)
        result["numeric_pairs"] = evaluated["pairs"]
        results[name] = result
        curves[name] = evaluated["total"]
        summaries[name] = evaluated["summary"]
        component_curves[name] = evaluated["components"]
        projected = {}
        for label, state_s in [("s_out=+, s_in=+", sig_p), ("s_out=-, s_in=+", sig_m)]:
            amplitudes = [
                complex(sp.N((state_s.H * record["Rperp"] * sig_p)[0].subs(family_data["values"])))
                for record in records
            ]
            with np.errstate(over="raise", invalid="raise"):
                value = float(np.sum(np.abs(amplitudes) ** 2))
            if not np.isfinite(value):
                raise ValueError("The circular-basis projection is not finite; rescale the tensor.")
            projected[label] = value
        circular_projections[name] = projected
    return dict(
        config=config,
        geometry=geometry,
        optical=optical,
        families=families,
        results=results,
        angles=angles,
        curves=curves,
        summaries=summaries,
        component_curves=component_curves,
        circular_projections=circular_projections,
        assumptions=assumptions,
        scan_label=(
            "Polarization angle θ (°)"
            if optical.get("scan_basis") == "SECOND"
            else "Detection angle α (°)"
        ),
        scan_kind=(
            "Co-rotating linear"
            if optical.get("scan_basis") == "SECOND"
            else (
                "Fixed circular channel"
                if optical.get("scan_basis") == "CONSTANT"
                else "Detection-state scan"
            )
        ),
    )


def calculate_qwp_source(config):
    """Run the original 2×2 source tensor with the original coherent intensity law.

    No lattice, rotation, material tensor, REFERENCE channel selection or component reference
    function is called on this route. The plotted curve comes from Q.T*R*Q*x.
    """
    values = qwp_source_values(config["source_parameters"])
    # Drop inactive crystal fields if a scripted caller supplied them.
    for key in [
        "lattice",
        "orientation",
        "hkl",
        "uvw",
        "azimuth_deg",
        "normal_sign",
        "allow_reflection",
        "T_manual",
        "custom_tensor",
        "mode_values",
        "modes",
    ]:
        config.pop(key, None)
    config.update(material=None, point_group=None, direct_jones=None, show_geometry=False)
    optical = optical_chain("QWP")
    config["effective_optical_parameters"] = copy.deepcopy(optical["parameters"])
    item = dict(
        irrep="Effective source model (not a crystal irrep)",
        partners=[QWP_SOURCE_TENSOR],
        numeric_partners=[QWP_SOURCE_TENSOR.subs(values)],
        calculation_tensors=[QWP_SOURCE_TENSOR],
        calculation_labels=["Complete Quarter-wave-plate source tensor"],
        values=values,
        rule="SINGLE_TENSOR",
        combination_reason="One complete tensor amplitude, followed by one squared modulus, exactly as in the Quarter-wave-plate main source.",
        note="The antisymmetric off-diagonal entries belong to this source model; they are not imposed on an orthorhombic material.",
    )
    run = assemble_calculated_run(
        config,
        None,
        optical,
        {QWP_MODE: item},
        lambda tensor, selected_optical: transverse_amplitude_record(tensor, selected_optical),
        [
            "Original Quarter-wave-plate main-source tensor and optical convention; the alternative appendix convention is not selected.",
            "a and A are real amplitudes; δ and φ are real phases. Input phases use degrees.",
            "This effective 2×2 source model has no surface-orientation parameter.",
        ],
    )
    return attach_physics_audit(run)


def calculate_experiment(configuration):
    """Return computed matrices, curves and summaries; never fit to a target plot.

    Configuration is copied before calculation. Reference formulas are
    deliberately outside this function and cannot determine its output.
    """
    config = copy.deepcopy(configuration)
    validate_method_policy(config)
    if not isinstance(config["plot_points"], int) or not 361 <= config["plot_points"] <= 3601:
        raise ValueError("Use between 361 and 3601 detection-angle samples.")
    if config["tensor_model"] == "QWP_SOURCE_2D":
        return calculate_qwp_source(config)
    if config["material"] not in MATERIALS:
        raise ValueError("Unknown material preset.")
    config["source_parameters"] = None
    validate_lattice_for_group(config)
    geometry = build_orientation(config)
    optical = optical_chain(
        config["optics"], config.get("direct_jones"), config.get("paper_parameters")
    )
    if config["calculation_method"] == "CIRCULAR" or (
        config["calculation_method"] == "GENERAL" and config["optics"].startswith("CIRCULAR_")
    ):
        parameters = config["paper_parameters"]
        circular_congruence(
            parameters["N"],
            parameters["s_in"],
            1,
            parameters["ell_i"],
            parameters["m_ph"],
            parameters.get("absorption_delta_m"),
        )
        if not isinstance(parameters["thin_2d_assumptions"], (bool, np.bool_)):
            raise ValueError("Declare the Circular thin-2D/electronic assumptions as a Boolean.")
    # Fixed profiles export their actual values; inactive direct controls are not exported as active inputs.
    config["effective_optical_parameters"] = copy.deepcopy(optical["parameters"])
    if config["optics"] != "DIRECT_JONES":
        config["direct_jones"] = None
    families = experiment_families(config)
    if config["calculation_method"] == "LINEAR":
        if any(
            not zero(tensor - tensor.T)
            for item in families.values()
            for tensor in item["calculation_tensors"]
        ):
            raise ValueError(
                "The Complex linear model workflow assumes a reciprocal symmetric tensor R.T=R. Use another explicitly justified model for a nonsymmetric tensor."
            )
    if config["optics"] == "LINEAR_PAIR":
        paired = {}
        for name, item in families.items():
            for channel, kind in [
                ("parallel", "LINEAR_PARALLEL"),
                ("crossed", "LINEAR_CROSSED"),
            ]:
                selected = copy.deepcopy(item)
                selected.update(
                    base_mode=name,
                    polarization_channel=channel,
                    optical=optical_chain(kind, paper=config["paper_parameters"]),
                )
                paired[name + " [" + channel + "]"] = selected
        families = paired
    assumptions = [
        "Collinear normal-incidence/backscattering geometry; ideal external polarization optics.",
        "Tensor entries are supplied coefficients, not fitted or first-principles predictions.",
        "Internal birefringence, Fresnel corrections, finite-NA averaging and CDW supercells are not included.",
    ]
    if any(item["rule"] == "COMPONENT_POWER_SUM" for item in families.values()):
        assumptions.append(
            "D2h Ag uses the user-prescribed component-intensity sum, not the standard coherent single-phonon Ag contraction."
        )
    if config["calculation_method"] == "QWP":
        assumptions.append(
            "3D rotation is an explicit extension: a rotated/projected crystal tensor replaces the original source tensor. The Quarter-wave-plate Jones sequence and coherent intensity law remain unchanged."
        )
        if any(len(item["partners"]) > 1 for item in families.values()):
            assumptions.append(
                "The sum over orthogonal degenerate phonon partners is a material-library extension; it is not a split of the elements of one tensor."
            )
    elif config["calculation_method"] == "CIRCULAR" or (
        config["calculation_method"] == "GENERAL" and config["optics"].startswith("CIRCULAR_")
    ):
        assumptions.extend(
            [
                "The supplied Circular-channel model paper gives conditional angular-momentum selection rules; it does not calculate vortex Raman intensities.",
                "Displayed intensities are ℓ=0 plane-wave Jones calculations. The separate vortex congruence check never masks or rescales those curves.",
                "The rule checker uses user-declared phonon charges; they are not assigned automatically to all selected modes.",
            ]
        )
    elif config["calculation_method"] == "CUBIC_REF":
        assumptions.extend(
            [
                "Cubic reference Section 2.2 states; the σ⁺α detector is an effective elliptical-state scan, with no extra Quarter-wave-plate return QWP.",
                "For Si, sum complete-tensor intensities over the three orthogonal T2g partners (Eq. 9). This is not a sum over Cartesian entries within one phonon.",
                "The Fig. 1 benchmark locks the cubic paper axes and d across all six surfaces. Other materials/orientations are a Jones/tensor extension, not a claimed paper benchmark.",
            ]
        )
    elif config["calculation_method"] == "LINEAR":
        assumptions.extend(
            [
                "Incident and detected linear polarization rotate together; θ is not the σ⁺α analyzer scan.",
                "One coefficient set is shared between parallel and crossed curves of each branch. The curves are calculations, not fits to supplied data.",
                "A real rotation acts as T.T*R*T even when R is complex; R.T=R does not require R.H=R.",
            ]
        )
    run = assemble_calculated_run(
        config,
        geometry,
        optical,
        families,
        lambda tensor, selected_optical: amplitude_record(tensor, geometry["T"], selected_optical),
        assumptions,
    )
    if config["calculation_method"] == "CIRCULAR" or (
        config["calculation_method"] == "GENERAL" and config["optics"].startswith("CIRCULAR_")
    ):
        run["circular"] = circular_diagnostics(run)
    return attach_physics_audit(run)


def benchmark_config(material, base):
    """Create a comparison example with its own declared lattice and surface.

    Display settings and the selected optical profile are copied. Material
    coefficients and geometry come from that material's illustrative preset.
    """
    if base["tensor_model"] == "QWP_SOURCE_2D":
        raise ValueError(
            "Select the 3D rotation extension for material comparisons; the original Quarter-wave-plate source has no material library."
        )
    config = demonstration_config(material, base["optics"])
    for key in [
        "normalize",
        "show_steps",
        "show_components",
        "show_geometry",
        "plot_points",
        "direct_jones",
        "paper_parameters",
    ]:
        if key in base:
            config[key] = copy.deepcopy(base[key])
    return config


"""One physical-input contract and separate Cartesian Ag presentation channels."""

GENERAL_PROFILES = {
    "CUBIC_VV": "VV: parallel linear states, scan θ",
    "CUBIC_VH": "VH: crossed linear states, scan θ",
    "LINEAR_PAIR": "VV and VH together, one coefficient set",
    "CIRCULAR_LINEAR": "Circular input / direct linear analyzer, scan α",
    "CUBIC_SIGMA": "σ⁺α reference: elliptical detection-state scan",
    "QWP": "Input QWP / Raman tensor / return QWP / linear analyzer",
    "CIRCULAR_SAME": "Same fixed circular basis label",
    "CIRCULAR_OPPOSITE": "Opposite fixed circular basis label",
    "DIRECT_JONES": "Custom direct Jones input and detection states",
}


def general_config(material="Si", optics="CUBIC_VV"):
    """Create general crystal inputs; the optical protocol is independent of material."""
    if optics not in GENERAL_PROFILES:
        raise ValueError("Choose a declared general optical protocol.")
    cfg = demonstration_config(material, optics)
    cfg.update(
        calculation_method="GENERAL",
        ag_rule="COHERENT_SINGLE_TENSOR",
        tensor_model="CRYSTAL_3D",
        paper_parameters={**default_paper_parameters("CIRCULAR"), "theta0_deg": 0},
        split_ag_plots=True,
        cartesian_plots=False,
        include_complete_audit=False,
        report_view="GENERAL",
        plot_points=721,
    )
    if material == "Si":
        cfg.update(hkl=(5, 0, 0), uvw=(0, -5, 0), normal_sign=1)
        cfg["mode_values"]["T2g"] = {d: exact(1)}
    return cfg


def slide_component_config():
    """Use the slide XY frame and Jones states, with separate Ag component plots."""
    cfg = general_config("CaNb2O6", "CUBIC_SIGMA")
    cfg.update(copy.deepcopy(COMPONENT_REFERENCE_GEOMETRY))
    cfg.update(
        modes=["Ag"],
        case_label="Ag components on the (211) reference frame",
        input_note="Unity metric reproduces the slide XY convention. Enter actual lattice ratios for a physical tilted CaNb2O6 surface.",
    )
    return cfg


def cartesian_tensor_parts(tensor):
    """Decompose a complete tensor without discarding off-diagonal entries.

    Symmetric xy/xz/yz pairs are kept together. If an explicitly supplied
    nonsymmetric tensor is used, its ordered entries remain separate.
    Zero xx,yy,zz contributions are retained for an Ag display.
    """
    R = sp.Matrix(tensor)
    parts = {}
    for i in range(3):
        item = sp.zeros(3)
        item[i, i] = R[i, i]
        parts["xyz"[i] * 2] = item
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        if zero(sp.Matrix([R[i, j], R[j, i]])):
            continue
        if zero(sp.Matrix([R[i, j] - R[j, i]])):
            item = sp.zeros(3)
            item[i, j], item[j, i] = R[i, j], R[j, i]
            parts["xyz"[i] + "xyz"[j]] = item
        else:
            for row, col in [(i, j), (j, i)]:
                if R[row, col] == 0:
                    continue
                item = sp.zeros(3)
                item[row, col] = R[row, col]
                parts["xyz"[row] + "xyz"[col]] = item
    check(zero(sum(parts.values(), sp.zeros(3)) - R), "Cartesian tensor reconstruction failed.")
    return parts


def attach_display_channels(run):
    """Calculate individual Ag(xx),Ag(yy),Ag(zz) plots using the same engine.

    The complete-mode run is retained for physics checks. Separate Cartesian
    intensities are never presented as independent phonon modes or summed
    into the displayed Ag result. Non-diagonal Ag forms also retain every
    allowed off-diagonal component, so no part of a general Ag tensor is lost.
    """
    channels = {}
    for name, result in run["results"].items():
        family_data = run["families"][name]
        optical = result.get("optical", run["optical"])
        base_name = family_data.get("base_mode", name)
        suffix = name[len(base_name) :] if name.startswith(base_name) else ""
        is_ag = family_data.get("irrep") == "Ag" and run["geometry"] is not None
        if is_ag:
            check(
                len(family_data["partners"]) == 1,
                "An Ag family must be nondegenerate in this library.",
            )
            pieces = cartesian_tensor_parts(family_data["partners"][0])
            for component, Rc in pieces.items():
                record = amplitude_record(Rc, run["geometry"]["T"], optical)
                evaluated = evaluate_terms(
                    dict(terms=[record]), family_data["values"], run["angles"]
                )
                label = base_name + "(" + component + ")" + suffix
                channels[label] = dict(
                    name=label,
                    base_mode=base_name,
                    source_mode=name,
                    component=component,
                    kind="Cartesian contribution of one Ag phonon",
                    optical=optical,
                    records=[record],
                    values=family_data["values"],
                    curve=evaluated["total"],
                    summary=evaluated["summary"],
                    partner_curves=evaluated["components"],
                    normalization_group=base_name,
                )
        else:
            channels[name] = dict(
                name=name,
                base_mode=base_name,
                source_mode=name,
                component=None,
                kind=(
                    "Complete phonon tensor"
                    if len(result["terms"]) == 1
                    else "Orthogonal unresolved phonon partners"
                ),
                optical=optical,
                records=result["terms"],
                values=family_data["values"],
                curve=run["curves"][name],
                summary=run["summaries"][name],
                partner_curves=run["component_curves"][name],
                normalization_group=base_name,
            )
    run["display_channels"] = channels
    run["display_curves"] = {name: item["curve"] for name, item in channels.items()}
    run["display_summaries"] = {name: item["summary"] for name, item in channels.items()}
    run["presentation_policy"] = {
        "Ag": "Separate Cartesian component powers; no Ag component sum in the main plots or main CSV.",
        "complete_mode": "Retained separately for coherent-interference checks; hidden from component plots.",
        "degenerate_modes": "Sum powers over orthogonal unresolved complete phonon partners.",
        "normalization": "One common scale per base mode, including its Ag components and paired VV/VH channels.",
    }
    return run


def calculate_general(configuration):
    """Use the same geometric/Jones contraction for every selected crystal."""
    cfg = copy.deepcopy(configuration)
    if cfg["tensor_model"] != "QWP_SOURCE_2D":
        cfg["calculation_method"] = "GENERAL"
        cfg["ag_rule"] = "COHERENT_SINGLE_TENSOR"
        cfg["paper_parameters"] = {
            **default_paper_parameters("CIRCULAR"),
            "theta0_deg": 0,
            **(cfg.get("paper_parameters") or {}),
        }
    run = calculate_experiment(cfg)
    run = attach_display_channels(run)
    run["style"] = copy.deepcopy(PLOT_STYLE_STATUS)
    return run


def symbolic_intensity_summary(records):
    """Derive all harmonic coefficients before numerical coefficient substitution."""
    basis = records[0].get("scan_basis", "FIRST")
    expand_real = lambda z: sp.factor_terms(sp.expand(z))
    if basis == "CONSTANT":
        power = sum((r["K0"] * sp.conjugate(r["K0"]) for r in records), sp.S.Zero)
        return dict(I0=expand_real(power), Ic=sp.S.Zero, Is=sp.S.Zero)
    if basis == "FIRST":
        cc = sum((r["C"] * sp.conjugate(r["C"]) for r in records), sp.S.Zero)
        dd = sum((r["D"] * sp.conjugate(r["D"]) for r in records), sp.S.Zero)
        cross = sum((r["C"] * sp.conjugate(r["D"]) for r in records), sp.S.Zero)
        return dict(
            I0=expand_real((cc + dd) / 2),
            Ic=expand_real((cc - dd) / 2),
            Is=expand_real((cross + sp.conjugate(cross)) / 2),
        )
    p0 = sum((r["K0"] * sp.conjugate(r["K0"]) for r in records), sp.S.Zero)
    pc = sum((r["Kc"] * sp.conjugate(r["Kc"]) for r in records), sp.S.Zero)
    ps = sum((r["Ks"] * sp.conjugate(r["Ks"]) for r in records), sp.S.Zero)
    c0 = sum((r["K0"] * sp.conjugate(r["Kc"]) for r in records), sp.S.Zero)
    s0 = sum((r["K0"] * sp.conjugate(r["Ks"]) for r in records), sp.S.Zero)
    cs = sum((r["Kc"] * sp.conjugate(r["Ks"]) for r in records), sp.S.Zero)
    return dict(
        I0=expand_real(p0 + (pc + ps) / 2),
        Ic=expand_real(c0 + sp.conjugate(c0)),
        Is=expand_real(s0 + sp.conjugate(s0)),
        I4c=expand_real((pc - ps) / 2),
        I4s=expand_real((cs + sp.conjugate(cs)) / 2),
    )


def matching_protocol_audit(run):
    """Compare three independent representations using identical physical states."""
    U = numeric(sp.Matrix.hstack(sig_p, sig_m))
    rows = []
    for name, channel in run["display_channels"].items():
        optical, values = channel["optical"], channel["values"]
        Ei = vector_samples(optical["Ein"], run["angles"])
        es = vector_samples(optical["effective_analyzer"], run["angles"])
        direct = np.zeros(len(run["angles"]))
        circular = np.zeros_like(direct)
        for record in channel["records"]:
            R = numeric(record["Rperp"].subs(values))
            A = np.einsum("in,ij,jn->n", es.conj(), R, Ei)
            z_i, z_s = U.conj().T @ Ei, U.conj().T @ es
            A_circ = np.einsum("in,ij,jn->n", z_s.conj(), U.conj().T @ R @ U, z_i)
            direct += np.abs(A) ** 2
            circular += np.abs(A_circ) ** 2
        curve = channel["curve"]
        scale = max(float(np.max(curve)), 1e-14)
        error_direct = float(np.max(np.abs(direct - curve)))
        error_circular = float(np.max(np.abs(circular - curve)))
        check(error_direct <= 2e-10 * scale + 1e-13, name + ": direct contraction failed.")
        check(
            error_circular <= 2e-10 * scale + 1e-13,
            name + ": circular-basis reconstruction failed.",
        )
        rows.append(dict(channel=name, direct_error=error_direct, circular_error=error_circular))
    return rows


def protocol_state_comparison():
    """State-projector differences identify different experiments, without curve alignment."""
    grid = np.array([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4])
    kinds = ["QWP", "CUBIC_SIGMA", "CIRCULAR_LINEAR"]
    states = {}
    for kind in kinds:
        optical = optical_chain(kind)
        v = vector_samples(optical["effective_analyzer"], grid)
        states[kind] = v
    rows = []
    for i, first in enumerate(kinds):
        for second in kinds[i + 1 :]:
            distances = []
            for q in range(len(grid)):
                x, y = states[first][:, q], states[second][:, q]
                distances.append(
                    float(np.linalg.norm(np.outer(x, x.conj()) - np.outer(y, y.conj())))
                )
            rows.append(
                dict(
                    first=first,
                    second=second,
                    projector_distances=distances,
                    same_states=all(x < 1e-12 for x in distances),
                )
            )
    return rows

print("Cell 10/22 — Run completed successfully.\nReady: The common material-to-intensity calculation pipeline is ready.\nNext: Run Cell 11.", flush=True)


# %% Code cell 11: Slide reference algebra
"""A separate derivation/check of the user-provided component reference, not a plotting engine."""

@lru_cache(maxsize=1)
def component_ag_symbolics():
    """Derive the reference equations from rotated rank-one tensor components.

    Even the display denominator is obtained from the algebra. The generic
    scattering engine does not call this reference function.
    """
    theta, beta, beta_prime = sp.symbols("theta beta beta_prime", real=True)
    amplitude_a, amplitude_b, amplitude_c = sp.symbols("a b c", nonnegative=True)
    frame = build_orientation(COMPONENT_REFERENCE_GEOMETRY)["T"]
    parts, weights = [], []
    for index, coefficient in enumerate([amplitude_a, amplitude_b, amplitude_c]):
        vector = tidy(P * frame.T * sp.eye(3)[:, index])

        def projected_power(angle, phase):
            """Evaluate the Jones-state power projected onto one rotated real vector."""
            # |vx*cos(angle)+vy*exp(i*phase)*sin(angle)|² for a real geometric vector.
            return tidy(
                (vector[0] ** 2 + vector[1] ** 2) / 2
                + (vector[0] ** 2 - vector[1] ** 2) * sp.cos(2 * angle) / 2
                + vector[0] * vector[1] * sp.sin(2 * angle) * sp.cos(phase)
            )

        input_power = projected_power(theta, beta)
        output_power = projected_power(theta + alpha, beta_prime)
        weights.append((input_power, output_power))
        parts.append(coefficient**2 * input_power * output_power)
    general = sum(parts)
    canonical = sp.expand(general)
    # Extract rational numerical denominators; no value 144 is supplied to the derivation.
    denominators = [sp.denom(term.as_coeff_Mul()[0]) for term in canonical.as_ordered_terms()]
    denominator = sp.ilcm(*denominators)
    u, v, sine_i, sine_s, phase_i, phase_s = sp.symbols("u v s t p q", real=True)
    substitutions = {
        sp.cos(2 * theta): u,
        sp.cos(2 * (theta + alpha)): v,
        sp.sin(2 * theta): sine_i,
        sp.sin(2 * (theta + alpha)): sine_s,
        sp.cos(beta): phase_i,
        sp.cos(beta_prime): phase_s,
    }
    polynomial = sp.Poly(
        sp.expand(denominator * canonical.xreplace(substitutions)),
        u,
        v,
        sine_i,
        sine_s,
        phase_i,
        phase_s,
    )
    coefficient = lambda monomial: sp.factor_terms(polynomial.coeff_monomial(monomial))
    constant = coefficient(1)
    linear = coefficient(u)
    bilinear = coefficient(u * v)
    phase_constant = coefficient(sine_i * phase_i)
    phase_linear = coefficient(v * sine_i * phase_i)
    mixed = coefficient(sine_i * sine_s * phase_i * phase_s)
    offset = sp.cancel(phase_constant / phase_linear)
    grouped = (
        constant
        + linear * (u + v)
        + bilinear * u * v
        + phase_linear * (offset + v) * sine_i * phase_i
        + phase_linear * (offset + u) * sine_s * phase_s
        + mixed * sine_i * sine_s * phase_i * phase_s
    )
    check(
        sp.expand(grouped - polynomial.as_expr()) == 0,
        "The grouped REFERENCE expansion failed its symbolic identity check.",
    )
    numerator = grouped.xreplace({value: key for key, value in substitutions.items()})
    special = sp.expand(general.subs({theta: sp.pi / 4, beta: sp.pi / 2, beta_prime: sp.pi / 2}))
    final_numerator = sp.collect(sp.expand(denominator * special), sp.sin(2 * alpha))
    return dict(
        T=frame,
        theta=theta,
        beta=beta,
        beta_prime=beta_prime,
        coefficients=(amplitude_a, amplitude_b, amplitude_c),
        weights=weights,
        parts=parts,
        general=general,
        expanded=numerator / denominator,
        expanded_numerator=numerator,
        denominator=denominator,
        special=special,
        final_numerator=final_numerator,
    )


def component_reference_matches(run):
    """Identify the reference geometry/state explicitly; never alter an input to match it."""
    config = run["config"]
    if (
        config.get("calculation_method") != "COMPONENT_REFERENCE"
        or config["point_group"] != "D2h"
        or "Ag" not in run["results"]
    ):
        return False
    if run["results"]["Ag"]["rule"] != "COMPONENT_POWER_SUM":
        return False
    direct = config.get("direct_jones") or {}
    same_state = config["optics"] == "COMPONENT_SIGMA_ALPHA" or (
        config["optics"] == "DIRECT_JONES"
        and all(
            key in direct and abs(float(direct[key]) - expected) < 1e-10
            for key, expected in [
                ("theta_i_deg", 45),
                ("beta_i_deg", 90),
                ("theta_s0_deg", 45),
                ("beta_s_deg", 90),
            ]
        )
    )
    reference_frame = build_orientation(COMPONENT_REFERENCE_GEOMETRY)["T"]
    return same_state and np.allclose(
        numeric(run["geometry"]["T"]), numeric(reference_frame), atol=1e-10, rtol=0
    )


def component_ag_flow_markdown(run):
    """Explain slides 12–14 only when the active inputs actually match that reference."""
    if not component_reference_matches(run):
        return []
    data = component_ag_symbolics()
    denominator_latex = raman_latex(data["denominator"])
    lines = [
        "## Component reference: slides 12, 13 and 14",
        "The active frame and Jones states match this declared reference. The generic matrix calculation has already produced the curve; the following independent derivation checks it.",
        "Transcription note: one intermediate z² line on slide 12 displays θ−α. The complete expressions on slides 12–13 and the slide-14 result use θ+α. This derivation follows that consistent completed sequence; the isolated sign is not copied into the engine.",
        "### A. General component intensities (slide 12)",
    ]
    equation = lambda label, expression: lines.append(
        "$$" + label + "=" + raman_latex(expression) + "$$"
    )
    equation(r"e_i(\theta,\beta)", jones(data["theta"], data["beta"]))
    equation(r"e_s(\theta+\alpha,\beta')", jones(data["theta"] + alpha, data["beta_prime"]))
    for label, part in zip([r"I_{Ag(x^2)}", r"I_{Ag(y^2)}", r"I_{Ag(z^2)}"], data["parts"]):
        equation(label, part)
    lines.append(r"$$I_{Ag}=I_{Ag(x^2)}+I_{Ag(y^2)}+I_{Ag(z^2)}.$$")
    lines.append("### B. Expand and collect the terms (slide 13)")
    lines.append(
        "The common denominator is derived from the rotated matrix entries: "
        + denominator_latex
        + "."
    )
    lines.append(
        r"$$I_{Ag}=\frac{1}{"
        + denominator_latex
        + r"}\left["
        + raman_latex(data["expanded_numerator"])
        + r"\right].$$"
    )
    lines.append("### C. Apply the slide 14 conditions")
    lines.append(
        r"$$\theta=\frac{\pi}{4},\quad\beta=\beta'=\frac{\pi}{2},\quad\cos2\theta=0,\quad\sin2\theta=1,\quad\cos\beta=\cos\beta'=0,\quad\cos2(\theta+\alpha)=-\sin2\alpha.$$"
    )
    lines.append("### D. Symbolic and numerical final intensity")
    lines.append(
        r"$$\boxed{I_{Ag}(\alpha)=\frac{1}{"
        + denominator_latex
        + r"}\left["
        + raman_latex(data["final_numerator"])
        + r"\right]}.$$"
    )
    values = run["families"]["Ag"]["values"]
    substitution = {
        symbol: sp.Abs(values[key]) for symbol, key in zip(data["coefficients"], [a, b, c])
    }
    equation(
        r"I_{Ag}(\alpha)\;\mathrm{(active\ coefficients)}",
        sp.N(sp.expand(data["special"].subs(substitution)), 8),
    )
    lines.append(
        "For complex inputs, a²,b²,c² in this reference mean the corresponding squared magnitudes. The user-prescribed component-intensity sum is retained."
    )
    return lines

print("Cell 11/22 — Run completed successfully.\nReady: The separate slide-reference derivation functions are ready.\nNext: Run Cell 12.", flush=True)


# %% Code cell 12: Complete mathematical derivation
"""Readable paper notes and calculation records, with equations tied to their source."""

PAPER_NOTES = "### Sources and model scope\n\nCircular selection rules: DOI 10.1039/D1CP02209A. Complex linear response: DOI 10.1039/D1CP03626B. Cubic benchmark: DOI 10.1002/jrs.70113.\n\nThe companion guides explain the assumptions and every code cell. Tensor coefficients are supplied inputs; the component reference remains an explicit separate intensity prescription."


def display_intensity(summary, variable=alpha):
    """Suppress only roundoff-sized display terms while retaining raw exported numbers."""
    cleaned = copy.deepcopy(summary)
    scale = max(
        abs(summary[key])
        for key in ["I0", "Ic", "Is"] + (["I4c", "I4s"] if "I4c" in summary else [])
    )
    threshold = 64 * np.finfo(float).eps * max(scale, np.finfo(float).tiny)
    for key in ["Ic", "Is", "I4c", "I4s"]:
        if key in cleaned and abs(cleaned[key]) <= threshold:
            cleaned[key] = 0
    return sp.N(intensity_expression(cleaned, variable), 8)


def final_intensity_context(run, name):
    """Place enough provenance beside every final equation to identify the calculation."""
    config = run["config"]
    optical = run["results"][name].get("optical", run["optical"])
    geometry = (
        "original optical source model"
        if run["geometry"] is None
        else f"hkl={config['hkl']}, [uvw]={config['uvw']}, normal={config['normal_sign']}, ψ={config['azimuth_deg']} degrees"
    )
    return (
        "**Final intensity — "
        + METHOD_LABELS[config["calculation_method"]]
        + "; "
        + name
        + ".** "
        + optical["label"]
        + ". "
        + geometry
        + "."
    )


def paper_steps_markdown(run):
    """Report the paper's actual geometry and algebra, followed by this run's results."""
    config, geometry, optical = run["config"], run["geometry"], run["optical"]
    linear_scan = config["calculation_method"] == "LINEAR"
    variable = theta_scan if linear_scan else alpha
    source = PAPER_SOURCES["linear" if linear_scan else "circular"]
    lines = [
        "# ROTATION RAMAN TENSOR CALCULATION",
        "## " + METHOD_LABELS[config["calculation_method"]],
        "**Case:** " + config["case_label"],
        "**Input note:** " + config["input_note"],
        f"**Material:** {config['material']}; **point group:** {config['point_group']}; **plane:** {config['hkl']}; **in-plane reference:** {config['uvw']}.",
        "**Source:** " + source["title"] + ", " + source["journal"] + ". " + source["url"],
        "### Coordinate frame",
    ]

    def equation(label, expression):
        """Typeset a calculated equation using the actual scan-variable name."""
        if isinstance(expression, (sp.Basic, sp.MatrixBase)):
            expression = expression.subs(alpha, variable)
        lines.append("$$" + label + "=" + raman_latex(expression) + "$$")

    for key in ["L", "g", "t", "T"]:
        if key in geometry:
            equation(key, geometry[key])
    equation(r"T^{-1}=T^T", geometry["T"].T)
    equation(r"\det T", sp.simplify(geometry["T"].det()))
    lines.extend("- " + item for item in run["assumptions"])
    if linear_scan:
        lines.extend(
            [
                "### Co-rotating linear states",
                r"$$e_i=(\cos\theta,\sin\theta)^T,\quad e_{s,\parallel}=e_i,\quad e_{s,\perp}=(-\sin\theta,\cos\theta)^T.$$",
            ]
        )
        lines.append(
            "θ is the polarization angle in the fixed measurement frame. A sample rotation at fixed laboratory optics requires the corresponding opposite frame-angle convention. The selected zero offset is "
            + str(config["paper_parameters"]["theta0_deg"])
            + " degrees."
        )
        lines.append(
            r"$$\mathcal A=K_0+K_c\cos2\theta+K_s\sin2\theta,\quad I=|\mathcal A|^2=I_0+I_c\cos2\theta+I_s\sin2\theta+I_{4c}\cos4\theta+I_{4s}\sin4\theta.$$"
        )
        lines.append(
            "Parallel and crossed curves of a branch use the same tensor coefficients. Eq. 13 is recovered on the review's principal xz plane. A general rotated surface can have a nonzero projected off-diagonal entry even when the crystal Ag tensor is diagonal."
        )
    else:
        lines.extend(
            [
                "### Circular basis and plane-wave Jones scan",
                r"$$U=(\sigma^{+}\ \sigma^{-}),\quad R_{circ}=U^\dagger R_\perp U,\quad I_{s_s,s_i}=|(R_{circ})_{s_s,s_i}|^2.$$",
            ]
        )
        equation(r"E_i", optical["Ein"])
        equation(r"e_s(\alpha)", optical["analyzer"])
        lines.append(
            "The polar curve is an ℓ=0 tensor/Jones calculation. A fixed circular analyzer gives a constant curve because no detection state changes during that scan. The linear-analyzer scan is an explicit extension for this program."
        )
    for name, result in run["results"].items():
        item = run["families"][name]
        values = item["values"]
        lines.append("### " + name)
        lines.append(
            "**Tensor policy:** " + RULE_LABELS[result["rule"]] + ". " + item["combination_reason"]
        )
        lines.append(
            "Active coefficients: `" + json.dumps(serializable(values), ensure_ascii=False) + "`."
        )
        selected = result["optical"]
        equation("E_i", selected["Ein"])
        equation("e_s", selected["analyzer"])
        for record, label in zip(result["terms"], item["calculation_labels"]):
            lines.append("**Complete tensor / phonon partner:** " + label + ".")
            if config["show_steps"]:
                equation("R_c", record["Rc"])
                equation("R_c T", tidy(record["Rc"] * geometry["T"]))
                equation(r"R_{lab}=T^T R_c T", record["Rlab"])
                equation(r"R_\perp=P R_{lab}P^T", record["Rperp"])
                equation(r"E_{i,3D}", record["Ein3"])
                equation(r"\mathcal P_{Raman,3D}\propto R_{lab}E_{i,3D}", record["Einduced3"])
            equation(r"R_{\perp,\mathrm{active}}", sp.N(record["Rperp"].subs(values), 6))
            equation(r"\mathcal A=e_s^\dagger R_\perp E_i", tidy(record["amplitude"].subs(values)))
            if linear_scan:
                for key in ["K0", "Kc", "Ks"]:
                    equation(key, sp.N(record[key].subs(values), 7))
        lines.append(final_intensity_context(run, name))
        equation(
            r"I(\theta)" if linear_scan else r"I(\alpha)",
            display_intensity(run["summaries"][name], variable),
        )
    if not linear_scan:
        diagnostics = run["circular"]
        lines.append("### All four circular tensor channels")
        for name, item in diagnostics["channels"].items():
            lines.append(
                "**"
                + name
                + ".** Rows are outgoing +/−; columns are incoming +/−, in the fixed XY basis."
            )
            for matrix in item["matrices"]:
                equation(r"R_{circ}", matrix)
            equation(r"I_{circ}\;\mathrm{(partner\ powers\ summed)}", sp.Matrix(item["powers"]))
        lines.extend(["### Separate angular-momentum check", r"$$s_s-s_i-\ell_i+m_\nu^{ph}=Np.$$"])
        lines.append(
            "User-declared charges for this independent rule example: `"
            + str(config["paper_parameters"]["m_ph"])
            + "`. These charges have not been assigned automatically to the modes above."
        )
        lines.append("**Scope:** " + diagnostics["scope"])
        lines.append(
            "**Rotation-axis check:** "
            + diagnostics["axis_check"]["note"]
            + " Compatible: "
            + str(diagnostics["axis_check"]["compatible"])
            + "."
        )
        lines += [
            "| s_i | s_s | Eq. 24 congruence | Matching m_ph | Optional Eq. 21 |",
            "|---:|---:|---|---|---|",
        ]
        for row in diagnostics["rule_checks"]:
            lines.append(
                f"| {row['s_i']} | {row['s_s']} | {row['eq24_pass']} | {row['matching_m_ph']} | {'not supplied' if row['eq21_pass'] is None else row['eq21_pass']} |"
            )
        lines.append(
            "A passing congruence is not a quantitative intensity. The condition is diagnostic only when the axis or thin-2D/electronic assumptions are unestablished. No row in this table masks the plane-wave curves."
        )
        lines.append(
            "Circular labels here refer to the stated Jones basis. If helicity is defined relative to each beam's propagation direction, use that beam's transverse frame before assigning a same/opposite-helicity name. The incident and returned wavevectors are opposite in backscattering."
        )
    lines.append(
        "Small roundoff-sized harmonics are suppressed in the displayed final equation only. Raw summary coefficients remain in the ZIP and CSV data."
    )
    return "\n\n".join(lines)


def linear_figures(run):
    """Show parallel/crossed curves together, using a common scale for each branch."""
    config = run["config"]
    groups = {}
    for name in run["results"]:
        base = run["families"][name].get("base_mode", name)
        groups.setdefault(base, []).append(name)
    figure = plt.figure(figsize=(11, 3.8 * len(groups)), layout="constrained")
    grid = figure.add_gridspec(len(groups), 2)
    for row, (base, names) in enumerate(groups.items()):
        cart = figure.add_subplot(grid[row, 0])
        polar = figure.add_subplot(grid[row, 1], projection="polar")
        maximum = max(run["summaries"][name]["Imax"] for name in names)
        scale = maximum if config["normalize"] and maximum > 0 else 1
        for index, name in enumerate(names):
            label = run["families"][name].get(
                "polarization_channel", run["optical"]["parameters"]["channels"]
            )
            color = ["#174e75", "#c45f26"][index % 2]
            curve = run["curves"][name] / scale
            cart.plot(np.rad2deg(run["angles"]), curve, label=label, color=color, linewidth=2)
            polar.plot(run["angles"], curve, label=label, color=color, linewidth=2)
        cart.set(
            xlim=(0, 360),
            xlabel="Polarization angle θ (°)",
            ylabel="I / common pair maximum" if config["normalize"] else "Model intensity (a.u.)",
            title=base + " — shared tensor coefficients",
        )
        cart.grid(alpha=0.25)
        cart.legend(fontsize=8)
        for axes in [cart, polar]:
            axes.set_ylim(0, 1 if maximum == 0 else 1.08 * maximum / scale)
        polar.set_theta_zero_location("E")
        polar.set_title(base + " — radius = intensity")
        polar.yaxis.set_major_locator(MaxNLocator(5))
    figure.suptitle(run_description(run), fontsize=10)
    return [("polar_intensity", figure)]


"""Calculated mathematical steps shared by all materials and optical protocols."""


"""Definitions used beside each calculated equation; numerical functions are unchanged."""
import re

DERIVATION_REFERENCES = {
    "PIMENTA2021": {
        "label": "Pimenta et al. (2021)",
        "title": "Polarized Raman spectroscopy in low-symmetry 2D materials: angle-resolved experiments and complex number tensor elements",
        "url": "https://doi.org/10.1039/D1CP03626B",
        "location": "Section 1.1, Eqs. (1)-(4); Section 1.2; linear-polarization discussion in Section 2",
        "scope": "Physical susceptibility derivative, mode-specific Raman tensors, relative intensity and complex coefficients. Supplied PDF pp. 3-5 checked directly.",
    },
    "PAUKATONG2026": {
        "label": "Paukatong et al. (2026)",
        "title": "Helicity-Dependent Raman Spectroscopy of Diamond and Zinc-Blende Crystal Structures",
        "url": "https://doi.org/10.1002/jrs.70113",
        "location": "Section 2.1, Eqs. (1)-(6); Section 2.2, Eqs. (9) and (11)",
        "scope": "Si T2g tensors, cubic surface axes, tensor rotation, summed orthogonal partners and complex polarization states. Supplied PDF pp. 2-4 checked directly.",
    },
    "KUMAR_NOTEBOOK": {
        "label": "Kumar-san, supplied original notebook (2026-10-15)",
        "title": "Raman intensity with the modified Raman tensor, original Version 2.0",
        "url": "https://faizal-07-script.github.io/rotation-raman-tensor-calculation/downloads/Dr_Kumar_Original.ipynb",
        "location": "Original Cells 2-11 and the separately labeled appendix",
        "scope": "Jones basis, quarter-wave plate, return-optic convention, conjugate detection and the effective 2D reference. This supplied notebook is a project source, not a journal article.",
    },
    "NIST_UNITS": {
        "label": "NIST, Guide to the SI, Section 7.10",
        "title": "Values of quantities expressed simply as numbers: the unit one",
        "url": "https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-7-rules-and-style-conventions-expressing-values",
        "location": "Section 7.10: dimension-one quantities and the radian",
        "scope": "Unit conventions; the form converts degrees to radians before evaluation.",
    },
    "IUPAC_POLARIZATION": {
        "label": "IUPAC Gold Book, polarization density",
        "title": "Polarization density",
        "url": "https://goldbook.iupac.org/terms/view/08856",
        "location": "Definition P = epsilon_0 chi E",
        "scope": "SI polarization density, electric field and dimensionless electric susceptibility.",
    },
    "PROGRAM_GEOMETRY": {
        "label": "Program coordinate derivation, Cells 3 and 12",
        "title": "Reciprocal metric, orthonormal frame and component transformation",
        "url": "",
        "location": "Displayed matrix definitions and their direct products",
        "scope": "L^-T is the dual-basis construction. The general noncubic metric and explicit substitutions are program derivations; they are not quoted equations from the cubic paper.",
    },
    "PROGRAM_ALGEBRA": {
        "label": "Program algebra, Cells 6, 11 and 12",
        "title": "Contraction, conjugate product, harmonics and stationary points",
        "url": "",
        "location": "Algebra of the displayed tensors and Jones states",
        "scope": "Matrix products, rank-one overlap factors, trigonometric expansions and extrema are derived here from the stated definitions. They are checked against direct numerical contractions.",
    },
}


def symbol_definition(key, latex, meaning, units):
    return dict(id=key, latex=latex, meaning=meaning, units=units)


SYMBOL_CATALOG = {
    row[0]: symbol_definition(*row) for row in [
        ("lattice", r"L;\ \mathbf a_0,\mathbf b_0,\mathbf c_0", "Direct-lattice matrix and its three column vectors, written in the crystal Cartesian basis. Unity values denote relative lattice lengths.", "one common length unit; or dimensionless relative lengths"),
        ("miller", r"h,k,l", "Surface Miller indices. They label a reciprocal-lattice normal; they are not Cartesian distances or wave numbers.", "dimensionless integers"),
        ("direction_indices", r"u,v,w", "Direct-lattice direction indices defining the in-plane reference. The zone condition is hu+kv+lw=0.", "dimensionless integers"),
        ("reciprocal_normal", r"\mathbf g_{hkl}", "Unnormalized surface normal obtained from the reciprocal metric L to the power -T. This definition omits the conventional reciprocal-lattice factor 2 pi, which cancels on normalization.", "inverse common lattice-length unit"),
        ("tangent", r"\mathbf t", "In-plane reference before normalization. With explicit uvw it is L(u,v,w); automatic X instead uses a projected unit reference.", "lattice-length unit for explicit uvw; dimensionless for automatic X"),
        ("frame_axes", r"\mathbf X,\mathbf Y,\mathbf Z;\ \mathbf X_0,\mathbf Y_0", "Unit measurement axes written in crystal coordinates. Subscript 0 denotes the frame before the in-plane rotation.", "dimensionless"),
        ("lab_normal", r"\hat{\mathbf Z}_{lab}", "The same measurement-normal direction expressed in measurement coordinates: (0,0,1). Use this representation with the measurement-frame projector P.", "dimensionless unit vector"),
        ("normal_sign", r"s_n", "Chosen side of the reciprocal surface normal, +1 or -1.", "dimensionless"),
        ("frame_angle", r"\psi", "In-plane rotation of the measurement axes about Z. It changes the frame rather than the optical scan state.", "rad in formulas; degree in the input form"),
        ("frame", r"T", "Real proper orthogonal matrix whose columns are X, Y, Z in crystal coordinates. It maps measurement components to crystal components; its inverse is its transpose.", "dimensionless"),
        ("in_plane_rotation", r"\Pi(\psi)", "Three-dimensional rotation about the measurement Z axis used to update the frame.", "dimensionless matrix"),
        ("coordinate_vector", r"\mathbf v_c,\mathbf v_{lab}", "Components of the same arbitrary vector in crystal and measurement coordinates.", "same units as the vector being represented"),
        ("reference_axis", r"\mathbf e_{ref};\ \mathbf e_x,\mathbf e_y,\mathbf e_z;\ \hat x", "Cartesian unit basis vectors. The ref label is the reference used by automatic X; x,y,z refer to crystal axes in the tensor decomposition.", "dimensionless"),
        ("tensor", r"R_c,R_{lab},R_\perp,R_{ref}", "Raman tensor in crystal, measurement, transverse or effective-reference coordinates. Matrix subscripts give entries; j labels the phonon partner. R_perp is 2 by 2 after the full 3 by 3 rotation.", "relative tensor-coefficient units in this program"),
        ("physical_tensor", r"R_\chi^{(m)}", "Physical Raman tensor defined by the derivative of susceptibility with respect to the declared normal coordinate of mode m. Its units depend on that coordinate's normalization.", "reciprocal unit of the normal coordinate u_m"),
        ("projector", r"P", "2 by 3 transverse selector [[1,0,0],[0,1,0]] in measurement coordinates. Its transpose embeds a Jones vector in three dimensions.", "dimensionless"),
        ("identity", r"I_3", "3 by 3 identity matrix; this I is not Raman intensity.", "dimensionless"),
        ("incident_state", r"E_i,E_{i,lab},E_{i,c}", "Normalized incident Jones state and its three-dimensional embeddings in measurement and crystal coordinates. Overall incident field strength is omitted.", "dimensionless"),
        ("detector_state", r"e,e_s,e_{an}", "Unit Jones polarization state; s is the effective detector at the sample and an is the analyzer after return optics. The amplitude uses the conjugate transpose of the detection state.", "dimensionless"),
        ("return_optics", r"B", "Jones matrix of the return optical path. The effective detector is B dagger times e_an.", "dimensionless"),
        ("qwp", r"Q;\ \mathrm{Rot}", "Quarter-wave-plate Jones matrix and real transverse rotation matrix. For the supplied Kumar convention the plate angle is -pi/4 and the return matrix is Q transpose.", "dimensionless matrices; their angle arguments are in rad"),
        ("circular_basis", r"\sigma^+,\sigma^-", "Normalized fixed-XY circular basis vectors (1,+i)/sqrt(2) and (1,-i)/sqrt(2). A superscript sign labels a state rather than a charge with SI units.", "dimensionless"),
        ("mixing_angle", r"\vartheta", "Jones mixing angle setting the magnitudes of the two transverse components. For a real linear state it is the polarization angle.", "rad in formulas; degree in direct-state inputs"),
        ("linear_angle", r"\theta;\ \theta_i,\theta_s", "Theta is the common linear-polarization scan angle for VV/VH. In the general direct-state product, theta_i and theta_s instead denote the incident and detection mixing angles.", "rad in formulas; degree in input and angle CSV columns"),
        ("analyzer_angle", r"\alpha", "Detection-state scan angle of the selected optical profile. A direct linear analyzer, the return-QWP chain and the elliptical reference use different Jones-state definitions.", "rad in formulas; degree in input and angle CSV columns"),
        ("jones_phase", r"\beta,\beta^\prime;\ \beta_i,\beta_s", "Relative phase of Y with respect to X. The reference uses beta for the incident state and beta prime for the detected state; direct controls use the i and s subscripts.", "rad in formulas; degree in the input form"),
        ("source_phase", r"\delta,\phi", "Phases in the supplied effective 2D source tensor. Delta belongs to its off-diagonal term; phi belongs to its yy term.", "rad in formulas; degree in the effective-source controls"),
        ("coefficient_phase", r"\phi_a,\phi_b", "Phase of the indicated complex tensor coefficient, relative to the chosen reference phase.", "rad in formulas; degree in coefficient controls"),
        ("coefficient_magnitude", r"\rho_a,\rho_b", "Nonnegative magnitude of the indicated complex tensor coefficient.", "same relative units as its tensor coefficient"),
        ("coefficients", r"a,b,c,d,e,f", "Independent complex tensor coefficients in the selected symmetry form. Only symbols actually used in this equation are active. For Si T2g the three partner tensors share d.", "relative tensor-coefficient units"),
        ("source_A", r"A", "Real off-diagonal reference amplitude in Kumar's effective 2D tensor; it is distinct from the detected amplitude written as calligraphic A.", "same relative coefficient units as source a"),
        ("source_a", r"a", "Real diagonal reference amplitude in Kumar's effective 2D tensor. It is distinct from a generally complex crystal coefficient named a.", "relative source tensor-coefficient units"),
        ("rank_one_coefficient", r"q", "Coefficient of the selected Ag rank-one Cartesian contribution: a for xx, b for yy or c for zz. It is not a phonon normal coordinate.", "relative tensor-coefficient units"),
        ("rotated_axis", r"\mathbf p;\ \mathbf v,v_x,v_y", "Crystal unit axis expressed in measurement coordinates, then restricted to XY. The projected vector need not have unit length.", "dimensionless"),
        ("overlap", r"G,G_i,G_s;\ \eta_i,\eta_s", "Eta denotes an incident or detector overlap amplitude. G is its nonnegative squared magnitude; active means evaluated with the actual selected optical chain.", "dimensionless"),
        ("scattered_response", r"E_{sc},E_{out};\ \mathcal P_c,\mathcal P_{lab}", "Reduced scattered/returned field and induced-response amplitudes calculated from a relative tensor and unit Jones state. These are not calibrated SI electric fields or polarization densities.", "relative tensor-coefficient units"),
        ("amplitude", r"\mathcal A,\mathcal A_j", "Detected complex Raman scattering amplitude. A j subscript identifies one orthogonal phonon partner; a Cartesian label identifies one tensor contribution.", "relative tensor-coefficient units"),
        ("amplitude_harmonics", r"C,D;\ K_0,K_c,K_s", "Complex coefficients of the first-harmonic or second-harmonic amplitude expansion. Subscripts 0,c,s mean constant, cosine and sine; a further j denotes a partner.", "same units as the detected amplitude"),
        ("intensity", r"I,I_j;\ I_0,I_c,I_s,I_{4c},I_{4s};\ I_{min},I_{max}", "Relative intensity, its real harmonic coefficients and extrema. The final j sum adds intensities of unresolved orthogonal phonon partners. Coherent tensor terms within one partner are added before squaring.", "squared relative tensor-coefficient units, plotted as a.u."),
        ("maximum_angle", r"\alpha_{max},\theta_{max}", "An angle at a continuous intensity maximum, obtained from the harmonic expression. It need not fall on the sampled grid; a constant curve has no unique extremum angle.", "degree when explicitly labeled degree; otherwise rad"),
        ("delta_extrema", r"\Delta", "Nonnegative modulation magnitude sqrt(I_c squared + I_s squared) for a first-harmonic scan. This uppercase Delta is distinct from the source phase delta.", "same relative units as intensity"),
        ("extrema_polynomial", r"u_1,u_2;\ z", "Complex intensity-harmonic coefficients used only to find second-harmonic stationary points, and the unit-circle variable z=exp(2 i theta). These u symbols are not phonon coordinates.", "u_1,u_2: intensity units; z: dimensionless"),
        ("susceptibility", r"\chi_{ij},\chi_{ij}^{(0)}", "Electric susceptibility component and its equilibrium value. Cartesian indices identify the field and induced-polarization components.", "dimensionless in SI"),
        ("normal_coordinate", r"u_m", "Generalized phonon normal coordinate for branch m, equivalent to the q^mu notation in Pimenta Eq. (2). The program does not prescribe its displacement or mass normalization.", "chosen normal-coordinate unit; e.g. m for a displacement, or kg^(1/2) m if mass weighted"),
        ("vacuum_permittivity", r"\epsilon_0", "Vacuum electric permittivity in the physical susceptibility relation.", "F m^-1 in SI"),
        ("physical_electric_field", r"\mathbf E_{i,c}^{\mathrm{phys}}", "Physical incident electric-field amplitude expressed in crystal coordinates. It includes the incident field magnitude omitted from the unit Jones vector.", "V m^-1 in SI"),
        ("transverse_field", r"\mathbf E", "Optical electric field in the transversality condition k dot E = 0. The same orthogonality condition holds for its normalized polarization direction.", "V m^-1 for the physical field; a unit polarization direction is dimensionless"),
        ("physical_polarization", r"\mathbf P_R^{\mathrm{phys},(m)}", "Physical Raman-induced electric polarization density of phonon m. It includes epsilon_0, the physical field and the normal-coordinate displacement.", "C m^-2 in SI"),
        ("physical_intensity", r"I_m^{\mathrm{physical}};\ \kappa_m", "Physical measured intensity and its proportionality factor relative to the squared reduced amplitude. Kappa includes omitted field, phonon and collection factors and is not calculated here.", "chosen measured-intensity unit; kappa: that unit divided by squared relative coefficient units"),
        ("wavevector", r"\mathbf k_i,\mathbf k_s;\ k_i,k_s", "Incident and scattered propagation vectors and their nonnegative magnitudes, written in measurement coordinates. Only their directions are used in this plane-wave calculation.", "m^-1 for physical wavevectors; not numerically predicted here"),
        ("helicity", r"S_3;\ h_i,h_s", "Normalized circular Stokes component and propagation-relative helicity expectation. With incident propagation along -Z and detection along +Z, h_i=-S_3 and h_s=+S_3.", "dimensionless; pure circular states have values +1 or -1"),
        ("representation_error", r"\epsilon_{direct},\epsilon_{circular}", "Maximum absolute intensity residual between equivalent matrix/basis representations, evaluated using the same tensor and actual optical states. These epsilon symbols are not epsilon_0.", "same relative units as unnormalized intensity"),
        ("cartesian_indices", r"i,j,k,l;\ m,n", "In matrix entries and contraction sums, indices run over Cartesian components. In an amplitude/partner sum, j labels a phonon partner and m,n label coherent terms. These index roles are local, not extra fitted parameters.", "dimensionless labels or integer indices"),
        ("imaginary_unit", r"i", "Imaginary unit, i squared = -1. It is distinct from the incident-state subscript i and Cartesian summation indices.", "dimensionless"),
        ("pi", r"\pi", "Circle constant used in angle conversion and special-angle states.", "dimensionless; angle multiples are in rad"),
        ("exponential", r"\exp", "Complex exponential. The e in an exponential is Euler's number, distinct from a tensor coefficient named e. Its exponent is dimensionless.", "dimensionless"),
        ("transpose", r"{}^T;\ {}^{-T};\ {}^{-1}", "Matrix transpose, inverse transpose and inverse. A superscript T is an operation; a standalone T is the frame matrix.", "operation; dimensions follow the operand"),
        ("conjugation", r"{}^*,\overline{\phantom a};\ {}^\dagger", "Complex conjugation and conjugate transpose. The detection state must be conjugated before contraction.", "operation; conjugation preserves units"),
        ("norm", r"|\cdot|;\ \|\cdot\|", "Complex modulus or Euclidean vector norm. Squaring a modulus squares the units of its argument.", "same units as the argument before squaring"),
        ("products", r"\cdot;\ \times;\ \sum", "Dot product, vector cross product and explicit sum. Their domains are given by the adjacent vector definitions or index limits.", "products multiply units; sums require matching units"),
        ("real_imag", r"\operatorname{Re},\operatorname{Im};\ \arg", "Real part, imaginary part and complex phase. The argument of a nonzero coefficient is its relative phase.", "Re/Im: operand units; arg: rad"),
        ("derivative", r"d/d\theta;\ d/d\alpha;\ \partial", "Derivative with respect to the indicated angle or normal coordinate. A derivative divides the numerator's units by the differentiation variable's units.", "intensity per rad for dI/dangle; reciprocal coordinate unit for dchi/du"),
        ("determinant", r"\det", "Determinant. A proper frame has det(T)=+1 and T transpose times T equals the identity.", "dimensionless for a rotation matrix"),
        ("big_o", r"O(u^2)", "Terms of second and higher order in the normal-coordinate expansion, omitted in the first-order Raman model.", "same susceptibility units as the retained Taylor series"),
        ("equilibrium_evaluation", r"\left.\cdot\right|_0", "Evaluate the derivative at the equilibrium normal coordinate u_m=0. This vertical bar denotes evaluation, not a modulus.", "operation; preserves the derivative's units"),
        ("inverse_trig", r"\operatorname{atan2};\ \pmod\pi", "Quadrant-aware inverse tangent and angular equivalence modulo pi, used for a first-harmonic extremum.", "rad; modulo-pi angles repeat after 180 degrees"),
    ]
}


def _without_latex_labels(value):
    """Remove formatting words/subscripts, keeping mathematical base symbols."""
    text = value.replace(r"\\", " ")
    text = re.sub(r"\\(?:begin|end)\{[^{}]*\}", " ", text)
    for _ in range(4):
        text = re.sub(r"\\(?:mathrm|text|operatorname)\{[^{}]*\}", " ", text)
    text = re.sub(r"_\{[^{}]*\}", " ", text)
    text = re.sub(r"_(?:\\[A-Za-z]+|[A-Za-z0-9])", " ", text)
    text = re.sub(r"\^\{?(?:-T|T|-1|\\dagger|\\ast|\*)\}?", " ", text)
    text = re.sub(r"\^\{\([^{}]*\)\}", " ", text)
    text = re.sub(r"\b(?:physical|phys|plot|symbolic|numerical|expanded|active|lab|ref)\b", " ", text)
    text = re.sub(r"\\[A-Za-z]+", " ", text)
    return text


def equation_symbol_definitions(value, expressions=(), scope="algebra", context=None):
    """Select local definitions, separating overloaded symbols and physical units."""
    value = value.replace(r"\mathrm{phys}", "phys").replace(r"\mathrm{physical}", "physical").replace(r"\mathrm{plot}", "plot")
    keys = []
    def add(key):
        if key not in keys:
            keys.append(key)
    has = lambda pattern: bool(re.search(pattern, value))
    reduced = _without_latex_labels(value)
    letters = set(re.findall(r"[A-Za-z]", reduced))
    free = set()
    for expr in expressions:
        free.update(str(s) for s in sp.sympify(expr).free_symbols)
    if "L" in letters: add("lattice")
    if has(r"\(h,k,l\)|g_\{hkl\}|hu\+kv\+lw"): add("miller")
    if has(r"\(u,v,w\)|hu\+kv\+lw"): add("direction_indices")
    if has(r"\\mathbf\s*\{?g|g_\{hkl\}"): add("reciprocal_normal")
    if has(r"\\mathbf\s*\{?t"): add("tangent")
    crystal_axes = value.replace(r"\hat{\mathbf Z}_{lab}", "")
    if re.search(r"\\mathbf\s*\{?[XYZ]", crystal_axes): add("frame_axes")
    if r"\hat{\mathbf Z}_{lab}" in value: add("lab_normal")
    if "s_n" in value: add("normal_sign")
    if r"\psi" in value: add("frame_angle")
    if "T" in letters: add("frame")
    if r"\Pi" in value: add("in_plane_rotation")
    if has(r"\\mathbf v_(?:c|\{lab\})"): add("coordinate_vector")
    if has(r"\\mathbf e_|\\hat\s*x"): add("reference_axis")
    if "R" in letters:
        add("physical_tensor" if r"R_\chi" in value or r"R_{\chi" in value else "tensor")
    if has(r"(?<![A-Za-z])P(?![A-Za-z])") and r"\mathbf P_R" not in value and r"\mathcal P" not in value:
        add("projector")
    elif any(token in value for token in ("=P", "[P", r"\,P", r"\quad P", "BPR", "=PR")): add("projector")
    if "I_3" in value: add("identity")
    if re.search(r"E_(?:i|\{i)", value.replace(r"\mathbf E_{i,c}^{phys}", "")): add("incident_state")
    if has(r"e(?:_(?:[isXYxy]|\{an\})|\(\\vartheta|\^\\dagger)") or "S_3(e)" in value: add("detector_state")
    if "B" in letters: add("return_optics")
    if "Q" in letters or r"\mathrm{Rot}" in value: add("qwp")
    if r"\sigma" in value: add("circular_basis")
    if r"\vartheta" in value: add("mixing_angle")
    if r"\theta" in value: add("linear_angle")
    if r"\alpha" in value: add("analyzer_angle")
    if r"\beta" in value: add("jones_phase")
    if r"\delta" in value or (r"\phi" in value and not has(r"\\phi_")): add("source_phase")
    if has(r"\\phi_"): add("coefficient_phase")
    if r"\rho" in value: add("coefficient_magnitude")
    coefficient_names = {"a", "b", "c", "d", "e", "f"}
    stripped = re.sub(r"\\mathbf\s*\{?[a-z]\}?", " ", value)
    stripped = re.sub(r"e\^\{?[+-]?i[^{}]*\}?", " ", stripped)
    stripped = re.sub(r"e_(?:[isXYxy]|\{[^{}]*\})|e\(|e\^\\dagger", " ", stripped)
    stripped = stripped.replace("dI", "I")
    stripped = stripped.replace(r"d\theta", r"\theta").replace(r"d\alpha", r"\alpha")
    literal_coefficients = set(re.findall(r"[A-Za-z]", _without_latex_labels(stripped))) & coefficient_names
    # In geometry, letters in directions and labels are not tensor coefficients.
    infer_literals = scope not in {"geometry", "optics"} or r"\rho" in value
    active_coefficients = (free & coefficient_names) | (literal_coefficients if infer_literals else set())
    if (context or {}).get("tensor_model") == "QWP_SOURCE_2D" and "a" in active_coefficients:
        active_coefficients.remove("a")
        add("source_a")
    if active_coefficients: add("coefficients")
    source_A_text = re.sub(r"\\mathcal\s*\{?A\}?", "", value)
    if "A" in free or "A" in _without_latex_labels(source_A_text): add("source_A")
    if has(r"(?<![A-Za-z])q(?![A-Za-z])"): add("rank_one_coefficient")
    if has(r"\\mathbf\s*[pv](?!_(?:c|\{lab\}))|v_[xy]"): add("rotated_axis")
    if "G" in letters or r"\eta" in value: add("overlap")
    if "E_{sc}" in value or "E_{out}" in value or r"\mathcal P" in value: add("scattered_response")
    if has(r"\\mathcal\s*\{?A"): add("amplitude")
    if letters & {"C", "D", "K"}: add("amplitude_harmonics")
    intensity_text = value.replace("I_3", "").replace(r"\mathrm{I}", "")
    if re.search(r"(?<![A-Za-z])I(?![A-Za-z])", intensity_text): add("intensity")
    if has(r"\\(?:alpha|theta)_\{max\}"): add("maximum_angle")
    if r"\Delta" in value: add("delta_extrema")
    if "u_1" in value or "u_2" in value or ("z" in letters and scope == "final"): add("extrema_polynomial")
    if has(r"\\chi_\{ij\}"): add("susceptibility")
    if "u_m" in value or "O(u^2)" in value: add("normal_coordinate")
    if r"\epsilon_0" in value: add("vacuum_permittivity")
    if r"\mathbf E_{i,c}^{phys}" in value: add("physical_electric_field")
    if r"\mathbf k\cdot\mathbf E" in value: add("transverse_field")
    if r"\mathbf P_R^{phys" in value: add("physical_polarization")
    if "physical" in value or r"\kappa" in value: add("physical_intensity")
    if has(r"\\mathbf\s*\{?k|k_[is]"): add("wavevector")
    if "S_3" in value or "h_i" in value or "h_s" in value: add("helicity")
    if r"\epsilon_{direct}" in value or r"\epsilon_{circular}" in value: add("representation_error")
    if r"\sum" in value or has(r"_\{[ijkl]{2}\}"): add("cartesian_indices")
    if "i" in letters or r"\mathrm{i}" in value: add("imaginary_unit")
    if r"\pi" in value: add("pi")
    if has(r"(?<![A-Za-z])e\^\{?(?:[-+]?i)|\\exp"): add("exponential")
    if has(r"\^\{?(?:T|-T|-1)\}?"): add("transpose")
    if r"\dagger" in value or r"\overline" in value or "^*" in value or "^{*}" in value: add("conjugation")
    if "|" in value.replace(r"\right|_0", ""): add("norm")
    if r"\right|_0" in value: add("equilibrium_evaluation")
    if r"\cdot" in value or r"\times" in value or r"\sum" in value: add("products")
    if r"\operatorname{Re}" in value or r"\operatorname{Im}" in value or r"\arg" in value: add("real_imag")
    if "dI" in value or r"\partial" in value: add("derivative")
    if r"\det" in value: add("determinant")
    if "O(u^2)" in value: add("big_o")
    if r"\operatorname{atan2}" in value or r"\pmod" in value: add("inverse_trig")
    rows = [copy.deepcopy(SYMBOL_CATALOG[key]) for key in keys]
    for row in rows:
        if row["id"] == "coefficients":
            row["latex"] = ",".join(sorted(active_coefficients))
        if row["id"] in {"linear_angle", "analyzer_angle"} and r"\mathrm{degree}" in value:
            row["units"] = "degree (explicitly labeled numerical angle)"
    return rows


def annotate_equation(value, expressions=(), scope="algebra", context=None):
    """Keep references separate from the intermediate algebra implemented here."""
    references = ["PROGRAM_ALGEBRA"]
    explanation = "Program derivation from the displayed definitions; matrix multiplication, complex conjugation or trigonometric algebra."
    if scope == "geometry":
        references = ["PAUKATONG2026", "PROGRAM_GEOMETRY"]
        explanation = "Frame/tensor convention: Paukatong Eqs. (4)-(6). The reciprocal metric, general lattice and explicit matrix substitutions are derived in this program."
    elif scope == "optics":
        references = ["PAUKATONG2026", "KUMAR_NOTEBOOK", "PROGRAM_ALGEBRA"]
        explanation = "Complex polarization convention: Paukatong Eq. (11). QWP and effective detector: supplied Kumar notebook. The actual selected Jones matrices are evaluated here."
    elif scope == "tensor":
        references = ["PIMENTA2021", "PAUKATONG2026", "PROGRAM_ALGEBRA"]
        explanation = "Physical tensor definition: Pimenta Eqs. (1)-(4). Si partner tensors and intensity sum: Paukatong Eqs. (1)-(3) and (9). Relative numerical coefficients are declared inputs."
    elif scope in {"record", "final"}:
        references = ["PIMENTA2021", "PAUKATONG2026", "KUMAR_NOTEBOOK", "PROGRAM_ALGEBRA"]
        explanation = "Tensor/intensity principle: Pimenta Eqs. (2)-(4); conjugate detector and Si partner sum: Paukatong Eqs. (9),(11). Intermediate products, harmonics and extrema are program algebra; QWP source convention follows Kumar where selected."
    symbols = equation_symbol_definitions(value, expressions, scope, context)
    if any(row["id"] in {"physical_polarization", "vacuum_permittivity", "physical_electric_field", "susceptibility"} for row in symbols):
        references.append("IUPAC_POLARIZATION")
    if any("angle" in row["id"] or "phase" in row["id"] for row in symbols):
        references.append("NIST_UNITS")
    return dict(kind="equation", value=value, symbols=symbols,
                reference_ids=list(dict.fromkeys(references)), derivation_note=explanation)


def equation_notes_markdown(item):
    rows = ["**Symbols and units**", "| Symbol | Meaning | Unit / convention |", "| --- | --- | --- |"]
    for symbol in item.get("symbols", []):
        rows.append("| $" + symbol["latex"].replace("|", r"\vert") + "$ | " + symbol["meaning"] + " | " + symbol["units"] + " |")
    rows += ["", "**Derivation / source:** " + item.get("derivation_note", "")]
    for key in item.get("reference_ids", []):
        ref = DERIVATION_REFERENCES[key]
        label = "[" + ref["label"] + "](" + ref["url"] + ")" if ref["url"] else ref["label"]
        rows.append("- " + label + "; " + ref["location"] + ".")
    return "\n".join(rows)


# Short definitions are used once at the end of the full-mathematics view.
# The explained view retains each equation's complete definitions and sources.
SHORT_SYMBOL_MEANINGS = {'lattice': 'Direct-lattice matrix and its crystal basis vectors.', 'miller': 'Surface Miller indices.', 'direction_indices': 'In-plane direct-lattice direction; hu + kv + lw = 0.', 'reciprocal_normal': 'Surface normal before normalization; the 2π factor is omitted.', 'tangent': 'In-plane reference before normalization.', 'frame_axes': 'Measurement unit axes in crystal coordinates; 0 means before rotation.', 'lab_normal': 'Measurement normal in measurement coordinates, (0,0,1).', 'normal_sign': 'Chosen normal direction, +1 or −1.', 'frame_angle': 'In-plane rotation of the measurement frame.', 'frame': 'Frame matrix: measurement components → crystal components.', 'in_plane_rotation': 'Rotation about the measurement normal.', 'coordinate_vector': 'The same vector in crystal and measurement coordinates.', 'reference_axis': 'Cartesian unit vectors; ref is the automatic in-plane reference.', 'tensor': 'Raman tensor in crystal, measurement, transverse or reference coordinates.', 'physical_tensor': 'Susceptibility derivative with respect to the phonon normal coordinate.', 'projector': '2 × 3 selector of measurement X and Y components.', 'identity': '3 × 3 identity matrix.', 'incident_state': 'Unit incident Jones state and its 3D embeddings.', 'detector_state': 'Unit Jones state; s is detection at the sample, an is the analyzer.', 'return_optics': 'Return-path Jones matrix.', 'qwp': 'Quarter-wave-plate matrix and transverse rotation matrix.', 'circular_basis': 'Fixed-XY circular Jones states, (1,±i)/√2.', 'mixing_angle': 'Jones mixing angle between X and Y components.', 'linear_angle': 'VV/VH scan angle; i and s label incident and detection mixing angles.', 'analyzer_angle': 'Detection-state scan angle for the selected optical profile.', 'jones_phase': 'Relative Y-to-X phase; i and s label incidence and detection.', 'source_phase': 'Off-diagonal and yy phases in the effective 2D source tensor.', 'coefficient_phase': 'Phase of a complex tensor coefficient.', 'coefficient_magnitude': 'Magnitude of a complex tensor coefficient.', 'coefficients': 'Active complex tensor coefficients; Si T2g partners share d.', 'source_A': 'Real off-diagonal source coefficient; distinct from calligraphic amplitude.', 'source_a': 'Real diagonal source coefficient in the effective 2D model.', 'rank_one_coefficient': 'Selected Ag Cartesian coefficient: a, b or c.', 'rotated_axis': 'Rotated crystal axis and its XY projection; projection need not be unit length.', 'overlap': 'η is a polarization overlap; G is its squared magnitude.', 'scattered_response': 'Reduced field or induced response from a relative tensor and unit Jones state.', 'amplitude': 'Detected complex amplitude; j labels a phonon partner.', 'amplitude_harmonics': 'Constant, cosine and sine coefficients in the amplitude expansion.', 'intensity': 'Relative intensity, harmonic coefficients and extrema; partner powers are summed.', 'maximum_angle': 'Angle at a continuous maximum; undefined for a constant curve.', 'delta_extrema': 'First-harmonic modulation magnitude; distinct from lowercase source phase δ.', 'extrema_polynomial': 'Stationary-point coefficients and z = exp(2iθ); these u values are not phonon coordinates.', 'susceptibility': 'Electric susceptibility; superscript 0 is its equilibrium value.', 'normal_coordinate': 'Phonon normal coordinate with a chosen displacement or mass normalization.', 'vacuum_permittivity': 'Vacuum electric permittivity.', 'physical_electric_field': 'Physical incident electric field in crystal coordinates.', 'transverse_field': 'Electric field in the transverse-wave condition.', 'physical_polarization': 'Physical Raman-induced polarization density of phonon m.', 'physical_intensity': 'Measured intensity and its uncalculated field/phonon/collection scale factor.', 'wavevector': 'Incident/scattered propagation vectors and magnitudes in measurement coordinates.', 'helicity': 'Circular Stokes component and propagation-relative helicity; hi = −S3, hs = +S3.', 'representation_error': 'Intensity residual between equivalent matrix or basis calculations.', 'cartesian_indices': 'Local Cartesian indices, phonon-partner labels or coherent-term labels.', 'imaginary_unit': 'Imaginary unit; distinct from incident and Cartesian index labels.', 'pi': 'Circle constant.', 'exponential': 'Exponential function; its e is distinct from a tensor coefficient e.', 'transpose': 'Transpose, inverse transpose and inverse; standalone T is the frame matrix.', 'conjugation': 'Complex conjugation and conjugate transpose.', 'norm': 'Complex modulus or Euclidean vector norm.', 'products': 'Dot product, cross product and sum.', 'real_imag': 'Real part, imaginary part and complex phase.', 'derivative': 'Derivative with respect to the indicated angle or normal coordinate.', 'determinant': 'Matrix determinant; a proper frame has det(T) = +1.', 'big_o': 'Omitted second- and higher-order normal-coordinate terms.', 'equilibrium_evaluation': 'Evaluate at the equilibrium coordinate; this bar is not a modulus.', 'inverse_trig': 'Quadrant-aware inverse tangent and angular equivalence modulo π.'}


def calculation_symbol_legend(entries):
    """Collect the symbols used in this calculation, preserving local meanings."""
    rows, seen = [], set()
    for entry in entries:
        for symbol in entry.get("symbols", []):
            key = tuple(symbol[field] for field in ("id", "latex", "meaning", "units"))
            if key not in seen:
                seen.add(key)
                row = copy.deepcopy(symbol)
                row["meaning"] = SHORT_SYMBOL_MEANINGS[row["id"]]
                rows.append(row)
    return rows


def calculation_reference_ids(entries):
    """List the sources used by this calculation once, in order of appearance."""
    return list(dict.fromkeys(key for entry in entries for key in entry.get("reference_ids", [])))


def calculation_legend_markdown(entries):
    """Put one short symbol-and-unit table after the complete mathematics."""
    lines = ["## Symbols and units", "| Symbol | Meaning | Unit / convention |", "| --- | --- | --- |"]
    for symbol in calculation_symbol_legend(entries):
        lines.append("| $" + symbol["latex"].replace("|", r"\vert") + "$ | " + symbol["meaning"] + " | " + symbol["units"] + " |")
    lines += ["", "## References"]
    for key in calculation_reference_ids(entries):
        ref = DERIVATION_REFERENCES[key]
        lines.append("- " + ("[" + ref["label"] + "](" + ref["url"] + ")" if ref["url"] else ref["label"]) + "; " + ref["location"] + ".")
    return "\n".join(lines)


def symbols_and_references_markdown():
    lines = ["# Version 4 - symbols, units and derivation references", "",
        "Choose Full mathematics for all equations with one short symbol list at the end. Explained derivation keeps the detailed definitions and sources below each equation. This file collects the complete definitions for reference.", "",
        "Angles are evaluated in radians; controls and angle CSV columns use degrees. Numerical Raman tensors use a declared relative coefficient scale, and plotted intensities use its square (a.u.). The physical susceptibility derivative has units set by the chosen phonon normal coordinate; no absolute detector calibration is inferred.", ""]
    for row in SYMBOL_CATALOG.values():
        lines += ["## $" + row["latex"] + "$", row["meaning"], "**Unit / convention:** " + row["units"], ""]
    lines += ["## Reference map", ""]
    for key, ref in DERIVATION_REFERENCES.items():
        lines += ["### " + ref["label"], ref["title"], ref["location"], ref["scope"]]
        if ref["url"]: lines.append(ref["url"])
        lines.append("")
    return "\n\n".join(lines)


class CalculationTrace:
    """Keep one mathematical source for notebook rendering and LaTeX export."""

    def __init__(self, variable=alpha, context=None):
        self.variable = variable
        self.entries = []
        self.scope = "algebra"
        self.context = context or {}

    def section(self, title, scope=None):
        if scope is not None:
            self.scope = scope
        self.entries.append(dict(kind="section", value=title))

    def note(self, value):
        self.entries.append(dict(kind="note", value=value))

    def tex(self, value, expressions=()):
        self.entries.append(annotate_equation(value, expressions, self.scope, self.context))

    def latex(self, expression):
        value = sp.sympify(expression)
        return raman_latex(value.subs(alpha, self.variable))

    def eq(self, lhs, expression):
        self.tex(lhs + "=" + self.latex(expression), (expression,))

    def chain(self, lhs, factors, answer):
        self.tex(lhs + "=" + r"\,".join(self.latex(x) for x in factors) + "=" + self.latex(answer), (*factors, answer))

    def markdown(self, explained=True):
        result = []
        for item in self.entries:
            result.append(
                "## " + item["value"]
                if item["kind"] == "section"
                else "$$" + item["value"] + "$$" if item["kind"] == "equation" else item["value"]
            )
            if explained and item["kind"] == "equation":
                result.append(equation_notes_markdown(item))
        if not explained:
            result.append(calculation_legend_markdown(self.entries))
        return "\n\n".join(result)


def latex_text(value):
    """Escape text while retaining Greek notation in a portable LaTeX document."""
    replacements = {
        "\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
        "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}",
        "^": r"\textasciicircum{}", "~": r"\textasciitilde{}",
        "—": "---", "–": "--", "−": "-", "°": r"$^\circ$",
        "→": r"$\to$", "×": r"$\times$", "±": r"$\pm$",
        "≤": r"$\le$", "≥": r"$\ge$", "≠": r"$\ne$", "′": "'",
    }
    greek = {"α":"alpha", "β":"beta", "γ":"gamma", "δ":"delta", "θ":"theta",
             "ϑ":"vartheta", "φ":"phi", "ψ":"psi", "σ":"sigma", "ρ":"rho",
             "ε":"epsilon", "η":"eta", "χ":"chi", "κ":"kappa", "μ":"mu",
             "π":"pi", "Γ":"Gamma", "Δ":"Delta", "Σ":"Sigma", "Π":"Pi"}
    replacements.update({ch:"$\\"+name+"$" for ch,name in greek.items()})
    return "".join(replacements.get(ch,ch) for ch in str(value))


def trace_geometry(trace, run):
    """Expand the direct/reciprocal metric and every frame-construction step."""
    geometry, cfg = run["geometry"], run["config"]
    trace.section("1. Lattice, surface and measurement axes", scope="geometry")
    if geometry is None:
        trace.note("The original effective 2D optical reference has no crystal-orientation input.")
        return
    trace.tex(
        r"L=[\mathbf a_0\ \mathbf b_0\ \mathbf c_0],\quad \mathbf g_{hkl}=L^{-T}(h,k,l)^T,\quad \mathbf t=L(u,v,w)^T"
    )
    L, T = geometry["L"], geometry["T"]
    trace.eq("L", L)
    trace.eq(r"L^{-T}", tidy(L.inv().T))
    if cfg.get("orientation", "hkl") == "hkl":
        h = sp.Matrix(cfg["hkl"])
        trace.eq("(h,k,l)^T", h)
        trace.chain(r"\mathbf g_{hkl}", [L.inv().T, h], geometry["g"])
        gn = sp.sqrt((geometry["g"].T * geometry["g"])[0])
        trace.eq(r"\|\mathbf g_{hkl}\|", sp.simplify(gn))
        trace.eq(r"\mathbf Z=s_n\mathbf g_{hkl}/\|\mathbf g_{hkl}\|", T[:, 2])
        trace.eq("s_n", cfg["normal_sign"])
        if cfg["uvw"] is not None:
            u = sp.Matrix(cfg["uvw"])
            trace.eq("(u,v,w)^T", u)
            trace.eq("hu+kv+lw", (h.T * u)[0])
            trace.chain(r"\mathbf t", [L, u], geometry["t"])
        else:
            trace.eq(
                r"\mathbf t=\mathbf e_{ref}-\mathbf Z(\mathbf Z^T\mathbf e_{ref})", geometry["t"]
            )
        trace.eq(r"\|\mathbf t\|", sp.simplify(sp.sqrt((geometry["t"].T * geometry["t"])[0])))
        trace.eq(r"\mathbf X_0=\mathbf t/\|\mathbf t\|", geometry["X0"])
        trace.eq(r"\mathbf Y_0=\mathbf Z\times\mathbf X_0", geometry["Y0"])
        trace.eq(r"\psi", deg(cfg["azimuth_deg"]))
        trace.eq(r"\mathbf X=\cos\psi\,\mathbf X_0+\sin\psi\,\mathbf Y_0", T[:, 0])
        trace.eq(r"\mathbf Y=-\sin\psi\,\mathbf X_0+\cos\psi\,\mathbf Y_0", T[:, 1])
    trace.eq(r"T=[\mathbf X\ \mathbf Y\ \mathbf Z]", T)
    trace.eq(r"T^{-1}=T^T", T.T)
    trace.eq(r"T^TT", sp.simplify(T.T * T))
    trace.eq(r"\det T", sp.simplify(T.det()))
    trace.tex(r"\mathbf v_c=T\mathbf v_{lab},\quad R_{lab}=T^TR_cT,\quad R_{lab}\ne |T^TR_cT|^2")
    trace.tex(
        r"\Pi(\psi)=\begin{pmatrix}\cos\psi&-\sin\psi&0\\\sin\psi&\cos\psi&0\\0&0&1\end{pmatrix},\quad T(\psi)=T(0)\Pi(\psi)"
    )
    trace.tex(r"R_{lab}(\psi)=\Pi(\psi)^T\,T(0)^TR_cT(0)\,\Pi(\psi)")
    trace.note(
        "The frame angle ψ changes the crystal-to-measurement transformation. The optical scan angle changes the declared Jones states; these are separate inputs."
    )


def trace_optics(trace, run):
    """Show general states, active optical matrices and effective sample detection."""
    optical = run["optical"]
    trace.section("2. Jones states and the active measurement protocol", scope="optics")
    trace.note(GENERAL_PROFILES.get(run["config"]["optics"], optical["label"]))
    trace.tex(
        r"e(\vartheta,\beta)=\begin{pmatrix}\cos\vartheta\\e^{i\beta}\sin\vartheta\end{pmatrix},\quad e^\dagger=(\cos\vartheta,\ e^{-i\beta}\sin\vartheta)"
    )
    trace.tex(r"\beta_i\equiv\beta,\quad\beta_s\equiv\beta^{\prime}")
    trace.tex(
        r"\sigma^{\pm}=\frac{1}{\sqrt2}\begin{pmatrix}1\\\pm i\end{pmatrix},\quad E_i^\dagger E_i=e_s^\dagger e_s=1"
    )
    trace.tex(
        r"\hat{\mathbf Z}_{lab}=(0,0,1)^T,\quad\mathbf k_i=-k_i\hat{\mathbf Z}_{lab},\quad\mathbf k_s=+k_s\hat{\mathbf Z}_{lab},\quad\mathbf k\cdot\mathbf E=0,\quad P^TP=I_3-\hat{\mathbf Z}_{lab}\hat{\mathbf Z}_{lab}^T"
    )
    trace.tex(r"S_3(e)=2\operatorname{Im}(e_X^*e_Y),\quad h_i=-S_3(E_i),\quad h_s=+S_3(e_s)")
    trace.note("Frame columns X, Y, Z above use crystal components. Wavevectors and the projector here use measurement components, with Z_lab=(0,0,1). Jones vectors are normalized states; the reduced scattered responses carry coefficient units.")
    trace.note(
        "Fixed-laboratory circular basis labels are used. Propagation-relative helicity changes sign between opposite beam directions. The model uses ideal transverse plane-wave states without a dielectric-propagation or finite-aperture correction."
    )
    if optical["kind"] == "QWP":
        trace.eq(r"Q=\mathrm{Rot}(-\pi/4)\,\mathrm{diag}(1,i)\,\mathrm{Rot}(-\pi/4)^T", QWP_QWP)
        trace.chain(r"E_i", [QWP_QWP, x_hat], optical["Ein"])
        trace.eq(r"B=Q^T", optical["B"])
    else:
        trace.eq("B", optical["B"])
    trace.eq("E_i", optical["Ein"])
    trace.eq(r"e_{an}", optical["analyzer"])
    trace.chain(
        r"e_s=B^\dagger e_{an}",
        [optical["B"].H, optical["analyzer"]],
        optical["effective_analyzer"],
    )
    trace.eq(r"e_s^\dagger", optical["effective_analyzer"].H)
    trace.eq("P", P)
    trace.tex(
        r"E_{i,lab}=P^TE_i,\quad \mathcal A_j=e_{an}^\dagger BPR_{lab,j}P^TE_i=e_s^\dagger R_{\perp,j}E_i"
    )
    trace.tex(r"R_{\perp,j}=PR_{lab,j}P^T,\quad I_j=\mathcal A_j\mathcal A_j^*")
    trace.tex(
        r"\left|\sum_m\mathcal A_m\right|^2=\sum_m|\mathcal A_m|^2+2\operatorname{Re}\sum_{m<n}\mathcal A_m\mathcal A_n^*"
    )
    trace.tex(
        r"a=\rho_a e^{i\phi_a},\quad b=\rho_b e^{i\phi_b},\quad \operatorname{Re}(ab^*)=\rho_a\rho_b\cos(\phi_a-\phi_b)"
    )


def trace_rank_one(trace, record, component, optical):
    """Derive the slide-style product for each rotated diagonal Ag contribution."""
    if component not in ["xx", "yy", "zz"]:
        return
    index = "xyz".index(component[0])
    Rc = record["Rc"]
    coefficient = Rc[index, index]
    # Recover the actual normalized rotated crystal axis without dividing by a
    # possibly zero coefficient; T is supplied explicitly by the caller.
    T = trace.frame
    p = T.T * sp.eye(3)[:, index]
    v = tidy(P * p)
    vx, vy = v
    ti, ts, bi, bs = sp.symbols("theta_i theta_s beta beta_prime", real=True)
    G = (
        lambda th, be: (vx**2 + vy**2) / 2
        + (vx**2 - vy**2) * sp.cos(2 * th) / 2
        + vx * vy * sp.sin(2 * th) * sp.cos(be)
    )
    trace.tex(
        r"R_{c,"
        + component
        + r"}=q\,\mathbf e_"
        + component[0]
        + r"\mathbf e_"
        + component[0]
        + r"^T"
    )
    trace.eq("q", coefficient)
    trace.chain(r"\mathbf p=T^T\mathbf e_" + component[0], [T.T, sp.eye(3)[:, index]], p)
    trace.eq(r"\mathbf v=P\mathbf p", v)
    trace.eq(r"R_{\perp," + component + r"}=q\mathbf v\mathbf v^T", tidy(coefficient * v * v.T))
    trace.tex(r"\mathcal A_{" + component + r"}=q\,(e_s^\dagger\mathbf v)(\mathbf v^TE_i)")
    trace.tex(r"I_{" + component + r"}=|q|^2\,|e_s^\dagger\mathbf v|^2\,|\mathbf v^TE_i|^2")
    trace.tex(r"G(\vartheta,\beta)=|v_x\cos\vartheta+v_y e^{i\beta}\sin\vartheta|^2")
    trace.tex(
        r"G=v_x^2\cos^2\vartheta+v_y^2\sin^2\vartheta+2v_xv_y\cos\vartheta\sin\vartheta\cos\beta"
    )
    trace.tex(
        r"\cos^2\vartheta=(1+\cos2\vartheta)/2,\quad\sin^2\vartheta=(1-\cos2\vartheta)/2,\quad2\sin\vartheta\cos\vartheta=\sin2\vartheta"
    )
    trace.eq(r"G_i(\theta_i,\beta)", sp.factor_terms(G(ti, bi)))
    trace.eq(r"G_s(\theta_s,\beta^\prime)", sp.factor_terms(G(ts, bs)))
    trace.note(
        "The following general product uses direct Jones states before any return optic. The active QWP path is specialized through its effective detector in the matrix steps below."
    )
    power = coefficient * sp.conjugate(coefficient)
    trace.tex(r"I_{" + component + r"}^{\mathrm{direct}}=|q|^2G_iG_s")
    trace.eq(
        r"I_{" + component + r"}^{\mathrm{direct,expanded}}",
        sp.expand(power * G(ti, bi) * G(ts, bs)),
    )
    # Specialize the two overlap factors to the active optical chain itself.
    # In particular, the return QWP changes e_s; it cannot be replaced with a
    # different elliptical scan just because two endpoint states agree.
    incident_overlap = tidy((v.T * optical["Ein"])[0])
    detector_overlap = tidy((optical["effective_analyzer"].H * v)[0])
    incident_power = tidy(incident_overlap * sp.conjugate(incident_overlap))
    detector_power = tidy(detector_overlap * sp.conjugate(detector_overlap))
    trace.eq(r"\eta_i=\mathbf v^TE_i", incident_overlap)
    trace.eq(r"\eta_i^*", sp.conjugate(incident_overlap))
    trace.eq(r"\eta_s=e_s^\dagger\mathbf v", detector_overlap)
    trace.eq(r"\eta_s^*", sp.conjugate(detector_overlap))
    trace.eq(r"G_{i,active}=\eta_i\eta_i^*", incident_power)
    trace.eq(r"G_{s,active}=\eta_s\eta_s^*", detector_power)
    trace.eq(
        r"I_{" + component + r"}^{active}=|q|^2G_{i,active}G_{s,active}",
        tidy(power * incident_power * detector_power),
    )
    if optical["kind"] in ["CUBIC_SIGMA", "COMPONENT_SIGMA_ALPHA"]:
        trace.tex(r"\theta_i=\pi/4,\quad\theta_s=\pi/4+\alpha,\quad\beta=\beta^\prime=\pi/2")
        trace.tex(
            r"\cos2\theta_i=0,\quad\sin2\theta_i=1,\quad\cos\beta=\cos\beta^\prime=0,\quad\cos2\theta_s=-\sin2\alpha"
        )
        special = sp.expand(
            (power * G(ti, bi) * G(ts, bs)).subs(
                {ti: sp.pi / 4, ts: sp.pi / 4 + alpha, bi: sp.pi / 2, bs: sp.pi / 2}
            )
        )
        trace.eq(r"I_{" + component + r"}^{\sigma^{+}\alpha}", sp.trigsimp(special))


def trace_tensor_definition(trace, run):
    """Show the complete phonon tensors before displaying their Ag contributions."""
    trace.section("3. Phonon response and the complete crystal tensor", scope="tensor")
    trace.tex(
        r"\chi_{ij}(\{u_m\})=\chi_{ij}^{(0)}+\sum_m(R_\chi^{(m)})_{ij}u_m+O(u^2),\quad R_{\chi,ij}^{(m)}=\left.\partial\chi_{ij}/\partial u_m\right|_0"
    )
    trace.tex(
        r"\mathbf P_R^{\mathrm{phys},(m)}=\epsilon_0R_\chi^{(m)}\mathbf E_{i,c}^{\mathrm{phys}}u_m,\quad I_m^{\mathrm{physical}}=\kappa_m|\mathcal A_m|^2,\quad I_m^{\mathrm{plot}}=|\mathcal A_m|^2\ (\mathrm{a.u.})"
    )
    trace.note(
        "R_chi is the physical susceptibility derivative. The numerical R_c below uses supplied relative coefficients, whose absolute SI scale is not specified. The normal coordinate may be displacement or mass weighted, so its convention must be stated before assigning an SI unit to R_chi. Symmetry fixes the allowed tensor form. Each phonon branch has its own complex coefficients. The common angular-response scale is set to one in the plotted arbitrary units."
    )
    for name, data in run["families"].items():
        if data.get("irrep") != "Ag" or run["geometry"] is None:
            continue
        trace.section("Complete crystal tensor: " + name)
        Rc = data["partners"][0]
        trace.eq(r"R_{c,Ag}", Rc)
        parts = cartesian_tensor_parts(Rc)
        trace.tex(r"R_{c,Ag}=" + "+".join(r"R_{c," + key + "}" for key in parts))
        T = run["geometry"]["T"]
        trace.chain(r"R_{lab,Ag}", [T.T, Rc, T], tidy(T.T * Rc * T))
        trace.note(
            "The following Ag figures show individual Cartesian contributions of this one tensor. A sum of their powers is not used as the plotted Ag result."
        )


def trace_record(trace, run, channel, record, partner_index):
    """Expand both matrix products, all tensor entries, and the detected amplitude."""
    Rc, optical = record.get("Rc", record["Rperp"]), channel["optical"]
    trace.section(channel["name"] + " / tensor " + str(partner_index), scope="record")
    trace.note(channel["kind"] + ".")
    trace.eq("R_c" if run["geometry"] is not None else "R_{ref}", Rc)
    if run["geometry"] is not None:
        T = run["geometry"]["T"]
        trace.frame = T
        trace.tex(r"(R_cT)_{ij}=\sum_{k=1}^3(R_c)_{ik}T_{kj}")
        trace.chain("R_cT", [Rc, T], tidy(Rc * T))
        trace.tex(r"(R_{lab})_{ij}=\sum_{k=1}^3\sum_{l=1}^3T_{ki}(R_c)_{kl}T_{lj}")
        trace.chain(r"R_{lab}=T^TR_cT", [T.T, Rc, T], record["Rlab"])
        for i in range(3):
            for j in range(3):
                # Display the explicit nine-term substitution even when some
                # terms vanish. It exposes signs and matrix positions.
                terms = [T[k, i] * Rc[k, l] * T[l, j] for k in range(3) for l in range(3)]
                raw = sp.Add(*terms, evaluate=False)
                trace.tex(
                    r"(R_{lab})_{"
                    + str(i + 1)
                    + str(j + 1)
                    + "}="
                    + trace.latex(raw)
                    + "="
                    + trace.latex(sp.expand(record["Rlab"][i, j]))
                )
        trace.chain(r"R_\perp=PR_{lab}P^T", [P, record["Rlab"], P.T], record["Rperp"])
        if channel["component"] in ["xx", "yy", "zz"]:
            trace_rank_one(trace, record, channel["component"], optical)
        Ei3 = tidy(P.T * optical["Ein"])
        Ec = tidy(T * Ei3)
        Pc = tidy(Rc * Ec)
        Pl = tidy(T.T * Pc)
        trace.chain(r"E_{i,lab}=P^TE_i", [P.T, optical["Ein"]], Ei3)
        trace.chain(r"E_{i,c}=TE_{i,lab}", [T, Ei3], Ec)
        trace.chain(r"\mathcal P_c=R_cE_{i,c}", [Rc, Ec], Pc)
        trace.chain(r"\mathcal P_{lab}=T^T\mathcal P_c", [T.T, Pc], Pl)
        trace.chain(r"E_{sc}=P\mathcal P_{lab}", [P, Pl], record["Esc"])
    trace.chain(r"E_{sc}=R_\perp E_i", [record["Rperp"], optical["Ein"]], record["Esc"])
    trace.chain(r"E_{out}=BE_{sc}", [optical["B"], record["Esc"]], record["Eout"])
    trace.eq(r"e_{an}^\dagger", optical["analyzer"].H)
    trace.chain(
        r"\mathcal A=e_{an}^\dagger E_{out}",
        [optical["analyzer"].H, record["Eout"]],
        record["amplitude"],
    )
    row = optical["analyzer"].H
    trace.eq(
        r"\mathcal A=(e_{an})_X^*(E_{out})_X+(e_{an})_Y^*(E_{out})_Y",
        sp.expand(row[0] * record["Eout"][0] + row[1] * record["Eout"][1]),
    )
    basis = record.get("scan_basis", "FIRST")
    keys = ["C", "D"] if basis == "FIRST" else ["K0", "Kc", "Ks"] if basis == "SECOND" else ["K0"]
    for key in keys:
        trace.eq({"K0": "K_0", "Kc": "K_c", "Ks": "K_s"}.get(key, key), record[key])
        trace.eq(
            r"\overline{" + {"K0": "K_0", "Kc": "K_c", "Ks": "K_s"}.get(key, key) + "}",
            sp.conjugate(record[key]),
        )
    trace.eq(r"\mathcal A_{expanded}", sp.expand(record["amplitude"]))
    trace.eq(r"\mathcal A^*", sp.conjugate(record["amplitude"]))
    if basis == "FIRST":
        trace.tex(r"I_j=(C\cos\alpha+D\sin\alpha)(C^*\cos\alpha+D^*\sin\alpha)")
        trace.tex(r"I_j=|C|^2\cos^2\alpha+|D|^2\sin^2\alpha+(CD^*+C^*D)\sin\alpha\cos\alpha")
        trace.tex(
            r"I_j=\frac{|C|^2+|D|^2}{2}+\frac{|C|^2-|D|^2}{2}\cos2\alpha+\operatorname{Re}(CD^*)\sin2\alpha"
        )
    elif basis == "SECOND":
        trace.tex(r"\mathcal A_j=K_0+K_c\cos2\theta+K_s\sin2\theta")
        trace.tex(
            r"I_j=|K_0|^2+|K_c|^2\cos^22\theta+|K_s|^2\sin^22\theta+2\operatorname{Re}(K_0K_c^*)\cos2\theta+2\operatorname{Re}(K_0K_s^*)\sin2\theta+2\operatorname{Re}(K_cK_s^*)\cos2\theta\sin2\theta"
        )
        trace.tex(
            r"\cos^22\theta=(1+\cos4\theta)/2,\quad\sin^22\theta=(1-\cos4\theta)/2,\quad2\sin2\theta\cos2\theta=\sin4\theta"
        )
    else:
        trace.tex(r"\mathcal A=K_0,\qquad I=K_0K_0^*,\qquad\partial I/\partial\alpha=0")


def trace_final(trace, run, channel):
    """Keep symbolic, magnitude/phase and substituted numerical equations distinct."""
    summary = symbolic_intensity_summary(channel["records"])
    symbolic = intensity_expression(summary, trace.variable)
    trace.section("Final intensity: " + channel["name"], scope="final")
    if len(channel["records"]) > 1:
        trace.tex(r"I=\sum_{j\in\mathrm{orthogonal\ phonon\ partners}}|\mathcal A_j|^2")
    else:
        trace.tex(r"I=|\mathcal A|^2")
    if channel["optical"]["scan_basis"] == "SECOND":
        trace.tex(r"I_0=\sum_j\left[|K_{0j}|^2+(|K_{cj}|^2+|K_{sj}|^2)/2\right]")
        trace.tex(
            r"I_c=2\operatorname{Re}\sum_jK_{0j}K_{cj}^*,\quad I_s=2\operatorname{Re}\sum_jK_{0j}K_{sj}^*"
        )
        trace.tex(
            r"I_{4c}=\frac12\sum_j(|K_{cj}|^2-|K_{sj}|^2),\quad I_{4s}=\operatorname{Re}\sum_jK_{cj}K_{sj}^*"
        )
    labels = {"I0": "I_0", "Ic": "I_c", "Is": "I_s", "I4c": "I_{4c}", "I4s": "I_{4s}"}
    for key, value in summary.items():
        trace.eq(labels[key], value)
    variable_tex = raman_latex(trace.variable)
    trace.eq(r"I(" + variable_tex + r")_{symbolic}", symbolic)
    # Preserve exact symbolic coefficients in paper output. UI numerical input
    # values are substituted only in the subsequent equation, never earlier.
    for symbol, value in sorted(channel["values"].items(), key=lambda kv: str(kv[0])):
        trace.eq(raman_latex(symbol), value)
        trace.tex(
            r"|"
            + raman_latex(symbol)
            + "|="
            + trace.latex(sp.Abs(value))
            + r",\quad\arg("
            + raman_latex(symbol)
            + ")="
            + trace.latex(sp.arg(value))
        )
    # Substitute into the symbolic law for the reported equation. This keeps
    # exact cancellations visible instead of printing tiny floating-point
    # harmonic residues from an independently evaluated amplitude summary.
    numeric_expression = sp.expand(sp.N(symbolic.subs(channel["values"]), 12))
    trace.eq(r"I(" + variable_tex + r")_{numerical}", numeric_expression)
    basis = channel["optical"]["scan_basis"]
    if basis == "FIRST":
        trace.tex(r"\frac{dI}{d\alpha}=-2I_c\sin2\alpha+2I_s\cos2\alpha")
        trace.tex(
            r"\Delta=\sqrt{I_c^2+I_s^2},\quad I_{max,min}=I_0\pm\Delta,\quad\alpha_{max}=\tfrac12\operatorname{atan2}(I_s,I_c)\pmod\pi"
        )
    elif basis == "SECOND":
        trace.tex(
            r"\frac{dI}{d\theta}=-2I_c\sin2\theta+2I_s\cos2\theta-4I_{4c}\sin4\theta+4I_{4s}\cos4\theta"
        )
        trace.tex(r"u_1=(I_c-iI_s)/2,\quad u_2=(I_{4c}-iI_{4s})/2,\quad z=e^{2i\theta}")
        trace.tex(r"2u_2z^4+u_1z^3-u_1^*z-2u_2^*=0,\quad|z|=1")
    trace.eq("I_{min}", sp.Float(channel["summary"]["Imin"], 12))
    trace.eq("I_{max}", sp.Float(channel["summary"]["Imax"], 12))
    if channel["summary"]["alpha_max"] is None:
        trace.tex(r"I=\mathrm{constant}:\quad\text{no unique maximum or minimum angle}")
    else:
        trace.eq(
            variable_tex + r"_{max}\ (\mathrm{degree})",
            sp.Float(channel["summary"]["alpha_max"], 12),
        )
    return dict(
        channel=channel["name"], variable=trace.variable, summary=summary, expression=symbolic
    )


def detailed_calculation(run):
    """Generate the same matrix-to-intensity stages for every displayed channel."""
    variable = theta_scan if run["optical"]["scan_basis"] == "SECOND" else alpha
    trace = CalculationTrace(variable, run["config"])
    trace.section("ROTATION RAMAN TENSOR CALCULATION / mathematical derivation")
    trace.note(run["config"]["case_label"])
    trace_geometry(trace, run)
    trace_optics(trace, run)
    trace_tensor_definition(trace, run)
    finals = []
    for channel in run["display_channels"].values():
        for j, record in enumerate(channel["records"], 1):
            trace_record(trace, run, channel, record, j)
        finals.append(trace_final(trace, run, channel))
    trace.section("Independent representation checks", scope="checks")
    for row in matching_protocol_audit(run):
        trace.tex(
            r"\epsilon_{direct}("
            + r"\mathrm{"
            + row["channel"].replace("_", r"\_")
            + "}"
            + ")="
            + raman_latex(sp.Float(row["direct_error"], 5))
            + r",\quad\epsilon_{circular}="
            + raman_latex(sp.Float(row["circular_error"], 5))
        )
    return dict(entries=trace.entries, markdown=trace.markdown(explained=False),
                mathematics_markdown=trace.markdown(explained=False),
                explained_markdown=trace.markdown(explained=True),
                symbol_legend=calculation_symbol_legend(trace.entries),
                reference_ids=calculation_reference_ids(trace.entries),
                finals=finals, references=DERIVATION_REFERENCES)


def latex_document(entries, title="Raman tensor calculation", explained=True):
    """Create a compilable article; long equations scale only when needed."""
    header = r"""\documentclass[10pt]{article}
\usepackage[margin=20mm]{geometry}
\usepackage{amsmath,amssymb,graphicx,hyperref}
\newcommand{\fitmath}[1]{\begingroup\sbox0{$\displaystyle #1$}\ifdim\wd0>\linewidth\resizebox{\linewidth}{!}{\usebox0}\else\usebox0\fi\endgroup}
\allowdisplaybreaks
\begin{document}
"""
    lines = [header, r"\section*{" + latex_text(title) + "}"]
    for item in entries:
        if item["kind"] == "section":
            lines.append(r"\subsection*{" + latex_text(item["value"]) + "}")
        elif item["kind"] == "equation":
            lines.append(r"\[\fitmath{" + item["value"] + r"}\]")
            if explained:
                lines.append(r"\begingroup\small\noindent\textbf{Symbols and units}\par\smallskip")
                for symbol in item.get("symbols", []):
                    lines.append(r"\noindent$" + symbol["latex"] + "$: " + latex_text(symbol["meaning"]) + r" \textit{Unit / convention:} " + latex_text(symbol["units"]) + r"\par\smallskip")
                lines.append(r"\noindent\textit{Derivation / source:} " + latex_text(item.get("derivation_note", "")) + r"\par")
                for key in item.get("reference_ids", []):
                    ref = DERIVATION_REFERENCES[key]
                    label = r"\href{" + ref["url"] + "}{" + latex_text(ref["label"]) + "}" if ref["url"] else latex_text(ref["label"])
                    lines.append(r"\noindent " + label + "; " + latex_text(ref["location"]) + r"\par")
                lines.append(r"\endgroup")
        else:
            lines.append(latex_text(item["value"]) + r"\par")
    if not explained:
        lines.append(r"\section*{Symbols and units}")
        for symbol in calculation_symbol_legend(entries):
            lines.append(r"\noindent$" + symbol["latex"] + "$: " + latex_text(symbol["meaning"]) + r" \textit{Unit / convention:} " + latex_text(symbol["units"]) + r"\par\smallskip")
        lines.append(r"\section*{References}")
        for key in calculation_reference_ids(entries):
            ref = DERIVATION_REFERENCES[key]
            label = r"\href{" + ref["url"] + "}{" + latex_text(ref["label"]) + "}" if ref["url"] else latex_text(ref["label"])
            lines.append(r"\noindent " + label + "; " + latex_text(ref["location"]) + r"\par")
    return "\n\n".join(lines) + r"\end{document}" + "\n"


def paper_intensity_latex(run, derivation):
    """Export symbolic I(angle) before substitution plus a separate numeric file."""
    symbolic, numerical = [], []
    for final in derivation["finals"]:
        name, variable, expression = final["channel"], final["variable"], final["expression"]
        common = [
            dict(kind="section", value=name),
            dict(kind="note", value=run["config"]["case_label"] + "; " + run["config"]["optics"]),
        ]
        symbolic.extend(
            common
            + [dict(kind="equation", value="I(" + raman_latex(variable) + ")=" + raman_latex(expression))]
        )
        substituted = sp.expand(sp.N(expression.subs(run["display_channels"][name]["values"]), 12))
        numerical.extend(
            common
            + [
                dict(
                    kind="equation", value="I(" + raman_latex(variable) + ")=" + raman_latex(substituted)
                )
            ]
        )
    for collection in (symbolic, numerical):
        for index, item in enumerate(collection):
            if item["kind"] == "equation":
                collection[index] = annotate_equation(item["value"], scope="final", context=run["config"])
    return dict(
        symbolic=latex_document(symbolic, "Symbolic intensity equations"),
        numerical=latex_document(numerical, "Intensity equations with numerical inputs"),
        full=latex_document(derivation["entries"], "1. Full mathematics", explained=False),
        explained=latex_document(derivation["entries"], "2. Explained derivation", explained=True),
    )

print("Cell 12/22 — Run completed successfully.\nReady: Derivation functions, symbol definitions, units and reference notes are ready.\nNext: Run Cell 13.", flush=True)


# %% Code cell 13: Scientific figures
"""Create readable calculation records and figures from already-computed results."""


def run_description(run):
    """Label the actual workflow/model; never assign a crystal to the 2D source."""
    config = run["config"]
    if config["tensor_model"] == "QWP_SOURCE_2D":
        return "Quarter-wave-plate — original 2×2 source model"
    method = METHOD_LABELS[config["calculation_method"]]
    suffix = " / 3D extension" if config["calculation_method"] == "QWP" else ""
    scope = " | ℓ=0 Jones reference" if config["calculation_method"] == "CIRCULAR" else ""
    return f"{method}{suffix} | {config['material']} / {config['point_group']} | {config['hkl']}{scope}"


def qwp_source_steps_markdown(run):
    """Follow the thirteen main-source steps without calling the REFERENCE reporter."""
    config, optical = run["config"], run["optical"]
    algebra = qwp_source_algebra()
    record = run["results"][QWP_MODE]["terms"][0]
    values = run["families"][QWP_MODE]["values"]
    lines = [
        "# ROTATION RAMAN TENSOR CALCULATION",
        "## Quarter-wave-plate — original source calculation",
        "**Case:** " + config["case_label"],
        "**Input note:** " + config["input_note"],
        "This route reproduces the main calculation of the supplied Quarter-wave-plate notebook. All fields and the polar curve are calculated from its complete 2×2 tensor and optical matrices.",
    ]

    def equation(label, expression):
        """Append an exact or numerically substituted source equation."""
        lines.append("$$" + label + "=" + raman_latex(expression) + "$$")

    lines.extend("- " + item for item in run["assumptions"])
    lines += [
        "### 1. Symbols",
        "a,A are real source amplitudes; δ,φ and α are real. Phase controls use degrees; matrix calculations use radians.",
        "Active source inputs: `" + json.dumps(serializable(config["source_parameters"])) + "`.",
        "### 2. Laboratory and circular bases",
    ]
    equation(r"\hat x", x_hat)
    equation(r"\hat y", y_hat)
    equation(r"\sigma^{+}", sig_p)
    equation(r"\sigma^{-}", sig_m)
    lines.append("### 3. Quarter-wave plate at −45°")
    equation("Q", QWP_QWP)
    equation(r"Q^\dagger Q", sp.simplify(QWP_QWP.H * QWP_QWP))
    lines.append("### 4. Incident field after the plate")
    equation(r"E_i=Q\hat x", optical["Ein"])
    lines.append(r"$$E_i=e^{i\pi/4}\sigma^{+}.$$")
    lines.append("### 5. Complete complex source tensor")
    equation("R", QWP_SOURCE_TENSOR)
    equation(r"R_{\rm numerical}", sp.N(record["Rperp"].subs(values), 7))
    lines.append("### 6. Circular-basis tensor elements")
    equation(r"R_{++}=(\sigma^{+})^\dagger R\sigma^{+}", algebra["Rpp"])
    equation(r"R_{-+}=(\sigma^{-})^\dagger R\sigma^{+}", algebra["Rmp"])
    lines.append("### 7. Raman-scattered field")
    equation(r"E_{sc}=R E_i", record["Esc"])
    lines.append(r"$$E_{sc}=e^{i\pi/4}(R_{++}\sigma^{+}+R_{-+}\sigma^{-}).$$")
    lines.append("### 8. Return plate and analyzer reference")
    equation(r"Q_{back}=Q^T", optical["B"])
    for label, key in [
        (r"Q_{back}\sigma^{+}", "v_plus"),
        (r"Q_{back}\sigma^{-}", "v_minus"),
        (r"\hat e_{ref}", "e_ref"),
        (r"\hat e_\perp", "e_perp"),
        ("p_1", "p1"),
        ("p_2", "p2"),
    ]:
        equation(label, algebra[key])
    equation("p_2/p_1", sp.simplify(algebra["p2"] / algebra["p1"]))
    lines.append("### 9. Linear analyzer axis")
    equation(r"e_\alpha", optical["analyzer"])
    lines.append(
        "The analyzer passes +Y at α=0 and −X at α=90°, after the returning plate."
    )
    lines.append("### 10. Returning field and detected amplitude")
    equation(r"E_{out}=Q_{back}E_{sc}", record["Eout"])
    equation(r"\mathcal A=e_\alpha^\dagger E_{out}", record["amplitude"])
    lines.append(r"$$\mathcal A=-R_{++}\cos\alpha-iR_{-+}\sin\alpha.$$")
    lines.append(
        "The minus sign is the source's common global phase. It drops out only after the squared modulus."
    )
    lines.append("### 11. Intensity from the complete amplitude")
    lines.append(
        r"$$I=|\mathcal A|^2=|R_{++}|^2\cos^2\alpha+|R_{-+}|^2\sin^2\alpha+2\operatorname{Im}(R_{++}R_{-+}^*)\sin\alpha\cos\alpha.$$"
    )
    for label, key in [
        (r"|R_{++}|^2", "Ipp"),
        (r"|R_{-+}|^2", "Imp"),
        (r"\operatorname{Im}(R_{++}R_{-+}^*)", "Icross"),
    ]:
        equation(label, algebra[key])
    equation(r"I_{\mathrm{source\ closed\ form}}", algebra["source_intensity"])
    lines.append(
        "The closed form is checked independently. The curve itself is evaluated from the matrix-chain amplitude above."
    )
    lines.append("### 12. Source special cases")
    lines.extend(
        [
            r"$$\phi=0:\quad I=(a^2+A^2-2aA\sin\delta)\cos^2\alpha.$$",
            r"$$A=0:\quad I=a^2\cos^2(\alpha-\phi/2).$$",
            r"$$A=0,\ \phi=\pi:\quad I=a^2\sin^2\alpha.$$",
        ]
    )
    lines.append("### 13. Calculated polar curve")
    total = run["summaries"][QWP_MODE]
    lines.append(final_intensity_context(run, QWP_MODE))
    equation(
        r"I(\alpha)\;\mathrm{(active\ inputs)}",
        display_intensity(total),
    )
    lines.append(
        "The Cartesian and polar figures use this same computed result. Source identity: `"
        + QWP_SOURCE["filename"]
        + "`, SHA-256 `"
        + QWP_SOURCE["sha256"]
        + "`."
    )
    return "\n\n".join(lines)


def steps_markdown(run):
    """Explain inputs, geometry, Jones propagation and channel intensities in English."""
    if run["config"]["tensor_model"] == "QWP_SOURCE_2D":
        return qwp_source_steps_markdown(run)
    if run["config"]["calculation_method"] == "CUBIC_REF":
        return cubic_steps_markdown(run)
    if run["config"]["calculation_method"] in ["CIRCULAR", "LINEAR"]:
        return paper_steps_markdown(run)
    config, geometry, optical = run["config"], run["geometry"], run["optical"]
    lines = [
        "# ROTATION RAMAN TENSOR CALCULATION",
        "## 1. Declared inputs and interpretation",
        f"**Case:** {config.get('case_label', 'Untitled case')}",
        "**Calculation workflow:** " + run_description(run),
        f"**Material / point group:** {config['material']} / {config['point_group']}",
        f"**Plane / in-plane direction:** {config['hkl']} / {config['uvw']}; normal-side sign={config['normal_sign']}; frame angle ψ={config['azimuth_deg']}°.",
        f"**Optical method:** {optical['label']}",
        "**Input note:** " + config.get("input_note", "User-supplied parameters."),
        "The in-plane frame angle ψ and detection scan angle α are distinct. No fitting or alignment to a target polar plot is performed.",
    ]

    def equation(label, expression):
        """Append an equation computed from the current run."""
        lines.append("$$" + label + "=" + raman_latex(expression) + "$$")

    lines.extend("- " + item for item in run["assumptions"])
    lines.append("## 2. Build the proper 3D measurement frame")
    for key in ["L", "g", "t", "X0", "Y0", "T"]:
        if key in geometry:
            equation(key, geometry[key])
    equation(r"T^{-1}=T^T", geometry["T"].T)
    equation(r"T^TT", tidy(geometry["T"].T * geometry["T"]))
    equation(r"\det T", sp.simplify(geometry["T"].det()))
    lines.extend(geometry["notes"])
    lines.append(
        "Positive ψ rotates the measurement X axis toward Y around Z. For an active sample rotation at fixed laboratory optics, the sign convention must be converted accordingly."
    )
    lines.append("## 3. Propagate the Jones states")
    if config["optics"] == "QWP":
        equation(r"Q_{\mathrm{QWP}}", QWP_QWP)
    equation(r"E_i", optical["Ein"])
    equation(r"B_{\mathrm{return}}", optical["B"])
    equation(r"e_{\mathrm{analyzer}}(\alpha)", optical["analyzer"])
    equation(
        r"e_{s,\mathrm{effective}}=B^\dagger e_{\mathrm{analyzer}}", optical["effective_analyzer"]
    )
    equation("P", P)
    lines.append(
        "Actual optical parameters: `" + json.dumps(serializable(optical["parameters"])) + "`."
    )
    lines.append(r"$$\mathcal A_j=e_{\rm analyzer}^\dagger B P T^T R_{c,j}T P^T E_i.$$")
    if config["calculation_method"] == "COMPONENT_REFERENCE":
        lines.extend(component_ag_flow_markdown(run))
    else:
        lines.append(
            "The following 3D geometry is an extension of the Quarter-wave-plate source. The original Jones sequence and coherent intensity rule are retained for each complete tensor."
        )
        lines.append(
            r"$$R_{++}=\tfrac12[R_{xx}+R_{yy}+i(R_{xy}-R_{yx})],\quad R_{-+}=\tfrac12[R_{xx}-R_{yy}+i(R_{xy}+R_{yx})].$$"
        )
        lines.append(r"$$\mathcal A=-R_{++}\cos\alpha-iR_{-+}\sin\alpha,\quad I=|\mathcal A|^2.$$")
    lines.append("## 4. Rotate and calculate every mode/channel")
    for name, result in run["results"].items():
        family_data = run["families"][name]
        values = family_data["values"]
        lines.append(f"### {name} ({family_data['irrep']})")
        lines.append("**Combination rule:** " + RULE_LABELS[result["rule"]] + ".")
        lines.append(family_data["combination_reason"])
        if family_data["note"]:
            lines.append(family_data["note"])
        if result["rule"] == "COMPONENT_POWER_SUM":
            equation(r"R_{Ag,c}\;\mathrm{(complete\ tensor)}", DIAG)
            equation(r"R_{Ag,lab}=T^T R_{Ag,c}T", tidy(geometry["T"].T * DIAG * geometry["T"]))
            lines.append(
                "The complete tensor above audits the rotation. The requested REFERENCE curve sums the following three component intensities; it does not square the sum of their amplitudes."
            )
        for index, (record, label) in enumerate(
            zip(result["terms"], family_data["calculation_labels"]), 1
        ):
            lines.append(f"#### Channel {index}: {label}")
            if config["show_steps"]:
                equation(r"R_c", record["Rc"])
                equation(r"R_cT", tidy(record["Rc"] * geometry["T"]))
                equation(r"R_{lab}=T^TR_cT", record["Rlab"])
                equation(r"R_\perp=P R_{lab}P^T", record["Rperp"])
            equation(r"R_{lab,\rm numerical}", sp.N(record["Rlab"].subs(values), 6))
            equation(r"R_{\perp,\rm numerical}", sp.N(record["Rperp"].subs(values), 6))
            if config["calculation_method"] == "QWP":
                for label, state_s in [(r"R_{++}", sig_p), (r"R_{-+}", sig_m)]:
                    equation(label, tidy((state_s.H * record["Rperp"] * sig_p)[0].subs(values)))
            equation(r"E_{i,3D}=P^TE_i", record["Ein3"])
            equation(
                r"\mathcal P_{\rm Raman,3D}\propto R_{lab}E_{i,3D}",
                sp.N(record["Einduced3"].subs(values), 6),
            )
            equation(
                r"E_{sc}\propto P\mathcal P_{\rm Raman,3D}", sp.N(record["Esc"].subs(values), 6)
            )
            equation(r"E_{out}=B E_{sc}", sp.N(record["Eout"].subs(values), 6))
            equation("C_j", sp.N(record["C"].subs(values), 7))
            equation("D_j", sp.N(record["D"].subs(values), 7))
            equation(r"\mathcal A_j(\alpha)", tidy(record["amplitude"].subs(values)))
            summary = summary_from_pairs(result["numeric_pairs"][[index - 1]])
            equation(
                r"I_j(\alpha)=|\mathcal A_j|^2",
                summary["I0"]
                + summary["Ic"] * sp.cos(2 * alpha)
                + summary["Is"] * sp.sin(2 * alpha),
            )
        total = run["summaries"][name]
        lines.append(final_intensity_context(run, name))
        lines.append(
            r"The final intensity is $I=|\mathcal A|^2$ for this complete tensor."
            if result["rule"] == "SINGLE_TENSOR"
            else r"The final intensity is $I=\sum_j|\mathcal A_j|^2$ with the channel meaning stated above."
        )
        equation(
            r"I(\alpha)",
            display_intensity(total),
        )
    lines.append("## 5. Sources and limits")
    if config["calculation_method"] == "QWP":
        lines.append(
            "The Quarter-wave-plate optical sequence was checked against the uploaded source notebook: `"
            + QWP_SOURCE["filename"]
            + "`."
        )
    for key in dict.fromkeys(MATERIALS[config["material"]]["sources"] + ["birefringence"]):
        source = SOURCES[key]
        lines.append(f"- {source['title']}: {source['url']}")
    return "\n\n".join(lines)


def figures_for_run(run):
    """Plot total intensity and optional channels; normalization only affects display."""
    config = run["config"]
    if config["calculation_method"] == "LINEAR":
        figures = linear_figures(run)
        if config["show_geometry"]:
            figures.append(("orientation", orientation_figure(run)))
        return figures
    names = list(run["results"])
    figure = plt.figure(figsize=(11, 3.7 * len(names)), layout="constrained")
    grid = figure.add_gridspec(len(names), 2)
    figures = []
    for row, name in enumerate(names):
        total = run["curves"][name]
        maximum = run["summaries"][name]["Imax"]
        scale = maximum if config["normalize"] and maximum > 0 else 1
        cartesian = figure.add_subplot(grid[row, 0])
        polar = figure.add_subplot(grid[row, 1], projection="polar")
        for axes, angles in [(cartesian, np.rad2deg(run["angles"])), (polar, run["angles"])]:
            if config["show_components"] and len(run["component_curves"][name]) > 1:
                for label, curve in zip(
                    run["families"][name]["calculation_labels"], run["component_curves"][name]
                ):
                    axes.plot(angles, curve / scale, "--", linewidth=1, alpha=0.65, label=label)
            axes.plot(angles, total / scale, color="#124e78", linewidth=2.2, label="total")
            axes.set_ylim(0, 1 if maximum == 0 else 1.08 * maximum / scale)
        cartesian.set(
            xlim=(0, 360),
            xlabel=run["scan_label"],
            ylabel="I / Imax of total mode" if config["normalize"] else "Intensity (a.u.)",
            title=f"{name} — {RULE_LABELS[run['results'][name]['rule']]}",
        )
        cartesian.grid(alpha=0.25)
        cartesian.legend(fontsize=8)
        polar.set_theta_zero_location("E")
        polar.set_theta_direction(1)
        polar.set_title(name + (" — zero signal" if maximum == 0 else " — radius = intensity"))
        polar.yaxis.set_major_locator(MaxNLocator(5))
    figure.suptitle(
        run_description(run),
        fontsize=10,
    )
    figures.append(("polar_intensity", figure))
    if not run["physics"]["uses_coherent_intensity"]:
        figures.append(("component_coherent_comparison", component_coherent_figure(run)))
    if config["show_geometry"] and run["geometry"] is not None:
        figures.append(("orientation", orientation_figure(run)))
    return figures


def component_coherent_figure(run):
    """Compare the unchanged REFERENCE rule with the complete tensor using identical inputs."""
    names = [
        name
        for name, item in run["physics"]["interference"].items()
        if item["selected_is_component_prescription"]
    ]
    figure = plt.figure(figsize=(11, 4 * len(names)), layout="constrained")
    grid = figure.add_gridspec(len(names), 2)
    for row, name in enumerate(names):
        item = run["physics"]["interference"][name]
        maximum = max(
            float(item["coherent_intensity"].max()), float(item["selected_intensity"].max())
        )
        scale = maximum if run["config"]["normalize"] and maximum > 0 else 1
        cartesian = figure.add_subplot(grid[row, 0])
        polar = figure.add_subplot(grid[row, 1], projection="polar")
        for axes, angles in [(cartesian, np.rad2deg(run["angles"])), (polar, run["angles"])]:
            axes.plot(
                angles,
                item["coherent_intensity"] / scale,
                color="#124e78",
                linewidth=2,
                label="Complete coherent tensor",
            )
            axes.plot(
                angles,
                item["selected_intensity"] / scale,
                "--",
                color="#c76d24",
                linewidth=2,
                label="Preserved REFERENCE component sum",
            )
            axes.set_ylim(0, 1.08 * maximum / scale if maximum > 0 else 1)
        cartesian.set(
            xlim=(0, 360),
            xlabel=run["scan_label"],
            ylabel=(
                "I / common comparison maximum"
                if run["config"]["normalize"]
                else "Intensity (a.u.)"
            ),
            title=name + ": same tensor, geometry and Jones states",
        )
        cartesian.grid(alpha=0.25)
        cartesian.legend(fontsize=8)
        polar.set_theta_zero_location("E")
        polar.set_theta_direction(1)
        polar.set_title("Interference changes the result; the REFERENCE curve is unchanged")
    figure.suptitle(
        "Within one phonon: coherent amplitude sum versus REFERENCE prescription", fontsize=11
    )
    return figure


def orientation_figure(run):
    """Plot the proper crystal-to-measurement frame used by any 3D workflow."""
    figure = plt.figure(figsize=(7, 6))
    axes = figure.add_subplot(111, projection="3d")
    frame = numeric(run["geometry"]["T"]).real
    for index, label in enumerate(["x crystal", "y crystal", "z crystal"]):
        vector = np.eye(3)[:, index]
        axes.quiver(0, 0, 0, *vector, color="gray", alpha=0.45)
        axes.text(*(1.08 * vector), label, color="gray")
    for index, (label, color) in enumerate(
        zip(["X lab", "Y lab", "Z normal"], ["#087f8c", "#d26a20", "#744caa"])
    ):
        vector = frame[:, index]
        axes.quiver(0, 0, 0, *vector, color=color, linewidth=2)
        axes.text(*(1.14 * vector), label, color=color)
    u, v = np.meshgrid(np.linspace(-0.6, 0.6, 2), np.linspace(-0.6, 0.6, 2))
    plane = frame[:, 0, None, None] * u + frame[:, 1, None, None] * v
    axes.plot_surface(*plane, alpha=0.12, color="#087f8c")
    axes.set(
        xlim=(-1.4, 1.4),
        ylim=(-1.4, 1.4),
        zlim=(-1.4, 1.4),
        xlabel="Cartesian crystal x",
        ylabel="Cartesian crystal y",
        zlabel="Cartesian crystal z",
    )
    axes.set_box_aspect((1, 1, 1))
    return figure


def comparison_figure(runs, normalized=True):
    """Overlay frozen runs and label their actual geometry and optical method."""
    figure = plt.figure(figsize=(13, 6), layout="constrained")
    cartesian = figure.add_subplot(121)
    polar = figure.add_subplot(122, projection="polar")
    styles = ["-", "--", "-.", ":"]
    for index, run in enumerate(runs, 1):
        config = run["config"]
        for name, curve in run["curves"].items():
            maximum = run["summaries"][name]["Imax"]
            scale = maximum if normalized and maximum > 0 else 1
            label = f"{index}: {name} | {run_description(run)} | {config['optics']}"
            style = styles[(index - 1) % len(styles)]
            cartesian.plot(
                np.rad2deg(run["angles"]), curve / scale, style, label=label, linewidth=1.5
            )
            polar.plot(run["angles"], curve / scale, style, linewidth=1.5)
    cartesian.set(
        xlim=(0, 360),
        xlabel="Scan angle (°); α or θ according to each case",
        ylabel="I / Imax of each mode" if normalized else "Intensity (a.u.)",
    )
    cartesian.set_ylim(bottom=0)
    cartesian.grid(alpha=0.25)
    cartesian.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    polar.set_theta_zero_location("E")
    polar.set_ylim(bottom=0)
    polar.yaxis.set_major_locator(MaxNLocator(5))
    figure.suptitle("Saved cases — compare the stated polarization and scan protocols")
    return figure


"""Scientific polar and Cartesian figures with one visible Ag component per plot."""
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, ScalarFormatter


def channel_display_scales(run):
    """Use a shared scale for all components and paired channels of one mode."""
    maxima = {}
    for item in run["display_channels"].values():
        group = item["normalization_group"]
        maxima[group] = max(maxima.get(group, 0.0), float(np.max(item["curve"])))
    return {group: value if value > 0 else 1.0 for group, value in maxima.items()}


def configure_polar_axis(axis, upper):
    """The radius is intensity; zero degrees is right and angles increase CCW."""
    axis.set_theta_zero_location("E")
    axis.set_theta_direction(1)
    axis.set_thetagrids(np.arange(0, 360, 45))
    radial_limit = upper if upper > 0 else 1
    axis.set_ylim(0, radial_limit)
    candidates = MaxNLocator(nbins=3, min_n_ticks=2).tick_values(0, radial_limit)
    axis.set_yticks([value for value in candidates if 0 < value < 0.92 * radial_limit])
    axis.yaxis.set_major_formatter(
        FuncFormatter(lambda radius, _: "" if radius == 0 else f"{radius:.3g}")
    )
    # Stack radius labels vertically: 22-point labels such as 0.02 and 0.04
    # otherwise overlap along a shallow radial line on a 6.5-by-5-inch figure.
    axis.set_rlabel_position(112.5)
    axis.grid(True, linestyle=":", linewidth=0.9, color="0.65")
    axis.tick_params(pad=9)
    axis.spines["polar"].set_linewidth(2)


def short_case_label(run):
    cfg = run["config"]
    if run["geometry"] is None:
        return "Optical reference"
    hkl = (
        "".join(str(int(x)) for x in cfg["hkl"])
        if cfg.get("orientation", "hkl") == "hkl"
        else "manual frame"
    )
    return str(cfg["material"]) + " (" + hkl + ")"


def publication_figures(run):
    """Create separate component figures; never add an Ag component-sum curve."""
    answer = []
    scales = channel_display_scales(run)
    normalized = bool(run["config"].get("normalize"))
    for index, (name, item) in enumerate(run["display_channels"].items()):
        scale = scales[item["normalization_group"]] if normalized else 1.0
        curve = item["curve"] / scale
        figure, axis = plt.subplots(subplot_kw={"projection": "polar"})
        figure.subplots_adjust(left=0.13, right=0.86, bottom=0.22, top=0.77)
        axis.plot(run["angles"], curve, color=f"C{index%10}")
        configure_polar_axis(axis, float(np.max(curve)) * 1.08)
        axis.set_title(name + "\n" + short_case_label(run), pad=23)
        radius_label = "Intensity / common mode maximum" if normalized else "Intensity (a.u.)"
        figure.text(0.5, 0.025, radius_label, ha="center", va="bottom", fontsize=19)
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
        answer.append(("polar_" + safe_name, figure))
        if run["config"].get("cartesian_plots", False):
            figure, axis = plt.subplots(layout="constrained")
            axis.plot(np.rad2deg(run["angles"]), curve, color=f"C{index%10}")
            axis.set_xlim(0, 360)
            axis.set_xticks(np.arange(0, 361, 90))
            axis.xaxis.set_minor_locator(AutoMinorLocator(2))
            axis.yaxis.set_minor_locator(AutoMinorLocator(2))
            axis.set_ylim(bottom=0, top=float(np.max(curve)) * 1.1 if np.max(curve) > 0 else 1)
            axis.set_xlabel(run["scan_label"])
            axis.set_ylabel("Normalized intensity" if normalized else "Intensity (a.u.)")
            axis.set_title(name + "\n" + short_case_label(run))
            answer.append(("cartesian_" + safe_name, figure))
    return answer


def publication_orientation(run):
    """Draw the actual frame, using the same font and line conventions."""
    if run["geometry"] is None:
        return None
    figure = plt.figure(figsize=(6.5, 5))
    axis = figure.add_subplot(projection="3d")
    figure.subplots_adjust(left=0, right=0.85, bottom=0.02, top=0.86)
    T = numeric(run["geometry"]["T"]).real
    for index, label in enumerate(["x", "y", "z"]):
        v = np.eye(3)[:, index]
        axis.quiver(0, 0, 0, *v, color="0.65", linestyle=":", linewidth=2)
        axis.text(*(1.12 * v), label, color="0.4", fontsize=19)
    for index, label in enumerate(["X", "Y", "Z"]):
        v = T[:, index]
        axis.quiver(0, 0, 0, *v, color=f"C{index}", linewidth=2)
        axis.text(*(1.12 * v), label, color=f"C{index}", fontsize=22)
    axis.set(xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), zlim=(-1.2, 1.2))
    axis.set_xticks([-1, 0, 1])
    axis.set_yticks([-1, 0, 1])
    axis.set_zticks([-1, 0, 1])
    axis.set_box_aspect((1, 1, 1))
    axis.set_title(short_case_label(run), pad=20)
    return figure


def publication_cubic_figure(study, individual=None):
    """Use the supplied style for the six-surface reference without rescaling curves."""
    protocols = [individual] if individual else list(CUBIC_PANELS)
    figure, axes = plt.subplots(
        1,
        len(protocols),
        subplot_kw={"projection": "polar"},
        figsize=(6.5 * len(protocols), 7),
        squeeze=False,
    )
    figure.subplots_adjust(left=0.06, right=0.94, bottom=0.24, top=0.74, wspace=0.47)
    for axis, protocol in zip(axes[0], protocols):
        upper = 0
        for k, run in enumerate(study["runs"][protocol]):
            curve = run["curves"]["T2g"] / study["common_d"] ** 2
            axis.plot(study["angles"], curve, color=CUBIC_COLORS[k], label=f"(5{k}0)")
            upper = max(upper, float(np.max(curve)))
        configure_polar_axis(axis, upper * 1.08)
        title = {
            "VV": r"VV: $\theta$",
            "VH": r"VH: $\theta$",
            "SIGMA": r"$\sigma^{+}\alpha$: $\alpha$",
        }[protocol]
        axis.set_title(title, pad=24)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(
        handles, labels, loc="lower center", ncol=3 if individual else 6, bbox_to_anchor=(0.5, 0.03)
    )
    figure.suptitle(r"Si $T_{2g}$ / common $I/|d|^2$", y=0.98)
    return figure


def publication_comparison(runs, channel_name, normalized=True):
    """Compare selected component snapshots without changing their physical inputs."""
    eligible = [r for r in runs if channel_name in r["display_channels"]]
    if not eligible:
        raise ValueError("Save a result containing the selected channel first.")
    bases = {r["display_channels"][channel_name]["optical"]["scan_basis"] for r in eligible}
    if len(bases) > 1:
        raise ValueError("Select cases with the same scan definition for a polar overlay.")
    figure, axis = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(6.5, 6.5))
    figure.subplots_adjust(left=0.13, right=0.86, bottom=0.28, top=0.83)
    upper = 0
    for index, run in enumerate(eligible):
        item = run["display_channels"][channel_name]
        scale = channel_display_scales(run)[item["normalization_group"]] if normalized else 1
        curve = item["curve"] / scale
        axis.plot(run["angles"], curve, label=f"{index+1}. " + short_case_label(run))
        upper = max(upper, float(np.max(curve)))
    configure_polar_axis(axis, upper * 1.08)
    axis.set_title(channel_name, pad=22)
    axis.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14))
    return figure

print("Cell 13/22 — Run completed successfully.\nReady: Polar-plot, Cartesian-plot and measurement-frame figure functions are ready.\nNext: Run Cell 14.", flush=True)


# %% Code cell 14: Six-surface silicon benchmark
"""Cubic benchmark, computed by the existing 3D Jones engine."""

CUBIC_SOURCE = dict(
    title="Helicity-Dependent Raman Spectroscopy of Diamond and Zinc-Blende Crystal Structures",
    journal="Journal of Raman Spectroscopy 57, 809-820 (2026)",
    doi="10.1002/jrs.70113",
    url="https://doi.org/10.1002/jrs.70113",
    pdf_pages_read=12,
    sha256="b54bb6b858da5abfd7f919129a1a31aea86521c5df863b05ebbcd8c75321f049",
    supporting_information="Separate SI is listed by the publisher; its download was unavailable during this revision. No claim to have read that separate file. Fig. 1 is reconstructed from main-text Eqs. 1-11 and independently derived checks.",
)
SOURCES["cubic_2026"] = CUBIC_SOURCE
CUBIC_PANELS = {
    "VV": ("CUBIC_VV", "Fig1a_VV.csv", "theta_deg", "(a) VV"),
    "VH": ("CUBIC_VH", "Fig1b_VH.csv", "theta_deg", "(b) VH"),
    "SIGMA": ("CUBIC_SIGMA", "Fig1c_sigma_plus_alpha.csv", "alpha_deg", r"(c) $\sigma^{+}\alpha$"),
}
CUBIC_COLORS = ["#ff0000", "#ff8c00", "#20a928", "#1685c4", "#9362cf", "#916252"]

CUBIC_READING_NOTES = "### Cubic benchmark reference\n\nDOI 10.1002/jrs.70113: the six-surface silicon benchmark uses the Eq. 4 frame, Eq. 11 Jones states and the complete T2g partner sum. VV and VH scan θ; σ⁺α scans α with θ=45 degrees and β=β′=90 degrees. All curves use one shared coefficient scale. The companion guides provide the derivation and independent checks."


def cubic_frame(indices):
    """Construct the paper's cubic Cartesian frame, including its polar-axis limit."""
    h, k, ell = real_vector(indices, "Cubic Miller indices")
    norm = sp.sqrt(h * h + k * k + ell * ell)
    m2 = sp.simplify(h * h + k * k)
    if zero(sp.Matrix([m2])):
        return sp.eye(3) if float(ell) > 0 else sp.diag(1, -1, -1)
    m = sp.sqrt(m2)
    return validate_frame(
        sp.Matrix.hstack(
            sp.Matrix([k, -h, 0]) / m,
            sp.Matrix([h * ell, k * ell, -m2]) / (m * norm),
            sp.Matrix([h, k, ell]) / norm,
        )
    )


def cubic_fig1_config(k, protocol, magnitude=1, plot_points=721):
    """Build one locked Fig. 1 case using the ordinary material/geometry engine."""
    if isinstance(k, bool) or k not in range(6) or protocol not in CUBIC_PANELS:
        raise ValueError("Fig. 1 uses integer k=0..5 and protocol VV, VH or SIGMA.")
    magnitude = real_number(magnitude, "Common tensor magnitude |d|")
    if magnitude <= 0:
        raise ValueError("Use a positive common |d| for the Fig. 1 intensity scale.")
    config = demonstration_config("Si", CUBIC_PANELS[protocol][0])
    config.update(
        hkl=(5, k, 0),
        uvw=(k, -5, 0),
        normal_sign=1,
        case_label=f"Cubic benchmark {protocol}: ({5}{k}{0})",
        input_note="Si T2g triplet; paper Eq. 4 axes, Eq. 11 states, common d; theoretical matrix calculation.",
        plot_points=plot_points,
        normalize=False,
        show_components=False,
    )
    config["mode_values"]["T2g"] = {d: exact(magnitude)}
    return config


def cubic_projected_partners(run):
    """Apply Eq. 8 to three complete rotated tensors, without splitting their entries."""
    frame = run["geometry"]["T"]
    records = run["results"]["T2g"]["terms"]
    return [
        tidy(sum((frame[row, column] * records[row]["Rlab"] for row in range(3)), sp.zeros(3)))
        for column in range(3)
    ]


def cubic_steps_markdown(run):
    """Document the actual rotated tensors, optical states and complete-partner sum."""
    variable = theta_scan if run["optical"]["scan_basis"] == "SECOND" else alpha
    lines = [
        "# ROTATION RAMAN TENSOR CALCULATION",
        "## Cubic reference tensor/Jones calculation",
        "**Case:** " + run["config"]["case_label"],
        "**Source:** " + CUBIC_SOURCE["title"] + ". " + CUBIC_SOURCE["url"],
        "The benchmark uses main-text Eqs. 1-11. Other materials use the same optical states as a general tensor/Jones extension.",
    ]

    def equation(label, expression):
        """Show an expression calculated from the active matrices, with the correct scan label."""
        lines.append("$$" + label + "=" + raman_latex(expression.subs(alpha, variable)) + "$$")

    equation("T", run["geometry"]["T"])
    equation(r"T^{-1}=T^T", run["geometry"]["T"].T)
    equation(r"e_i", run["optical"]["Ein"])
    equation(r"e_s", run["optical"]["effective_analyzer"])
    lines.append(
        "VV/VH use the paper's θ parameter; σ⁺α fixes θ=45 degrees and scans α. For an active laboratory sample rotation the frame-angle sign must be converted consistently."
    )
    for name, result in run["results"].items():
        values = run["families"][name]["values"]
        lines.append("### " + name + ": complete phonon partners")
        for i, record in enumerate(result["terms"], 1):
            lines.append("**Partner " + str(i) + ".**")
            if run["config"]["show_steps"]:
                equation("R_c", record["Rc"])
                equation(r"R_{lab}=T^TR_cT", record["Rlab"])
                equation(r"R_\perp=P R_{lab}P^T", record["Rperp"])
            equation(r"\mathcal A_" + str(i), tidy(record["amplitude"].subs(values)))
        lines.append(
            r"$$I=\sum_{\nu\in\mathrm{orthogonal\ partners}}|\mathcal A_\nu|^2.$$ Each complete tensor is contracted coherently. This sum does not discard interference within a tensor."
        )
        lines.append(final_intensity_context(run, name))
        equation("I", display_intensity(run["summaries"][name], variable))
    return "\n\n".join(lines)


def cubic_all_extrema(summary):
    """Return all global extremum angles from harmonic stationary roots over 0..360 degrees."""
    ic, iss = summary["Ic"], summary["Is"]
    i4c, i4s = summary.get("I4c", 0), summary.get("I4s", 0)
    if max(abs(ic), abs(iss), abs(i4c), abs(i4s)) < 1e-13 * max(
        summary["I0"], np.finfo(float).tiny
    ):
        return dict(maxima_deg=[], minima_deg=[], constant=True)
    u1, u2 = (ic - 1j * iss) / 2, (i4c - 1j * i4s) / 2
    poly = np.trim_zeros(
        np.array([2 * u2, u1, 0, -u1.conjugate(), -2 * u2.conjugate()], complex), "f"
    )
    roots = np.roots(poly)
    base = [(np.angle(z) / 2) % np.pi for z in roots if abs(abs(z) - 1) < 1e-5]
    angles = np.unique(np.round(np.rad2deg(base + [x + np.pi for x in base]) % 360, 9) % 360)
    values = (
        summary["I0"]
        + ic * np.cos(2 * np.deg2rad(angles))
        + iss * np.sin(2 * np.deg2rad(angles))
        + i4c * np.cos(4 * np.deg2rad(angles))
        + i4s * np.sin(4 * np.deg2rad(angles))
    )
    tolerance = 1e-9 * max(summary["Imax"], np.finfo(float).tiny)
    return dict(
        maxima_deg=angles[np.abs(values - summary["Imax"]) < tolerance].tolist(),
        minima_deg=angles[np.abs(values - summary["Imin"]) < tolerance].tolist(),
        constant=False,
    )


def calculate_cubic_fig1(magnitude=1, plot_points=721):
    """Calculate all 18 cases through calculate_experiment, with one shared tensor scale."""
    runs = {protocol: [] for protocol in CUBIC_PANELS}
    for protocol in runs:
        for k in range(6):
            runs[protocol].append(
                calculate_experiment(cubic_fig1_config(k, protocol, magnitude, plot_points))
            )
    return dict(
        runs=runs,
        common_d=float(magnitude),
        source=CUBIC_SOURCE,
        surfaces=[(5, k, 0) for k in range(6)],
        scale_policy="One shared |d|^2 divisor; no per-curve normalization.",
        angles=runs["VV"][0]["angles"],
    )


def cubic_fig1_figure(study, individual=None):
    """Plot the computed arrays with the paper's angle sense, colors and common scale."""
    keys = [individual] if individual else list(CUBIC_PANELS)
    figure = plt.figure(figsize=(6.4, 5.9) if individual else (14, 5.1), layout="constrained")
    for i, key in enumerate(keys, 1):
        axes = figure.add_subplot(1, len(keys), i, projection="polar")
        for k, run in enumerate(study["runs"][key]):
            axes.plot(
                run["angles"],
                run["curves"]["T2g"] / study["common_d"] ** 2,
                color=CUBIC_COLORS[k],
                label=f"(5{k}0)",
                linewidth=1.8,
            )
        axes.set_theta_zero_location("E")
        axes.set_theta_direction(1)
        axes.set_ylim(0, {"VV": 1.5, "VH": 1.2, "SIGMA": 1.5}[key])
        axes.set_title(
            CUBIC_PANELS[key][3] + (" — θ" if key != "SIGMA" else " — α"), pad=21
        )
        axes.set_ylabel(r"$I/|d|^2$", labelpad=22)
        axes.grid(alpha=0.45)
        axes.legend(loc="upper left", bbox_to_anchor=(1.02, 1.1), fontsize=8, frameon=False)
    figure.suptitle("Si T2g — Cubic benchmark: calculated from rotated 3×3 tensors", fontsize=12)
    return figure


# The fixed benchmark and the general inspector share the same detailed trace.
def cubic_steps_markdown(run):
    displayed = attach_display_channels(copy.deepcopy(run))
    return detailed_calculation(displayed)["markdown"]


cubic_fig1_figure = publication_cubic_figure

print("Cell 14/22 — Run completed successfully.\nReady: The six-surface silicon benchmark and its reference checks are ready.\nNext: Run Cell 15.", flush=True)


# %% Code cell 15: OriginLab handoff
"""OriginLab handoff for the computed Fig. 1 arrays, without recalculating curves."""

ORIGIN_FIG1_SCRIPT = r'''"""Run inside Origin's Python Console with originpro available.

The CSV arrays were calculated by ROTATION RAMAN TENSOR CALCULATION.
This script creates native Origin polar graphs from those arrays and saves
an OPJU project. It does not replace the physics calculation or clear the
current Origin session. Use a blank project for a clean Fig. 1 deliverable.
"""
import csv
from pathlib import Path
import originpro as op

COLORS = ["#ff0000", "#ff8c00", "#20a928", "#1685c4", "#9362cf", "#916252"]
PANELS = [
    ("Fig1a_VV.csv", "Fig. 1(a) VV", "θ", 1.5),
    ("Fig1b_VH.csv", "Fig. 1(b) VH", "θ", 1.2),
    ("Fig1c_sigma_plus_alpha.csv", "Fig. 1(c) σ⁺α", "α", 1.5),
]


def build_origin_fig1(data_directory=None):
    """Create three six-surface θ(X)-radius(Y) plots with shared intensity units."""
    folder = Path(data_directory) if data_directory else Path(__file__).resolve().parent
    for filename, title, angle_name, radial_limit in PANELS:
        with (folder / filename).open(newline="", encoding="utf-8") as source:
            rows = list(csv.reader(source))
        if len(rows) < 362 or len(rows[0]) != 7:
            raise ValueError("Expected one degree-angle column and six surface-intensity columns.")
        columns = list(zip(*[[float(value) for value in row] for row in rows[1:]]))
        if abs(columns[0][0]) > 1e-10 or abs(columns[0][-1] - 360) > 1e-10:
            raise ValueError("The angular column must run from 0 to 360 degrees.")
        sheet = op.new_sheet("w", lname=title + " - Si T2g input data")
        sheet.cols = 7
        sheet.from_list(0, list(columns[0]), lname=angle_name, units="degree", axis="X")
        for column in range(1, 7):
            sheet.from_list(column, list(columns[column]), lname="(5" + str(column-1) + "0)",
                            units="I/|d|^2", axis="Y",
                            comments="One common d scale; no per-curve normalization.")
        graph = op.new_graph(lname=title + " - six surface orientations", template="polar")
        layer = graph[0]
        for column, color in enumerate(COLORS, 1):
            plot = layer.add_plot(sheet, coly=column, colx=0, type=192)
            plot.color = color
        layer.rescale()
        layer.set_xlim(0, 360, 45)
        layer.set_ylim(0, radial_limit, 0.25 if radial_limit == 1.5 else 0.2)
        graph.lt_exec("legend -r;")
    output = folder / "Cubic_Fig1_Origin.opju"
    suffix = 2
    while output.exists():
        output = folder / ("Cubic_Fig1_Origin_" + str(suffix) + ".opju")
        suffix += 1
    op.save(str(output))
    if not output.exists():
        raise RuntimeError("Origin did not create the requested project file; check write permissions.")
    print("Created Fig. 1(a), 1(b), 1(c) native Origin polar graphs:", output)
    return output


if __name__ == "__main__":
    build_origin_fig1()
'''

CUBIC_ORIGIN_README = r"""# Cubic benchmark: Python calculation and OriginLab plotting

The attached program computes Si T2g response for (500), (510), (520),
(530), (540), (550) using J. Raman Spectrosc. 57,
809-820 (2026), DOI 10.1002/jrs.70113, Eqs. 1-11.

## Make the graphs in OriginLab

1. Extract this entire ZIP into one writable folder. Keep the CSVs and
   plot_in_origin.py together. Open a blank Origin project.
2. In Origin's Python Console, run the following using your extracted path:

   import runpy
   runpy.run_path(r"C:\YourFolder\plot_in_origin.py", run_name="__main__")

3. The script imports each seven-column CSV, designates column A as X
   (degrees), B:G as Y (intensity), creates the native POLAR template with
   plot type 192, and colors the six surfaces red through brown.
   It saves Cubic_Fig1_Origin.opju in that folder, with a numeric suffix
   if that filename already exists. Existing Origin windows are not cleared.
4. Verify the angular axis: zero at the right, 90 at the top, positive
   counterclockwise, 0-360 degrees. Use the same radius scale for all six
   curves within each panel. Export the three Origin graphs;
   merge them into a single figure in Origin if desired.

If automated plotting is unavailable in your Origin version, import each
CSV manually, set A=X and B:G=Y, select all seven columns and choose
Polar θ(X) r(Y). X is already in degrees; do not convert to radians.
Select the six line colors in the order of the column labels.

## Files and angular meanings

- Fig1a_VV.csv: theta_deg and six complete Si intensities divided by |d|².
- Fig1b_VH.csv: theta_deg and six complete Si intensities divided by |d|².
- Fig1c_sigma_plus_alpha.csv: alpha_deg and six intensities divided by |d|².
- intensity_raw_long.csv: unnormalized and common-scaled intensities together.
- extrema.csv: continuous-angle maxima/minima and all equivalent angles.
- matrices_and_inputs.json: all inputs, original tensors, rotated tensors,
  amplitudes, and Eq. 8 phonon-basis tensors.
- calculation_steps.md: the actual matrix calculation for all 18 cases.
- paper_reading_notes.md: full-main-paper reading record and scope.
- validation.json: numerical benchmark checks.
- previews/: Matplotlib previews, explicitly not native Origin output.

One common d is used across every surface and protocol. None of these
curves is normalized to its own maximum. For d=1, the common-scaled and
raw intensities are identical. A polar radius represents intensity, not
the square root of intensity.

The limiting checks are VV maximum 1 at (500) and 4/3 at (550), VH
maximum 1 for all surfaces, and σ⁺α maximum at 90 degrees for
(500), tilting to 103.2825255885 degrees for (550).

## What has been run

The Python tensor calculations, analytic checks, CSV round trips and
Matplotlib previews were executed. The Origin script is syntax checked
and uses the official documented API. OriginLab is not installed in the
calculation environment, so native Origin execution and creation of an
OPJU file occur when you run the script inside your local Origin session.
No provided PNG is claimed to be exported by Origin.

OriginLab references:
https://docs.originlab.com/origin-help/polar-graph/
https://docs.originlab.com/x-function/ref/plotxy/
https://docs.originlab.com/originpro/classoriginpro_1_1graph_1_1GLayer.html
https://docs.originlab.com/originpro/classoriginpro_1_1worksheet_1_1WSheet.html
https://docs.originlab.com/originpro/namespaceoriginpro_1_1project.html
"""


def cubic_summary_markdown(study):
    """Summarize measured-from-model extrema without individual curve normalization."""
    lines = [
        "## Cubic benchmark: Si T2g, six (5,k,0) surfaces",
        "All 18 curves are calculated from three rotated 3×3 tensors using Eq. 9 and Eq. 11. VV/VH scan θ; σ⁺α scans α. One common |d|² scale is retained.",
        "| Surface | VV maximum / |d|² | VH maximum / |d|² | σ⁺α maximum angle (degrees, 0..180) | σ⁺α maximum / |d|² |",
        "|---|---:|---:|---:|---:|",
    ]
    for k in range(6):
        vv = study["runs"]["VV"][k]["summaries"]["T2g"]
        vh = study["runs"]["VH"][k]["summaries"]["T2g"]
        sigma = study["runs"]["SIGMA"][k]["summaries"]["T2g"]
        lines.append(
            f"| (5{k}0) | {vv['Imax']/study['common_d']**2:.9g} | {vh['Imax']/study['common_d']**2:.9g} | {sigma['alpha_max']:.9f} | {sigma['Imax']/study['common_d']**2:.9g} |"
        )
    return "\n\n".join(lines[:2]) + "\n\n" + "\n".join(lines[2:])


def make_cubic_origin_archive(study, validation=None):
    """Package the actual computed data and an Origin-native plotting script."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_OriginLab.md", CUBIC_ORIGIN_README)
        archive.writestr("plot_in_origin.py", ORIGIN_FIG1_SCRIPT)
        archive.writestr("paper_reading_notes.md", CUBIC_READING_NOTES)
        archive.writestr("summary.md", cubic_summary_markdown(study))
        archive.writestr(
            "validation.json",
            json.dumps(
                serializable(validation or {"status": "not run"}), indent=2, allow_nan=False
            ),
        )
        raw = io.StringIO()
        raw_writer = csv.writer(raw)
        raw_writer.writerow(
            [
                "protocol",
                "surface",
                "scan_angle_deg",
                "intensity_raw",
                "intensity_over_common_d_squared",
            ]
        )
        extrema = io.StringIO()
        extrema_writer = csv.writer(extrema)
        extrema_writer.writerow(
            [
                "protocol",
                "surface",
                "Imin_raw",
                "Imax_raw",
                "all_maximum_angles_deg",
                "all_minimum_angles_deg",
            ]
        )
        matrices = {}
        steps = []
        for protocol, (_, filename, angle_name, _) in CUBIC_PANELS.items():
            table = io.StringIO()
            writer = csv.writer(table)
            writer.writerow([angle_name] + [f"I_(5{k}0)" for k in range(6)])
            curves = [
                run["curves"]["T2g"] / study["common_d"] ** 2 for run in study["runs"][protocol]
            ]
            writer.writerows(zip(np.rad2deg(study["angles"]), *curves))
            archive.writestr(filename, table.getvalue())
            for k, run in enumerate(study["runs"][protocol]):
                surface = f"(5{k}0)"
                raw_writer.writerows(
                    (
                        protocol,
                        surface,
                        float(angle),
                        float(value),
                        float(value / study["common_d"] ** 2),
                    )
                    for angle, value in zip(np.rad2deg(study["angles"]), run["curves"]["T2g"])
                )
                summary = run["summaries"]["T2g"]
                angles = cubic_all_extrema(summary)
                extrema_writer.writerow(
                    [
                        protocol,
                        surface,
                        summary["Imin"],
                        summary["Imax"],
                        json.dumps(angles["maxima_deg"]),
                        json.dumps(angles["minima_deg"]),
                    ]
                )
                matrices[protocol + surface] = dict(
                    inputs=run["config"],
                    T=run["geometry"]["T"],
                    terms=run["results"]["T2g"]["terms"],
                    phonon_basis_tensors_eq8=cubic_projected_partners(run),
                    summary=summary,
                )
                steps.append(cubic_steps_markdown(run))
        archive.writestr("intensity_raw_long.csv", raw.getvalue())
        archive.writestr("extrema.csv", extrema.getvalue())
        archive.writestr(
            "matrices_and_inputs.json",
            json.dumps(serializable(matrices), indent=2, allow_nan=False),
        )
        archive.writestr("calculation_steps.md", "\n\n---\n\n".join(steps))
        for protocol in [None, *CUBIC_PANELS]:
            figure = cubic_fig1_figure(study, protocol)
            for extension in ["pdf", "svg", "png"]:
                image_buffer = io.BytesIO()
                figure.savefig(image_buffer, format=extension, dpi=600, bbox_inches="tight")
                archive.writestr(
                    "previews/" + (protocol or "Fig1_all") + "." + extension,
                    image_buffer.getvalue(),
                )
            plt.close(figure)
    return buffer.getvalue()

print("Cell 15/22 — Run completed successfully.\nReady: OriginLab data-export and plotting-script functions are ready.\nNext: Run Cell 16.", flush=True)


# %% Code cell 16: Data, LaTeX and figure export
"""Reproducible ZIP export with explicit inputs and no dependence on widget globals."""


def make_archive(run, figures, report, comparisons=(), comparison_plot=None, validation=None):
    """Serialize the exact active calculation and optional frozen comparisons.

    This function accepts all state as arguments. A later UI selection cannot
    silently change the data associated with an earlier exported calculation.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:

        def write_json(name, value):
            """Write readable UTF-8 JSON with explicit SymPy/complex conversion."""
            archive.writestr(
                name, json.dumps(serializable(value), indent=2, ensure_ascii=False, allow_nan=False)
            )

        write_json("inputs.json", run["config"])
        write_json("summary.json", run["summaries"])
        write_json("assumptions.json", run["assumptions"])
        write_json(
            "calculation_policy.json",
            dict(
                calculation_method=run["config"]["calculation_method"],
                tensor_model=run["config"]["tensor_model"],
                ag_rule=run["config"]["ag_rule"],
                optics=run["config"]["optics"],
                mode_rules={name: item["rule"] for name, item in run["results"].items()},
                exact_component_reference=component_reference_matches(run),
                description=run_description(run),
                scan_label=run["scan_label"],
                scan_kind=run["scan_kind"],
                circular_basis="Fixed laboratory XY; propagation-relative helicity requires the beam-frame convention",
            ),
        )
        write_json(
            "calculated_matrices.json",
            {
                name: {
                    "terms": result["terms"],
                    "coefficient_values": run["families"][name]["values"],
                }
                for name, result in run["results"].items()
            },
        )
        if "circular" in run:
            write_json("circular_selection_diagnostics.json", run["circular"])
        if run["config"]["calculation_method"] in ["CIRCULAR", "LINEAR"]:
            write_json("paper_sources.json", PAPER_SOURCES)
        archive.writestr("paper_reading_notes.md", PAPER_NOTES)
        archive.writestr("paper_equation_map.md", PAPER_EQUATION_MAP)
        archive.writestr("physics_checks.md", physics_audit_markdown(run))
        write_json("polarization_states.json", run["physics"]["optical_states"])
        write_json("tensor_library.json", POINT_GROUPS)
        write_json("material_presets.json", MATERIALS)
        write_json("sources.json", SOURCES)
        if run["config"]["calculation_method"] == "QWP":
            write_json("qwp_source.json", QWP_SOURCE)
        write_json("validation.json", validation or {"status": "not run in this session"})
        write_json(
            "software.json",
            {
                "version": AUDIT_VERSION,
                "intensity_origin": "matrix amplitudes; no target-curve fitting",
            },
        )
        archive.writestr("calculation_steps.md", report)
        table = io.StringIO()
        writer = csv.writer(table)
        names = list(run["curves"])
        angle_name = "theta_deg" if run["optical"].get("scan_basis") == "SECOND" else "alpha_deg"
        writer.writerow([angle_name] + names)
        writer.writerows(zip(np.rad2deg(run["angles"]), *[run["curves"][name] for name in names]))
        archive.writestr("intensity_raw.csv", table.getvalue())
        table = io.StringIO()
        writer = csv.writer(table)
        writer.writerow(["mode", "component_or_partner", angle_name, "intensity"])
        for name, curves in run["component_curves"].items():
            for label, curve in zip(run["families"][name]["calculation_labels"], curves):
                writer.writerows(
                    (name, label, float(angle), float(value))
                    for angle, value in zip(np.rad2deg(run["angles"]), curve)
                )
        archive.writestr("component_intensities.csv", table.getvalue())
        table = io.StringIO()
        writer = csv.writer(table)
        writer.writerow(
            [
                "mode",
                angle_name,
                "entry_self_power",
                "within_mode_interference",
                "complete_coherent_intensity",
                "selected_intensity",
            ]
        )
        for name, item in run["physics"]["interference"].items():
            writer.writerows(
                zip(
                    [name] * len(run["angles"]),
                    np.rad2deg(run["angles"]),
                    item["entry_self_power"],
                    item["interference"],
                    item["coherent_intensity"],
                    item["selected_intensity"],
                )
            )
        archive.writestr("coherence_audit.csv", table.getvalue())
        write_json(
            "physics_audit_summary.json",
            dict(
                uses_coherent_intensity=run["physics"]["uses_coherent_intensity"],
                validation_scope=run["physics"]["validation_scope"],
                modes={
                    name: dict(
                        relative_difference_from_selected=item["relative_difference_from_selected"],
                        selected_is_component_prescription=item[
                            "selected_is_component_prescription"
                        ],
                        interpretation=item["interpretation"],
                    )
                    for name, item in run["physics"]["interference"].items()
                },
            ),
        )
        for name, figure in figures:
            for format_name in ["png", "svg"]:
                image_buffer = io.BytesIO()
                figure.savefig(image_buffer, format=format_name, bbox_inches="tight", dpi=150)
                archive.writestr(name + "." + format_name, image_buffer.getvalue())
        write_json("comparison_inputs.json", [saved_run["config"] for saved_run in comparisons])
        table = io.StringIO()
        writer = csv.writer(table)
        writer.writerow(
            [
                "case",
                "case_label",
                "method",
                "optics",
                "scan",
                "material",
                "point_group",
                "mode",
                "scan_angle_deg",
                "intensity",
            ]
        )
        for index, saved_run in enumerate(comparisons, 1):
            config = saved_run["config"]
            for name, curve in saved_run["curves"].items():
                writer.writerows(
                    (
                        index,
                        config.get("case_label", ""),
                        config["calculation_method"],
                        config["optics"],
                        saved_run["scan_kind"],
                        config["material"],
                        config["point_group"],
                        name,
                        float(angle),
                        float(value),
                    )
                    for angle, value in zip(np.rad2deg(saved_run["angles"]), curve)
                )
        archive.writestr("comparison_raw.csv", table.getvalue())
        if comparison_plot is not None:
            image_buffer = io.BytesIO()
            comparison_plot.savefig(image_buffer, format="png", bbox_inches="tight", dpi=150)
            archive.writestr("comparison.png", image_buffer.getvalue())
    return buffer.getvalue()


"""Separate main component data, complete-mode audits, LaTeX and styled figures."""

UPGRADE_SOURCES = {
    "tensor_and_complex_response": "https://doi.org/10.1039/D1CP03626B",
    "circular_selection_scope": "https://doi.org/10.1039/D1CP02209A",
    "cubic_reference_geometry_and_states": "https://doi.org/10.1002/jrs.70113",
    "matplotlib_style": "https://matplotlib.org/stable/users/explain/customizing.html",
    "matplotlib_polar_axes": "https://matplotlib.org/stable/gallery/pie_and_polar_charts/polar_demo.html",
}


def csv_from_curves(angles, curves, angle_name):
    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow([angle_name, *curves])
    writer.writerows(zip(np.rad2deg(angles), *curves.values()))
    return text.getvalue()


def make_general_archive(run, figures, derivation, validation=None, comparisons=()):
    """Save exactly the displayed components plus separately named audit quantities."""
    buffer = io.BytesIO()
    tex = paper_intensity_latex(run, derivation)
    angle_name = "theta_deg" if run["optical"]["scan_basis"] == "SECOND" else "alpha_deg"
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:

        def js(name, value):
            archive.writestr(
                name, json.dumps(serializable(value), indent=2, ensure_ascii=False, allow_nan=False)
            )

        js("inputs.json", run["config"])
        js("display_policy.json", run["presentation_policy"])
        js("display_harmonics_and_extrema.json", run["display_summaries"])
        js("complete_modes_audit_harmonics.json", run["summaries"])
        js("validation.json", validation or {"status": "not run"})
        js("identical_state_representation_checks.json", matching_protocol_audit(run))
        js("different_protocol_state_checks.json", protocol_state_comparison())
        js("plot_style_status.json", run["style"])
        js("sources.json", UPGRADE_SOURCES)
        js(
            "calculated_matrices.json",
            {
                name: dict(
                    records=item["records"], coefficient_values=item["values"], kind=item["kind"]
                )
                for name, item in run["display_channels"].items()
            },
        )
        js("complete_mode_physics_audit.json", run["physics"])
        procedures = run.get("checking_procedures") or checking_procedures_for_run(run)
        js("checking_procedures.json", procedures)
        js("optical_method_guide.json", dict(profile=optical_method_catalog()[run["config"]["optics"]], effective_parameters=run["optical"]["parameters"]))
        archive.writestr("optical_method_guide.md", optical_method_markdown(run["config"]["optics"]) + "\n\n" + optical_methods_overview_markdown())
        archive.writestr("checking_procedures.md", checking_report_markdown(procedures))
        if validation and validation.get("optical_reference"):
            js("optical_reference_validation.json", validation["optical_reference"])
            archive.writestr(
                "optical_reference_validation.md", checking_report_markdown(validation["optical_reference"])
            )
        js("mathematical_steps.json", derivation["entries"])
        js("derivation_references.json", DERIVATION_REFERENCES)
        archive.writestr("symbols_and_references.md", symbols_and_references_markdown())
        archive.writestr(
            "intensity_raw.csv", csv_from_curves(run["angles"], run["display_curves"], angle_name)
        )
        archive.writestr(
            "complete_modes_audit.csv", csv_from_curves(run["angles"], run["curves"], angle_name)
        )
        archive.writestr("calculation_steps.md", derivation["markdown"])
        archive.writestr("calculation_mathematics.md", derivation["mathematics_markdown"])
        archive.writestr("calculation_explained.md", derivation["explained_markdown"])
        js("symbol_legend.json", derivation["symbol_legend"])
        archive.writestr("intensity_symbolic.tex", tex["symbolic"])
        archive.writestr("intensity_numerical.tex", tex["numerical"])
        archive.writestr("calculation_full.tex", tex["full"])
        archive.writestr("calculation_explained.tex", tex["explained"])
        archive.writestr("sci.mplstyle", SCI_STYLE_TEXT)
        archive.writestr(
            "README.txt",
            "ROTATION RAMAN TENSOR CALCULATION — VERSION 4\n\n"
            "intensity_raw.csv contains the actual plotted channels. Ag(xx), Ag(yy), Ag(zz) are separate Cartesian contributions, not independent phonon modes. They are not summed in this file or in the main plots.\n"
            "complete_modes_audit.csv retains the coherent complete-mode result for interference checks. Off-diagonal components of lower-symmetry Ag tensors are also retained.\n"
            "intensity_symbolic.tex contains I(angle) before numerical coefficient substitution. intensity_numerical.tex is the distinct numerical version. calculation_full.tex and calculation_mathematics.md contain every mathematical step, followed by one short symbol list. calculation_explained.tex and calculation_explained.md contain the same equations with detailed definitions and sources below each equation. calculation_steps.md is the full-mathematics compatibility copy.\n"
            "Figures use the supplied sci.mplstyle: requested Arial, 22-point base font, 2-point lines, 600-dpi export and transparent background. plot_style_status.json records the actual local font. Install Arial for exact font matching when a fallback is reported.\n"
            "VV/VH scan θ; σ input / analyzer-state protocols scan α. The QWP, elliptical detector and direct linear analyzer are different optical states and are not forced to have equal curves.\n"
            "Material symmetry, tensor coefficients, lattice metric, surface and optical states all affect intensity. Example coefficients and unity metrics are illustrative.\n",
        )
        for name, figure in figures:
            for ext in ["pdf", "svg", "png"]:
                image_buffer = io.BytesIO()
                figure.savefig(
                    image_buffer, format=ext, dpi=600, bbox_inches="tight", transparent=True
                )
                archive.writestr("figures/" + name + "." + ext, image_buffer.getvalue())
        js("comparison_inputs.json", [r["config"] for r in comparisons])
        rows = io.StringIO()
        writer = csv.writer(rows)
        writer.writerow(["case", "channel", "protocol", "scan_angle_deg", "intensity"])
        for case, saved in enumerate(comparisons, 1):
            for name, curve in saved["display_curves"].items():
                writer.writerows(
                    (case, name, saved["config"]["optics"], float(angle), float(value))
                    for angle, value in zip(np.rad2deg(saved["angles"]), curve)
                )
        archive.writestr("comparison_components.csv", rows.getvalue())
    return buffer.getvalue()

print("Cell 16/22 — Run completed successfully.\nReady: Data, figures, annotated derivations and LaTeX export functions are ready.\nNext: Run Cell 17.", flush=True)


# %% Code cell 17: Application controls
"""Notebook inputs and result controls."""

import ipywidgets as widgets

STYLE = {"description_width": "initial"}


def dropdown(options, value, description):
    return widgets.Dropdown(
        options=options,
        value=value,
        description=description,
        style=STYLE,
        layout=widgets.Layout(width="800px", max_width="100%"),
    )


def number(value, label):
    return widgets.FloatText(
        value=float(value), description=label, style=STYLE, layout=widgets.Layout(width="280px")
    )


model_pick = dropdown(
    [
        ("General crystal calculation: full 3D tensor", "CRYSTAL_3D"),
        ("Original effective 2D optical reference", "QWP_SOURCE_2D"),
    ],
    "CRYSTAL_3D",
    "1.1 Tensor model",
)
optics_pick = dropdown(
    [(label, key) for key, label in GENERAL_PROFILES.items()], "CUBIC_VV", "1.2 Optical method"
)
example_pick = dropdown(
    [
        ("Slide-frame Ag(xx), Ag(yy), Ag(zz) on (211)", "SLIDE"),
        ("Full 3D CaNb2O6 (100), QWP optics", "QWP_3D"),
        ("Original complex 2D optical reference", "QWP_2D"),
        ("Complex linear BP reference", "LINEAR_BP"),
        ("Monolayer MoS2 circular-channel reference", "CIRCULAR_MOS2"),
        ("Silicon (500), VV startup example", "SI_500"),
        ("Silicon (530), VV reference frame", "SI_530"),
    ],
    "SI_500",
    "1.3 Example",
)
load_example_button = widgets.Button(
    description="1.4 Load selected example", layout=widgets.Layout(width="260px")
)
case_label = widgets.Text(
    value="Silicon (500), VV startup example",
    description="1.5 Case label",
    style=STYLE,
    layout=widgets.Layout(width="800px", max_width="100%"),
)
input_note = widgets.Textarea(
    value="",
    description="1.6 Input note",
    style=STYLE,
    layout=widgets.Layout(width="800px", height="58px", max_width="100%"),
)
material_pick = dropdown([(v["label"], k) for k, v in MATERIALS.items()], "Si", "2.1 Material")
group_pick = dropdown(
    [(k + " / " + v["symbol"], k) for k, v in POINT_GROUPS.items()]
    + [("Custom Cartesian 3x3 tensor", "CUSTOM")],
    "Oh",
    "2.2 Point group",
)
material_note = widgets.HTML()
mode_pick = widgets.SelectMultiple(
    description="2.3 Mode / branch", style=STYLE, layout=widgets.Layout(width="370px", height="110px")
)
coef_accordion = widgets.Accordion()
ag_relation = dropdown(
    [
        ("Independent a,b,c", "free"),
        ("a=b=c (copy a)", "equal"),
        ("a=b (copy a)", "ab"),
        ("b=c (copy b)", "bc"),
        ("a=c (copy a)", "ac"),
    ],
    "free",
    "2.4 D2h Ag relation",
)
custom_tensor = widgets.Textarea(
    value='[["1","0","0"],["0","0.8","0"],["0","0","0.6"]]',
    description="2.6 Custom 3x3 tensor JSON",
    style=STYLE,
    layout=widgets.Layout(width="800px", height="85px", max_width="100%"),
)
coef_note = widgets.HTML(
    "Each branch has its own complex coefficients. Ag Cartesian contributions are plotted separately."
)
ag_locked = widgets.HTML()
surface_options = {**SURFACES, **{f"(5{k}0)": ((5, k, 0), (k, -5, 0)) for k in range(6)}}
surface_pick = dropdown(list(surface_options) + ["Custom hkl"], "(500)", "3.2 Surface preset")
hkl_fields = [
    widgets.IntText(value=v, description="3.3 " + k, layout=widgets.Layout(width="130px"))
    for k, v in zip("hkl", (5, 0, 0))
]
uvw_fields = [
    widgets.IntText(value=v, description="3.4 " + k, layout=widgets.Layout(width="130px"))
    for k, v in zip("uvw", (0, -5, 0))
]
auto_x = widgets.Checkbox(value=False, description="3.5 Automatic in-plane X reference")
normal_pick = dropdown([("+ reciprocal normal", 1), ("- reciprocal normal", -1)], 1, "3.6 Normal side")
psi = number(0, "3.7 Frame angle ψ (degree)")
lattice_fields = [
    number(v, k)
    for k, v in zip(
        [
            "3.8 a0",
            "3.8 b0",
            "3.8 c0",
            "3.9 Lattice α (degree)",
            "3.9 Lattice β (degree)",
            "3.9 Lattice γ (degree)",
        ],
        [1, 1, 1, 90, 90, 90],
    )
]
direct_widgets = {
    k: number(v, label)
    for k, v, label in [
        ("theta_i_deg", 45, "4.1 Input θᵢ (degree)"),
        ("beta_i_deg", 90, "4.2 Input βᵢ (degree)"),
        ("theta_s0_deg", 45, "4.3 Detector θₛ₀ (degree)"),
        ("beta_s_deg", 0, "4.4 Detector βₛ (degree)"),
    ]
}
direct_box = widgets.VBox(list(direct_widgets.values()))
theta_zero = number(0, "4.5 Linear scan zero (degree)")
analyzer_zero = number(45, "4.6 Direct analyzer zero (degree)")
source_widgets = {
    k: number(v, label)
    for k, v, label in [
        ("a", 1, "2.1 Real source a"),
        ("A", 0.4, "2.2 Real source A"),
        ("delta_deg", 60, "2.3 Source δ (degree)"),
        ("phi_deg", 60, "2.4 Source φ (degree)"),
    ]
}
source_box = widgets.VBox(
    [
        widgets.HTML("Original 2D source tensor; crystal orientation is inactive in this model."),
        widgets.HBox([source_widgets["a"], source_widgets["A"]]),
        widgets.HBox([source_widgets["delta_deg"], source_widgets["phi_deg"]]),
    ]
)
circular_spin = dropdown(
    [("σ⁺ (sᵢₙ=+1): (1,+i)/√2", 1), ("σ⁻ (sᵢₙ=−1): (1,−i)/√2", -1)], 1, "4.7 Circular basis label"
)
circular_N = dropdown([(str(v), v) for v in [2, 3, 4, 6]], 2, "4.8 Cyclic order N")
circular_ell = widgets.IntText(value=0, description="4.9 Incident OAM (rule only)", style=STYLE)
circular_charges = widgets.Text(
    value="0",
    description="4.10 Phonon charges (comma-separated)",
    style=STYLE,
    layout=widgets.Layout(width="700px", max_width="100%"),
)
circular_dm = widgets.Text(value="", description="4.11 Absorption charge (optional)", style=STYLE)
circular_scope = widgets.Checkbox(
    value=False,
    description="4.12 Declare the thin-2D / electronic-state assumptions for the separate rule check",
)
circular_controls = widgets.VBox(
    [circular_spin, circular_N, circular_ell, circular_charges, circular_dm, circular_scope]
)
optical_preview = widgets.Output()
optical_guide_out = widgets.Output()
normalize = widgets.Checkbox(
    value=False,
    description="5.2 Normalize with one common scale per mode, including its components and VV/VH pair",
)
cartesian_plots = widgets.Checkbox(
    value=False, description="5.3 Also generate Cartesian intensity-versus-angle plots"
)
show_geometry = widgets.Checkbox(value=True, description="5.4 Show the 3D measurement frame")
show_steps = widgets.Checkbox(value=True, description="5.5 Display all mathematical steps")
points = widgets.Dropdown(
    options=[("0.5 degree", 721), ("1 degree", 361), ("0.1 degree", 3601)],
    value=721,
    description="5.1 Angular grid",
    style=STYLE,
)
run_button = widgets.Button(
    description="6. CALCULATE ROTATION + RAMAN",
    button_style="success",
    icon="play",
    layout=widgets.Layout(width="360px"),
)
export_button = widgets.Button(
    description="7.1 Download data + LaTeX + figures",
    button_style="info",
    icon="download",
    disabled=True,
    layout=widgets.Layout(width="360px"),
)
latex_button = widgets.Button(
    description="7.2 Download symbolic I(angle).tex",
    disabled=True,
    layout=widgets.Layout(width="360px"),
)
validate_button = widgets.Button(description="8. Run validation", icon="check", layout=widgets.Layout(width="220px"))
compare_add = widgets.Button(description="9.1 Save current comparison", disabled=True, layout=widgets.Layout(width="250px"))
compare_clear = widgets.Button(description="9.2 Clear comparisons", layout=widgets.Layout(width="210px"))
compare_channel = dropdown([], None, "9.3 Comparison channel")
compare_normalized = widgets.Checkbox(
    value=True, description="9.4 Compare with a common per-mode normalization"
)
status = widgets.HTML()
style_note = widgets.HTML(
    "Style: supplied sci.mplstyle; requested font Arial; active local font "
    + html.escape(PLOT_STYLE_STATUS["actual_font"])
    + ". Export: PDF/SVG/PNG, 600 dpi."
)
(
    step_out,
    plot_out,
    table_out,
    geometry_out,
    physics_out,
    validation_out,
    latex_out,
    download_out,
    compare_out,
    library_out,
    sources_out,
) = [widgets.Output() for _ in range(11)]
explained_out = widgets.Output()
derivation_tabs = widgets.Tab(children=[step_out, explained_out])
derivation_tabs.set_title(0, "1. Full mathematics")
derivation_tabs.set_title(1, "2. Explained derivation")
derivation_tabs.selected_index = 0
cubic_out = widgets.Output()
cubic_d = number(1, "10.1 Shared |d|")
cubic_points = widgets.Dropdown(
    options=[("0.5 degree", 721), ("1 degree", 361), ("0.1 degree", 3601)],
    value=721,
    description="10.2 Angular grid",
    style=STYLE,
)
cubic_surface = dropdown([(f"(5{k}0)", k) for k in range(6)], 3, "10.5 Inspect surface")
cubic_protocol = dropdown(
    [("VV", "VV"), ("VH", "VH"), ("σ⁺α reference", "SIGMA")], "VV", "10.6 Inspect protocol"
)
cubic_button = widgets.Button(
    description="10.3 Calculate all 18 silicon cases",
    button_style="success",
    layout=widgets.Layout(width="360px"),
)
cubic_export = widgets.Button(
    description="10.4 Download silicon OriginLab ZIP",
    disabled=True,
    layout=widgets.Layout(width="360px"),
)
cubic_inspect = widgets.Button(
    description="10.7 Inspect selected mathematical steps",
    disabled=True,
    layout=widgets.Layout(width="360px"),
)
cubic_status = widgets.HTML()
cubic_panel = widgets.VBox(
    [
        widgets.HTML("Locked silicon T2g benchmark: (500), (510), (520), (530), (540), (550)."),
        widgets.HBox([cubic_d, cubic_points]),
        widgets.HBox([cubic_button, cubic_export]),
        cubic_surface,
        cubic_protocol,
        cubic_inspect,
        cubic_status,
        cubic_out,
    ]
)
tab_names = [
    "Mathematical derivation",
    "Polar plots",
    "Intensity values",
    "3D frame",
    "Protocol checks",
    "Validation",
    "LaTeX source",
    "Downloads",
    "Comparisons",
    "Tensor library",
    "Cubic benchmark",
    "Sources",
]
tab_index = {name: i for i, name in enumerate(tab_names)}
tabs = widgets.Tab(
    children=[
        derivation_tabs,
        plot_out,
        table_out,
        geometry_out,
        physics_out,
        validation_out,
        latex_out,
        download_out,
        compare_out,
        library_out,
        cubic_panel,
        sources_out,
    ]
)
for i, title in enumerate(tab_names):
    tabs.set_title(i, title)
state = dict(
    run=None,
    figures=[],
    derivation=None,
    report="",
    archive=None,
    validation=None,
    last_error=None,
    comparisons=[],
    comparison_figure=None,
    cubic_study=None,
    cubic_archive=None,
    cubic_validation=None,
)
ui = dict(busy=False, coefs={}, definitions={}, wired=False)

print("Cell 17/22 — Run completed successfully.\nReady: Numbered input widgets are ready. The initial material is Silicon, surface (500).\nNext: Run Cell 18.", flush=True)


# %% Code cell 18: Input handling
@contextmanager
def form_transaction():
    """Batch a preset update so observers do not interpret partial forms as active inputs."""
    previous = ui["busy"]
    ui["busy"] = True
    try:
        yield
    finally:
        ui["busy"] = previous


def synchronize_ag_relation(_=None):
    """Make selected equality constraints visible by copying and disabling dependent fields."""
    if ui["busy"]:
        return
    fields = ui["coefs"].get("Ag", {}) if group_pick.value == "D2h" else {}
    if not fields:
        return
    links = {"free": {}, "equal": {b: a, c: a}, "ab": {b: a}, "bc": {c: b}, "ac": {c: a}}[
        ag_relation.value
    ]
    with form_transaction():
        for symbol, pair in fields.items():
            for widget in pair:
                widget.disabled = symbol in links
        for destination, source in links.items():
            for target, origin in zip(fields[destination], fields[source]):
                target.value = origin.value


def on_coefficient_change(_=None):
    """Apply only the equality constraint explicitly selected by the user, then invalidate."""
    if ui["busy"]:
        return
    synchronize_ag_relation()
    invalidate()


def update_visible_modes(_=None):
    """Show coefficient panels for selected branches without changing any tensor coefficient."""
    # Close obsolete layout containers, but retain the numerical coefficient fields.
    for panel in coef_accordion.children:
        for child in panel.children:
            child.close()
        panel.close()
    panels, titles = [], []
    for name, fields in ui["coefs"].items():
        if name in mode_pick.value:
            header = widgets.HTML(
                "<b>" + html.escape(name) + "</b>: magnitude and phase in degrees"
            )
            panels.append(widgets.VBox([header] + [widgets.HBox(pair) for pair in fields.values()]))
            titles.append(name)
    coef_accordion.children = panels
    for index, title in enumerate(titles):
        coef_accordion.set_title(index, title)
    if panels:
        coef_accordion.selected_index = 0
    invalidate()


def populate_definitions():
    """Rebuild branch coefficient fields from the selected material/point-group templates."""
    for fields in ui["coefs"].values():
        for pair in fields.values():
            for widget in pair:
                widget.close()
    definitions = definitions_for(material_pick.value, group_pick.value)
    ui["definitions"], ui["coefs"] = definitions, {}
    for name, item in definitions.items():
        fields = {
            symbol: (
                number(DEFAULT_VALUES[symbol], f"2.5 |{symbol}|"),
                number(0, f"2.5 Phase {symbol} (°)"),
            )
            for symbol in parameters_for(item)
        }
        ui["coefs"][name] = fields
        for pair in fields.values():
            for widget in pair:
                widget.observe(on_coefficient_change, names="value")
    mode_pick.options = list(definitions)
    mode_pick.value = tuple(definitions)
    ag_relation.layout.display = "" if group_pick.value == "D2h" and "Ag" in ui["coefs"] else "none"
    custom_tensor.layout.display = "" if group_pick.value == "CUSTOM" else "none"
    update_visible_modes()
    with library_out:
        clear_output()
        axes = (
            POINT_GROUPS[group_pick.value]["axes"]
            if group_pick.value in POINT_GROUPS
            else "User-defined Cartesian tensor axes"
        )
        display(Markdown("**" + group_pick.value + "** — " + axes))
        for name, item in definitions.items():
            display(
                Markdown(
                    f"**{name}** ({item['irrep']}), {len(item['partners']) or 1} tensor(s)/partner(s)"
                )
            )
            for tensor in item["partners"]:
                display(Math(raman_latex(tensor)))


"""Input transactions keep the crystal, geometry and optical protocol explicit."""


def clear_result():
    for _, figure in state["figures"]:
        plt.close(figure)
    state.update(run=None, figures=[], derivation=None, report="", archive=None)
    export_button.disabled = latex_button.disabled = compare_add.disabled = True
    for output in [
        step_out,
        explained_out,
        plot_out,
        table_out,
        geometry_out,
        physics_out,
        latex_out,
        download_out,
    ]:
        output.clear_output(wait=False)


def invalidate(_=None):
    if ui["busy"]:
        return
    if state["run"] is not None:
        clear_result()
    status.value = "<b>Inputs changed.</b> Calculate again. Saved comparisons retain their inputs."


def lattice_template(group):
    system = POINT_GROUPS.get(group, {}).get("system", "triclinic")
    return (1, 1, 1, 90, 90, 120) if system in ["trigonal", "hexagonal"] else (1, 1, 1, 90, 90, 90)


def load_material_fields():
    information = MATERIALS[material_pick.value]
    previous_group = group_pick.value
    if material_pick.value != "GENERAL":
        group_pick.value = information["group"]
    group_pick.disabled = material_pick.value != "GENERAL"
    metric = (
        information["lattice"]
        if material_pick.value != "GENERAL"
        else lattice_template(group_pick.value)
    )
    for field, value in zip(lattice_fields, metric):
        field.value = value
    ag_relation.value = "free"
    populate_definitions()
    material_note.value = (
        "<b>"
        + html.escape(information["space_group"])
        + "</b><br>"
        + html.escape(information["note"])
    )


def on_material(_=None):
    if ui["busy"]:
        return
    # A material change updates its tensor forms and conventional lattice only.
    # It preserves hkl, uvw, normal, frame angle and the optical protocol.
    with form_transaction():
        load_material_fields()
        case_label.value = str(material_pick.value) + " / selected surface and optical states"
        input_note.value = "Illustrative tensor coefficients and lattice ratios; replace with sample-specific inputs."
    synchronize_ag_relation()
    invalidate()


def on_group(_=None):
    if ui["busy"]:
        return
    with form_transaction():
        for field, value in zip(lattice_fields, lattice_template(group_pick.value)):
            field.value = value
        ag_relation.value = "free"
        populate_definitions()
    invalidate()


def on_surface(_=None):
    if ui["busy"]:
        return
    if surface_pick.value in surface_options:
        indices, direction = surface_options[surface_pick.value]
        with form_transaction():
            for field, value in zip(hkl_fields, indices):
                field.value = value
            for field, value in zip(uvw_fields, direction):
                field.value = value
    invalidate()


def on_manual_indices(_=None):
    if ui["busy"]:
        return
    actual = tuple(field.value for field in hkl_fields)
    preset = surface_options.get(surface_pick.value)
    if preset and actual != preset[0]:
        with form_transaction():
            surface_pick.value = "Custom hkl"
    invalidate()


def on_auto_x(_=None):
    for field in uvw_fields:
        field.disabled = auto_x.value
    invalidate()


def collect_paper_parameters():
    # Inactive circular-rule fields must not block other optical protocols.
    if not optics_pick.value.startswith("CIRCULAR_"):
        return {**default_paper_parameters("CIRCULAR"),
                "theta0_deg": exact(theta_zero.value),
                "analyzer_zero_deg": exact(analyzer_zero.value)}
    charges = [
        circular_integer(x.strip(), "Phonon charge")
        for x in circular_charges.value.split(",")
        if x.strip()
    ]
    if not charges:
        raise ValueError("Enter at least one integer phonon charge for the separate rule example.")
    dm = circular_dm.value.strip()
    return dict(
        s_in=circular_spin.value,
        N=circular_N.value,
        ell_i=circular_ell.value,
        m_ph=charges,
        absorption_delta_m=circular_integer(dm, "Absorption charge") if dm else None,
        thin_2d_assumptions=bool(circular_scope.value),
        theta0_deg=exact(theta_zero.value),
        analyzer_zero_deg=exact(analyzer_zero.value),
    )


def on_optics(_=None):
    if ui["busy"]:
        return
    kind = optics_pick.value
    direct_box.layout.display = "" if kind == "DIRECT_JONES" else "none"
    theta_zero.layout.display = "" if kind in ["CUBIC_VV", "CUBIC_VH", "LINEAR_PAIR"] else "none"
    analyzer_zero.layout.display = "" if kind == "CIRCULAR_LINEAR" else "none"
    circular_controls.layout.display = "" if kind.startswith("CIRCULAR_") else "none"
    with optical_preview:
        clear_output()
        try:
            direct = {k: exact(v.value) for k, v in direct_widgets.items()}
            optical = optical_chain(
                kind,
                direct,
                dict(
                    s_in=circular_spin.value,
                    theta0_deg=exact(theta_zero.value),
                    analyzer_zero_deg=exact(analyzer_zero.value),
                ),
            )
            variable = theta_scan if optical["scan_basis"] == "SECOND" else alpha
            display(Math(r"E_i=" + raman_latex(optical["Ein"].subs(alpha, variable))))
            display(
                Math(
                    r"e_s=B^\dagger e_{an}="
                    + raman_latex(optical["effective_analyzer"].subs(alpha, variable))
                )
            )
            display(Markdown("Scan basis: **" + optical["scan_basis"] + "**."))
        except Exception as exception:
            print(str(exception))
    with optical_guide_out:
        clear_output()
        display(Markdown(optical_method_markdown(kind)))
    invalidate()


def update_model_visibility():
    original = model_pick.value == "QWP_SOURCE_2D"
    crystal_inputs.layout.display = "none" if original else ""
    orientation_inputs.layout.display = "none" if original else ""
    source_box.layout.display = "" if original else "none"
    optics_pick.disabled = original


def on_model(_=None):
    if ui["busy"]:
        return
    with form_transaction():
        if model_pick.value == "QWP_SOURCE_2D":
            ui["previous_crystal_optics"] = optics_pick.value
            optics_pick.value = "QWP"
        else:
            optics_pick.value = ui.get("previous_crystal_optics", "CUBIC_SIGMA")
    update_model_visibility()
    on_optics()


def load_configuration(cfg):
    """Load explicit visible values; changing a report label never changes optics."""
    with form_transaction():
        model_pick.value = cfg["tensor_model"]
        optics_pick.value = cfg["optics"]
        case_label.value = cfg["case_label"]
        input_note.value = cfg.get("input_note", "")
        if cfg["tensor_model"] == "QWP_SOURCE_2D":
            for key, value in cfg["source_parameters"].items():
                source_widgets[key].value = float(value)
        else:
            material_pick.value = cfg["material"]
            if cfg["material"] == "GENERAL":
                group_pick.value = cfg["point_group"]
            load_material_fields()
            for field, value in zip(lattice_fields, cfg["lattice"]):
                field.value = float(value)
            for field, value in zip(hkl_fields, cfg["hkl"]):
                field.value = int(value)
            auto_x.value = cfg["uvw"] is None
            if cfg["uvw"] is not None:
                for field, value in zip(uvw_fields, cfg["uvw"]):
                    field.value = int(value)
            normal_pick.value = cfg["normal_sign"]
            psi.value = float(cfg["azimuth_deg"])
            matching = [
                key for key, (hkl, _) in surface_options.items() if tuple(hkl) == tuple(cfg["hkl"])
            ]
            surface_pick.value = matching[0] if matching else "Custom hkl"
            mode_pick.value = tuple(cfg["modes"])
            for name, values in cfg["mode_values"].items():
                for symbol, value in values.items():
                    if symbol not in ui["coefs"].get(name, {}):
                        continue
                    magnitude, phase = ui["coefs"][name][symbol]
                    magnitude.value = float(sp.N(sp.Abs(value)))
                    phase.value = float(sp.N(sp.arg(value) * 180 / sp.pi)) if value != 0 else 0
            if cfg.get("custom_tensor") is not None:
                custom_tensor.value = json.dumps(
                    [
                        [str(complex(sp.N(x))) for x in row]
                        for row in sp.Matrix(cfg["custom_tensor"]).tolist()
                    ]
                )
            ui["previous_crystal_optics"] = cfg["optics"]
        parameters = cfg.get("paper_parameters") or {}
        circular_spin.value = parameters.get("s_in", 1)
        circular_N.value = parameters.get("N", 2)
        circular_ell.value = parameters.get("ell_i", 0)
        circular_charges.value = ",".join(str(x) for x in parameters.get("m_ph", [0]))
        circular_dm.value = (
            ""
            if parameters.get("absorption_delta_m") is None
            else str(parameters["absorption_delta_m"])
        )
        circular_scope.value = parameters.get("thin_2d_assumptions", False)
        theta_zero.value = float(parameters.get("theta0_deg", 0))
        analyzer_zero.value = float(
            parameters.get("analyzer_zero_deg", 0 if cfg["optics"].startswith("CIRCULAR_") else 45)
        )
        for key, value in (cfg.get("direct_jones") or {}).items():
            direct_widgets[key].value = float(value)
        normalize.value = bool(cfg.get("normalize", False))
        cartesian_plots.value = bool(cfg.get("cartesian_plots", False))
        points.value = cfg.get("plot_points", 721)
    update_visible_modes()
    for field in uvw_fields:
        field.disabled = auto_x.value
    update_model_visibility()
    on_optics()
    invalidate()


def on_load_example(_=None):
    name = example_pick.value
    if name == "SLIDE":
        cfg = slide_component_config()
    elif name == "QWP_3D":
        cfg = physical_start_config()
    elif name == "QWP_2D":
        cfg = qwp_source_config()
    elif name == "LINEAR_BP":
        cfg = linear_bp_reference_config()
    elif name == "CIRCULAR_MOS2":
        cfg = circular_mos2_reference_config()
    elif name == "SI_500":
        cfg = cubic_fig1_config(0, "VV")
    else:
        cfg = cubic_fig1_config(3, "VV")
    load_configuration(cfg)
    status.value = "<b>Example loaded.</b> Review the visible inputs, then calculate."

print("Cell 18/22 — Run completed successfully.\nReady: Input handlers are ready. Enter your own values in the interface in Cell 22.\nNext: Run Cell 19.", flush=True)


# %% Code cell 19: Calculation actions
"""Calculate once, then inspect the same matrices, components, LaTeX and plots."""


def collect_config():
    if model_pick.value == "QWP_SOURCE_2D":
        cfg = qwp_source_config()
        cfg.update(source_parameters={k: exact(w.value) for k, w in source_widgets.items()})
    else:
        cfg = general_config(material_pick.value, optics_pick.value)
        values = {
            name: {
                symbol: complex_parameter(pair[0].value, pair[1].value)
                for symbol, pair in ui["coefs"][name].items()
            }
            for name in mode_pick.value
        }
        tensor = None
        if group_pick.value == "CUSTOM":
            entries = json.loads(custom_tensor.value)
            if len(entries) != 3 or any(len(row) != 3 for row in entries):
                raise ValueError("The custom tensor requires exactly 3 rows and 3 columns.")
            tensor = sp.Matrix([[parse_complex(value) for value in row] for row in entries])
        cfg.update(
            point_group=group_pick.value,
            modes=list(mode_pick.value),
            mode_values=values,
            custom_tensor=tensor,
            lattice=tuple(exact(w.value) for w in lattice_fields),
            hkl=tuple(w.value for w in hkl_fields),
            uvw=None if auto_x.value else tuple(w.value for w in uvw_fields),
            normal_sign=normal_pick.value,
            azimuth_deg=exact(psi.value),
            paper_parameters=collect_paper_parameters(),
            direct_jones={key: exact(field.value) for key, field in direct_widgets.items()},
        )
    cfg.update(
        case_label=case_label.value,
        input_note=input_note.value,
        plot_points=points.value,
        normalize=normalize.value,
        cartesian_plots=cartesian_plots.value,
        show_steps=show_steps.value,
        show_geometry=show_geometry.value,
    )
    return cfg


def report_error(exception):
    state["last_error"] = dict(
        type=type(exception).__name__, message=str(exception), traceback=traceback.format_exc()
    )
    status.value = "<b>Calculation error:</b> " + html.escape(str(exception))


def result_table_markdown(run):
    lines = ["| Channel | Imin | Imax | Maximum angle (degree) |", "|---|---:|---:|---:|"]
    for name, item in run["display_channels"].items():
        s = item["summary"]
        angle = "constant / zero" if s["alpha_max"] is None else f"{s['alpha_max']:.8g}"
        lines.append(f"| {name} | {s['Imin']:.10g} | {s['Imax']:.10g} | {angle} |")
    lines += [
        "",
        "| Angle (degree) | " + " | ".join(run["display_curves"]) + " |",
        "|---:|" + ":---:|" * len(run["display_curves"]),
    ]
    for degree in range(0, 361, 15):
        index = int(np.argmin(np.abs(np.rad2deg(run["angles"]) - degree)))
        lines.append(
            "| "
            + str(degree)
            + " | "
            + " | ".join(f"{curve[index]:.8g}" for curve in run["display_curves"].values())
            + " |"
        )
    return "\n".join(lines)


def protocol_check_markdown(run):
    lines = [
        "### Identical physical inputs, independent representations",
        "| Channel | Direct contraction error | Circular-basis error |",
        "|---|---:|---:|",
    ]
    for row in matching_protocol_audit(run):
        lines.append(
            f"| {row['channel']} | {row['direct_error']:.3g} | {row['circular_error']:.3g} |"
        )
    lines += [
        "",
        "### Different detection-state scans",
        "The table compares pure-state projectors at 0, 45, 90 and 135 degrees. Zero means the same detection state up to global phase.",
        "| Protocols | Projector distances | Identical scans |",
        "|---|---|---|",
    ]
    for row in protocol_state_comparison():
        lines.append(
            "| "
            + row["first"]
            + " / "
            + row["second"]
            + " | "
            + ", ".join(f"{x:.5g}" for x in row["projector_distances"])
            + " | "
            + str(row["same_states"])
            + " |"
        )
    lines += [
        "",
        "### Complete-mode coherence audit",
        "Complete-mode intensities remain in the audit record; Ag component powers are separate in the main plots.",
    ]
    for name, item in run["physics"]["interference"].items():
        lines.append(
            "**"
            + name
            + "**: maximum within-mode cross term = "
            + f"{np.max(np.abs(item['interference'])):.9g}"
            + "."
        )
    if "circular" in run:
        lines += ["", run["circular"]["scope"]]
    return "\n".join(lines)


def on_run(_=None):
    if ui["busy"]:
        return
    clear_result()
    state["last_error"] = None
    status.value = "<b>Calculating...</b>"
    try:
        run = calculate_general(collect_config())
        run["checking_procedures"] = checking_procedures_for_run(run)
        derivation = detailed_calculation(run)
        figures = publication_figures(run)
        if run["config"].get("show_geometry"):
            frame = publication_orientation(run)
            if frame is not None:
                figures.append(("measurement_frame", frame))
        state.update(run=run, figures=figures, derivation=derivation, report=derivation["markdown"])
        for output, key in [(step_out, "mathematics_markdown"), (explained_out, "explained_markdown")]:
            with output:
                if run["config"].get("show_steps", True):
                    display(Markdown(derivation[key]))
                else:
                    display(Markdown("Both derivation views are included in the download. Enable the display option to show them here."))
        with plot_out:
            for name, figure in figures:
                if name != "measurement_frame":
                    display(figure)
        with geometry_out:
            for name, figure in figures:
                if name == "measurement_frame":
                    display(figure)
        with table_out:
            display(Markdown(result_table_markdown(run)))
        with physics_out:
            display(Markdown(checking_report_markdown(run["checking_procedures"])))
            display(Markdown(protocol_check_markdown(run)))
        with latex_out:
            source = paper_intensity_latex(run, derivation)["symbolic"]
            display(Markdown("**Symbolic intensity before numerical coefficient substitution.**"))
            display(
                widgets.Textarea(value=source, layout=widgets.Layout(width="100%", height="330px"))
            )
            display(latex_button)
        for _, figure in figures:
            plt.close(figure)
        export_button.disabled = latex_button.disabled = compare_add.disabled = False
        status.value = (
            "<b>Calculation complete.</b> "
            + str(len(run["display_channels"]))
            + " plotted channels; "
            + str(sum(x["kind"] == "equation" for x in derivation["entries"]))
            + " equations. See the result tabs below."
        )
    except Exception as exception:
        clear_result()
        report_error(exception)


def download_link(data, filename, mime="application/zip"):
    encoded = base64.b64encode(data).decode("ascii")
    return HTML(
        '<a download="'
        + html.escape(filename, quote=True)
        + '" href="data:'
        + mime
        + ";base64,"
        + encoded
        + '">Download '
        + html.escape(filename)
        + "</a>"
    )


def on_export(_=None):
    if state["run"] is None:
        return
    try:
        data = make_general_archive(
            state["run"],
            state["figures"],
            state["derivation"],
            state["validation"],
            state["comparisons"],
        )
        state["archive"] = data
        with download_out:
            clear_output()
            display(download_link(data, "Rotation_Raman_Result.zip"))
        tabs.selected_index = tab_index["Downloads"]
    except Exception as exception:
        report_error(exception)


def on_latex(_=None):
    if state["run"] is None:
        return
    data = paper_intensity_latex(state["run"], state["derivation"])["symbolic"].encode("utf-8")
    with download_out:
        clear_output()
        display(download_link(data, "intensity_symbolic.tex", "text/plain"))
    tabs.selected_index = tab_index["Downloads"]


def on_validate(_=None):
    with validation_out:
        clear_output()
        try:
            checks = run_self_checks() + validate_general_upgrade() + validate_optical_method_guide()
            source_report = validate_optical_reference()
            check(source_report["status"] == "passed", "QWP source reference checks failed.")
            checks.append(
                f"QWP source reference: {source_report['passed']}/{source_report['total']} checking procedures pass."
            )
            state["validation"] = dict(
                status="passed", software_version=AUDIT_VERSION, checks=checks, optical_reference=source_report
            )
            for line in checks:
                print("PASS:", line)
            display(Markdown(checking_report_markdown(source_report)))
            print(
                "These tests validate the implemented model and algebra. Sample-specific coefficients and omitted propagation effects require separate input."
            )
        except Exception as exception:
            state["validation"] = dict(status="failed", error=str(exception))
            report_error(exception)
            raise


def render_comparison(_=None):
    with compare_out:
        clear_output()
        if state["comparison_figure"] is not None:
            plt.close(state["comparison_figure"])
        if not state["comparisons"] or compare_channel.value is None:
            return
        try:
            figure = publication_comparison(
                state["comparisons"], compare_channel.value, compare_normalized.value
            )
            state["comparison_figure"] = figure
            display(figure)
            plt.close(figure)
            display(
                Markdown(
                    "\n".join(
                        f"{i}. {r['config']['case_label']}; {r['config']['optics']}"
                        for i, r in enumerate(state["comparisons"], 1)
                    )
                )
            )
        except ValueError as exception:
            print(str(exception))


def add_comparison(_=None):
    if state["run"] is None:
        return
    state["comparisons"].append(copy.deepcopy(state["run"]))
    options = list(
        dict.fromkeys(name for run in state["comparisons"] for name in run["display_channels"])
    )
    selected = compare_channel.value
    compare_channel.options = options
    compare_channel.value = selected if selected in options else options[0]
    render_comparison()


def clear_comparison(_=None):
    state["comparisons"] = []
    if state["comparison_figure"] is not None:
        plt.close(state["comparison_figure"])
    state["comparison_figure"] = None
    compare_channel.options = []
    compare_out.clear_output()


def invalidate_cubic(_=None):
    state.update(cubic_study=None, cubic_archive=None, cubic_validation=None)
    cubic_export.disabled = cubic_inspect.disabled = True
    cubic_out.clear_output()
    cubic_status.value = "Benchmark inputs changed. Calculate again."


def on_cubic_run(_=None):
    try:
        study = calculate_cubic_fig1(cubic_d.value, cubic_points.value)
        messages = validate_cubic_fig1(study)
        state.update(
            cubic_study=study,
            cubic_archive=None,
            cubic_validation=dict(status="passed", checks=messages),
        )
        with cubic_out:
            clear_output()
            display(Markdown(cubic_summary_markdown(study)))
            figure = publication_cubic_figure(study)
            display(figure)
            plt.close(figure)
        cubic_export.disabled = cubic_inspect.disabled = False
        cubic_status.value = "<b>18 cases calculated and independently checked.</b>"
    except Exception as exception:
        report_error(exception)


def on_cubic_inspect(_=None):
    if state["cubic_study"] is None:
        return
    cfg = copy.deepcopy(
        state["cubic_study"]["runs"][cubic_protocol.value][cubic_surface.value]["config"]
    )
    load_configuration(cfg)
    on_run()
    tabs.selected_index = tab_index["Mathematical derivation"]


def on_cubic_export(_=None):
    if state["cubic_study"] is None:
        return
    try:
        data = make_cubic_origin_archive(state["cubic_study"], state["cubic_validation"])
        state["cubic_archive"] = data
        with download_out:
            clear_output()
            display(download_link(data, "Cubic_Fig1_OriginLab.zip"))
        tabs.selected_index = tab_index["Downloads"]
    except Exception as exception:
        report_error(exception)

print("Cell 19/22 — Run completed successfully.\nReady: Calculate, inspect, compare and download actions are ready for Cell 22.\nNext: Run Cell 20.", flush=True)


# %% Code cell 20: Core validation
def generator_matrices(group):
    """Return point-group generators in the same Cartesian convention as the library."""
    Rz = lambda t: sp.Matrix([[sp.cos(t), -sp.sin(t), 0], [sp.sin(t), sp.cos(t), 0], [0, 0, 1]])
    inv = -sp.eye(3)
    c2x = sp.diag(1, -1, -1)
    c2y = sp.diag(-1, 1, -1)
    mxz = sp.diag(1, -1, 1)
    myz = sp.diag(-1, 1, 1)
    mh = sp.diag(1, 1, -1)
    c3 = Rz(2 * sp.pi / 3)
    c4 = Rz(sp.pi / 2)
    c6 = Rz(sp.pi / 3)
    cycle = sp.Matrix([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
    return {
        "C1": [],
        "Ci": [inv],
        "C2": [c2y],
        "Cs": [mxz],
        "C2h": [c2y, inv],
        "D2": [c2x, c2y],
        "C2v": [mxz, myz],
        "D2h": [c2x, c2y, inv],
        "D3": [c3, c2x],
        "C3v": [c3, myz],
        "D3d": [c3, c2x, inv],
        "D4": [c4, c2x],
        "C4v": [c4, mxz],
        "D2d": [c4 * mh, c2x],
        "D4h": [c4, c2x, inv],
        "D6": [c6, c2x],
        "C6v": [c6, mxz],
        "D6h": [c6, c2x, inv],
        "D3h": [c3, c2x, mh],
        "Td": [cycle, c4 * mh],
        "Oh": [cycle, c4, inv],
    }[group]


def validate_tensor_library():
    """Check completeness, covariance and selected irrep characters, not just matrix shape."""
    check(len(POINT_GROUPS) == 21, "The advertised point-group count is incorrect.")
    trial = {
        a: 1 + sp.I / 5,
        b: sp.Rational(4, 5) - sp.I / 7,
        c: sp.Rational(3, 5) + sp.I / 8,
        d: sp.Rational(2, 5) - sp.I / 9,
        e: sp.Rational(3, 10) + sp.I / 11,
        f: sp.Rational(1, 5) - sp.I / 13,
    }
    expected = {
        ("C2", "A"): [1],
        ("C2", "B"): [-1],
        ("Cs", "A'"): [1],
        ("Cs", "A''"): [-1],
        ("C2h", "Ag"): [1, 1],
        ("C2h", "Bg"): [-1, 1],
        ("C2v", "A1"): [1, 1],
        ("C2v", "A2"): [-1, -1],
        ("C2v", "B1"): [1, -1],
        ("C2v", "B2"): [-1, 1],
        ("D2h", "Ag"): [1, 1, 1],
        ("D2h", "B1g"): [-1, -1, 1],
        ("D2h", "B2g"): [-1, 1, 1],
        ("D2h", "B3g"): [1, -1, 1],
        ("D3", "E"): [-1, 0],
        ("C3v", "E"): [-1, 0],
        ("D3d", "Eg"): [-1, 0, 2],
        ("D4h", "B1g"): [-1, 1, 1],
        ("D4h", "B2g"): [-1, -1, 1],
        ("D4h", "Eg"): [0, 0, 2],
        ("D6h", "E1g"): [1, 0, 2],
        ("D6h", "E2g"): [-1, 0, 2],
        ("D3h", "E'"): [-1, 0, 2],
        ("D3h", "E''"): [-1, 0, -2],
        ("Oh", "Eg"): [-1, 0, 2],
        ("Oh", "T2g"): [0, -1, 3],
        ("Td", "E"): [-1, 0],
        ("Td", "T2"): [0, -1],
    }
    covariance_count = 0
    character_count = 0
    for group_name, group in POINT_GROUPS.items():
        symmetric_basis = []
        for irrep, family_data in group["tensors"].items():
            tensors = family_data["partners"]
            for tensor in tensors:
                check(
                    tensor.shape == (3, 3) and tensor == tensor.T,
                    f"{group_name}/{irrep}: invalid symmetric tensor.",
                )
                symmetric_basis.extend(
                    np.array(tensor.diff(symbol), dtype=complex).reshape(9)
                    for symbol in tensor.free_symbols
                )
            partners = np.column_stack(
                [numeric(tensor.subs(trial)).reshape(9) for tensor in tensors]
            )
            for index, generator in enumerate(generator_matrices(group_name)):
                matrix = numeric(generator)
                transformed = np.column_stack(
                    [
                        (matrix @ numeric(tensor.subs(trial)) @ matrix.T).reshape(9)
                        for tensor in tensors
                    ]
                )
                representation = np.linalg.lstsq(partners, transformed, rcond=None)[0]
                check(
                    np.allclose(partners @ representation, transformed, atol=1e-10),
                    f"{group_name}/{irrep}: covariance failed.",
                )
                check(
                    np.allclose(
                        representation.conj().T @ representation, np.eye(len(tensors)), atol=1e-10
                    ),
                    f"{group_name}/{irrep}: partner norm is inconsistent.",
                )
                if (group_name, irrep) in expected:
                    check(
                        np.isclose(
                            np.trace(representation), expected[group_name, irrep][index], atol=1e-10
                        ),
                        f"{group_name}/{irrep}: character label check failed.",
                    )
                    character_count += 1
                covariance_count += 1
        check(
            np.linalg.matrix_rank(np.column_stack(symmetric_basis), tol=1e-9) == 6,
            f"{group_name}: incomplete symmetric tensor basis.",
        )
    return f"21 point groups: six-dimensional symmetric basis, {covariance_count} covariance checks and {character_count} irrep-character checks."


def validate_qwp_method():
    """Compare the optical chain with the explicit matrices/formula in the uploaded source."""
    expected = sp.Matrix([[1 + sp.I, -1 + sp.I], [-1 + sp.I, 1 + sp.I]]) / 2
    check(zero(QWP_QWP - expected), "The Quarter-wave-plate QWP differs from the source matrix.")
    check(zero(QWP_QWP.H * QWP_QWP - sp.eye(2)), "The Quarter-wave-plate QWP must be unitary.")
    check(
        zero(QWP_RETURN_QWP - QWP_QWP.T),
        "The adopted Quarter-wave-plate return matrix must be Q.T.",
    )
    check(
        zero(QWP_QWP * x_hat - ((1 + sp.I) / sp.sqrt(2)) * sig_p),
        "The Quarter-wave-plate incident circular state is incorrect.",
    )
    optical = optical_chain("QWP")
    angles = np.array([0, 0.19, 0.73, 1.6, 3.4, 5.8])
    for amplitude, off_diagonal, phase_delta, phase_phi in [
        (1, 0.4, 0.7, 1.1),
        (0.6, 0.2, -0.9, 0),
        (1.3, 0.7, 2.1, -1.2),
    ]:
        # Embed the source 2×2 effective tensor only for this algebraic regression test.
        # This is not a material preset or a proposed CaNb2O6 crystal tensor.
        matrix = np.array(
            [
                [amplitude, off_diagonal * np.exp(1j * phase_delta)],
                [-off_diagonal * np.exp(1j * phase_delta), amplitude * np.exp(1j * phase_phi)],
            ]
        )
        crystal = np.zeros((3, 3), complex)
        crystal[:2, :2] = matrix
        record = amplitude_record(sp.Matrix(crystal), sp.eye(3), optical)
        r_pp = amplitude * (1 + np.exp(1j * phase_phi)) / 2 + 1j * off_diagonal * np.exp(
            1j * phase_delta
        )
        r_mp = amplitude * (1 - np.exp(1j * phase_phi)) / 2
        reference = np.abs(-r_pp * np.cos(angles) - 1j * r_mp * np.sin(angles)) ** 2
        check(
            np.allclose(numeric_curve(dict(terms=[record]), {}, angles), reference, atol=1e-11),
            "The Quarter-wave-plate source intensity regression failed.",
        )
    return "Quarter-wave-plate source: Q, Q.T, incident σ⁺, analyzer reference and complex-tensor intensity match the uploaded notebook."


def validate_method_separation():
    """Prove that source, 3D Quarter-wave-plate and REFERENCE cannot exchange calculation policies."""
    original_config = qwp_source_config()
    original = calculate_experiment(original_config)
    record = original["results"][QWP_MODE]["terms"][0]
    check(
        original["geometry"] is None and "Rc" not in record,
        "The source model was silently embedded in a 3D crystal.",
    )
    check(original["config"]["material"] is None, "The source model was assigned a material.")
    check(
        "hkl" not in original["config"],
        "Inactive source orientation was exported as an active input.",
    )
    algebra = qwp_source_algebra()
    check(
        zero(
            [
                algebra["record"]["amplitude"]
                + algebra["Rpp"] * sp.cos(alpha)
                + sp.I * algebra["Rmp"] * sp.sin(alpha)
            ]
        ),
        "The source amplitude differs from the Quarter-wave-plate circular-basis derivation.",
    )
    check(
        sp.simplify(algebra["p2"] / algebra["p1"]) == sp.I,
        "The Quarter-wave-plate return phase ratio is incorrect.",
    )
    for amplitude, off_diagonal, delta_deg, phi_deg in [
        (1, 0.4, 60, 60),
        (1, 0.4, 60, 0),
        (1, 0, 0, 180),
        (0.7, 0, 37, 45),
        (-0.9, 0.3, -60, 135),
    ]:
        config = qwp_source_config()
        config["source_parameters"] = dict(
            a=amplitude, A=off_diagonal, delta_deg=delta_deg, phi_deg=phi_deg
        )
        run = calculate_experiment(config)
        radians_delta, radians_phi = np.deg2rad([delta_deg, phi_deg])
        rpp = amplitude * (1 + np.exp(1j * radians_phi)) / 2 + 1j * off_diagonal * np.exp(
            1j * radians_delta
        )
        rmp = amplitude * (1 - np.exp(1j * radians_phi)) / 2
        expected = np.abs(rpp * np.cos(run["angles"]) + 1j * rmp * np.sin(run["angles"])) ** 2
        check(
            np.allclose(run["curves"][QWP_MODE], expected, atol=1e-11),
            "The pure Quarter-wave-plate source curve fails a source/special-case comparison.",
        )

    component_config = component_reference_config()
    ref_config = copy.deepcopy(component_config)
    ref_config.update(calculation_method="QWP", optics="QWP", ag_rule="COHERENT_SINGLE_TENSOR")
    component_run, ref_run = calculate_experiment(component_config), calculate_experiment(
        ref_config
    )
    check(
        len(component_run["results"]["Ag"]["terms"]) == 3,
        "REFERENCE Ag lost its three prescribed components.",
    )
    check(
        len(ref_run["results"]["Ag"]["terms"]) == 1,
        "The Quarter-wave-plate Ag tensor was split by a REFERENCE rule.",
    )
    check(
        ref_run["results"]["Ag"]["rule"] == "SINGLE_TENSOR",
        "The Quarter-wave-plate mode is not coherent.",
    )
    check(
        component_reference_matches(component_run) and not component_reference_matches(ref_run),
        "component reference reporting leaked into Quarter-wave-plate.",
    )
    for run in [component_run, ref_run]:
        frame = numeric(run["geometry"]["T"])
        optical = run["optical"]
        input_field = numeric(optical["Ein"]).reshape(2)
        backward = numeric(optical["B"])
        projection = np.array([[1, 0, 0], [0, 1, 0]])
        complete = np.diag([1, 0.8, 0.6])
        tensors = (
            [complete]
            if run["config"]["calculation_method"] == "QWP"
            else [np.diag(row) for row in np.diag([1, 0.8, 0.6])]
        )
        expected = []
        for angle in run["angles"]:
            detector = numeric(optical["analyzer"].subs(alpha, angle)).reshape(2)
            expected.append(
                sum(
                    abs(
                        np.vdot(
                            detector,
                            backward
                            @ projection
                            @ frame.T
                            @ tensor
                            @ frame
                            @ projection.T
                            @ input_field,
                        )
                    )
                    ** 2
                    for tensor in tensors
                )
            )
        check(
            np.allclose(run["curves"]["Ag"], expected, atol=1e-11),
            "A workflow curve differs from its independent matrix contraction.",
        )
    # Relative component phases change coherent Ag interference, but not the REFERENCE sum.
    changed = []
    for config in [ref_config, component_config]:
        shifted = copy.deepcopy(config)
        shifted["mode_values"]["Ag"][b] *= -1
        changed.append(calculate_experiment(shifted))
    check(
        not np.allclose(changed[0]["curves"]["Ag"], ref_run["curves"]["Ag"]),
        "Coherent Quarter-wave-plate Ag interference was lost.",
    )
    check(
        np.allclose(changed[1]["curves"]["Ag"], component_run["curves"]["Ag"]),
        "REFERENCE component phases incorrectly interfere.",
    )
    for method_config, wrong_key, wrong_value in [
        (ref_config, "ag_rule", "REFERENCE_AG_COMPONENT_SUM"),
        (component_config, "optics", "QWP"),
        (original_config, "optics", "COMPONENT_SIGMA_ALPHA"),
    ]:
        invalid = copy.deepcopy(method_config)
        invalid[wrong_key] = wrong_value
        try:
            calculate_experiment(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "A hybrid Quarter-wave-plate/REFERENCE configuration was accepted."
            )
    # The pure source route must not call either crystal or REFERENCE processing.
    forbidden_names = [
        "build_orientation",
        "experiment_families",
        "component_ag_symbolics",
        "component_ag_flow_markdown",
    ]
    saved = {name: globals()[name] for name in forbidden_names}

    def forbidden_call(*args, **kwargs):
        """Detect a foreign calculation/report path during the source-only check."""
        raise AssertionError("The Quarter-wave-plate source called crystal/REFERENCE processing.")

    try:
        for name in forbidden_names:
            globals()[name] = forbidden_call
        source_run = calculate_experiment(original_config)
        source_report = steps_markdown(source_run)
        check(
            "### 13." in source_report,
            "The thirteen-step Quarter-wave-plate source report is incomplete.",
        )
    finally:
        globals().update(saved)
    return "Method separation: original Quarter-wave-plate source and special cases, coherent 3D Ag, unchanged REFERENCE Ag sum, phase-interference distinction, rejected hybrids and isolated source/report paths pass."


def validate_full_3d_chain():
    """Use a direct NumPy 3D contraction independently of the reduced tensor calculation."""
    random = np.random.default_rng(1203)
    count = 0
    for hkl, uvw in [((0, 0, 1), (1, 0, 0)), ((1, 1, 0), (0, 0, 1)), ((2, 1, 1), (0, 1, -1))]:
        config = dict(
            lattice=(3, 4, 5, 90, 90, 90),
            orientation="hkl",
            hkl=hkl,
            uvw=uvw,
            normal_sign=1,
            azimuth_deg=17,
        )
        geometry = build_orientation(config)
        frame = geometry["T"]
        frame_array = numeric(frame)
        check(
            np.isclose(np.linalg.det(frame_array), 1), "The surface frame is not a proper rotation."
        )
        crystal = random.normal(size=(3, 3)) + 1j * random.normal(size=(3, 3))
        for kind in ["QWP", "DIRECT_JONES", "COMPONENT_SIGMA_ALPHA"]:
            optical = optical_chain(
                kind, dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=12, beta_s_deg=0)
            )
            record = amplitude_record(sp.Matrix(crystal), frame, optical)
            for angle in [0, 0.32, 1.3, 2.61, 5.7]:
                analyzer = numeric(optical["analyzer"].subs(alpha, angle)).reshape(2)
                incident = numeric(optical["Ein"]).reshape(2)
                return_matrix = numeric(optical["B"])
                projection = np.array([[1, 0, 0], [0, 1, 0]])
                direct = (
                    abs(
                        np.vdot(
                            projection.T @ return_matrix.conj().T @ analyzer,
                            frame_array.T @ crystal @ frame_array @ projection.T @ incident,
                        )
                    )
                    ** 2
                )
                calculated = numeric_curve(dict(terms=[record]), {}, np.array([angle]))[0]
                check(
                    np.isclose(calculated, direct, rtol=1e-10, atol=1e-10),
                    "The projected and full 3D calculations disagree.",
                )
                count += 1
        # A complete isotropic coherent tensor is frame-invariant. This test is
        # deliberately not applied to the separate user Ag component-sum model.
        check(
            np.allclose(frame_array.T @ np.eye(3) @ frame_array, np.eye(3), atol=1e-10),
            "Isotropic tensor rotation invariance failed.",
        )
    return f"{count} full 3D complex-tensor contractions match the Jones engine; proper-frame and isotropic tensor invariants pass."


def validate_component_reference():
    """Check both the general REFERENCE formula and the supplied slide-14 specialization."""
    frame = build_orientation(COMPONENT_REFERENCE_GEOMETRY)["T"]
    angles = np.array([0, 0.17, 0.73, 1.53, 2.87, 4.11, 6.2])
    theta = np.deg2rad(23)
    beta = np.deg2rad(57)
    beta_prime = np.deg2rad(-37)
    optical = optical_chain(
        "DIRECT_JONES", dict(theta_i_deg=23, beta_i_deg=57, theta_s0_deg=23, beta_s_deg=-37)
    )
    tensors = [sp.diag(a, 0, 0), sp.diag(0, b, 0), sp.diag(0, 0, c)]
    records = [amplitude_record(tensor, frame, optical) for tensor in tensors]
    factor = (
        lambda angle, phase, sign: 5 / 12
        + np.cos(2 * angle) / 12
        + sign * np.sin(2 * angle) * np.cos(phase) / np.sqrt(6)
    )
    reference = (
        (1 - np.cos(2 * theta)) * (1 - np.cos(2 * (theta + angles))) / 36
        + 0.8**2 * factor(theta, beta, -1) * factor(theta + angles, beta_prime, -1)
        + 0.6**2 * factor(theta, beta, 1) * factor(theta + angles, beta_prime, 1)
    )
    calculated = numeric_curve(dict(terms=records), {a: 1, b: 0.8, c: 0.6}, angles)
    check(
        np.allclose(calculated, reference, atol=1e-11),
        "The general REFERENCE component formula does not match the rotated tensors.",
    )
    records = [
        amplitude_record(tensor, frame, optical_chain("COMPONENT_SIGMA_ALPHA"))
        for tensor in tensors
    ]
    for av, bv, cv in [(1, 0.8, 0.6), (1, 1, 1), (0.7, 1, 0.4), (1, 0.8, 0.8), (1, 1, 0.6)]:
        calculated = numeric_curve(dict(terms=records), {a: av, b: bv, c: cv}, angles)
        reference = (
            4 * av**2
            + 25 * bv**2
            + 25 * cv**2
            + (4 * av**2 - 5 * bv**2 - 5 * cv**2) * np.sin(2 * angles)
        ) / 144
        check(
            np.allclose(calculated, reference, atol=1e-11),
            "The slide-14 REFERENCE specialization failed.",
        )
    data = component_ag_symbolics()
    check(
        data["denominator"] == 144,
        "The denominator derived from the reference matrices should be 144.",
    )
    check(
        sp.expand(data["expanded"] - data["general"]) == 0,
        "The REFERENCE symbolic expansion is not an identity.",
    )
    # Prove that reference reporting cannot supply or overwrite the production curve.
    original = globals()["component_ag_symbolics"]

    def forbidden_reference_call():
        """Fail if a target-reference function is used to generate a production curve."""
        raise AssertionError("The production engine called the component reference formula.")

    try:
        globals()["component_ag_symbolics"] = forbidden_reference_call
        run = calculate_experiment(component_reference_config())
    finally:
        globals()["component_ag_symbolics"] = original
    check(
        np.isclose(run["summaries"]["Ag"]["I0"], 29 / 144),
        "The default REFERENCE matrix intensity is incorrect.",
    )
    check(
        np.isclose(run["summaries"]["Ag"]["Is"], -1 / 144),
        "The default REFERENCE angular coefficient is incorrect.",
    )
    return "REFERENCE slides 12–14: general β,β′ formula, five special coefficient cases and independently derived denominator agree; the production engine does not call the reference formula."


def validate_degeneracy_and_limits():
    """Check unresolved-partner sums and geometry-specific selection rules."""
    random = np.random.default_rng(72)
    angles = np.linspace(0, 2 * np.pi, 73)
    direct = optical_chain(
        "DIRECT_JONES", dict(theta_i_deg=45, beta_i_deg=90, theta_s0_deg=45, beta_s_deg=0)
    )
    for group, mode in [("D3d", "Eg"), ("D6h", "E2g"), ("Oh", "T2g")]:
        tensors = [
            tensor.subs({a: 1, b: 0.8, c: 0.6 + sp.I / 8, d: 0.4 - sp.I / 9, e: 0.3, f: 0.2})
            for tensor in POINT_GROUPS[group]["tensors"][mode]["partners"]
        ]
        mixing, _ = np.linalg.qr(random.normal(size=(len(tensors), len(tensors))))
        mixed = [
            sum((sp.Float(mixing[j, k]) * tensors[k] for k in range(len(tensors))), sp.zeros(3))
            for j in range(len(tensors))
        ]
        first = numeric_curve(
            dict(terms=[amplitude_record(tensor, sp.eye(3), direct) for tensor in tensors]),
            {},
            angles,
        )
        second = numeric_curve(
            dict(terms=[amplitude_record(tensor, sp.eye(3), direct) for tensor in mixed]),
            {},
            angles,
        )
        check(
            np.allclose(first, second, atol=1e-10),
            f"{group}/{mode}: the unresolved partner sum depends on the partner basis.",
        )
    silicon = lambda optical: dict(
        terms=[amplitude_record(tensor, sp.eye(3), optical) for tensor in CUBIC_T]
    )
    check(
        np.allclose(numeric_curve(silicon(direct), {d: 1}, angles), 0.5),
        "Si (001) circular-input/direct-linear result should be constant 1/2 for d=1.",
    )
    check(
        np.allclose(
            numeric_curve(silicon(optical_chain("QWP")), {d: 1}, angles), np.sin(angles) ** 2
        ),
        "Si (001) under the Quarter-wave-plate sequence should give sin²(α) for d=1.",
    )
    e1 = dict(
        terms=[
            amplitude_record(tensor, sp.eye(3), direct)
            for tensor in POINT_GROUPS["D6h"]["tensors"]["E1g"]["partners"]
        ]
    )
    check(
        np.allclose(numeric_curve(e1, {c: 1}, angles), 0),
        "Basal normal-backscattering E1g extinction failed.",
    )
    return "Degenerate partner-basis invariance, Si optical-profile limits and basal D6h E1g extinction pass."


def validate_input_and_numerics():
    """Exercise zero signals, overflow handling, input immutability and invalid geometry."""
    config = component_reference_config()
    before = serializable(config)
    run = calculate_experiment(config)
    check(serializable(config) == before, "Calculation mutated the caller configuration.")
    config["mode_values"]["Ag"] = {a: 0, b: 0, c: 0}
    zero_run = calculate_experiment(config)
    check(
        np.all(zero_run["curves"]["Ag"] == 0) and zero_run["summaries"]["Ag"]["alpha_max"] is None,
        "Zero-signal handling failed.",
    )
    invalid = component_reference_config()
    invalid["uvw"] = (1, 0, 0)
    try:
        calculate_experiment(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("An in-plane direction outside the surface was accepted.")
    try:
        validate_frame(sp.diag(1, 1, -1))
    except ValueError:
        pass
    else:
        raise AssertionError("A reflected frame was accepted as a proper rotation.")
    try:
        summary_from_pairs(np.array([[1e200, 0]], complex))
    except ValueError:
        pass
    else:
        raise AssertionError("Overflow was not reported explicitly.")
    check(
        run["config"]["direct_jones"] is None,
        "Inactive direct Jones controls leaked into a fixed-profile configuration.",
    )
    check(
        run["config"]["effective_optical_parameters"]["beta_s_deg"] == 90,
        "The fixed REFERENCE profile does not export its actual β′.",
    )
    return "Zero/overflow handling, invalid geometry/reflection rejection, fixed-profile provenance and configuration immutability pass."


def run_self_checks():
    """Run independent algebra/numerical regressions without editing the user's active form."""
    return [
        validate_tensor_library(),
        validate_qwp_method(),
        validate_method_separation(),
        validate_full_3d_chain(),
        validate_component_reference(),
        validate_degeneracy_and_limits(),
        validate_input_and_numerics(),
        validate_linear_scans(),
        validate_triclinic_convention(),
        validate_circular_channels_and_rules(),
        validate_resonance_utility(),
        validate_polarization_and_interference(),
    ]

print("Cell 20/22 — Run completed successfully.\nReady: Core validation functions are ready; the tests execute in Cell 22 or with tool 8.\nNext: Run Cell 21.", flush=True)


# %% Code cell 21: General-model validation
"""Independent checks against the equations and scope of the two supplied papers."""


def validate_linear_scans():
    """Recover Eq. 13 and test general complex co-rotating scans directly."""
    run = calculate_experiment(linear_bp_reference_config())
    angles = run["angles"]
    cosine, sine = np.cos(angles), np.sin(angles)
    for name, ratio, phase_deg in [("Ag(1)", 1.96, 0), ("Ag(2)", 1.32, 94)]:
        phase = np.deg2rad(phase_deg)
        expected_parallel = (
            cosine**2 + ratio * np.cos(phase) * sine**2
        ) ** 2 + ratio**2 * sine**4 * np.sin(phase) ** 2
        expected_crossed = (
            ((1 - ratio * np.cos(phase)) ** 2 + ratio**2 * np.sin(phase) ** 2) * sine**2 * cosine**2
        )
        check(
            np.allclose(run["curves"][name + " [parallel]"], expected_parallel, atol=1e-10),
            "Complex linear model Eq. 13a failed.",
        )
        check(
            np.allclose(run["curves"][name + " [crossed]"], expected_crossed, atol=1e-10),
            "Complex linear model Eq. 13b failed.",
        )
    check(
        np.allclose(run["curves"]["B2g [parallel]"], (1.30 * np.sin(2 * angles)) ** 2, atol=1e-10),
        "Complex linear model Eq. 13c failed.",
    )
    check(
        np.allclose(run["curves"]["B2g [crossed]"], (1.30 * np.cos(2 * angles)) ** 2, atol=1e-10),
        "Complex linear model Eq. 13d failed.",
    )
    check(abs(run["summaries"]["B2g [parallel]"]["I4c"]) > 0.1, "The fourth harmonic was lost.")
    # Numerical full 3D contractions use independent vectors, not K0/Kc/Ks.
    rng = np.random.default_rng(20261018)
    crystal = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
    crystal = (crystal + crystal.T) / 2
    frame = build_orientation(dict(COMPONENT_REFERENCE_GEOMETRY, azimuth_deg=17))["T"]
    frame_n = numeric(frame)
    for kind in ["LINEAR_PARALLEL", "LINEAR_CROSSED"]:
        optical = optical_chain(kind, paper=dict(theta0_deg=13))
        record = amplitude_record(sp.Matrix(crystal), frame, optical)
        sample = np.linspace(0, 2 * np.pi, 41)
        measured = []
        for angle in sample:
            ei = np.array([np.cos(angle + np.deg2rad(13)), np.sin(angle + np.deg2rad(13)), 0])
            es = ei if kind == "LINEAR_PARALLEL" else np.array([-ei[1], ei[0], 0])
            measured.append(abs(np.vdot(es, frame_n.T @ crystal @ frame_n @ ei)) ** 2)
        result = dict(terms=[record])
        check(
            np.allclose(numeric_curve(result, {}, sample), measured, rtol=1e-10, atol=1e-10),
            "The co-rotating engine differs from direct 3D contraction.",
        )
        summary = numeric_summary(result, {})
        fine = np.linspace(0, np.pi, 20001)
        fine_curve = numeric_curve(result, {}, fine)
        check(
            summary["Imax"] >= fine_curve.max() - 1e-9
            and summary["Imax"] - fine_curve.max() < 1e-6,
            "The quartic continuous-angle maximum failed.",
        )
        check(
            summary["Imin"] <= fine_curve.min() + 1e-9
            and fine_curve.min() - summary["Imin"] < 1e-6,
            "The quartic continuous-angle minimum failed.",
        )
        phased = amplitude_record(sp.exp(sp.I * sp.pi / 7) * sp.Matrix(crystal), frame, optical)
        check(
            np.allclose(
                numeric_curve(result, {}, sample),
                numeric_curve(dict(terms=[phased]), {}, sample),
                atol=1e-10,
            ),
            "An unobservable global tensor phase changed the curve.",
        )
    # The monoclinic xy scan cannot depend on the excluded zz diagonal c.
    config = paper_demo_config("LINEAR", "MoTe2-1Tprime")
    config["modes"] = ["Ag"]
    first = calculate_experiment(config)
    config["mode_values"]["Ag"][c] = 9
    second = calculate_experiment(config)
    check(
        all(np.allclose(first["curves"][name], second["curves"][name]) for name in first["curves"]),
        "A spurious c term entered the monoclinic xy scan (printed Eq. 14a issue).",
    )
    return "Complex linear model: Eqs. 13a–d, complex full-3D scans, fourth harmonics, continuous extrema, global-phase invariance and the monoclinic projected-coefficient check pass."


def validate_triclinic_convention():
    """Make the Eq. 15 / Eq. 16 angular-sign comparison explicit and testable."""
    av, bv, dv = 1, 0.8, 0.4
    phase_b, phase_d = np.deg2rad([41, 109])
    tensor = np.array(
        [[av, dv * np.exp(1j * phase_d)], [dv * np.exp(1j * phase_d), bv * np.exp(1j * phase_b)]]
    )
    angles = np.linspace(0, 2 * np.pi, 71)
    for crossed in [False, True]:
        matrix_intensity = []
        reflected = []
        for angle in angles:
            ei = np.array([np.cos(angle), np.sin(angle)])
            es = np.array([-np.sin(angle), np.cos(angle)]) if crossed else ei
            matrix_intensity.append(abs(np.vdot(es, tensor @ ei)) ** 2)
            opposite = np.array([np.cos(angle), -np.sin(angle)])
            opposite_s = np.array([np.sin(angle), np.cos(angle)]) if crossed else opposite
            reflected.append(abs(np.vdot(opposite_s, tensor @ opposite)) ** 2)
        cs, ss = np.cos(angles), np.sin(angles)
        if not crossed:
            printed = (
                av**2 * cs**4
                + bv**2 * ss**4
                + (dv * np.sin(2 * angles)) ** 2
                + np.sin(2 * angles)
                * (
                    av * bv * np.cos(phase_b) * np.sin(2 * angles) / 2
                    - 2 * av * dv * np.cos(phase_d) * cs**2
                    - 2 * bv * dv * np.cos(phase_d - phase_b) * ss**2
                )
            )
        else:
            printed = (
                (av**2 + bv**2 - 2 * av * bv * np.cos(phase_b)) * (np.sin(2 * angles) / 2) ** 2
                + (dv * np.cos(2 * angles)) ** 2
                - np.sin(4 * angles)
                * (bv * dv * np.cos(phase_d - phase_b) - av * dv * np.cos(phase_d))
                / 2
            )
        check(
            np.allclose(printed, reflected, atol=1e-11),
            "The documented Eq. 16 angle-sign comparison failed.",
        )
        check(
            not np.allclose(printed, matrix_intensity),
            "The general off-diagonal sign convention was not exercised.",
        )
    return "Triclinic convention: printed Eq. 16 is reproduced with the documented angle reversal; the engine keeps the explicit positive-angle matrix convention."


def validate_circular_channels_and_rules():
    """Test circular tensor channels separately from conditional momentum congruences."""
    for tensor, expected in [(sp.eye(2), np.eye(2)), (sp.diag(1, -1), np.array([[0, 1], [1, 0]]))]:
        matrix = circular_basis_matrix(tensor)
        check(
            np.allclose(np.abs(numeric(matrix)) ** 2, expected),
            "A basic Circular circular tensor channel failed.",
        )
    mixed = np.abs(numeric(circular_basis_matrix(sp.diag(2, 1)))) ** 2
    check(np.all(mixed > 0), "Anisotropic Ag was incorrectly forced into one circular channel.")
    mos2 = calculate_experiment(circular_mos2_reference_config())
    check(
        mos2["circular"]["rule_applicable"],
        "The declared ideal monolayer normal-axis example was not recognized.",
    )
    a_channels = mos2["circular"]["channels"]["A1'"]["powers"]
    e_channels = mos2["circular"]["channels"]["E'"]["powers"]
    check(
        np.allclose(a_channels - np.diag(np.diag(a_channels)), 0),
        "MoS2 A1-prime should be diagonal in the circular basis.",
    )
    check(
        np.allclose(np.diag(e_channels), 0),
        "MoS2 E-prime should be off-diagonal in the circular basis.",
    )
    for kind in ["CIRCULAR_SAME", "CIRCULAR_OPPOSITE"]:
        config = circular_mos2_reference_config()
        config["optics"] = kind
        run = calculate_experiment(config)
        check(
            all(np.ptp(curve) < 1e-12 for curve in run["curves"].values()),
            "A fixed circular channel acquired an artificial angle dependence.",
        )
    # Reconstruct the MoS2 absorption options and Table 2 Raman restrictions.
    for ell in range(-3, 4):
        for spin in [-1, 1]:
            absorption = any((dm - spin - ell) % 3 == 0 for dm in [-1, 1])
            if not absorption:
                continue
            oc = circular_congruence(3, spin, spin, ell, [0])["eq24_pass"]
            imc = circular_congruence(3, spin, -spin, ell, [2, -2])["eq24_pass"]
            check(
                oc == (ell % 3 == 0) and imc == (ell % 3 == 0),
                "The MoS2 Table 2 necessary-condition example failed.",
            )
    # N=2 alone does not distinguish the channels; the Raman tensor still matters.
    check(
        circular_congruence(2, 1, 1, 0, [0])["eq24_pass"]
        and circular_congruence(2, 1, -1, 0, [0])["eq24_pass"],
        "The N=2 necessary-condition distinction was lost.",
    )
    ca = calculate_experiment(paper_demo_config("CIRCULAR", "CaNb2O6"))
    check(
        not ca["circular"]["axis_check"]["compatible"] and not ca["circular"]["rule_applicable"],
        "The general CaNb2O6 (211) normal was incorrectly certified as a 2D C2 axis.",
    )
    config = circular_mos2_reference_config()
    config["paper_parameters"]["ell_i"] = 1
    vortex_check = calculate_experiment(config)
    check(
        all(
            np.allclose(mos2["curves"][name], vortex_check["curves"][name])
            for name in mos2["curves"]
        ),
        "The conditional vortex rule silently masked a plane-wave intensity.",
    )
    return "Circular-channel model: circular Jones channels, mixed Ag, fixed-channel constants, MoS2 Table 2 conditions, N=2 insufficiency, tilted-axis scope and unmodified ℓ=0 reference curves pass."


def validate_resonance_utility():
    """Check the explicit finite third-order sum and continuous complex phase."""
    laser = np.linspace(-1, 1, 101)
    gamma = 0.12
    phonon = 0.025
    calculated = resonance_element(laser, phonon, [dict(Ecv=0, Gamma_c=gamma, weight=1)])
    expected = 1 / ((laser + 1j * gamma) * (laser - phonon + 1j * gamma))
    check(np.allclose(calculated, expected), "The Linear Eq. 9 one-term denominator failed.")
    phase = np.unwrap(np.angle(calculated))
    check(phase[-1] - phase[0] > np.pi, "The resonance phase lost its quadrant/continuous branch.")
    complex_numerator = resonance_element(laser, phonon, [dict(Ecv=0, Gamma_c=gamma, weight=1j)])
    check(
        np.allclose(complex_numerator, 1j * calculated), "A complex numerator phase was discarded."
    )
    return "Resonance utility: explicit third-order denominators, complex numerator weights and continuous phase agree with the supplied-term model."


def validate_polarization_and_interference():
    """Check physical state identities and interference with independent counterexamples."""
    for state, kind, expected_s3 in [
        (sig_p, "circular", 1),
        (sig_m, "circular", -1),
        (x_hat, "linear", 0),
        (y_hat, "linear", 0),
    ]:
        stokes = normalized_stokes(numeric(state))
        check(
            stokes["kind"] == kind and abs(stokes["S3"] - expected_s3) < 1e-12,
            "A basic Jones/Stokes state was misidentified.",
        )
    component = optical_chain("COMPONENT_SIGMA_ALPHA")
    dr = optical_chain("QWP")
    angles = np.deg2rad([0, 45, 90])
    p = vector_samples(component["effective_analyzer"], angles)
    k = vector_samples(dr["effective_analyzer"], angles)
    overlaps = np.abs(np.sum(p.conjugate() * k, axis=0)) ** 2
    check(
        np.allclose(overlaps, [1, 0.5, 1]),
        "The distinct REFERENCE and Quarter-wave-plate intermediate detection states were lost.",
    )
    for kind in OPTICS_LABELS:
        optical = optical_chain(
            kind,
            direct=dict(theta_i_deg=23, beta_i_deg=67, theta_s0_deg=11, beta_s_deg=83),
            paper=dict(s_in=-1, theta0_deg=19),
        )
        for vector in [optical["Ein"], optical["effective_analyzer"]]:
            sampled = vector_samples(vector, np.linspace(0, 2 * np.pi, 19))
            check(
                np.allclose(np.sum(np.abs(sampled) ** 2, axis=0), 1),
                "A Jones state lost unit normalization.",
            )
            for column in sampled.T:
                stokes = normalized_stokes(column)
                check(
                    abs(sum(stokes[key] ** 2 for key in ["S1", "S2", "S3"]) - 1) < 1e-10,
                    "A pure Jones state left the Poincare sphere.",
                )
    config = component_reference_config()
    config.update(orientation="matrix", T_manual=sp.eye(3), plot_points=361)
    config["mode_values"]["Ag"] = {a: 1, b: 1, c: 0}
    same = calculate_experiment(config)
    item = same["physics"]["interference"]["Ag"]
    check(
        np.allclose(item["coherent_intensity"], np.cos(same["angles"]) ** 2)
        and np.allclose(same["curves"]["Ag"], 0.5),
        "The constructive/destructive interference counterexample failed.",
    )
    check(
        np.allclose(item["entry_self_power"] + item["interference"], item["coherent_intensity"]),
        "Self-powers plus interference do not reconstruct the complete intensity.",
    )
    config["mode_values"]["Ag"][b] = -1
    opposite = calculate_experiment(config)
    check(
        np.allclose(
            opposite["physics"]["interference"]["Ag"]["coherent_intensity"],
            np.sin(opposite["angles"]) ** 2,
        )
        and np.allclose(opposite["curves"]["Ag"], 0.5),
        "A relative π phase was lost or incorrectly inserted into the REFERENCE prescription.",
    )
    source = calculate_experiment(qwp_source_config())
    check(source["physics"]["uses_coherent_intensity"], "The original coherent source law changed.")
    check(
        not same["physics"]["uses_coherent_intensity"],
        "The component reference was incorrectly certified as a coherent law.",
    )
    for parameters in [
        dict(N=5),
        dict(s_in=True),
        dict(ell_i=0.5),
        dict(m_ph=[1.5]),
        dict(absorption_delta_m=True),
        dict(ell_i=float("inf")),
    ]:
        config = circular_mos2_reference_config()
        config["paper_parameters"].update(parameters)
        try:
            calculate_experiment(config)
        except ValueError:
            pass
        else:
            raise AssertionError("An invalid scripted Circular charge/order was accepted.")
    rule = circular_congruence(3, 1, 1, 0, [0])
    check(
        rule["combined_necessary_pass"] is None and not rule["absorption_condition_checked"],
        "An unspecified absorption condition was reported as verified.",
    )
    return "Physics audit: pure Jones/Stokes states, explicit beam-direction convention, distinct REFERENCE/Quarter-wave-plate detector paths, retained constructive/destructive interference, unchanged reference laws and scripted Circular input checks pass."


def validate_cubic_fig1(study):
    """Check all 18 computed curves against independent reductions and phonon-basis invariance."""
    largest_error = 0.0
    for protocol, runs in study["runs"].items():
        for k, run in enumerate(runs):
            check(
                run["config"]["hkl"] == (5, k, 0),
                "A requested Cubic reference surface was replaced.",
            )
            check(
                zero(run["geometry"]["T"] - cubic_frame((5, k, 0))),
                "Cubic reference Eq. 4 frame mismatch.",
            )
            check(
                len(run["results"]["T2g"]["terms"]) == 3
                and run["results"]["T2g"]["rule"] == "DEGENERATE_PARTNER_SUM",
                "Si needs all three complete T2g phonon partners.",
            )
            g = 4 * 25 * k * k / (25 + k * k) ** 2
            angle = run["angles"]
            reference = {
                "VV": np.sin(2 * angle) ** 2 + g * np.cos(angle) ** 4,
                "VH": np.cos(2 * angle) ** 2 + (g / 4) * np.sin(2 * angle) ** 2,
                "SIGMA": np.sin(angle) ** 2 + (g / 4) * (1 - np.sin(2 * angle)),
            }[protocol]
            actual = run["curves"]["T2g"] / study["common_d"] ** 2
            error = float(np.max(np.abs(actual - reference)))
            largest_error = max(largest_error, error)
            check(error < 3e-12, "A Fig. 1 curve disagrees with the independent (h,k,0) reduction.")
            # Independent 3D einsum, including Eq. 8 rotation of the phonon basis.
            frame = numeric(run["geometry"]["T"]).real
            rotated = np.array(
                [
                    numeric(record["Rlab"].subs(run["families"]["T2g"]["values"]))
                    for record in run["results"]["T2g"]["terms"]
                ]
            )
            projected = np.einsum("ia,ijk->ajk", frame, rotated)
            ei = P.T * run["optical"]["Ein"]
            es = P.T * run["optical"]["effective_analyzer"]
            incident, detected = vector_samples(ei, angle), vector_samples(es, angle)
            amplitudes = np.einsum("ia,nij,ja->na", detected.conjugate(), projected, incident)
            check(
                np.allclose(
                    np.sum(np.abs(amplitudes) ** 2, axis=0),
                    run["curves"]["T2g"],
                    atol=3e-12 * study["common_d"] ** 2,
                ),
                "Eq. 8 changed the total degenerate Si intensity.",
            )
            expected_max = {
                "VV": 4 / (4 - g),
                "VH": 1,
                "SIGMA": 0.5 + g / 4 + np.sqrt(0.25 + g * g / 16),
            }[protocol]
            summary = run["summaries"]["T2g"]
            check(
                abs(summary["Imax"] / study["common_d"] ** 2 - expected_max) < 2e-11,
                "A continuous-angle Fig. 1 maximum failed.",
            )
            if protocol == "SIGMA":
                expected_angle = 90 + np.rad2deg(np.arctan(g / 2)) / 2
                check(
                    abs(summary["alpha_max"] - expected_angle) < 1e-8,
                    "The σ⁺α tilt does not match Eq. 11 / Eq. 18.",
                )
            if k == 5:
                check(
                    np.allclose(amplitudes[2], 0, atol=1e-12 * study["common_d"]),
                    "The (110) LO extinction check failed.",
                )
                check(
                    np.max(actual) > 0,
                    "A Fig. 6 LO-only extinction was incorrectly used as total Si Fig. 1.",
                )
    scaled = calculate_experiment(cubic_fig1_config(3, "SIGMA", magnitude=2, plot_points=361))
    phased_config = cubic_fig1_config(3, "SIGMA", plot_points=361)
    phased_config["mode_values"]["T2g"][d] = sp.exp(sp.I * sp.pi / 7)
    phased = calculate_experiment(phased_config)
    check(
        np.allclose(scaled["curves"]["T2g"], 4 * phased["curves"]["T2g"], atol=1e-11),
        "The common d scale or global-phase invariance failed.",
    )
    compile(ORIGIN_FIG1_SCRIPT, "plot_in_origin.py", "exec")
    return [
        "All 18 curves: general 3D matrix engine matches independently derived closed forms; largest absolute error in I/|d|² = "
        + format(largest_error, ".3g"),
        "Eq. 4 proper frames, three complete Si partners, independent Eq. 8 phonon-basis invariance and (110) LO/Si distinction pass.",
        "Continuous extrema, σ tilt 90 to 103.2825255885 degrees, common d scaling and unobservable global phase pass.",
        "Origin plotting script compiles. Actual native Origin execution requires the user's Origin installation.",
    ]


"""Independent regressions for the general engine, components and mathematical export."""


def validate_general_upgrade():
    checks = []
    cfg = slide_component_config()
    cfg["mode_values"]["Ag"] = {
        a: sp.exp(sp.I * deg(23)),
        b: sp.Rational(4, 5) * sp.exp(-sp.I * deg(41)),
        c: sp.Rational(3, 5) * sp.exp(sp.I * deg(79)),
    }
    run = calculate_general(cfg)
    t = run["angles"]
    expected = {
        "Ag(xx)": (1 + np.sin(2 * t)) / 36,
        "Ag(yy)": 0.8**2 * (25 - 5 * np.sin(2 * t)) / 144,
        "Ag(zz)": 0.6**2 * (25 - 5 * np.sin(2 * t)) / 144,
    }
    check(
        set(run["display_curves"]) == set(expected),
        "Ag main plots must contain exactly xx,yy,zz contributions.",
    )
    for name, array in expected.items():
        check(
            np.allclose(run["display_curves"][name], array, atol=2e-13),
            name + ": independent reference component formula failed.",
        )
    check(
        run["results"]["Ag"]["rule"] == "SINGLE_TENSOR",
        "The complete-mode audit must retain coherent interference.",
    )
    legacy = calculate_experiment(component_reference_config())
    for index, name in enumerate(expected):
        check(
            np.allclose(
                run["display_curves"][name], legacy["component_curves"]["Ag"][index], atol=2e-13
            ),
            "A preserved slide component changed.",
        )
    checks.append(
        "Separate Ag(xx), Ag(yy), Ag(zz) match independent slide-frame laws and the previous individual component arrays; no Ag sum is plotted."
    )
    # The same Rc, frame, values and actual Jones states must agree even when
    # their historical report routes have different names.
    comparisons = 0
    for old_cfg in [
        physical_start_config(),
        linear_bp_reference_config(),
        circular_mos2_reference_config(),
        cubic_fig1_config(3, "VV"),
        cubic_fig1_config(3, "VH"),
        cubic_fig1_config(3, "SIGMA"),
    ]:
        old = calculate_experiment(old_cfg)
        new = calculate_general(old_cfg)
        for name, curve in old["curves"].items():
            check(
                np.allclose(new["curves"][name], curve, atol=2e-12, rtol=1e-12),
                "An identical-state route changed its complete-mode result.",
            )
            comparisons += 1
    checks.append(
        f"Historical crystal routes and the common engine agree on {comparisons} complete-mode curves when tensors, frames, coefficients and optical states match."
    )
    # A source 2D tensor embeds exactly into a general 3D tensor for the same
    # external geometry, including the source reference antisymmetric entries.
    source_cfg = qwp_source_config()
    source = calculate_general(source_cfg)
    R = qwp_source_algebra()["record"]["Rperp"].subs(
        qwp_source_values(source_cfg["source_parameters"])
    )
    R3 = sp.zeros(3)
    R3[:2, :2] = R
    custom_name = next(iter(definitions_for("GENERAL", "CUSTOM")))
    custom = general_config("GENERAL", "QWP")
    custom.update(
        point_group="CUSTOM",
        modes=[custom_name],
        mode_values={custom_name: {}},
        custom_tensor=R3,
        orientation="matrix",
        T_manual=sp.eye(3),
    )
    embedded = calculate_general(custom)
    check(
        np.allclose(
            next(iter(source["curves"].values())), embedded["curves"][custom_name], atol=1e-12
        ),
        "2D-source / embedded-3D optical equivalence failed.",
    )
    checks.append(
        "The original 2D optical reference and its explicit general 3D embedding agree for identical tensors and optics."
    )
    # Check every point group with complex coefficients in a principal setting.
    group_count = 0
    channel_count = 0
    trial = {
        a: 1 + sp.I / 5,
        b: sp.Rational(4, 5) - sp.I / 7,
        c: sp.Rational(3, 5) + sp.I / 8,
        d: sp.Rational(2, 5) - sp.I / 9,
        e: sp.Rational(3, 10) + sp.I / 11,
        f: sp.Rational(1, 5) - sp.I / 13,
    }
    for group, data in POINT_GROUPS.items():
        definitions = definitions_for("GENERAL", group)
        for optics in ["CUBIC_VV", "CUBIC_VH", "CUBIC_SIGMA"]:
            general = general_config("GENERAL", optics)
            general.update(
                point_group=group,
                modes=list(definitions),
                mode_values={
                    name: {symbol: trial[symbol] for symbol in parameters_for(item)}
                    for name, item in definitions.items()
                },
                lattice=(
                    (1, 1, 1, 90, 90, 120)
                    if data["system"] in ["trigonal", "hexagonal"]
                    else (1, 1, 1, 90, 90, 90)
                ),
                hkl=(0, 0, 1),
                uvw=(1, 0, 0),
                normal_sign=1,
                plot_points=361,
            )
            calculated = calculate_general(general)
            rows = matching_protocol_audit(calculated)
            channel_count += len(rows)
        group_count += 1
    checks.append(
        f"All {group_count} point groups pass direct and circular-basis reconstructions for VV, VH and σ⁺α ({channel_count} displayed-channel checks)."
    )
    dark = general_config("GENERAL", "CUBIC_VH")
    dark.update(
        point_group="D3",
        modes=["A1"],
        mode_values={"A1": {a: 1 + sp.I / 5, b: sp.Rational(4, 5)}},
        hkl=(0, 0, 1),
        uvw=(1, 0, 0),
        normal_sign=1,
        lattice=(1, 1, 1, 90, 90, 120),
    )
    dark_run = calculate_general(dark)
    check(
        float(np.max(dark_run["curves"]["A1"])) < 1e-25,
        "The principal isotropic A1 crossed channel must be dark.",
    )
    corrupted = copy.deepcopy(dark_run)
    corrupted["curves"]["A1"] = np.ones_like(dark_run["angles"]) * 1e-8
    try:
        tensor_interference_audit(corrupted)
    except ArithmeticError:
        pass
    else:
        raise AssertionError(
            "The roundoff-aware audit accepted a real nonzero error in a dark channel."
        )
    checks.append(
        "Exact dark channels pass a propagated roundoff bound; an injected nonzero intensity still fails the independent audit."
    )
    # Symbolic intensities are independently evaluated, not copied from the
    # floating-point production harmonic summaries.
    for profile in [
        "CUBIC_SIGMA",
        "CUBIC_VV",
        "CUBIC_VH",
        "QWP",
        "CIRCULAR_LINEAR",
        "CIRCULAR_SAME",
        "LINEAR_PAIR",
        "DIRECT_JONES",
    ]:
        current = copy.deepcopy(cfg)
        current["optics"] = profile
        current["paper_parameters"]["analyzer_zero_deg"] = 45
        calculated = calculate_general(current)
        for name, item in calculated["display_channels"].items():
            summary = symbolic_intensity_summary(item["records"])
            expression = intensity_expression(summary, alpha).subs(item["values"])
            values = np.asarray(
                sp.lambdify(alpha, expression, "numpy")(calculated["angles"]), complex
            )
            check(
                np.allclose(values.imag, 0, atol=1e-11),
                "A symbolic intensity acquired an imaginary part.",
            )
            check(
                np.allclose(values.real, item["curve"], atol=2e-11, rtol=1e-11),
                "Symbolic intensity and plotted array differ.",
            )
    checks.append(
        "Symbolic I(angle) before coefficient substitution matches plotted arrays for eight optical configurations, including paired linear and fixed circular channels."
    )
    comparisons = protocol_state_comparison()
    check(
        all(not row["same_states"] for row in comparisons),
        "Distinct optical experiments were incorrectly equated.",
    )
    # The two circular endpoint labels agree for QWP/reference optics while
    # the intermediate projectors differ. This is a state check, not alignment.
    row = next(r for r in comparisons if r["first"] == "QWP" and r["second"] == "CUBIC_SIGMA")
    check(
        row["projector_distances"][0] < 1e-12
        and row["projector_distances"][2] < 1e-12
        and row["projector_distances"][1] > 0.1,
        "The distinct intermediate detector states were lost.",
    )
    checks.append(
        "QWP, direct-linear and elliptical-state scans remain distinct; identical circular endpoints do not force equal intermediate intensities."
    )
    check(
        np.allclose(mpl.rcParams["figure.figsize"], [6.5, 5]),
        "The supplied default figure size changed.",
    )
    check(
        mpl.rcParams["font.size"] == 22
        and mpl.rcParams["lines.linewidth"] == 2
        and mpl.rcParams["savefig.dpi"] == 600,
        "The supplied font/line/export settings changed.",
    )
    check("font.family: Arial" in SCI_STYLE_TEXT, "The requested style font was lost.")
    checks.append(
        "Supplied sci.mplstyle dimensions, base font, line width, transparency and export DPI are retained; the actual font is explicitly recorded."
    )
    return checks


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
         r"Qe_x=e^{i\pi/4}\sigma^{+}"),
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
         r"RQe_x=e^{i\pi/4}(R_{++}\sigma^{+}+R_{-+}\sigma^{-})"),
        ("K08","Return plate and physical angle zero","Cell 8",
         "Detect a wrong return matrix or an arbitrary analyzer reference that would rotate or mirror a plot.",
         "Reconstruct the two returned circular states, their real axes and their relative phase.",
         r"Q_b=Q^T,\quad e_{\rm ref}=e_y,\quad e_\perp=-e_x,\quad p_2/p_1=i"),
        ("K09","Analyzer endpoint calibration","Cell 9",
         "Establish what α=0 and α=90 degrees detect in this optical chain.",
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
         "Set φ=0 and compare the complete angular law, not only one angle.",
         r"I_{\phi=0}=(a^2+A^2-2aA\sin\delta)\cos^2\alpha"),
        ("K16","Diagonal-tensor phase limit","Cell 12",
         "Check that a relative diagonal phase shifts the analyzer pattern with the correct sign.",
         "Set A=0 and compare with the independently shifted cosine law.",
         r"I_{A=0}=a^2\cos^2(\alpha-\phi/2)"),
        ("K17","Pure flipped-channel limit","Cell 12",
         "Confirm extinction of the same-label channel in a known limiting tensor.",
         "Set A=0 and φ=π.",
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
         "Substitute A=0, φ=π and δ=φ/2 separately into the computed difference.",
         r"\Delta I_{A=0}=\Delta I_{\phi=\pi}=\Delta I_{\delta=\phi/2}=0"),
        ("K22","Alternative-convention mirror check","Appendix",
         "Identify a documented change of optical convention without forcing different experiments to share one curve.",
         "Use the appendix return plate and lab-x analyzer, then compare with the main source law at -α.",
         r"I_{\rm appendix}(\alpha)=I_{\rm main}(-\alpha)\quad\text{for the declared source tensor}"),
        ("K23","Angular periodicity","Cell 13; added explicit check",
         "Ensure that the plotted first-harmonic amplitude gives a 180-degree intensity period.",
         "Translate the source scan by π and reduce the difference symbolically.",
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
                              residual_latex=[raman_latex(z) for z in reduced]))


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
                notation_note="Cells 6-11 intermittently call <σ⁻|R|σ⁺> R+-; this report consistently writes R-+. The contracted vector, not the ambiguous label, defines the channel.")


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

print("Cell 21/22 — Run completed successfully.\nReady: General-model and source-reference checks are ready; the tests execute in Cell 22 or with tool 8.\nNext: Run Cell 22.", flush=True)


# %% Code cell 22: Check Silicon (500) and open the application
"""Check silicon and open the calculator with a short guide."""

NOTEBOOK_QUICK_GUIDE = """### Quick start

**Goal:** Calculate Raman intensity for a chosen material, surface and polarization.

1. Choose the model and polarization in **1**.
2. Select the material and tensor coefficients in **2**.
3. Set the surface, optical settings and plot options in **3–5**.
4. Click **6. Calculate**, then check **Polar plots** and **Mathematical derivation**.
5. Use **7** to save the results.

**First run:** Silicon (500), VV is loaded and checked automatically.
"""

crystal_inputs = widgets.VBox(
    [
        material_pick,
        group_pick,
        material_note,
        mode_pick,
        coef_note,
        ag_relation,
        coef_accordion,
        custom_tensor,
    ]
)
orientation_inputs = widgets.VBox(
    [
        surface_pick,
        widgets.HBox(hkl_fields),
        widgets.HBox(uvw_fields),
        auto_x,
        normal_pick,
        psi,
        widgets.HTML(
            "Zone condition: h*u+k*v+l*w=0. Lengths use one common unit. Replace illustrative ratios for tilted anisotropic surfaces."
        ),
        widgets.HBox(lattice_fields[:3]),
        widgets.HBox(lattice_fields[3:]),
    ]
)
optical_inputs = widgets.VBox(
    [optical_preview, direct_box, theta_zero, analyzer_zero, circular_controls]
)
settings = widgets.Tab(
    children=[
        widgets.VBox([case_label, input_note, source_box, crystal_inputs]),
        orientation_inputs,
        optical_inputs,
        widgets.VBox([normalize, cartesian_plots, show_geometry, show_steps, points]),
        widgets.VBox(
            [widgets.HBox([compare_add, compare_clear]), compare_channel, compare_normalized]
        ),
    ]
)
for i, title in enumerate(
    ["2. Material / tensors", "3. Orientation", "4. Jones states", "5. Display", "9. Comparisons"]
):
    settings.set_title(i, title)
optical_overview_out = widgets.Output()
with optical_overview_out:
    display(Markdown(optical_methods_overview_markdown()))
    overview_figure = optical_profile_comparison_figure()
    display(overview_figure)
    plt.close(overview_figure)
optical_guide_panel = widgets.Accordion(children=[optical_overview_out, optical_guide_out])
optical_guide_panel.set_title(0, "Optical profiles: comparison, physics and references")
optical_guide_panel.set_title(1, "Selected optical profile: equations and source scope")
optical_guide_panel.selected_index = None

app_view = widgets.VBox(
    [
        widgets.HTML(
            "<h2>261024 - Raman Tensor Rotation Ver 4.0</h2><p>Version 4.0</p>"
        ),
        model_pick,
        optics_pick,
        optical_guide_panel,
        example_pick,
        load_example_button,
        settings,
        style_note,
        widgets.HBox([run_button, export_button]),
        validate_button,
        status,
        tabs,
    ]
)


def start_application():
    if ui["wired"]:
        display(Markdown(NOTEBOOK_QUICK_GUIDE), metadata={"raman_quick_start": True})
        display(app_view)
        return
    ordinary = [
        case_label,
        input_note,
        *uvw_fields,
        normal_pick,
        psi,
        *lattice_fields,
        custom_tensor,
        *source_widgets.values(),
        circular_N,
        circular_ell,
        circular_charges,
        circular_dm,
        circular_scope,
        normalize,
        cartesian_plots,
        show_geometry,
        show_steps,
        points,
    ]
    for control in ordinary:
        control.observe(invalidate, names="value")
    for control, callback in [
        (material_pick, on_material),
        (group_pick, on_group),
        (model_pick, on_model),
        (optics_pick, on_optics),
        (surface_pick, on_surface),
        (mode_pick, update_visible_modes),
        (ag_relation, on_coefficient_change),
        (auto_x, on_auto_x),
        (circular_spin, on_optics),
        (theta_zero, on_optics),
        (analyzer_zero, on_optics),
        (compare_channel, render_comparison),
        (compare_normalized, render_comparison),
    ]:
        control.observe(callback, names="value")
    for control in hkl_fields:
        control.observe(on_manual_indices, names="value")
    for control in direct_widgets.values():
        control.observe(on_optics, names="value")
    for button, callback in [
        (load_example_button, on_load_example),
        (run_button, on_run),
        (export_button, on_export),
        (latex_button, on_latex),
        (validate_button, on_validate),
        (compare_add, add_comparison),
        (compare_clear, clear_comparison),
        (cubic_button, on_cubic_run),
        (cubic_export, on_cubic_export),
        (cubic_inspect, on_cubic_inspect),
    ]:
        button.on_click(callback)
    for control in [cubic_d, cubic_points]:
        control.observe(invalidate_cubic, names="value")
    ui["wired"] = True
    with sources_out:
        display(
            Markdown(
                "\n\n".join(
                    "**" + role.replace("_", " ") + "**: " + url
                    for role, url in UPGRADE_SOURCES.items()
                )
            )
        )
        display(
            Markdown(
                "The style follows the supplied screenshots. Material symmetry, complex coefficients, lattice metric, surface orientation and optical states all enter the calculation."
            )
        )
    load_configuration(cubic_fig1_config(0, "VV"))
    on_run()
    if state["last_error"] is not None:
        raise RuntimeError(state["last_error"])
    startup_theta = state["run"]["angles"]
    startup_expected = np.sin(2 * startup_theta) ** 2
    np.testing.assert_allclose(
        state["run"]["display_curves"]["T2g"], startup_expected, rtol=0, atol=1e-10,
        err_msg="Silicon (500) VV startup check failed.",
    )
    on_validate()
    tabs.selected_index = tab_index["Polar plots"]
    display(Markdown(NOTEBOOK_QUICK_GUIDE), metadata={"raman_quick_start": True})
    display(app_view)


start_application()

print("Cell 22/22 — Run completed successfully.\nReady: The Silicon (500), VV startup test passed. Its polar plot, annotated derivation and calculator are ready.\nNext: Inspect Polar plots or Mathematical derivation; use tools 1–6 for another calculation.", flush=True)
