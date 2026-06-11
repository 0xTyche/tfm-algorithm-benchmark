# datasets/tools

Format converters and dataset helpers for the TFM benchmark. Each script maps
one algorithm's native data layout to a common interchange format, so any
upstream source can feed any downstream algorithm without manual reformatting.

---

## Canonical formats

### Level B — raw bead image pair

The preferred format for end-to-end (image → displacement → traction) comparisons.
Store a `manifest.json` alongside the image files:

```json
{
  "schema": "tfm-benchmark.levelb.v1",
  "name": "<dataset-name>",
  "type": "beads",
  "frames": [
    { "ref": "images/ref.tif", "targ": "images/targ.tif" }
  ],
  "meta": { "pixel_size_nm": null, "time_interval_s": null, "notes": "" }
}
```

`pixel_size_nm` must be filled in before computing physical traction values (Pa).
Multiple frames are supported for time-lapse datasets.

### Level A — canonical displacement field

Use this format when raw bead images are unavailable and only the displacement
field is known (force-inversion-only comparison). Saved as `canonical_displacement.mat`:

```
displField        1×T struct array
  .pos            N×2 double  [x  y]  units: pixels
  .vec            N×2 double  [ux uy] units: pixels
```

`T` is the number of time frames (1 for static TFM).

---

## Scripts

### MATLAB

#### `uinferforce_export_canonical_displacement.m`

Reads a u-inferforce `movieData.mat` and writes the displacement field to the
canonical `displField` format. Prefers `DisplacementFieldCorrectionProcess`
output; falls back to `DisplacementFieldCalculationProcess` if correction was
not run.

```matlab
uinferforce_export_canonical_displacement( ...
    'datasets/u-inferforce-master-datasets/Results/movieData.mat', ...
    'datasets/canonical_displacement.mat');
```

Calling with no arguments opens file-picker dialogs (requires MATLAB desktop).

---

#### `easy_to_use_export_canonical_displacement.m`

Converts an Easy-to-use TFM `input_data.mat` (variable `input_data.displacement`)
to the canonical `displField` struct array. Preserves the noise sample if present.

```matlab
easy_to_use_export_canonical_displacement( ...
    'datasets/Easy-to-use-TFM-datasets/dotmatdata/input_data.mat', ...
    'datasets/canonical_displacement.mat');
```

---

#### `displField_to_easy_to_use_input_data.m`

Wraps a canonical `displField` struct into the `input_data` struct required by
Easy-to-use TFM. Accepts an optional noise displacement sample via `NoiseMatPath`.

```matlab
displField_to_easy_to_use_input_data( ...
    'datasets/canonical_displacement.mat', ...
    'datasets/input_data_for_easy_to_use.mat');

% With a noise sample:
displField_to_easy_to_use_input_data( ...
    'datasets/canonical_displacement.mat', ...
    'datasets/input_data_for_easy_to_use.mat', ...
    'NoiseMatPath', 'datasets/canonical_noise.mat');
```

---

#### `easy_to_use_export_uinferforce_displField.m`

Re-saves the displacement array from an Easy-to-use `input_data.mat` as a
standalone `displField.mat` for direct injection into u-inferforce Step 4/5.
This converts the data structure only; the calling MovieData must already
define compatible image dimensions and ROI.

```matlab
easy_to_use_export_uinferforce_displField( ...
    'datasets/Easy-to-use-TFM-datasets/dotmatdata/input_data.mat', ...
    'datasets/displacementField/displField.mat');
```

---

#### `easy_to_use_input_data_to_uinferforce_movieData.m`

Builds a minimal u-inferforce `MovieData` project from an Easy-to-use
`input_data.mat`. Because u-inferforce requires a real image series to define
image dimensions and run `sanityCheck`, this script generates dummy bead images
(Gaussian noise by default — not blank, to avoid drift-correction failures on
flat templates). It then saves the displacement field to the expected process
output path and registers a `DisplacementFieldCalculationProcess`, making the
project immediately consumable by u-inferforce force inversion (Steps 4/5).

`PixelSize_um`, `NumAperture`, and `Emission_nm` are required because
u-inferforce uses them to compute the PSF sigma.

```matlab
easy_to_use_input_data_to_uinferforce_movieData( ...
    'datasets/Easy-to-use-TFM-datasets/dotmatdata/input_data.mat', ...
    'datasets/u-inferforce-master-datasets/Results/movieData.mat', ...
    'PixelSize_um', 0.108, 'TimeInterval_s', 1.0, ...
    'NumAperture', 1.40, 'Emission_nm', 507);
```

| Option | Default | Description |
|---|---|---|
| `PixelSize_um` | — | Pixel size in µm (required) |
| `NumAperture` | — | Objective NA (required) |
| `Emission_nm` | — | Emission wavelength in nm (required) |
| `TimeInterval_s` | — | Frame interval in seconds (required) |
| `ImageSize_px` | inferred | `[height width]` override |
| `DummyImageMode` | `'noise'` | `'noise'` or `'blank'` |
| `DummyImageDir` | alongside `movieData.mat` | Where to write dummy TIFs |

---

### Python

#### `make_levelb_manifest.py`

Generates a Level-B `manifest.json` for a dataset organized as `Ref_Image/` and
`Targ_Image/` subdirectories. Auto-detects the single `.tif` file in each folder;
warns if multiple files are found and picks the first.

```bash
python make_levelb_manifest.py \
    --dataset-dir datasets/u-inferforce-master-datasets \
    --name u-inferforce-sample
```

---

#### `uinferforce_to_pytfm_dataset.py`

Copies a u-inferforce `Ref_Image`/`Targ_Image` dataset into the pyTFM/ClickPoints
naming convention (`<frame>before.tif` / `<frame>after.tif`) and writes a
`pytfm_input.json` configuration file with material and PIV parameters.

```bash
python uinferforce_to_pytfm_dataset.py \
    --src  datasets/u-inferforce-master-datasets \
    --dst  datasets/u-inferforce-master-datasets_pyTFM \
    --pixelsize-um 0.181 \
    --young-pa 8000 \
    --poisson 0.49 \
    --window-size-px 100 \
    --overlap-px 60
```

---

#### `pytfm_make_clickpoints_db.py`

Creates a ClickPoints `.cdb` database required by the pyTFM GUI add-on
(`TFM_addon`). Run this after `uinferforce_to_pytfm_dataset.py`.

```bash
python pytfm_make_clickpoints_db.py \
    --dataset-dir datasets/u-inferforce-master-datasets_pyTFM \
    --db-name database.cdb
```

Requires `clickpoints` and `pyTFM` to be installed, or pass `--pytfm-root` to
load from the local source tree.

---

#### `pytfm_quick_test.py`

Runs a complete single-shot pyTFM analysis (PIV displacement via `calculate_deformation`,
FTTC tractions via `TFM_tractions`) on a dataset prepared by
`uinferforce_to_pytfm_dataset.py`. Saves `u.npy`, `v.npy`, `tx.npy`, `ty.npy`,
and two quiver plots to the output directory.

```bash
python pytfm_quick_test.py \
    --dataset-dir datasets/u-inferforce-master-datasets_pyTFM \
    --out-dir     evaluation/out/pytfm_quick
```

PIV and material parameters are read from `pytfm_input.json` in `--dataset-dir`.

---

## Conversion map

| Source | Target | Script |
|--------|--------|--------|
| u-inferforce `movieData.mat` | canonical `displField` | `uinferforce_export_canonical_displacement.m` |
| Easy-to-use `input_data.mat` | canonical `displField` | `easy_to_use_export_canonical_displacement.m` |
| canonical `displField` | Easy-to-use `input_data.mat` | `displField_to_easy_to_use_input_data.m` |
| Easy-to-use `input_data.mat` | u-inferforce `displField.mat` | `easy_to_use_export_uinferforce_displField.m` |
| Easy-to-use `input_data.mat` | u-inferforce `movieData.mat` | `easy_to_use_input_data_to_uinferforce_movieData.m` |
| u-inferforce `Ref_Image`/`Targ_Image` | pyTFM dataset | `uinferforce_to_pytfm_dataset.py` |
| u-inferforce `Ref_Image`/`Targ_Image` | Level-B `manifest.json` | `make_levelb_manifest.py` |
