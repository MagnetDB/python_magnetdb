# Data Management Plan — JNL-G

**Project**: JNL-G — Digital twin of the Laboratoire National des Champs Magnétiques Intenses-Grenoble
**Funder**: Agence Nationale de la Recherche (ANR) — call AAPG2025
**Funder template**: ANR structured DMP template on Opidor (Science Europe-based)
**Project duration**: 48 months
**Coordinator**: Christophe Trophime (LNCMI, CNRS UPR)
**Partners**: LNCMI (CNRS UPR) · UNISTRA / CEMOSIS
**Plan version**: v1.1 — initial version, integrated with EMFL DMP (within 6 months of project start)
**Next planned versions**: mid-term (T0+24) and final (T0+48)
**Related plans**: EMFL Data Management Plan — ISABEL deliverable D4.3 / final D4.4 (Horizon 2020 Grant Agreement No 871106). Identifier (HAL/DOI): *to be added*. The EMFL DMP is the parent plan for user experimental data and EMFL administrative data; the present JNL-G DMP only covers operational, simulation, code and modeling data of the LNCMI-G installation, and inherits the EMFL data-policy rules (open-by-default, CC0 default license, 5-year embargo on raw data, 10-year minimum retention).

---

## General information

### Project

- **Acronym / title.** JNL-G — Digital twin of the LNCMI-G.
- **Funder reference.** ANR AAPG2025, axe E.5 (Calcul Haute Performance, Modèles Numériques, Simulations, Applications).
- **Coordinator.** Christophe Trophime, Research Engineer, LNCMI (CNRS UPR).
- **Partner scientific leader (CEMOSIS).** Christophe Prud'homme, Professor, Université de Strasbourg.
- **Abstract.** The project develops a hierarchical digital twin (DT) of the LNCMI-G high-field magnet installation, integrating systemic models (power and cooling), full-order multiphysics models of resistive and superconducting magnets, reduced-order models, and a data layer based on operational records from the magnet control systems. The deliverables include the DT software, an operational dashboard, predictive maintenance tools, and an extended MagnetDB platform.

### Plan

- **DMP responsible.** Christophe Trophime (coordinator), supported by Kevin Paillot (WP3 LNCMI lead) and Joubine Aghili (WP3 CEMOSIS lead).
- **Reviewers.** WP4 leads (Cédric GrandClément, Christophe Prud'homme, Vincent Chabannes).
- **Update schedule.** Annual review aligned with the WP0 yearly advancement reports (T0+12, T0+24, T0+36, T0+48). Mandatory revisions submitted to the ANR at T0+24 and T0+48.
- **Identifier.** To be filled after Opidor entry.

### Contributors

| Role | Person | Affiliation | Responsibility |
|---|---|---|---|
| DMP coordinator | Christophe Trophime | LNCMI | Project-wide DMP, sections 1, 3, 4, 5, 6 |
| WP3 LNCMI lead | Kevin Paillot | LNCMI | Sections 1, 2, 3 (operational data) |
| WP3 CEMOSIS lead | Joubine Aghili | UNISTRA / CEMOSIS | Sections 1, 2 (data-driven modeling) |
| WP4 architecture lead | Christophe Prud'homme | UNISTRA / CEMOSIS | Section 3 (storage architecture) |
| Data analytics | Christiane Warth-Martin | LNCMI | Section 4 (personal data, anonymization) |

---

## Section 1 — Data description and collection or re-use of existing data

### 1.0 List of datasets

| # | Short name | Type | Origin | Owner |
|---|---|---|---|---|
| D1 | Raw operational data | Observational / instrument | Existing + new (continuous acquisition) | LNCMI |
| D2 | Curated operational data | Derived (processed) | Produced by project (T3.1) | LNCMI |
| D3 | Derived operational statistics | Derived (analytical) | Produced by project (WP3) | LNCMI |
| D4 | MagnetDB relational data | Configuration / metadata | Existing + new | LNCMI |
| D5 | Simulation & computational data | Computational | Produced by project (WP1, WP2) | LNCMI / CEMOSIS |
| D6 | Source code & software artifacts | Software | Existing + new | LNCMI / CEMOSIS |
| D7 | System models (Modelica / FMU) | Computational (model) | Produced by project (T1.1) | LNCMI |

**Scope boundary with the EMFL DMP.** This DMP covers **exclusively operational and technical data**: telemetry from the magnet control systems (Pupitre, PigBrother, Hybrid), power and cooling installation data, and energy provider data (RTE/Enedis) used for operational monitoring. It does not cover any scientist-produced measurement data. **User experimental data** (raw measurements collected by external user teams during their access campaigns) and **EMFL administrative data** (user-proposal management, access ranking, contact details of user teams) are **covered by the EMFL Data Management Plan** (ISABEL D4.3, see Related plans above). LNCMI-G inherits and applies the EMFL rules for those data; the JNL-G project does not redefine them. Where a dataset of the present DMP touches the EMFL boundary (typically through a time-window link between an operational run and a user proposal), the EMFL rule prevails on the user-side fields.

The term "data" in this DMP therefore refers to operational data from the monitoring and control systems of the installation and the magnets, archived MCS logs, simulation setup files and results, source code artifacts, and system models.

**Terminology note.** In the EMFL context, the word *experiment* designates the scientific activity of a user team using the magnet installation (governed by the EMFL DMP). In this document, the same time window is referred to as an **operational run** — the set of control-system recordings produced by the installation during that period. In the MagnetDB schema this entity is named `Record`. An operational run and the corresponding EMFL experiment share a time window and possibly a proposal reference, but contain entirely different data and are managed under different data policies. This DMP covers only the operational run (D1–D3) and its configuration metadata (D4). The word *experiment* is not used in this DMP to avoid confusion with EMFL vocabulary.

### 1.1 Re-use of existing data

The project re-uses three pre-existing assets:

- the historical archive of MCS recordings (Pupitre, PigBrother, Hybrid) accumulated by LNCMI-G operations since the deployment of each control system. The pre-existing storage state is described in the EMFL DMP §5.2 (RAID-1, per-proposal organization, technical data stored in a database every second);
- the existing MagnetDB instance (PostgreSQL + S3 object store, migrated from MinIO to RustFS at project start) and its current schema, which will be migrated to the redesigned schema (Sprint 0) at project start;
- the existing Feel++ / HiFiMagnet / MagnetTools / `python_magnetrun` codebases, used as the technical foundation for WP1, WP2 and WP4.

JNL-G is the project that **modernizes the LNCMI-G operational data layer** described in EMFL DMP §5.2: the per-second technical database is being re-engineered into the three-layer architecture of D1 / D2 / D3, with explicit curation, S3 publication, provenance, and a structured PostgreSQL backbone (D4).

No external third-party datasets are re-used at project start. External APIs (RTE, Enedis, weather) are referenced in real time during T3.1 — they are not re-distributed by the project.

### 1.2 Datasets — description, formats, expected volume

#### D1 — Raw operational data

- **Description.** Time-series recordings produced by the three control systems of the LNCMI-G installation: Pupitre (resistive magnet operation), PigBrother (cooling and power installation), Hybrid (hybrid magnet system). Acquired continuously during operations.
- **Origin.** Existing (historical archive, several years of operations) + newly produced throughout the project.
- **Format.** Native MCS files (vendor-specific binary / text-based formats inherited from each control system). No transformation is applied at this stage.
- **Sampling rate.** From 1 Hz (slow process variables) to 5 kHz (fast electrical channels).
- **Estimated volume.** Several TB of historical data + ~hundreds of GB / year of new acquisition.
- **Re-use status.** Existing format, partly retained for traceability and as fallback for D2.

#### D2 — Curated operational data

- **Description.** Selected and harmonized subset of D1, restricted to the channels relevant to the digital twin and to predictive maintenance work (WP3, WP2). Initial scope: Pupitre. PigBrother and Hybrid extensions are planned (timeline TBD — see open points).
- **Origin.** Newly produced by the project, generated by the curation pipeline implemented in T3.1.
- **Format.** Apache Parquet (columnar, compressed, partitioned by operational run / date).
- **Estimated volume.** ~10–30% of the corresponding raw volume after channel selection and compression.
- **Justification of format choice.** Parquet is interoperable, language-agnostic, supports schema evolution, and is natively consumable by Python (`pandas`, `pyarrow`, `polars`), Spark and DuckDB. It is the canonical interchange layer between LNCMI and CEMOSIS.

#### D3 — Derived operational statistics

- **Description.** Computed datasets aggregating D2: per-run statistics (`RecordStats`), derived time series (e.g. Rainflow-counted cycles, stitched trend series), cumulative statistics (`CumulativeStats`). Downsampling (LTTB) is applied at display time only; no pre-stored downsampled files.
- **Origin.** Newly produced by the project (Phase 1–3 pipelines).
- **Format.** Parquet for derived time-series payloads stored in RustFS S3 + relational rows in PostgreSQL with JSONB columns for per-run summaries.
- **Estimated volume.** A few % of D2 volume (aggregated and downsampled).

#### D4 — MagnetDB relational data

- **Description.** Configuration and metadata of the LNCMI-G assets and their use:
  - sites (housing, alimentation, pump configurations), magnets, parts;
  - geometry references, materials;
  - operational runs (`Record`) and their lifecycle: raw data file references (`sources` → D1), curated Parquet file references (`curated` → D2 in RustFS S3), run type, time bounds, operator identity;
  - links to attachments stored in S3 (CAD, mesh, computed data, simulation outputs);
  - provenance metadata for meshes, CAD and computed results.
- **Origin.** Existing (current MagnetDB) + newly produced (Sprint 0 schema redesign + ongoing entries).
- **Format.** PostgreSQL relational tables. Personal data (user identifiers used for booking / planning) are present in the operational instance but are anonymized in any export.
- **Estimated volume.** Hundreds of MB of relational data; attachments (in S3) reach the GB range.

#### D5 — Simulation and computational data

- **Description.** Inputs and outputs of HiFiMagnet / Feel++ simulations and ROM evaluations:
  - geometric setup files (CAD: STEP, BREP);
  - meshes (Gmsh `.msh`, MED, exodus);
  - field results (CSV, HDF5, EnSight, VTK / VTU);
  - computed quantities (R(I) tables, inductance matrices) stored as `ComputedData` (relational + StorageAttachment hybrid);
  - rendering artifacts (PNG plots, vtk.js scenes for the web frontend).
- **Origin.** Newly produced by the project (WP1, WP2, WP4).
- **Estimated volume.** From hundreds of MB (per simulation case) to ~100 GB (large 3D non-linear runs, mesh refinements).
- **Justification of format choice.** All formats are open, well-established standards in scientific computing and supported by the Feel++ ecosystem and ParaView.

#### D6 — Source code and software artifacts

- **Description.** Source code, documentation, container images, CI artifacts, packaged binaries.
- **Components.**
  - **MagnetDB GitHub organization** — public, open-source: `python_magnetdb`, `python_magnetgeo`, `python_magnetsetup`, `python_magnetapi`, `python_magnetrun`.
  - **Feel++ GitHub organization** — public, open-source: framework, toolboxes, HiFiMagnet, Feel++‑HTS.
  - **Restricted components**: parts of MagnetTools, hosted in private GitHub repositories. Built artifacts are distributed via the LNCMI baremetal apt depot (`.deb` packages) and a DockerHub base image (`feelpp/magnettools`).
- **Format.** Source code (C++, Python, Modelica, JS / TS), documentation (Markdown, AsciiDoc, Sphinx / Antora), OCI container images, `.deb` packages, Helm charts, Apptainer / Singularity images for HPC deployment.
- **Estimated volume.** A few GB across repositories; tens of GB for cumulative container image releases.

#### D7 — System models (Modelica / FMU)

- **Description.** Dynamic models of the LNCMI-G power supply (AC/DC converters, DC current source with PID control) and water cooling system (primary and secondary loops), developed in T1.1 for co-simulation in T1.3.
- **Origin.** Newly produced by the project. Possibly partly derived from existing internal LNCMI models, to be assessed in T1.1.
- **Format.** Modelica source (`.mo`); compiled models exported as Functional Mockup Units (FMU 2.0 for Co-Simulation).
- **Estimated volume.** Less than 100 MB of source + a few hundred MB of FMU bundles.
- **Hosting.** To be decided (open point — see §3.4).

### 1.3 Origin and methodology of new data collection

| Dataset | Method |
|---|---|
| D1 | Continuous, automated acquisition by the existing MCS during installation operation. No new instrumentation is required, although a small instrumentation budget (7 k€) covers sensor renewal. |
| D2 | Automated curation pipeline (T3.1), triggered offline on archived D1 batches and online on streaming D1. |
| D3 | Asynchronous statistics pipelines (Celery tasks) triggered after curation; shared `trigger_full_stats_pipeline()` helper used by both offline and streaming paths. |
| D4 | Manual entry through MagnetDB UI for configuration data; automatic creation by Phase 4 ingest for `Record` (operational run) rows. |
| D5 | Generated by REANA-orchestrated workflows (setup → CAD → mesh → run → archive); attached to MagnetDB through `StorageAttachment`. |
| D6 | Standard software development lifecycle on GitHub with CI/CD on GitHub Actions and project-internal runners. |
| D7 | Manual development in OpenModelica / Dymola; FMU export through standard tooling. |

### 1.4 Utility of the data outside the project

- **D1, D2, D3** — primary value to other EMFL laboratories (HFML Nijmegen, HLD Dresden) and to high-field magnet user facilities for benchmarking and predictive-maintenance studies. The FlexRICAN community is identified as a direct consumer of aggregated energy-management data.
- **D4** — schema and curated demonstration datasets are useful for any group operating instrument-centric facilities, especially those building MagnetDB-like configuration databases.
- **D5** — relevant to the magnet-design community (CERN, ITER, fusion magnet groups) and to the Feel++ user community as benchmark cases.
- **D6** — open-source contributions to Feel++, Scimba and the MagnetDB ecosystem, useful to NumPEx Exa-MA, FlexRICAN, the eye2brain project, and the broader scientific-computing community.
- **D7** — useful as a co-simulation reference for facilities studying the coupled behavior of power-cooling-load systems.

---

## Section 2 — Documentation and data quality

### 2.1 Metadata and documentation accompanying the data

- **D1.** Each raw recording is identified by its MCS-assigned filename, timestamp, and the MagnetDB `Record` (operational run) it is linked to. No external metadata standard applies; the documentation is provided through MagnetDB itself.
- **D2 / D3.** Each Parquet file carries a schema (column names, units, dtypes) embedded in its footer. Per-run `Record` rows in PostgreSQL hold processing parameters (curation version, channel selection) ensuring traceability from D2 / D3 back to D1.
- **D4.** The PostgreSQL schema is the authoritative documentation. The schema is published openly in the MagnetDB GitHub organization, version-controlled through Django migrations.
- **D5.** Meshes, CAD and computed data carry **provenance metadata** (input geometry, material properties, solver version, mesh generator parameters). The current attachment models lack systematic provenance — closing this gap is an explicit project task (`MeshAttachment`, `CadAttachment` provenance enhancement).
- **D6.** Standard software documentation: README, API reference (Sphinx / Doxygen), user manuals (Antora-based site), CHANGELOG. Releases are tagged with semantic versioning and archived on Software Heritage and Zenodo (DOI).
- **D7.** FMU `modelDescription.xml` provides interface metadata; complementary documentation describes the physical assumptions, parameters, and validation cases.

### 2.2 Metadata standards and discoverability

The project does not rely on a single external metadata standard; instead, FAIR-compliant identifiers are used wherever publication or release occurs:

- **DOI** for software releases (Zenodo) and demonstration datasets;
- **HAL** identifiers for publications;
- **ORCID** for contributors;
- **ROR** for affiliations;
- **SWHID** (Software Heritage IDentifier) for source code snapshots.

The MagnetDB schema can be exported to JSON Schema for re-use; the curated dataset bundles will be accompanied by a schema descriptor and a `README.md`.

### 2.3 Data quality control

- **D1.** Quality is assessed at acquisition by the MCS itself (out-of-range alarms, sensor health). Anomalies feed T3.2 (anomaly detection, predictive maintenance).
- **D2.** Curation pipeline performs schema validation, monotonic timestamp checks, sampling-rate consistency checks. Any rejected file is logged with a reason and made available for manual review.
- **D3.** Pipelines are deterministic and idempotent; statistical outputs are recomputable from D2. Versioning of the pipeline code is enforced through CI.
- **D5.** Verification and validation is the explicit object of T1.2 / T1.3 / T4.2 deliverables (test cases + validation reports vs. experimental data from WP3).
- **D6.** Quality is enforced through the CI/CD pipelines: unit tests, integration tests, performance benchmarks, code-style and security checks, container image scanning. The CEMOSIS-side research engineer requested in the budget is explicitly tasked with CI/CD, verification, validation and benchmarking.

---

## Section 3 — Storage and backup during the research process

### 3.1 Storage during the project — per dataset

| Dataset | Primary storage | Location | Access protocol |
|---|---|---|---|
| D1 | LNCMI NAS (sshfs export) | LNCMI-G site, Grenoble | sshfs / SSH — LNCMI internal network only |
| D2 | RustFS S3 bucket (MagnetDB instance) | LNCMI-G server room | S3 API (HTTPS) via MagnetDB; pre-signed URLs for CEMOSIS direct access |
| D3 | RustFS S3 bucket + PostgreSQL | LNCMI-G server room | S3 API + SQL via MagnetDB API |
| D4 | PostgreSQL (MagnetDB primary database) | LNCMI-G server room | MagnetDB REST/API behind LemonLDAP::NG SSO |
| D5 | RustFS S3 (attachments) referenced from PostgreSQL | LNCMI-G server room | S3 API via MagnetDB |
| D6 | GitHub (origin) + GitHub Container Registry + LNCMI apt depot + DockerHub | Distributed | git over HTTPS / SSH; OCI; HTTPS |
| D7 | TBD (see §3.4) | TBD | TBD |

The **curated Parquet layer on RustFS S3 (D2) is the canonical processed-data layer**. The sshfs-mounted raw paths (D1) are retained as fallback only; this design choice is what allows external partners (CEMOSIS) to consume project data without requiring sshfs access to the LNCMI internal network. CEMOSIS accesses D2 directly via pre-signed RustFS URLs (time-limited, read-only), which are also usable in Python notebooks (`pd.read_parquet(url)`) without installing any MagnetDB-specific tooling.

### 3.2 Volume planning

| Layer | End-of-project volume target | Growth assumption |
|---|---|---|
| D1 (raw) | 5–10 TB cumulative | ~0.5–1 TB / year of new acquisition |
| D2 (curated) | 1–3 TB cumulative | proportional to D1 acquisition |
| D3 (derived) | < 100 GB | small, dominated by aggregates |
| D4 (relational) | < 10 GB | structural / metadata growth |
| D5 (sim/comp) | 1–5 TB | dominated by 3D non-linear runs |
| D6 (code / images) | < 100 GB | container image accumulation |
| D7 (system models) | < 1 GB | small, model-source dominant |

The 10 k€ "servers / data storage" line in the LNCMI requested budget covers the procurement of additional disk capacity for the MagnetDB RustFS S3 instance to absorb D2 / D3 / D5 growth.

### 3.3 Backup strategy

- **PostgreSQL (D4) and RustFS S3 (D2, D3, D5):** daily backups managed by the LNCMI IT team, following a 3-2-1 strategy (3 copies, 2 different media, 1 offsite). Backup retention follows the LNCMI institutional policy.
- **Raw operational data (D1):** kept under the existing LNCMI backup policy, unchanged by the project.
- **Source code (D6):** distributed by design — every clone is a backup; in addition, every release is mirrored on Software Heritage and Zenodo.
- **System models (D7):** to be aligned with the chosen hosting strategy (open point).

### 3.4 Hosting decisions still open

These items are not yet fixed and will be resolved during the first six months of the project (under Task T0.1 Monitoring and Planning, in coordination with T4.1 Architecture):

1. **D7 (system models)** — choice between hosting in the MagnetDB GitHub organization, a separate Modelica-focused repository, or a partner-only distribution channel. Depends on the open-source clearance of any pre-existing internal LNCMI models that will be re-used.
2. **Demo / training datasets** (a public subset of D2 + D4) — choice of repository among Girder, data.gouv.fr, Zenodo, or a combination, depending on the size of each bundle and on DOI requirements.
3. **PigBrother and Hybrid Parquet curation (D2 extension)** — timeline for extending the Pupitre curation pipeline to the other two MCS sources.
4. **Retention policy** for raw D1 (sshfs) and for intermediate D2 versions, particularly across schema changes of the curation pipeline.

### 3.5 Data security and protection during the research

- **Authentication.** Access to MagnetDB and to the project's DT services is controlled by LemonLDAP::NG (SSO) with OIDC delegation. External partners get federated access through the same gateway.
- **Authorization.** Role-based scoping at three levels — `own` / `site` / `all` — consistent across the API, the operational dashboard, and the underlying queries.
- **Network segmentation.** Raw data on sshfs (D1) are reachable only from within the LNCMI internal network. The MagnetDB front-end (Traefik with SSL) and the curated S3 bucket are reachable externally over HTTPS, behind the SSO gateway.
- **Credentials.** Service accounts and CI tokens are managed through the LNCMI IT secrets store; rotation is performed annually or after any incident.
- **Distinct service URLs.** Docker-internal URLs (e.g., `http://lemonldap`) are kept distinct from external browser-facing URLs (e.g., `https://auth.lemon.magnetdb-dev.local`) in environment configuration.

---

## Section 4 — Legal and ethical requirements, codes of conduct

### 4.1 Personal data

- **Inheritance from the EMFL DMP.** Personal data of magnet users (user-team contacts, proposal authorship, access procedures) are governed by the **EMFL Data Management Plan** (ISABEL D4.3 §2). The EMFL DMP commits to GDPR, the EU Data Protection Law Enforcement Directive, and applicable national / regional rules; it specifies that user personal data are restricted to consortium members, used only with user consent, and that aggregated statistics are reported anonymously. The JNL-G project does not redefine these rules and complies with them.
- **JNL-G-specific scope.** The only personal data handled in addition by JNL-G are the user identifiers already present in MagnetDB (D4) — name, affiliation, contact email — used for booking, planning and access control of the LNCMI-G installation. **No experimental data and no data subject to medical, biometric or other sensitive-personal-data regulation are collected by JNL-G.**
- **GDPR compliance.** Processing is covered by the CNRS general framework and by the EMFL framework above. The project does not introduce any new processing of personal data beyond what is already declared by LNCMI / EMFL.
- **CNIL registration.** The DT authentication and access architecture (LemonLDAP::NG / OIDC) developed in WP4 — which is the **JNL-G-specific addition** to the EMFL personal-data framework — will be registered as an extension of LNCMI's existing register of processing activities prior to launch, as referred in the proposal.
- **Anonymization.** Any export of D4 outside the LNCMI internal network is anonymized: personal identifiers are replaced by opaque pseudonyms or removed entirely depending on the use case. Opaque pseudonyms are used where traceability of "user X over time" is required for analytics; full removal is used for public datasets. This is consistent with the EMFL DMP rule that personal information shall not be published.
- **Right of access / rectification / erasure.** Handled through the existing CNRS / LNCMI / EMFL procedures; the DT does not establish a separate process.

### 4.2 Intellectual property and licensing

- **Source code (D6).**
  - **Public components** of MagnetDB and Feel++: open-source, released under permissive licenses (Apache-2.0 or LGPL-3.0 depending on the component, in line with the existing licensing of those repositories). New contributions follow the licensing of the parent repository.
  - **MagnetTools and other restricted components**: kept under their existing private-repository regime; built artifacts are distributed only via the LNCMI apt depot and the `feelpp/magnettools` DockerHub image. Decision on whether parts can be open-sourced is part of the §3.4 open points.
- **Datasets.**
  - **EMFL alignment.** The EMFL DMP (ISABEL D4.3) sets **CC0 1.0 Universal** as the default license for shared datasets, on the principle of open re-use. JNL-G adopts CC0 as the default for the datasets listed below; CC-BY-4.0 is used as a fallback when attribution is required by an institutional policy.
  - **D5 demonstration cases** (a public subset, released as benchmark datasets): CC0 by default; CC-BY-4.0 if attribution is required.
  - **D2 / D3 curated datasets** released externally: CC0 by default; CC-BY-4.0 fallback. CC-BY-NC-4.0 may be considered exceptionally if the Operating Data Exchange Policy (§4.3) identifies a concern over commercial re-use of operational data of a national infrastructure — this would be a deviation from the EMFL default and must be justified.
  - **D4 schema descriptors**: CC-BY-4.0 (attribution useful for traceability of the schema itself).
- **Patentable results.** None expected at project start. Should patentable outcomes arise (e.g., a novel ROM technique or a hardware-related innovation), publication and data release on the relevant items will be delayed until the patent application stage is closed, in accordance with CNRS IP policy.
- **Database rights.** The MagnetDB instance is a database in the sense of Directive 96/9/EC; sui generis database rights are held by LNCMI. The schema is openly published; the contents follow the access regime described in §5.
- **Third-party rights.** No third-party copyrighted data are incorporated. References to external APIs (RTE, Enedis) are runtime-only.

### 4.3 Confidentiality and contractual aspects

- **Inter-partner confidentiality agreement.** A confidentiality agreement between LNCMI and UNISTRA / CEMOSIS will be signed before any operational data exchange takes place (as committed in the proposal). The agreement covers the curated subset (D2) provided for verification and validation.
- **Operating Data Exchange Policy.** A formal policy describing what subset of operational data may be released externally, in what aggregated form, and under which licence will be drafted in year 2 of the project (T0.1 / T4.1). This policy will be appended as an annex to v2 of the DMP.
- **External collaborators.** Any access by collaborators outside the consortium (e.g., visiting researchers, FlexRICAN partners, EMFL partners) is subject to a written agreement following the CNRS / Université de Strasbourg standard models.

### 4.4 Ethics and codes of conduct

- The project does not involve human subjects, animal experimentation, dual-use research, or sensitive geographic data; **no ethics committee review is required**.
- The consortium adheres to the CNRS Code of Ethics for Research and to the European Code of Conduct for Research Integrity (ALLEA).
- The project endorses the CNRS Open Science roadmap and the ANR principle "as open as possible, as closed as necessary".
- Authorship and contribution of all research outputs follow the CRediT taxonomy where applicable.

---

## Section 5 — Data sharing and long-term preservation

### 5.1 Sharing strategy — per dataset

| Dataset | Will be shared? | When | Where | License | Conditions |
|---|---|---|---|---|---|
| D1 (raw) | No | — | — | — | LNCMI-internal only |
| D2 (curated) | Partial — demo bundles | At project end (T0+48), incremental from T0+24 | Zenodo + Girder / data.gouv.fr (TBD) | CC0 (CC-BY-4.0 fallback) | Subset selected via the Operating Data Exchange Policy |
| D3 (derived) | Partial — same demo bundles | Same as D2 | Same as D2 | Same as D2 | Same as D2 |
| D4 (schema + demo content) | Yes — schema + demo contents | T0+12 (schema), T0+24 (demo) | GitHub + Zenodo | CC-BY-4.0 (content) + Apache-2.0 (schema migrations) | Personal data removed per EMFL DMP |
| D5 (sim / comp) | Partial — benchmark cases | Continuous | Zenodo + GitHub | CC0 (CC-BY-4.0 fallback) + Apache-2.0 (scripts) | Selected representative cases |
| D6 (code) | Yes — public components | Continuous (releases) | GitHub + Software Heritage + Zenodo | Apache-2.0 / LGPL-3.0 (per component) | Free re-use |
| D7 (system models) | TBD | TBD | TBD (see §3.4) | TBD | TBD |

### 5.2 Repositories — selection and trustworthiness

The repositories listed above were selected against the Science Europe criteria for trustworthy repositories: they (i) are widely adopted, (ii) provide persistent identifiers, (iii) implement long-term preservation policies, (iv) offer stable access, and (v) are recognized by the French Open Science strategy.

| Repository | Purpose | Identifier | Notes |
|---|---|---|---|
| **GitHub** | Source code primary location | URL | Mirrored to Software Heritage |
| **Software Heritage** | Code archival | SWHID | Continuous archival of public repositories |
| **Zenodo** | Software releases, demo datasets | DOI | CERN-hosted, recommended by ANR |
| **HAL** | Publications | HAL ID | French national open archive |
| **data.gouv.fr** | Public datasets | URL + DOI mirror | Considered for demo bundles, decision pending |
| **Girder** | Larger demo datasets | URL | LNCMI / community option, decision pending |

### 5.3 Embargo

The project follows the embargo rules of the **EMFL DMP** (ISABEL D4.3):

- **Raw data tied to user campaigns (out of scope here, but referenced for consistency)**: 5 years from the end of the experiment, after which data become openly accessible with the EMFL facility acting as custodian.
- **D2 / D3 / D5 demo bundles**: a short embargo (up to 12 months from the corresponding publication submission) may apply when the dataset is tied to a paper still under review. This is shorter than the EMFL 5-year rule because the project-side curated bundles are not user data.
- **D6 (code)** and **publications**: no embargo; immediate open release.
- **Patents (hypothetical)**: standard embargo until the patent application is filed, in line with CNRS IP policy.

### 5.4 Long-term preservation

The project applies the **EMFL DMP** (ISABEL D4.3) baseline of **10-year minimum retention** for raw, technical and administrative data, with longer retention for code and schema artifacts on community archives:

- **D6 (code)** — preserved indefinitely on Software Heritage and Zenodo (DOI per release).
- **D5 benchmark cases and demo bundles** — preserved on Zenodo with DOI; minimum guarantee 20 years per Zenodo policy. Exceeds the EMFL minimum.
- **D4 schema descriptors** — preserved on Zenodo + GitHub. Exceeds the EMFL minimum.
- **D2 / D3 curated demo bundles** — preserved on Zenodo and / or data.gouv.fr. Exceeds the EMFL minimum.
- **D1 raw operational data** — kept according to the LNCMI institutional retention policy; the EMFL 10-year minimum applies. A retention review (alignment between LNCMI policy and EMFL 10-year rule, plus deletion notification protocol per EMFL DMP §4) is part of the §3.4 open points.
- **D7 system models** — preservation policy aligned with the §3.4 hosting decision; minimum 10 years to remain consistent with the EMFL baseline.

After project completion, MagnetDB itself remains operated by LNCMI as part of its normal infrastructure responsibilities. The DT services developed under WP4 are integrated into the LNCMI operational systems (T4.3) and inherit LNCMI's operations and maintenance.

### 5.5 Methods and tools needed to access and re-use the data

- **D2 / D3 / D5 (Parquet, HDF5, VTK, CSV)**: any standard scientific Python (`pyarrow`, `pandas`, `h5py`) or ParaView for VTK. The README of each demo bundle lists exact dependencies and provides an example notebook.
- **D4 demo bundles**: a Docker Compose snippet shipped with the bundle reconstructs a minimal MagnetDB stack (postgres, redis, rustfs, api, jupyter) so that students and external users can browse the schema and run example queries.
- **D6 (code)**: standard build instructions in each repository's README; container images on GHCR / DockerHub; Apptainer images for HPC.
- **D7 (FMU)**: any FMI-compliant tool (OpenModelica, Dymola, Simulink, Feel++ co-simulation runner) following the FMI 2.0 standard.

### 5.6 Data utility and dissemination

The project's dissemination plan (proposal §III) directly supports the sharing strategy:

- publications in international peer-reviewed venues (Magnet Technology Conference, ICOSAHOM, ECCOMAS, ENUMATH, SIAM, IEEE Digital Twin, MAFELAP) with HAL deposit;
- engagement with the EMFL and FlexRICAN communities for adoption and re-use;
- demonstrator role within the NumPEx initiative and the Exa-MA targeted project;
- communication via LinkedIn and the project's open documentation channels.

---

## Section 6 — Data management responsibilities and resources

### 6.1 Responsibilities

| Domain | Lead | Backup | Scope |
|---|---|---|---|
| Overall DMP coordination | Christophe Trophime (LNCMI) | Christophe Prud'homme (CEMOSIS) | All datasets, plan updates, ANR liaison |
| Operational data (D1, D2, D3) | Kevin Paillot (LNCMI) | Joubine Aghili (CEMOSIS, for analytics) | Curation pipeline, statistics, predictive maintenance |
| MagnetDB platform (D4) | Christophe Trophime (LNCMI) | To-be-hired LNCMI Research Engineer | Schema, ingestion, attachments |
| Simulation data (D5) | Vincent Chabannes (CEMOSIS) | Christophe Trophime (LNCMI) | FOM / ROM outputs, attachments, provenance |
| Code & software (D6) | Vincent Chabannes (CEMOSIS) | To-be-hired CEMOSIS Research Engineer | CI/CD, releases, container images |
| System models (D7) | Benjamin Vincent (LNCMI) | — | Modelica / FMU |
| Personal data & anonymization | Christiane Warth-Martin (LNCMI) | Christophe Trophime | D4 user identifiers |
| Security & access control | Cédric GrandClément (LNCMI) | LNCMI IT team | LemonLDAP::NG, MCS interface, network |
| EMFL DMP liaison | François Debray (LNCMI) | Christophe Trophime | Interface with EMFL DMP coordination (FlexRICAN, EMFL board); alignment of JNL-G data policies with the EMFL DMP; raising deviations (e.g. licensing, retention) to the EMFL coordination team |

### 6.2 Resources allocated

The proposal explicitly budgets resources that contribute to data management:

**LNCMI side**

- *To-be-hired Research Engineer — 36 person-months* (from the 189 463 € staff line). Contributes directly to the curation and analysis pipelines of WP3 and to the DT architecture in T4.1, i.e. to the implementation of D2 / D3 / D4 / D5 management.
- *Servers / data storage — 10 k€* (within the 17 k€ instruments line). Increases RustFS S3 disk capacity for D2 / D3 / D5.
- *Subcontracting — 10 k€* covering UX improvements to the MagnetDB platform and the DT operational dashboard, both of which are user-facing components of the data management infrastructure.
- *Internal staff (permanent personnel)*. Contributions are detailed in the proposal table; the total of 71.5 PM of LNCMI staff over 48 months includes the time of all data-management leads listed in §6.1.

**CEMOSIS side**

- *Funded PhD — 36 person-months* (within the 202 826 € staff line). Develops ROM methodology with direct effect on D3 / D5 (data-driven and reduced-order representations).
- *Research Engineer — 12 person-months*. In charge of CI / CD, verification, validation and benchmarking — directly responsible for the D6 quality controls and contributes to D2 / D3 / D5 pipelines.
- *Internal staff (permanent personnel)*. Contributions of C. Prud'homme (9.6 PM), V. Chabannes (9.6 PM) and J. Aghili (7.2 PM).

**Mission and overheads**

- 8 k€ overheads on each side cover travel for project meetings, conferences and training — including DMP-related events and Opidor / NumPEx workshops.

### 6.3 Costs and cost coverage

The resources above cover all data-management activities during the 48 months of the project, including:

- storage hardware and operating costs (covered under LNCMI institutional infrastructure operations);
- backup and IT maintenance (covered under LNCMI IT services);
- repository deposit costs (Zenodo, HAL, Software Heritage are free to use);
- staff time for curation, validation, and documentation (covered under the requested ANR funding).

Long-term preservation costs after T0+48 are absorbed by LNCMI as part of its standard infrastructure responsibilities and by the long-term policies of the chosen public repositories.

### 6.4 DMP review and update

- Mid-term version (T0+24) and final version (T0+48) submitted to the ANR.
- Internal annual reviews aligned with WP0 yearly advancement reports (T0+12, T0+24, T0+36, T0+48).
- Triggered updates whenever a §3.4 open point is resolved or a new dataset emerges.

---

## Annex A — Open points to resolve

These items are tracked outside the dataset descriptions because they cut across several sections:

1. **Training datasets** for ML / ROM work (T2.3, T3.2, T3.3): scope, generation, storage — derived from CuratedData (D2) or curated independently.
2. **System models (D7, T1.1)**: hosting (MagnetDB org? separate repo?), FMU licensing, open or partner-only distribution.
3. **Demo DB hosting**: choice between Girder, data.gouv.fr, Zenodo, or a combination.
4. **PigBrother / Hybrid Parquet curation**: timeline for extending the Pupitre curated pipeline to the other two sources.
5. **Retention policy** for raw D1 and intermediate D2 versions, especially after schema changes.

All five items will be resolved before v2 of the DMP (T0+24).

## Annex B — Cross-reference with the project DMP summary

| DMP summary section | Opidor / Science Europe section | Notes |
|---|---|---|
| §1 Data summary | Section 1 | Datasets D1–D7 list |
| §2 Data sources, formats and storage | Sections 1, 2, 3 | Per-dataset description, documentation, storage |
| §3 FAIR principles | Sections 1, 2, 5 | Findability, accessibility, interoperability, re-usability addressed across the three sections |
| §4 Legal, ethical and security | Sections 3, 4 | Security in §3.5; legal & ethical in §4 |
| §5 Sharing and preservation | Section 5 | Sharing & long-term preservation |
| §6 Open points to resolve | Annex A | Tracked separately for visibility |

## Annex C — Relationship with the EMFL DMP (parent plan)

The JNL-G DMP is a **child plan** of the EMFL Data Management Plan (ISABEL deliverable D4.3, final version D4.4). The EMFL DMP covers the four EMFL facilities (LNCMI-Toulouse, LNCMI-Grenoble, HFML-RU/FOM Nijmegen, HLD-HZDR Dresden) and applies to all data produced under EMFL access campaigns.

The table below maps each DMP topic to the authoritative source — EMFL parent plan, JNL-G child plan, or both:

| Topic | Authoritative source | JNL-G addition |
|---|---|---|
| User experimental data | EMFL DMP §3, §4, §5 | None — out of scope for JNL-G |
| EMFL administrative data (proposals, user contacts) | EMFL DMP §2 | None — out of scope for JNL-G |
| User personal data (GDPR) | EMFL DMP §2 | DT auth architecture (LemonLDAP::NG / OIDC) — JNL-G specific |
| Default dataset license | EMFL DMP (CC0) | JNL-G aligns; CC-BY-4.0 fallback documented |
| Embargo on raw data | EMFL DMP (5 years) | JNL-G aligns |
| Minimum retention | EMFL DMP (10 years) | JNL-G aligns; longer where Zenodo / Software Heritage apply |
| Operational technical data of LNCMI-G | JNL-G DMP §1, §3 (D1, D2, D3, D4) | The whole project re-engineers this layer |
| Simulation and computational data | JNL-G DMP (D5) | Project-specific |
| Source code, software, system models | JNL-G DMP (D6, D7) | Project-specific |
| MagnetDB platform | JNL-G DMP §1 (D4) | Project-specific |

**Deviation policy.** Where a JNL-G choice deviates from the EMFL DMP (for instance, considering a more restrictive license such as CC-BY-NC-4.0 for a specific operational dataset under §4.2), the deviation is escalated to the EMFL coordination team (§6.1, EMFL DMP liaison) and documented in v2 of the present plan.

**Update synchronization.** Updates to the EMFL DMP (foreseen periodically beyond ISABEL) are reviewed by the JNL-G DMP coordinator at each annual revision; any change relevant to JNL-G is reflected in the next DMP version.
