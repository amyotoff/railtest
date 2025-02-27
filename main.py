import os
import requests
from flask import Flask, request
import telegram
import openai

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
APP_URL = os.environ.get("APP_URL", "")  # Например: "https://имя-приложения.up.railway.app"

openai.api_key = OPENAI_API_KEY
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def get_bitcoin_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        data = requests.get(url).json()
        return data["bitcoin"]["usd"]
    except:
        return "N/A"

def get_oil_price():
    # Упрощённая заглушка. 
    # Если нужно, интегрируйте реальный API для котировок нефти.
    return 70

def handle_message(msg: telegram.Message):
    text = (msg.text or "").strip()

    # Если нет текста — ничего не делаем
    if not text:
        return

    # "AmyBot, нарисуй..." => генерация картинки
    if text.lower().startswith("amybot, нарисуй"):
        prompt = text[len("Amybot, нарисуй"):].strip() or "красивая картинка"
        try:
            response = openai.Image.create(prompt=prompt, n=1, size="512x512")
            img_url = response['data'][0]['url']
            msg.reply_photo(photo=img_url)
        except:
            msg.reply_text("Извини, не получилось нарисовать картинку.")
        return

    # Если в тексте есть "$", отвечаем ценой биткоина и нефти
    if "$" in text:
        btc = get_bitcoin_price()
        oil = get_oil_price()
        msg.reply_text(f"Биткоин: ${btc}, нефть: ${oil} за баррель")
        return

    # Иначе — шлём в ChatCompletion
    system_prompt = (
        "Ты — AmyBot, креативный профессионал. Любишь кофе, гаджеты и путешествия. "
        "Отвечай по существу, но интересно."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=200
        )
        answer = response["choices"][0]["message"]["content"]
        msg.reply_text(answer)
    except:
        msg.reply_text("Упс, что-то пошло не так при запросе к OpenAI.")

@app.route("/", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message:
        handle_message(update.message)
    return "OK"

if __name__ == "__main__":
    if APP_URL:
        bot.set_webhook(APP_URL)
        print(f"Webhook установлен на {APP_URL}")
    else:
        print("APP_URL не задан. Установите переменную окружения или пропишите вручную.")

    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
