from telegram import Bot
from django.conf import settings
import requests

_telegram_bot = None
_raya_bot = None

_TELEGRAM_API_URL = "https://api.telegram.org/bot{}/{}"


def get_telegram_bot():
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    return _telegram_bot


def get_raya_bot():
    global _raya_bot
    if _raya_bot is None:
        _raya_bot = Bot(token=settings.RAYA_BOT_TOKEN)
    return _raya_bot


def send_document_sync(bot: Bot, chat_id: str | int, file_path: str, filename: str):
    path = "sendDocument"
    url = _TELEGRAM_API_URL.format(bot.token, path)
    with open(file_path, "rb") as file:
        files = {"document": (filename, file)}
        data = {"chat_id": chat_id}
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()


def send_message_sync(bot: Bot, chat_id: str | int, message: str):
    path = "sendMessage"
    url = _TELEGRAM_API_URL.format(bot.token, path)

    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()
