from telegram import Update
from telegram.ext import Application, CommandHandler

import django
from django.core.management.base import BaseCommand
from django.conf import settings

from bot.handlers import start, join_group, authorize
import reusable.telegram_bot.bot_command


class Command(BaseCommand):
    help = "Runs the Telegram bot"

    def handle(self, *args, **kwargs):
        django.setup()

        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        application.add_handler(
            CommandHandler(reusable.telegram_bot.bot_command.START_COMMAND, start)
        )
        application.add_handler(
            CommandHandler(
                reusable.telegram_bot.bot_command.AUTHORIZE_COMMAND, authorize
            )
        )
        application.add_handler(
            CommandHandler(
                reusable.telegram_bot.bot_command.JOIN_GROUP_COMMAND, join_group
            )
        )

        application.run_polling(allowed_updates=Update.ALL_TYPES)
