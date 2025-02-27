import os
import logging
import aiohttp
import openai
import nest_asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Применяем nest_asyncio для разрешения проблемы с вложенными event loop'ами
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Получаем токены из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", "<YOUR_TELEGRAM_BOT_TOKEN>")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "<YOUR_OPENAI_API_KEY>")

# Инициализация OpenAI API
openai.api_key = OPENAI_API_KEY


async def get_chatgpt_response(prompt: str) -> str:
    """
    Отправляет запрос к ChatGPT с использованием модели GPT-4 и возвращает сгенерированный ответ.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Ошибка при запросе к ChatGPT: {e}")
        return "Произошла ошибка при обращении к ChatGPT."


async def generate_dalle_image(prompt: str) -> str:
    """
    Генерирует изображение с помощью DALL·E и возвращает URL сгенерированного изображения.
    """
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        logging.error(f"Ошибка при генерации изображения: {e}")
        return ""


async def get_btc_price() -> str:
    """
    Получает текущую цену биткоина в долларах США через Coindesk API.
    """
    try:
        url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        price = data["bpi"]["USD"]["rate"]  # строка вида '23,456.78'
        return f"Текущая цена биткоина: {price} USD"
    except Exception as e:
        logging.error(f"Ошибка при запросе цены BTC: {e}")
        return "Не удалось получить цену биткоина."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start, приветствующий пользователя.
    """
    await update.message.reply_text(
        "Привет! Я бот, который может отвечать на вопросы, генерировать изображения и сообщать цену биткоина.\n\n"
        "• Напишите 'amybot' для обращения к ChatGPT;\n"
        "• Используйте 'нарисуй' или 'сделай картинку' для генерации изображения;\n"
        "• Отправьте '$' для получения цены биткоина."
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик текстовых сообщений.
    
    Обрабатывает:
      1. Сообщения, равные '$' – для получения цены биткоина.
      2. Сообщения, содержащие 'нарисуй' или 'сделай картинку' – для генерации изображения через DALL·E.
      3. Сообщения, содержащие 'amybot' – для обращения к ChatGPT.
    """
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.lower().strip()

    # 1. Если сообщение равно "$", отправляем цену биткоина
    if message_text == "$":
        price_text = await get_btc_price()
        await update.message.reply_text(price_text)
        return

    # 2. Если сообщение содержит ключевые слова для генерации изображения
    if "нарисуй" in message_text or "сделай картинку" in message_text:
        prompt_for_dalle = update.message.text
        placeholder_msg = await update.message.reply_text("Рисую, подождите...")
        image_url = await generate_dalle_image(prompt_for_dalle)
        await placeholder_msg.delete()
        if image_url:
            await update.message.reply_photo(photo=image_url, caption="Вот ваш рисунок!")
        else:
            await update.message.reply_text("Не удалось сгенерировать картинку, попробуйте ещё раз.")
        return

    # 3. Если сообщение содержит 'amybot', обращаемся к ChatGPT
    if "amybot" in message_text:
        user_prompt = update.message.text.replace("amybot", "").strip()
        if not user_prompt:
            user_prompt = "Привет!"
        chatgpt_answer = await get_chatgpt_response(user_prompt)
        await update.message.reply_text(chatgpt_answer)


async def main():
    """
    Основная функция для создания и запуска приложения Telegram.
    """
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Передаём close_loop=False, чтобы не пытаться закрыть уже работающий event loop
    await application.run_polling(close_loop=False)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
