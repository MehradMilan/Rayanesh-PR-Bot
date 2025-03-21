from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application, CommandHandler
from bot.commands import start, register_user, create_document, finalize_document
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **kwargs):
        
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))

        application.run_polling(allowed_updates=Update.ALL_TYPES)