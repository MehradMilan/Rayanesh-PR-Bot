from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import django
from django.core.management.base import BaseCommand
from django.conf import settings

from bot.handlers import start, authorize, handle_email, handle_name, cancel
import bot.commands
import bot.states


class Command(BaseCommand):
    help = "Runs the Rayanesh Telegram bot"

    async def post_init(application):
        await application.bot.set_my_commands(
            [("start", "شروع!"), ("authorize", "احراز هویت"), ("help", "راهنمایی")]
        )

    def handle(self, *args, **kwargs):
        django.setup()

        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        application.add_handler(CommandHandler(bot.commands.START_COMMAND, start))

        auth_conv_handler = ConversationHandler(
            entry_points=[CommandHandler(bot.commands.AUTHORIZE_COMMAND, authorize)],
            states={
                bot.states.AWAITING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
                ],
                bot.states.AWAITING_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(auth_conv_handler)

        application.run_polling(allowed_updates=Update.ALL_TYPES)
