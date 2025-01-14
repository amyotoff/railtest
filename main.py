import os
import openai
import logging
from typing import Dict, Any
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

# Improved logging configuration with file handler
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# States as an Enum for better type safety
from enum import Enum, auto
class States(Enum):
    REFLECTION_1 = auto()
    REFLECTION_2 = auto()
    REFLECTION_3 = auto()
    FORGIVENESS = auto()
    FUTURE = auto()

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

# Load configuration
config = Config()
TELEGRAM_BOT_TOKEN = config.get_env("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = config.get_env("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class YearCompassBot:
    """Main bot class implementing YearCompass functionality"""
    
    @staticmethod
    def get_system_prompt() -> Dict[str, str]:
        """Returns the system prompt for OpenAI."""
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

    @staticmethod
    async def handle_openai_request(messages: list) -> str:
        """Handles OpenAI API requests with error handling."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Updated from gpt-40-mini
                messages=messages
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI Error: {e}")
            return "An error occurred. Please try again later."

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles /start command."""
        await update.message.reply_text(
            "👋 Welcome to YearCompass Bot!\n"
            "Type /yearcompass to start your year reflection journey."
        )

    @staticmethod
    async def yearcompass_start(update: Update, context: CallbackContext) -> States:
        """Starts the YearCompass conversation."""
        await update.message.reply_text(
            "🌟 Let's begin! Step 1: What was your brightest moment or biggest achievement last year? "
            "Share it, whether it was huge or tiny!"
        )
        return States.REFLECTION_1

    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles messages outside the YearCompass flow."""
        user_message = update.message.text
        messages = [{"role": "user", "content": user_message}]
        response = await YearCompassBot.handle_openai_request(messages)
        await update.message.reply_text(response)

    @staticmethod
    async def cancel(update: Update, context: CallbackContext) -> int:
        """Cancels the YearCompass process."""
        await update.message.reply_text(
            "YearCompass cancelled. Come back when you're ready! /yearcompass"
        )
        return ConversationHandler.END

    # Main execution setup
    @classmethod
    def run(cls) -> None:
        """Sets up and runs the bot."""
        persistence = PicklePersistence(filepath='yearcompass_bot_data')
        
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).persistence(persistence).build()

        # Add conversation handler with the states
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("yearcompass", cls.yearcompass_start)],
            states={
                States.REFLECTION_1: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_1)
                ],
                States.REFLECTION_2: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_2)
                ],
                States.REFLECTION_3: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.reflection_3)
                ],
                States.FORGIVENESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.forgiveness)
                ],
                States.FUTURE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, cls.future)
                ],
            },
            fallbacks=[CommandHandler("cancel", cls.cancel)]
        )

        app.add_handler(CommandHandler("start", cls.start_command))
        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            cls.handle_message
        ))

        logger.info("Bot started. Send /start or /yearcompass to begin.")
        app.run_polling()

if __name__ == "__main__":
    YearCompassBot.run()
