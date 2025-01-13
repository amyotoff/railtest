from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai

# Установи ключ OpenAI API
openai.api_key = "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"

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я тестовый бот. Напиши что-нибудь, и я отвечу!")

# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Получение текста от пользователя

    try:
        # Отправка запроса к OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": user_message}],
        )
        bot_reply = response['choices'][0]['message']['content']  # Получение ответа

        # Отправка ответа пользователю
        await update.message.reply_text(bot_reply)
    except Exception as e:
        # Обработка ошибок
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")
        print(f"Error: {e}")

# Основная функция для запуска бота
def main():
    # Замени на свой Telegram Bot Token
    TELEGRAM_BOT_TOKEN = "1190854549:AAFMDjUG89f3WOnBCDlXiVQlxCtwmbsLGZ4"


    # Создание бота
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))  # Обработка команды /start
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработка текстовых сообщений

    # Запуск бота
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
