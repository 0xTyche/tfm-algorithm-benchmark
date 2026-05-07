import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Quick pyTFM test run on a converted dataset (beads_before/after).")
    ap.add_argument("--dataset-dir", required=True, help="Dataset folder containing pytfm_input.json")
    ap.add_argument("--out-dir", required=True, help="Output folder for tx/ty/u/v and plots")
    ap.add_argument(
        "--pytfm-root",
        default=None,
        help="Path to algorithms/python/pyTFM-master (if pyTFM is not installed as a package)",
    )
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg_path = dataset_dir / "pytfm_input.json"
    if not cfg_path.exists():
        raise SystemExit(f"missing {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    if args.pytfm_root:
        pytfm_root = Path(args.pytfm_root).resolve()
        sys.path.insert(0, str(pytfm_root))

    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from pyTFM.TFM_functions import calculate_deformation, TFM_tractions
        from pyTFM.plotting import show_quiver
    except Exception as e:
        raise SystemExit(
            "Failed to import pyTFM dependencies. "
            "Ensure pyTFM (and its deps like openpiv, numpy, scipy, matplotlib) are installed.\n"
            f"Error: {e}"
        )

    beads_before = dataset_dir / cfg["files"]["beads_before"]
    beads_after = dataset_dir / cfg["files"]["beads_after"]

    p = cfg["analysis_parameters"]
    window_size_px = int(p.get("window_size_px", 100))
    overlap_px = int(p.get("overlap_px", 60))

    # deformation (pixels)
    u, v, *_ = calculate_deformation(str(beads_after), str(beads_before), window_size=window_size_px, overlap=overlap_px)

    # traction (Pa) – pixelsize2 is the pixel size of the deformation grid
    ps1 = float(p.get("pixelsize", 0.181))
    ps2 = ps1 * float(np.mean(np.array(beads_after.shape[:2]) / np.array(u.shape))) if False else None  # placeholder
    # safer: estimate ps2 from u shape only, using bead image dimensions via imread
    try:
        import imageio.v3 as iio

        im = iio.imread(beads_after)
        im_shape = im.shape[:2]
        ps2 = ps1 * float(np.mean(np.array(im_shape) / np.array(u.shape)))
    except Exception:
        ps2 = ps1

    young = float(p.get("young", 8000.0))
    sigma = float(p.get("sigma", 0.49))
    h = p.get("h", "infinite")

    tx, ty = TFM_tractions(u, v, pixelsize1=ps1, pixelsize2=ps2, h=h, young=young, sigma=sigma)

    np.save(out_dir / "u.npy", u)
    np.save(out_dir / "v.npy", v)
    np.save(out_dir / "tx.npy", tx)
    np.save(out_dir / "ty.npy", ty)

    fig1, _ = show_quiver(u, v, cbar_str="deformation [px]")
    fig1.savefig(out_dir / "deformation.png", dpi=200)
    plt.close(fig1)

    fig2, _ = show_quiver(tx, ty, cbar_str="traction [Pa]")
    fig2.savefig(out_dir / "traction.png", dpi=200)
    plt.close(fig2)

    print(f"Wrote outputs to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

