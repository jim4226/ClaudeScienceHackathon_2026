#!/usr/bin/env bash
# SKELETOME — data acquisition
# ---------------------------------------------------------------------------
# Downloads (or, for the 9 GB phyloP bigWig, DOES NOT download — see note) every
# external input listed in DATA_MANIFEST.md. Idempotent: skips files already present.
#
# Design rules (match DATA_MANIFEST.md):
#   * hg38 is the reference build. hg19 Whalen/Pollard is lifted later (Phase 1).
#   * The 9 GB Zoonomia phyloP bigWig is NEVER fully downloaded by default. pyBigWig
#     streams it over HTTP by position (see code/phylop.py). Pass --full-phylop only
#     if you deliberately want a local 9 GB copy.
#   * ENCODE download URLs 307-redirect to signed S3 — always use `curl -L`.
#   * Anything marked TODO in the manifest is a guarded, clearly-labelled stub here.
#
# Usage:
#   bash code/download.sh                 # core small files (default)
#   bash code/download.sh --chrombpnet    # + ENCODE ChromBPNet model tarballs (§6)
#   bash code/download.sh --genome        # + hg38 FASTA (~940 MB) + chrom.sizes (§10)
#   bash code/download.sh --full-phylop   # + full 9 GB phyloP bigWig (usually DON'T)
#   bash code/download.sh --all           # everything except --full-phylop
#   bash code/download.sh --all --full-phylop
#
# Env:
#   DATA_DIR   target dir (default: ./data)
#   ALPHA_GENOME_API_KEY  required at SCORING time, not download time (see note at end).
# ---------------------------------------------------------------------------
set -euo pipefail

DATA_DIR="${DATA_DIR:-./data}"
DO_CHROMBPNET=0
DO_GENOME=0
DO_FULL_PHYLOP=0

for arg in "$@"; do
  case "$arg" in
    --chrombpnet)   DO_CHROMBPNET=1 ;;
    --genome)       DO_GENOME=1 ;;
    --full-phylop)  DO_FULL_PHYLOP=1 ;;
    --all)          DO_CHROMBPNET=1; DO_GENOME=1 ;;
    -h|--help)      grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$DATA_DIR"/{hars,substitutions,constraint,chains,chrombpnet,gwas,genome,controls}
cd "$DATA_DIR"

# ---- helpers ---------------------------------------------------------------
# fetch <url> <outfile> [curl-extra-args...]  -- skip if present & non-empty
fetch() {
  local url="$1"; local out="$2"; shift 2
  if [[ -s "$out" ]]; then
    echo "[skip] $out already present"; return 0
  fi
  echo "[get ] $out"
  # -L follow redirects (ENCODE S3), --fail on HTTP errors, -C - resume, retry
  curl -L --fail --retry 3 --retry-delay 5 -C - -o "$out" "$@" "$url"
}

todo() { echo "[TODO] $*  -- see DATA_MANIFEST.md; resolve in Claude Science, do not fabricate."; }

echo "== SKELETOME download into $(pwd) =="

# ===========================================================================
# §5  liftOver chain hg19 -> hg38   [VERIFIED LIVE, ~222 KB]
# ===========================================================================
fetch "https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz" \
      "chains/hg19ToHg38.over.chain.gz"

# ===========================================================================
# §4  Zoonomia RoCCs mask (hg38)   [VERIFIED LIVE, ~4.7 MB gzip BED]
# ===========================================================================
fetch "https://cgl.gi.ucsc.edu/data/cactus/zoonomia-2021-track-hub/hg38/RoCCs.bed.gz" \
      "constraint/RoCCs.bed.gz"

# ===========================================================================
# §3  Zoonomia 241-way phyloP bigWig (hg38, 9.0 GB)
#     DEFAULT = DO NOT DOWNLOAD. Stream by position via pyBigWig over HTTP.
# ===========================================================================
PHYLOP_URL="https://hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way/hg38.cactus241way.phyloP.bw"
if [[ "$DO_FULL_PHYLOP" -eq 1 ]]; then
  echo "[warn] Downloading the FULL 9 GB phyloP bigWig (you passed --full-phylop)."
  fetch "$PHYLOP_URL" "constraint/hg38.cactus241way.phyloP.bw"
else
  echo "[note] Skipping 9 GB phyloP bigWig by design."
  echo "       pyBigWig reads it remotely by position (HTTP range). Recipe:"
  echo "         import pyBigWig; bw = pyBigWig.open(\"$PHYLOP_URL\")"
  echo "         bw.values(\"chr20\", pos, pos+1)[0]   # single-base phyloP, no full download"
  # Persist the URL so downstream code has a single source of truth.
  echo "$PHYLOP_URL" > constraint/PHYLOP_BIGWIG_URL.txt
fi

# ===========================================================================
# §2a  Whalen & Pollard HAR MPRA — GEO GSE110760 (hg19; TSVs inside RAW.tar, ~661 MB)
#      Only the small annotation/variant TSVs are needed; the tar is large.
#      GEO suppl file path pattern:
#        https://ftp.ncbi.nlm.nih.gov/geo/series/GSE110nnn/GSE110760/suppl/GSE110760_RAW.tar
# ===========================================================================
GSE_URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE110nnn/GSE110760/suppl/GSE110760_RAW.tar"
if [[ -s "substitutions/GSE110760_RAW.tar" ]]; then
  echo "[skip] substitutions/GSE110760_RAW.tar already present"
else
  echo "[get ] GSE110760_RAW.tar (~661 MB) — extract only the variant/annotation TSVs after."
  # Guarded: this URL pattern is the standard GEO layout. If it 404s, use the
  # acc.cgi 'download' links at https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE110760
  curl -L --fail --retry 3 --retry-delay 5 -C - \
       -o "substitutions/GSE110760_RAW.tar" "$GSE_URL" \
    || todo "GSE110760_RAW.tar direct fetch failed — confirm suppl URL on the GEO acc.cgi page"
  if [[ -s "substitutions/GSE110760_RAW.tar" ]]; then
    echo "[info] Listing tar (do not extract everything; grab variant/annotation TSVs only):"
    tar -tf "substitutions/GSE110760_RAW.tar" | head -n 50 || true
    todo "Identify + extract the TSV enumerating human-specific substitutions (chrom,pos,ref,alt,ancestral)"
  fi
fi

# ===========================================================================
# §1  zooHARs Table S1 (Keough 2023, Science abm1696; hg38)  [TODO exact suppl URL]
#     science.org supplement is paywalled to automated fetch; Zenodo 7478724 is open.
# ===========================================================================
todo "zooHAR Table S1: download the supplement from science.org (doi:10.1126/science.abm1696) OR"
todo "  the open Zenodo archive 7478724 (AcceleratedRegionsNF), then export har.bed (chrom start end har_id)."
# Placeholder so downstream code fails loudly rather than silently:
[[ -s "hars/har.bed" ]] || echo "[note] hars/har.bed not yet built — Phase 1 must create it from Table S1."

# ===========================================================================
# §10  Reference genome hg38 (optional; needed for ChromBPNet + allele lookups)
# ===========================================================================
if [[ "$DO_GENOME" -eq 1 ]]; then
  fetch "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes" \
        "genome/hg38.chrom.sizes"
  fetch "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz" \
        "genome/hg38.fa.gz"
  if [[ -s "genome/hg38.fa.gz" && ! -s "genome/hg38.fa" ]]; then
    echo "[info] gunzip hg38.fa.gz"; gunzip -k "genome/hg38.fa.gz"
  fi
else
  echo "[note] Skipping hg38 FASTA (pass --genome). Needed for ChromBPNet --genome + allele lookups."
fi

# ===========================================================================
# §6  ENCODE ChromBPNet skeletal model tarballs (optional enrichment layer)
#     URLs 307-redirect to signed S3 — curl -L required (fetch() already does).
# ===========================================================================
if [[ "$DO_CHROMBPNET" -eq 1 ]]; then
  # MSC (H1-MSC) weights  [VERIFIED LIVE: redirect + tarball served]
  fetch "https://www.encodeproject.org/files/ENCFF640AVL/@@download/ENCFF640AVL.tar.gz" \
        "chrombpnet/ENCFF640AVL_msc.tar.gz"
  # MG63 osteosarcoma weights  [VERIFIED META]
  fetch "https://www.encodeproject.org/files/ENCFF841SWM/@@download/ENCFF841SWM.tar.gz" \
        "chrombpnet/ENCFF841SWM_mg63.tar.gz"
  # Limb DNase model: annotation ENCSR138OCE listed NO downloadable files this session.
  todo "Limb ChromBPNet .h5: ENCSR138OCE annotation page had no files. Find the model file under"
  todo "  the linked experiment ENCSR818JGZ (or a sibling file accession) at encodeproject.org, then"
  todo "  save as chrombpnet/limb_ENCSR138OCE.tar.gz. Also confirm ENCSR858EVI (2nd limb) files."
  # Extract nobias models for variant-scorer (--model chrombpnet_nobias.h5):
  for t in chrombpnet/*.tar.gz; do
    [[ -e "$t" ]] || continue
    d="${t%.tar.gz}"; mkdir -p "$d"
    tar -xzf "$t" -C "$d" || todo "extract $t"
  done
  echo "[info] After extraction, locate each chrombpnet_nobias.h5 for src/variant_scoring.py --model"
else
  echo "[note] Skipping ChromBPNet models (pass --chrombpnet). Optional layer, gated by hour-1 smoke test."
fi

# ===========================================================================
# §7  GO 2.0 Osteoarthritis GWAS + SuSiE credible sets (GRCh38)  [TODO exact URL]
#     Portal go-20-gwas sub-path 404'd this session; resolve via GWAS Catalog / paper.
# ===========================================================================
todo "OA GWAS credible sets (Hatzikotoulas 2025, Nature s41586-025-08771-z):"
todo "  1) GWAS Catalog: find GCST accession(s), then FTP"
todo "     https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST<xxx>/"
todo "  2) or the paper Data-Availability (Zenodo/portal) for SuSiE credible-set TSVs"
todo "  3) or repo https://github.com/hmgu-itg/Genetics-of-Osteoarthritis-2.0"
todo "  Save credible sets -> gwas/oa_credible_sets.tsv (confirm columns: credible_set_id,variant_id,chr,pos,pip,...)"

# ---- §7b supporting skeletal GWAS (optional) ----
# Morris 2019 eBMD — GCST006979 page showed no sumstats this session; verify accession first.
todo "Morris 2019 eBMD sumstats: verify correct GCST (GCST006979 showed 'not available'); GRCh38 harmonised"
todo "  at ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/<GCST>/ (*.h.tsv.gz), or GEFOS www.gefos.org"
# Yengo 2022 height (GIANT) — bulk, GRCh37; only if height annotation used.
echo "[note] Yengo 2022 height (GIANT): https://giant-consortium.web.broadinstitute.org/GIANT_consortium_data_files (optional)"

# ===========================================================================
# §9  To 2024 embryonic skeletal multiome — E-MTAB-14385 (STRETCH ONLY; large)
# ===========================================================================
todo "E-MTAB-14385 multiome (STRETCH only): enumerate file accessions at"
todo "  https://www.ebi.ac.uk/biostudies/studies/E-MTAB-14385 before downloading (GBs). Do NOT auto-pull."

# ===========================================================================
# §8  GDF5 controls — not a download; write the frozen control table.
# ===========================================================================
CTRL="controls/controls.tsv"
if [[ ! -s "$CTRL" ]]; then
  cat > "$CTRL" <<'TSV'
chrom	pos_hg38	ref_ancestral	alt_human	rsid	is_control	notes
chr20	35364817	.	.	rs4911178	GDF5-GROW1	hip; expect derived REDUCES activity ~0.72x (Capellini 2017); fill ref/alt from hg38+source
chr20	35319358	.	.	rs6060369	GDF5-R4	knee; expect derived reduces activity
chr20	35437976	.	.	rs143384	none	GDF5 5'UTR OA SNP; annotate
TSV
  echo "[info] Wrote frozen $CTRL (HACNS1/GBX2 + negative controls: add in Phase 0 with coords)."
  todo "Fill ref_ancestral/alt_human for controls from hg38 FASTA + source polarization; add HACNS1 + negatives."
fi

echo
echo "== done. Notes =="
echo " * AlphaGenome (PRIMARY engine) is API-only — no bulk download. Set ALPHA_GENOME_API_KEY and call"
echo "   dna_client.create(\$ALPHA_GENOME_API_KEY) at scoring time (Phase 3). Register:"
echo "   https://deepmind.google.com/science/alphagenome"
echo " * phyloP stays remote (9 GB) unless you passed --full-phylop."
echo " * Resolve every [TODO] above before Phase 1/3/5 — see DATA_MANIFEST.md Open TODOs."
