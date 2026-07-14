# Hackathon provenance

This file identifies the canonical submission artifacts and the boundaries of
the public release. Git commit timestamps, workflow logs, content hashes, and
the claim-to-artifact ledger provide the auditable record.

## Canonical submission artifacts

| Artifact | Canonical location |
|---|---|
| Project | `HumanVector` |
| Scientific paper | `electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf` |
| Paper source | `electrical-body-clock/paper/from_clocks_to_coordinates_full.tex` |
| Public demo | `https://jim4226.github.io/` |
| Evidence ledger | `electrical-body-clock/CLAIM_TO_ARTIFACT_LEDGER.md` |
| Root release seal | `RELEASE_MANIFEST.sha256` |
| Electrical release seal | `electrical-body-clock/RELEASE_MANIFEST.sha256` |

The canonical PDF is 54 pages and has SHA-256
`c1cb1807f852be288d89966abba1676179622403559cf094482206f1edc77bc0`.

The six-page judge brief and earlier manuscript remain in `paper/` for
historical transparency. When they differ, the canonical 54-page paper and its
claim-to-artifact ledger govern the submission.

## Public versus controlled artifacts

- Public code, aggregate outputs, disclosed derived open-data tables, selected
  licensed demo records, frozen model checkpoints, figures, and papers are
  committed here.
- Participant-level AABC inputs and per-visit AABC scores remain in the approved
  controlled-access environment.
- Raw MRI and CT volumes, restricted clinical records, and identifiable data are
  not committed.
- The Atlas uses independent reference records across modalities. It does not
  represent one multimodally scanned person.

See [DATA_LICENSES.md](DATA_LICENSES.md) for the source-by-source map.

## Integrity mechanisms

- patient-level splitting before outcome analysis;
- physically separated outcome-free feature construction and outcome stages;
- frozen protocol and scorer artifacts before the target evaluation;
- deterministic fixtures and independent verifier scripts;
- one claim-to-artifact ledger for public headline quantities;
- null, conditional, and failed-gate results retained rather than hidden;
- SHA-256 manifests regenerated after release changes;
- GitHub Actions running the same public verification commands.

This file does not replace event eligibility rules. The repository history and
source-system logs should be used to verify when each analysis and artifact was
created.
