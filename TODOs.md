Fixes / Features:
- [ ] magnettools: 
  - [x] update opt2ymlto produce yaml files according to newscheme
  - [ ] magnettools: encapsulate python bindings to support for logging
- [x] python_magnetgeo: 
  - [x] add default values for inner and outer bore in Insert, Bitters, Supras
- [ ] magnetdb-webapp: 
  - [x] validate visualisation
  - [ ] make view for records attached to site a list that can be expanded (accordeon), and same for other similar stuff
- [ ] magnetdb: 
  - [ ] add site_screen.py like site_magnet.py to deal with screens in msite
  - [ ] add list of screens in site view

For students:
- [x] seed inserts, bitters and at least an existing site
  - [x] add Bitters (seeds-Bitters)
  - [x] add inserts (seed-M19061901, seed-M19071101)
  - [x] add at least one existing site (seed-M19061901, seed-M19071101)
- [ ] magnetapi
  - [ ] show ring to get an example for ring.json
  - [ ] do the same for Bitters
  - [ ] Test mass import
- [ ] Prepare dataset for students
  - [ ] add more records to the dataset (see seed-records)
  - [ ] get pupitre, pigbrother data for existing sites -- use magnetrun analysis in fry mode to get names of files to store
  - [ ] get config for existing sites
  - [ ] need for yaml files for geometry??
  - [ ] for ETL need probes or at least keys () dicts for magnetrun branch XX
- [ ] Magnetrun
  - [ ] test
- [ ] Magnetsetup
  - [ ] test
- [ ] magnetworkflows
  - [ ] Validate testsuite with separate cooling models
- [ ] dev environment
  - [ ] setup a jupyterlab docker (see python_magnetrun)
  - [ ] setup a marimo docker
  - [ ] check [2026 feelpp projects](https://feelpp.github.io/course-project/csmi/2026/m1-s2/topics)

Roadmap:
- [ ] magnetdb:
  - [ ] Add housing to site model
  - [ ] Start Phase 0
