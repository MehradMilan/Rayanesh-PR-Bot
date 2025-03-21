from telegram import Update
from telegram.ext import Application, CommandHandler

from django.core.management.base import BaseCommand
from django.conf import settings

from bot.handlers import start, join_group, authorize
from reusable.models import Bot_Command

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **kwargs):
        
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler(Bot_Command.START_COMMAND, start))
        application.add_handler(CommandHandler(Bot_Command.AUTHORIZE_COMMAND, authorize))
        application.add_handler(CommandHandler(Bot_Command.JOIN_GROUP_COMMAND, join_group))

        application.run_polling(allowed_updates=Update.ALL_TYPES)