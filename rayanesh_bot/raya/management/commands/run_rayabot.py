from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

import django
from django.core.management.base import BaseCommand
from django.conf import settings

from raya.handlers import (
    accept_join,
    approve_join_request,
    list_groups,
    show_group_info,
    give_access,
    set_access_level,
    select_group,
    enter_doc_link,
    confirm_doc,
    revoke_access_start,
    revoke_process_link,
    revoke_select_group,
    remove_user_start,
    remove_select_group,
    remove_user,
    confirm_schedule,
    receive_schedule_time,
    send_notification_start,
    receive_notification_message,
    cancel,
)
import raya.commands
import raya.states


class Command(BaseCommand):
    help = "Runs the Raya Telegram bot"

    async def post_init(self, application):
        await application.bot.set_my_commands(
            [
                (raya.commands.ACCEPT_JOIN_GROUP_COMMAND, "Accept New Joiners"),
                (raya.commands.LIST_GROUPS_COMMAND, "List all active groups"),
                (
                    raya.commands.GIVE_ACCESS_COMMAND,
                    "Give a document's access to a group.",
                ),
                (
                    raya.commands.REVOKE_ACCESS_COMMAND,
                    "Revoke a document's access from a group.",
                ),
                (raya.commands.REMOVE_USER_COMMAND, "Remove a user from a group."),
                (raya.commands.SEND_NOTIFICATION, "Send notification to users"),
                (raya.commands.CANCEL_COMMAND, "Cancel a command"),
            ]
        )

    def handle(self, *args, **kwargs):
        django.setup()

        application = (
            Application.builder()
            .post_init(self.post_init)
            .token(settings.RAYA_BOT_TOKEN)
            .build()
        )

        application.add_handler(
            CommandHandler(raya.commands.ACCEPT_JOIN_GROUP_COMMAND, accept_join)
        )
        application.add_handler(
            CallbackQueryHandler(approve_join_request, pattern="^approve:")
        )
        application.add_handler(
            CallbackQueryHandler(approve_join_request, pattern="^deny:")
        )
        application.add_handler(
            CommandHandler(raya.commands.LIST_GROUPS_COMMAND, list_groups)
        )
        application.add_handler(
            CallbackQueryHandler(show_group_info, pattern="^groupinfo:")
        )

        give_access_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(raya.commands.GIVE_ACCESS_COMMAND, give_access)
            ],
            states={
                raya.states.SELECT_GROUP: [
                    MessageHandler(filters.Regex(r"^/group_\d+"), select_group)
                ],
                raya.states.ENTER_DOC_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_doc_link)
                ],
                raya.states.CONFIRM_DOC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_doc)
                ],
                raya.states.ACCESS_LEVEL: [
                    CallbackQueryHandler(
                        set_access_level, pattern="^(reader|commenter|writer)$"
                    )
                ],
            },
            fallbacks=[CommandHandler(raya.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(give_access_conv_handler)

        revoke_access_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(raya.commands.REVOKE_ACCESS_COMMAND, revoke_access_start)
            ],
            states={
                raya.states.SELECT_GROUP: [
                    MessageHandler(filters.Regex(r"^/group_\d+"), revoke_select_group)
                ],
                raya.states.ENTER_DOC_LINK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_process_link)
                ],
            },
            fallbacks=[CommandHandler(raya.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(revoke_access_conv_handler)

        remove_user_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler(raya.commands.REMOVE_USER_COMMAND, remove_user_start)
            ],
            states={
                raya.states.SELECT_GROUP: [
                    MessageHandler(filters.Regex(r"^/group_\d+"), remove_select_group)
                ],
                raya.states.SELECT_USER: [
                    MessageHandler(filters.Regex(r"^/remove_user_\d+"), remove_user)
                ],
            },
            fallbacks=[CommandHandler(raya.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(remove_user_conv_handler)

        send_notification_handler = ConversationHandler(
            entry_points=[
                CommandHandler(raya.commands.SEND_NOTIFICATION, send_notification_start)
            ],
            states={
                raya.states.SELECT_GROUP: [CallbackQueryHandler(select_group)],
                raya.states.RECEIVE_NOTIFICATION_MESSAGE: [
                    MessageHandler(
                        filters.TEXT | filters.PHOTO | filters.VIDEO,
                        receive_notification_message,
                    )
                ],
                raya.states.RECEIVE_SCHEDULE_TIME: [
                    MessageHandler(filters.TEXT, receive_schedule_time)
                ],
                raya.states.CONFIRM_SCHEDULE: [
                    CallbackQueryHandler(
                        confirm_schedule, pattern=r"^confirm_schedule$"
                    ),
                    CallbackQueryHandler(cancel, pattern=r"^cancel_schedule$"),
                ],
            },
            fallbacks=[CommandHandler(raya.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(send_notification_handler)

        application.run_polling(allowed_updates=Update.ALL_TYPES)
