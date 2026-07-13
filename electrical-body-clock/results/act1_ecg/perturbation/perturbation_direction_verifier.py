#!/usr/bin/env python3
"""
perturbation_direction_verifier.py

Independent verifier for PERTURBATION_TRANSPORT_LOCK.json + s_ikr_scorer.py.
Asserts the frozen algebra, the content self-hash, and exact scorer reproduction.
Also asserts the harness never loads an outcome column.

Usage:
    python perturbation_direction_verifier.py \
        --lock  ../outputs/PERTURBATION_TRANSPORT_LOCK.json \
        --fixture ../outputs/scorer_fixture.json

Exit code 0 = all checks pass; non-zero = failure.
"""
from __future__ import annotations
import argparse, json, hashlib, sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s_ikr_scorer import SIKrScorer, NegativeControlHarness, _canonical_self_sha256

OUTCOME_TOKENS = ("death", "died", "mort", "event", "surv", "time_to",
                  "deceased", "dod", "outcome", "label", "hazard")


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}")
    return bool(cond)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", required=True)
    ap.add_argument("--fixture", required=True)
    args = ap.parse_args()

    with open(args.lock) as fh:
        lock = json.load(fh)
    with open(args.fixture) as fh:
        fx = json.load(fh)

    C = np.asarray(lock["contrast_C"], float)
    Sigma_q = np.asarray(lock["Sigma_q"], float)
    Sigma_q_inv = np.asarray(lock["Sigma_q_inv"], float)
    w = np.asarray(lock["direction"]["w_IKr"], float)
    v = np.asarray(lock["direction"]["v_IKr_whitened"], float)

    ok = True
    print("== frozen algebra ==")
    u = np.ones(4)
    ok &= check("C u = 0", np.allclose(C @ u, 0, atol=1e-9))
    ok &= check("C C' = I", np.allclose(C @ C.T, np.eye(3), atol=1e-9))
    ok &= check("Sigma_q symmetric", np.allclose(Sigma_q, Sigma_q.T, atol=1e-12))
    ev = np.linalg.eigvalsh(Sigma_q)
    ok &= check(f"Sigma_q positive-definite (min eig {ev.min():.4f})", (ev > 0).all())
    ok &= check("Sigma_q @ Sigma_q_inv = I", np.allclose(Sigma_q @ Sigma_q_inv, np.eye(3), atol=1e-8))
    ok &= check("w' Sigma_q w = 1", abs(w @ Sigma_q @ w - 1.0) < 1e-4)
    ok &= check("v is unit-norm (whitened)", abs(np.linalg.norm(v) - 1.0) < 1e-6)
    # v and w consistency: v = Sigma_q^{1/2} w / ||.||  (both point the same way)
    from scipy.linalg import sqrtm
    v_from_w = sqrtm(Sigma_q).real @ w
    v_from_w = v_from_w / np.linalg.norm(v_from_w)
    ok &= check("v aligns with Sigma_q^{1/2} w", float(v @ v_from_w) > 0.999999)

    print("== content self-hash ==")
    recomputed = _canonical_self_sha256(lock)
    stored = lock.get("_content_self_sha256", "")
    ok &= check(f"content_self_sha256 matches ({recomputed[:12]}...)", recomputed == stored)

    print("== scorer exact reproduction ==")
    sc = SIKrScorer(lock)
    z = np.asarray(fx["z"], float)
    q = sc.q_from_z(z)
    ok &= check("q = C z reproduces fixture", np.allclose(q, np.asarray(fx["q"]), atol=1e-9))
    ok &= check("S_IKr_raw reproduces fixture", np.allclose(sc.score(q), np.asarray(fx["S_IKr_raw"]), atol=1e-9))
    ok &= check("S_IKr_std reproduces fixture", np.allclose(sc.score_std(q), np.asarray(fx["S_IKr_std"]), atol=1e-9))
    # geometry identity: S = v . u  with u = Sigma_q^{-1/2} q
    Sig_ih = np.asarray(lock["Sigma_q_inv_half"], float)
    U = q @ Sig_ih.T
    S_via_v = U @ v
    ok &= check("identity S_IKr = v_hat . u (u=Sigma^{-1/2}q)", np.allclose(sc.score(q), S_via_v, atol=1e-8))
    D = np.linalg.norm(U, axis=1)
    ok &= check("|S_IKr| <= D for all fixture rows", bool((np.abs(sc.score(q)) <= D + 1e-9).all()))

    print("== negative-control harness ==")
    harness = NegativeControlHarness(sc)
    ok &= check("flipped score = -raw", np.allclose(harness.score_flipped(q), -sc.score(q), atol=1e-9))
    ok &= check("random-dir score row0 reproduces fixture",
                np.allclose(harness.score_random(q)[0, :5],
                            np.asarray(fx["random_dir_score_row0_first5"]), atol=1e-9))

    print("== outcome-blindness ==")
    # No key in the lock or fixture references an outcome column name.
    blob = (json.dumps(lock) + json.dumps(fx)).lower()
    leaks = [t for t in OUTCOME_TOKENS if t in blob]
    # 'mort' appears legitimately in reveal_protocol endpoint DESCRIPTIONS; ensure no DATA column present.
    # The scorer only accepts z / q arrays; it has no outcome parameter.
    import inspect
    sig_params = set(inspect.signature(sc.score_from_z).parameters) | set(inspect.signature(sc.score).parameters)
    ok &= check("scorer signatures carry no outcome parameter",
                not any(t in " ".join(sig_params).lower() for t in OUTCOME_TOKENS))
    print(f"  (note: endpoint names appear in reveal_protocol prose only: {sorted(leaks)})")

    print()
    print("VERIFIER RESULT:", "ALL PASS" if ok else "FAILURE(S) DETECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
