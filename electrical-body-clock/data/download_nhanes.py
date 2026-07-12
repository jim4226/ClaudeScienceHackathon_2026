#!/usr/bin/env python
"""
download_nhanes.py — fetch the NHANES 2005-2010 public-use modules and the
NCHS Public-Use Linked Mortality File used by Act II of The Electrical Body Clock.

No participant-level data are redistributed with this repository. This script
downloads them locally, in accordance with the CDC/NCHS data-use terms:
  * NHANES public-use data: https://wwwn.cdc.gov/nchs/nhanes/
  * NCHS Public-Use Linked Mortality File (2019 release):
    https://www.cdc.gov/nchs/data-linkage/mortality-public.htm

Outputs -> data/nhanes/
  {MODULE}_{D,E,F}.xpt   biomarker / questionnaire modules (SAS transport)
  MORT_{D,E,F}.dat       fixed-width linked-mortality files
"""
import os
import requests

OUT = os.path.join(os.path.dirname(__file__), "nhanes")
os.makedirs(OUT, exist_ok=True)

# NHANES continuous cycles: letter -> first calendar year of the cycle
CYCLES = {"D": "2005", "E": "2007", "F": "2009"}

# Module stems (the same stem is suffixed with the cycle letter, e.g. DEMO_D)
MODULES = [
    "DEMO",    # demographics (age, sex, race, PIR, survey design)
    "BIOPRO",  # standard biochemistry: renal + hepatic + glucose + uric acid
    "CBC",     # complete blood count: hematologic + WBC differential
    "CRP",     # C-reactive protein (inflammation)
    "GHB",     # glycohemoglobin (HbA1c)
    "TCHOL",   # total cholesterol
    "HDL",     # HDL cholesterol
    "TRIGLY",  # triglycerides + LDL (fasting subsample)
    "BPX",     # blood pressure
    "BMX",     # body measures (BMI, waist)
    "MCQ",     # medical conditions questionnaire
    "DIQ",     # diabetes questionnaire
    "BPQ",     # blood-pressure / cholesterol dx + medication
    "KIQ_U",   # kidney conditions
    "SMQ",     # smoking
    "ALQ",     # alcohol
]

MORT_BASE = ("https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/"
             "linked_mortality/NHANES_{yr0}_{yr1}_MORT_2019_PUBLIC.dat")
MORT_YEARS = {"D": ("2005", "2006"), "E": ("2007", "2008"), "F": ("2009", "2010")}


def download(url, path, timeout=180):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return os.path.getsize(path)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return len(r.content)


def main():
    # Modules
    for stem in MODULES:
        for letter, yr in CYCLES.items():
            fn = f"{stem}_{letter}"
            url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{yr}/DataFiles/{fn}.xpt"
            path = os.path.join(OUT, f"{fn}.xpt")
            try:
                sz = download(url, path)
                print(f"OK   {fn:12s} {sz:>10,} B")
            except Exception as e:
                print(f"MISS {fn:12s} {type(e).__name__}: {e}")

    # Linked mortality
    for letter, (y0, y1) in MORT_YEARS.items():
        url = MORT_BASE.format(yr0=y0, yr1=y1)
        path = os.path.join(OUT, f"MORT_{letter}.dat")
        try:
            sz = download(url, path)
            n = sum(1 for _ in open(path))
            print(f"OK   MORT_{letter}      {sz:>10,} B  ({n} rows)")
        except Exception as e:
            print(f"MISS MORT_{letter}      {type(e).__name__}: {e}")

    print(f"\nDone. Files in {OUT}/")


if __name__ == "__main__":
    main()
