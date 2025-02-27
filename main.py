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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
    """Заглушка для стоимости нефти."""
    return "70"

def generate_image(prompt: str) -> str:
    """Генерирует картинку через OpenAI (dall-e-3) и возвращает URL."""
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "Не указан OPENAI_API_KEY — не могу нарисовать картинку."
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024",
            model="dall-e-3"
        )
        return response["data"][0]["url"]
    except Exception as e:
        logging.error(f"Ошибка DALL·E: {e}")
        return "Извини, не получилось нарисовать картинку."

def generate_chat_response(user_text: str) -> str:
    """Отправляет запрос в ChatGPT (gpt-4o) и возвращает ответ."""
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai.api_key:
        return "Не указан OPENAI_API_KEY — не могу ответить через ChatGPT."
    
    system_prompt = (
        "Ты — AmyBot, молодой креативный профессионал, который любит спешалти кофе, "
        "красивый дизайн и гаджеты. Отвечай коротко, иногда с лёгкой иронией."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Убедитесь, что у вас есть доступ к этой модели, иначе используйте, например, "gpt-3.5-turbo"
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    await update.message.reply_text(
        "Привет, я AmyBot!\n\n"
        "Скажи что-нибудь:\n"
        "- Если в сообщении есть символ '$', я покажу цену биткоина и нефти.\n"
        "- Если начнешь с 'AmyBot, нарисуй ...' — нарисую картинку.\n"
        "- Всё остальное: отвечу через ChatGPT.\n"
        "Приятного общения!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help."""
    await update.message.reply_text(
        "Я умею:\n"
        "- Показывать цену биткоина и нефти (сообщение с '$').\n"
        "- Генерировать изображение (начни фразу с 'AmyBot, нарисуй').\n"
        "- Общаться через ChatGPT по любым вопросам.\n\n"
        "Команды:\n"
        "/start — начать\n"
        "/help — помощь"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех входящих текстовых сообщений (не команд)."""
    user_text = update.message.text.strip()
    
    if "$" in user_text:
        btc = get_bitcoin_price()
        oil = get_oil_price()
        reply_text = f"Биткоин: ${btc}\nНефть: ${oil} за баррель"
        await update.message.reply_text(reply_text)
    elif user_text.lower().startswith("amybot, нарисуй"):
        prompt = user_text[len("AmyBot, нарисуй"):].strip()
        if not prompt:
            prompt = "что-нибудь креативное"
        img_result = generate_image(prompt)
        await update.message.reply_text(img_result)
    else:
        chat_reply = generate_chat_response(user_text)
        await update.message.reply_text(chat_reply)

def main():
    """Точка входа: создаёт приложение бота и запускает polling."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в переменных окружения.")

    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    application.run_polling()

if __name__ == "__main__":
    main()
