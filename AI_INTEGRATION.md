# 🤖 AI Integration Plan

План интеграции реальных AI моделей в Faceit Stats Bot v0.2.2

## 🎯 Цели

1. **Анализ демо-файлов CS2** с помощью ML
2. **Персональные рекомендации** на основе AI
3. **Предсказание исхода матчей**
4. **Поиск оптимальных тиммейтов** с ML алгоритмами

## 📦 Необходимые зависимости

### Python (AI/ML)

```txt
# AI/ML библиотеки
openai>=1.0.0                    # OpenAI API (GPT-4, GPT-3.5)
anthropic>=0.7.0                 # Claude API
langchain>=0.1.0                 # LLM orchestration
transformers>=4.35.0             # Hugging Face models
torch>=2.1.0                     # PyTorch для ML
numpy>=1.24.0                    # Numerical computing
pandas>=2.0.0                    # Data analysis
scikit-learn>=1.3.0              # ML algorithms

# CS2 Demo parsing
demoparser2>=0.1.0               # CS2 demo parser
awpy>=1.3.0                      # CS:GO/CS2 analytics

# Faceit API
aiohttp>=3.9.0                   # Async HTTP client
pydantic>=2.0.0                  # Data validation
```

### Node.js (Frontend AI features)

```json
{
  "@ai-sdk/openai": "^0.0.20",
  "ai": "^3.0.0",
  "langchain": "^0.1.0",
  "openai": "^4.20.0"
}
```

## 🏗️ Архитектура AI системы

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│  - AI Chat Interface                                │
│  - Real-time Recommendations                        │
│  - Match Predictions                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  ┌─────────────────────────────────────────────┐   │
│  │         AI Service Layer                    │   │
│  │  - LLM Integration (GPT-4/Claude)          │   │
│  │  - Prompt Engineering                       │   │
│  │  - Context Management                       │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │         ML Models Layer                     │   │
│  │  - Demo Analysis Model                      │   │
│  │  - Player Performance Predictor             │   │
│  │  - Teammate Matching Algorithm              │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │         Data Processing                     │   │
│  │  - CS2 Demo Parser                          │   │
│  │  - Faceit API Client                        │   │
│  │  - Feature Engineering                      │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              External Services                      │
│  - OpenAI API (GPT-4)                              │
│  - Anthropic API (Claude)                          │
│  - Faceit API                                      │
│  - CS2 Game Coordinator                            │
└─────────────────────────────────────────────────────┘
```

## 🔧 Реализация по этапам

### Этап 1: Базовая интеграция с AI (1-2 недели)

#### 1.1 OpenAI Integration

```python
# src/server/ai/openai_service.py
from openai import AsyncOpenAI
from typing import List, Dict

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        
    async def analyze_player_performance(
        self, 
        stats: Dict,
        match_history: List[Dict]
    ) -> str:
        """Анализ производительности игрока с помощью GPT-4"""
        
        prompt = f"""
        Проанализируй статистику игрока CS2:
        
        Текущие показатели:
        - K/D: {stats['kd_ratio']}
        - Headshot %: {stats['hs_percentage']}
        - Win Rate: {stats['win_rate']}
        
        История последних 20 матчей: {match_history}
        
        Дай подробный анализ и рекомендации по улучшению.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Ты профессиональный CS2 тренер"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
```

#### 1.2 Faceit API Integration

```python
# src/server/integrations/faceit_client.py
import aiohttp
from typing import Optional, Dict, List

class FaceitAPIClient:
    BASE_URL = "https://open.faceit.com/data/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
    
    async def get_player_stats(self, player_id: str) -> Dict:
        """Получить статистику игрока"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/players/{player_id}/stats/cs2",
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def get_match_history(
        self, 
        player_id: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Получить историю матчей"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/players/{player_id}/history",
                headers=self.headers,
                params={"game": "cs2", "limit": limit}
            ) as response:
                data = await response.json()
                return data.get("items", [])
```

### Этап 2: Demo Analysis (2-3 недели)

#### 2.1 CS2 Demo Parser

```python
# src/server/parsers/demo_parser.py
from demoparser2 import DemoParser
from typing import Dict, List
import pandas as pd

class CS2DemoAnalyzer:
    def __init__(self):
        self.parser = DemoParser()
    
    async def parse_demo(self, demo_path: str) -> Dict:
        """Парсинг CS2 демо файла"""
        
        # Парсинг основных событий
        df = self.parser.parse_event(
            demo_path,
            event_name="player_death",
            player=["X", "Y", "Z"],
            other=["total_rounds_played", "weapon"]
        )
        
        # Извлечение статистики
        stats = self._extract_statistics(df)
        
        # Анализ ключевых моментов
        key_moments = self._identify_key_moments(df)
        
        return {
            "statistics": stats,
            "key_moments": key_moments,
            "round_by_round": self._analyze_rounds(df)
        }
    
    def _extract_statistics(self, df: pd.DataFrame) -> Dict:
        """Извлечение статистики из датафрейма"""
        return {
            "total_kills": len(df),
            "headshots": len(df[df['hitgroup'] == 1]),
            "weapon_usage": df['weapon'].value_counts().to_dict(),
            "positions": self._analyze_positions(df)
        }
```

#### 2.2 ML Model для анализа

```python
# src/server/ml/performance_model.py
import torch
import torch.nn as nn
from typing import Dict, List

class PlayerPerformanceModel(nn.Module):
    """ML модель для предсказания производительности"""
    
    def __init__(self, input_size: int = 50):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.network(x)
    
    def predict_performance(self, features: Dict) -> float:
        """Предсказание производительности игрока"""
        # Преобразование фич в тензор
        x = self._features_to_tensor(features)
        
        with torch.no_grad():
            prediction = self.forward(x)
        
        return prediction.item()
```

### Этап 3: Advanced Features (3-4 недели)

#### 3.1 Teammate Matching Algorithm

```python
# src/server/ml/teammate_matcher.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np

class TeammateMatchingAI:
    """AI для подбора оптимальных тиммейтов"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()
    
    async def find_best_teammates(
        self,
        player_profile: Dict,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """Найти лучших тиммейтов используя ML"""
        
        # Извлечение фич
        player_features = self._extract_features(player_profile)
        
        # Оценка совместимости с каждым кандидатом
        scores = []
        for candidate in candidates:
            candidate_features = self._extract_features(candidate)
            compatibility = self._calculate_compatibility(
                player_features,
                candidate_features
            )
            scores.append({
                "player": candidate,
                "score": compatibility,
                "reasons": self._explain_match(player_features, candidate_features)
            })
        
        # Сортировка по совместимости
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        return scores[:top_k]
```

#### 3.2 Real-time Match Predictions

```python
# src/server/ml/match_predictor.py
from transformers import AutoModel, AutoTokenizer
import torch

class MatchOutcomePredictor:
    """Предсказание исхода матча в реальном времени"""
    
    def __init__(self):
        self.model = AutoModel.from_pretrained("bert-base-uncased")
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    
    async def predict_match_outcome(
        self,
        team1_stats: Dict,
        team2_stats: Dict,
        map_name: str
    ) -> Dict:
        """Предсказать исход матча"""
        
        # Подготовка данных
        features = self._prepare_features(team1_stats, team2_stats, map_name)
        
        # Предсказание
        with torch.no_grad():
            prediction = self.model(**features)
        
        win_probability = torch.softmax(prediction.logits, dim=1)[0][1].item()
        
        return {
            "team1_win_probability": win_probability,
            "team2_win_probability": 1 - win_probability,
            "confidence": self._calculate_confidence(prediction),
            "key_factors": self._identify_key_factors(features)
        }
```

## 🔑 Необходимые API ключи

Добавить в `.env`:

```env
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Faceit
FACEIT_API_KEY=...

# Optional: Hugging Face
HUGGINGFACE_TOKEN=hf_...
```

## 📊 Метрики и мониторинг

```python
# src/server/monitoring/ai_metrics.py
from prometheus_client import Counter, Histogram

ai_requests = Counter('ai_requests_total', 'Total AI requests')
ai_latency = Histogram('ai_request_duration_seconds', 'AI request latency')
ai_errors = Counter('ai_errors_total', 'Total AI errors')
```

## 🧪 Тестирование AI компонентов

```python
# tests/test_ai_integration.py
import pytest
from src.server.ai.openai_service import OpenAIService

@pytest.mark.asyncio
async def test_player_analysis():
    service = OpenAIService(api_key="test-key")
    
    stats = {
        "kd_ratio": 1.2,
        "hs_percentage": 45.5,
        "win_rate": 52.3
    }
    
    analysis = await service.analyze_player_performance(stats, [])
    
    assert analysis is not None
    assert len(analysis) > 0
```

## 📈 Roadmap

- **Week 1-2**: OpenAI integration + Faceit API
- **Week 3-4**: Demo parser + basic ML models
- **Week 5-6**: Advanced matching algorithms
- **Week 7-8**: Real-time predictions + optimization
- **Week 9+**: Fine-tuning, A/B testing, production deployment

## 💡 Best Practices

1. **Кэширование** - кэшировать AI ответы для одинаковых запросов
2. **Rate limiting** - ограничивать количество AI запросов
3. **Fallbacks** - иметь запасные варианты при недоступности AI
4. **Мониторинг** - отслеживать качество и стоимость AI запросов
5. **A/B тестирование** - тестировать разные промпты и модели

---

Готов начать реализацию! 🚀
