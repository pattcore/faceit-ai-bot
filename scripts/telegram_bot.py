import logging
import os
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import UploadFile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from src.server.database.models import User
from src.server.exceptions import DemoAnalysisException
from src.server.features.player_analysis.service import PlayerAnalysisService
from src.server.features.demo_analyzer.service import DemoAnalyzer
from src.server.features.teammates.models import TeammatePreferences
from src.server.features.teammates.service import TeammateService
from src.server.config.settings import settings


logger = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO)


player_service = PlayerAnalysisService()
demo_analyzer = DemoAnalyzer()
teammate_service = TeammateService()

MAX_DEMO_SIZE_MB = settings.MAX_DEMO_FILE_MB
MAX_DEMO_SIZE_BYTES = MAX_DEMO_SIZE_MB * 1024 * 1024
_SNIFF_BYTES = 4096

WAITING_NICKNAME, WAITING_ANALYZE_PARAMS, WAITING_TM_PARAMS, WAITING_DEMO = range(4)
user_session_data: dict[int, dict] = {}

if REDIS_AVAILABLE:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Telegram bot rate limiting enabled via Redis")
    except Exception:
        logger.exception("Failed to connect to Redis for Telegram bot rate limiting")
        redis_client = None
else:
    redis_client = None


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

    try:
        key = f"rl:bot:telegram:{operation}:{user_key}:minute"
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)
        if count > limit_per_minute:
            return False

        if limit_per_day is not None and limit_per_day > 0:
            day_suffix = datetime.utcnow().strftime("%Y%m%d")
            day_key = f"rl:bot:telegram:{operation}:{user_key}:day:{day_suffix}"
            day_count = await redis_client.incr(day_key)
            if day_count == 1:
                await redis_client.expire(day_key, 86400)
            if day_count > limit_per_day:
                return False

        return True
    except Exception as e:
        logger.error("Telegram bot rate limit error: %s", e)
        return True


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
    await query.answer()

    user_id = query.from_user.id if query.from_user else 0

    if query.data == "menu_stats":
        user_session_data[user_id] = {"action": "stats"}
        await query.edit_message_text(
            "📊 Статистика игрока\n\n"
            "Отправь Faceit ник игрока для получения статистики.\n\n"
            "Пример: s1mple",
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
            "Примеры:\n  s1mple\n  s1mple en",
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
            "Примеры:\n  1500 2000\n  1500 2000 ru\n  1500 2000 ru rifler",
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
            "Опционально в подписи к файлу можно указать язык: ru или en.",
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
    await update.effective_chat.send_message(
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
    await update.effective_chat.send_message(
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
    await update.effective_chat.send_message(
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
    await update.effective_chat.send_message(
        "Готово. Вернуться в главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(
        "Привет! Я Faceit AI Bot в Telegram.\n\n"
        "Выбери нужный раздел в меню ниже "
        "или используй команды вручную: /faceit_stats, /faceit_analyze, /tm_find, /demo_analyze.",
        reply_markup=get_main_menu_keyboard(),
    )


async def cmd_faceit_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"
    if not await check_bot_rate_limit(
        user_key,
        "faceit_stats",
        limit_per_minute=20,
        limit_per_day=200,
    ):
        await update.effective_chat.send_message(
            "Превышен лимит запросов для этой команды, попробуй позже.",
        )
        return

    if not context.args:
        await update.effective_chat.send_message(
            "Использование: /faceit_stats <faceit_ник>"
        )
        return

    nickname = context.args[0]
    await update.effective_chat.send_message("Ищу статистику, подожди...")

    stats = await player_service.get_player_stats(nickname)
    if not stats:
        await update.effective_chat.send_message(
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

    await update.effective_chat.send_message("\n".join(lines))


async def cmd_faceit_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"
    if not await check_bot_rate_limit(
        user_key,
        "faceit_analyze",
        limit_per_minute=5,
        limit_per_day=50,
    ):
        await update.effective_chat.send_message(
            "Превышен лимит AI-анализов для этой команды, попробуй позже.",
        )
        return

    if not context.args:
        await update.effective_chat.send_message(
            "Использование: /faceit_analyze <faceit_ник> [ru|en]"
        )
        return

    nickname = context.args[0]
    language: str = "ru"
    if len(context.args) > 1 and context.args[1] in {"ru", "en"}:
        language = context.args[1]

    await update.effective_chat.send_message(
        f"Делаю AI-анализ игрока {nickname} ({language})..."
    )

    analysis = await player_service.analyze_player(nickname, language=language)
    if not analysis:
        await update.effective_chat.send_message(
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

    await update.effective_chat.send_message("\n".join(lines))


async def cmd_tm_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_chat.send_message(
            "Использование: /tm_find <min_elo> <max_elo> [lang] [role]"
        )
        return

    user = update.effective_user
    user_key = f"{user.id if user else 0}"
    if not await check_bot_rate_limit(
        user_key,
        "tm_find",
        limit_per_minute=5,
        limit_per_day=50,
    ):
        await update.effective_chat.send_message(
            "Превышен лимит запросов для этой команды, попробуй позже.",
        )
        return

    try:
        min_elo = int(context.args[0])
        max_elo = int(context.args[1])
    except ValueError:
        await update.effective_chat.send_message(
            "min_elo и max_elo должны быть целыми числами"
        )
        return

    language = context.args[2] if len(context.args) > 2 else "ru"
    role = context.args[3] if len(context.args) > 3 else "any"

    await update.effective_chat.send_message(
        f"Ищу тиммейтов {min_elo}-{max_elo} ELO, язык {language}, роль {role}..."
    )

    db = SessionLocal()
    try:
        user = User(
            id=0,
            username=f"telegram_{update.effective_user.id}",
            email=f"telegram_{update.effective_user.id}@local",
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
            await update.effective_chat.send_message(
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
            if p.match_summary:
                lines.append("Кратко: " + p.match_summary[:200])

        await update.effective_chat.send_message("\n".join(lines))
    finally:
        db.close()


async def cmd_demo_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_key = f"{user.id if user else 0}"
    if not await check_bot_rate_limit(
        user_key,
        "demo_analyze",
        limit_per_minute=3,
        limit_per_day=10,
    ):
        await update.effective_chat.send_message(
            "Превышен лимит анализов демок для этой команды, попробуй позже.",
        )
        return

    message = update.effective_message
    args = context.args
    language = "ru"
    if args and args[0] in {"ru", "en"}:
        language = args[0]

    if not message.document:
        await update.effective_chat.send_message(
            "Пришли команду так: /demo_analyze [ru|en] и прикрепи .dem файл в том же сообщении."
        )
        return

    doc = message.document
    filename = doc.file_name or ""
    if not filename.lower().endswith(".dem"):
        await update.effective_chat.send_message(
            "Нужен файл демки с расширением .dem"
        )
        return

    if doc.file_size and doc.file_size > MAX_DEMO_SIZE_BYTES:
        await update.effective_chat.send_message(
            f"Файл слишком большой. Максимальный размер {MAX_DEMO_SIZE_MB} МБ."
        )
        return

    await update.effective_chat.send_message(
        "Скачиваю и анализирую демку, это может занять время..."
    )

    telegram_file = await doc.get_file()
    buffer = BytesIO()
    await telegram_file.download_to_memory(out=buffer)
    buffer.seek(0)

    snippet = buffer.read(_SNIFF_BYTES)
    if not snippet:
        await update.effective_chat.send_message(
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
        await update.effective_chat.send_message(
            "Похоже, это не бинарная демка CS2. Пришли корректный .dem файл."
        )
        return

    buffer.seek(0)

    upload = UploadFile(filename=filename, file=buffer)  # type: ignore[arg-type]
    try:
        analysis = await demo_analyzer.analyze_demo(upload, language=language)
    except DemoAnalysisException as exc:
        detail = getattr(exc, "detail", None)
        message = "Не удалось проанализировать демку."
        if isinstance(detail, dict):
            message = str(detail.get("error") or detail) or message
        elif isinstance(detail, str):
            message = detail or message
        await update.effective_chat.send_message(message)
        return
    except Exception:
        logger.exception("Telegram demo_analyze failed")
        await update.effective_chat.send_message(
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

    await update.effective_chat.send_message("\n".join(lines))


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

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_main_menu_button, pattern="^menu_"),
        ],
        states={
            WAITING_NICKNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stats_nickname),
            ],
            WAITING_ANALYZE_PARAMS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_analyze_params,
                ),
            ],
            WAITING_TM_PARAMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tm_params),
            ],
            WAITING_DEMO: [
                MessageHandler(filters.Document.ALL, handle_demo_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(handle_back_to_main, pattern="^back_main$"),
        ],
    )

    app.add_handler(conv_handler)

    logger.info("Starting Telegram bot...")
    app.run_polling(allowed_updates=["message", "edited_message", "callback_query"])


if __name__ == "__main__":
    main()
