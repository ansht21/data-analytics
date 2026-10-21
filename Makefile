.PHONY: run streamlit test lint typecheck docker clean

run:            ## Full pipeline + Excel workbook
	python run_pipeline.py

streamlit:      ## Launch interactive dashboard on :8501
	streamlit run streamlit_app/Dashboard.py

test:           ## Pytest suite with coverage gate
	pytest --cov=src --cov-report=term-missing

lint:           ## Ruff lint
	ruff check src tests run_pipeline.py

typecheck:      ## MyPy strict-ish pass
	mypy src

docker:         ## Build container image
	docker build -t weekly-revenue-reconciliation-engine .

clean:          ## Remove generated artifacts (cross-platform)
	python -c "import glob,os,shutil; [os.remove(f) for f in glob.glob('reports/*.xlsx')+glob.glob('logs/*.log')+glob.glob('data/processed/*.parquet') if os.path.exists(f)]; shutil.rmtree('data/processed', ignore_errors=True) or __import__('pathlib').Path('data/processed').mkdir(parents=True, exist_ok=True)"
