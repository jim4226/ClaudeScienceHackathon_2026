# How Claude Science changed the research workflow

Claude was used as a scientific collaborator, implementation partner, and
adversarial reviewer. It did not supply biological measurements or replace the
researcher's responsibility for data access, scientific decisions, and final
claims.

## Roles in the workflow

### 1. Hypothesis formalization

Claude helped turn a broad multi-organ aging idea into testable coordinates:
shared movement `A`, disagreement magnitude `D`, signed contrast coordinates
`q`, and a controlled-perturbation projection `S`. The key conceptual revision
followed a negative result: a null unsigned radius motivated testing whether
direction, rather than distance, carried mechanism.

### 2. Outcome-blind implementation

Claude helped build and review:

- patient-level split logic;
- outcome-free feature tables;
- protocol locks and self-hashes;
- frozen score definitions and calibration constants;
- negative controls and deterministic test fixtures;
- the one-time confirmatory analysis harness.

The public verifier rechecks the released perturbation geometry without any
outcome column.

### 3. Parallel analysis and critique

Separate Claude contexts acted as analysis authors, statistical critics,
novelty reviewers, release auditors, and independent result verifiers. This
surfaced errors that were corrected before release, including ambiguous
orthogonality language, overinterpretation of null effects, inconsistent
NHANES uncertainty fields, mixed phase-model interpretation, figure-to-claim
mismatches, and the need for balanced LEMON sensitivity analysis.

### 4. Reproducible writing

The manuscript, figures, and README were repeatedly checked against machine
outputs. Headline quantities are mapped to committed artifacts in
`electrical-body-clock/CLAIM_TO_ARTIFACT_LEDGER.md`. The release manifests seal
the submitted paper source, PDF, figures, model artifacts, and result files.

### 5. Scientific communication

Claude helped create the HumanVector Atlas and its evidence labels. The demo
keeps illustration, reference anatomy, observed data, model output, and locked
tests visually distinct. It also states that records from different modalities
come from independent cohorts.

## What Claude did not do

- It did not generate or alter raw participant measurements.
- It did not receive unrestricted permission to redistribute controlled data.
- It did not make the project a clinical device.
- It did not convert exploratory findings into confirmatory ones.
- It did not make null results disappear.

## Auditable public artifacts

- `electrical-body-clock/results/act1_ecg/perturbation/PERTURBATION_TRANSPORT_LOCK.json`
- `electrical-body-clock/results/act1_ecg/perturbation/perturbation_direction_verifier.py`
- `electrical-body-clock/results/act1_ecg/perturbation/scorer_fixture.json`
- `electrical-body-clock/results/act1_ecg/reveal/REVEAL_LOG_populated.json`
- `electrical-body-clock/CLAIM_TO_ARTIFACT_LEDGER.md`
- `electrical-body-clock/RELEASE_MANIFEST.sha256`
- `RELEASE_MANIFEST.sha256`
- `.github/workflows/ci.yml`

The intended contribution of AI here is not merely speed. It is the ability to
conduct a broad research program while making its claims narrower, more
traceable, and easier to challenge.
