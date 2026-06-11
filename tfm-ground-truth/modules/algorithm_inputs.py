"""
algorithm_inputs.py

Generate algorithm-specific input packages (images + manifests) for TFM pipelines.

Targets based on ALGORITHMS_AND_DATASETS_INPUTS.md:
- u-inferforce (MATLAB): Ref_Image / Targ_Image + manifest.json
- pyTFM (Python): <frame>before.tif / <frame>after.tif + pytfm_input.json + out.txt
- Easy-to-use TFM (MATLAB): input_data.mat (displacement.pos/vec)

All outputs are written into a single ZIP archive in-memory for Streamlit download.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import tifffile
from scipy.io import savemat


@dataclass(frozen=True)
class PyTFMParams:
    pixelsize_um: float
    window_size_px: int
    overlap_px: int


def _write_tiff_to_bytes(img: np.ndarray, *, compression: Optional[str] = None) -> bytes:
    buf = io.BytesIO()
    tifffile.imwrite(buf, img, photometric="minisblack", compression=compression)
    return buf.getvalue()


def _mat_input_data_bytes(pos: np.ndarray, vec: np.ndarray) -> bytes:
    """
    Build a MATLAB .mat payload with variable `input_data` containing:
      input_data.displacement(1).pos (N×2)
      input_data.displacement(1).vec (N×2)
    """
    # 1×1 struct displacement with fields pos, vec
    displacement = np.zeros((1,), dtype=[("pos", "O"), ("vec", "O")])
    displacement[0]["pos"] = np.asarray(pos)
    displacement[0]["vec"] = np.asarray(vec)

    # 1×1 struct input_data with field displacement
    input_data = np.zeros((1,), dtype=[("displacement", "O")])
    input_data[0]["displacement"] = displacement

    buf = io.BytesIO()
    savemat(buf, {"input_data": input_data}, do_compression=True)
    return buf.getvalue()


def build_algorithm_inputs_zip(
    *,
    case_id: str,
    ref_image: Optional[np.ndarray],
    def_image: Optional[np.ndarray],
    pos: Optional[np.ndarray],
    vec: Optional[np.ndarray],
    forces: Optional[list],
    metadata: Optional[Dict[str, Any]],
    include_uinferforce: bool,
    include_pytfm: bool,
    include_easy_to_use: bool,
    pytfm_frame_id: str = "01",
    pytfm_params: Optional[PyTFMParams] = None,
    tiff_compat_mode: bool = True,
) -> bytes:
    """
    Create a ZIP containing algorithm-specific input files.

    - case_id becomes the top-level folder name inside the zip
    - tiff_compat_mode=True writes plain grayscale TIFFs (no compression, no extra metadata)
    """
    if not case_id or not case_id.strip():
        case_id = "case"
    case_id = case_id.strip()

    if pytfm_params is None:
        pytfm_params = PyTFMParams(pixelsize_um=1.0, window_size_px=64, overlap_px=32)

    # TIFF compression choice
    compression = None if tiff_compat_mode else "deflate"

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        root = f"{case_id}/"

        # Common: provenance file
        summary = {
            "case_id": case_id,
            "has_images": ref_image is not None and def_image is not None,
            "has_displacement": pos is not None and vec is not None,
            "pytfm": {
                "frame_id": pytfm_frame_id,
                "pixelsize_um": float(pytfm_params.pixelsize_um),
                "window_size_px": int(pytfm_params.window_size_px),
                "overlap_px": int(pytfm_params.overlap_px),
            },
            "tiff_compat_mode": bool(tiff_compat_mode),
            "metadata": metadata or {},
        }
        if forces is not None:
            summary["forces"] = forces
        zf.writestr(root + "case_summary.json", json.dumps(summary, ensure_ascii=False, indent=2))

        # ---- u-inferforce (Level B) ----
        if include_uinferforce:
            if ref_image is None or def_image is None:
                raise ValueError("u-inferforce 输入需要 ref_image 与 def_image")

            base = root + "u-inferforce/"
            ref_rel = "Ref_Image/01.tif"
            targ_rel = "Targ_Image/01.tif"

            zf.writestr(base + ref_rel, _write_tiff_to_bytes(ref_image, compression=compression))
            zf.writestr(base + targ_rel, _write_tiff_to_bytes(def_image, compression=compression))

            manifest = {
                "dataset": case_id,
                "level": "B",
                "notes": "Minimal manifest for u-inferforce-style datasets. Paths are relative to this manifest file.",
                "frames": [
                    {
                        "frame": 1,
                        "ref_image": ref_rel,
                        "targ_image": targ_rel,
                    }
                ],
            }
            zf.writestr(base + "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        # ---- pyTFM (Level B) ----
        if include_pytfm:
            if ref_image is None or def_image is None:
                raise ValueError("pyTFM 输入需要 ref_image 与 def_image")

            base = root + "pyTFM/"
            frame = pytfm_frame_id
            before_name = f"{frame}before.tif"
            after_name = f"{frame}after.tif"

            zf.writestr(base + before_name, _write_tiff_to_bytes(ref_image, compression=compression))
            zf.writestr(base + after_name, _write_tiff_to_bytes(def_image, compression=compression))

            pytfm_input = {
                "dataset": case_id,
                "level": "B",
                "frames": [{"before": before_name, "after": after_name}],
                "parameters": {
                    "pixelsize_um": float(pytfm_params.pixelsize_um),
                    "window_size_px": int(pytfm_params.window_size_px),
                    "overlap_px": int(pytfm_params.overlap_px),
                },
            }
            zf.writestr(base + "pytfm_input.json", json.dumps(pytfm_input, ensure_ascii=False, indent=2))

            out_txt = "\n".join(
                [
                    f"pixelsize_um={float(pytfm_params.pixelsize_um)}",
                    f"window_size_px={int(pytfm_params.window_size_px)}",
                    f"overlap_px={int(pytfm_params.overlap_px)}",
                    "",
                    "This file is intended to help downstream evaluation scripts align grids/units.",
                ]
            )
            zf.writestr(base + "out.txt", out_txt)

        # ---- Easy-to-use TFM (Level A) ----
        if include_easy_to_use:
            if pos is None or vec is None:
                raise ValueError("Easy-to-use 输入需要位移点集 pos/vec（先在平台里求解位移场）")

            base = root + "easy-to-use/"
            zf.writestr(base + "input_data.mat", _mat_input_data_bytes(pos, vec))

        # Human-readable README
        readme = (
            f"# Algorithm input package: {case_id}\n\n"
            "This ZIP is generated by the Streamlit app.\n\n"
            "## Contents\n"
            "- `u-inferforce/`: ref/targ bead images + `manifest.json`\n"
            "- `pyTFM/`: before/after bead images + `pytfm_input.json` + `out.txt`\n"
            "- `easy-to-use/`: `input_data.mat` containing displacement pos/vec\n\n"
            "## Notes\n"
            "- If an algorithm expects a different manifest schema, edit the JSON files accordingly.\n"
            "- TIFF compat mode writes plain 16-bit grayscale TIFF (best compatibility for legacy MATLAB tools).\n"
        )
        zf.writestr(root + "README.md", readme)

    return zip_buf.getvalue()

