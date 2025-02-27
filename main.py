import os
import logging
import requests
import openai

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Уровень логирования (при желании можно сделать WARNING, чтобы не засорять логи)
logging.basicConfig(level=logging.INFO)

# ===================== ЛОГИКА БОТА =====================

def get_bitcoin_price() -> str:
    """Возвращает стоимость биткоина (USD) по CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        return str(data["bitcoin"]["usd"])
    except Exception as e:
        logging.error(f"Ошибка при получении цены биткоина: {e}")
        return "N/A"

def get_oil_price() -> str:
    """Простая заглушка для нефти. В реальном проекте подключите реальный API."""
    return "70"

def generate_image(prompt: str) -> str:
    """Генерация картинки через OpenAI (DALL·E). Возвращает URL или сообщение об ошибке."""
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "Не указан OPENAI_API_KEY — не могу нарисовать картинку."

    try:
        response = openai.Image.create(prompt=prompt, n=1, size="512x512")
        return response["data"][0]["url"]
    except Exception as e:
        logging.error(f"Ошибка DALL·E: {e}")
        return "Извини, не получилось нарисовать картинку."

def generate_chat_response(user_text: str) -> str:
    """
    Отправляет сообщение в ChatGPT (gpt-3.5-turbo или другую модель)
    и возвращает ответ. 
    """
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "Не указан OPENAI_API_KEY — не могу ответить через ChatGPT."

    system_prompt = (
        "Ты — AmyBot, молодой креативный профессионал, который любит спешалти кофе, "
        "красивый дизайн и гаджеты. Отвечай коротко, иногда иронично."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Или другой, доступный вам
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Ошибка ChatGPT: {e}")
        return "Извини, у меня не получается ответить."

# ===================== ОБРАБОТЧИКИ =====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start
    """
    await update.message.reply_text(
        "Привет, я AmyBot!\n\n"
        "Скажи что-нибудь:\n"
        "- В сообщении есть символ '$'? Я покажу цену биткоина и нефти.\n"
        "- 'AmyBot, нарисуй ...' — нарисую картинку.\n"
        "- Всё остальное: ответ через ChatGPT.\n"
        "Приятного общения!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help
    """
    await update.message.reply_text(
        "Я умею:\n"
        "- Показывать цену биткоина и нефти (сообщение с '$')\n"
        "- Генерировать изображение (начни фразу с 'AmyBot, нарисуй')\n"
        "- Общаться через ChatGPT по любым вопросам.\n\n"
        "Команды:\n"
        "/start — начать\n"
        "/help — помощь"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка обычных текстовых сообщений (не команд).
    """
    user_text = update.message.text.strip()
    if "$" in user_text:
        # Показываем биткоин и нефть
        btc = get_bitcoin_price()
        oil = get_oil_price()
        reply_text = f"Биткоин: ${btc}\nНефть: ${oil} за баррель"
        await update.message.reply_text(reply_text)
    elif user_text.lower().startswith("amybot, нарисуй"):
        # Генерация картинки через DALL·E
        prompt = user_text[len("AmyBot, нарисуй"):].strip()
        if not prompt:
            prompt = "что-нибудь креативное"
        img_result = generate_image(prompt)
        await update.message.reply_text(img_result)
    else:
        # Общение через ChatGPT
        chat_reply = generate_chat_response(user_text)
        await update.message.reply_text(chat_reply)

# ===================== MAIN =====================

def main():
    """
    Точка входа. Создаёт приложение бота и запускает webhook-сервер на Railway.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в переменных окружения.")
    
    app_url = os.environ.get("APP_URL")
    if not app_url:
        raise ValueError("Не задан APP_URL (адрес Railway-приложения).")

    # Получаем порт (Railway передаёт в переменной PORT)
    port = int(os.environ.get("PORT", "5000"))

    # Создаём приложение бота
    application = ApplicationBuilder().token(bot_token).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик всех остальных текстовых сообщений
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    application.add_handler(text_handler)

    # Запускаем вебхук на 0.0.0.0:<port>, 
    # при этом Telegram будет стучаться на app_url (https://...)
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=app_url
    )

    logging.info(f"Bot started with webhook on {app_url}")

if __name__ == "__main__":
    main()
