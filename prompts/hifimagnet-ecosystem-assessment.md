# HiFiMagnet Ecosystem — Pre-requisites Assessment Summary

> Generated: 2026-04-27  
> Sources: per-package `*-assessment.yaml` files in each repository's `prompts/` directory.  
> **Dev Effort score: 1 = minimal work needed, 5 = very high effort required**

## Summary Table

| Package | Overall Readiness | CI | Tests / Coverage | Installability | API Stability | Readability | Maintenance | Dev Effort |
|---|---|---|---|---|---|---|---|---|
| **python_magnetgeo** | 3 — usable w/ caveats | ✅ GHA (active) | pytest+cov / **57 %** | `pip install -e .` works | mostly stable (v1.0.1, Beta) | 3/5 | active, solo | **2** |
| **python_magnetrun** | 3 — usable w/ caveats | ✅ GHA (4 Pythons + Debian) | pytest+cov / **~30 %** | manual step (local dep) | unstable, Pre-Alpha | 3/5 | active, solo | **3** |
| **python_magnetworkflows** | 3 — usable w/ caveats | ⚠️ GHA (push triggers **disabled**) | pytest / unknown | system packages (Feel++) | unstable | 3/5 | active, small team | **3** |
| **hifimagnet-paraview** | 3 — usable w/ caveats | ✅ GHA (unit + integration) | pytest / **<30 %** | system ParaView required | unstable, Pre-Alpha | 2/5 | active, small team | **4** |
| **python-magnettools** | 3 — usable w/ caveats | ❌ none | pytest / **30–70 %** | C++ build + system pkgs | experimental | 4/5 | active, solo | **4** |
| **python_magnetgmsh** | 2 — early-stage | ❌ none | shell scripts (no pytest) | manual + system gmsh | experimental, Alpha | 3/5 | active, small team | **3** |
| **python_magnetsetup** | 2 — early-stage | ❌ none | pytest / **<30 %** (logging only) | pip works, system pkgs | unstable | 3/5 | active, small team | **4** |
| **magnet_scipy** | 2 — early-stage | ❌ none | pytest / **~21 %** (stubbed) | pip works (pure Python) | experimental, Alpha | 3/5 | inactive (~7 mo) | **3** |
| **hifimagnet-salome** | 2 — early-stage | ❌ none | manual scripts / unknown | SALOME + proprietary MeshGems | unstable | 3/5 | active, solo | **5** |
| **magnettools-cpp** | 3 — usable w/ caveats | ❌ none | manual scripts / **<30 %** | complex (NAG, CADNA, etc.) | mostly stable | 2/5 | active, solo | **5** |

---

## Per-package Notes

### python_magnetgeo
- Root dependency of the whole stack; best positioned overall.
- Active CI (GitHub Actions, Python 3.11/3.12/3.13), 57% coverage.
- Not published to PyPI — all dependents require a git-install.
- Code concerns: 124 `isinstance` guards, files up to 887 lines (`Insert.py`), inconsistent file naming (PascalCase vs snake_case), 10 TODO/FIXME in core code.

### python_magnetrun
- CI green on 4 Python versions + Debian Trixie; Codecov integrated.
- `python_magnetcooling` is a local non-PyPI dependency requiring a manual pre-install step.
- Coverage at 30% with several modules at 0% (e.g. `BandH.py`).
- Active refactoring (`rework_analysis` branch); API breaking changes documented in CHANGELOG.

### python_magnetworkflows
- CI file exists but push/PR triggers are **commented out** — only runs on `workflow_dispatch`.
- Core dependency Feel++ must be installed as Debian system packages; standard venv requires `--system-site-packages`.
- Leftover artefacts (`.bak`, `.old`, `~` files) committed inside the package directory.

### hifimagnet-paraview
- CI present but meaningful tests require a non-pip-installable ParaView OSMesa binary + Git LFS data.
- Readability 2/5: 40+ commented-out `print()` calls in `stats.py` alone; 20+ functions exceed 50 lines.
- Maintainability 2/5: the 3D/2D/Axi module triplets (`stats`/`statsAxi`, `histo`/`histoAxi`, `meshinfo`/`meshinfoAxi`) duplicate large swaths of logic with no shared base class.

### python-magnettools
- Python pybind11 bindings for the `magnettools-cpp` C++ library.
- Highest readability in the ecosystem (4/5): Google-style docstrings, type annotations, clean module separation.
- No CI; build requires CMake + system C++ libraries; not published to PyPI.

### python_magnetgmsh
- `tests/` directory exists but is empty; pytest is configured but no `test_*.py` files written.
- Shell-script test suite requires external geometry data at `/data/geometries` — not reproducible by new contributors.
- Gmsh ≥ 4.13.1 may require the dev channel (`gmsh.info/python-packages-dev`).

### python_magnetsetup
- No CI — the only existing tests cover the logging module; core simulation-setup logic is untested.
- `jsonmodel.py` (1294 lines) and `setup.py` (1048 lines) are severely oversized.
- Mixed `print()`/`logger` usage, heavy commented-out blocks, and a broken f-string in `jsonmodel.py`.

### magnet_scipy
- Pure Python (scipy/numpy/pandas), so the simplest install in the ecosystem.
- Inactive: last commit ~7 months ago (September 2025).
- Multiple refactor variants coexist (`main.py`, `main_refactor.py`, `coupled_main_refactor.py`) with no clear canonical entry point.
- README Quick Start examples are stubbed out with no actual runnable code.

### hifimagnet-salome
- Requires a full SALOME platform environment (9.9–9.15) and a proprietary MeshGems licence.
- No standard Python packaging (`setup.py`/`pyproject.toml` absent).
- 36 TODO/FIXME markers; `print()` used throughout instead of `logging`.
- Highest dev effort in the ecosystem alongside `magnettools-cpp`.

### magnettools-cpp
- C++ library underpinning most field calculations; very large optional dependency matrix (NAG, CADNA, MATHEVAL, SUNDIALS, SPHEREPACK, EXPOKIT).
- Readability 2/5: pre-C++11 idioms (`NULL`, raw pointers, `using namespace std` in 15 headers), 430-line fat header (`MagnetType.h`).
- Empty `ChangeLog`; no semantic version tags in git; commit messages are terse and sometimes typo-ridden.

---

## Key Findings

| Priority | Finding |
|---|---|
| **Highest leverage** | `python_magnetgeo` is the root dependency of the whole stack and the best positioned. Publishing it to PyPI would unblock all downstream packages. |
| **Missing CI (critical)** | `python_magnetgmsh`, `python_magnetsetup`, `magnet_scipy`, `python-magnettools`, `magnettools-cpp`, and `hifimagnet-salome` have **no CI at all** — regressions are invisible. |
| **System-dep blockers** | `hifimagnet-salome` (SALOME + MeshGems), `hifimagnet-paraview` (ParaView OSMesa), `python_magnetworkflows` (Feel++) cannot be installed with plain `pip install` and cannot be tested in standard CI runners without significant extra work. |
| **Coverage gap** | Only `python_magnetgeo` exceeds 50% coverage. Everything else is ≤30%, meaning regressions in core logic would go undetected. |
| **Structural debt** | `hifimagnet-paraview` (3D/2D/Axi duplication) and `python_magnetsetup` (1000+ line modules) are the worst offenders for long-term maintainability. |
| **Bus-factor risk** | Most packages have a solo maintainer (Christophe Trophime); `python_magnetworkflows` and `hifimagnet-paraview` are the only ones with a meaningful second contributor. |
| **Mislabeled assessment** | `python_magnetcooling/prompts/python_magnetrun-assessment.yaml` contains a `python_magnetrun` assessment — `python_magnetcooling` has no dedicated pre-requisites analysis yet. |

---

## Score Legend

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Overall Readiness | prototype | usable with caveats | production-ready |
| Readability | unreadable | average | exemplary |
| Maintenance | unmaintained | actively maintained solo | full governance |
| Dev Effort | minimal | moderate | very high |
