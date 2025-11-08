.PHONY: help install test test-unit test-integration test-coverage lint format clean

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt
	npm install

test: ## Запустить все тесты
	pytest tests -v

test-unit: ## Запустить unit тесты
	pytest tests/unit -v

test-integration: ## Запустить integration тесты
	pytest tests/integration -v

test-coverage: ## Запустить тесты с покрытием кода
	pytest tests --cov=src/server --cov-report=html --cov-report=term-missing --cov-fail-under=70

lint: ## Запустить линтер
	flake8 src/server tests
	pylint src/server

format: ## Форматировать код
	black src/server tests
	isort src/server tests

clean: ## Очистить временные файлы
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

dev: ## Запустить в режиме разработки
	python -m uvicorn src.server.main:app --reload --host 0.0.0.0 --port 8000

build: ## Собрать проект
	npm run build
	python -m pip install -r requirements.txt

deploy: ## Задеплоить проект
	./deploy.sh
