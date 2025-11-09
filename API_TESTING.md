# 🧪 Тестирование API

## Запуск сервера

```fish
# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
python main.py
```

Сервер запустится на `http://localhost:8000`

## 📡 Доступные Endpoints

### 1. Анализ игрока

**GET** `/api/players/{nickname}/analysis`

Получить полный анализ игрока с рекомендациями.

**Пример:**
```fish
curl http://localhost:8000/api/players/s1mple/analysis
```

**Ответ:**
```json
{
  "player_id": "abc123",
  "nickname": "s1mple",
  "stats": {
    "kd_ratio": 1.35,
    "win_rate": 58.5,
    "headshot_percentage": 52.3,
    "average_kills": 22.5,
    "matches_played": 450,
    "elo": 2500,
    "level": 10
  },
  "strengths": {
    "aim": 9,
    "game_sense": 8,
    "positioning": 7,
    "teamwork": 8,
    "consistency": 9
  },
  "weaknesses": {
    "areas": ["positioning"],
    "priority": "positioning",
    "recommendations": [
      "Практиковать удержание позиций",
      "Изучить карты детальнее"
    ]
  },
  "training_plan": {
    "focus_areas": ["positioning"],
    "daily_exercises": [
      {
        "name": "Position practice",
        "duration": "30 минут",
        "description": "Практика позиционирования"
      }
    ],
    "estimated_time": "2-4 недели"
  },
  "overall_rating": 8,
  "analyzed_at": "2025-11-09T18:00:00Z"
}
```

---

### 2. Статистика игрока

**GET** `/api/players/{nickname}/stats`

Получить базовую статистику игрока.

**Пример:**
```fish
curl http://localhost:8000/api/players/s1mple/stats
```

---

### 3. История матчей

**GET** `/api/players/{nickname}/matches?limit=20`

Получить историю матчей игрока.

**Параметры:**
- `limit` (optional) - количество матчей (по умолчанию 20)

**Пример:**
```fish
curl "http://localhost:8000/api/players/s1mple/matches?limit=10"
```

---

### 4. Поиск игроков

**GET** `/api/players/search?query=s1mple&limit=20`

Поиск игроков по никнейму.

**Параметры:**
- `query` (required) - поисковый запрос
- `limit` (optional) - лимит результатов (по умолчанию 20)

**Пример:**
```fish
curl "http://localhost:8000/api/players/search?query=s1mple&limit=5"
```

---

## 🔑 Настройка API ключа

Создайте файл `.env` в корне проекта:

```env
FACEIT_API_KEY=your_faceit_api_key_here
```

### Как получить Faceit API ключ:

1. Зайдите на https://developers.faceit.com/
2. Зарегистрируйтесь или войдите
3. Создайте новое приложение
4. Скопируйте API ключ
5. Добавьте в `.env` файл

---

## 📖 Документация API

После запуска сервера доступна интерактивная документация:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Примеры тестирования

### Python
```python
import requests

# Анализ игрока
response = requests.get("http://localhost:8000/api/players/s1mple/analysis")
data = response.json()
print(f"Общая оценка: {data['overall_rating']}/10")
print(f"K/D: {data['stats']['kd_ratio']}")
```

### JavaScript (fetch)
```javascript
fetch('http://localhost:8000/api/players/s1mple/analysis')
  .then(res => res.json())
  .then(data => {
    console.log('Анализ:', data);
    console.log('Рейтинг:', data.overall_rating);
  });
```

### Fish shell
```fish
# Красивый вывод с jq
curl -s http://localhost:8000/api/players/s1mple/analysis | jq .

# Только статистику
curl -s http://localhost:8000/api/players/s1mple/analysis | jq '.stats'

# Только рекомендации
curl -s http://localhost:8000/api/players/s1mple/analysis | jq '.weaknesses.recommendations'
```

---

## ⚠️ Troubleshooting

### Ошибка: "Faceit API key not configured"
- Проверьте наличие `.env` файла
- Убедитесь что `FACEIT_API_KEY` установлен

### Ошибка: "Player not found"
- Проверьте правильность никнейма
- Убедитесь что игрок существует на Faceit

### Ошибка: CORS
- Добавьте ваш домен в `origins` в `main.py`
- Или установите `NODE_ENV=development` для разработки

---

## 🚀 Production

Для production используйте:

```fish
# С uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# С gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📊 Мониторинг

Проверка здоровья сервиса:

```fish
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "service": "analysis"
}
```
