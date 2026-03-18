import argparse
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.io
from PIL import Image
from scipy.interpolate import RegularGridInterpolator, griddata


def _as_frames(x):
    """Normalize scipy.loadmat squeeze_me outputs into a list of frame structs."""
    if hasattr(x, "_fieldnames"):
        return [x]
    if isinstance(x, np.ndarray):
        return [xi for xi in x.ravel().tolist()]
    return [x]


def load_uinferforce_forcefield(path: Path, frame: int = 1, *, shifted: bool = False):
    d = scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)
    key = "forceFieldShifted" if shifted else "forceField"
    if key not in d:
        raise ValueError(f"u-inferforce forceField.mat missing {key}: {path}")
    frames = _as_frames(d[key])
    if not (1 <= frame <= len(frames)):
        raise ValueError(f"frame out of range: {frame} (1..{len(frames)})")
    fr = frames[frame - 1]
    pos = np.asarray(fr.pos, dtype=float)
    vec = np.asarray(fr.vec, dtype=float)
    good = np.isfinite(pos).all(axis=1) & np.isfinite(vec).all(axis=1)
    pos, vec = pos[good], vec[good]
    return {
        "pos": pos,
        "vec": vec,
        "meta": {"source": str(path), "frame": frame, "n": int(pos.shape[0]), "shifted": shifted},
    }


def load_easy_bay(path: Path, frame: int = 1):
    d = scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)
    if "TFM_results" not in d:
        raise ValueError(f"Easy-to-use result missing TFM_results: {path}")
    frames = _as_frames(d["TFM_results"])
    if not (1 <= frame <= len(frames)):
        raise ValueError(f"frame out of range: {frame} (1..{len(frames)})")
    fr = frames[frame - 1]
    pos = np.asarray(fr.pos, dtype=float)
    tr = np.asarray(fr.traction, dtype=float)
    good = np.isfinite(pos).all(axis=1) & np.isfinite(tr).all(axis=1)
    pos, tr = pos[good], tr[good]
    settings = {}
    if "TFM_settings" in d and hasattr(d["TFM_settings"], "_fieldnames"):
        s = d["TFM_settings"]
        for key in [
            "young",
            "poisson",
            "micrometer_per_pix",
            "meshsize",
            "zdepth",
            "regularization_parameter",
            "type_noise",
            "i_max",
            "j_max",
        ]:
            if hasattr(s, key):
                try:
                    val = getattr(s, key)
                    if isinstance(val, np.ndarray) and val.shape == ():
                        val = val.item()
                    if isinstance(val, (np.floating, np.integer)):
                        val = val.item()
                    if isinstance(val, str) or isinstance(val, (int, float)):
                        settings[key] = val
                except Exception:
                    pass
    return {
        "pos": pos,
        "vec": tr,
        "meta": {"source": str(path), "frame": frame, "n": int(pos.shape[0]), "settings": settings},
    }


def parse_pytfm_out_params(out_txt: Path) -> dict:
    params = {}
    if not out_txt.exists():
        return params
    for line in out_txt.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "\t" not in line:
            continue
        k, v = line.split("\t", 1)
        k = k.strip()
        v = v.strip()
        if k in {"pixelsize", "window_size", "overlap"}:
            try:
                params[k] = float(v)
            except Exception:
                pass
    return params


def load_pytfm_traction_interpolators(
    folder: Path,
    frame_id: str,
    *,
    out_txt: Optional[Path] = None,
    pixelsize_um: Optional[float] = None,
    window_size_um: Optional[float] = None,
    overlap_um: Optional[float] = None,
):
    """Return (itx, ity, meta) where interpolators take points as (y,x)."""
    folder = Path(folder)
    tx_path = folder / f"{frame_id}tx.npy"
    ty_path = folder / f"{frame_id}ty.npy"
    if not tx_path.exists() or not ty_path.exists():
        raise FileNotFoundError(f"Missing pyTFM traction npy files: {tx_path} / {ty_path}")
    tx = np.load(tx_path)
    ty = np.load(ty_path)
    if tx.shape != ty.shape:
        raise ValueError(f"Shape mismatch tx vs ty: {tx.shape} vs {ty.shape}")

    params = parse_pytfm_out_params(out_txt) if out_txt else {}
    ps = pixelsize_um if pixelsize_um is not None else params.get("pixelsize", None)
    ws = window_size_um if window_size_um is not None else params.get("window_size", None)
    ov = overlap_um if overlap_um is not None else params.get("overlap", None)
    if ps is None or ws is None or ov is None:
        raise ValueError(
            "Need pixelsize_um/window_size_um/overlap_um. Provide --pytfm-out-txt or pass the values explicitly."
        )

    window_size_pix = int(math.ceil(ws / ps))
    overlap_pix = int(math.ceil(ov / ps))
    step = window_size_pix - overlap_pix
    if step <= 0:
        raise ValueError(f"Invalid PIV step: window_size_pix={window_size_pix}, overlap_pix={overlap_pix}")

    before_tif = folder / f"{frame_id}before.tif"
    if not before_tif.exists():
        before_tif = folder / f"{frame_id}before.tiff"
    if not before_tif.exists():
        raise FileNotFoundError(f"Missing {frame_id}before.tif to infer image size: {before_tif}")
    im = Image.open(before_tif)
    width, height = im.size

    ny, nx = tx.shape
    x0 = window_size_pix / 2.0
    y0 = window_size_pix / 2.0
    xs = x0 + step * np.arange(nx, dtype=float)
    ys = y0 + step * np.arange(ny, dtype=float)

    itx = RegularGridInterpolator((ys, xs), tx, bounds_error=False, fill_value=np.nan)
    ity = RegularGridInterpolator((ys, xs), ty, bounds_error=False, fill_value=np.nan)

    meta = {
        "source": str(folder),
        "frame_id": frame_id,
        "grid_shape": [int(ny), int(nx)],
        "image_shape": [int(height), int(width)],
        "pixelsize_um": float(ps),
        "window_size_um": float(ws),
        "overlap_um": float(ov),
        "window_size_pix": int(window_size_pix),
        "overlap_pix": int(overlap_pix),
        "step_pix": int(step),
    }
    return itx, ity, meta


def best_scale(a: np.ndarray, b: np.ndarray) -> float:
    """Return scalar s minimizing ||s*a - b||_2 over all entries."""
    num = float(np.sum(a * b))
    den = float(np.sum(a * a))
    if den == 0:
        return 0.0
    return num / den


def vector_metrics(a: np.ndarray, b: np.ndarray):
    """Compute vector field metrics between a and b (Nx2)."""
    diff = a - b
    rmse_xy = float(np.sqrt(np.mean(diff[:, 0] ** 2 + diff[:, 1] ** 2)))
    rmse_x = float(np.sqrt(np.mean(diff[:, 0] ** 2)))
    rmse_y = float(np.sqrt(np.mean(diff[:, 1] ** 2)))

    ma = np.linalg.norm(a, axis=1)
    mb = np.linalg.norm(b, axis=1)
    rmse_mag = float(np.sqrt(np.mean((ma - mb) ** 2)))

    eps = 1e-12
    mask = (ma > eps) & (mb > eps)
    if np.any(mask):
        dot = np.sum(a[mask] * b[mask], axis=1)
        cos = dot / (ma[mask] * mb[mask])
        cos = np.clip(cos, -1.0, 1.0)
        mean_cos = float(np.mean(cos))
        ang = np.degrees(np.arccos(cos))
        mean_ang = float(np.mean(ang))
        med_ang = float(np.median(ang))
    else:
        mean_cos = float("nan")
        mean_ang = float("nan")
        med_ang = float("nan")

    return {
        "rmse_vector": rmse_xy,
        "rmse_x": rmse_x,
        "rmse_y": rmse_y,
        "rmse_magnitude": rmse_mag,
        "mean_cosine": mean_cos,
        "mean_angle_deg": mean_ang,
        "median_angle_deg": med_ang,
    }


def angles_deg(v: np.ndarray) -> np.ndarray:
    ang = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    return np.mod(ang + 360.0, 360.0)


def angle_error_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ma = np.linalg.norm(a, axis=1)
    mb = np.linalg.norm(b, axis=1)
    eps = 1e-12
    mask = (ma > eps) & (mb > eps)
    out = np.full((a.shape[0],), np.nan, dtype=float)
    if np.any(mask):
        dot = np.sum(a[mask] * b[mask], axis=1)
        cos = dot / (ma[mask] * mb[mask])
        cos = np.clip(cos, -1.0, 1.0)
        out[mask] = np.degrees(np.arccos(cos))
    return out


def save_hist1d_overlay(
    series: list,
    out_path: Path,
    *,
    bins: int,
    xlim=None,
    xlabel: str,
    title: str,
    density: bool = True,
):
    """Overlay 1D histograms (lines) for multiple series."""
    try:
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"matplotlib is required for plotting: {e}")

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=160)
    for s in series:
        x = np.asarray(s["x"], dtype=float)
        x = x[np.isfinite(x)]
        if x.size == 0:
            continue
        ax.hist(
            x,
            bins=bins,
            range=xlim,
            density=density,
            histtype="step",
            linewidth=1.8,
            color=s.get("color", None),
            label=s.get("label", "series"),
            alpha=s.get("alpha", 1.0),
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel("density" if density else "count")
    ax.set_title(title)
    if xlim is not None:
        ax.set_xlim(xlim)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def save_cdf_overlay(
    series: list,
    out_path: Path,
    *,
    xlim=None,
    xlabel: str,
    title: str,
):
    """Overlay empirical CDF curves for multiple series."""
    try:
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"matplotlib is required for plotting: {e}")

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=160)
    for s in series:
        x = np.asarray(s["x"], dtype=float)
        x = x[np.isfinite(x)]
        if x.size == 0:
            continue
        x = np.sort(x)
        y = np.linspace(1.0 / x.size, 1.0, x.size)
        ax.plot(
            x,
            y,
            color=s.get("color", None),
            linewidth=2.0,
            alpha=s.get("alpha", 1.0),
            label=s.get("label", "series"),
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel("CDF")
    ax.set_title(title)
    ax.set_ylim(0.0, 1.0)
    if xlim is not None:
        ax.set_xlim(xlim)
    ax.grid(True, linewidth=0.6, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def _percentile_range(x: np.ndarray, lo=1.0, hi=99.0):
    x = x[np.isfinite(x)]
    if x.size == 0:
        return (0.0, 1.0)
    a = float(np.percentile(x, lo))
    b = float(np.percentile(x, hi))
    if not np.isfinite(a) or not np.isfinite(b) or a == b:
        m = float(np.nanmax(x))
        return (0.0, m if m > 0 else 1.0)
    return (a, b)


def save_hist2d(
    x: np.ndarray,
    y: np.ndarray,
    out_path: Path,
    *,
    bins: int,
    xlim,
    ylim,
    xlabel: str,
    ylabel: str,
    title: str,
    log_density: bool,
    diag: bool = False,
):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"matplotlib is required for plotting: {e}")

    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]
    y = y[m]

    H, xedges, yedges = np.histogram2d(x, y, bins=bins, range=[xlim, ylim], density=True)
    Ht = H.T

    fig, ax = plt.subplots(figsize=(6, 5), dpi=160)
    norm = LogNorm(vmin=max(Ht[Ht > 0].min(), 1e-12), vmax=Ht.max()) if (log_density and np.any(Ht > 0)) else None
    im = ax.imshow(
        Ht,
        origin="lower",
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        aspect="auto",
        cmap="magma",
        norm=norm,
    )
    fig.colorbar(im, ax=ax, label="density")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    try:
        ax.ticklabel_format(axis="both", style="plain", useOffset=False)
    except Exception:
        pass
    if diag:
        lo2 = max(xedges[0], yedges[0])
        hi2 = min(xedges[-1], yedges[-1])
        ax.plot([lo2, hi2], [lo2, hi2], color="cyan", linewidth=1.0, alpha=0.8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def save_quiver_overlay(
    pos: np.ndarray,
    fields: list,
    out_path: Path,
    *,
    title: str,
    step: int,
    scale_ratio: float = 0.12,
):
    """Overlay multiple vector fields on the same (x,y) points using different colors.

    fields: list of dicts {name, vec(N,2), color}
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"matplotlib is required for plotting: {e}")

    if pos.ndim != 2 or pos.shape[1] != 2:
        raise ValueError("pos must be N×2")

    # Subsample to avoid an unreadable wall of arrows.
    n = pos.shape[0]
    step = max(1, int(step))
    idx = np.arange(0, n, step)

    x = pos[idx, 0]
    y = pos[idx, 1]

    # Choose a shared scale based on the max magnitude across all fields (subsampled).
    mags = []
    for f in fields:
        v = np.asarray(f["vec"], dtype=float)
        mags.append(np.linalg.norm(v[idx], axis=1))
    mags = np.concatenate(mags) if mags else np.array([1.0])
    vmax = float(np.nanpercentile(mags, 99.0)) if np.isfinite(mags).any() else 1.0
    vmax = max(vmax, 1e-6)

    # Make arrows reasonably sized relative to image extent.
    # quiver 'scale' is inverse: smaller => longer arrows.
    span = max(float(np.nanmax(x) - np.nanmin(x)), float(np.nanmax(y) - np.nanmin(y)), 1.0)
    desired_max_arrow = scale_ratio * span
    quiver_scale = vmax / desired_max_arrow

    fig, ax = plt.subplots(figsize=(8, 6), dpi=160)
    for f in fields:
        v = np.asarray(f["vec"], dtype=float)
        ucomp = v[idx, 0]
        vcomp = v[idx, 1]
        ax.quiver(
            x,
            y,
            ucomp,
            vcomp,
            angles="xy",
            scale_units="xy",
            scale=quiver_scale,
            color=f.get("color", "white"),
            alpha=f.get("alpha", 0.85),
            linewidth=0.3,
            label=f.get("name", "field"),
        )

    ax.set_title(title)
    ax.set_aspect("equal", adjustable="box")
    ax.invert_yaxis()  # image coordinate convention
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def compare_pair(a_name: str, a_vec: np.ndarray, b_name: str, b_vec: np.ndarray):
    """Return metrics comparing a vs b and scaled-b-to-a diagnostics."""
    m0 = vector_metrics(a_vec, b_vec)
    s = best_scale(b_vec, a_vec)
    m1 = vector_metrics(a_vec, s * b_vec)
    return {
        "a": a_name,
        "b": b_name,
        "raw": m0,
        "scaled_b_to_a": {"scale_factor": s, **m1},
    }


def main():
    ap = argparse.ArgumentParser(description="Compare pyTFM vs u-inferforce vs Easy-to-use Bay-FTTC traction vectors.")

    ap.add_argument("--uinferforce-forcefield", required=True, help="Path to u-inferforce forceField.mat")
    ap.add_argument("--uinferforce-frame", type=int, default=1, help="Frame index in forceField.mat (1-based)")
    ap.add_argument("--uinferforce-shifted", action="store_true", help="Use forceFieldShifted instead of forceField")

    ap.add_argument("--easy-bay", required=True, help="Path to Easy-to-use Bay-FTTC_results_*.mat")
    ap.add_argument("--easy-frame", type=int, default=1, help="Frame index in TFM_results (1-based)")

    ap.add_argument("--pytfm-folder", required=True, help="pyTFM output folder containing <frame>tx.npy/<frame>ty.npy")
    ap.add_argument("--pytfm-frame-id", required=True, help="Frame id prefix (e.g. '04' -> '04tx.npy')")
    ap.add_argument("--pytfm-out-txt", default=None, help="Path to pyTFM out.txt (to read pixelsize/window/overlap)")
    ap.add_argument("--pixelsize-um", type=float, default=None)
    ap.add_argument("--window-size-um", type=float, default=None)
    ap.add_argument("--overlap-um", type=float, default=None)

    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--interp-easy", default="linear", choices=["linear", "nearest"], help="Interpolation for Easy->U")
    ap.add_argument("--plots-dir", default=None, help="If set, write 2D density plots (PNG) into this directory")
    ap.add_argument("--bins", type=int, default=180, help="2D histogram bins per axis (default: 180)")
    ap.add_argument("--log-density", action="store_true", help="Use log color scale for density plots")
    ap.add_argument(
        "--overlay-step",
        type=int,
        default=40,
        help="Subsample factor for overlay quiver plot (e.g. 40 means plot every 40th vector).",
    )
    args = ap.parse_args()

    u = load_uinferforce_forcefield(
        Path(args.uinferforce_forcefield),
        frame=args.uinferforce_frame,
        shifted=args.uinferforce_shifted,
    )
    e = load_easy_bay(Path(args.easy_bay), frame=args.easy_frame)
    itx, ity, pmeta = load_pytfm_traction_interpolators(
        Path(args.pytfm_folder),
        args.pytfm_frame_id,
        out_txt=Path(args.pytfm_out_txt) if args.pytfm_out_txt else None,
        pixelsize_um=args.pixelsize_um,
        window_size_um=args.window_size_um,
        overlap_um=args.overlap_um,
    )

    target = u["pos"]

    # easy -> u via griddata
    ex = griddata(e["pos"], e["vec"][:, 0], target, method=args.interp_easy)
    ey = griddata(e["pos"], e["vec"][:, 1], target, method=args.interp_easy)
    e_on_u = np.stack([ex, ey], axis=1)

    # pytfm -> u via regular grid interpolator; expects points as (y,x)
    pts_yx = np.stack([target[:, 1], target[:, 0]], axis=1)
    px = itx(pts_yx)
    py = ity(pts_yx)
    p_on_u = np.stack([px, py], axis=1)

    mask = np.isfinite(u["vec"]).all(axis=1) & np.isfinite(e_on_u).all(axis=1) & np.isfinite(p_on_u).all(axis=1)
    pos_m = target[mask]
    u_vec = u["vec"][mask]
    e_vec = e_on_u[mask]
    p_vec = p_on_u[mask]

    pairs = {
        "u_vs_easy": compare_pair("uinferforce", u_vec, "easy_to_use", e_vec),
        "u_vs_pytfm": compare_pair("uinferforce", u_vec, "pytfm", p_vec),
        "pytfm_vs_easy": compare_pair("pytfm", p_vec, "easy_to_use", e_vec),
    }

    plot_files = []
    if args.plots_dir:
        plots_dir = Path(args.plots_dir)

        # 0) Overlay quiver plot (three colors)
        p0 = plots_dir / "overlay_quiver_three_methods.png"
        save_quiver_overlay(
            pos_m,
            [
                {"name": "u-inferforce", "vec": u_vec, "color": "#00FFFF", "alpha": 0.85},
                {"name": "pyTFM", "vec": p_vec, "color": "#FFD700", "alpha": 0.80},
                {"name": "easy-to-use", "vec": e_vec, "color": "#FF4DA6", "alpha": 0.75},
            ],
            p0,
            title="Traction vectors overlay (same sample points; subsampled)",
            step=args.overlay_step,
        )
        plot_files.append(str(p0))

        # A) Magnitude distribution (three methods; same sampling points)
        mags_u = np.linalg.norm(u_vec, axis=1)
        mags_p = np.linalg.norm(p_vec, axis=1)
        mags_e = np.linalg.norm(e_vec, axis=1)
        mag_range = _percentile_range(np.concatenate([mags_u, mags_p, mags_e]), lo=0.0, hi=99.5)
        pA = plots_dir / "overlay_magnitude_distribution.png"
        save_hist1d_overlay(
            [
                {"x": mags_u, "label": "u-inferforce", "color": "#00FFFF"},
                {"x": mags_p, "label": "pyTFM", "color": "#FFD700"},
                {"x": mags_e, "label": "easy-to-use", "color": "#FF4DA6"},
            ],
            pA,
            bins=min(220, args.bins),
            xlim=mag_range,
            xlabel="|T| (Pa)",
            title="Traction magnitude distribution (three methods; same points)",
        )
        plot_files.append(str(pA))

        # B) Direction distribution (three methods)
        pB = plots_dir / "overlay_direction_distribution_deg.png"
        save_hist1d_overlay(
            [
                {"x": angles_deg(u_vec), "label": "u-inferforce", "color": "#00FFFF"},
                {"x": angles_deg(p_vec), "label": "pyTFM", "color": "#FFD700"},
                {"x": angles_deg(e_vec), "label": "easy-to-use", "color": "#FF4DA6"},
            ],
            pB,
            bins=180,
            xlim=(0.0, 360.0),
            xlabel="direction angle (deg)",
            title="Traction direction distribution (three methods; same points)",
        )
        plot_files.append(str(pB))

        # C) Error distribution (three pairwise CDF curves)
        # Use angle error in degrees (0..180). Each curve corresponds to one pair.
        pC = plots_dir / "overlay_angle_error_cdf_deg.png"
        save_cdf_overlay(
            [
                {"x": angle_error_deg(u_vec, p_vec), "label": "u-inferforce vs pyTFM", "color": "#7CFC00"},
                {"x": angle_error_deg(u_vec, e_vec), "label": "u-inferforce vs easy-to-use", "color": "#FF4500"},
                {"x": angle_error_deg(p_vec, e_vec), "label": "pyTFM vs easy-to-use", "color": "#1E90FF"},
            ],
            pC,
            xlim=(0.0, 180.0),
            xlabel="angle error (deg)",
            title="Traction direction error CDF (three pairwise comparisons; same points)",
        )
        plot_files.append(str(pC))

        # per-pair plots (scaled magnitude, direction, angle error vs magnitude)
        for key, pair in pairs.items():
            a = pair["a"]
            b = pair["b"]
            # pick vectors
            if key == "u_vs_easy":
                a_vec, b_vec = u_vec, e_vec
            elif key == "u_vs_pytfm":
                a_vec, b_vec = u_vec, p_vec
            else:
                a_vec, b_vec = p_vec, e_vec

            s = float(pair["scaled_b_to_a"]["scale_factor"])
            am = np.linalg.norm(a_vec, axis=1)
            bm = np.linalg.norm(s * b_vec, axis=1)
            mag_range = _percentile_range(np.concatenate([am, bm]))

            p1 = plots_dir / f"{key}__joint_density_magnitude_scaled.png"
            save_hist2d(
                am,
                bm,
                p1,
                bins=args.bins,
                xlim=mag_range,
                ylim=mag_range,
                xlabel=f"|T| {a} (Pa)",
                ylabel=f"|T| {b} (scaled) (Pa)",
                title=f"2D density: magnitude ({a} vs {b})",
                log_density=args.log_density,
                diag=True,
            )
            plot_files.append(str(p1))

            p2 = plots_dir / f"{key}__joint_density_direction_deg.png"
            save_hist2d(
                angles_deg(a_vec),
                angles_deg(b_vec),
                p2,
                bins=args.bins,
                xlim=(0.0, 360.0),
                ylim=(0.0, 360.0),
                xlabel=f"angle {a} (deg)",
                ylabel=f"angle {b} (deg)",
                title=f"2D density: direction ({a} vs {b})",
                log_density=args.log_density,
                diag=True,
            )
            plot_files.append(str(p2))

            ang_err = angle_error_deg(a_vec, s * b_vec)
            p3 = plots_dir / f"{key}__joint_density_angle_error_vs_magnitude.png"
            ang_hi = min(180.0, _percentile_range(ang_err, lo=0.0, hi=99.0)[1])
            save_hist2d(
                am,
                ang_err,
                p3,
                bins=args.bins,
                xlim=mag_range,
                ylim=(0.0, ang_hi),
                xlabel=f"|T| {a} (Pa)",
                ylabel="angle error (deg)",
                title=f"2D density: angle error vs magnitude ({a} vs {b})",
                log_density=args.log_density,
                diag=False,
            )
            plot_files.append(str(p3))

    out = {
        "inputs": {
            "uinferforce": u["meta"],
            "easy_to_use": e["meta"],
            "pytfm": pmeta,
            "interp_easy": args.interp_easy,
        },
        "alignment": {
            "compared_points": int(u_vec.shape[0]),
            "uinferforce_points": int(u["pos"].shape[0]),
            "easy_points": int(e["pos"].shape[0]),
        },
        "pairs": pairs,
        "plots": plot_files,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

