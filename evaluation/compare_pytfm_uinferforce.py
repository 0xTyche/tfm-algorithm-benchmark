import argparse
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.io
from PIL import Image
from scipy.interpolate import RegularGridInterpolator


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
        raise ValueError(f"u-inferforce {path.name} missing {key}: {path}")
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
    """Return angles in degrees in [0, 360). v is Nx2."""
    ang = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    return np.mod(ang + 360.0, 360.0)


def angle_error_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Unsigned angle error in degrees between vectors a and b (Nx2)."""
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
        if k in {"sigma", "young", "pixelsize", "window_size", "overlap", "h"}:
            try:
                params[k] = float(v)
            except Exception:
                pass
    return params


def load_pytfm_traction_grid(
    folder: Path,
    frame_id: str,
    *,
    out_txt: Optional[Path] = None,
    pixelsize_um: Optional[float] = None,
    window_size_um: Optional[float] = None,
    overlap_um: Optional[float] = None,
):
    """
    Load pyTFM tx/ty grids (Pa) and build pixel-coordinate centers for each grid cell.

    Coordinate convention:
    - x increases to the right, y increases downward (image coordinate),
      matching u-inferforce pos convention.
    """
    folder = Path(folder)
    tx_path = folder / f"{frame_id}tx.npy"
    ty_path = folder / f"{frame_id}ty.npy"
    if not tx_path.exists() or not ty_path.exists():
        raise FileNotFoundError(f"Missing pyTFM traction npy files: {tx_path} / {ty_path}")
    tx = np.load(tx_path)
    ty = np.load(ty_path)
    if tx.shape != ty.shape:
        raise ValueError(f"Shape mismatch tx vs ty: {tx.shape} vs {ty.shape}")

    params = {}
    if out_txt is not None:
        params = parse_pytfm_out_params(out_txt)

    ps = pixelsize_um if pixelsize_um is not None else params.get("pixelsize", None)
    ws = window_size_um if window_size_um is not None else params.get("window_size", None)
    ov = overlap_um if overlap_um is not None else params.get("overlap", None)
    if ps is None or ws is None or ov is None:
        raise ValueError(
            "Need pixelsize_um/window_size_um/overlap_um. Provide --pytfm-out-txt or pass the values explicitly."
        )

    # Match pyTFM clickpoints integration: ceil(um/px)
    window_size_pix = int(math.ceil(ws / ps))
    overlap_pix = int(math.ceil(ov / ps))
    step = window_size_pix - overlap_pix
    if step <= 0:
        raise ValueError(f"Invalid PIV step: window_size_pix={window_size_pix}, overlap_pix={overlap_pix}")

    # Read image size to validate grid size and build pixel center coords
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

    # sanity checks (best-effort; allow slight overrun due to ceil)
    if xs[-1] > width + 1 or ys[-1] > height + 1:
        raise ValueError(
            f"Computed grid centers exceed image size. "
            f"image(w,h)=({width},{height}), xs[-1]={xs[-1]}, ys[-1]={ys[-1]}, "
            f"window_size_pix={window_size_pix}, overlap_pix={overlap_pix}"
        )

    # Build (pos, vec) for grid points
    XX, YY = np.meshgrid(xs, ys)
    pos = np.stack([XX.ravel(), YY.ravel()], axis=1)
    vec = np.stack([tx.ravel(), ty.ravel()], axis=1)
    good = np.isfinite(vec).all(axis=1) & np.isfinite(pos).all(axis=1)
    pos, vec = pos[good], vec[good]

    # Interpolators for fast sampling at arbitrary points
    itx = RegularGridInterpolator((ys, xs), tx, bounds_error=False, fill_value=np.nan)
    ity = RegularGridInterpolator((ys, xs), ty, bounds_error=False, fill_value=np.nan)

    return {
        "pos": pos,
        "vec": vec,
        "interp": (itx, ity),
        "meta": {
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
            "n": int(pos.shape[0]),
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Compare u-inferforce vs pyTFM traction vectors.")
    ap.add_argument("--uinferforce-forcefield", required=True, help="Path to u-inferforce forceField.mat")
    ap.add_argument("--uinferforce-frame", type=int, default=1, help="Frame index in forceField.mat (1-based)")
    ap.add_argument("--uinferforce-shifted", action="store_true", help="Use forceFieldShifted instead of forceField")

    ap.add_argument("--pytfm-folder", required=True, help="pyTFM output folder containing <frame>tx.npy/<frame>ty.npy")
    ap.add_argument("--pytfm-frame-id", required=True, help="Frame id prefix (e.g. '04' -> '04tx.npy')")
    ap.add_argument("--pytfm-out-txt", default=None, help="Path to pyTFM out.txt (to read pixelsize/window/overlap)")
    ap.add_argument("--pixelsize-um", type=float, default=None)
    ap.add_argument("--window-size-um", type=float, default=None)
    ap.add_argument("--overlap-um", type=float, default=None)

    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--plots-dir", default=None, help="If set, write 2D density plots (PNG) into this directory")
    ap.add_argument("--bins", type=int, default=180, help="2D histogram bins per axis (default: 180)")
    ap.add_argument("--log-density", action="store_true", help="Use log color scale for density plots")
    args = ap.parse_args()

    u = load_uinferforce_forcefield(
        Path(args.uinferforce_forcefield),
        frame=args.uinferforce_frame,
        shifted=args.uinferforce_shifted,
    )

    p = load_pytfm_traction_grid(
        Path(args.pytfm_folder),
        frame_id=args.pytfm_frame_id,
        out_txt=Path(args.pytfm_out_txt) if args.pytfm_out_txt else None,
        pixelsize_um=args.pixelsize_um,
        window_size_um=args.window_size_um,
        overlap_um=args.overlap_um,
    )

    itx, ity = p["interp"]
    target = u["pos"]
    # RegularGridInterpolator expects points as (y,x)
    pts_yx = np.stack([target[:, 1], target[:, 0]], axis=1)
    tx_u = itx(pts_yx)
    ty_u = ity(pts_yx)
    p_on_u = np.stack([tx_u, ty_u], axis=1)

    mask = np.isfinite(p_on_u).all(axis=1)
    u_vec = u["vec"][mask]
    p_vec = p_on_u[mask]

    m0 = vector_metrics(u_vec, p_vec)
    s = best_scale(p_vec, u_vec)  # scale pyTFM -> u-inferforce
    m1 = vector_metrics(u_vec, s * p_vec)

    plot_files = []
    if args.plots_dir:
        plots_dir = Path(args.plots_dir)
        um = np.linalg.norm(u_vec, axis=1)
        pm_s = np.linalg.norm(s * p_vec, axis=1)

        mag_range = _percentile_range(np.concatenate([um, pm_s]))
        p1 = plots_dir / "joint_density_magnitude_scaled.png"
        save_hist2d(
            um,
            pm_s,
            p1,
            bins=args.bins,
            xlim=mag_range,
            ylim=mag_range,
            xlabel="|T| u-inferforce (Pa)",
            ylabel="|T| pyTFM (scaled) (Pa)",
            title="2D density: traction magnitude",
            log_density=args.log_density,
            diag=True,
        )
        plot_files.append(str(p1))

        au = angles_deg(u_vec)
        apy = angles_deg(p_vec)
        p2 = plots_dir / "joint_density_direction_deg.png"
        save_hist2d(
            au,
            apy,
            p2,
            bins=args.bins,
            xlim=(0.0, 360.0),
            ylim=(0.0, 360.0),
            xlabel="angle u-inferforce (deg)",
            ylabel="angle pyTFM (deg)",
            title="2D density: traction direction",
            log_density=args.log_density,
            diag=True,
        )
        plot_files.append(str(p2))

        ang_err = angle_error_deg(u_vec, s * p_vec)
        p3 = plots_dir / "joint_density_angle_error_vs_magnitude.png"
        ang_hi = min(180.0, _percentile_range(ang_err, lo=0.0, hi=99.0)[1])
        save_hist2d(
            um,
            ang_err,
            p3,
            bins=args.bins,
            xlim=mag_range,
            ylim=(0.0, ang_hi),
            xlabel="|T| u-inferforce (Pa)",
            ylabel="angle error (deg)",
            title="2D density: angle error vs magnitude",
            log_density=args.log_density,
            diag=False,
        )
        plot_files.append(str(p3))

    out = {
        "inputs": {"uinferforce": u["meta"], "pytfm": p["meta"]},
        "alignment": {
            "compared_points": int(u_vec.shape[0]),
            "uinferforce_points": int(u["pos"].shape[0]),
            "pytfm_grid_points": int(p["pos"].shape[0]),
        },
        "metrics": {
            "raw": m0,
            "scaled_pytfm": {"scale_factor": s, **m1},
        },
        "plots": plot_files,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

