"""
Groq Integration Service
Service for Groq AI models
"""
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse
import aiohttp
import json
from ..config.settings import settings
from .sample_store import append_sample

logger = logging.getLogger(__name__)


class GroqService:
    """Service for Groq API"""

    def __init__(self, api_key: Optional[str] = None):
        local_base_url = getattr(settings, "LOCAL_LLM_BASE_URL", None)
        local_model = getattr(settings, "LOCAL_LLM_MODEL", None)
        openrouter_api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        openrouter_model = getattr(settings, "OPENROUTER_MODEL", None)

        if local_base_url:
            self.provider = "local"
            self.groq_base_url = local_base_url
            self.model = local_model or getattr(settings, "GROQ_MODEL", "qwen:0.5b")
            self.api_key = api_key or getattr(settings, "LOCAL_LLM_API_KEY", None)
        elif openrouter_api_key:
            self.provider = "openrouter"
            self.api_key = api_key or openrouter_api_key
            self.groq_base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = (
                openrouter_model
                or getattr(settings, "GROQ_MODEL", "meta-llama/llama-3.1-8b-instruct")
            )
        else:
            self.provider = "groq"
            self.api_key = api_key or getattr(settings, "GROQ_API_KEY", None)
            self.groq_base_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = getattr(settings, "GROQ_MODEL", "llama3-70b-8192")

        if not self.api_key and self.provider != "local":
            logger.warning("Groq API key not configured")

    def _is_openrouter_base_url(self) -> bool:
        """Return True if groq_base_url points to openrouter.ai host."""
        try:
            parsed = urlparse(self.groq_base_url)
            return parsed.netloc == "openrouter.ai"
        except Exception:
            return False

    def _normalize_language(self, language: Optional[str]) -> str:
        """Normalize language code to a small set (currently 'ru' or 'en')."""
        if not language:
            return "ru"
        lang = str(language).lower()
        if lang.startswith("en"):
            return "en"
        if lang.startswith("ru"):
            return "ru"
        return "en"


    def _log_sample(
        self,
        task: str,
        language: str,
        input_payload: Dict,
        output_payload,
    ) -> None:
        try:
            record = {
                "task": task,
                "language": language,
                "input": input_payload,
                "output": output_payload,
            }
            logger.info(
                "ai_sample %s",
                json.dumps(record, ensure_ascii=False, default=str),
            )

            # Additionally, persist samples for future coach model training
            append_sample(record)
        except Exception:
            logger.exception("Failed to log AI sample")

    async def analyze_player_performance(
        self,
        stats: Dict,
        match_history: Optional[List[Dict]] = None,
        language: str = "ru",
    ) -> str:
        """
        Analyze player performance with Groq AI

        Args:
            stats: Current player statistics
            match_history: Recent match history

        Returns:
            Detailed analysis and recommendations
        """
        if not self.api_key and getattr(self, "provider", None) != "local":
            return "Analysis unavailable - API key not configured"

        try:
            lang = self._normalize_language(language)
            prompt = self._build_analysis_prompt(stats, match_history or [], lang)

            headers = {
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            if self._is_openrouter_base_url():
                referer = getattr(settings, "WEBSITE_URL", "")
                app_title = getattr(settings, "APP_TITLE", "Faceit AI Bot")
                if referer:
                    headers["HTTP-Referer"] = referer
                headers["X-Title"] = app_title

            if lang == "en":
                system_content = (
                    "You are a professional CS2 coach with over 10 years of experience. "
                    "Analyze the provided statistics and context (including demo data if present) "
                    "and give specific, practical recommendations for improvement. "
                    "Always answer ONLY in ENGLISH. Do NOT use Russian or other languages. "
                    "Be reasonably detailed but avoid unnecessary fluff."
                )
            else:
                system_content = (
                    "Ты профессиональный тренер по CS2 с более чем 10-летним опытом. "
                    "Анализируй переданные показатели и контекст (включая данные демки, если есть) "
                    "и давай конкретные, практические рекомендации по улучшению. "
                    "Всегда отвечай ТОЛЬКО на РУССКОМ языке. Не используй английский, кроме "
                    "названий карт, оружия и стандартных CS-терминов. Будь подробным, но без воды."
                )

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 300
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"][
                            "content"
                        ]
                        self._log_sample(
                            task="analysis",
                            language=lang,
                            input_payload={
                                "stats": stats,
                                "match_history": match_history or [],
                            },
                            output_payload=content,
                        )
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Groq API error: {response.status} - "
                            f"{error_text}"
                        )
                        return (
                            f"Error analyzing performance: "
                            f"{response.status}"
                        )

        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return (
                f"Error analyzing performance: {str(e)}"
            )

    async def generate_demo_coach_report(
        self,
        demo_input: Dict,
        language: str = "ru",
    ) -> Dict:
        lang = self._normalize_language(language)
        if not self.api_key and getattr(self, "provider", None) != "local":
            return {}

        if lang == "en":
            system_content = (
                "You are a professional CS2 coach. Based on the structured match "
                "data, generate a detailed coaching report for the player. "
                "Return ONLY one valid JSON object with the following top-level "
                "fields: overview, strengths, weaknesses, key_moments, "
                "training_plan, summary. All text fields must be in ENGLISH."
            )
            header = (
                "You are an AI CS2 coach. You receive structured match data "
                "(JSON below). Based on it, generate a detailed coaching report "
                "for the player in JSON with the following schema: overview, "
                "strengths, weaknesses, key_moments, training_plan, summary.\n\n"
                "Input data:\n"
            )
        else:
            system_content = (
                "Ты профессиональный тренер по CS2. На основе структурированных "
                "данных матча составь подробный коуч-отчёт для игрока. Верни "
                "ТОЛЬКО один корректный JSON-объект со следующими полями верхнего "
                "уровня: overview, strengths, weaknesses, key_moments, "
                "training_plan, summary. Все текстовые поля должны быть на "
                "РУССКОМ языке."
            )
            header = (
                "Ты — AI‑тренер по CS2. На входе у тебя структурированные данные "
                "матча (JSON ниже). На их основе составь развёрнутый коуч‑отчёт "
                "для игрока в формате JSON со следующей схемой: overview, "
                "strengths, weaknesses, key_moments, training_plan, summary.\n\n"
                "Входные данные:\n"
            )

        user_prompt = header + json.dumps(demo_input, ensure_ascii=False, indent=2)

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self._is_openrouter_base_url():
            referer = getattr(settings, "WEBSITE_URL", "")
            app_title = getattr(settings, "APP_TITLE", "Faceit AI Bot")
            if referer:
                headers["HTTP-Referer"] = referer
            headers["X-Title"] = app_title

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_content,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.4,
            "max_tokens": 800,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(
                            "Groq demo coach error: %s - %s",
                            response.status,
                            text,
                        )
                        return {}
                    data = await response.json()
                    content = data["choices"][0]["message"][
                        "content"
                    ]

            text = content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                cleaned_lines = [
                    line
                    for line in lines
                    if not line.strip().startswith("```")
                ]
                text = "\n".join(cleaned_lines).strip()

            try:
                report = json.loads(text)
            except json.JSONDecodeError:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        report = json.loads(text[start : end + 1])
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to parse demo coach report JSON",
                            exc_info=True,
                        )
                        return {}
                else:
                    return {}

            if isinstance(report, dict):
                self._log_sample(
                    task="demo_coach_report",
                    language=lang,
                    input_payload={"demo_input": demo_input},
                    output_payload=report,
                )
                return report

            return {}
        except Exception:
            logger.exception("Error in generate_demo_coach_report")
            return {}

    async def generate_training_plan(
        self,
        player_stats: Dict,
        focus_areas: List[str],
        language: str = "ru",
    ) -> Dict:
        """
        Generate personalized training plan

        Args:
            player_stats: Player statistics
            focus_areas: Areas for improvement

        Returns:
            Structured training plan
        """
        lang = self._normalize_language(language)

        if not self.api_key and getattr(self, "provider", None) != "local":
            return self._get_default_training_plan(lang)

        try:
            if lang == "en":
                prompt = f"""
                Create a detailed training plan for a CS2 player.

                Player statistics:
                - K/D: {player_stats.get('kd_ratio', 'N/A')}
                - Headshot %: {player_stats.get('hs_percentage', 'N/A')}
                - Win Rate: {player_stats.get('win_rate', 'N/A')}

                Main focus areas for improvement: {', '.join(focus_areas)}

                Return ONLY one valid JSON object with the following fields:
                - daily_exercises: list of objects with fields name, duration, description
                - weekly_goals: list of strings
                - estimated_time: string

                All text fields (name, description, weekly_goals, estimated_time)
                must be in ENGLISH.

                Do not add any explanations, comments or markdown, only pure JSON.
                """
            else:
                prompt = f"""
                Составь подробный тренировочный план для игрока CS2.

                Статистика игрока:
                - K/D: {player_stats.get('kd_ratio', 'N/A')}
                - Headshot %: {player_stats.get('hs_percentage', 'N/A')}
                - Win Rate: {player_stats.get('win_rate', 'N/A')}

                Основные направления для улучшения: {', '.join(focus_areas)}

                Верни ТОЛЬКО один корректный JSON-объект со следующими полями:
                - daily_exercises: список объектов с полями name, duration, description
                - weekly_goals: список строк
                - estimated_time: строка

                Все текстовые поля (name, description, weekly_goals, estimated_time)
                должны быть НА РУССКОМ ЯЗЫКЕ.

                Не добавляй никаких пояснений, комментариев или markdown, только чистый JSON.
                """

            headers = {
                "Content-Type": "application/json"
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            if lang == "en":
                system_content = (
                    "You are a CS2 coach. Reply strictly in JSON format, without "
                    "any extra text. All text fields in the JSON must be in ENGLISH."
                )
            else:
                system_content = (
                    "Ты тренер по CS2. Отвечай строго в формате JSON, без "
                    "дополнительного текста. Все текстовые поля в JSON "
                    "должны быть на РУССКОМ языке."
                )

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 300
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"][
                            "content"
                        ]

                        # Try to parse JSON strictly first
                        text = content.strip()

                        # Remove optional markdown code fences
                        if text.startswith("```"):
                            lines = text.splitlines()
                            cleaned_lines = [
                                line
                                for line in lines
                                if not line.strip().startswith("```")
                            ]
                            text = "\n".join(cleaned_lines).strip()

                        plan = None

                        try:
                            plan = json.loads(text)
                        except json.JSONDecodeError:
                            start = text.find("{")
                            end = text.rfind("}")
                            if start != -1 and end != -1 and end > start:
                                candidate_span = text[start : end + 1]
                                try:
                                    plan = json.loads(candidate_span)
                                except json.JSONDecodeError:
                                    brace_level = 0
                                    for idx, ch in enumerate(text[start:], start):
                                        if ch == "{":
                                            brace_level += 1
                                        elif ch == "}":
                                            brace_level -= 1
                                            if brace_level == 0:
                                                candidate = text[start : idx + 1]
                                                try:
                                                    plan = json.loads(candidate)
                                                    break
                                                except json.JSONDecodeError:
                                                    continue

                        if plan is None:
                            logger.error(
                                "Failed to parse Groq training plan JSON",
                            )
                            return self._get_default_training_plan(lang)

                        self._log_sample(
                            task="training_plan",
                            language=lang,
                            input_payload={
                                "player_stats": player_stats,
                                "focus_areas": focus_areas,
                            },
                            output_payload=plan,
                        )
                        return plan
                    else:
                        return self._get_default_training_plan(lang)

        except Exception as e:
            logger.error(f"Error generating training plan: {str(e)}")
            return self._get_default_training_plan(lang)

    async def describe_teammate_matches(
        self,
        payload: Dict,
        language: str = "ru",
    ) -> Dict:
        lang = self._normalize_language(language)

        if not self.api_key and getattr(self, "provider", None) != "local":
            return {}

        try:
            if lang == "en":
                system_content = (
                    "You are a CS2 coach. Given a player profile and a list of "
                    "candidate teammates, you evaluate how well each candidate "
                    "fits the player. Return ONLY one JSON object where keys are "
                    "candidate user_id values and values are objects with fields "
                    "'score' (0-1 float, higher is better) and 'summary' (short "
                    "text explanation in ENGLISH). Do not add any extra text."
                )
            else:
                system_content = (
                    "Ты тренер по CS2. Тебе дан профиль игрока и список кандидатов "
                    "в тиммейты. Оцени, насколько каждый кандидат подходит игроку. "
                    "Верни ТОЛЬКО один JSON-объект, где ключи — user_id кандидатов, "
                    "а значения — объекты с полями 'score' (число от 0 до 1, чем выше, "
                    "тем лучше) и 'summary' (короткое объяснение на русском языке). "
                    "Не добавляй никакого дополнительного текста."
                )

            prompt = json.dumps(payload, ensure_ascii=False)

            headers = {
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            if self._is_openrouter_base_url():
                referer = getattr(settings, "WEBSITE_URL", "")
                app_title = getattr(settings, "APP_TITLE", "Faceit AI Bot")
                if referer:
                    headers["HTTP-Referer"] = referer
                headers["X-Title"] = app_title

            request_payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 400,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.groq_base_url,
                    headers=headers,
                    json=request_payload,
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(
                            "Groq teammate match error: %s - %s",
                            response.status,
                            text,
                        )
                        return {}
                    data = await response.json()
                    content = data["choices"][0]["message"][
                        "content"
                    ]

            text = content.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                cleaned_lines = [
                    line
                    for line in lines
                    if not line.strip().startswith("```")
                ]
                text = "\n".join(cleaned_lines).strip()

            try:
                parsed = json.loads(text)
                if isinstance(parsed, Dict):
                    self._log_sample(
                        task="teammates",
                        language=lang,
                        input_payload=payload,
                        output_payload=parsed,
                    )
                    return parsed
                return {}
            except json.JSONDecodeError:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        parsed = json.loads(text[start : end + 1])
                        if isinstance(parsed, Dict):
                            self._log_sample(
                                task="teammates",
                                language=lang,
                                input_payload=payload,
                                output_payload=parsed,
                            )
                            return parsed
                    except json.JSONDecodeError:
                        logger.error(
                            "Failed to parse teammate match JSON",
                            exc_info=True,
                        )
                return {}
        except Exception:
            logger.exception("Error in describe_teammate_matches")
            return {}

    def _build_analysis_prompt(
        self,
        stats: Dict,
        match_history: List[Dict],
        language: str = "ru",
    ) -> str:
        """Build analysis prompt.

        Used both for overall Faceit stats and for single-demo stats.
        Optionally includes extra context such as map, score and key moments
        when these fields are present in the stats dict.
        """
        lang = self._normalize_language(language)

        map_name = stats.get("map_name")
        total_rounds = stats.get("total_rounds")
        score_team1 = stats.get("score_team1")
        score_team2 = stats.get("score_team2")
        key_moments = stats.get("key_moments") or []

        # Build short optional context block (used mostly for demo analysis)
        extra_context_lines: List[str] = []
        if map_name and map_name != "unknown":
            if lang == "en":
                extra_context_lines.append(f"Map: {map_name}")
            else:
                extra_context_lines.append(f"Карта: {map_name}")

        if (isinstance(score_team1, (int, float)) and
                isinstance(score_team2, (int, float)) and
                total_rounds):
            if lang == "en":
                extra_context_lines.append(
                    f"Final score: {int(score_team1)}:{int(score_team2)} "
                    f"over {int(total_rounds)} rounds"
                )
            else:
                extra_context_lines.append(
                    f"Финальный счёт: {int(score_team1)}:{int(score_team2)} "
                    f"за {int(total_rounds)} раундов"
                )

        if key_moments and isinstance(key_moments, list):
            # Use up to 3 key moments to keep prompt compact
            snippets: List[str] = []
            for km in key_moments[:3]:
                try:
                    rn = km.get("round")
                    desc = km.get("description")
                    if rn is not None and desc:
                        if lang == "en":
                            snippets.append(f"round {rn}: {desc}")
                        else:
                            snippets.append(f"раунд {rn}: {desc}")
                except Exception:
                    continue
            if snippets:
                if lang == "en":
                    extra_context_lines.append(
                        "Key rounds in this match: " + "; ".join(snippets)
                    )
                else:
                    extra_context_lines.append(
                        "Ключевые раунды в этом матче: " + "; ".join(snippets)
                    )

        extra_context_block = "\n".join(extra_context_lines)

        if lang == "en":
            return f"""
            Analyze CS2 player statistics (and demo context if present).

            Current metrics:
            - K/D: {stats.get('kd_ratio', 'N/A')}
            - Headshot %: {stats.get('hs_percentage', 'N/A')}
            - Win Rate: {stats.get('win_rate', 'N/A')}
            - Average damage: {stats.get('avg_damage', 'N/A')}
            - Matches played (or demos considered): {stats.get('matches_played', 'N/A')}

            Recent matches (Faceit history): {len(match_history)}

            {extra_context_block}

            Provide a compact, structured analysis in ENGLISH:
            1. Strengths of the player
            2. Weaknesses
            3. Specific recommendations for improvement (as a list)
            4. Action plan for the next week
            Use no more than 6 bullet points in total and keep the answer under 250 words.
            """
        else:
            return f"""
            Проанализируй статистику игрока CS2 (и контекст демки, если он есть).

            Текущие показатели:
            - K/D: {stats.get('kd_ratio', 'N/A')}
            - Headshot %: {stats.get('hs_percentage', 'N/A')}
            - Win Rate: {stats.get('win_rate', 'N/A')}
            - Средний урон: {stats.get('avg_damage', 'N/A')}
            - Сыграно матчей (или учтённых демок): {stats.get('matches_played', 'N/A')}

            Количество недавних матчей (Faceit): {len(match_history)}

            {extra_context_block}

            Дай компактный, структурированный анализ на РУССКОМ языке:
            1. Сильные стороны игрока
            2. Слабые стороны
            3. Конкретные рекомендации по улучшению (списком)
            4. План действий на ближайшую неделю
            Используй не больше 6 пунктов всего и уложись примерно в 250 слов.
            """

    def _get_default_training_plan(self, language: str = "ru") -> Dict:
        """Default training plan used when AI plan is unavailable."""
        lang = self._normalize_language(language)
        if lang == "en":
            return {
                "daily_exercises": [
                    {
                        "name": "Aim Training",
                        "duration": 30,
                        "description": "Aim training on aim_botz",
                    },
                    {
                        "name": "Spray Control",
                        "duration": 20,
                        "description": "Recoil control for AK-47 and M4A4",
                    },
                ],
                "weekly_goals": [
                    "Increase accuracy by 5%",
                    "Improve K/D to 1.2",
                ],
                "estimated_time": "2-3 weeks",
            }
        else:
            return {
                "daily_exercises": [
                    {
                        "name": "Тренировка аима",
                        "duration": 30,
                        "description": "Тренировка аима на aim_botz и картах для практики",
                    },
                    {
                        "name": "Контроль спрея",
                        "duration": 20,
                        "description": "Отработка отдачи на AK-47 и M4A4",
                    },
                ],
                "weekly_goals": [
                    "Увеличить точность стрельбы на 5%",
                    "Довести K/D до 1.2",
                ],
                "estimated_time": "2-3 недели",
            }
