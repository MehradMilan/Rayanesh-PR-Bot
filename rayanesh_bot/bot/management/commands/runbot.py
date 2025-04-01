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
    opened_gate,
    closed_gate,
    deactivate_gate,
    choose_playlist,
    send_music_start,
    receive_music,
    receive_name,
    listen_choose_playlist,
    listen_music_start,
    confirm_delete,
    create_playlist_cover,
    create_playlist_description,
    create_playlist_name,
    create_playlist_start,
    my_playlists,
    show_playlist_details,
    toggle_playlist_visibility,
    handle_send_to_raya,
    edit_title,
    edit_cover,
    receive_new_cover,
    receive_new_title,
    all_songs,
    remove_song,
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
                (bot.commands.SEND_MUSIC_COMMAND, "اضافه کردن موسیقی به پلی‌لیست"),
                (bot.commands.LISTEN_MUSIC_COMMAND, "موسیقی بشنویم!"),
                (bot.commands.MY_PLAYLISTS_COMMAND, "تمام پلی‌لیست‌ها"),
                (bot.commands.CREATE_PLAYLIST_COMMAND, "پلی‌لیست خودتو بساز!"),
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
            MessageHandler(filters.Regex(r"^/opened\d+(?:@\w+)?$"), opened_gate)
        )
        application.add_handler(
            MessageHandler(filters.Regex(r"^/closed_\d+(?:@\w+)?$"), closed_gate)
        )
        application.add_handler(
            MessageHandler(filters.Regex(r"^/holiday_\d+(?:@\w+)?$"), deactivate_gate)
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

        send_music_handler = ConversationHandler(
            entry_points=[
                CommandHandler(bot.commands.SEND_MUSIC_COMMAND, send_music_start)
            ],
            states={
                bot.states.CHOOSE_PLAYLIST: [CallbackQueryHandler(choose_playlist)],
                bot.states.SEND_MUSIC: [
                    MessageHandler(
                        filters.AUDIO | filters.Document.AUDIO, receive_music
                    )
                ],
                bot.states.ENTER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
                ],
                bot.states.SEND_TO_RAYAMUSIC: [
                    CallbackQueryHandler(handle_send_to_raya)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(send_music_handler)

        listen_music_handler = ConversationHandler(
            entry_points=[
                CommandHandler(bot.commands.LISTEN_MUSIC_COMMAND, listen_music_start)
            ],
            states={
                bot.states.LISTEN_CHOOSE_PLAYLIST: [
                    CallbackQueryHandler(listen_choose_playlist)
                ],
                bot.states.CONFIRM_DELETE: [CallbackQueryHandler(confirm_delete)],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(listen_music_handler)

        create_playlist_handler = ConversationHandler(
            entry_points=[
                CommandHandler(
                    bot.commands.CREATE_PLAYLIST_COMMAND, create_playlist_start
                )
            ],
            states={
                bot.states.CREATE_PLAYLIST_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, create_playlist_name
                    )
                ],
                bot.states.CREATE_PLAYLIST_DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, create_playlist_description
                    )
                ],
                bot.states.CREATE_PLAYLIST_COVER: [
                    MessageHandler(filters.PHOTO, create_playlist_cover)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(create_playlist_handler)

        my_playlists_handler = ConversationHandler(
            entry_points=[
                CommandHandler(bot.commands.MY_PLAYLISTS_COMMAND, my_playlists)
            ],
            states={
                bot.states.SHOW_PLAYLIST_DETAILS: [
                    CallbackQueryHandler(show_playlist_details)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(my_playlists_handler)
        application.add_handler(
            MessageHandler(
                filters.Regex(r"^/(public|private)_\d+(?:@\w+)?$"),
                toggle_playlist_visibility,
            )
        )

        edit_playlist_handler = ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Regex(r"^/edit_title_\d+(?:@\w+)?$"), edit_title
                ),
                MessageHandler(
                    filters.Regex(r"^/edit_cover_\d+(?:@\w+)?$"), edit_cover
                ),
            ],
            states={
                bot.states.EDIT_TITLE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_title)
                ],
                bot.states.EDIT_COVER: [
                    MessageHandler(filters.PHOTO, receive_new_cover)
                ],
            },
            fallbacks=[CommandHandler(bot.commands.CANCEL_COMMAND, cancel)],
        )
        application.add_handler(edit_playlist_handler)

        application.add_handler(
            MessageHandler(filters.Regex(r"^/all_songs_\d+(?:@\w+)?$"), all_songs)
        )
        application.add_handler(
            MessageHandler(filters.Regex(r"^/remove_\d+(?:@\w+)?$"), remove_song)
        )

        application.add_handler(CommandHandler(bot.commands.HELP_COMMAND, help))

        application.run_polling(allowed_updates=Update.ALL_TYPES)
