import os
import openai
import logging
from typing import Dict, Any
from enum import Enum, auto

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext,
    PicklePersistence
)

# --------------------------------------------
# Логирование (с логами в файл 'bot.log' + вывод в консоль)
# --------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --------------------------------------------
# Состояния (States) как Enum для ConversationHandler
# --------------------------------------------
class States(Enum):
    REFLECTION_1 = auto()
    REFLECTION_2 = auto()
    REFLECTION_3 = auto()
    FORGIVENESS = auto()
    FUTURE = auto()
    # Если нужен финальный шаг (SUMMARY), добавьте здесь

# --------------------------------------------
# Класс Config для удобной обработки переменных окружения
# --------------------------------------------
class Config:
    """Configuration class for environment variables"""
    @staticmethod
    def _clean_env_value(value: str) -> str:
        """Cleans string from non-printable characters and trims whitespace."""
        return "".join(ch for ch in value if ch.isprintable()).strip()
    
    @classmethod
    def get_env(cls, key: str) -> str:
        """Gets and validates environment variable."""
        value = os.getenv(key, "")
        cleaned_value = cls._clean_env_value(value)
        if not cleaned_value:
            raise ValueError(f"{key} is missing or empty. Check your settings.")
        return cleaned_value

# --------------------------------------------
# Считываем токены из окружения
# --------------------------------------------
config = Config()
TELEGRAM_BOT_TOKEN = config.get_env("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = config.get_env("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# --------------------------------------------
# Основной класс YearCompassBot
# --------------------------------------------
class YearCompassBot:
    """Main bot class implementing YearCompass functionality."""
    
    # ----- 1. Подготовка системного промпта для OpenAI -----
    @staticmethod
    def get_system_prompt() -> Dict[str, str]:
        """
        Returns the system prompt for OpenAI.
        The bot acts as a supportive, playful, sarcastic, 
        and humorous YearCompass guide.
        """
        content = (
            "You are a supportive, playful, sarcastic, and humorous YearCompass guide. "
            "Your job is to walk the user through reflecting on the past year and planning the next, "
            "using an interactive approach. Collect the user's answers and provide a final comedic summary. "
            "Use irony and jokes, but stay supportive.\n\n"
            "Guidelines:\n"
            "1) Reflect on the past year's events, habits, achievements, and failures.\n"
            "2) Discuss forgiveness and releasing grudges.\n"
            "3) Explore future plans and goals.\n"
            "4) Provide a final summary with support and humor.\n"
            "Keep a friendly but ironic tone.\n"
        )
        return {"role": "system", "content": content}

    # ----- 2. Отправка запроса в OpenAI -----
    @staticmethod
    async def handle_openai_request(messages: list) -> str:
        """
        Handles OpenAI API requests with error handling.
        Model set to 'gpt-3.5-turbo' for demonstration. 
        (Replace with 'gpt-40-mini' if you indeed have access.)
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            return "An error occurred while contacting OpenAI. Please try again later."

    # ----- 3. Команда /start -----
    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles /start command."""
        await update.message.reply_text(
            "👋 Welcome to YearCompass Bot!\n"
            "Type /yearcompass to start your year reflection journey."
        )

    # ----- 4. Начало сценария YearCompass -----
    @staticmethod
    async def yearcompass_start(update: Update, context: CallbackContext) -> States:
        """Starts the YearCompass conversation."""
        await update.message.reply_text(
            "🌟 Let's begin! Step 1: What was your brightest moment or biggest achievement last year?\n"
            "Share it, whether it was huge or tiny!"
        )
        return States.REFLECTION_1

    # ----- 5. Шаги сценария -----
    @staticmethod
    async def reflection_1(update: Update, context: CallbackContext) -> States:
        """User answers step 1 -> move to step 2."""
        user_text = update.message.text
        context.user_data["reflection_1"] = user_text
        await update.message.reply_text(
            "Great! Step 2: Who were the main people (or habits) last year that influenced you? "
            "On whom did you have an impact?"
        )
        return States.REFLECTION_2

    @staticmethod
    async def reflection_2(update: Update, context: CallbackContext) -> States:
        """User answers step 2 -> move to step 3."""
        user_text = update.message.text
        context.user_data["reflection_2"] = user_text
        await update.message.reply_text(
            "Cool! Step 3: Name a major failure or unfinished project "
            "you'd like to let go of before the new year."
        )
        return States.REFLECTION_3

    @staticmethod
    async def reflection_3(update: Update, context: CallbackContext) -> States:
        """User answers step 3 -> move to forgiveness."""
        user_text = update.message.text
        context.user_data["reflection_3"] = user_text
        await update.message.reply_text(
            "Understood! Next: FORGIVENESS. Is there anything or anyone you want to forgive? "
            "Any grudges you'd like to leave behind?"
        )
        return States.FORGIVENESS

    @staticmethod
    async def forgiveness(update: Update, context: CallbackContext) -> States:
        """User answers forgiveness -> move to future plans."""
        user_text = update.message.text
        context.user_data["forgiveness"] = user_text
        await update.message.reply_text(
            "Now let's look to the future. What bold goals and dreams do you have "
            "for the coming year? Any unexpected plot twists you'd like to see?"
        )
        return States.FUTURE

    @staticmethod
    async def future(update: Update, context: CallbackContext) -> int:
        """
        User answers future -> we can do final summary here or just end.
        For demonstration, let's just end the conversation.
        If you want a final summary, add a new state (e.g., SUMMARY).
        """
        user_text = update.message.text
        context.user_data["future"] = user_text
        
        # Option 1: End the conversation here
        await update.message.reply_text(
            "Great! Thanks for sharing your plans. "
            "You can /yearcompass again anytime to reflect or plan!"
        )
        return ConversationHandler.END

        # Option 2: If you want a final summary step, do something like:
        # return States.SUMMARY

    # ----- 6. Сообщения вне сценария -----
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handles messages outside the YearCompass flow.
        Here we just pass the user's input to OpenAI (ChatCompletion).
        """
        user_message = update.message.text
        messages = [{"role": "user", "content": user_message}]
        response = await YearCompassBot.handle_openai_request(messages)
        await update.message.reply_text(response)

    # ----- 7. Отмена сценария /cancel -----
    @staticmethod
    async def cancel(update: Update, context: CallbackContext) -> int:
        """Cancels the YearCompass process."""
        await update.message.reply_text(
            "YearCompass cancelled. Come back when you're ready! (/yearcompass)"
        )
        return ConversationHandler.END

    # ----- 8. Запуск бота -----
    @classmethod
    def run(cls) -> None:
        """Sets up and runs the bot with conversation + normal message handling."""
        # If you see "unexpected keyword argument 'filename'", 
        # use PicklePersistence('yearcompass_bot_data') instead.
        persistence = PicklePersistence('yearcompass_bot_data')

        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).persistence(persistence).build()

        # Define conversation handler for YearCompass steps
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("yearcompass", cls.yearcompass_start)],
            states={
                States.REFLECTION_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_1)],
                States.REFLECTION_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_2)],
                States.REFLECTION_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_3)],
                States.FORGIVENESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.forgiveness)],
                States.FUTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cls.future)],
                # If you add a final summary step, add it here
            },
            fallbacks=[CommandHandler("cancel", cls.cancel)],
            allow_reentry=True  # optional if you want user to re-enter conversation
        )

        # Register handlers
        app.add_handler(CommandHandler("start", cls.start_command))
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cls.handle_message))

        logger.info("Bot started. Send /start or /yearcompass to begin.")
        app.run_polling()

# --------------------------------------------
# Точка входа
# --------------------------------------------
if __name__ == "__main__":
    YearCompassBot.run()
