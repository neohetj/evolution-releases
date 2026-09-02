.PHONY: check validate-component validate-bundle

MANIFEST ?=
COMPONENT ?=

check:
	python3 -m unittest discover -s tests -v
	python3 -m compileall -q scripts tests

validate-component:
	python3 scripts/release_contract.py validate-component --component "$(COMPONENT)" "$(MANIFEST)"

validate-bundle:
	python3 scripts/release_contract.py validate-bundle "$(MANIFEST)"
