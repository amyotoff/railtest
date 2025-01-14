import os
import openai
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext,
    PicklePersistence
)

# -------------------------
# Логирование на случай отладки
# -------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -------------------------
# ШАГИ (STATES) ДЛЯ CONVERSATIONHANDLER
# -------------------------
(
    REFLECTION_1,   # Вопрос: самое яркое событие/достижение
    REFLECTION_2,   # Люди/привычки года — зависит от вашей логики
    REFLECTION_3,   # Неудачи/незавершённый проект
    FORGIVENESS,    # Прощение и отпускание
    FUTURE,         # Цели и мечты на будущее
) = range(5)

# -------------------------
# ФУНКЦИЯ ДЛЯ ОЧИСТКИ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# -------------------------
def _clean_env_value(value: str) -> str:
    """Очищает строку от непечатаемых символов и пробелов по краям."""
    return "".join(ch for ch in value if ch.isprintable()).strip()

# -------------------------
# СЧИТЫВАЕМ ТОКЕНЫ
# -------------------------
RAW_TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = _clean_env_value(RAW_TELEGRAM_BOT_TOKEN)

RAW_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = _clean_env_value(RAW_OPENAI_API_KEY)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN отсутствует или пуст. Проверь настройки.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY отсутствует или пуст. Проверь настройки.")

openai.api_key = OPENAI_API_KEY

# -------------------------
# СИСТЕМНЫЙ ПРОМПТ ДЛЯ OPENAI
# -------------------------
def year_compass_humorous_system_prompt():
    """
    Возвращает системное сообщение (role='system'), в котором боту 
    предписывается быть юмористическим, ироничным «YearCompass» гидом.
    """
    content = (
        "You are a supportive, playful, sarcastic, and humorous YearCompass guide. "
        "Your job is to walk the user through reflecting on the past year and planning the next, "
        "using an interactive approach. Collect the user’s answers and provide a final comedic summary. "
        "Use irony and jokes, but stay supportive.\n\n"
        "Here are your guidelines:\n"
        "1) Reflect on the past year's events, habits, achievements, and failures.\n"
        "2) Discuss forgiveness and releasing grudges.\n"
        "3) Explore future plans and goals.\n"
        "4) Provide a final summary with humor.\n"
        "Be sure to keep a friendly but ironic tone.\n"
    )
    return {"role": "system", "content": content}

# -------------------------
# ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (вне сценария)
# -------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если пользователь пишет что-то вне YearCompass-сценария, просто отвечаем через OpenAI (или эхо)."""
    user_message = update.message.text
    try:
        # Замените модель на "gpt-3.5-turbo" или "gpt-4", если не имеете особой модели
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        bot_reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуем позже.")

# -------------------------
# КОМАНДА /start
# -------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start: приветствие."""
    await update.message.reply_text(
        "Привет! Сделаем Year Compass?\n"
        "Набери /yearcompass, чтобы начать!"
    )

# -------------------------
# ШАГИ СЦЕНАРИЯ «YEARCOMPASS»
# -------------------------
async def yearcompass_start(update: Update, context: CallbackContext):
    """
    Точка входа в сценарий YearCompass — спрашиваем первый вопрос (REFLECTION_1).
    """
    await update.message.reply_text(
        "Начнём! Шаг 1: Вспомни самое яркое событие или достижение прошлого года. "
        "Может, оно было грандиозным... а может и совсем нет. Поделись!"
    )
    return REFLECTION_1

async def reflection_1(update: Update, context: CallbackContext):
    """Обрабатываем ответ на шаг 1, переходим к шагу 2."""
    user_text = update.message.text
    context.user_data["reflection_1"] = user_text  # Сохраняем ответ
    await update.message.reply_text(
        "Отлично! Шаг 2: Теперь вспомни главных людей (или привычки) прошлого года. "
        "Кто повлиял на тебя? На кого повлиял ты?"
    )
    return REFLECTION_2

async def reflection_2(update: Update, context: CallbackContext):
    """Обрабатываем ответ на шаг 2, переходим к шагу 3."""
    user_text = update.message.text
    context.user_data["reflection_2"] = user_text
    await update.message.reply_text(
        "Окей! Шаг 3: Назови одну главную неудачу или незавершённый проект, "
        "который бы ты хотел отпустить. Будем смотреть на вещи трезво!"
    )
    return REFLECTION_3

async def reflection_3(update: Update, context: CallbackContext):
    """Обрабатываем ответ на шаг 3, переходим к теме FORGIVENESS."""
    user_text = update.message.text
    context.user_data["reflection_3"] = user_text
    await update.message.reply_text(
        "Понятно! Теперь поговорим о прощении (FORGIVENESS). "
        "Есть ли что-то или кого-то, что ты хотел бы простить? "
        "Или какие обиды оставить в прошлом?"
    )
    return FORGIVENESS

async def forgiveness(update: Update, context: CallbackContext):
    """Обрабатываем прощение, переходим к планам FUTURE."""
    user_text = update.message.text
    context.user_data["forgiveness"] = user_text
    await update.message.reply_text(
        "Хорошо! Теперь взглянем на будущее. "
        "Какие смелые цели и мечты ты хочешь поставить на следующий год? "
        "Какой сюрпризный поворот сюжета ожидаешь?"
    )
    return FUTURE

async def future(update: Update, context: CallbackContext):
    """
    Обрабатываем планы на будущее, переходим к формированию сводки (summary).
    """
    user_text = update.message.text
    context.user_data["future"] = user_text

    await update.message.reply_text("Отлично! Сейчас подготовлю резюме того, что мы обсудили...")
    return await final_summary(update, context)

# -------------------------
# ФИНАЛЬНАЯ СВОДКА
# -------------------------
async def final_summary(update: Update, context: CallbackContext):
    """
    Делаем сводку при помощи OpenAI, используя системный промпт + ответы.
    Завершаем разговор ConversationHandler.
    """
    answers = context.user_data

    # Формируем system prompt
    system_prompt = year_compass_humorous_system_prompt()

    # Собираем пользовательские ответы в один текст
    user_text = (
        "Here are the user's answers to the YearCompass steps:\n"
        f"1) Biggest event/achievement: {answers.get('reflection_1', '')}\n"
        f"2) People/habits: {answers.get('reflection_2', '')}\n"
        f"3) Unfinished project or failure: {answers.get('reflection_3', '')}\n"
        f"4) Forgiveness/letting go: {answers.get('forgiveness', '')}\n"
        f"5) Future goals: {answers.get('future', '')}\n\n"
        "Now, please provide a comedic summary with some ironic commentary and a friendly, supportive tone. "
        "End with a couple of personalized tips for next year."
    )

    try:
        # Замените модель на "gpt-3.5-turbo" или "gpt-4", если у вас есть доступ
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                system_prompt,                     # системный промпт
                {"role": "user", "content": user_text}
            ]
        )
        bot_reply = response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        bot_reply = (
            "Опа! Произошла ошибка при формировании сводки. "
            "Попробуй позже или перезапусти /yearcompass."
        )

    await update.message.reply_text(bot_reply)

    # Завершаем диалог
    return ConversationHandler.END

# -------------------------
# /cancel — прервать диалог
# -------------------------
async def cancel(update: Update, context: CallbackContext):
    """Если пользователь хочет прервать YearCompass-процесс."""
    await update.message.reply_text("Окей, отменяем YearCompass. Приходи, когда будешь готов!")
    return ConversationHandler.END

# -------------------------
# ЕСЛИ ПОЛЬЗОВАТЕЛЬ ПИШЕТ ВНЕ СЦЕНАРИЯ
# -------------------------
async def handle_plain_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Если пользователь пишет что-то вне YearCompass-сценария,
    можем либо отвечать через OpenAI, либо просто эхо.
    """
    user_message = update.message.text
    # Можно вызывать ChatCompletion или просто сделать эхо:
    await update.message.reply_text(f"Эхо: {user_message}")

# -------------------------
# ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА
# -------------------------
def main():
    # Если у вас PTB 20+, можно использовать ключевые аргументы:
    # persistence = PicklePersistence(filename='yearcompass_bot_data')
    # Если это вызывает ошибку, оставьте как есть (позиционный аргумент).
    persistence = PicklePersistence('yearcompass_bot_data')

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).persistence(persistence).build()

    # Настраиваем ConversationHandler для YearCompass
    yearcompass_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("yearcompass", yearcompass_start)],
        states={
            REFLECTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflection_1)],
            REFLECTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflection_2)],
            REFLECTION_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflection_3)],
            FORGIVENESS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, forgiveness)],
            FUTURE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, future)],
            # SUMMARY вызывается внутри future() -> final_summary
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(yearcompass_conv_handler)

    # Обработчик всех прочих текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plain_message))

    print("Бот запущен... Ожидаем сообщения. /start или /yearcompass")
    app.run_polling()


if __name__ == "__main__":
    main()
