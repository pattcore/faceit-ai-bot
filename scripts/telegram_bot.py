import logging
import os
from io import BytesIO
from typing import Optional

from fastapi import UploadFile
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from src.server.database.connection import SessionLocal
from src.server.database.models import User
from src.server.features.player_analysis.service import PlayerAnalysisService
from src.server.features.demo_analyzer.service import DemoAnalyzer
from src.server.features.teammates.models import TeammatePreferences
from src.server.features.teammates.service import TeammateService


logger = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO)


player_service = PlayerAnalysisService()
demo_analyzer = DemoAnalyzer()
teammate_service = TeammateService()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message(
        "Привет! Я Faceit AI Bot в Telegram.\n"
        "Команды:\n"
        "/faceit_stats <ник> — быстрая стата\n"
        "/faceit_analyze <ник> [ru|en] — AI-анализ игрока\n"
        "/tm_find <min_elo> <max_elo> [lang] [role] — поиск тиммейтов\n"
        "/demo_analyze [lang] + .dem файл — анализ демки"
    )


async def cmd_faceit_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    await update.effective_chat.send_message("\n".join(lines))


async def cmd_tm_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_chat.send_message(
            "Использование: /tm_find <min_elo> <max_elo> [lang] [role]"
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

    await update.effective_chat.send_message(
        "Скачиваю и анализирую демку, это может занять время..."
    )

    telegram_file = await doc.get_file()
    buffer = BytesIO()
    await telegram_file.download_to_memory(out=buffer)
    buffer.seek(0)

    upload = UploadFile(filename=filename, file=buffer)  # type: ignore[arg-type]
    analysis = await demo_analyzer.analyze_demo(upload, language=language)

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

    logger.info("Starting Telegram bot...")
    app.run_polling(allowed_updates=["message", "edited_message"])


if __name__ == "__main__":
    main()
