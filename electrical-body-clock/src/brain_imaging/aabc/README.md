# NeuroMotionVector source

This folder contains the analysis scripts used for the AABC NeuroMotionVector
extension.

- `neuromotionvector_pipeline.py`: clock training, frozen geometry, and model
  analysis pipeline.
- `run_pipeline.py`: command-line execution entry point.
- `prepare_demographics.py`: controlled-environment demographic preparation.
- `make_figures.py`: figure generation from analysis outputs.
- `make_fixture.py`: synthetic fixture generation for public pipeline checks.

The scripts do not contain AABC data, participant identifiers, credentials, or
machine-specific home paths. Running the real-data path requires independently
authorized AABC access and compliance with its data-use agreement. Only
disclosure-safe aggregate outputs are published under
`../../../results/brain_imaging/aabc_aggregates/`.
