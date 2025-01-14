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

# Очищаем и обрезаем токены от невидимых символов
raw_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = "".join(ch for ch in raw_token if ch.isprintable()).strip()

raw_api_key = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = "".join(ch for ch in raw_api_key if ch.isprintable()).strip()

# Устанавливаем ключи
openai.api_key = OPENAI_API_KEY

# Проверяем, что переменные окружения не пусты
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
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Либо "gpt-4", если доступна
            messages=[{"role": "user", "content": user_message}]
        )
        bot_reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        await update.message.reply_text("Что-то пошло не так. Попробуем позже.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен... Ожидаем сообщения.")
    app.run_polling()

if __name__ == "__main__":
    main()
