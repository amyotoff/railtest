import os
import openai
import logging

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

# -------------------------
# Логирование на случай отладки
# -------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -------------------------
# ШАГИ (STATES) ДЛЯ CONVERSATIONHANDLER
# -------------------------
(
    REFLECTION_1,   # Вопрос: самое яркое событие/достижение
    REFLECTION_2,   # Люди/привычки года — зависит от вашей логики
    REFLECTION_3,   # Неудачи/незавершённый проект
    FORGIVENESS,    # Прощение и отпускание
    FUTURE,         # Цели и мечты на будущее
) = range(5)

# -------------------------
# ФУНКЦИЯ ДЛЯ ОЧИСТКИ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# -------------------------
def _clean_env_value(value: str) -> str:
    """Очищает строку от непечатаемых символов и пробелов по краям."""
    return "".join(ch for ch in value if ch.isprintable()).strip()

# -------------------------
# СЧИТЫВАЕМ ТОКЕНЫ
# -------------------------
RAW_TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = _clean_env_value(RAW_TELEGRAM_BOT_TOKEN)

RAW_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = _clean_env_value(RAW_OPENAI_API_KEY)

if not TELEGRAM_BOT_T

