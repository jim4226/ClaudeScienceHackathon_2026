HeartVector FROZEN harness bundle (median-beat pipeline). Self-contained.
Usage:
  import sys; sys.path.insert(0,'hv_bundle'); import hv_frozen as hv
  hv.load_defs('hv_bundle/FROZEN_DISAGREEMENT_DEFINITIONS_RC2.json')
  nets = hv.load_clocks('hv_bundle/models', device='cpu')
  data,qa = hv.extract_record('<wfdb_path_no_ext>')      # or hv.extract_from_signal(sig12,fs_in)
  X = hv.masked_inputs(data)[None]                        # (1,5,12,450)
  preds = hv.infer_clocks(X, nets)                        # dict phase->age(years)
  sc = hv.score_frozen(preds, age, sex)                   # A/A_std/D/D_std/q/D3_* ; sex 1=female
VALIDATED: scorer max|Δ|=0 vs 44,832 stored Chapman rows; clocks strict-load.
AMU=59.644061 ASD=16.282862 (PTB-XL train). NO refit permitted.
