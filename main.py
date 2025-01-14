import os
import logging
import openai

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Вопросы YearCompass
QUESTION_1, QUESTION_2, QUESTION_3, QUESTION_4, QUESTION_5, QUESTION_6, QUESTION_7, QUESTION_8, QUESTION_9 = range(9)

questions = [
    "1) Оглянись назад на прошедший год. Что было твоей самой большой радостью?",
    "2) Какое твое главное разочарование (если оно было)?",
    "3) Чему ты научился(ась) за этот год?",
    "4) Какое достижение вызывает у тебя гордость больше всего?",
    "5) Что бы ты хотел(а) продолжить делать в следующем году?",
    "6) Каким опытом прошлого года ты особенно дорожишь?",
    "7) Есть ли что-то, что ты хотел(а) бы простить, отпустить, исцелить?",
    "8) Опиши тремя словами прошлый год.",
    "9) Опиши тремя словами свои надежды на следующий год."
]

def generate_gpt_summary(answers: list[str]) -> str:
    """
    Вызывает ChatGPT, передаёт ему ответы пользователя и возвращает
    ироничный и поддерживающий комментарий + рекомендации на будущее.
    """
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        return ("Ошибка: не указан OPENAI_API_KEY в переменных окружения.\n"
                "Не могу сгенерировать GPT-ответ.")

    # Собираем ответы в удобочитаемый формат
    user_answers_str = ""
    for i, (q, a) in enumerate(zip(questions, answers), start=1):
        user_answers_str += f"{i}) {q}\nОТВЕТ: {a}\n\n"

    # Сообщаем системе, что она — «ироничный и поддерживающий коуч»
    system_prompt = (
        "Ты — ироничный и одновременно поддерживающий коуч. "
        "Сейчас ты проводишь упражнение YearCompass с клиентом на русском языке. "
        "Твоя задача — посмотреть на ответы пользователя и дать короткое резюме "
        "про его прошедший год, а также рекомендации на будущее. "
        "Используй лёгкий, ироничный тон, но без излишнего сарказма."
    )
    # Сообщаем «assistant» контекст (запрос пользователя)
    user_prompt = (
        "Ниже ответы пользователя на упражнение YearCompass. "
        "Составь, пожалуйста, итоговый комментарий: "
        "сделай небольшое ободряющее резюме и рекомендации "
        "на будущий год в ироничном, но доброжелательном стиле.\n\n"
        f"{user_answers_str}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,   # Настройка «творчества»
            max_tokens=700,    # Примерный лимит токенов в ответе
        )
        gpt_reply = response["choices"][0]["message"]["content"]
        return gpt_reply.strip()

    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return (
            "Извини, у меня не получилось связаться с ChatGPT, "
            "поэтому просто скажу: ты молодец и удачи в новом году!"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинаем упражнение, сбрасываем состояние и задаём первый вопрос.
    """
    user_id = update.effective_user.id
    context.user_data[user_id] = {"answers": [], "current_question": 0}

    # Приветственное сообщение с объяснением бота
    welcome_text = (
        "Привет! Я бот, который поможет тебе провести небольшое упражнение YearCompass, "
        "чтобы осмыслить прошедший год и наметить планы на новый.\n\n"
        "YearCompass — это серия вопросов, которые помогают подвести итоги года: "
        "вспомнить радости, разочарования, уроки, а также сформировать намерения "
        "на следующий год.\n\n"
        "После того как ты ответишь на все вопросы, я (при поддержке GPT) "
        "предложу тебе небольшое иронично-поддерживающее резюме "
        "и рекомендации. Надеюсь, это вдохновит тебя!\n\n"
        "Вот список моих команд:\n"
        "/start — начать упражнение с начала\n"
        "/help — показать это же сообщение (подсказку)\n"
        "(В процессе опроса, пожалуйста, отвечай на вопросы последовательно.)\n\n"
        "Итак, поехали. Первый вопрос:\n\n"
        f"{questions[0]}"
    )

    await update.message.reply_text(welcome_text)
    return QUESTION_1

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показываем справку с описанием бота и команд.
    """
    help_text = (
        "Я бот для выполнения упражнения YearCompass. "
        "Задаю серию вопросов про твой прошедший год и планы на новый, "
        "а затем формирую итоговый комментарий при помощи GPT.\n\n"
        "Команды:\n"
        "/start — начать упражнение заново\n"
        "/help — показать это сообщение\n\n"
        "Если ты уже проходишь вопросы, просто продолжай отвечать. "
        "Если скомандуешь /start, мы начнём всё с начала."
    )
    await update.message.reply_text(help_text)

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принимаем ответ на текущий вопрос. Если это не команда,
    сохраняем и задаём следующий вопрос, либо переходим к итоговому сообщению.
    """
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    current_question_index = user_data.get("current_question", 0)

    message_text = update.message.text.strip()

    # Если пользователь отправил команду (например, /help), просим вернуться к вопросу
    if message_text.startswith("/"):
        await update.message.reply_text(
            "Похоже, это не ответ на вопрос. Вернёмся к упражнению?\n"
            f"Пожалуйста, ответь на вопрос:\n\n{questions[current_question_index]}"
        )
        return current_question_index

    # Сохраняем ответ
    answers = user_data.get("answers", [])
    answers.append(message_text)
    user_data["answers"] = answers

    # Переходим к следующему вопросу
    next_question_index = current_question_index + 1
    user_data["current_question"] = next_question_index
    context.user_data[user_id] = user_data

    # Если не дошли до конца
    if next_question_index < len(questions):
        await update.message.reply_text(questions[next_question_index])
        return next_question_index
    else:
        # Все вопросы пройдены — формируем GPT-анализ
        gpt_msg = generate_gpt_summary(answers)
        # Отправляем пользователю
        await update.message.reply_text(
            gpt_msg,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Если пользователь пишет что-то не в ответ на вопрос,
    просим вернуться к упражнению.
    """
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    current_question_index = user_data.get("current_question", 0)

    await update.message.reply_text(
        "Это сообщение не похоже на ответ. Давай вернёмся к упражнению.\n"
        f"Сейчас вопрос:\n\n{questions[current_question_index]}"
    )
    return current_question_index

def main():
    # Считываем токен бота из переменной окружения
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения.")

    # Создаём приложение бота
    application = ApplicationBuilder().token(bot_token).build()

    # Конфигурируем хендлер команды /help
    help_handler = CommandHandler("help", help_command)

    # Конфигурируем «машину состояний» (ConversationHandler) для YearCompass
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUESTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_4: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_5: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_6: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_7: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_8: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
            QUESTION_9: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question),
                         MessageHandler(filters.ALL, fallback)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, fallback)],
        allow_reentry=True
    )

    # Регистрируем хендлеры
    application.add_handler(help_handler)
    application.add_handler(conv_handler)

    # Запускаем бота (polling)
    application.run_polling()

if __name__ == "__main__":
    main()
