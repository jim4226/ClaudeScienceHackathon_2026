"""
S_IKr scorer — frozen external transport of the IKr-blockade signed direction.

The signed IKr perturbation score for an external patient with contrast vector
q = C z (z = frozen phase-age calibration z-scores in order [P, AV, QRS, STT]) is

        S_IKr      = w_IKr . q                      (raw, units of Mahalanobis projection)
        S_IKr_std  = (S_IKr - MU_S_CAL) / SD_S_CAL  (calibration-standardized)

where w_IKr = Sigma_q^{-1} m_IKr / sqrt(m_IKr' Sigma_q^{-1} m_IKr) is the frozen,
covariance-scaled signed direction derived OUTCOME-BLIND from participant-level
dofetilide-minus-placebo q-contrasts (ECGRDVQ), confirmed within-cohort in quinidine.

Geometry:  in whitened coordinates u = Sigma_q^{-1/2} q,
           D = ||u||  (unsigned disagreement radius; was null)
           S_IKr = v_hat . u   with v_hat = Sigma_q^{-1/2} m_IKr / ||.||  (unit)
           so |S_IKr| <= D always; S_IKr keeps the signed projection that D discarded.

This module loads all frozen constants from PERTURBATION_TRANSPORT_LOCK.json.
It NEVER reads an outcome column. It is CPU-only and dependency-light (numpy).
"""
from __future__ import annotations
import json, hashlib
import numpy as np

PHASE_ORDER = ["P", "AV", "QRS", "STT"]


def _canonical_self_sha256(obj: dict) -> str:
    """Canonical content hash: drop underscore-prefixed keys, sort, compact JSON, sha256."""
    core = {k: v for k, v in obj.items() if not k.startswith("_")}
    payload = json.dumps(core, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class SIKrScorer:
    def __init__(self, lock: dict):
        self.lock = lock
        d = lock["direction"]
        self.C = np.asarray(lock["contrast_C"], float)                 # 3 x 4
        self.Sigma_q = np.asarray(lock["Sigma_q"], float)              # 3 x 3
        self.Sigma_q_inv = np.asarray(lock["Sigma_q_inv"], float)      # 3 x 3
        self.w_IKr = np.asarray(d["w_IKr"], float)                     # 3
        self.v_IKr = np.asarray(d["v_IKr_whitened"], float)            # 3
        self.sign_convention = d["sign_convention"]
        self.mu_S_cal = float(lock["standardization"]["mu_S_cal"])
        self.sd_S_cal = float(lock["standardization"]["sd_S_cal"])
        self._validate_frozen_algebra()

    # ---- construction from file ----
    @classmethod
    def from_lock_file(cls, path: str) -> "SIKrScorer":
        with open(path) as fh:
            lock = json.load(fh)
        return cls(lock)

    # ---- algebra guards ----
    def _validate_frozen_algebra(self, atol: float = 1e-6):
        u = np.ones(4)
        assert np.allclose(self.C @ u, 0, atol=atol), "C u != 0"
        assert np.allclose(self.C @ self.C.T, np.eye(3), atol=atol), "C C' != I"
        assert np.allclose(self.Sigma_q, self.Sigma_q.T, atol=atol), "Sigma_q not symmetric"
        ev = np.linalg.eigvalsh(self.Sigma_q)
        assert (ev > 0).all(), "Sigma_q not positive-definite"
        assert np.allclose(self.Sigma_q @ self.Sigma_q_inv, np.eye(3), atol=atol), "Sigma_q_inv wrong"
        assert abs(self.w_IKr @ self.Sigma_q @ self.w_IKr - 1.0) < 1e-4, "w' Sigma_q w != 1"

    # ---- scoring ----
    def q_from_z(self, z: np.ndarray) -> np.ndarray:
        """z: (..., 4) in PHASE_ORDER -> q: (..., 3)."""
        z = np.asarray(z, float)
        return z @ self.C.T

    def score(self, q: np.ndarray) -> np.ndarray:
        """q: (N,3) contrast vectors -> raw S_IKr = w_IKr . q."""
        q = np.atleast_2d(np.asarray(q, float))
        return q @ self.w_IKr

    def score_std(self, q: np.ndarray) -> np.ndarray:
        """Calibration-standardized S_IKr_std."""
        return (self.score(q) - self.mu_S_cal) / self.sd_S_cal

    def score_from_z(self, z: np.ndarray, standardized: bool = True) -> np.ndarray:
        q = self.q_from_z(z)
        return self.score_std(q) if standardized else self.score(q)


# ---------- negative-control harness ----------
class NegativeControlHarness:
    """
    Diagnostic empirical-null controls. These are FROZEN and DIAGNOSTIC ONLY:
    they cannot be searched to find a better direction, cannot redefine w_IKr,
    cannot change the endpoint, and cannot gate the primary conclusion.

    (1) sign-flipped directions: -w_IKr and a fixed set of within-cohort
        treatment-sign-flip realizations recorded in the lock.
    (2) random contrast-space directions: a predetermined set of unit vectors in
        q-space, generated from a fixed RNG algorithm+seed, standardized on the
        same calibration constants.
    """
    def __init__(self, scorer: SIKrScorer, n_random: int = 200, seed: int = 20260712):
        self.scorer = scorer
        self.seed = seed
        self.n_random = n_random
        self.rng = np.random.default_rng(seed)
        self.random_dirs = self._make_random_directions()

    def _make_random_directions(self) -> np.ndarray:
        """Unit directions in q-space, each normalized so d' Sigma_q d = 1 (matches w scale)."""
        G = self.rng.standard_normal((self.n_random, 3))
        out = []
        for g in G:
            nrm = np.sqrt(g @ self.scorer.Sigma_q @ g)
            out.append(g / nrm)
        return np.asarray(out)

    def flipped_direction(self) -> np.ndarray:
        return -self.scorer.w_IKr

    def score_random(self, q: np.ndarray) -> np.ndarray:
        """Return (N x n_random) raw scores under the random directions (empirical null)."""
        q = np.atleast_2d(np.asarray(q, float))
        return q @ self.random_dirs.T

    def score_flipped(self, q: np.ndarray) -> np.ndarray:
        q = np.atleast_2d(np.asarray(q, float))
        return q @ self.flipped_direction()
