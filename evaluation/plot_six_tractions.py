import argparse
import json
from pathlib import Path

import numpy as np
import scipy.io


def _as_frames(x):
    if hasattr(x, "_fieldnames"):
        return [x]
    if isinstance(x, np.ndarray):
        return [xi for xi in x.ravel().tolist()]
    return [x]


def load_force_field(path: Path, frame: int = 1):
    d = scipy.io.loadmat(path, squeeze_me=True, struct_as_record=False)
    if "forceField" not in d:
        raise ValueError(f"Missing forceField in {path}")
    frames = _as_frames(d["forceField"])
    if not (1 <= frame <= len(frames)):
        raise ValueError(f"frame out of range: {frame} (1..{len(frames)})")
    fr = frames[frame - 1]
    pos = np.asarray(fr.pos, dtype=float)
    vec = np.asarray(fr.vec, dtype=float)
    good = np.isfinite(pos).all(axis=1) & np.isfinite(vec).all(axis=1)
    pos = pos[good]
    vec = vec[good]
    mag = np.linalg.norm(vec, axis=1)
    return pos, vec, mag


def save_magnitude_plot(pos: np.ndarray, mag: np.ndarray, out_path: Path, title: str):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.2, 5.5), dpi=180)
    p = ax.scatter(
        pos[:, 0],
        pos[:, 1],
        c=mag,
        s=10,
        cmap="inferno",
        marker="s",
        linewidths=0.0,
    )
    cbar = fig.colorbar(p, ax=ax)
    cbar.set_label("|T| (Pa)")
    ax.set_title(title)
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    ax.set_aspect("equal", adjustable="box")
    ax.invert_yaxis()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def save_vector_plot(pos: np.ndarray, vec: np.ndarray, out_path: Path, title: str, max_arrows: int = 2500):
    import matplotlib.pyplot as plt

    n = pos.shape[0]
    step = max(1, int(np.ceil(np.sqrt(max(1, n / max_arrows)))))
    idx = np.arange(0, n, step)
    x = pos[idx, 0]
    y = pos[idx, 1]
    tx = vec[idx, 0]
    ty = vec[idx, 1]
    mag = np.linalg.norm(vec[idx], axis=1)

    # Keep quiver readable regardless of data scale.
    vmax = float(np.nanpercentile(mag, 99.0)) if mag.size > 0 else 1.0
    vmax = max(vmax, 1e-6)
    span = max(float(np.nanmax(x) - np.nanmin(x)), float(np.nanmax(y) - np.nanmin(y)), 1.0)
    desired_max_arrow = 0.12 * span
    quiver_scale = vmax / desired_max_arrow

    fig, ax = plt.subplots(figsize=(6.2, 5.5), dpi=180)
    q = ax.quiver(
        x,
        y,
        tx,
        ty,
        mag,
        cmap="viridis",
        angles="xy",
        scale_units="xy",
        scale=quiver_scale,
        width=0.0023,
        alpha=0.92,
    )
    cbar = fig.colorbar(q, ax=ax)
    cbar.set_label("|T| (Pa)")
    ax.set_title(title)
    ax.set_xlabel("x (pixel)")
    ax.set_ylabel("y (pixel)")
    ax.set_aspect("equal", adjustable="box")
    ax.invert_yaxis()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Generate magnitude/vector plots for six u-inferforce methods.")
    ap.add_argument(
        "--input-root",
        default="datasets/real_data/result/six_method_results",
        help="Root folder with one subfolder per method containing forceField.mat",
    )
    ap.add_argument("--frame", type=int, default=1, help="Frame index in forceField.mat (1-based)")
    ap.add_argument(
        "--methods",
        nargs="+",
        default=["QR", "svd", "gsvd", "1NormReg", "LaplacianReg", "1NormRegLaplacian"],
        help="Method folder names under --input-root",
    )
    args = ap.parse_args()

    input_root = Path(args.input_root)
    summary = {"input_root": str(input_root), "frame": int(args.frame), "methods": []}

    for method in args.methods:
        method_dir = input_root / method
        ff_path = method_dir / "forceField.mat"
        if not ff_path.exists():
            raise FileNotFoundError(f"Missing file: {ff_path}")

        pos, vec, mag = load_force_field(ff_path, frame=args.frame)

        csv_path = method_dir / f"traction_frame{args.frame}_xy_tx_ty_mag.csv"
        npz_path = method_dir / f"traction_frame{args.frame}_xy_tx_ty_mag.npz"
        np.savetxt(
            csv_path,
            np.column_stack([pos, vec, mag]),
            delimiter=",",
            header="x,y,tx,ty,mag",
            comments="",
        )
        np.savez_compressed(npz_path, pos=pos, vec=vec, mag=mag)

        mag_fig = method_dir / f"traction_magnitude_frame{args.frame}.png"
        vec_fig = method_dir / f"traction_vector_frame{args.frame}.png"
        save_magnitude_plot(pos, mag, mag_fig, f"{method} | Traction Magnitude")
        save_vector_plot(pos, vec, vec_fig, f"{method} | Traction Vector")

        summary["methods"].append(
            {
                "method": method,
                "n_vectors": int(pos.shape[0]),
                "mean_traction_pa": float(np.mean(mag)),
                "mean_traction_kpa": float(np.mean(mag) / 1000.0),
                "force_field_mat": str(ff_path),
                "csv": str(csv_path),
                "npz": str(npz_path),
                "magnitude_figure": str(mag_fig),
                "vector_figure": str(vec_fig),
            }
        )

    summary_path = input_root / "plots_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
