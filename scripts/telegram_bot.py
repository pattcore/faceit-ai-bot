import logging
import os
import time
import asyncio
from datetime import datetime
from functools import wraps
from io import BytesIO
from typing import Optional

from fastapi import UploadFile
import httpx
from prometheus_client import Counter, Histogram, start_http_server
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore[assignment]

from src.server.database.connection import SessionLocal
from src.server.database.models import User, Subscription, SubscriptionTier
from src.server.exceptions import DemoAnalysisException
from src.server.features.player_analysis.service import PlayerAnalysisService
from src.server.features.demo_analyzer.service import DemoAnalyzer
from src.server.features.teammates.models import TeammatePreferences
from src.server.features.teammates.service import TeammateService
from src.server.config.settings import settings


logger = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO)


BOT_COMMANDS_TOTAL = Counter(
    "bot_commands_total",
    "Total bot commands handled",
    ["bot", "command", "status"],
)


BOT_COMMAND_DURATION_SECONDS = Histogram(
    "bot_command_duration_seconds",
    "Bot command handling duration in seconds",
    ["bot", "command"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)


BOT_RATE_LIMIT_DENIED_TOTAL = Counter(
    "bot_rate_limit_denied_total",
    "Total bot rate limit denials",
    ["bot", "operation"],
)


player_service = PlayerAnalysisService()
demo_analyzer = DemoAnalyzer()
teammate_service = TeammateService()

_tg_limit_mb = int(os.getenv("TELEGRAM_MAX_DEMO_FILE_MB", str(settings.MAX_DEMO_FILE_MB)))
MAX_DEMO_SIZE_MB = min(settings.MAX_DEMO_FILE_MB, _tg_limit_mb)
MAX_DEMO_SIZE_BYTES = MAX_DEMO_SIZE_MB * 1024 * 1024
_SNIFF_BYTES = 4096

API_INTERNAL_URL = os.getenv("API_INTERNAL_URL", "http://api:8000").rstrip("/")
DEMO_UPLOAD_API_URL = os.getenv("DEMO_UPLOAD_API_URL", API_INTERNAL_URL).rstrip("/")

WAITING_NICKNAME, WAITING_ANALYZE_PARAMS, WAITING_TM_PARAMS, WAITING_DEMO = range(4)
user_session_data: dict[int, dict] = {}

if REDIS_AVAILABLE:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    BOT_REDIS_TIMEOUT_SECONDS = float(os.getenv("BOT_REDIS_TIMEOUT_SECONDS", "1"))
    try:
        redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info("Telegram bot rate limiting enabled via Redis")
    except Exception:
        logger.exception("Failed to connect to Redis for Telegram bot rate limiting")
        redis_client = None
else:
    redis_client = None


ADMIN_STEAM_IDS = {x.strip() for x in os.getenv("ADMIN_STEAM_IDS", "").split(",") if x.strip()}
ADMIN_BIND_TTL_SECONDS = int(os.getenv("ADMIN_BIND_TTL_SECONDS", "31536000"))
BOT_BYPASS_STEAM_IDS = {x.strip() for x in os.getenv("BOT_BYPASS_STEAM_IDS", "").split(",") if x.strip()}


def has_active_paid_subscription(db: SessionLocal, steam_id: str) -> bool:
    user = db.query(User).filter(User.steam_id == steam_id).first()
    if user is None:
        return False

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.is_active == True)
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    if subscription is None:
        return False

    now = datetime.utcnow()
    if subscription.expires_at is not None and subscription.expires_at < now:
        return False

    tier = subscription.tier
    if isinstance(tier, SubscriptionTier):
        return tier != SubscriptionTier.FREE
    try:
        return SubscriptionTier(tier) != SubscriptionTier.FREE
    except Exception:
        return False


async def is_subscriber_telegram(user_key: str) -> bool:
    if redis_client is None:
        return False
    try:
        v = await asyncio.wait_for(
            redis_client.get(f"rl:bot:telegram:subscriber:{user_key}"),
            timeout=BOT_REDIS_TIMEOUT_SECONDS,
        )
        return v == "1"
    except Exception:
        return False

async def is_admin_telegram(user_key: str) -> bool:
    if redis_client is None:
        return False
    try:
        v = await asyncio.wait_for(redis_client.get(f"rl:bot:telegram:admin:{user_key}"), timeout=BOT_REDIS_TIMEOUT_SECONDS)
        return v == "1"
    except Exception:
        return False

async def check_bot_rate_limit(
    user_key: str,
    operation: str,
    limit_per_minute: int,
    limit_per_day: Optional[int] = None,
) -> bool:
    """Rate limit Telegram bot commands per user.

    Returns True if allowed, False if limit exceeded.
    """
    if redis_client is None:
        return True

    if await is_admin_telegram(user_key):
        return True

    if await is_subscriber_telegram(user_key):
        return True

    try:
        key = f"rl:bot:telegram:{operation}:{user_key}:minute"
        count = await asyncio.wait_for(redis_client.incr(key), timeout=1.0)
        if count == 1:
            await asyncio.wait_for(redis_client.expire(key, 60), timeout=1.0)
        if count > limit_per_minute:
            try:
                BOT_RATE_LIMIT_DENIED_TOTAL.labels(bot="telegram", operation=operation).inc()
            except Exception:
                logger.exception("Failed to update Telegram bot rate limit metric")
            return False

        if limit_per_day is not None and limit_per_day > 0:
            day_suffix = datetime.utcnow().strftime("%Y%m%d")
            day_key = f"rl:bot:telegram:{operation}:{user_key}:day:{day_suffix}"
            day_count = await asyncio.wait_for(redis_client.incr(day_key), timeout=1.0)
            if day_count == 1:
                await asyncio.wait_for(redis_client.expire(day_key, 86400), timeout=1.0)
            if day_count > limit_per_day:
                try:
                    BOT_RATE_LIMIT_DENIED_TOTAL.labels(bot="telegram", operation=operation).inc()
                except Exception:
                    logger.exception("Failed to update Telegram bot rate limit metric")
                return False

        return True
    except Exception as e:
        logger.error("Telegram bot rate limit error: %s", e)
        return True


def track_telegram_command(command_name: str):
    """Decorator to record command count, status and latency for Telegram commands."""

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            start_time = time.perf_counter()
            status = "success"
            try:
                return await func(update, context, *args, **kwargs)
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.perf_counter() - start_time
                try:
                    BOT_COMMANDS_TOTAL.labels(
                        bot="telegram",
                        command=command_name,
                        status=status,
                    ).inc()
                    BOT_COMMAND_DURATION_SECONDS.labels(
                        bot="telegram",
                        command=command_name,
                    ).observe(duration)
                except Exception:
                    logger.exception("Failed to update Telegram bot Prometheus metrics")

        return wrapper

    return decorator


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Статистика игрока", callback_data="menu_stats")],
        [InlineKeyboardButton("🤖 AI-анализ игрока", callback_data="menu_analyze")],
        [InlineKeyboardButton("👥 Поиск тиммейтов", callback_data="menu_teammates")],
        [InlineKeyboardButton("🎮 Анализ демки", callback_data="menu_demo")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="menu_help")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_main_menu_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    user_id = query.from_user.id if query.from_user else 0

    if query.data == "menu_stats":
        user_session_data[user_id] = {"action": "stats"}
        await query.edit_message_text(
            "📊 Статистика игрока\n\n"
            "Отправь Faceit ник игрока для получения статистики.\n\n"
            "Пример: s1mple\n\n"
            "Можно нажать /cancel, чтобы выйти в меню.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
            ),
        )
        return WAITING_NICKNAME

    if query.data == "menu_analyze":
        user_session_data[user_id] = {"action": "analyze"}
        await query.edit_message_text(
            "🤖 AI-анализ игрока\n\n"
            "Отправь Faceit ник для глубокого анализа.\n"
            "Можно добавить язык (ru/en) через пробел.\n\n"
            "Примеры:\n  s1mple\n  s1mple en\n\n"
            "Можно нажать /cancel, чтобы выйти в меню.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
            ),
        )
        return WAITING_ANALYZE_PARAMS

    if query.data == "menu_teammates":
        user_session_data[user_id] = {"action": "teammates"}
        await query.edit_message_text(
            "👥 Поиск тиммейтов\n\n"
            "Отправь параметры поиска:\n"
            "<min_elo> <max_elo> [язык] [роль]\n\n"
            "Примеры:\n  1500 2000\n  1500 2000 ru\n  1500 2000 ru rifler\n\n"
            "Можно нажать /cancel, чтобы выйти в меню.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
            ),
        )
        return WAITING_TM_PARAMS

    if query.data == "menu_demo":
        user_session_data[user_id] = {"action": "demo"}
        await query.edit_message_text(
            "🎮 Анализ демки\n\n"
            "Пришли сюда демку CS2 в файле .dem.\n"
            "Опционально в подписи к файлу можно указать язык: ru или en.\n\n"
            "Можно нажать /cancel, чтобы выйти в меню.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
            ),
        )
        return WAITING_DEMO

    if query.data == "menu_help":
        await query.edit_message_text(
            "ℹ️ Помощь\n\n"
            "Я могу:\n"
            "• Показать Faceit статистику\n"
            "• Сделать AI-анализ игрока\n"
            "• Подобрать тиммейтов по ELO\n"
            "• Проанализировать демку CS2\n\n"
            "Выбери нужный пункт в меню ниже.",
            reply_markup=get_main_menu_keyboard(),
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "Главное меню Faceit AI Bot:", reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def handle_back_to_main(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    user_id = query.from_user.id if query.from_user else 0
    user_session_data.pop(user_id, None)

    await query.edit_message_text(
        "Главное меню Faceit AI Bot:", reply_markup=get_main_menu_keyboard()
    )


async def handle_stats_nickname(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message = update.effective_message
    if not message or not message.text:
        return WAITING_NICKNAME

    nickname = message.text.strip().split()[0]
    context.args = [nickname]
    await cmd_faceit_stats(update, context)

    chat = update.effective_chat
    if chat is None:
        return ConversationHandler.END

    await chat.send_message(
        "Готово. Вернуться в главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_analyze_params(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message = update.effective_message
    if not message or not message.text:
        return WAITING_ANALYZE_PARAMS

    parts = message.text.strip().split()
    if not parts:
        return WAITING_ANALYZE_PARAMS

    context.args = parts[:2]
    await cmd_faceit_analyze(update, context)

    chat = update.effective_chat
    if chat is None:
        return ConversationHandler.END

    await chat.send_message(
        "Готово. Вернуться в главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_tm_params(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message = update.effective_message
    if not message or not message.text:
        return WAITING_TM_PARAMS

    parts = message.text.strip().split()
    context.args = parts
    await cmd_tm_find(update, context)

    chat = update.effective_chat
    if chat is None:
        return ConversationHandler.END

    await chat.send_message(
        "Готово. Вернуться в главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def handle_demo_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message = update.effective_message
    if not message or not message.document:
        return WAITING_DEMO

    caption_parts = (
        (message.caption or "").strip().split() if message.caption else []
    )
    args: list[str] = []
    if caption_parts and caption_parts[0] in {"ru", "en"}:
        args = [caption_parts[0]]

    context.args = args
    await cmd_demo_analyze(update, context)

    chat = update.effective_chat
    if chat is None:
        return ConversationHandler.END

    await chat.send_message(
        "Готово. Вернуться в главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    chat = update.effective_chat
    if chat is None:
        return ConversationHandler.END

    await chat.send_message(
        "Диалог отменён. Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


@track_telegram_command("start")
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    await chat.send_message(
        "Привет! Я Faceit AI Bot в Telegram.\n\n"
        "Выбери нужный раздел в меню ниже.",
        reply_markup=get_main_menu_keyboard(),
    )


@track_telegram_command("faceit_stats")
async def cmd_faceit_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"

    chat = update.effective_chat
    if chat is None:
        return
    if not await check_bot_rate_limit(
        user_key,
        "faceit_stats",
        limit_per_minute=20,
        limit_per_day=200,
    ):
        await chat.send_message(
            "Превышен лимит запросов для этой команды, попробуй позже.",
        )
        return

    if not context.args:
        await chat.send_message(
            "Использование: /faceit_stats <faceit_ник>"
        )
        return

    nickname = context.args[0]
    await chat.send_message("Ищу статистику, подожди...")

    stats = await player_service.get_player_stats(nickname)
    if not stats:
        await chat.send_message(
            f"Не удалось найти статистику для {nickname}"
        )
        return

    game_data = stats.get("stats", {}).get("lifetime", {})
    elo = stats.get("elo")
    level = stats.get("level")
    kd_ratio = game_data.get("Average K/D Ratio") or game_data.get("K/D Ratio")
    winrate = game_data.get("Win Rate %")

    lines = [f"Статистика Faceit для {nickname}:"]
    if elo is not None:
        lines.append(f"ELO: {elo}")
    if level is not None:
        lines.append(f"Уровень: {level}")
    if kd_ratio is not None:
        lines.append(f"K/D: {kd_ratio}")
    if winrate is not None:
        lines.append(f"Winrate %: {winrate}")

    await chat.send_message("\n".join(lines))


@track_telegram_command("demo_analyze_url")
async def cmd_demo_analyze_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"

    chat = update.effective_chat
    if chat is None:
        return
    if not await check_bot_rate_limit(
        user_key,
        "demo_analyze",
        limit_per_minute=3,
        limit_per_day=10,
    ):
        await chat.send_message(
            "Превышен лимит анализов демок для этой команды, попробуй позже.",
        )
        return

    args = context.args or []
    language = "ru"
    if args and args[0] in {"ru", "en"}:
        language = args[0]
        args = args[1:]

    if not args:
        await chat.send_message(
            "Пришли команду так: /demo_analyze_url [ru|en] <прямая ссылка на .dem>"
        )
        return

    url = args[0]
    if not (url.startswith("http://") or url.startswith("https://")):
        await chat.send_message("Нужна http/https ссылка на .dem файл.")
        return

    await chat.send_message("Скачиваю демку по ссылке и запускаю анализ...")

    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            submit = await client.post(
                f"{DEMO_UPLOAD_API_URL}/demo/analyze/url/background",
                json={
                    "url": url,
                    "language": language,
                    "user_id": str(user.id) if user else None,
                },
            )
        except Exception:
            logger.exception("Telegram demo_analyze_url submit failed")
            await chat.send_message("Не удалось отправить демку на анализ (ошибка сети).")
            return

        if submit.status_code >= 400:
            try:
                payload = submit.json()
                detail = payload.get("detail")
            except Exception:
                detail = None
            await chat.send_message(str(detail or "Не удалось отправить демку на анализ."))
            return

        task_id = submit.json().get("task_id")
        if not task_id:
            await chat.send_message("Не удалось получить task_id для анализа демки.")
            return

        await chat.send_message("Анализ запущен. Жду результат...")

        max_wait_seconds = int(os.getenv("BOT_DEMO_URL_MAX_WAIT_SECONDS", "480"))
        poll_interval = float(os.getenv("BOT_DEMO_URL_POLL_SECONDS", "3"))
        deadline = time.time() + max_wait_seconds

        last_status: Optional[str] = None
        while time.time() < deadline:
            try:
                status_resp = await client.get(f"{DEMO_UPLOAD_API_URL}/tasks/status/{task_id}")
            except Exception:
                logger.exception("Telegram demo_analyze_url status check failed")
                await chat.send_message("Не удалось получить статус задачи анализа.")
                return

            if status_resp.status_code >= 400:
                await chat.send_message("Не удалось получить статус задачи анализа.")
                return

            status_payload = status_resp.json()
            celery_status = status_payload.get("status")
            if celery_status and celery_status != last_status:
                last_status = celery_status

            if celery_status in {"SUCCESS", "FAILURE", "REVOKED"}:
                if celery_status != "SUCCESS":
                    await chat.send_message("Анализ не удался. Попробуй другую демку/ссылку.")
                    return

                result = (status_payload.get("result") or {})
                analysis = ((result.get("analysis") or {}) if isinstance(result, dict) else {})
                metadata = analysis.get("metadata") or {}
                coach = analysis.get("coach_report") or {}

                lines = [
                    f"Анализ демки {metadata.get('map_name', 'unknown')}",
                    f"Матч: {metadata.get('match_id', 'unknown')}",
                    f"Счёт: {metadata.get('score', {})}",
                    "",
                ]

                summary = coach.get("summary") if isinstance(coach, dict) else None
                if summary:
                    lines.append("Краткий вывод коуча:")
                    lines.append(str(summary)[:1000])
                else:
                    recs = analysis.get("recommendations") or []
                    if recs:
                        lines.append("Рекомендации:")
                        for rec in recs[:5]:
                            lines.append(f"- {rec}")

                await chat.send_message("\n".join(lines))
                return

            await asyncio.sleep(poll_interval)

        await chat.send_message(
            f"Анализ ещё выполняется. Task ID: {task_id}"
        )


@track_telegram_command("faceit_analyze")
async def cmd_faceit_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"

    chat = update.effective_chat
    if chat is None:
        return
    if not await check_bot_rate_limit(
        user_key,
        "faceit_analyze",
        limit_per_minute=5,
        limit_per_day=50,
    ):
        await chat.send_message(
            "Превышен лимит AI-анализов для этой команды, попробуй позже.",
        )
        return

    if not context.args:
        await chat.send_message(
            "Использование: /faceit_analyze <faceit_ник> [ru|en]"
        )
        return

    nickname = context.args[0]
    language: str = "ru"
    if len(context.args) > 1 and context.args[1] in {"ru", "en"}:
        language = context.args[1]

    await chat.send_message(
        f"Делаю AI-анализ игрока {nickname} ({language})..."
    )

    analysis = await player_service.analyze_player(nickname, language=language)
    if not analysis:
        await chat.send_message(
            f"Не удалось проанализировать игрока {nickname}"
        )
        return

    strengths = analysis.strengths
    weaknesses = analysis.weaknesses
    training_plan = analysis.training_plan

    lines = [
        f"AI-анализ игрока {nickname}:",
        f"Общий рейтинг: {analysis.overall_rating}",
        "",
        "Сильные стороны:",
        f"  Aim: {strengths.aim}",
        f"  Game sense: {strengths.game_sense}",
        f"  Positioning: {strengths.positioning}",
        f"  Teamwork: {strengths.teamwork}",
        f"  Consistency: {strengths.consistency}",
        "",
        f"Слабые стороны (priority: {weaknesses.priority}):",
    ]
    for area in weaknesses.areas:
        lines.append(f"  - {area}")

    lines.append("")
    lines.append("Рекомендации:")
    for rec in weaknesses.recommendations:
        lines.append(f"  - {rec}")

    lines.append("")
    lines.append("Тренировочный план:")
    if training_plan.focus_areas:
        lines.append("Фокус: " + ", ".join(training_plan.focus_areas))
    if training_plan.daily_exercises:
        lines.append("Ежедневные упражнения:")
        for ex in training_plan.daily_exercises[:5]:
            if isinstance(ex, dict):
                name = ex.get("name") or "Упражнение"
                duration = ex.get("duration") or ""
                description = ex.get("description") or ""
                line = f"  - {name}"
                if duration:
                    line += f" ({duration})"
                if description:
                    line += f": {description}"
                lines.append(line)
            else:
                lines.append(f"  - {ex}")
    if training_plan.estimated_time:
        lines.append(f"Оценочный срок: {training_plan.estimated_time}")

    await chat.send_message("\n".join(lines))


@track_telegram_command("tm_find")
async def cmd_tm_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None:
        return

    args = context.args or []
    if len(args) < 2:
        await chat.send_message(
            "Использование: /tm_find <min_elo> <max_elo> [lang] [role]"
        )
        return

    user = update.effective_user
    user_id = user.id if user else 0
    user_key = f"{user_id}"
    if not await check_bot_rate_limit(
        user_key,
        "tm_find",
        limit_per_minute=5,
        limit_per_day=50,
    ):
        await chat.send_message(
            "Превышен лимит запросов для этой команды, попробуй позже.",
        )
        return

    try:
        min_elo = int(args[0])
        max_elo = int(args[1])
    except ValueError:
        await chat.send_message(
            "min_elo и max_elo должны быть целыми числами"
        )
        return

    language = args[2] if len(args) > 2 else "ru"
    role = args[3] if len(args) > 3 else "any"

    await chat.send_message(
        f"Ищу тиммейтов {min_elo}-{max_elo} ELO, язык {language}, роль {role}..."
    )

    db = SessionLocal()
    try:
        user = User(
            id=0,
            username=f"telegram_{user_id}",
            email=f"telegram_{user_id}@local",
            hashed_password="",
        )

        prefs = TeammatePreferences(
            min_elo=min_elo,
            max_elo=max_elo,
            preferred_maps=[],
            preferred_roles=[] if role == "any" else [role],
            communication_lang=[language],
            play_style="unknown",
            time_zone="unknown",
        )

        profiles = await teammate_service.find_teammates(
            db=db,
            current_user=user,
            preferences=prefs,
        )

        if not profiles:
            await chat.send_message(
                "Не нашёл подходящих тиммейтов по заданным параметрам."
            )
            return

        lines = ["Найденные тиммейты:"]
        for p in profiles[:5]:
            score = (
                f"{p.compatibility_score:.1f}"
                if p.compatibility_score is not None
                else "—"
            )
            lines.append(
                f"\n{p.faceit_nickname or 'Неизвестный игрок'} (score: {score})"
            )
            lines.append(f"ELO: {p.stats.faceit_elo}")
            langs = ", ".join(p.preferences.communication_lang) or "—"
            roles = ", ".join(p.preferences.preferred_roles) or "—"
            lines.append(f"Языки: {langs}")
            lines.append(f"Роли: {roles}")
            lines.append(f"Стиль: {p.preferences.play_style}")
            contact_parts: list[str] = []
            if p.discord_contact:
                contact_parts.append(f"Discord: {p.discord_contact}")
            if p.telegram_contact:
                contact_parts.append(f"Telegram: {p.telegram_contact}")
            if p.contact_url:
                contact_parts.append(f"Ссылка: {p.contact_url}")
            if contact_parts:
                lines.append("Контакты:")
                for part in contact_parts:
                    lines.append(f"  - {part}")
            if p.match_summary:
                lines.append("Кратко: " + p.match_summary[:200])

        await chat.send_message("\n".join(lines))
    finally:
        db.close()


@track_telegram_command("demo_analyze")
async def cmd_demo_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"

    chat = update.effective_chat
    if chat is None:
        return
    if not await check_bot_rate_limit(
        user_key,
        "demo_analyze",
        limit_per_minute=3,
        limit_per_day=10,
    ):
        await chat.send_message(
            "Превышен лимит анализов демок для этой команды, попробуй позже.",
        )
        return

    message = update.effective_message
    args = context.args or []
    language = "ru"
    if args and args[0] in {"ru", "en"}:
        language = args[0]

    if not message or not message.document:
        await chat.send_message(
            "Пришли команду так: /demo_analyze [ru|en] и прикрепи .dem файл в том же сообщении."
        )
        return

    doc = message.document
    filename = doc.file_name or ""
    if not filename.lower().endswith(".dem"):
        await chat.send_message(
            "Нужен файл демки с расширением .dem"
        )
        return

    if doc.file_size and doc.file_size > MAX_DEMO_SIZE_BYTES:
        await chat.send_message(
            f"Файл слишком большой. Максимальный размер {MAX_DEMO_SIZE_MB} МБ.\n"
            "Если демка больше — загрузи её по ссылке и используй /demo_analyze_url.\n"
            "Пример: /demo_analyze_url https://uploads.pattmsc.online/demos/your_demo.dem"
        )
        return

    await chat.send_message(
        "Скачиваю и анализирую демку, это может занять время..."
    )

    try:
        telegram_file = await doc.get_file()
    except BadRequest as exc:
        if "File is too big" in str(exc):
            await chat.send_message(
                f"Файл слишком большой для скачивания через Telegram. Максимальный размер {MAX_DEMO_SIZE_MB} МБ.\n"
                "Если демка больше — загрузи её по ссылке и используй /demo_analyze_url.\n"
                "Пример: /demo_analyze_url https://uploads.pattmsc.online/demos/your_demo.dem"
            )
            return
        raise
    buffer = BytesIO()
    await telegram_file.download_to_memory(out=buffer)
    buffer.seek(0)

    snippet = buffer.read(_SNIFF_BYTES)
    if not snippet:
        await chat.send_message(
            "Файл пустой, пришли, пожалуйста, валидную демку .dem."
        )
        return

    sniff = snippet.lower()
    suspicious_markers = (
        b"<html",
        b"<script",
        b"<?php",
        b"#!/bin/bash",
        b"#!/usr/bin/env",
        b"import os",
        b"import sys",
    )
    if any(marker in sniff for marker in suspicious_markers):
        await chat.send_message(
            "Похоже, это не бинарная демка CS2. Пришли корректный .dem файл."
        )
        return

    buffer.seek(0)

    upload = UploadFile(filename=filename, file=buffer)
    try:
        analysis = await demo_analyzer.analyze_demo(upload, language=language)
    except DemoAnalysisException as exc:
        detail = getattr(exc, "detail", None)
        error_message = "Не удалось проанализировать демку."
        if isinstance(detail, dict):
            error_message = str(detail.get("error") or detail) or error_message
        elif isinstance(detail, str):
            error_message = detail or error_message
        await chat.send_message(error_message)
        return
    except Exception:
        logger.exception("Telegram demo_analyze failed")
        await chat.send_message(
            "Произошла внутренняя ошибка при анализе демки."
        )
        return

    metadata = analysis.metadata
    coach = analysis.coach_report

    lines = [
        f"Анализ демки {metadata.map_name}",
        f"Матч: {metadata.match_id}",
        f"Счёт: {metadata.score}",
        "",
    ]

    if coach and coach.summary:
        lines.append("Краткий вывод коуча:")
        lines.append(coach.summary[:1000])
    elif analysis.recommendations:
        lines.append("Рекомендации:")
        for rec in analysis.recommendations[:5]:
            lines.append(f"- {rec}")

    await chat.send_message("\n".join(lines))




@track_telegram_command("admin_bind")
async def cmd_admin_bind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    if redis_client is None:
        await update.effective_message.reply_text("Redis недоступен, привязка админа временно невозможна.")
        return

    args = context.args or []
    steam_id = (args[0].strip() if args else "")
    if not steam_id:
        await update.effective_message.reply_text("Использование: /admin_bind <steam_id>")
        return

    if ADMIN_STEAM_IDS and steam_id not in ADMIN_STEAM_IDS:
        await update.effective_message.reply_text("SteamID не разрешён для админ-привязки.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.steam_id == steam_id).first()
    finally:
        db.close()

    if user is None:
        await update.effective_message.reply_text("Не нашёл пользователя с таким SteamID в базе.")
        return

    tg_id = str(update.effective_user.id)
    try:
        await asyncio.wait_for(redis_client.set(f"rl:bot:telegram:admin:{tg_id}", "1", ex=ADMIN_BIND_TTL_SECONDS), timeout=BOT_REDIS_TIMEOUT_SECONDS)
    except Exception:
        await update.effective_message.reply_text("Не удалось записать флаг админа в Redis.")
        return

    await update.effective_message.reply_text("Готово: админ-привязка установлена, лимиты для тебя отключены.")


@track_telegram_command("sub_bind")
async def cmd_sub_bind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return
    if redis_client is None:
        await update.effective_message.reply_text(
            "Redis недоступен, привязка подписчика временно невозможна."
        )
        return

    args = context.args or []
    steam_id = (args[0].strip() if args else "")
    if not steam_id:
        await update.effective_message.reply_text("Использование: /sub_bind <steam_id>")
        return

    if BOT_BYPASS_STEAM_IDS and steam_id not in BOT_BYPASS_STEAM_IDS:
        db = SessionLocal()
        try:
            if not has_active_paid_subscription(db, steam_id=steam_id):
                await update.effective_message.reply_text(
                    "У этого SteamID нет активной подписки."
                )
                return
        finally:
            db.close()

    tg_id = str(update.effective_user.id)
    try:
        await asyncio.wait_for(
            redis_client.set(
                f"rl:bot:telegram:subscriber:{tg_id}",
                "1",
                ex=ADMIN_BIND_TTL_SECONDS,
            ),
            timeout=BOT_REDIS_TIMEOUT_SECONDS,
        )
    except Exception:
        await update.effective_message.reply_text("Не удалось записать флаг подписчика в Redis.")
        return

    await update.effective_message.reply_text(
        "Готово: подписка привязана, лимиты для тебя отключены."
    )
def main() -> None:
    token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("faceit_stats", cmd_faceit_stats))
    app.add_handler(CommandHandler("faceit_analyze", cmd_faceit_analyze))
    app.add_handler(CommandHandler("tm_find", cmd_tm_find))
    app.add_handler(CommandHandler("demo_analyze", cmd_demo_analyze))
    app.add_handler(CommandHandler("demo_analyze_url", cmd_demo_analyze_url))

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
        ],
        states={
            WAITING_NICKNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stats_nickname),
                CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
            ],
            WAITING_ANALYZE_PARAMS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_analyze_params,
                ),
                CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
            ],
            WAITING_TM_PARAMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tm_params),
                CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
            ],
            WAITING_DEMO: [
                MessageHandler(filters.Document.ALL, handle_demo_message),
                CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(handle_back_to_main, pattern="^back_main$"),
            CommandHandler("cancel", cancel_conversation),
        ],
    )

    app.add_handler(conv_handler)

    metrics_port = int(os.getenv("TELEGRAM_METRICS_PORT", "9102"))
    start_http_server(metrics_port)
    logger.info(
        "Starting Telegram bot Prometheus metrics server on port %s", metrics_port
    )

    logger.info("Starting Telegram bot...")
    app.run_polling(allowed_updates=["message", "edited_message", "callback_query"])


if __name__ == "__main__":
    main()
