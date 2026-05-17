PYTHON ?= python3
VENV ?= .venv
UI_APP := code/ui/app.py
UI_REQUIREMENTS := code/ui/requirements.txt

ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV)/Scripts/python.exe
else
VENV_PYTHON := $(VENV)/bin/python
endif

.DEFAULT_GOAL := help

.PHONY: help ui ui-venv ui-install ui-run ui-clean

help:
	@echo "HospitalDB UI targets:"
	@echo "  make ui          Create/update the UI virtualenv and run Streamlit"
	@echo "  make ui-venv     Create the UI virtualenv only"
	@echo "  make ui-install  Install UI Python requirements into the virtualenv"
	@echo "  make ui-run      Run the Streamlit UI after installing requirements"
	@echo "  make ui-clean    Remove the UI virtualenv"

ui: ui-run

ui-venv: $(VENV_PYTHON)

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

ui-install: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r $(UI_REQUIREMENTS)

ui-run: ui-install
	$(VENV_PYTHON) -m streamlit run $(UI_APP)

ui-clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"
