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
    cancel,
)
import raya.commands
import raya.states


class Command(BaseCommand):
    help = "Runs the Raya Telegram bot"

    async def post_init(self, application):
        await application.bot.set_my_commands(
            [
                ("accept_join", "Accept New Joiners"),
                ("list_groups", "List all active groups"),
                ("give_access", "Give a document's access to a group."),
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

        application.run_polling(allowed_updates=Update.ALL_TYPES)
