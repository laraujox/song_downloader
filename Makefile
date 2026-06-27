# Run `make setup` once, then `make backend` and `make frontend` in two terminals.

PYTHON ?= python

setup:
	$(PYTHON) -m venv .venv
	.venv/Scripts/pip install -r requirements.txt
	cd frontend && npm install

backend:
	.venv/Scripts/uvicorn backend.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

.PHONY: setup backend frontend
