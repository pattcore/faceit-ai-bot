#!/bin/bash

# Скрипт тестирования сайтов Faceit Stats Bot
# Использование: bash test-sites.sh

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧪 Тестирование сайтов Faceit Stats Bot${NC}"
echo "============================================================"

# Счетчики
TOTAL_TESTS=0
PASSED_TESTS=0

# Функция для проверки URL
test_url() {
    local url=$1
    local name=$2
    
    echo -e "\n${YELLOW}📍 Проверка: $name${NC}"
    echo "   URL: $url"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Проверка доступности
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "   ${GREEN}✅ Статус: $response OK${NC}"
        
        # Получаем размер контента
        size=$(curl -s "$url" 2>/dev/null | wc -c)
        echo "   📦 Размер: $size bytes"
        
        # Проверяем содержимое
        content=$(curl -s "$url" 2>/dev/null)
        if echo "$content" | grep -q "Faceit"; then
            echo -e "   ${GREEN}✅ Содержит 'Faceit'${NC}"
        fi
        if echo "$content" | grep -q "Stats Bot"; then
            echo -e "   ${GREEN}✅ Содержит 'Stats Bot'${NC}"
        fi
        
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    elif [ "$response" = "403" ]; then
        echo -e "   ${YELLOW}⚠️  Статус: $response (Доступ ограничен - возможно Cloudflare)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "   ${RED}❌ Ошибка: Сервер недоступен${NC}"
        return 1
    else
        echo -e "   ${YELLOW}⚠️  Статус: $response${NC}"
        return 1
    fi
}

# Тестирование сайтов

# 1. GitHub Pages
test_url "https://pat1one.github.io/faceit-ai-bot/" "GitHub Pages"

# 2. Главный сайт
echo -e "\n${YELLOW}📍 Проверка: Главный сайт (pattmsc.online)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://pattmsc.online" 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "   ${GREEN}✅ Сайт доступен (Статус: $response)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ "$response" = "403" ]; then
    echo -e "   ${YELLOW}⚠️  Статус 403: Сайт работает, но доступ ограничен (возможно Cloudflare)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${RED}❌ Сайт недоступен (Статус: $response)${NC}"
fi

# 3. API
echo -e "\n${YELLOW}📍 Проверка: API (api.pattmsc.online)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://api.pattmsc.online/docs" 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "   ${GREEN}✅ API доступен (Статус: $response)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${RED}❌ API недоступен (Статус: $response)${NC}"
fi

# 4. Проверка downloads
echo -e "\n${YELLOW}📍 Проверка: Downloads${NC}"
downloads=(
    "faceit-ai-bot-chrome.zip"
    "faceit-ai-bot-firefox.xpi"
    "faceit-ai-bot-edge.zip"
    "faceit-ai-bot-opera.zip"
    "faceit-ai-bot-docker.tar.gz"
)

downloads_ok=0
for file in "${downloads[@]}"; do
    url="https://pattmsc.online/downloads/$file"
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo -e "   ${GREEN}✅ $file доступен${NC}"
        downloads_ok=$((downloads_ok + 1))
    else
        echo -e "   ${YELLOW}⚠️  $file не найден (ожидается после релиза)${NC}"
    fi
done

# 5. Проверка GitHub Release
echo -e "\n${YELLOW}📍 Проверка: GitHub Release v0.2.0${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
response=$(curl -s -o /dev/null -w "%{http_code}" "https://api.github.com/repos/pat1one/faceit-ai-bot/releases/tags/v0.2.0" 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "   ${GREEN}✅ Релиз v0.2.0 существует${NC}"
    
    # Получаем информацию о релизе
    release_info=$(curl -s "https://api.github.com/repos/pat1one/faceit-ai-bot/releases/tags/v0.2.0" 2>/dev/null)
    assets_count=$(echo "$release_info" | grep -o '"name":' | wc -l)
    echo "   📦 Артефактов: $assets_count"
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${YELLOW}⚠️  Релиз v0.2.0 не найден${NC}"
fi

# 6. Проверка Docker Images
echo -e "\n${YELLOW}📍 Проверка: Docker Images (ghcr.io)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if command -v docker &> /dev/null; then
    if docker pull ghcr.io/pat1one/faceit-ai-bot/api:latest &> /dev/null; then
        echo -e "   ${GREEN}✅ Docker образ API доступен${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${YELLOW}⚠️  Docker образ API не найден (ожидается после релиза)${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  Docker не установлен, пропускаем проверку${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS - 1))
fi

# Итоги
echo ""
echo "============================================================"
echo -e "${CYAN}📊 ИТОГИ ТЕСТИРОВАНИЯ${NC}"
echo "============================================================"

echo -e "\n📈 Результат: ${GREEN}$PASSED_TESTS${NC}/${TOTAL_TESTS} тестов пройдено"

if [ $downloads_ok -gt 0 ]; then
    echo -e "📥 Downloads: ${GREEN}$downloads_ok${NC}/${#downloads[@]} файлов доступно"
fi

# Процент успеха
if [ $TOTAL_TESTS -gt 0 ]; then
    percentage=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "✨ Успешность: ${GREEN}${percentage}%${NC}"
fi

echo ""
if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 Все тесты пройдены успешно!${NC}"
    exit 0
elif [ $PASSED_TESTS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Некоторые тесты не прошли${NC}"
    exit 1
else
    echo -e "${RED}❌ Все тесты провалены${NC}"
    exit 1
fi
