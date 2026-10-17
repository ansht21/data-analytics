.PHONY: setup fixtures test run-api run-ui demo-good demo-bad docker-up clean

setup:
	python -m venv .venv
	.venv/Scripts/Activate.ps1; pip install -r requirements.txt

fixtures:
	python fixtures/make_fixtures.py

test:
	pytest -q

run-api:
	uvicorn api.main:app --reload --port 8000

run-ui:
	streamlit run app.py --server.port 8501

demo-good:
	python pipeline/ingest.py --batch fixtures/good_sample.csv

demo-bad:
	python pipeline/ingest.py --batch fixtures/bad_nulls.csv --auto-investigate

docker-up:
	docker compose up --build

clean:
	Remove-Item -Recurse -Force __pycache__,src/__pycache__,pipeline/__pycache__,api/__pycache__,tests/__pycache__,.pytest_cache -ErrorAction SilentlyContinue
