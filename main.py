import os
import logging

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

def generate_final_message(answers: list[str]) -> str:
    text = (
        "Спасибо, что поделился(ась) своими мыслями! \n\n"
        "Вот твои ответы на упражнение YearCompass:\n\n"
    )
    for i, (question, ans) in enumerate(zip(questions, answers), start=1):
        text += f"{i}) {question}\nТвой ответ: {ans}\n\n"

    text += (
        "Похоже, у тебя был действительно яркий и необычный год!\n"
        "Судя по всему, ты успел(а) и погрустить, и порадоваться, и чему-то научиться.\n\n"
        "В новом году желаю тебе:\n"
        "1. Больше времени на то, что приносит радость!\n"
        "2. Немного самоиронии — она всегда полезна.\n"
        "3. Чётких целей и большего терпения к себе!\n\n"
        "Продолжай в том же духе, но не забывай иногда отдыхать ;)\n"
        "Ура новому году!"
    )
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Очищаем/инициализируем данные пользователя
    context.user_data[user_id] = {"answers": [], "current_question": 0}
    await update.message.reply_text(
        "Привет! Я проведу тебя через упражнение YearCompass.\n"
        "Давай начнём. Пожалуйста, отвечай на вопросы по порядку.\n\n"
        f"{questions[0]}"
    )
    return QUESTION_1

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    current_question_index = user_data.get("current_question", 0)

    message_text = update.message.text.strip()

    # Если пользователь отправил команду (например, '/help'), просим вернуться к вопросу
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
    user_data["current_question"] = current_question_index + 1
    context.user_data[user_id] = user_data

    next_question_index = current_question_index + 1
    if next_question_index < len(questions):
        await update.message.reply_text(questions[next_question_index])
        return next_question_index
    else:
        # Выдаём итоговый ответ
        final_msg = generate_final_message(answers)
        await update.message.reply_text(final_msg, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    current_question_index = user_data.get("current_question", 0)

    await update.message.reply_text(
        "Это сообщение не похоже на ответ. Давай вернёмся к упражнению.\n"
        f"Сейчас вопрос:\n\n{questions[current_question_index]}"
    )
    return current_question_index

def main():
    # Считываем токен из переменной окружения Railway (TELEGRAM_TOKEN)
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Не найден TELEGRAM_TOKEN в переменных окружения.")

    application = ApplicationBuilder().token(bot_token).build()

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

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
