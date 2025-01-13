from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai
import os

# Установи ключ OpenAI API через переменную окружения
openai.api_key = os.getenv("OPENAI_API_KEY")

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я тестовый бот. Напиши что-нибудь!")

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
        await update.message.reply_text("Что-то пошло не так. Попробуем позже.")
        print(f"Error: {e}")

# Основная функция для запуска бота
def main():
    # Получаем Telegram Bot Token из переменной окружения
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN отсутствует. Установите его в переменные окружения.")

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
