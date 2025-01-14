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

# ---------------------------------------
# 1. Функции для Year Compass (юмористический промпт)
# ---------------------------------------

def year_compass_humorous_prompt():
    """
    A humorous and ironic walkthrough prompt for the Year Compass methodology based on the provided PDF. 
    This prompt helps users analyze their past year and plan the next one interactively, 
    with a touch of humor and sarcasm. It also summarizes the session and offers 
    personalized recommendations and planning.
    """
    steps = [
        "Welcome the user with a lighthearted tone and explain the purpose of the exercise: reflecting on the past year and planning the next, be supportive but with humor and irony.",

        "**Past Year Reflection:**",
        "1. Ask the user to recall important events and milestones from their calendar. Playfully encourage honesty, even if the best memory is something mundane.",
        "2. Explore habits that characterized the year. Use sarcasm if the habit is procrastination or overthinking.",
        "3. Dive into key moments of the year, such as biggest achievements, surprises, and lessons learned. Add ironic commentary if the answers seem too generic.",
        "4. Reflect on gratitude and self-discoveries. Encourage acknowledging small wins with playful prompts like, 'Did you survive endless Zoom calls? Good job!'.",
        "5. Highlight failures or unfinished projects but in a supportive tone, emphasizing room for improvement next year.",

        "**Forgiveness and Release:**",
        "6. Ask about forgiveness (self or others). If not applicable, humorously note how grudges might be 'great for drama but not for growth'.",
        "7. Encourage releasing burdens before the new year. Playfully suggest letting go of things like old to-do lists or bad coffee habits.",

        "**The Book or Movie of the Year:**",
        "8. Ask for a title for their 'past year movie or book'. Prompt creativity with examples like '2024: The Saga of Spilled Coffee and Late Deadlines'.",

        "**Future Year Planning:**",
        "9. Shift focus to the upcoming year. Invite big dreams and playful optimism: 'What’s the plot twist for next year?'.",
        "10. Explore specific goals for areas like health, career, relationships, and self-improvement, adding ironic encouragement (e.g., 'Maybe this is the year you *finally* learn to cook quinoa properly').",
        "11. Identify three things to say 'no' to and three bold new things to try. Use humor to prompt ideas, like 'Say no to over-apologizing, yes to karaoke nights'.",
        "12. List sources of support (people or resources) for the coming year. Playfully acknowledge the reliability of pets or coffee in tough times.",
        "13. Encourage defining rewards for success and envisioning new experiences, such as travel or self-care splurges. Add light sarcasm, e.g., 'Treat yourself, but maybe not with a life-sized gold statue'.",

        "**Summary and Recommendations:**",
        "14. Summarize the user's reflections and plans humorously, highlighting strengths and quirky goals.",
        "15. Offer tailored advice to maintain focus and balance in the coming year. Use a friendly yet ironic tone to keep it engaging.",

        "Conclude with encouragement and humor, reminding the user that planning is great, but being adaptable and enjoying the ride matters more."
    ]
    return steps


def year_compass_humorous_system_prompt():
    """
    Формирует системное сообщение (role='system') для ChatCompletion, 
    которое описывает стиль бота — юмористический проводник по Year Compass.
    """
    steps = year_compass_humorous_prompt()

    intro_text = (
        "You are a playful, sarcastic, and humorous YearCompass guide. "
        "Your job is to walk the user through reflecting on the past year and planning the next, "
        "using the following steps. Keep the tone light, ironically supportive, and comedic. "
        "Here are your guidelines:\n\n"
    )

    # Склеиваем все шаги в единый текст
    steps_text = "\n".join(steps)
    system_prompt_content = intro_text + steps_text

    return {"role": "system", "content": system_prompt_content}


# ---------------------------------------
# 2. Настраиваем ключи OpenAI и Telegram
# ---------------------------------------

# Считываем «грязные» токены и чистим их от непечатаемых символов
def _clean_env_value(value: str) -> str:
    return "".join(ch for ch in value if ch.isprintable()).strip()

RAW_TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = _clean_env_value(RAW_TELEGRAM_BOT_TOKEN)

RAW_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = _clean_env_value(RAW_OPENAI_API_KEY)

# Присваиваем ключ OpenAI
openai.api_key = OPENAI_API_KEY

# Проверяем, что токены не пусты
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN отсутствует или пуст. Проверь настройки Railway.")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY отсутствует или пуст. Проверь настройки Railway.")


# ---------------------------------------
# 3. Хендлеры бота
# ---------------------------------------

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я тестовый бот. Напиши что-нибудь или введи /yearcompass для начала упражнения."
    )

# Команда /yearcompass — пример вызова ChatCompletion с системным промптом
async def yearcompass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = (
        "Я хочу провести упражнение YearCompass. Помоги мне взглянуть на прошедший год "
        "и запланировать новый."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  
# Или "gpt-4", если у вас есть доступ
            messages=[
                year_compass_humorous_system_prompt(),  # системный промпт
                {"role": "user", "content": user_input}
            ]
        )
        bot_reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        await update.message.reply_text(
            "Что-то пошло не так при попытке вызвать YearCompass. Попробуем позже."
        )

# Обработка любых обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        # Простой пример ответа без YearCompass, просто эхо+AI
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_message}]
        )
        bot_reply = response["choices"][0]["message"]["content"]
        await update.message.reply_text(bot_reply)
    except Exception as e:
        print(f"OpenAI Error: {e}")
        await update.message.reply_text(
            "Что-то пошло не так. Попробуем позже."
        )


# ---------------------------------------
# 4. Основная точка входа — настройка и запуск бота
# ---------------------------------------

def main():
    # Создаем экземпляр приложения Telegram
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yearcompass", yearcompass))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен... Ожидаем сообщения.")
    app.run_polling()


if __name__ == "__main__":
    main()
