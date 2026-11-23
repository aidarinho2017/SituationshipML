.PHONY: install model api web test build dev docker docker-down

install:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

model:
	.venv/bin/python backend/train_model.py

api:
	.venv/bin/uvicorn backend.app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

test:
	PYTHONPATH=backend .venv/bin/pytest backend/tests -q

build:
	cd frontend && npm run build

dev:
	@echo "Run 'make api' and 'make web' in separate terminals."

docker:
	docker compose up --build

docker-down:
	docker compose down

