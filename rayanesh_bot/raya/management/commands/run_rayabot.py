from telegram import Update
from telegram.ext import Application, CommandHandler

from django.core.management.base import BaseCommand
from django.conf import settings

from raya.handlers import accept_join
from reusable.models import Raya_Command

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **kwargs):
        
        application = Application.builder().token(settings.RAYA_BOT_TOKEN).build()

        application.add_handler(CommandHandler(Raya_Command.ACCEPT_JOIN_GROUP, accept_join))

        application.run_polling(allowed_updates=Update.ALL_TYPES)
        