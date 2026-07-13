"""Borzoi variant-effect scoring for SKELETOME HAR substitutions.
For each substitution: extract a 524,288-bp hg38 window centered on the variant,
one-hot encode ref and alt, run both through Borzoi, and compare predicted
accessibility over central bins in skeletal-lineage vs neural tracks.
GDF5/GROW1 blind positive control: expect derived (alt) allele REDUCES activity.

Inputs (in workdir):
  manifest.tsv   - substitution manifest (har_id,chrom,pos_hg38,ref,alt,is_control,...)
  /assets/hg38.fa (+ .fai)   - reference genome (mounted volume)
  Borzoi weights via HF_HOME=/assets/hf (mounted volume)
Outputs:
  out/borzoi_scores.csv  - per-variant skeletal/neural deltas + GDF5 flag
  out/progress.json      - checkpoint
"""
import os, json, time, sys
import numpy as np, pandas as pd
import torch

SEQLEN = 524288
# Borzoi predicts the central 6144 bins x 32bp = 196608 bp; variant at center -> bin 3072
OUT_BINS = 6144
BINSIZE = 32
CENTER_BIN = OUT_BINS // 2          # 3072
BIN_FLANK = 16                       # +/-16 bins = +/-512 bp around the variant
ASSETS = os.environ.get("ASSETS", "/assets")
os.environ.setdefault("HF_HOME", f"{ASSETS}/hf")

import pysam
from borzoi_pytorch import Borzoi
from borzoi_pytorch.pytorch_borzoi_model import TRACKS_DF

# ---- track index selection (recomputed here so job is self-contained) ----
desc = TRACKS_DF["description"].astype(str)
is_acc = desc.str.contains(r"DNASE|ATAC", case=False)
skel = desc.str.contains(r"osteoblast|chondro|mesenchym|MSC|\blimb\b|arm bone|leg bone|forelimb|hindlimb|skeletal muscle|stromal cell of bone", case=False)
immune = desc.str.contains(r"CD34|pDC|GMP|Mega|Bone Marrow CD34", case=False)
SKEL_IDX = TRACKS_DF[is_acc & skel & ~immune]["index"].to_numpy()
NEURAL = is_acc & desc.str.contains(r"neural|neuron|brain|cortex|astrocyte|SK-N|forebrain|hindbrain", case=False)
NEURAL_IDX = TRACKS_DF[NEURAL]["index"].to_numpy()
print(f"skeletal tracks={len(SKEL_IDX)} neural tracks={len(NEURAL_IDX)}", flush=True)

ONEHOT = {"A":0,"C":1,"G":2,"T":3}
def onehot(seq):
    x = np.zeros((4, len(seq)), dtype=np.float32)
    for i,b in enumerate(seq):
        j = ONEHOT.get(b.upper(), -1)
        if j>=0: x[j,i]=1.0
    return x

def make_window(fa, chrom, pos1, allele):
    """pos1 = 1-based variant position; returns one-hot (4,SEQLEN) with `allele` at center."""
    center0 = pos1 - 1
    start = center0 - SEQLEN//2
    end = start + SEQLEN
    # clamp to chrom bounds with N-padding
    clen = fa.get_reference_length(chrom)
    s = max(start,0); e = min(end,clen)
    seq = fa.fetch(chrom, s, e).upper()
    # pad
    left = s-start; right = end-e
    seq = ("N"*left) + seq + ("N"*right)
    seq = list(seq)
    # place allele at center index SEQLEN//2
    ci = SEQLEN//2
    seq[ci] = allele
    return onehot("".join(seq))

def score_pair(model, fa, chrom, pos1, ref, alt, dev):
    xr = make_window(fa, chrom, pos1, ref)
    xa = make_window(fa, chrom, pos1, alt)
    xb = torch.from_numpy(np.stack([xr,xa])).to(dev)          # float32 in; autocast handles precision
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16):
        out = model(xb)                       # (2, tracks, 6144)
    out = out.float().cpu().numpy()
    lo, hi = CENTER_BIN-BIN_FLANK, CENTER_BIN+BIN_FLANK
    # summed signal over central bins per track
    ref_sig = out[0][:, lo:hi].sum(axis=1)    # (tracks,)
    alt_sig = out[1][:, lo:hi].sum(axis=1)
    delta = alt_sig - ref_sig                 # derived - ancestral
    def grp(idx):
        d = delta[idx]
        r = ref_sig[idx]; a = alt_sig[idx]
        return float(d.mean()), float(np.log2((a.sum()+1)/(r.sum()+1)))
    skel_d, skel_lr = grp(SKEL_IDX)
    neur_d, neur_lr = grp(NEURAL_IDX)
    return skel_d, skel_lr, neur_d, neur_lr

def main():
    dev = "cuda"
    man = pd.read_csv("manifest.tsv", sep="\t")
    print(f"variants: {len(man)}", flush=True)
    fa = pysam.FastaFile(f"{ASSETS}/hg38.fa")
    model = Borzoi.from_pretrained("johahi/borzoi-replicate-0").to(dev).eval()
    os.makedirs("out", exist_ok=True)
    rows=[]; t0=time.time()
    for i,r in man.iterrows():
        ch = r["chrom"] if str(r["chrom"]).startswith("chr") else f"chr{r['chrom']}"
        try:
            sd, slr, nd, nlr = score_pair(model, fa, ch, int(r["pos_hg38"]), r["ref"], r["alt"], dev)
            rows.append({**r.to_dict(), "skel_delta":sd, "skel_log2r":slr,
                         "neural_delta":nd, "neural_log2r":nlr,
                         "skel_minus_neural":sd-nd})
        except Exception as e:
            rows.append({**r.to_dict(), "error":str(e)[:120]})
        if (i+1)%50==0:
            pd.DataFrame(rows).to_csv("out/borzoi_scores.csv", index=False)
            json.dump({"done":int(i+1),"total":len(man),"sec":time.time()-t0},
                      open("out/progress.json","w"))
            print(f"{i+1}/{len(man)} {(i+1)/(time.time()-t0):.2f} var/s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("out/borzoi_scores.csv", index=False)
    # report GDF5 controls
    ctrl = df[df.get("is_control")==True]
    print("\n=== GDF5 CONTROLS ===", flush=True)
    for _,c in ctrl.iterrows():
        sd = c.get('skel_delta'); sl = c.get('skel_log2r')
        sd_s = f"{sd:+.4f}" if pd.notna(sd) else "NA"
        sl_s = f"{sl:+.4f}" if pd.notna(sl) else "NA"
        print(f"  {c.get('control_name')}: skel_delta={sd_s} skel_log2r={sl_s} "
              f"(expect negative for GROW1 derived)", flush=True)
    print(f"\nDONE {len(df)} variants in {time.time()-t0:.0f}s", flush=True)

if __name__=="__main__":
    main()
