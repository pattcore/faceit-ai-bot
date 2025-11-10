.PHONY: help install dev build test lint format clean docker-build docker-up docker-down deploy

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(BLUE)Установка npm зависимостей...$(NC)"
	npm install
	@echo "$(BLUE)Установка Python зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

dev: ## Запустить dev сервер
	@echo "$(BLUE)Запуск dev сервера...$(NC)"
	npm run dev

build: ## Собрать проект
	@echo "$(BLUE)Сборка проекта...$(NC)"
	npm run build
	@echo "$(GREEN)✓ Проект собран$(NC)"

test: ## Запустить тесты
	@echo "$(BLUE)Запуск тестов...$(NC)"
	npm test
	@echo "$(GREEN)✓ Тесты пройдены$(NC)"

test-coverage: ## Запустить тесты с coverage
	@echo "$(BLUE)Запуск тестов с coverage...$(NC)"
	npm run test:coverage
	@echo "$(GREEN)✓ Coverage отчёт создан$(NC)"

lint: ## Проверить код линтером
	@echo "$(BLUE)Проверка кода...$(NC)"
	npm run lint
	npm run type-check
	@echo "$(GREEN)✓ Код проверен$(NC)"

format: ## Форматировать код
	@echo "$(BLUE)Форматирование кода...$(NC)"
	npx prettier --write .
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

clean: ## Очистить временные файлы
	@echo "$(BLUE)Очистка...$(NC)"
	rm -rf .next node_modules __pycache__ dist build out coverage .pytest_cache
	@echo "$(GREEN)✓ Очищено$(NC)"

docker-build: ## Собрать Docker образы
	@echo "$(BLUE)Сборка Docker образов...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Docker образы собраны$(NC)"

docker-up: ## Запустить Docker контейнеры
	@echo "$(BLUE)Запуск Docker контейнеров...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Docker контейнеры запущены$(NC)"

docker-down: ## Остановить Docker контейнеры
	@echo "$(BLUE)Остановка Docker контейнеров...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Docker контейнеры остановлены$(NC)"

docker-logs: ## Показать логи Docker
	@echo "$(BLUE)Логи Docker:$(NC)"
	docker compose logs -f

deploy: ## Деплой на VPS
	@echo "$(BLUE)Деплой на VPS...$(NC)"
	git push origin main
	@echo "$(GREEN)✓ Деплой запущен через GitHub Actions$(NC)"

check: lint test ## Полная проверка (lint + test)
	@echo "$(GREEN)✓ Все проверки пройдены!$(NC)"
