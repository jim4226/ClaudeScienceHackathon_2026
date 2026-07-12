"""The Electrical Body Clock — ECG subsystem aging clocks.

NeuroKit2 DWT delineation + wfdb I/O + torch 1D-CNN age regressors.
CPU is used for waveform extraction; GPU (A10G default) for training.
One persistent Volume `ptbxl-data` at /data holds raw waveforms,
extracted tensors, and job outputs across jobs.
"""

import modal

META = {
    "packages": [
        "torch", "neurokit2", "wfdb", "scipy", "scikit-learn",
        "statsmodels", "pandas", "numpy", "tqdm", "pyarrow", "matplotlib",
    ],
    "gpu_default": "A10G",
    # physionet.org declared as a job-time fallback; the canonical path
    # stages waveforms into the Volume from the compute_provider kernel,
    # so extraction/training jobs need no network.
    "egress_domains": ["physionet.org"],
    "description": "ECG subsystem aging clock: neurokit2 delineation + torch 1D CNN",
}


def build(
    *, secrets: dict | None = None
) -> tuple["modal.Image", dict[str, "modal.Volume"], dict[str, str]]:
    secrets = secrets or {}
    img = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("git")
        .pip_install(
            "numpy<2",
            "scipy",
            "pandas",
            "scikit-learn",
            "statsmodels",
            "wfdb",
            "neurokit2",
            "tqdm",
            "pyarrow",
            "matplotlib",
            "torch",
        )
    )
    vols = {
        "/data": modal.Volume.from_name("ptbxl-data", create_if_missing=True),
    }
    return img, vols, {}
