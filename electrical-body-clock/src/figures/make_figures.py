"""
Paper figures for The Electrical Body Clock (Act I). Run after analyze_clocks.py.
Fig 1: clock performance (MAE + R2) per subsystem vs whole-beat baseline
Fig 2: age-gap correlation heatmap (are the four clocks independent?)
Fig 3: disease-substrate matrix (Cohen's d heatmap) with hypothesised-substrate boxes
"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import matplotlib.patches as mpatches
try:
    apply_figure_style()
except NameError:
    plt.rcParams.update({"figure.dpi":150,"font.size":10})

M="drive_staging/ptbxl/models"
CLK={"p":"Atrial\n(P)","pr":"AV cond.\n(PR)","qrs":"Ventricular\n(QRS)","stt":"Repol.\n(ST-T)","whole":"Whole\nbeat"}
COLS={"p":"#4C72B0","pr":"#55A868","qrs":"#C44E52","stt":"#8172B3","whole":"#7f7f7f"}
GROUP_LAB={"atrial_disease":"Atrial disease","av_conduction_disease":"AV conduction",
  "ventricular_conduction_disease":"Vent. conduction","hypertrophy":"Hypertrophy",
  "ischemia_or_stt_abnormality":"Ischemia/ST-T","myocardial_infarction":"Myocardial infarction"}
PRIMARY={"atrial_disease":"p","av_conduction_disease":"pr",
  "ventricular_conduction_disease":"qrs","hypertrophy":"qrs",
  "ischemia_or_stt_abnormality":"stt","myocardial_infarction":"stt"}

def fig_performance():
    perf=pd.read_csv(f"{M}/clock_performance.csv").set_index("clock")
    order=["whole","p","pr","qrs","stt"]; order=[o for o in order if o in perf.index]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(10,4))
    x=range(len(order))
    a1.bar(x,[perf.loc[o,"MAE"] for o in order],color=[COLS[o] for o in order],alpha=0.85)
    a1.set_xticks(x); a1.set_xticklabels([CLK[o] for o in order],fontsize=8.5)
    a1.set_ylabel("Test MAE (years)"); a1.set_title("(a) Age-prediction error per subsystem",fontsize=10)
    for i,o in enumerate(order): a1.text(i,perf.loc[o,"MAE"],f"{perf.loc[o,'MAE']:.1f}",ha="center",va="bottom",fontsize=8)
    a2.bar(x,[perf.loc[o,"R2"] for o in order],color=[COLS[o] for o in order],alpha=0.85)
    a2.set_xticks(x); a2.set_xticklabels([CLK[o] for o in order],fontsize=8.5)
    a2.set_ylabel("R² (predicted vs chronological)"); a2.set_title("(b) Variance explained",fontsize=10)
    for i,o in enumerate(order): a2.text(i,perf.loc[o,"R2"],f"{perf.loc[o,'R2']:.2f}",ha="center",va="bottom",fontsize=8)
    fig.suptitle("Electrical Body Clock — subsystem age prediction (PTB-XL test set)",fontsize=11,y=1.02)
    fig.tight_layout(); fig.savefig(f"{M}/fig1_performance.png",dpi=150,bbox_inches="tight"); plt.close(fig)

def fig_gapcorr():
    C=pd.read_csv(f"{M}/gap_correlation.csv",index_col=0)
    fig,ax=plt.subplots(figsize=(5,4.3))
    im=ax.imshow(C.values,cmap="RdBu_r",vmin=-1,vmax=1)
    ax.set_xticks(range(len(C))); ax.set_yticks(range(len(C)))
    labs=[CLK[c].replace("\n"," ") for c in C.columns]
    ax.set_xticklabels(labs,rotation=30,ha="right",fontsize=8); ax.set_yticklabels(labs,fontsize=8)
    for i in range(len(C)):
        for j in range(len(C)):
            ax.text(j,i,f"{C.values[i,j]:.2f}",ha="center",va="center",
                    color="white" if abs(C.values[i,j])>0.5 else "black",fontsize=8.5)
    ax.set_title("(c) Subsystem age-gap correlation",fontsize=10)
    fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04,label="Pearson r")
    fig.tight_layout(); fig.savefig(f"{M}/fig2_gapcorr.png",dpi=150,bbox_inches="tight"); plt.close(fig)

def fig_substrate():
    D=pd.read_csv(f"{M}/substrate_matrix_d.csv",index_col=0)
    P=pd.read_csv(f"{M}/substrate_matrix_p.csv",index_col=0)
    fig,ax=plt.subplots(figsize=(6.5,5))
    vmax=np.nanmax(np.abs(D.values))
    im=ax.imshow(D.values,cmap="RdBu_r",vmin=-vmax,vmax=vmax,aspect="auto")
    ax.set_xticks(range(len(D.columns))); ax.set_xticklabels([CLK[c].replace("\n"," ") for c in D.columns],fontsize=8.5)
    ax.set_yticks(range(len(D.index))); ax.set_yticklabels([GROUP_LAB[g] for g in D.index],fontsize=8.5)
    for i,g in enumerate(D.index):
        for j,c in enumerate(D.columns):
            v=D.values[i,j]; pv=P.values[i,j]
            star="*" if pv<0.001 else ("·" if pv<0.05 else "")
            ax.text(j,i,f"{v:.2f}{star}",ha="center",va="center",
                    color="white" if abs(v)>vmax*0.5 else "black",fontsize=8)
        # box the hypothesised primary substrate
        jp=list(D.columns).index(PRIMARY[g])
        ax.add_patch(mpatches.Rectangle((jp-0.5,i-0.5),1,1,fill=False,edgecolor="black",lw=2.2))
    ax.set_title("Disease-substrate specificity matrix\n(Cohen's d of age-gap: cases vs controls; boxes = hypothesised primary substrate)",fontsize=9.5)
    fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04,label="Cohen's d (age-gap inflation)")
    fig.tight_layout(); fig.savefig(f"{M}/fig3_substrate_matrix.png",dpi=150,bbox_inches="tight"); plt.close(fig)

if __name__=="__main__":
    fig_performance(); fig_gapcorr(); fig_substrate()
    print("saved fig1_performance.png, fig2_gapcorr.png, fig3_substrate_matrix.png")
