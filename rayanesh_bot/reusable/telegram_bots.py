from telegram import Bot
from django.conf import settings

_telegram_bot = None
_raya_bot = None


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
