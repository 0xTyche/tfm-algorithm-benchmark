# cTFM — Confocal Traction Force Microscopy

**Authors:** Manuel Zündel, Alexander E. Ehret, Edoardo Mazza
**Institution:** Experimental Continuum Mechanics Group, Institute of Mechanical Systems, ETH Zürich
**Copyright:** 2014–2016

Computes 3D traction vectors from confocal z-stack image pairs using nonlinear finite element analysis (NLFEM) in ABAQUS.

---

## Method overview

The substrate is treated as a nonlinear hyperelastic solid. Fluorescent beads embedded in the substrate are detected in both the deformed and reference states, and their displacements are imposed as boundary conditions in an ABAQUS FEM model. The resulting reaction forces give the cell traction field.

This differs from all other algorithms in this benchmark: it requires 3D confocal z-stacks and a commercial FEM solver (ABAQUS), and it models large deformations. It cannot be run against the standard Level B widefield bead image datasets.

---

## Workflow

The analysis runs in four sequential steps:

| Step | Script | Environment | Description |
|------|--------|-------------|-------------|
| A | `A_detection_and_meshing.m` | MATLAB GUI | Detect fluorescent dots in z-stacks; generate triangular mesh |
| B | `B_ReferenceConfigurationReconstruction.m` | MATLAB | Reconstruct reference (stress-free) configuration |
| C1 | ABAQUS CAE | ABAQUS + Python 2 | Run NLFEM; compute traction from boundary displacements |
| C2 | `C2_TractionFieldsPlots.m` | MATLAB | Load ABAQUS results; plot traction fields |

### Step A — Detection and meshing

`A_detection_and_meshing.m` launches the `cTFM_meshing` GUI. The GUI lets you:
- Load confocal z-stacks (deformed and reference)
- Detect bead positions (automatic + manual correction)
- Generate and optimize a triangular mesh on the detected bead array

Mesh optimization uses Gurobi. The output is a mesh data file consumed by steps B and C1.

### Step B — Reference configuration reconstruction

`B_ReferenceConfigurationReconstruction.m` computes the undeformed (reference) positions of the mesh nodes from the reference-state z-stack. This step establishes the stress-free geometry for the FEM model.

Set `module_path`, `path_data`, and `job_name` at the top of the script before running.

### Step C1 — Nonlinear FEM (ABAQUS)

The Python scripts in `ReferenceReconstructionAndNLTFM/TFR_Python/` run inside ABAQUS CAE's embedded Python 2 interpreter. Do not run them with a standalone Python installation.

Key classes:

| Class | File | Role |
|-------|------|------|
| `AdaptiveMeshing` | `Classes/AdaptiveMeshing.py` | Refines FEM mesh around high-gradient regions |
| `BCApplication` | `Classes/BC_Application.py` | Applies measured bead displacements as Dirichlet BCs |
| `ExportResults` | `Classes/ExportResults.py` | Reads traction output from the ABAQUS ODB file |

`AdditionalPythonModules/` contains a bundled `scipy`/`numpy` distribution for use within ABAQUS's Python environment. This directory must remain alongside the scripts at runtime.

### Step C2 — Traction plots

`C2_TractionFieldsPlots.m` reads the exported results and generates traction vector and magnitude visualizations.

---

## Dependencies

| Dependency | Version | Required for |
|------------|---------|--------------|
| MATLAB | R2015a or later | Steps A, B, C2 |
| MATLAB Image Processing Toolbox | — | Step A (z-stack loading) |
| MATLAB Optimization Toolbox | — | Step B |
| Gurobi | 6.x or later | Step A (mesh optimization) |
| ABAQUS | 6.14-1 or later | Step C1 |
| Python | 2.7 (ABAQUS built-in) | Step C1 |

**Python note:** the scripts in `TFR_Python/` use Python 2 syntax (`print 'x'`, `np.matrix`) because they execute inside ABAQUS's embedded interpreter. Installing Python 3 separately will not help and will break compatibility.

**Gurobi note:** a valid Gurobi license is required for step A. Academic licenses are available from Gurobi at no cost.

---

## Input data

- Confocal z-stack TIFF series: deformed state (cell present) and reference state (cell removed or before seeding)
- Fluorescent bead layer must be within the confocal imaging volume

This algorithm is **not compatible** with 2D widefield bead images used by the other algorithms in this benchmark.

---

## Output

- 3D traction vector field at mesh node positions
- Traction magnitude and direction plots (step C2)

---

## Directory structure

```
cTFM/
├── A_detection_and_meshing.m
├── B_ReferenceConfigurationReconstruction.m
├── C2_TractionFieldsPlots.m
├── Detection_Meshing/
│   ├── cTFM_meshing.m          # GUI entry point (called by step A)
│   └── functions/              # Supporting MATLAB functions
├── ReferenceReconstructionAndNLTFM/
│   ├── TFR_Matlab/             # MATLAB reference reconstruction routines
│   └── TFR_Python/
│       ├── Classes/            # ABAQUS Python 2 scripts (C1)
│       └── AdditionalPythonModules/  # Bundled scipy/numpy for ABAQUS
└── README.md
```
