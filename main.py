import os
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Подгружаем ключи из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверяем, что переменные окружения установлены
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN отсутствует или пуст. Проверь настройки Railway.")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY отсутствует или пуст. Проверь настройки Railway.")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я тестовый бот. Напиши что-нибудь!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        # Запрос к OpenAI ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Или "gpt-3.5-turbo", если GPT-4 недоступен
            messages=[{"role": "user", "content": user_message}]
        )
        bot_reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуем позже.")

def main():
    # Создаем экземпляр приложения
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен... Ожидаем сообщения.")
    # Запускаем бота в режиме Polling
    app.run_polling()

if __name__ == "__main__":
    main()
