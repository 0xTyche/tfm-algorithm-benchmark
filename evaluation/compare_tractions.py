import argparse
import json
from pathlib import Path

import numpy as np
import scipy.io
from scipy.interpolate import griddata


def _as_frames(x):
    """Normalize scipy.loadmat squeeze_me outputs into a list of frame structs."""
    # mat_struct (single) -> [x]
    if hasattr(x, "_fieldnames"):
        return [x]
    # numpy object array of mat_struct
    if isinstance(x, np.ndarray):
        # squeeze_me often makes (n,) object array; ensure flat iteration
        return [xi for xi in x.ravel().tolist()]
    return [x]


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
    # drop NaNs
    good = np.isfinite(pos).all(axis=1) & np.isfinite(tr).all(axis=1)
    pos, tr = pos[good], tr[good]
    settings = {}
    if "TFM_settings" in d and hasattr(d["TFM_settings"], "_fieldnames"):
        s = d["TFM_settings"]
        # Only keep scalar-like fields (best-effort; avoid dumping huge arrays)
        for key in ["young", "poisson", "micrometer_per_pix", "meshsize", "zdepth", "regularization_parameter", "type_noise", "i_max", "j_max"]:
            if hasattr(s, key):
                try:
                    val = getattr(s, key)
                    # squeeze numpy scalars
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
        "meta": {
            "source": str(path),
            "frame": frame,
            "n": int(pos.shape[0]),
            "settings": settings,
        },
    }


def load_uinferforce_forcefield(path: Path, frame: int = 1):
    d = scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)
    if "forceField" not in d:
        raise ValueError(f"u-inferforce forceField.mat missing forceField: {path}")
    frames = _as_frames(d["forceField"])
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
        "meta": {
            "source": str(path),
            "frame": frame,
            "n": int(pos.shape[0]),
        },
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

    # cosine similarity + angle error (ignore near-zero vectors)
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
    """Return angles in degrees in [0, 360). v is Nx2.

    We use a wrapped range to avoid the -180/180 discontinuity which can
    create artificial bands in 2D density plots.
    """
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
    # Avoid confusing scientific-offset formatting (e.g. +2.7e1 on axis)
    try:
        ax.ticklabel_format(axis="both", style="plain", useOffset=False)
    except Exception:
        pass
    if diag:
        lo = max(xedges[0], yedges[0])
        hi = min(xedges[-1], yedges[-1])
        ax.plot([lo, hi], [lo, hi], color="cyan", linewidth=1.0, alpha=0.8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Compare u-inferforce vs Easy-to-use TFM traction vectors.")
    ap.add_argument("--uinferforce-forcefield", required=True, help="Path to u-inferforce forceField.mat")
    ap.add_argument("--easy-bay", required=True, help="Path to Easy-to-use Bay-FTTC_results_*.mat")
    ap.add_argument("--frame", type=int, default=1, help="Frame index (1-based)")
    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--interp", default="linear", choices=["linear", "nearest"], help="Interpolation method")
    ap.add_argument("--plots-dir", default=None, help="If set, write 2D density plots (PNG) into this directory")
    ap.add_argument("--bins", type=int, default=180, help="2D histogram bins per axis (default: 180)")
    ap.add_argument("--log-density", action="store_true", help="Use log color scale for density plots")
    args = ap.parse_args()

    u = load_uinferforce_forcefield(Path(args.uinferforce_forcefield), frame=args.frame)
    e = load_easy_bay(Path(args.easy_bay), frame=args.frame)

    # Interpolate Easy-to-use traction onto u-inferforce traction positions
    # so comparison happens on the same coordinate set (usually smaller).
    points = e["pos"]
    values_x = e["vec"][:, 0]
    values_y = e["vec"][:, 1]
    target = u["pos"]

    ex = griddata(points, values_x, target, method=args.interp)
    ey = griddata(points, values_y, target, method=args.interp)
    e_on_u = np.stack([ex, ey], axis=1)

    mask = np.isfinite(e_on_u).all(axis=1)
    u_vec = u["vec"][mask]
    e_vec = e_on_u[mask]

    # Metrics without scaling
    m0 = vector_metrics(u_vec, e_vec)

    # Best scalar scaling of Easy-to-use to u-inferforce (diagnostic)
    s = best_scale(e_vec, u_vec)
    m1 = vector_metrics(u_vec, s * e_vec)

    plot_files = []
    if args.plots_dir:
        plots_dir = Path(args.plots_dir)
        um = np.linalg.norm(u_vec, axis=1)
        ems = np.linalg.norm(s * e_vec, axis=1)

        # 1) Magnitude joint density (scaled)
        p1 = plots_dir / "joint_density_magnitude_scaled.png"
        mag_range = _percentile_range(np.concatenate([um, ems]))
        save_hist2d(
            um,
            ems,
            p1,
            bins=args.bins,
            xlim=mag_range,
            ylim=mag_range,
            xlabel="|T| u-inferforce",
            ylabel="|T| easy-to-use (scaled)",
            title="2D density: traction magnitude",
            log_density=args.log_density,
            diag=True,
        )
        plot_files.append(str(p1))

        # 2) Direction joint density (angles; scaling does not affect angle)
        au = angles_deg(u_vec)
        ae = angles_deg(e_vec)
        p2 = plots_dir / "joint_density_direction_deg.png"
        save_hist2d(
            au,
            ae,
            p2,
            bins=args.bins,
            xlim=(0.0, 360.0),
            ylim=(0.0, 360.0),
            xlabel="angle u-inferforce (deg)",
            ylabel="angle easy-to-use (deg)",
            title="2D density: traction direction",
            log_density=args.log_density,
            diag=True,
        )
        plot_files.append(str(p2))

        # 3) Angle error vs magnitude
        ang_err = angle_error_deg(u_vec, s * e_vec)
        p3 = plots_dir / "joint_density_angle_error_vs_magnitude.png"
        ang_hi = min(180.0, _percentile_range(ang_err, lo=0.0, hi=99.0)[1])
        save_hist2d(
            um,
            ang_err,
            p3,
            bins=args.bins,
            xlim=mag_range,
            ylim=(0.0, ang_hi),
            xlabel="|T| u-inferforce",
            ylabel="angle error (deg)",
            title="2D density: angle error vs magnitude",
            log_density=args.log_density,
            diag=False,
        )
        plot_files.append(str(p3))

    out = {
        "inputs": {
            "uinferforce": u["meta"],
            "easy_to_use": e["meta"],
            "interp": args.interp,
        },
        "alignment": {
            "compared_points": int(u_vec.shape[0]),
            "uinferforce_points": int(u["pos"].shape[0]),
            "easy_points": int(e["pos"].shape[0]),
        },
        "metrics": {
            "raw": m0,
            "scaled_easy_to_use": {
                "scale_factor": s,
                **m1,
            },
        },
        "plots": plot_files,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

