"""
Render a publication-quality schematic of the project pipeline.

Outputs (created under ./assets/):
  - project_schematic.pdf  (vector, recommended for papers)
  - project_schematic.png  (high-res raster, 600 dpi)

This script uses only Matplotlib (no LaTeX required).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


# ---------- style (top-journal friendly) ----------
mpl.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.linewidth": 0.8,
        "text.color": "#111827",  # near-black
        "axes.labelcolor": "#111827",
    }
)


@dataclass(frozen=True)
class BoxSpec:
    xy: Tuple[float, float]  # lower-left in figure fraction coords
    wh: Tuple[float, float]  # width, height in figure fraction coords
    title: str
    body_lines: Sequence[str]
    facecolor: str = "#F9FAFB"
    edgecolor: str = "#111827"
    title_color: str = "#111827"
    body_color: str = "#111827"


def _draw_box(ax, spec: BoxSpec) -> Tuple[float, float, float, float]:
    x, y = spec.xy
    w, h = spec.wh

    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=spec.edgecolor,
        facecolor=spec.facecolor,
        transform=ax.transAxes,
        zorder=2,
    )
    ax.add_patch(patch)

    # Title
    ax.text(
        x + 0.018,
        y + h - 0.045,
        spec.title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=spec.title_color,
        zorder=3,
    )

    # Body (bullets)
    body_y0 = y + h - 0.085
    line_h = 0.040
    for i, line in enumerate(spec.body_lines):
        ax.text(
            x + 0.022,
            body_y0 - i * line_h,
            line,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.5,
            color=spec.body_color,
            zorder=3,
        )

    return x, y, w, h


def _arrow(
    ax,
    start: Tuple[float, float],
    end: Tuple[float, float],
    color: str = "#111827",
    lw: float = 1.3,
    rad: float = 0.0,
    zorder: int = 1,
):
    a = FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        transform=ax.transAxes,
        zorder=zorder,
    )
    ax.add_patch(a)


def _center_right(x: float, y: float, w: float, h: float) -> Tuple[float, float]:
    return (x + w, y + h / 2)


def _center_left(x: float, y: float, w: float, h: float) -> Tuple[float, float]:
    return (x, y + h / 2)


def _center_top(x: float, y: float, w: float, h: float) -> Tuple[float, float]:
    return (x + w / 2, y + h)


def _center_bottom(x: float, y: float, w: float, h: float) -> Tuple[float, float]:
    return (x + w / 2, y)


def render(out_dir: str = "assets") -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    # A4-ish landscape, clean margins
    fig = plt.figure(figsize=(12.5, 7.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()

    # Palette (subtle, print-friendly)
    c_inputs = "#EEF2FF"  # indigo-50
    c_physics = "#ECFDF5"  # emerald-50
    c_bis = "#FFFBEB"  # amber-50
    c_outputs = "#F0F9FF"  # sky-50

    # Header
    ax.text(
        0.5,
        0.965,
        "BIS-based Traction → Displacement Pipeline (with Synthetic Bead Images)",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=14,
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.935,
        "Uniform traction stress per square patch • Analytic integration removes singularity • Linear system u = A t (optional Tikhonov)",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=10,
        color="#374151",
    )

    # Boxes layout (figure fraction coordinates)
    boxes: list[Tuple[BoxSpec, Tuple[float, float, float, float]]] = []

    spec_inputs = BoxSpec(
        xy=(0.05, 0.62),
        wh=(0.27, 0.26),
        title="Inputs",
        body_lines=[
            "• Geometry: field size, boundary, grid spacing (px)",
            r"• Pixel size: $s$ (μm/px)  ⇒  px↔m",
            r"• Material: $E$ (kPa→Pa),  $\nu$",
            r"• Patches: centers & sizes (px)",
            r"• Traction stress: $t_x,t_y$ (Pa) per patch",
        ],
        facecolor=c_inputs,
        edgecolor="#3730A3",
    )

    spec_balance = BoxSpec(
        xy=(0.36, 0.62),
        wh=(0.27, 0.26),
        title="Force / moment consistency (optional)",
        body_lines=[
            r"• Patch force: $\mathbf{F}=\mathbf{t}\,A$",
            r"• $A=(s_{\mathrm{px}}\cdot s\cdot10^{-6})^2$ (m²)",
            r"• Balance: $\sum \mathbf{F}=0,\ \sum M_z=0$",
            r"• Solve $F_3$ (or $t_3$) to satisfy equilibrium",
        ],
        facecolor=c_physics,
        edgecolor="#065F46",
    )

    spec_bis = BoxSpec(
        xy=(0.67, 0.62),
        wh=(0.28, 0.26),
        title="BIS forward model (analytic, non-singular)",
        body_lines=[
            r"• Discretize substrate into square cells",
            r"• Uniform traction per cell (Pa)",
            r"• Analytic area-integration of Boussinesq kernel",
            r"• Linear operator:  $\,\mathbf{u}=\mathbf{A}\mathbf{t}$",
            r"• (optional) Tikhonov:  $\min\|\mathbf{A}\mathbf{t}-\mathbf{u}\|^2+\lambda^2\|\mathbf{t}\|^2$",
        ],
        facecolor=c_bis,
        edgecolor="#92400E",
    )

    # Mid-level outputs (fields)
    spec_fields = BoxSpec(
        xy=(0.05, 0.28),
        wh=(0.58, 0.26),
        title="Primary outputs (fields)",
        body_lines=[
            r"• Displacement: $u_x(x,y),u_y(x,y)$ (px),  $|u|=\sqrt{u_x^2+u_y^2}$",
            r"• Traction visualization: heatmap (Pa) + arrows (direction)",
            r"• Displacement visualization: magnitude (jet) + vectors (black/green style)",
            r"• Side-by-side comparison for reports / figures",
        ],
        facecolor=c_outputs,
        edgecolor="#0369A1",
    )

    spec_synth = BoxSpec(
        xy=(0.67, 0.28),
        wh=(0.28, 0.26),
        title="Synthetic bead images (for PIV/TFM)",
        body_lines=[
            r"• Reference: Gaussian PSF beads + noise (16-bit TIFF)",
            r"• Deformed: bead positions updated by $(u_x,u_y)$",
            r"• Output: reference.tif & deformed.tif",
            r"• Export: MAT (forces/traction, displacement grid)",
        ],
        facecolor="#FDF2F8",  # rose-50
        edgecolor="#9D174D",
    )

    # Draw boxes
    for spec in (spec_inputs, spec_balance, spec_bis, spec_fields, spec_synth):
        boxes.append((spec, _draw_box(ax, spec)))

    # Unpack coords
    _, b_in = boxes[0]
    _, b_bal = boxes[1]
    _, b_bis = boxes[2]
    _, b_fields = boxes[3]
    _, b_synth = boxes[4]

    # Connectors (Inputs -> Balance -> BIS -> Fields & Synth)
    _arrow(ax, _center_right(*b_in), _center_left(*b_bal), color="#374151")
    _arrow(ax, _center_right(*b_bal), _center_left(*b_bis), color="#374151")

    # BIS to fields (down-left)
    _arrow(
        ax,
        (_center_bottom(*b_bis)[0] - 0.08, _center_bottom(*b_bis)[1]),
        (_center_top(*b_fields)[0] + 0.15, _center_top(*b_fields)[1]),
        color="#374151",
        rad=0.05,
    )
    # BIS to synthetic (down)
    _arrow(ax, _center_bottom(*b_bis), _center_top(*b_synth), color="#374151")

    # Fields to synthetic (for warping beads)
    _arrow(
        ax,
        (_center_right(*b_fields)[0], _center_right(*b_fields)[1] - 0.06),
        (_center_left(*b_synth)[0], _center_left(*b_synth)[1]),
        color="#374151",
        rad=0.0,
    )
    ax.text(
        0.64,
        0.37,
        r"apply $x'=x+u_x,\ y'=y+u_y$",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=9,
        color="#374151",
    )

    # Footnote (reproducibility / quality)
    ax.text(
        0.05,
        0.07,
        "Figure generated by render_project_schematic.py  •  Output: PDF (vector) + PNG (600 dpi)  •  Style: print-safe, colorblind-friendly",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        color="#4B5563",
    )

    pdf_path = os.path.join(out_dir, "project_schematic.pdf")
    png_path = os.path.join(out_dir, "project_schematic.png")
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return pdf_path, png_path


if __name__ == "__main__":
    pdf, png = render()
    print(f"Saved: {pdf}")
    print(f"Saved: {png}")

