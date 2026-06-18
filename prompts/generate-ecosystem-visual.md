# Prompt: Generate HiFiMagnet Ecosystem Status Visual

## Goal

Write a self-contained Python script that produces a publication-quality figure
summarising the **pre-requisites assessment** of the HiFiMagnet package ecosystem.
The figure must convey two things at a glance:

1. **Current readiness** of each package (overall quality / maturity).
2. **Required dev effort** to bring it to a production-ready state.

Save the output as `hifimagnet-ecosystem-status.png` (300 dpi) and, if plotly is
available, also as `hifimagnet-ecosystem-status.html` for interactive inspection.

---

## Input Data

Use the following dataset verbatim. All scores are integers on a 1–5 scale.

```python
packages = [
    # name, category, overall_readiness, readability, has_ci, coverage_pct, dev_effort
    # overall_readiness: 1=prototype … 5=production-ready
    # readability:       1=unreadable … 5=exemplary
    # has_ci:            True / False
    # coverage_pct:      integer 0-100 (use midpoint of ranges; 0 if unknown)
    # dev_effort:        1=minimal … 5=very high
    dict(name="python_magnetgeo",       category="geometry",    overall=3, readability=3, has_ci=True,  coverage=57, effort=2),
    dict(name="python_magnetgmsh",      category="geometry",    overall=2, readability=3, has_ci=False, coverage=0,  effort=3),
    dict(name="hifimagnet-salome",      category="geometry",    overall=2, readability=3, has_ci=False, coverage=0,  effort=5),
    dict(name="python_magnetsetup",     category="simulation",  overall=2, readability=3, has_ci=False, coverage=15, effort=4),
    dict(name="python_magnetworkflows", category="simulation",  overall=3, readability=3, has_ci=True,  coverage=0,  effort=3),
    dict(name="hifimagnet-paraview",    category="postproc",    overall=3, readability=2, has_ci=True,  coverage=20, effort=4),
    dict(name="python_magnetrun",       category="data",        overall=3, readability=3, has_ci=True,  coverage=30, effort=3),
    dict(name="python_magnetcooling",   category="data",        overall=3, readability=3, has_ci=True,  coverage=30, effort=3),
    dict(name="magnet_scipy",           category="simulation",  overall=2, readability=3, has_ci=False, coverage=21, effort=3),
    dict(name="python-magnettools",     category="field",       overall=3, readability=4, has_ci=False, coverage=50, effort=4),
    dict(name="magnettools-cpp",        category="field",       overall=3, readability=2, has_ci=False, coverage=10, effort=5),
]
```

Category colour palette (use consistently across all sub-plots):

| Category | Colour |
|---|---|
| geometry | `#4C72B0` (steel blue) |
| simulation | `#DD8452` (orange) |
| postproc | `#55A868` (green) |
| data | `#C44E52` (red) |
| field | `#8172B2` (purple) |

---

## Required Layout

Produce a **single figure** with three panels arranged horizontally
(`figsize=(18, 7)`):

### Panel 1 — Bubble chart: Readiness vs Dev Effort

- X-axis: `dev_effort` (1–5, label "Dev Effort →  more work")
- Y-axis: `overall_readiness` (1–5, label "Overall Readiness →  more mature")
- Bubble size: proportional to `coverage_pct` (min visible size even at 0%)
- Bubble colour: by `category` using the palette above
- Marker shape: filled circle if `has_ci=True`, open circle (unfilled) if `has_ci=False`
- Label each bubble with the short package name (strip `python_` prefix for brevity;
  use `magnettools-py` for `python-magnettools`)
- Add light grey dashed grid lines at every integer tick
- Add a light-red shaded rectangle covering effort ≥ 4 AND readiness ≤ 2
  (high-effort / low-readiness danger zone), with a small "⚠ danger zone" label
- Legend entries: categories (colour) + CI status (filled vs open marker)

### Panel 2 — Horizontal stacked bar: Score breakdown per package

Sort packages by `overall_readiness` descending, then `dev_effort` ascending.

Draw a horizontal stacked bar for each package with three segments:

| Segment | Value | Colour |
|---|---|---|
| Readiness | `overall_readiness` | `#2ca02c` (green) |
| Readability | `readability` | `#1f77b4` (blue) |
| Effort (inverse) | `6 - dev_effort` | `#d62728` (red, so longer = less effort) |

Normalise each bar to a 0–15 total width so bars are comparable.
Add a small vertical dashed line at x=9 (mid-point, score 3 on each dimension).
Label the right end of each bar with the package's `coverage_pct` value
(e.g. `"57 %"`) so coverage is visible without a separate axis.

### Panel 3 — CI / packaging status matrix (heatmap-style)

Rows = packages (same sort order as Panel 2).
Columns = the following boolean attributes (derive from the input data and the
notes below):

| Column | Source |
|---|---|
| Has CI | `has_ci` |
| CI auto-triggers | False for python_magnetworkflows (triggers disabled), else same as has_ci |
| Coverage > 30 % | `coverage > 30` |
| pip-installable | False for hifimagnet-salome, hifimagnet-paraview, python_magnetworkflows, python_magnetgmsh; True otherwise |
| Published to PyPI | False for all packages |
| Solo bus-factor | True for python_magnetgeo, python_magnetrun, python_magnetcooling, magnet_scipy, python-magnettools, magnettools-cpp, hifimagnet-salome |

Use a two-colour scheme: ✅ green cell for True / ❌ red cell for False.
Display the emoji (or equivalent coloured rectangle + text) inside each cell.
Add column labels rotated 45°.

---

## Implementation requirements

- Use **matplotlib** as the primary library (always available).
- Optionally use **plotly** for the HTML export (guard with `try/except ImportError`).
- No hard-coded absolute paths — save outputs next to the script.
- Use `matplotlib.rcParams` to set a clean style:
  `plt.style.use("seaborn-v0_8-whitegrid")` (fall back to `"seaborn-whitegrid"`
  if the versioned name is unavailable).
- Add a figure-level title:
  `"HiFiMagnet Ecosystem — Package Readiness & Dev Effort Assessment (2026-04-27)"`
- Add a footer note:
  `"Bubble size ∝ test coverage (%). Open circles = no CI. Effort: 1 = minimal, 5 = very high."`
- The script must be runnable with `python generate_ecosystem_visual.py` with no
  arguments and no interactive prompts.

---

## Output files expected

| File | Description |
|---|---|
| `hifimagnet-ecosystem-status.png` | 300 dpi static figure |
| `hifimagnet-ecosystem-status.html` | Interactive plotly version (if plotly installed) |

Place both files in the same directory as the script.
