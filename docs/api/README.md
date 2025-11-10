# API Документация

## Базовая информация

- **Base URL:** `https://pattmsc.online/api` (production)
- **Base URL:** `http://localhost:8000/api` (development)
- **Формат:** JSON
- **Аутентификация:** API Key (X-API-Key header)

## Эндпоинты

### Игроки

#### GET /api/players/{nickname}/stats

Получить статистику игрока

**Параметры:**
- `nickname` (string) - никнейм игрока на Faceit

**Ответ:**

```json
{
  "nickname": "s1mple",
  "level": 10,
  "elo": 3000,
  "games": 1234,
  "winrate": 65.5,
  "kd_ratio": 1.45
}
```

#### POST /api/players/{nickname}/analyze

Анализ игрока

**Параметры:**
- `nickname` (string) - никнейм игрока

**Ответ:**

```json
{
  "nickname": "s1mple",
  "recommendation": "Отличный игрок для команды",
  "strengths": ["aim", "game_sense"],
  "weaknesses": ["communication"],
  "rating": 9.5
}
```

### Поиск тиммейтов

#### POST /api/teammates/search

Поиск подходящих тиммейтов

**Тело запроса:**

```json
{
  "min_level": 7,
  "max_level": 10,
  "min_elo": 2000,
  "region": "EU",
  "languages": ["ru", "en"]
}
```

**Ответ:**

```json
{
  "teammates": [
    {
      "nickname": "player1",
      "level": 10,
      "elo": 2800,
      "match_score": 95
    }
  ],
  "total": 1
}
```

## Коды ошибок

- `400` - Неверный запрос
- `401` - Не авторизован
- `404` - Игрок не найден
- `429` - Слишком много запросов
- `500` - Ошибка сервера

## Rate Limits

- **Бесплатный:** 100 запросов/час
- **Premium:** 1000 запросов/час

## Примеры

См. [examples/](../../examples/)

## Swagger UI

Интерактивная документация: https://pattmsc.online/docs
