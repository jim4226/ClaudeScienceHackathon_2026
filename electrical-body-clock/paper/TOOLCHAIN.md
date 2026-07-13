# Paper build toolchain

All three manuscripts compile with **Tectonic** (a self-contained, reproducible
LaTeX engine that fetches exactly the packages each document needs and caches them
by content hash — so the TeX package set is pinned by Tectonic itself rather than by
a system TeX Live install).

- **Engine:** Tectonic ≥ 0.15 (tested with **0.16.9**).
- **Build:** from the repository root, `make paper`, or per-document:
  ```bash
  tectonic -X compile from_clocks_to_coordinates_full.tex   # 55-page technical account
  tectonic -X compile clocks_to_coordinates.tex             # 6-page judge cut
  tectonic -X compile manuscript.tex                        # original reproducible paper
  ```
- **Fonts:** the documents use standard TeX font packages (no system fonts
  required); Tectonic downloads them on first build.
- **Figures:** committed under `figs_full/` (full manuscript), `figs_c2c/`
  (judge cut) and `figs/` (original), referenced by local relative path.

First build downloads packages/fonts (network needed once); subsequent builds are
offline from the Tectonic cache.
