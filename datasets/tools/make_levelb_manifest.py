import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create a Level-B (raw image) manifest.json from a Ref_Image/Targ_Image style dataset."
    )
    ap.add_argument("--dataset-dir", required=True, help="Path to dataset root, e.g. datasets/u-inferforce-master-datasets")
    ap.add_argument("--name", default=None, help="Dataset name override (default: folder name)")
    ap.add_argument("--ref", default=None, help="Ref image path (relative to dataset-dir). If omitted, auto-detect under Ref_Image/")
    ap.add_argument("--targ", default=None, help="Target image path (relative to dataset-dir). If omitted, auto-detect under Targ_Image/")
    ap.add_argument("--out", default="manifest.json", help="Output manifest filename (relative to dataset-dir)")
    args = ap.parse_args()

    root = Path(args.dataset_dir).resolve()
    if not root.exists():
        raise SystemExit(f"dataset-dir not found: {root}")

    name = args.name or root.name

    def autodetect_one(folder: Path) -> str:
        if not folder.exists():
            raise SystemExit(f"missing folder: {folder}")
        cands = []
        for ext in (".tif", ".tiff"):
            cands.extend(sorted(folder.glob(f"*{ext}")))
        cands = [p for p in cands if p.is_file()]
        if not cands:
            raise SystemExit(f"no tif found under: {folder}")
        if len(cands) > 1:
            # choose the first, but be explicit
            print(f"[warn] multiple tif files under {folder}, using: {cands[0].name}")
        return str(cands[0].relative_to(root).as_posix())

    ref = args.ref or autodetect_one(root / "Ref_Image")
    targ = args.targ or autodetect_one(root / "Targ_Image")

    manifest = {
        "schema": "tfm-benchmark.levelb.v1",
        "name": name,
        "type": "beads",
        "frames": [{"ref": ref, "targ": targ}],
        "meta": {"pixel_size_nm": None, "time_interval_s": None, "notes": ""},
    }

    out_path = root / args.out
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

