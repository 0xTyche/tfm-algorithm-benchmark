import argparse
import json
import shutil
from pathlib import Path


def autodetect_one_tif(folder: Path) -> Path:
    if not folder.exists():
        raise SystemExit(f"missing folder: {folder}")
    cands = []
    for ext in (".tif", ".tiff"):
        cands += sorted(folder.glob(f"*{ext}"))
        cands += sorted(folder.glob(f"*{ext.upper()}"))
    cands = [p for p in cands if p.is_file()]
    if not cands:
        raise SystemExit(f"no tif found under: {folder}")
    if len(cands) > 1:
        print(f"[warn] multiple tif files under {folder}, using: {cands[0].name}")
    return cands[0]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert u-inferforce sample dataset (Ref_Image/Targ_Image) into a pyTFM-ready folder."
    )
    ap.add_argument(
        "--src",
        required=True,
        help="Source dataset root, e.g. datasets/u-inferforce-master-datasets",
    )
    ap.add_argument(
        "--dst",
        required=True,
        help="Destination dataset folder (will be created), e.g. datasets/u-inferforce-master-datasets_pyTFM",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite dst folder if it already exists")
    ap.add_argument(
        "--pixelsize-um",
        type=float,
        default=0.181,
        help="Pixel size of bead images in µm/pixel (edit later if unknown)",
    )
    ap.add_argument("--young-pa", type=float, default=8000.0, help="Young's modulus in Pa (edit later)")
    ap.add_argument("--poisson", type=float, default=0.49, help="Poisson ratio (pyTFM uses sigma)")
    ap.add_argument(
        "--window-size-px",
        type=int,
        default=100,
        help="PIV window size in pixels (tune for your beads)",
    )
    ap.add_argument(
        "--overlap-px",
        type=int,
        default=60,
        help="PIV overlap in pixels (>= window_size/2 is common)",
    )
    ap.add_argument(
        "--frame-id",
        default="01",
        help="Frame id prefix for pyTFM/ClickPoints conventions (e.g. '01' -> '01before.tif'/'01after.tif')",
    )
    args = ap.parse_args()

    src = Path(args.src).resolve()
    dst = Path(args.dst).resolve()

    if not src.exists():
        raise SystemExit(f"--src not found: {src}")
    if dst.exists():
        if not args.overwrite:
            raise SystemExit(f"--dst exists: {dst} (use --overwrite to replace)")
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    ref = autodetect_one_tif(src / "Ref_Image")
    targ = autodetect_one_tif(src / "Targ_Image")

    # pyTFM / ClickPoints convention: <frame>before.tif / <frame>after.tif
    # We map:
    #   before = reference (assumed unstressed or reference)
    #   after  = target   (assumed deformed)
    # If your definition is opposite, swap these two files.
    before_name = f"{args.frame_id}before.tif"
    after_name = f"{args.frame_id}after.tif"

    shutil.copy2(ref, dst / before_name)
    shutil.copy2(targ, dst / after_name)

    # Minimal config for a quick test run (you will likely tune these)
    config = {
        "analysis_parameters": {
            "sigma": float(args.poisson),
            "young": float(args.young_pa),
            "pixelsize": float(args.pixelsize_um),
            # pyTFM's internal config.yaml uses µm for window_size/overlap,
            # but the pure-python tutorial uses pixels. We'll store pixels here
            # and document it in notes.
            "window_size_px": int(args.window_size_px),
            "overlap_px": int(args.overlap_px),
            "notes": "window_size_px/overlap_px are in pixels for calculate_deformation().",
        },
        "files": {
            "beads_before": before_name,
            "beads_after": after_name,
        },
        "source": {
            "src_dataset": str(src),
            "ref_image": str(ref),
            "targ_image": str(targ),
        },
    }
    (dst / "pytfm_input.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote dataset: {dst}")
    print(f" - {before_name}")
    print(f" - {after_name}")
    print(" - pytfm_input.json (edit parameters as needed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

