import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a ClickPoints .cdb database for pyTFM TFM_addon.")
    ap.add_argument("--dataset-dir", required=True, help="Folder containing <frame>before.tif and <frame>after.tif images")
    ap.add_argument("--db-name", default="database.cdb", help="Output database file name (ends with .cdb)")
    ap.add_argument(
        "--pytfm-root",
        default=None,
        help="Path to algorithms/python/pyTFM-master (if pyTFM is not installed)",
    )
    args = ap.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    if not dataset_dir.exists():
        raise SystemExit(f"dataset-dir not found: {dataset_dir}")

    if args.pytfm_root:
        sys.path.insert(0, str(Path(args.pytfm_root).resolve()))

    try:
        from pyTFM.database_functions import setup_database_internal
        import clickpoints
    except Exception as e:
        raise SystemExit(
            "Failed to import pyTFM.database_functions. "
            "Install pyTFM (and clickpoints) first, or pass --pytfm-root.\n"
            f"Error: {e}"
        )

    db_name = args.db_name
    if not db_name.endswith(".cdb"):
        raise SystemExit("--db-name must end with .cdb")

    # Create a new DB and use pyTFM's internal setup (this repo version of
    # setup_database_for_tfm does not accept custom regex kwargs).
    db_path = dataset_dir / db_name
    db = clickpoints.DataFile(str(db_path), "w")

    # Minimal folders/keys dict expected by setup_database_internal()
    # We only have before/after; no cell image.
    folders = {
        "folder_after": str(dataset_dir),
        "folder_before": str(dataset_dir),
        "folder_cells": None,
        "folder_out": str(dataset_dir),
    }
    keys = {
        # IMPORTANT: use single backslash in regex (raw string) so \d matches digits.
        "after": r"\d{1,4}after",
        "before": r"\d{1,4}before",
        "cells": "None",
        "frames": r"^(\d{1,4})",
    }

    setup_database_internal(db, keys, folders)
    try:
        db.close()
    except Exception:
        pass
    print(f"Wrote: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

