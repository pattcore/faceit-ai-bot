#!/bin/bash

set -e  # Exit on error

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Faceit AI Bot - Деплой${NC}"
echo "=========================================="

# Определяем команду docker compose
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Проверка .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env файл не найден. Копирую из .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ Пожалуйста, отредактируйте .env файл и запустите скрипт снова!${NC}"
    exit 1
fi

# Остановка старых контейнеров
echo -e "${YELLOW}🛑 Остановка старых контейнеров...${NC}"
$DOCKER_COMPOSE down

# Собираем и запускаем сервисы
echo -e "${BLUE}🔨 Сборка сервисов...${NC}"
$DOCKER_COMPOSE build

echo -e "${BLUE}Запуск сервисов...${NC}"
$DOCKER_COMPOSE up -d

echo -e "${YELLOW}⏳ Ожидание запуска сервисов...${NC}"
sleep 10

# Проверка статуса сервисов
echo ""
echo -e "${GREEN}Проверка статуса сервисов:${NC}"
$DOCKER_COMPOSE ps

echo ""
echo -e "${GREEN}=========================================="
echo "Сервисы запущены и доступны:"
echo -e "=========================================="${NC}
echo -e "${BLUE}Frontend (Next.js):${NC}    http://localhost:3000"
echo -e "${BLUE}Backend API:${NC}           http://localhost:8000"
echo -e "${BLUE}API Docs (Swagger):${NC}    http://localhost:8000/docs"
echo -e "${BLUE}💾 PostgreSQL:${NC}            localhost:5432"
echo ""
echo -e "${YELLOW}Полезные команды:${NC}"
echo "  $DOCKER_COMPOSE logs -f          - просмотр логов всех сервисов"
echo "  $DOCKER_COMPOSE logs -f web      - просмотр логов frontend"
echo "  $DOCKER_COMPOSE logs -f api      - просмотр логов backend"
echo "  $DOCKER_COMPOSE down             - остановка всех сервисов"
echo "  $DOCKER_COMPOSE restart          - перезапуск всех сервисов"
echo ""