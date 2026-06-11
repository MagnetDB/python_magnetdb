<!--
This file is intended to live at  github.com/<MagnetDB-org>/.github  →  profile/README.md
It renders as the organization landing page.
-->

<!-- Optional: add a logo here -->
<!-- <p align="center"><img src="path/to/logo.svg" width="180" alt="MagnetDB logo"></p> -->

<p align="center">
  <a href="https://anr.fr"><img src="https://anr.fr/typo3conf/ext/anr_skin/Resources/Public/assets/img/anr-logo-2021-complet.png" width="220" alt="ANR – Agence nationale de la recherche"></a>
  &nbsp;&nbsp;
  <img src="assets/jnlg-logo-1.png" width="80" alt="JNL-G project logo">
</p>

# MagnetDB

**A scientific data management and simulation platform for high-field magnet research.**

MagnetDB centralizes the configurations, operational data, simulation workflows and analytics of the high-field magnets operated at the [Laboratoire National des Champs Magnétiques Intenses](https://lncmi.cnrs.fr) (LNCMI), CNRS. LNCMI is the french magnet user facility located on 2 sites -- Grenoble (LNCMI-G) and Toulouse (LNCMI-T).

It is the foundation for the digital-twin work being carried out under the ANR JNL-G project (2026–2030) and integrates with the Feel++ scientific computing framework developed at [CEMOSIS](https://cemosis.fr).

The platform serves researchers, magnet designers, operators and lab directors with a single view of magnet configurations, real-time and historical operational data, simulation results, and predictive-maintenance signals.

---

## What's in this organization

The MagnetDB organization hosts the open-source components of the platform. Restricted components (in particular parts of MagnetTools) are kept in private repositories; built artifacts for those are distributed via the LNCMI internal apt depot and the `feelpp/magnettools` DockerHub image.

### Core platform

| Repository | Purpose |
|---|---|
| **`python_magnetdb`** | Django + FastAPI backend, PostgreSQL schema, REST API, background workers, S3/MinIO integration |
| **`magnetdb-frontend`** | Web frontend — currently migrating from Vue 2 to React 18 + TypeScript + Vite |
| **`python_magnetapi`** | Lightweight client library for the MagnetDB API |

### Geometry, mesh and CAD

| Repository | Purpose |
|---|---|
| **`python_magnetgeo`** | Polymorphic geometry definitions for LNCMI-G resistive and superconductor magnets |
| **`python_magnetgmsh`** | Mesh generation from `python_magnetgeo` definitions via Gmsh |
| **`hifimagnet-salome`** | CAD and Mesh Generation with [SALOME](https://www.salome-platform.org) tools (requires a valid **MeshGems** license) |

### Simulation setup and execution

| Repository | Purpose |
|---|---|
| **`python_magnetsetup`** | Templating engine that turns a MagnetDB configuration into a Feel++ / HiFiMagnet simulation case |
| **`python_magnetworkflow`** | Orchestrated workflow: setup → CAD → mesh → run → archive |
| **`hifimagnet-paraview`** | ParaView plugins and post-processing scripts |

### Operational data and analysis

| Repository | Purpose |
|---|---|
| **`python_magnetrun`** | Parsing, curation and analysis of magnets operational data from the different control and monitoring systems -- namely Pupitre, PigBrother and Hybrid MCS recordings following internal LNCMI nomenclature |
| **`magnet-scipy`** | SciPy-based analytics for magnet operational data |
| **`python_magnetcooling`** | Cooling-loop and thermal-hydraulic modelling helpers |

### C++ tools (with Python bindings)

| Repository | Purpose |
|---|---|
| **`python_magnettools`** | Python bindings to the C++ MagnetTools library (analytical magnet calculations) |

---

## How the pieces fit together

```
                ┌───────────────────────────────────────────────────┐
                │              MagnetDB (Django + FastAPI)          │
                │  PostgreSQL · MinIO (S3) · Celery · LemonLDAP SSO │
                └───────────────────────────────────────────────────┘
                           ▲                          ▲
        ┌──────────────────┘                          └──────────────────┐
        │                                                                │
operational data                                              simulation pipeline
        │                                                                │
python_magnetrun                                              python_magnetsetup
        │                                                              │ │
   curation                                                      Feel++ │ HiFiMagnet
   ETL                                                                  │ │
   stats                                                        Orchestrated workflows
   anomaly                                                              │ │
   detection                                                            │ python_magnetgmsh
        │                                                               │ │
        ▼                                                               ▼ ▼
Pupitre · PigBrother · Hybrid                              CAD · mesh · results · provenance
(MCS recordings, sshfs)                                    (attachments in MinIO)
```

The platform follows a three-layer operational data architecture: 

- **Raw** (sshfs, LNCMI-internal) → **Curated Parquet on S3** (canonical interchange layer) → **Derived statistics in PostgreSQL + S3**.

---

## Getting started

- **Documentation**: see the docs site of the relevant repository (each component ships its own Sphinx / Antora site)
- **Demo stack**: a minimal Docker Compose setup (postgres + redis + minio + api + jupyter) is available in `python_magnetdb` for students and external evaluators
- **Container images**: published to GitHub Container Registry (`ghcr.io/<org>/...`)
- **HPC**: Apptainer / Singularity images are available for SLURM / PBS / SGE clusters

If you are joining the project as a student or contributor, start with `python_magnetdb` and the demo Docker Compose stack — it gives you a working MagnetDB instance with a curated seed dataset in under five minutes.

> [!NOTE] The demo stack is intended for evaluation and development purposes. It is not production-ready and should not be used to deploy a real MagnetDB instance.

> [!NOTE] Container images may not be actually published to GHCR until the first stable release (v1.0.0) is tagged.

---

## Related projects

- **[Feel++](https://github.com/feelpp/feelpp)** — finite-element framework used by HiFiMagnet for non-linear multiphysics magnet simulation
- **Scimba** — scientific machine-learning framework used in the JNL-G project for ROM and Neural Galerkin methods
- **JNL-G (ANR AAPG2025)** — Digital twin of the LNCMI-G installation; the project under which MagnetDB is being extended into a full digital-twin platform
- **FASUM (ANR Equipex+)** — 40 T all-superconducting user magnet at LNCMI-G; MagnetDB ingests its operational data
- **EMFL** — European Magnetic Field Laboratory; LNCMI-G is one of three EMFL member facilities

---

## Contributing

Contributions are welcome. Each repository has its own `CONTRIBUTING.md` describing coding standards, testing, and the pull-request workflow.

- Issues and pull requests are tracked per repository
- Larger architectural discussions happen in `python_magnetdb` Discussions
- Releases follow [semantic versioning](https://semver.org/)
- Tagged releases are archived on [Software Heritage](https://www.softwareheritage.org/) and [Zenodo](https://zenodo.org/) with a DOI

---

## Data management

The data managed by MagnetDB in the context of the JNL-G project is described in the project's Data Management Plan. **JNL-G's data are operational data of the LNCMI-G installation — recordings produced by the magnet, power and cooling control systems** while a magnet is energized. User experimental data (measurements performed by external user teams on their own samples) are out of scope and are governed by the [EMFL DMP](https://emfl.eu/).

---

## Funding and acknowledgments

MagnetDB is developed at LNCMI (CNRS UPR 3228) in collaboration with CEMOSIS (Université de Strasbourg). Its development has received support from:

- **ANR AAPG2025 JNL-G** — *Digital twin of the LNCMI-G*
- **H2020 ISABEL** (Grant Agreement No 871106) — *Improving the sustainability of the European Magnetic Field Laboratory*
- **ANR Equipex+ FASUM** (ANR-21-ESRE-0027) — *Forty Tesla Superconducting User Magnet*
- **CNRS** institutional support to LNCMI as a national research infrastructure

<p>
  <a href="https://anr.fr"><img src="https://anr.fr/typo3conf/ext/anr_skin/Resources/Public/assets/img/anr-logo-2021-complet.png" height="50" alt="ANR – Agence nationale de la recherche"></a>
  &nbsp;&nbsp;
  <img src="assets/jnlg-logo-1.png" height="50" alt="JNL-G project logo">
</p>

---

## Contact

- **Lead developer**: Christophe Trophime — *christophe.trophime@lncmi.cnrs.fr*
- **LNCMI Grenoble**: 25 avenue des Martyrs, 38000 Grenoble, France — [lncmi.cnrs.fr](https://lncmi.cnrs.fr)
- **Issues**: please open them in the relevant repository of this organization

---

<sub>MagnetDB is open-source software. Public components are released under the Apache-2.0 or LGPL-3.0 license (see each repository for its exact terms). Documentation and demonstration datasets are released under CC0 or CC-BY-4.0.</sub>
