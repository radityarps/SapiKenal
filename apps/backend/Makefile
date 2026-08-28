.PHONY: install test run docker-build docker-run docker-stop clean

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

run:
	python main.py

docker-build:
	docker compose build

docker-run:
	docker compose up

docker-stop:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
