from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
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
    select_group,
    select_urgency,
    start_add_task,
    enter_deadline,
    enter_description,
    enter_title,
    help,
)
import bot.commands
import bot.states


class Command(BaseCommand):
    help = "Runs the Rayanesh Telegram bot"

    async def post_init(self, application):
        await application.bot.set_my_commands(
            [
                (bot.commands.START_COMMAND, "شروع!"),
                (bot.commands.AUTHORIZE_COMMAND, "احراز هویت"),
                (bot.commands.ADD_TASK_COMMAND, "اضافه کردن تسک به گروه"),
                (bot.commands.HELP_COMMAND, "راهنمایی"),
                (
                    bot.commands.LIST_TASKS_COMMAND,
                    "لیست کردن تمام تسک‌های فعال این گروه",
                ),
            ]
        )

    def handle(self, *args, **kwargs):
        django.setup()

        application = (
            Application.builder()
            .post_init(self.post_init)
            .token(settings.TELEGRAM_BOT_TOKEN)
            .build()
        )

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
            MessageHandler(filters.Regex(r"^/details_\d+(?:@\w+)?$"), send_task_details)
        )
        application.add_handler(
            MessageHandler(filters.Regex(r"^/pickup_\d+(?:@\w+)?$"), pick_up_task)
        )
        application.add_handler(
            MessageHandler(filters.Regex(r"^/done_\d+(?:@\w+)?$"), mark_task_as_done)
        )
        application.add_handler(
            MessageHandler(
                filters.Regex(r"^/opened\d+(?:@\w+)?$"),
            )
        )
        application.add_handler(
            MessageHandler(
                filters.Regex(r"^/closed_\d+(?:@\w+)?$"),
            )
        )
        application.add_handler(
            MessageHandler(
                filters.Regex(r"^/holiday_\d+(?:@\w+)?$"),
            )
        )

        add_task_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(bot.commands.ADD_TASK_COMMAND, start_add_task)
            ],
            states={
                bot.states.SELECT_GROUP: [
                    CallbackQueryHandler(select_group, pattern=r"^group_\d+$")
                ],
                bot.states.ENTER_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_title)
                ],
                bot.states.ENTER_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description)
                ],
                bot.states.SELECT_URGENCY: [CallbackQueryHandler(select_urgency)],
                bot.states.ENTER_DEADLINE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_deadline)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(add_task_conv_handler)

        application.add_handler(CommandHandler(bot.commands.HELP_COMMAND, help))

        application.run_polling(allowed_updates=Update.ALL_TYPES)
