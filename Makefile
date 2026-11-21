# Analysis and report entry points. Simulation and builds live in scripts/.
#   make report   -> build/report/report.pdf
PYTHON ?= python3
VENV   := .venv
PY     := $(VENV)/bin/python

.PHONY: report report-assets clean-report

$(VENV)/.requirements-installed: analysis/requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --quiet -r analysis/requirements.txt
	touch $@

report-assets: $(VENV)/.requirements-installed
	$(PY) analysis/report_assets.py

report: report-assets
	latexmk -pdf -cd -interaction=nonstopmode -halt-on-error -outdir=../build/report report/report.tex
	@echo "report: build/report/report.pdf"

clean-report:
	rm -rf build/report
