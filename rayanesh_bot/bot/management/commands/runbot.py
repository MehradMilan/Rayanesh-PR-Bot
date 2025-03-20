from django.core.management.base import BaseCommand
from telegram.ext import Updater, CommandHandler
from bot.commands import start, register_user, create_document, finalize_document
from django.conf import settings

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **kwargs):
        updater = Updater(settings.TELEGRAM_BOT_TOKEN)

        dispatcher = updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("register", register_user))
        dispatcher.add_handler(CommandHandler("create_document", create_document))
        dispatcher.add_handler(CommandHandler("finalize_document", finalize_document))

        updater.start_polling()
        updater.idle()