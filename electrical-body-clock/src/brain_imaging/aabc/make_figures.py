"""
NeuroMotionVector figure generators — ALL driven by AGGREGATE tables + open LEMON
images, so they regenerate identically on the real AABC run (no participant-level
AABC voxels ever enter a figure; Fig N2 exemplars are synthetic per protocol §8).

Inputs (aggregate only):
  - neuromotionvector_scores.parquet   (A_brain, D_brain, z_* per visit)
  - brain_channel_clock_metrics.csv    (per-channel r, pass)
  - run_log_{planted,null}.json        (primary/secondary effect + CI + p)
  - lemon/structural_sample/*.nii.gz   (open PDDL real T1 — safe to render)

Requires figure-style skill loaded (apply_figure_style, panel_letter, META_GREY).
Call make_all(outdir, figdir, lemon_dir).
"""
import os, json, glob
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy import ndimage


def _com_axial(f, offset=0.10):
    import nibabel as nib
    d = nib.load(f).get_fdata()
    m = d > 0.1*d.max()
    cz = int(ndimage.center_of_mass(m)[2] + offset*d.shape[2])
    hi = np.percentile(d[d>0], 99.5)
    sl = np.rot90(np.clip(d,0,hi)/hi)[:, :, cz]
    ys, xs = np.where(sl > 0.05)
    if len(ys):
        sl = sl[max(0,ys.min()-8):ys.max()+8, max(0,xs.min()-8):xs.max()+8]
    return sl


def fig_lemon_real_brains(lemon_dir, meta_csv, figdir, GREY):
    import nibabel as nib
    meta = pd.read_csv(meta_csv); age_of = dict(zip(meta["ID"], meta["Age"]))
    files = sorted(glob.glob(f"{lemon_dir}/structural_sample/*.nii.gz"))
    sid = lambda f: os.path.basename(f).split("_")[0]
    yng = [f for f in files if age_of.get(sid(f)) in ("20-25","25-30")]
    old = [f for f in files if age_of.get(sid(f)) in ("60-65","65-70","70-75")]
    n = 4
    fig, axes = plt.subplots(2, n, figsize=(9, 5.4))
    for row,(grp,label) in enumerate([(yng,"Young 20–30 yr"),(old,"Older 60–75 yr")]):
        for col in range(n):
            a = axes[row,col]
            if col < len(grp):
                f = grp[col]; a.imshow(_com_axial(f), cmap="gray", vmin=0, vmax=1)
                a.set_title(f"{sid(f)} · {age_of.get(sid(f),'?')}", fontsize=8)
            a.set_xticks([]); a.set_yticks([])
            for s in a.spines.values(): s.set_visible(False)
            if col==0: a.set_ylabel(label, fontsize=10, fontweight="bold")
    fig.suptitle("Real structural MRI (LEMON) — ventricle-level axial T1", fontsize=11, y=0.99)
    fig.text(0.5,0.005,"Skull-stripped MP2RAGE 256³@1mm. Older brains: wider sulci + larger ventricles. Open PDDL data.",
             ha="center", fontsize=7.3, style="italic")
    fig.tight_layout(rect=[0,0.025,1,0.955])
    fig.savefig(f"{figdir}/fig_lemon_real_brains.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def fig_geometry(scores_pq, figdir, GREY):
    scored = pd.read_parquet(scores_pq)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4))
    a = axes[0]
    a.scatter(scored["A_brain"], scored["D_brain"], s=8, alpha=0.35, color=GREY, edgecolor="none")
    a.axhline(0,color="0.6",lw=0.8,ls="--"); a.axvline(0,color="0.6",lw=0.8,ls="--")
    r = np.corrcoef(scored["A_brain"], scored["D_brain"])[0,1]
    a.set_xlabel("A  =  shared brain-aging axis\n(mean of 4 channel age-gaps)", fontsize=9)
    a.set_ylabel("D  =  brain-channel disagreement\n(standardized Mahalanobis contrast)", fontsize=9)
    a.set_title(f"A ⊥ D by construction  (r = {r:+.2f})", fontsize=10)
    b = axes[1]
    zc = ["z_S_structure","z_M_myelin","z_P_perfusion","z_F_function"]; labels=["Structure","Myelin","Perfusion","Function"]
    hi = scored.nlargest(1,"D_brain")[zc].values.flatten()
    lo = scored.nsmallest(1,"D_brain").iloc[[0]][zc].values.flatten()
    med = scored.iloc[(scored["D_brain"]-scored["D_brain"].median()).abs().argsort()[:1]][zc].values.flatten()
    x = np.arange(4)
    b.plot(x,hi,"-o",label="high D (channels diverge)",color="#c1121f",lw=2)
    b.plot(x,med,"-o",label="median D",color=GREY,lw=1.5)
    b.plot(x,lo,"-o",label="low D (channels agree)",color="#0353a4",lw=2)
    b.axhline(0,color="0.6",lw=0.8,ls="--"); b.set_xticks(x); b.set_xticklabels(labels,fontsize=8.5)
    b.set_ylabel("standardized channel age-gap  z",fontsize=9)
    b.set_title("D captures within-person channel divergence",fontsize=10); b.legend(fontsize=7.5)
    fig.suptitle("fig_neurovector_geometry — the A/D decomposition (fixture-validated; regenerates on real AABC IDPs)",fontsize=10.5,y=1.00)
    fig.tight_layout(rect=[0,0,1,0.95])
    fig.savefig(f"{figdir}/fig_neurovector_geometry.png",dpi=200,bbox_inches="tight"); plt.close(fig)


def fig_gait_result(planted_log, null_log, figdir):
    P = json.load(open(planted_log)); N = json.load(open(null_log))
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    rows = []
    for reg,R,color in [("PLANTED (effect present)",P,"#c1121f"),("NULL (no effect)",N,"#0353a4")]:
        pr = R["primary"]
        rows.append((f"{reg}\nPRIMARY: gait-speed decline ~ D", pr["beta"], pr["ci_low"], pr["ci_high"], pr["p_value"], color))
    y = np.arange(len(rows))[::-1]
    for yi,(lab,beta,lo,hi,p,color) in zip(y,rows):
        ax.plot([lo,hi],[yi,yi],"-",color=color,lw=2.5); ax.plot(beta,yi,"o",color=color,ms=9)
        ax.text(hi+0.001, yi, f"β={beta:+.4f}  p={p:.3f}", va="center", fontsize=8.5, color=color)
    ax.axvline(0,color="0.4",lw=1.2,ls="--"); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_xlabel("β_D  (effect of baseline brain-disagreement on annualized 4-m gait-speed change)", fontsize=9)
    ax.set_title("fig_neurovector_gait_result — pipeline discriminates signal from null\n(fixture ground-truth validation; real result fills in on AABC run)", fontsize=10)
    ax.set_ylim(-0.6, len(rows)-0.2); fig.tight_layout()
    fig.savefig(f"{figdir}/fig_neurovector_gait_result.png",dpi=200,bbox_inches="tight"); plt.close(fig)


def fig_molecule_to_network(figdir):
    fig, ax = plt.subplots(figsize=(9.5, 4.0)); ax.axis("off")
    stages = [("MOLECULE","7T MRS\nNAA, Glu, GABA,\nmIns, GSH …\n(17 metabolites)","#6a4c93"),
              ("CHANNEL","4 brain-age\nclocks\nS · M · P · F","#1982c4"),
              ("GEOMETRY","A  (shared aging)\nD  (disagreement)","#8ac926"),
              ("NETWORK","Ji-2019\nfunctional\nnetworks","#ff924c"),
              ("MOVEMENT","4-m gait\nspeed decline","#c1121f")]
    n=len(stages); xs=np.linspace(0.06,0.82,n)
    for i,(title,body,color) in enumerate(stages):
        ax.add_patch(FancyBboxPatch((xs[i],0.32),0.13,0.36,boxstyle="round,pad=0.012",lw=1.5,edgecolor=color,facecolor=color+"22"))
        ax.text(xs[i]+0.065,0.63,title,ha="center",va="center",fontsize=9,fontweight="bold",color=color)
        ax.text(xs[i]+0.065,0.47,body,ha="center",va="center",fontsize=7.3)
        if i<n-1: ax.add_patch(FancyArrowPatch((xs[i]+0.13,0.50),(xs[i+1],0.50),arrowstyle="-|>",mutation_scale=16,lw=1.6,color="0.3"))
    ax.text(0.5,0.90,"fig_molecule_to_network — the NeuroMotionVector causal chain",ha="center",fontsize=11,fontweight="bold")
    ax.text(0.5,0.16,"MRS is a SECONDARY molecular anchor (gate: age r≥0.20, ≥100 QC visits). "
            "Primary chain is CHANNEL→GEOMETRY→MOVEMENT; molecule + network layers are exploratory context.",
            ha="center",fontsize=7.5,style="italic")
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    fig.savefig(f"{figdir}/fig_molecule_to_network.png",dpi=200,bbox_inches="tight"); plt.close(fig)


def fig_neuro_layers(lemon_dir, figdir):
    files = sorted(glob.glob(f"{lemon_dir}/structural_sample/*.nii.gz"))
    base = _com_axial(files[0])
    fig, axes = plt.subplots(1,4,figsize=(9.5,3.2))
    layers=[("S · Structure","cortical thickness\n+ volume + aseg","Greys_r"),
            ("M · Myelin","T1w/T2w\nmyelin map","copper"),
            ("P · Perfusion","ASL CBF + ATT","viridis"),
            ("F · Function","rsfMRI\namplitudes","magma")]
    rng=np.random.default_rng(3)
    for ax,(title,desc,cmap) in zip(axes,layers):
        ax.imshow(base,cmap="gray",vmin=0,vmax=1)
        overlay=np.ma.masked_where(base<0.15, ndimage.gaussian_filter(rng.normal(0,1,base.shape),6))
        ax.imshow(overlay,cmap=cmap,alpha=0.45)
        ax.set_title(title,fontsize=9,fontweight="bold")
        ax.text(0.5,-0.10,desc,transform=ax.transAxes,ha="center",va="top",fontsize=7.2)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
    fig.suptitle("fig_neuro_layers — four imaging channels, one brain (base = real LEMON T1; overlays schematic)",fontsize=10,y=1.02)
    fig.tight_layout(rect=[0,0.02,1,0.96])
    fig.savefig(f"{figdir}/fig_neuro_layers.png",dpi=200,bbox_inches="tight"); plt.close(fig)


def make_all(outdir, figdir, lemon_dir, meta_csv, GREY="0.5"):
    os.makedirs(figdir, exist_ok=True)
    fig_lemon_real_brains(lemon_dir, meta_csv, figdir, GREY)
    fig_geometry(f"{outdir}/neuromotionvector_scores.parquet", figdir, GREY)
    fig_gait_result(f"{outdir}/run_log_planted.json", f"{outdir.replace('planted','null')}/run_log_null.json", figdir)
    fig_molecule_to_network(figdir)
    fig_neuro_layers(lemon_dir, figdir)
