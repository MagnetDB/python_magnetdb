# License Audit

**Date**: 2026-05-13  
**Project license**: MIT (all internal components: `python_magnetdb`, `python_magnetgeo`, `magnettools`, `python_magnetgmsh`)

---

## Findings by severity

### Requires attention: LGPL dependencies

| Package | Version | License | Used via |
|---|---|---|---|
| `psycopg` | 3.3.2 | **LGPL-3.0-only** | direct |
| `psycopg-binary` | 3.3.2 | **LGPL-3.0-only** | direct (binary extra) |
| `paramiko` | 3.5.1 | **LGPL** (unversioned) | `fabric` → `python-magnetsetup` |

**Are these a conflict?** No hard conflict with MIT, but LGPL imposes an obligation: users must be able to replace/relink the LGPL library with a modified version.

- For `psycopg` (pure Python + C extension loaded dynamically), Python's import mechanism satisfies the "relinking" requirement — this is a well-established, accepted position.
- For **`psycopg-binary`**, the pre-compiled wheel bundles libpq **statically**. This is the more nuanced case: under strict LGPL-3.0, users should be able to relink against a modified libpq. Most projects accept this in practice, but it's worth knowing. If strict compliance matters, switch to `psycopg[c]` (dynamically links to the system's libpq) and remove the `[binary]` extra.
- For `paramiko`, the LGPL version is not specified in METADATA. The `fabric` dependency only uses it for SSH — same analysis applies.

### Benign: MPL-2.0 dependencies

| Package | License | Used via |
|---|---|---|
| `certifi` | MPL-2.0 | `requests` (transitive) |
| `pathspec` | MPL-2.0 | `black` (dev only) |

MPL-2.0 is **file-level** copyleft: modifications to MPL source files must be released under MPL, but using MPL libraries does not propagate to your code. No conflict.

### Missing license declaration

**`python-magnetsetup`** (`python_magnetsetup/pyproject.toml`) has no `license` field and no `LICENSE` file. Since it is in-tree and authored by the same team, there is no third-party conflict — but it should declare `license = "MIT"` for consistency.

### Requires documentation: `gmsh` GPL-2+ with API exception (`python_magnetgmsh`)

The `gmsh` Python package (4.13.1) is declared **GPL-2+** in its PyPI metadata. At face value this would require any code linking against it to also be GPL. However, the Gmsh project grants an **explicit API exception**:

> Use of the Gmsh API (all language bindings, including Python) is permitted in programs that are not GPL, without those programs being required to be GPL themselves.

`python_magnetgmsh` only ever calls published Gmsh API functions via `ctypes` dynamic loading of `libgmsh.so` — exactly the usage covered by the exception. Its MIT license is therefore valid, and both planned licenses (Apache-2.0, LGPL-3.0) are equally permitted under the exception.

Caveats:
- The PyPI METADATA does not mention the exception. Any downstream auditor will see "GPL" and may be alarmed. The `python_magnetgmsh` README should explicitly document this.
- The exception covers only the API surface. Any future code accessing Gmsh internals beyond the published API would lose this protection.
- GPL-2+ is strictly incompatible with Apache-2.0 in the FSF sense (patent termination clause). The API exception bypasses this, but only for API consumers — worth noting if `python_magnetgmsh` is ever statically bundled with Gmsh.

### Unmaintained dependency (not a license conflict, but a risk)

`xlwt` in `python_magnetgeo/pyproject.toml`: BSD-licensed, no conflict, but the package has been abandoned since 2019. Its recommended replacement is `openpyxl` (MIT).

---

## Full dependency license table

### Python backend (`pyproject.toml`)

| Package | License | Notes |
|---|---|---|
| django | BSD-3-Clause | |
| psycopg | LGPL-3.0-only | See above |
| psycopg-binary | LGPL-3.0-only | Static libpq — see above |
| jsonfield | MIT | |
| pyjwt | MIT | |
| uvicorn | BSD-3-Clause | |
| uvloop | MIT | |
| fastapi | MIT | |
| pydantic | MIT | |
| python-multipart | Apache-2.0 | |
| minio | Apache-2.0 | |
| requests | Apache-2.0 | |
| cryptography | Apache-2.0 OR BSD-3-Clause | |
| celery | BSD-3-Clause | |
| pandas | BSD-3-Clause | |
| pyarrow | Apache-2.0 | |
| numpy | BSD-3-Clause | |
| scipy | BSD-3-Clause | |
| tabulate | MIT | |
| pyyaml | MIT | |
| pint | BSD-3-Clause | |
| watchfiles | MIT | |
| pytz | MIT | |
| matplotlib | PSF/BSD-compatible | |
| mplcursors | MIT | |
| magnettools | MIT | from github.com/feelpp/magnettools |
| python-magnetgeo | MIT | in-tree submodule |
| python-magnetsetup | **undeclared** | in-tree submodule — should be MIT |

### Transitive dependencies (notable)

| Package | License | Used via |
|---|---|---|
| paramiko | LGPL (unversioned) | fabric |
| certifi | MPL-2.0 | requests |
| pathspec | MPL-2.0 | black (dev) |
| bcrypt | Apache-2.0 | paramiko |
| pynacl | Apache-2.0 | paramiko |
| pycryptodome | BSD + Public Domain | |
| python-dateutil | BSD + Apache-2.0 (dual) | |

### python_magnetgeo (`python_magnetgeo/pyproject.toml`)

| Package | License | Notes |
|---|---|---|
| pyyaml | MIT | |
| pandas | BSD-3-Clause | |
| xlwt | BSD | unmaintained since 2019 |

### python_magnetsetup (`python_magnetsetup/pyproject.toml`)

| Package | License | Notes |
|---|---|---|
| python-magnetgeo | MIT | |
| fabric | BSD-2-Clause | |
| pint | BSD-3-Clause | |
| python-decouple | MIT | |
| requests | Apache-2.0 | |
| chevron | MIT | |
| pyyaml | MIT | |

### Web frontend (`web/package.json`)

| Package | License | Notes |
|---|---|---|
| vue / vue-router / vuex | MIT | |
| axios | MIT | |
| plotly.js | MIT | |
| chart.js | MIT | |
| mathjs | Apache-2.0 | |
| lodash | MIT | |
| tailwindcss | MIT | |
| nouislider | MIT | |
| yup | MIT | |
| @guolao/vue-monaco-editor | MIT | |

### Salome Platform and MeshGems (external tools)

#### Salome Platform — LGPL-2.1

All core Salome modules (KERNEL, GEOM, SMESH, SHAPER) from https://github.com/SalomePlatform are **LGPL-2.1** (not "or later").

| Usage pattern | Location | Implication |
|---|---|---|
| External subprocess call (`salome -w1 -t ...`) | `python_magnetsetup/setup.py` | No obligation — external process is not linking |
| Singularity container wrapping Salome | `python_magnetsetup/setup.py` | Salome remains separate inside container |
| Direct API import (`import salome`, `from salome.geom ...`) | `python_magnetgeo/examples/salome_export.py` | Script runs *inside* Salome's own Python — Salome is the host, not a dependency |
| XAO file format reading | `python_magnetgmsh/xao2msh.py` | File format only, no Salome library involved |

No license obligation arises in any of these patterns. Salome is never linked into distributed code.

**Caveat for Apache-2.0 relicensing**: Apache-2.0 and LGPL-2.1-only are technically incompatible per FSF (patent termination clause is an extra restriction under GPL-2). This only matters if MagnetDB code were ever distributed as a combined linked work with Salome — which it is not. Not a practical blocker, but worth noting if the deployment model changes.

#### MeshGems (BLSurf / GHS3D / Hexotic) — Proprietary commercial

MeshGems is owned by **Spatial/Dassault Systèmes** and requires a paid commercial license. The Salome FAQ explicitly states these plugins are not distributed via the internet.

The project correctly treats MeshGems as a user-supplied external tool:
- Algorithm names (`"BLSURF"`, `"GHS3D"`) appear only as config strings — not linked code
- `mgkeydir: str = r"/opt/MeshGems"` in `python_magnetsetup/node.py` is a user-configured path
- `mesh_gems_directory` in `python_magnetdb/models/server.py` is a configuration field only

**Distribution risk**: Any Docker or Singularity image distributed publicly (Docker Hub, GHCR, etc.) that **bundles MeshGems binaries** would violate the MeshGems commercial license. Images may include Salome (LGPL), but MeshGems must be absent or injected at runtime by users who hold a valid commercial license.

### python_magnetgmsh (`../python_magnetgmsh/pyproject.toml`)

| Package | License | Notes |
|---|---|---|
| gmsh | **GPL-2+** (with API exception) | API exception permits MIT/Apache-2.0/LGPL-3.0 use — must be documented |
| xmltodict | MIT | |
| pyyaml | MIT | |
| python-magnetgeo | MIT | |
| numpy | BSD-3-Clause | |

### to_duckdb (`to_duckdb/requirements.txt`)

| Package | License | Notes |
|---|---|---|
| duckdb | MIT | |
| pyyaml | MIT | |
| python-magnetgeo | MIT | |
| pytest | MIT | dev |

---

## Summary

| Category | Verdict |
|---|---|
| GPL packages | `gmsh` is GPL-2+, but covered by Gmsh API exception — must be documented |
| LGPL (psycopg, paramiko) | Compatible in practice; `psycopg[binary]` has a nuanced static-linking caveat |
| MPL-2.0 (certifi, pathspec) | No conflict — file-level copyleft only |
| Apache-2.0 packages | Fully compatible with MIT |
| Internal packages | `python_magnetsetup` should declare its license |

## Recommended actions

1. **`python_magnetsetup/pyproject.toml`**: add `license = {text = "MIT"}` and a `LICENSE` file.
2. **`psycopg[binary]`**: if strict LGPL-3.0 compliance is required, switch to `psycopg[c]` (dynamic linking to system libpq). Otherwise document the accepted risk.
3. **`xlwt`** in `python_magnetgeo`: plan migration to `openpyxl` (MIT) to drop an unmaintained dependency.
4. **`paramiko`**: confirm LGPL version (likely 2.1+) — no action needed, but worth documenting.
5. **`gmsh` API exception**: add a note to the `python_magnetgmsh` README explicitly stating that `gmsh` is used solely through its published API under the Gmsh API exception, and that this permits the MIT (and planned Apache-2.0/LGPL-3.0) licensing of `python_magnetgmsh`.
6. **MeshGems in containers**: ensure no publicly distributed Docker or Singularity image bundles MeshGems binaries. MeshGems must be absent or user-injected at runtime.
7. **`python_magnetgeo/examples/salome_export.py`**: add a header comment stating it requires a separate Salome Platform installation (LGPL-2.1) and is not part of the installable package API.
