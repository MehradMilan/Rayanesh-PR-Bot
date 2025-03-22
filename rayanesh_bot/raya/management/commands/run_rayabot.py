from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

import django
from django.core.management.base import BaseCommand
from django.conf import settings

from raya.handlers import accept_join, approve_join_request
import reusable.telegram_bot.bot_command


class Command(BaseCommand):
    help = "Runs the Telegram bot"

    def handle(self, *args, **kwargs):
        django.setup()

        application = Application.builder().token(settings.RAYA_BOT_TOKEN).build()

        application.add_handler(
            CommandHandler(
                reusable.telegram_bot.bot_command.ACCEPT_JOIN_GROUP_COMMAND, accept_join
            )
        )
        application.add_handler(
            CallbackQueryHandler(approve_join_request, pattern="^approve:")
        )
        application.add_handler(
            CallbackQueryHandler(approve_join_request, pattern="^deny:")
        )

        application.run_polling(allowed_updates=Update.ALL_TYPES)
