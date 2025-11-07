#!/bin/bash

set -e  # Exit on error

echo "🚀 Faceit AI Bot - Полная сборка проекта"
echo "=========================================="

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для вывода предупреждения
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Функция для вывода ошибки
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Проверка наличия .env файла
if [ ! -f .env ]; then
    warning ".env файл не найден. Копирую из .env.example..."
    cp .env.example .env
    warning "Пожалуйста, отредактируйте .env файл перед запуском!"
fi

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Определяем команду docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo ""
echo "📦 Шаг 1: Установка зависимостей Node.js"
if [ -f package.json ]; then
    npm install
    success "Зависимости Node.js установлены"
else
    warning "package.json не найден, пропускаю установку зависимостей Node.js"
fi

echo ""
echo "🔨 Шаг 2: Сборка Next.js приложения"
if [ -f package.json ]; then
    npm run build
    success "Next.js приложение собрано"
else
    warning "Пропускаю сборку Next.js"
fi

echo ""
echo "🎨 Шаг 3: Сборка расширения для браузера (webpack)"
if [ -f webpack.config.js ]; then
    npm run webpack:build
    success "Расширение для браузера собрано"
else
    warning "webpack.config.js не найден, пропускаю сборку расширения"
fi

echo ""
echo "🐳 Шаг 4: Сборка Docker образов"
$DOCKER_COMPOSE build --no-cache
success "Docker образы собраны"

echo ""
echo "=========================================="
success "Сборка завершена успешно!"
echo ""
echo "Для запуска проекта используйте:"
echo "  ./deploy.sh          - запуск всех сервисов"
echo "  npm run dev          - запуск только Next.js в dev режиме"
echo "  docker-compose up -d - запуск Docker сервисов"