PYTHON ?= python3

.PHONY: check contracts workflow docs privacy

check: contracts workflow docs privacy

contracts:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
	$(PYTHON) scripts/validate_contracts.py

workflow:
	bash scripts/validate-go.sh

docs:
	$(PYTHON) scripts/validate_docs.py

privacy:
	$(PYTHON) scripts/public_safety_audit.py
