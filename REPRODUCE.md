# Reproduce and verify HumanVector

The release separates fast, public verification from full retraining. The
verification path needs no controlled-access data and does not retrain any
model.

## Fast fresh-clone check

Recommended environment:

- Ubuntu 22.04 or newer
- Python 3.11
- GNU Make
- internet access only for installing Python dependencies

```bash
git clone https://github.com/jim4226/ClaudeScienceHackathon_2026.git
cd ClaudeScienceHackathon_2026

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "numpy>=1.26,<3" "scipy>=1.11"

make verify
```

Expected final line:

```text
VERIFY RESULT: ALL PASS
```

`make verify` checks:

1. the frozen IKr scorer and deterministic fixture;
2. the protocol-lock self-hash and stored geometry identities;
3. every released result file referenced by the claim-to-artifact ledger;
4. the arm-level and repository-level SHA-256 manifests.

## Demo smoke test

The CPU smoke test uses committed frozen weights and explicitly licensed example
records. It does not launch a public server.

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r electrical-body-clock/demo/hf_space/requirements.txt
make demo-smoke
```

The hosted Space keeps compatible lower bounds in `requirements.txt`. The exact
versions used by the judged CPU smoke test are recorded separately in
`electrical-body-clock/demo/hf_space/requirements-lock.txt`.

## Compile the manuscripts

Install [Tectonic](https://tectonic-typesetting.github.io/) and run:

```bash
make paper
```

The canonical output is:

```text
electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf
```

The released canonical PDF is 54 pages and has SHA-256:

```text
c1cb1807f852be288d89966abba1676179622403559cf094482206f1edc77bc0
```

Tectonic may produce a byte-different PDF when its engine or dependency bundle
changes. Verify scientific content and page rendering as well as source
compilation; the release manifest seals the submitted bytes.

## Regenerate release manifests

After intentionally changing a released artifact:

```bash
make manifest
make verify
```

Never hand-edit a recorded digest.

## Full retraining

Full retraining requires the original datasets and provider-specific access
terms. See [DATA_LICENSES.md](DATA_LICENSES.md) and
[electrical-body-clock/README.md](electrical-body-clock/README.md). Controlled
AABC participant data and other restricted inputs are not included in this
repository.

## Windows

Use WSL Ubuntu for parity with CI. The repository includes `.gitattributes` so
the manifest text files retain LF line endings across platforms.
