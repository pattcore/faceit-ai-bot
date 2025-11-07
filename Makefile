.PHONY: help install build dev deploy clean test logs release

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Показать эту справку
	@echo "$(BLUE)Faceit AI Bot - Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Установить все зависимости
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	npm install
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

build: ## Собрать весь проект
	@echo "$(BLUE)🔨 Сборка проекта...$(NC)"
	chmod +x build-all.sh
	./build-all.sh

dev: ## Запустить в режиме разработки
	@echo "$(BLUE)🔧 Запуск в режиме разработки...$(NC)"
	chmod +x dev.sh
	./dev.sh

deploy: ## Деплой всех сервисов
	@echo "$(BLUE)🚀 Деплой сервисов...$(NC)"
	chmod +x deploy.sh
	./deploy.sh

clean: ## Очистить временные файлы и контейнеры
	@echo "$(YELLOW)🧹 Очистка...$(NC)"
	docker-compose down -v
	rm -rf node_modules/.cache
	rm -rf .next
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

test: ## Запустить тесты
	@echo "$(BLUE)🧪 Запуск тестов...$(NC)"
	npm test

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-web: ## Показать логи frontend
	docker-compose logs -f web

logs-api: ## Показать логи backend
	docker-compose logs -f api

stop: ## Остановить все сервисы
	@echo "$(YELLOW)🛑 Остановка сервисов...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Сервисы остановлены$(NC)"

restart: ## Перезапустить все сервисы
	@echo "$(YELLOW)🔄 Перезапуск сервисов...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Сервисы перезапущены$(NC)"

status: ## Показать статус сервисов
	@echo "$(BLUE)📊 Статус сервисов:$(NC)"
	docker-compose ps

release: ## Создать релиз проекта
	@echo "$(BLUE)🚀 Создание релиза...$(NC)"
	chmod +x release.sh
	./release.sh