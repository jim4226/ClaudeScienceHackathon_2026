#!/usr/bin/env python3
"""Verify the released, frozen artifacts of the electrical arm.

This does NOT retrain anything. It checks the claims that can be checked from a
fresh clone with no restricted data:

  1. The frozen IKr perturbation scorer reproduces its deterministic fixture and
     the protocol-lock self-hash (runs the independent verifier).
  2. Every result file named in the claim-to-artifact ledger exists.
  3. The SHA-256 release manifest matches the committed files.

Exit 0 iff all checks pass. Intended to be run as `make verify`.
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)                      # electrical-body-clock/
PERT = os.path.join(ARM, "results", "act1_ecg", "perturbation")


def _ok(msg): print(f"  [PASS] {msg}")
def _fail(msg): print(f"  [FAIL] {msg}")


def check_perturbation_verifier() -> bool:
    print("== frozen IKr scorer + protocol lock ==")
    r = subprocess.run(
        [sys.executable, "perturbation_direction_verifier.py",
         "--lock", "PERTURBATION_TRANSPORT_LOCK.json",
         "--fixture", "scorer_fixture.json"],
        cwd=PERT, capture_output=True, text=True)
    passed = r.returncode == 0 and "ALL PASS" in r.stdout
    (_ok if passed else _fail)("perturbation_direction_verifier: "
                               + ("ALL PASS" if passed else "FAILED"))
    if not passed:
        print(r.stdout[-800:], r.stderr[-400:])
    return passed


def check_ledger_files() -> bool:
    print("== claim-to-artifact ledger files exist ==")
    ledger = os.path.join(ARM, "CLAIM_TO_ARTIFACT_LEDGER.md")
    if not os.path.exists(ledger):
        _fail("CLAIM_TO_ARTIFACT_LEDGER.md missing"); return False
    # every backtick-quoted results/... path in the ledger must exist
    import re
    missing = []
    for m in re.finditer(r"`([^`]*results/[^`]+?)`", open(ledger).read()):
        rel = m.group(1).strip()
        p = os.path.join(ARM, rel)
        if not os.path.exists(p):
            missing.append(rel)
    if missing:
        for rel in sorted(set(missing)):
            _fail(f"ledger references missing file: {rel}")
        return False
    _ok("all ledger-referenced result files present")
    return True


def check_manifest() -> bool:
    print("== SHA-256 release manifest ==")
    mpath = os.path.join(ARM, "RELEASE_MANIFEST.sha256")
    if not os.path.exists(mpath):
        _fail("RELEASE_MANIFEST.sha256 missing (run scripts/make_manifest.py)"); return False
    bad = 0
    for line in open(mpath):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        p = os.path.join(ARM, rel)
        if not os.path.exists(p):
            _fail(f"manifest file missing: {rel}"); bad += 1; continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != digest:
            _fail(f"hash mismatch: {rel}"); bad += 1
    if bad:
        return False
    _ok("all manifest hashes match")
    return True


def main() -> int:
    results = [check_perturbation_verifier(), check_ledger_files(), check_manifest()]
    print()
    if all(results):
        print("VERIFY RESULT: ALL PASS")
        return 0
    print("VERIFY RESULT: FAILURES ABOVE")
    return 1


if __name__ == "__main__":
    sys.exit(main())
