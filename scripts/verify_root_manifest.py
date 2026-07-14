#!/usr/bin/env python3
"""Verify the ROOT RELEASE_MANIFEST.sha256 byte-for-byte.

Recomputes SHA-256 for every path listed in the root manifest and compares it to
the recorded hash. Exits non-zero on any mismatch or missing file, so it can gate
CI. Run from a fresh clone: `python scripts/verify_root_manifest.py`.
"""
from __future__ import annotations
import hashlib, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "RELEASE_MANIFEST.sha256")


def main() -> int:
    if not os.path.exists(MANIFEST):
        print(f"[FAIL] root manifest not found: {MANIFEST}")
        return 1
    ok = bad = miss = 0
    for line in open(MANIFEST, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        expected, rel = line.split("  ", 1)
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f"[FAIL] missing: {rel}")
            miss += 1
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got == expected:
            ok += 1
        else:
            print(f"[FAIL] hash mismatch: {rel}")
            bad += 1
    total = ok + bad + miss
    if bad or miss:
        print(f"== root manifest: {ok}/{total} OK, {bad} mismatched, {miss} missing ==")
        return 1
    print(f"[PASS] root manifest: all {ok} files match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
