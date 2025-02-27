import os
import sys
import logging
import requests
from flask import Flask, request
import telegram
import openai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask-приложения
app = Flask(__name__)

# Получаем токены из переменных окружения
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Указываем адрес Railway-приложения, где будет доступен ваш бот
# Можно захардкодить или получить из переменной окружения.
APP_URL = "https://railtest-production-95b6.up.railway.app"

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY:
    logger.error("Не установлены необходимые переменные окружения TELEGRAM_BOT_TOKEN или OPENAI_API_KEY")
    sys.exit(1)

# Настройка OpenAI
openai.api_key = OPENAI_API_KEY

# Инициализация бота Telegram
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def get_bitcoin_price():
    """
    Получает стоимость биткоина (USD) с использованием API CoinGecko.
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        price = data.get("bitcoin", {}).get("usd", "N/A")
        return price
    except Exception as e:
        logger.error(f"Ошибка получения цены биткоина: {e}")
        return "N/A"

def get_oil_price():
    """
    Возвращает стоимость нефти. Для примера используется фиксированное значение.
    В реальном проекте используйте актуальное API для получения цены.
    """
    return 70  # примерная цена в долларах за баррель

def handle_message(message: telegram.Message):
    """
    Обрабатывает входящие сообщения:
      1. Проверяем, обращено ли сообщение к боту.
      2. Если в тексте есть символ '$', отправляем цены биткоина и нефти.
      3. Если текст начинается с "AmyBot, нарисуй" — генерируем картинку.
      4. Иначе — отправляем запрос к OpenAI ChatCompletion.
    """
    if not message.text:
        return

    text = message.text.strip()
    
    # Определяем, обращено ли сообщение к боту (начинается с 'AmyBot' или reply на бота)
    is_addressed = (
        text.lower().startswith("amybot") or
        (
            message.reply_to_message 
            and message.reply_to_message.from_user 
            and message.reply_to_message.from_user.username == bot.username
        )
    )

    if not is_addressed:
        return

    # Команда для генерации изображения
    if text.lower().startswith("amybot, нарисуй"):
        prompt = text[len("AmyBot, нарисуй"):].strip()
        if not prompt:
            prompt = "картина мечты"
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512"
            )
            image_url = response['data'][0]['url']
            message.reply_photo(photo=image_url)
        except Exception as e:
            logger.error(f"Ошибка генерации изображения: {e}")
            message.reply_text("Извини, не удалось нарисовать картинку.")
        return

    # Сообщение содержит символ '$' — выводим цены
    if "$" in text:
        btc_price = get_bitcoin_price()
        oil_price = get_oil_price()
        reply = f"Биткоин: ${btc_price}\nНефть: ${oil_price} за баррель"
        message.reply_text(reply)
        return

    # Обычный режим общения через OpenAI Chat API
    system_prompt = (
        "Ты — AmyBot, молодой креативный профессионал, любишь спешалти кофе, сикрет бары, "
        "красивый скандинавский дизайн и гаджеты в стиле Apple и Teenage Engineering.\n"
        "Ты построил несколько успешных стартапов, был журналистом Forbes и создал свой издательский дом Lookatmedia.\n"
        "Ты долго жил в Москве, а теперь живешь в Риме.\n"
        "Ты родился в Караганде, в школе учился в Липецке, любишь путешествия и яхтинг, ты классный шкипер.\n"
        "Отвечай коротко, изредка используй странные метафоры."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    try:
        # Замените "gpt-3.5-turbo" на свою реальную модель, если нужно
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        answer = response['choices'][0]['message']['content']
        message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка обработки запроса в OpenAI: {e}")
        message.reply_text("Извини, произошла ошибка при обработке твоего запроса.")

@app.route("/", methods=["POST"])
def webhook_handler():
    """
    Обработчик вебхука для Telegram.
    """
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        if update.message:
            handle_message(update.message)
    except Exception as e:
        logger.error(f"Ошибка в webhook_handler: {e}")
    return "ok"

if __name__ == "__main__":
    # Устанавливаем webhook
    try:
        bot.set_webhook(APP_URL)
        logger.info(f"Webhook установлен на {APP_URL}")
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

    # Запуск Flask-сервера
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

