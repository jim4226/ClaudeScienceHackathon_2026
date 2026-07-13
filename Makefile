# From Clocks to Coordinates — reproducibility entry points.
#
# These targets run from a fresh clone with NO restricted data. They verify the
# frozen, released artifacts and build the papers; they do NOT retrain the clocks
# (training needs the staged PTB-XL windows — see electrical-body-clock/README.md).
#
#   make verify       # check frozen scorer, ledger files, SHA-256 manifest
#   make demo-smoke   # headless end-to-end test of the live demo (no server)
#   make paper        # compile all three manuscripts with tectonic
#   make manifest     # (re)generate the SHA-256 release manifest
#   make all          # verify + demo-smoke + paper

PYTHON ?= python3
TECTONIC ?= tectonic
ARM := electrical-body-clock
PAPER := $(ARM)/paper

.PHONY: all verify demo-smoke paper manifest clean help

help:
	@grep -E '^\t?#|^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | sed 's/^/  /'

all: verify demo-smoke paper

# ---------------------------------------------------------------- verify
verify:
	$(PYTHON) $(ARM)/scripts/verify_release.py

# regenerate the SHA-256 manifest (run after changing any released artifact)
manifest:
	$(PYTHON) $(ARM)/scripts/make_manifest.py

# ---------------------------------------------------------------- demo
demo-smoke:
	$(PYTHON) $(ARM)/demo/hf_space/smoke_test.py

# ---------------------------------------------------------------- papers
paper:
	cd $(PAPER) && $(TECTONIC) -X compile manuscript.tex
	cd $(PAPER) && $(TECTONIC) -X compile from_clocks_to_coordinates_full.tex
	cd $(PAPER) && $(TECTONIC) -X compile clocks_to_coordinates.tex
	@echo "Compiled: manuscript.pdf, from_clocks_to_coordinates_full.pdf, clocks_to_coordinates.pdf"

clean:
	rm -f $(PAPER)/*.aux $(PAPER)/*.log $(PAPER)/*.out $(PAPER)/*.bbl $(PAPER)/*.blg
