PYTHON ?= python3

.PHONY: check contracts workflow privacy

check: contracts workflow privacy

contracts:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
	$(PYTHON) scripts/validate_contracts.py

workflow:
	bash scripts/validate-go.sh

privacy:
	$(PYTHON) scripts/public_safety_audit.py
