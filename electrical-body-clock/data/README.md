# Data

**No participant-level data are stored in this repository.** Both datasets are
openly available under their own data-use agreements; the scripts here download
and preprocess them into this directory (which is `.gitignore`d).

## Act I — PTB-XL (PhysioNet)
```bash
python data/download_ptbxl.py        # -> data/ptbxl/
```
Downloads PTB-XL v1.0.3 (21,799 clinical 12-lead ECGs, 500 Hz, 10 s) from
PhysioNet. See <https://physionet.org/content/ptb-xl/>.

- Citation: Wagner et al. (2020), *Sci Data* 7:154,
  <https://doi.org/10.1038/s41597-020-0495-6>
- Distributed via PhysioNet: Goldberger et al. (2000), *Circulation* 101(23):e215,
  <https://doi.org/10.1161/01.CIR.101.23.e215>

## Act II — NHANES 2005–2010 + linked mortality (CDC / NCHS)
```bash
python data/download_nhanes.py       # -> data/nhanes/
```
Downloads the NHANES continuous cycles 2005–2006, 2007–2008, 2009–2010
(public-use XPT modules) and the NCHS Public-Use Linked Mortality File
(2019 release, fixed-width `.dat`).

- NHANES: <https://wwwn.cdc.gov/nchs/nhanes/>
- Linked Mortality File: <https://www.cdc.gov/nchs/data-linkage/mortality-public.htm>

After downloading, build the merged analysis table:
```bash
python src/nhanes/build_master.py    # -> data/nhanes/master.parquet
```

## Data-use terms
Use of these data is governed by the PhysioNet Credentialed/Open Data Use
Agreement (PTB-XL) and the NCHS public-use and linked-mortality terms (NHANES).
By downloading you agree to those terms. Do **not** attempt to re-identify
participants or redistribute participant-level records.
