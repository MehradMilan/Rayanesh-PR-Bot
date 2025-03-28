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

from bot.handlers import (
    start,
    authorize,
    handle_email,
    handle_name,
    cancel,
    send_group_chat_id_to_healthcheck_channel,
    list_tasks,
    send_task_details,
    pick_up_task,
    mark_task_as_done,
)
import bot.commands
import bot.states


class Command(BaseCommand):
    help = "Runs the Rayanesh Telegram bot"

    async def post_init(self, application):
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
        application.add_handler(
            CommandHandler(
                bot.commands.REVEAL_CHAT_ID_COMMAND,
                send_group_chat_id_to_healthcheck_channel,
            )
        )
        application.add_handler(
            CommandHandler(bot.commands.LIST_TASKS_COMMAND, list_tasks)
        )

        application.add_handler(
            MessageHandler(filters.regex(r"^/details_\d+$"), send_task_details)
        )
        application.add_handler(
            MessageHandler(filters.regex(r"^/pickup_\d+$"), pick_up_task)
        )
        application.add_handler(
            MessageHandler(filters.regex(r"^/done_\d+$"), mark_task_as_done)
        )

        application.run_polling(allowed_updates=Update.ALL_TYPES)
