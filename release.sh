#!/bin/bash

set -e  # Exit on error

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Получаем версию из package.json
VERSION=$(node -p "require('./package.json').version")
RELEASE_NAME="faceit-ai-bot-v${VERSION}"
RELEASE_DIR="releases/${RELEASE_NAME}"

echo -e "${BLUE}Faceit AI Bot - Создание релиза v${VERSION}${NC}"
echo "=========================================="

# Создаем директорию для релиза
echo -e "${YELLOW}📁 Создание директории релиза...${NC}"
rm -rf "releases/${RELEASE_NAME}"
mkdir -p "${RELEASE_DIR}"

# Проверяем наличие билдов
if [ ! -d ".next" ]; then
    echo -e "${RED}✗ Next.js билд не найден. Запустите: npm run build${NC}"
    exit 1
fi

if [ ! -f "public/background.js" ] || [ ! -f "public/popup.js" ]; then
    echo -e "${RED}✗ Webpack билд не найден. Запустите: npm run webpack:build${NC}"
    exit 1
fi

# Копируем необходимые файлы
echo -e "${YELLOW}Копирование файлов...${NC}"

# 1. Browser Extension
echo "  - Browser Extension..."
mkdir -p "${RELEASE_DIR}/browser-extension"
cp manifest.json "${RELEASE_DIR}/browser-extension/"
cp popup.html "${RELEASE_DIR}/browser-extension/"
cp public/background.js "${RELEASE_DIR}/browser-extension/"
cp public/popup.js "${RELEASE_DIR}/browser-extension/"
# Копируем иконки если есть
if ls public/icon*.png 1> /dev/null 2>&1; then
    cp public/icon*.png "${RELEASE_DIR}/browser-extension/" 2>/dev/null || true
fi

# 2. Docker файлы и конфигурация
echo "  - Docker конфигурация..."
mkdir -p "${RELEASE_DIR}/docker"
cp docker-compose.yml "${RELEASE_DIR}/docker/"
cp Dockerfile* "${RELEASE_DIR}/docker/"
cp .env.example "${RELEASE_DIR}/docker/"
cp nginx.conf "${RELEASE_DIR}/docker/" 2>/dev/null || true

# 3. Скрипты деплоя
echo "  - Скрипты деплоя..."
mkdir -p "${RELEASE_DIR}/scripts"
cp build-all.sh "${RELEASE_DIR}/scripts/"
cp deploy.sh "${RELEASE_DIR}/scripts/"
cp build.sh "${RELEASE_DIR}/scripts/" 2>/dev/null || true
chmod +x "${RELEASE_DIR}/scripts/"*.sh

# 4. Документация
echo "  - Документация..."
cp README.md "${RELEASE_DIR}/"
cp LICENSE "${RELEASE_DIR}/" 2>/dev/null || true

# 5. Создаем архив browser extension
echo -e "${YELLOW}Создание архива расширения для браузера...${NC}"
cd "${RELEASE_DIR}/browser-extension"
zip -r "../faceit-ai-bot-extension-v${VERSION}.zip" ./* > /dev/null
cd - > /dev/null
echo -e "${GREEN}✓ Архив расширения создан: ${RELEASE_DIR}/faceit-ai-bot-extension-v${VERSION}.zip${NC}"

# 6. Создаем полный архив релиза
echo -e "${YELLOW}Создание полного архива релиза...${NC}"
cd releases
tar -czf "${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}" > /dev/null
cd - > /dev/null
echo -e "${GREEN}✓ Полный архив создан: releases/${RELEASE_NAME}.tar.gz${NC}"

# 7. Создаем RELEASE_NOTES.md
echo -e "${YELLOW}Создание release notes...${NC}"
cat > "${RELEASE_DIR}/RELEASE_NOTES.md" << EOF
# Faceit AI Bot v${VERSION}

## Что включено в релиз

### 🌐 Browser Extension
- \`faceit-ai-bot-extension-v${VERSION}.zip\` - готовое расширение для браузера
- Установка: распакуйте и загрузите в Chrome/Edge через chrome://extensions

### 🐳 Docker Deployment
- Все необходимые Docker файлы для деплоя
- Docker Compose конфигурация
- Скрипты автоматического деплоя

### 📚 Документация
- README.md - основная документация
- Примеры конфигурации (.env.example)

## Быстрый старт

### Установка расширения для браузера
1. Распакуйте \`faceit-ai-bot-extension-v${VERSION}.zip\`
2. Откройте chrome://extensions
3. Включите "Режим разработчика"
4. Нажмите "Загрузить распакованное расширение"
5. Выберите папку с расширением

### Деплой через Docker
\`\`\`bash
cd docker
cp .env.example .env
# Отредактируйте .env файл
docker-compose up -d
\`\`\`

### Деплой с помощью скриптов
\`\`\`bash
cd scripts
chmod +x *.sh
./deploy.sh
\`\`\`

## 📊 Доступные сервисы после деплоя
- 🌐 Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 💾 PostgreSQL: localhost:5432

## Технологии
- Frontend: Next.js 15, React 19, TypeScript
- Backend: FastAPI, Python 3.9+
- Database: PostgreSQL 16
- Browser Extension: Webpack, Babel
- Deployment: Docker, Docker Compose

## Changelog
- Первый релиз проекта
- Базовая функциональность AI-ассистента
- Расширение для браузера
- Docker деплой

---
Дата релиза: $(date +%Y-%m-%d)
EOF

echo -e "${GREEN}✓ Release notes созданы${NC}"

# Вывод итоговой информации
echo ""
echo -e "${GREEN}=========================================="
echo "Релиз v${VERSION} успешно создан!"
echo -e "==========================================${NC}"
echo ""
echo -e "${BLUE}📁 Файлы релиза:${NC}"
echo "  releases/${RELEASE_NAME}/"
echo "  ├── browser-extension/"
echo "  │   └── faceit-ai-bot-extension-v${VERSION}.zip"
echo "  ├── docker/"
echo "  ├── scripts/"
echo "  ├── README.md"
echo "  └── RELEASE_NOTES.md"
echo ""
echo -e "${BLUE}Архивы:${NC}"
echo "  releases/${RELEASE_NAME}.tar.gz (полный релиз)"
echo "  releases/${RELEASE_NAME}/faceit-ai-bot-extension-v${VERSION}.zip (только расширение)"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "  1. Проверьте содержимое: cd releases/${RELEASE_NAME}"
echo "  2. Протестируйте расширение"
echo "  3. Создайте GitHub Release с тегом v${VERSION}"
echo "  4. Загрузите архивы в GitHub Release"
echo ""