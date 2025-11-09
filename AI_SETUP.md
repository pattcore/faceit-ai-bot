# 🤖 AI Integration Setup Guide

## ✅ Что уже реализовано

### 1. OpenAI Integration ✅
- **Сервис**: `src/server/ai/openai_service.py`
- **Функции**:
  - Анализ производительности игрока
  - Генерация персональных планов тренировок
  - AI рекомендации на основе статистики

### 2. Faceit API Integration ✅
- **Клиент**: `src/server/integrations/faceit_client.py`
- **Функции**:
  - Получение статистики игрока
  - История матчей
  - Поиск игроков

### 3. AI Analysis Endpoints ✅
- **Роутер**: `src/server/features/ai_analysis/routes.py`
- **Endpoints**:
  - `POST /ai/analyze-player` - AI анализ игрока
  - `GET /ai/training-plan/{player_id}` - План тренировок

### 4. Demo Analyzer с AI ✅
- **Сервис**: `src/server/features/demo_analyzer/service.py`
- **Интеграция**: AI рекомендации в анализе демо

## 🔑 Настройка API ключей

### 1. Получить OpenAI API Key

```bash
# Зарегистрируйтесь на https://platform.openai.com/
# Создайте API ключ в разделе API Keys
# Скопируйте ключ
```

### 2. Получить Faceit API Key

```bash
# Зайдите на https://developers.faceit.com/
# Создайте приложение
# Скопируйте Client ID как API Key
```

### 3. Добавить ключи в .env

```env
# AI Services
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...  # Опционально

# Faceit API
FACEIT_API_KEY=your-faceit-api-key

# Optional
HUGGINGFACE_TOKEN=hf_...
```

## 📦 Установка зависимостей

```bash
# Python зависимости
pip install -r requirements.txt

# Это установит:
# - openai>=1.0.0
# - anthropic>=0.7.0
# - langchain>=0.1.0
# - aiohttp>=3.9.0
# - torch>=2.1.0 (для ML моделей)
# - pandas, numpy, scikit-learn
```

## 🚀 Запуск с AI

```bash
# 1. Убедитесь что .env настроен
cat .env | grep API_KEY

# 2. Запустите backend
python main.py
# или
uvicorn src.server.main:app --reload

# 3. Проверьте API docs
open http://localhost:8000/docs
```

## 📝 Использование API

### Анализ игрока

```bash
curl -X POST "http://localhost:8000/ai/analyze-player" \
  -H "Content-Type: application/json" \
  -d '{
    "player_nickname": "s1mple",
    "faceit_id": null
  }'
```

**Ответ:**
```json
{
  "player_id": "...",
  "nickname": "s1mple",
  "analysis": "Детальный AI анализ...",
  "recommendations": [
    "Улучшить позиционирование на карте Mirage",
    "Работать над экономикой в force-buy раундах"
  ],
  "training_plan": {
    "daily_exercises": [...],
    "weekly_goals": [...],
    "estimated_time": "2-3 недели"
  },
  "strengths": ["Отличный aim", "Хорошая реакция"],
  "weaknesses": ["Слабая экономика", "Позиционирование"]
}
```

### План тренировок

```bash
curl "http://localhost:8000/ai/training-plan/{player_id}"
```

### Анализ демо с AI

```bash
curl -X POST "http://localhost:8000/demo/analyze" \
  -F "demo=@match.dem"
```

## 🧪 Тестирование

```bash
# Тест OpenAI сервиса
python -c "
from src.server.ai.openai_service import OpenAIService
import asyncio

async def test():
    service = OpenAIService()
    result = await service.analyze_player_performance({
        'kd_ratio': 1.2,
        'hs_percentage': 45,
        'win_rate': 52
    })
    print(result)

asyncio.run(test())
"

# Тест Faceit клиента
python -c "
from src.server.integrations.faceit_client import FaceitAPIClient
import asyncio

async def test():
    client = FaceitAPIClient()
    player = await client.get_player_by_nickname('s1mple')
    print(player)

asyncio.run(test())
"
```

## 📊 Мониторинг использования AI

### Логи

```bash
# Смотреть логи AI запросов
tail -f logs/ai_service.log

# Или в консоли
docker-compose logs -f api | grep "OpenAI\|Faceit"
```

### Метрики

- AI requests: `/metrics` endpoint (Prometheus)
- Latency: Средняя задержка AI запросов
- Errors: Количество ошибок AI

## 💰 Стоимость использования

### OpenAI GPT-4 Turbo

- **Input**: $0.01 / 1K tokens
- **Output**: $0.03 / 1K tokens
- **Средний запрос**: ~1500 tokens = $0.06

### Рекомендации по оптимизации

1. **Кэширование** - кэшировать AI ответы
2. **Rate limiting** - ограничить запросы
3. **Batch processing** - группировать запросы
4. **Fallback** - использовать дефолтные ответы

## 🔒 Безопасность

```python
# Никогда не коммитьте API ключи!
# Используйте .env файл
# Добавьте .env в .gitignore ✅

# Ротация ключей
# Меняйте API ключи каждые 90 дней

# Мониторинг
# Отслеживайте необычную активность
```

## 🐛 Troubleshooting

### OpenAI API не работает

```bash
# Проверить ключ
echo $OPENAI_API_KEY

# Проверить баланс
# https://platform.openai.com/usage

# Проверить лимиты
# https://platform.openai.com/account/limits
```

### Faceit API ошибки

```bash
# 401 Unauthorized - неверный API key
# 429 Too Many Requests - превышен лимит
# 404 Not Found - игрок не найден
```

### Медленные ответы

```python
# Используйте async/await
# Добавьте timeout
async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
    ...
```

## 📚 Дополнительные ресурсы

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Faceit API Docs](https://developers.faceit.com/)
- [LangChain Docs](https://python.langchain.com/)
- [AI_INTEGRATION.md](./AI_INTEGRATION.md) - Детальный план

## 🎯 Следующие шаги

1. ✅ Базовая AI интеграция
2. ✅ Faceit API клиент
3. ✅ AI анализ игроков
4. ⏳ CS2 Demo парсинг (требует demoparser2)
5. ⏳ ML модели для предсказаний
6. ⏳ Real-time анализ матчей

---

**Готово к использованию!** 🚀

Для запуска нужно только добавить API ключи в `.env` файл.
