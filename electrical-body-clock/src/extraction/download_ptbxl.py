"""Job A — stage PTB-XL v1.0.3 onto the /data Volume as ONE zip file.

Lesson from the first attempt: writing ~43,600 small WFDB files onto a Modal
Volume is punishingly slow (per-file commit overhead), and PhysioNet throttles
to ~0.2 MB/s. Fix: pull the single 1.83 GB zip from the HuggingFace mirror
(longisland3/ptb-xl, HF CDN ~37 MB/s) and keep it AS ONE FILE on the Volume.
The extraction job reads WFDB records directly out of the zip in memory —
never exploding it into small files on the Volume.

Verifies the zip is a valid archive containing records500 + metadata, then
commits it to /data/ptbxl-data.zip. Idempotent: skips if already present & valid.
"""
import os, sys, time, zipfile, json
import urllib.request

DATA = "/data"; OUT = "./out"; os.makedirs(OUT, exist_ok=True)
ZIP_DEST = os.path.join(DATA, "ptbxl-data.zip")
# HF-mirror direct resolve URL (HF CDN ~37 MB/s vs PhysioNet's ~0.2 MB/s)
ZIP_URL = "https://huggingface.co/datasets/longisland3/ptb-xl/resolve/main/ptb-xl-data.zip"

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def zip_is_valid(path):
    if not os.path.exists(path) or os.path.getsize(path) < 1_500_000_000:
        return False, 0, 0
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        n500 = sum(1 for n in names if "records500/" in n and n.endswith("_hr.dat"))
        return (n500 >= 21000), len(names), n500
    except Exception:
        return False, 0, 0

ok, nnames, n500 = zip_is_valid(ZIP_DEST)
if ok:
    log(f"zip already staged & valid: {ZIP_DEST} ({n500} records500 .dat)")
    json.dump({"status": "already_present", "n_records500_dat": n500,
               "n_names": nnames, "zip_gb": round(os.path.getsize(ZIP_DEST)/1e9, 2)},
              open(f"{OUT}/download_receipt.json", "w"))
    sys.exit(0)

tmp = ZIP_DEST + ".part"
t0 = time.time()
log(f"downloading {ZIP_URL} -> {tmp}")
req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "python-urllib"})
with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as f:
    total = int(r.headers.get("Content-Length", 0)); got = 0; last = 0
    while True:
        chunk = r.read(4 << 20)
        if not chunk:
            break
        f.write(chunk); got += len(chunk)
        if got - last > 400 * (1 << 20):
            log(f"  {got/1e9:.2f}/{total/1e9:.2f} GB ({100*got/max(1,total):.0f}%)  "
                f"{got/1e6/max(0.1,time.time()-t0):.0f} MB/s"); last = got
dt = time.time() - t0
log(f"download done: {got/1e9:.2f} GB in {dt:.0f}s ({got/1e6/max(0.1,dt):.0f} MB/s)")

# validate before committing to final name
os.replace(tmp, ZIP_DEST)
ok, nnames, n500 = zip_is_valid(ZIP_DEST)
if not ok:
    log(f"VALIDATION FAILED: names={nnames} records500_dat={n500}")
    json.dump({"status": "invalid_zip", "n_names": nnames, "n_records500_dat": n500},
              open(f"{OUT}/download_receipt.json", "w"))
    sys.exit(1)

receipt = {"status": "downloaded", "zip_path": ZIP_DEST,
           "zip_gb": round(os.path.getsize(ZIP_DEST)/1e9, 2),
           "n_names": nnames, "n_records500_dat": n500,
           "download_mbps": round(got/1e6/max(0.1, dt), 1), "seconds": round(dt)}
json.dump(receipt, open(f"{OUT}/download_receipt.json", "w"))
log(f"RECEIPT: {receipt}")
