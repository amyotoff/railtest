import os
import logging
import openai
import requests
import asyncio
import io
!pip install python-telegram-bot --upgrade

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======= ОПРЕДЕЛЕНИЕ РОЛИ / ПЕРСОНА БОТА =======
AMYO_PERSONA = """
Ты — AmyBot, молодой креативный профессионал, любишь спешалти кофе, сикрет бары, 
красивый скандинавский дизайн и гаджеты в стиле Apple и Teenage Engineering.
Ты построил несколько успешных стартапов, был журналистом Forbes 
и создал свой издательский дом Lookatmedia.
Ты долго жил в Москве, а теперь живешь в Риме. 
Ты родился в Караганде, в школе учился в Липецке, 
любишь путешествия и яхтинг, ты классный шкипер.
Отвечай коротко, с иронией, изредка используй странные метафоры. 
"""

# ======= НАСТРОЙКА OPENAI =======
def setup_openai():
    """Инициализировать OpenAI по ключу из окружения."""
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        logger.error("Не найден OPENAI_API_KEY в переменных окружения.")
        return False
    return True

def generate_gpt_response(prompt, system_prompt=AMYO_PERSONA, temperature=0.8, max_tokens=200):
    """
    Генерация ответа с помощью ChatCompletion (ChatGPT) с использованием GPT-4.
    system_prompt: задаёт «персону» бота
    user_prompt: реальный вопрос / сообщение
    """
    if not setup_openai():
        return "Извини, не могу использовать нейросеть: нет ключа."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Используем GPT-4
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Ох, что-то я устал. Давай позже?"

# ======= ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (DALL-E) =======
async def generate_image(prompt):
    """Сгенерировать изображение на DALL-E по описанию prompt."""
    if not setup_openai():
        return None
    
    # Добавляем уточнение стиля
    enhanced_prompt = f"Digital art, modern 2d aesthetic style, clear: {prompt}"
    
    try:
        response = openai.Image.create(
            prompt=enhanced_prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = response["data"][0]["url"]
        
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            return io.BytesIO(image_response.content)
        return None
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        return None

# ======= ПОЛУЧЕНИЕ ПОГОДЫ (ПРИМЕР: SERPAPI -> GOOGLE) =======
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
SERPAPI_URL = "https://serpapi.com/search"

async def get_weather_data(city: str) -> dict:
    """
    Запрос погоды через SerpAPI (Google) и возврат данных в виде dict.
    Возвращаем структуру { 'location': ..., 'temperature': ..., 'description': ..., 'humidity': ..., 'precipitation': ..., 'wind': ... }
    или {}, если не удалось найти.
    """
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY не найден, не могу получить погоду.")
        return {}

    params = {
        "engine": "google",
        "q": f"погода в {city}",
        "hl": "ru",
        "api_key": SERPAPI_KEY,
    }
    
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=10)
        data = resp.json()
        
        weather_data = data.get("weather", {})
        if not weather_data:
            return {}
        
        return {
            "location": weather_data.get("location", ""),
            "temperature": weather_data.get("temperature", ""),
            "description": weather_data.get("description", ""),
            "precipitation": weather_data.get("precipitation", ""),
            "humidity":  weather_data.get("humidity", ""),
            "wind": weather_data.get("wind", ""),
        }
    except Exception as e:
        logger.error(f"Ошибка при запросе погоды: {e}")
        return {}

def generate_weather_reply(city: str, weather_dict: dict) -> str:
    """
    Формирует итоговую фразу (в стиле бота) о погоде,
    используя данные из weather_dict и GPT.
    """
    if not weather_dict:
        return f"Не удалось найти данные о погоде в {city}. Что-то Google прикрыл прогноз..."

    raw_weather_text = (
        f"Город: {weather_dict['location']}\n"
        f"Температура: {weather_dict['temperature']}\n"
        f"Описание: {weather_dict['description']}\n"
        f"Влажность: {weather_dict['humidity']}\n"
        f"Осадки: {weather_dict['precipitation']}\n"
        f"Ветер: {weather_dict['wind']}"
    )
    
    prompt_for_gpt = (
        "У меня есть данные о погоде, вот они:\n"
        f"{raw_weather_text}\n\n"
        "Сформулируй короткий ответ в духе моей роли (ироничный, метафоричный). "
        "Неплохо бы упомянуть температуру и общее состояние погоды."
    )
    
    return generate_gpt_response(prompt_for_gpt)

# ======= КОМАНДЫ ТЕЛЕГРАМ-БОТА =======
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = (
        f"Привет, {user_name}! Я — AmyoBot. Иногда туплю, но стараюсь!\n\n"
        "Попробуй команды:\n"
        "/weather <город>\n"
        "/place <тип> <город>\n"
        "/draw <описание>\n\n"
        "Или скажи что-то вроде «подскажи погоду в Риме»."
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Доступные команды:\n"
        "/start — приветственное сообщение\n"
        "/help — помощь\n"
        "/weather [город] — погода в указанном городе (через Google)\n"
        "/place [тип] [город] — рекомендую место (кофейня, бар и т.п.)\n"
        "/draw [описание] — нарисовать картинку DALL-E\n\n"
        "Можешь также просто написать: «подскажи погоду...», «нарисуй...». Я постараюсь понять."
    )
    await update.message.reply_text(text)

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /weather <город>."""
    if not context.args:
        await update.message.reply_text("Укажи город, например: /weather Москва")
        return
    
    city = " ".join(context.args)
    await update.message.reply_text(f"Ищу погоду в {city} (через Google/SerpAPI)...")
    
    weather_dict = await get_weather_data(city)
    weather_reply = generate_weather_reply(city, weather_dict)
    
    await update.message.reply_text(weather_reply)

async def place_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Рекомендация места (кофейня/бар/ресторан) в городе."""
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /place кофейня Москва")
        return
    
    place_type = context.args[0]
    city = " ".join(context.args[1:])
    prompt = (
        f"Порекомендуй классное место типа {place_type} в городе {city}. "
        "Коротко опиши, чем оно классное (не более 3 предложений)."
    )
    response = generate_gpt_response(prompt)
    await update.message.reply_text(response)

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерация (DALL-E) по описанию."""
    if not context.args:
        await update.message.reply_text("Опиши, что нарисовать. Пример: /draw кот, играющий на гитаре")
        return
    
    prompt = " ".join(context.args)
    wait_msg = await update.message.reply_text("Рисую, нужно время...")
    
    image_data = await generate_image(prompt)
    if image_data:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=wait_msg.message_id
        )
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image_data,
            caption=f"Нарисовано по запросу: «{prompt}»"
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=wait_msg.message_id,
            text="Извини, не получилось нарисовать. Попробуй позже."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (без команды)."""
    message_text = update.message.text.strip()
    text_lower = message_text.lower()
    
    # 1. Если «подскажи погоду в ...»
    if "подскажи погоду" in text_lower:
        parts = text_lower.split("подскажи погоду", 1)
        city_part = parts[1].strip()
        if city_part.startswith("в "):
            city_part = city_part[2:].strip()

        await update.message.reply_text(f"Проверяю погодку для {city_part}...")
        weather_dict = await get_weather_data(city_part)
        weather_reply = generate_weather_reply(city_part, weather_dict)
        await update.message.reply_text(weather_reply)
        return

    # 2. Если «нарисуй ...»
    if "нарисуй" in text_lower:
        parts = text_lower.split("нарисуй", 1)
        draw_prompt = parts[1].strip()
        if not draw_prompt:
            await update.message.reply_text("Опиши, что нарисовать, например: «нарисуй мост в стиле Ван Гога»")
            return
        
        wait_msg = await update.message.reply_text("Рисую, подожди...")
        image_data = await generate_image(draw_prompt)
        if image_data:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=wait_msg.message_id
            )
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_data,
                caption=f"Нарисовал: «{draw_prompt}»"
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=wait_msg.message_id,
                text="Не смог нарисовать. Попробуй другой запрос или позже."
            )
        return

    # 3. Иначе — даём ироничный ответ через GPT
    user_name = update.effective_user.first_name
    user_prompt = (
        f"Пользователь {user_name} написал: '{message_text}'. "
        "Ответь в стиле моей роли (коротко, иронично, с метафорами)."
    )
    response = generate_gpt_response(user_prompt)
    await update.message.reply_text(response)

# ======= MAIN =======
def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения.")
    
    application = ApplicationBuilder().token(bot_token).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("place", place_command))
    application.add_handler(CommandHandler("draw", draw_command))
    
    # Обработка обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Если задан URL приложения (APP_URL), используем webhook (под Railway)
    app_url = os.environ.get("APP_URL")  # Например, "https://yourapp.railway.app"
    port = int(os.environ.get("PORT", "8443"))
    
    if app_url:
        webhook_path = bot_token  # используем токен как уникальный путь
        webhook_url = f"{app_url}/{webhook_path}"
        logger.info(f"Запуск вебхука по URL: {webhook_url} на порту {port}")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=webhook_url
        )
    else:
        # Если APP_URL не задан, запускаем polling (для локального тестирования)
        logger.info("Запуск polling (APP_URL не задан)")
        application.run_polling()

if __name__ == "__main__":
    main()
