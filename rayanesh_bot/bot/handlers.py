import logging
import re
from telegram import Update, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from datetime import timedelta
from asgiref.sync import sync_to_async
import typing
import asyncio
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from django.db.models import Case, When, IntegerField, Value, Q, CharField

import bot.tasks
from user.models import TelegramUser, Group, Task
from music.models import Song, Playlist, SentSong
from raya.models import Gate
import reusable.db_sync_services as db_sync_services
from bot.tasks import extract_deeplink_from_message
import bot.commands
import reusable.persian_response as persian
import reusable.telegram_bots
import bot.states

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user
    command, params = await extract_deeplink_from_message(update.message.text)
    if command is None:
        telegram_user, created = await db_sync_services.get_or_create_telegram_user(
            user
        )
        await update.message.reply_text(persian.START_SUCCESS)
    elif command in bot.commands.DEEPLINK_HANDLERS.keys():
        response: str = await bot.commands.DEEPLINK_HANDLERS[command](
            user.id, params[0]
        )
        await update.message.reply_text(response)
        return
    else:
        return


async def authorize(update: Update, context: CallbackContext) -> int:
    user: User = update.effective_user
    telegram_user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        user.id
    )

    if not telegram_user:
        await update.message.reply_text(persian.USER_NOT_EXIST)
        return ConversationHandler.END

    await update.message.reply_text(persian.ENTER_NAME)
    return bot.states.AWAITING_NAME


async def handle_name(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user:
        await update.message.reply_text(persian.USER_NOT_EXIST)
        return ConversationHandler.END

    telegram_user.name = update.message.text.strip()
    await db_sync_services.save_user(telegram_user)
    await update.message.reply_text(persian.ENTER_EMAIL)
    return bot.states.AWAITING_EMAIL


async def handle_email(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user:
        await update.message.reply_text(persian.USER_NOT_EXIST)
        return ConversationHandler.END

    email = update.message.text.strip()

    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
    if not re.match(EMAIL_REGEX, email):
        await update.message.reply_text(persian.EMAIL_INVALID)
        return bot.states.AWAITING_EMAIL

    telegram_user.email = email
    telegram_user.is_authorized = True
    await db_sync_services.save_user(telegram_user)

    await update.message.reply_text(persian.USER_AUTH_SUCCESS)
    return ConversationHandler.END


async def send_group_chat_id_to_healthcheck_channel(
    update: Update, context: CallbackContext
) -> None:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if (
        telegram_user is None
        or not telegram_user.is_authorized
        or telegram_user.user_type != TelegramUser.MANAGER_USER
    ):
        await update.message.reply_text(persian.NO_ACCESS)
        return

    chat = update.message.chat
    if chat.type.upper() not in ["GROUP", "SUPERGROUP"]:
        await update.message.reply_text(persian.NO_GROUP)
        logger.info(f"Invalid request in chat: {chat.title} with id={chat.id}")
        return

    try:
        message = f"Group {chat.title} chat ID:\n`{chat.id}`".replace(
            "_", "\_"
        ).replace("-", "\-")
        await reusable.telegram_bots.get_raya_bot().send_message(
            chat_id=settings.HEALTHCHECK_CHAT_ID, text=message, parse_mode="MarkdownV2"
        )
        await update.message.reply_text(persian.SEND_CHAT_ID_SUCCESS)
    except Exception as e:
        logger.error(f"Failed to send message to channel: {e}")


async def list_tasks(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id

    if not update.message.chat.type in ["group", "supergroup"]:
        await update.message.reply_text(persian.NO_GROUP)
        return

    group: Group = await sync_to_async(
        lambda: Group.objects.filter(chat_id=chat_id).first()
    )()
    if not group:
        await update.message.reply_text(persian.GROUP_NOT_FOUND)
        return

    PRIORITY_ORDER = {
        "very_high": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    tasks = await sync_to_async(
        lambda: list(
            Task.objects.filter(
                scope_group=group,
                state__in=[Task.INITIAL_STATE, Task.TAKEN_STATE],
                deadline__gte=timezone.now(),
            )
            .annotate(
                priority_order=Case(
                    *[
                        When(priority_level=key, then=Value(val))
                        for key, val in PRIORITY_ORDER.items()
                    ],
                    output_field=IntegerField(),
                )
            )
            .order_by("priority_order", "deadline")
        )
    )()

    if not tasks:
        await update.message.reply_text(persian.NO_PENDING_TASKS)
        return

    task_message = persian.TASK_LIST_HEADER

    for task in tasks:
        priority = task.priority_level
        deadline_str = (
            "بدون مهلت" if not task.deadline else str(task.deadline - timedelta(days=0))
        )
        remaining_time = task.deadline - timezone.now() if task.deadline else None
        if remaining_time:
            days_left = remaining_time.days
            hours_left = remaining_time.seconds // 3600
            deadline_str = f"{days_left} روز و {hours_left} ساعت باقی مانده"

        task_message += f"{persian.PRIORITY_EMOJIS[priority]} {task.title}\n"
        task_message += f"ددلاین: {deadline_str}\n"
        task_message += f"/details_{task.id} "
        if task.state == Task.INITIAL_STATE:
            task_message += f"/pickup_{task.id}\n\n"
        elif task.state == Task.TAKEN_STATE:
            task_message += f"/done_{task.id}\n\n"

    await update.message.reply_text(task_message)


async def task_group_filters(
    update: Update, command_str: str
) -> typing.Tuple[bool, str | Task]:
    message = update.message.text

    if not update.message.chat.type.upper() in ["GROUP", "SUPERGROUP"]:
        return False, persian.NO_GROUP
    chat_id = update.message.chat.id
    group: Group = await sync_to_async(
        lambda: Group.objects.filter(chat_id=chat_id).first()
    )()
    if not group:
        return False, persian.GROUP_NOT_FOUND

    task_id = re.match(rf"/{command_str}_(\d+)(?:@\w+)?", message).groups()[0]
    task = await sync_to_async(
        lambda: Task.objects.filter(id=task_id, scope_group=group).first()
    )()
    if task is None:
        return False, persian.TASK_NOT_FOUND

    return True, task


async def send_task_details(update: Update, context: CallbackContext) -> None:
    is_ok, response = await task_group_filters(update=update, command_str="details")
    if not is_ok:
        await update.message.reply_text(response)
        return
    task: Task = response
    priority_name = persian.PRIORITY_NAMES.get(task.priority_level, "نامشخص")
    deadline = task.deadline if task.deadline else "ندارد"
    task_message = persian.TASK_DETAILS_HEADER.format(
        title=task.title,
        description=task.description,
        priority_name=priority_name,
        deadline=deadline,
    )
    await update.message.reply_text(task_message)


async def pick_up_task(update: Update, context: CallbackContext) -> None:
    is_ok, response = await task_group_filters(update=update, command_str="pickup")
    if not is_ok:
        await update.message.reply_text(response)
        return
    task: Task = response
    if await db_sync_services.get_task_assignee(task=task):
        await update.message.reply_text(persian.TASK_ALREADY_TAKEN)
        return
    telegram_user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        update.effective_user.id
    )
    await db_sync_services.assigne_user_to_task(user=telegram_user, task=task)
    await update.message.reply_text(
        persian.TASK_PICKED_UP.format(title=task.title, name=telegram_user.name)
    )


async def mark_task_as_done(update: Update, context: CallbackContext) -> None:
    is_ok, response = await task_group_filters(update=update, command_str="done")
    if not is_ok:
        await update.message.reply_text(response)
        return
    task: Task = response
    telegram_user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        update.effective_user.id
    )
    if await db_sync_services.get_task_assignee(task=task) != telegram_user:
        await update.message.reply_text(persian.ERROR_TASK_DONE)
        return
    await db_sync_services.mark_task_as_done(task=task)
    await update.message.reply_text(persian.TASK_MARKED_DONE.format(title=task.title))


async def start_add_task(update: Update, context: CallbackContext):
    if update.message.chat.type.upper() in ["GROUP", "SUPERGROUP"]:
        await update.message.reply_text(persian.COME_TO_PV)
        return ConversationHandler.END

    context.user_data.clear()
    user = await db_sync_services.get_telegram_user_by_id(
        telegram_id=update.effective_user.id
    )
    context.user_data["user"] = user
    groups = await db_sync_services.get_user_groups(user)

    if not groups:
        await update.message.reply_text(persian.NO_ACTIVE_GROUP_MEMBER)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(group.title, callback_data=f"group_{group.id}")]
        for group in groups
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        persian.SELECT_GROUP_HEADER, reply_markup=reply_markup
    )
    return bot.states.SELECT_GROUP


async def select_group(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    try:
        group_id = int(query.data.split("_", 1)[1])
        group = await db_sync_services.get_group_by_id(group_id)
    except Exception:
        await update.message.reply_text(persian.GROUP_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["group"] = group
    await query.message.reply_text(persian.ENTER_TITLE)
    return bot.states.ENTER_TITLE


async def enter_title(update: Update, context: CallbackContext):
    context.user_data["title"] = update.message.text.strip()
    await update.message.reply_text(persian.ENTER_DESCRIPTION)
    return bot.states.ENTER_DESCRIPTION


async def enter_description(update: Update, context: CallbackContext):
    context.user_data["description"] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton(f"{emoji} {label}", callback_data=level)]
        for level, (label, emoji) in persian.PRIORITY_LEVEL_MAP.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(persian.SELECT_URGENCY, reply_markup=reply_markup)
    return bot.states.SELECT_URGENCY


async def select_urgency(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    level = query.data
    context.user_data["priority_level"] = level

    if level == Task.VERY_HIGH_PRIORITY:
        deadline = timezone.now().replace(hour=23, minute=59)
        if (deadline - timezone.now()).total_seconds() > 6 * 3600:
            deadline = timezone.now() + timedelta(hours=6)
        context.user_data["deadline"] = deadline
        return await save_new_task(query, context)

    await query.message.reply_text(persian.ENTER_DEADLINE_DAYS)
    return bot.states.ENTER_DEADLINE


async def enter_deadline(update: Update, context: CallbackContext):
    try:
        days = int(update.message.text.strip())
        deadline = timezone.now().date() + timedelta(days=days)
        deadline = timezone.make_aware(
            timezone.datetime.combine(
                deadline, timezone.datetime.min.time().replace(hour=23, minute=59)
            )
        )
        context.user_data["deadline"] = deadline
    except Exception:
        await update.message.reply_text(persian.INVALID_DEADLINE_INPUT)
        return bot.states.ENTER_DEADLINE

    return await save_new_task(update, context)


async def save_new_task(update_or_query, context: CallbackContext):
    task = Task(
        title=context.user_data["title"],
        description=context.user_data["description"],
        scope_group=context.user_data["group"],
        priority_level=context.user_data["priority_level"],
        deadline=context.user_data["deadline"],
        owner_user=context.user_data["user"],
    )
    await sync_to_async(task.save)()
    await update_or_query.message.reply_text(persian.TASK_CREATED_SUCCESS)
    return ConversationHandler.END


async def gate_group_filters(
    update: Update, command_str: str
) -> typing.Tuple[bool, str | Gate]:
    message = update.message.text

    if not update.message.chat.type.upper() in ["GROUP", "SUPERGROUP"]:
        return False, persian.NO_GROUP
    chat_id = update.message.chat.id
    group: Group = await sync_to_async(
        lambda: Group.objects.filter(chat_id=chat_id).first()
    )()
    if not group:
        return False, persian.GROUP_NOT_FOUND

    gate_id = re.match(rf"/{command_str}_(\d+)(?:@\w+)?", message).groups()[0]
    gate = await sync_to_async(
        lambda: Gate.objects.filter(id=gate_id, gate_keepers_group=group).first()
    )()
    if gate is None:
        return False, persian.GATE_NOT_FOUND

    return True, gate


async def closed_gate(update: Update, context: CallbackContext) -> None:
    is_ok, response = await gate_group_filters(update=update, command_str="closed")
    if not is_ok:
        logger.info(f"Invalid command on closing gate: {response}")
        return
    user = await db_sync_services.get_telegram_user_by_id(
        telegram_id=update.effective_user.id
    )
    gate: Gate = response
    await db_sync_services.close_gate(gate=gate)
    await update.message.reply_text(persian.CLOSED_GATE_RESPONSE.format(name=user.name))


async def opened_gate(update: Update, context: CallbackContext) -> None:
    is_ok, response = await gate_group_filters(update=update, command_str="opened")
    if not is_ok:
        logger.info(f"Invalid command on opening gate: {response}")
        return
    user = await db_sync_services.get_telegram_user_by_id(
        telegram_id=update.effective_user.id
    )
    gate: Gate = response
    await db_sync_services.open_gate(gate=gate)
    await db_sync_services.activate_gate(gate=gate)
    await update.message.reply_text(persian.OPENED_GATE_RESPONSE.format(name=user.name))


async def deactivate_gate(update: Update, context: CallbackContext) -> None:
    is_ok, response = await gate_group_filters(update=update, command_str="holiday")
    if not is_ok:
        logger.info(f"Invalid command on deactivating gate: {response}")
        return
    user = await db_sync_services.get_telegram_user_by_id(
        telegram_id=update.effective_user.id
    )
    gate: Gate = response
    await db_sync_services.deactivate_gate(gate=gate)
    await update.message.reply_text(persian.HOLIDAY_GATE_RESPONSE)


async def send_music_start(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    playlists = await sync_to_async(
        lambda: list(
            Playlist.objects.filter(
                Q(is_active=True)
                & (Q(is_public=True, is_accessible=True) | Q(owner=telegram_user))
            ).distinct()
        )
    )()
    if not playlists:
        await update.message.reply_text(persian.NO_PLAYLIST_EXIST)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(p.name, callback_data=str(p.id))] for p in playlists
    ]
    await update.message.reply_text(
        persian.CHOOSE_PLAYLIST_ADD_MUSIC,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return bot.states.CHOOSE_PLAYLIST


async def choose_playlist(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    playlist_id = int(query.data)
    context.user_data["playlist_id"] = playlist_id

    await query.message.reply_text(persian.SEND_MUSIC_AUDIO_FILE)
    return bot.states.SEND_MUSIC


async def receive_music(update: Update, context: CallbackContext):
    message = update.message
    audio = message.audio

    if not audio:
        await update.message.reply_text(
            f"{persian.INVALID_AUDIO_FILE}\n\n{persian.SEND_MUSIC_AUDIO_FILE}"
        )
        return bot.states.SEND_MUSIC

    telegram_file = await context.bot.get_file(audio.file_id)
    file_bytes = await telegram_file.download_as_bytearray()
    file_bytes = BytesIO(file_bytes)
    title, artist = bot.tasks.get_audio_title_and_artist(file_bytes)
    context.user_data["artist"] = artist
    context.user_data["file_message"] = message
    if title is None:
        await update.message.reply_text(persian.ASK_SONG_NAME)
        return bot.states.ENTER_NAME
    context.user_data["song_name"] = title
    return await forward_to_save_music(update=update, context=context)


async def receive_name(update: Update, context: CallbackContext):
    song_name = update.message.text
    context.user_data["song_name"] = song_name
    return await forward_to_save_music(update=update, context=context)


async def forward_to_save_music(update: Update, context: CallbackContext):
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(telegram_id=user.id)
    original_message = context.user_data["file_message"]
    playlist_id = context.user_data["playlist_id"]
    playlist = await sync_to_async(lambda: Playlist.objects.get(id=playlist_id))()
    song_name = context.user_data["song_name"]
    artist = context.user_data["artist"]

    caption = persian.MUSIC_CAPTION.format(
        song_name=song_name,
        username=(telegram_user.username or telegram_user.name),
        rayanesh_id=settings.RAYANESH_CHANNEL_ID,
    )

    try:
        forwarded = await context.bot.copy_message(
            chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
            from_chat_id=user.id,
            message_id=int(original_message.message_id),
            caption=caption,
        )
    except Exception as e:
        logger.error(f"Failed to save music: {e}")
        return ConversationHandler.END

    try:
        await context.bot.delete_message(
            chat_id=user.id,
            message_id=original_message.message_id,
        )
    except Exception as e:
        logger.error(f"Failed to delete original file.")

    await sync_to_async(
        lambda: playlist.songs.add(
            Song.objects.create(
                name=song_name,
                channel_message_id=str(forwarded.message_id),
                added_by=telegram_user,
                caption=caption,
                artist=artist,
            )
        )
    )()
    context.user_data["last_forwarded_message_id"] = forwarded.message_id

    keyboard = [
        [
            InlineKeyboardButton(persian.YES, callback_data="send_to_raya_yes"),
            InlineKeyboardButton(persian.NO, callback_data="send_to_raya_no"),
        ]
    ]
    await update.message.reply_text(
        persian.SEND_MUSIC_SUCCESS_ASK_SEND_RAYA_MUSIC,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return bot.states.SEND_TO_RAYAMUSIC


async def handle_send_to_raya(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "send_to_raya_yes":
        try:
            await context.bot.copy_message(
                chat_id=settings.RAYAMUSIC_CHANNEL_CHAT_ID,
                from_chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                message_id=int(context.user_data["last_forwarded_message_id"]),
            )
            await query.message.reply_text(persian.SEND_TO_RAYA_MUSIC_SUCCESS)
        except Exception as e:
            logger.error(f"Failed to forward to RAYAMUSIC channel: {e}")
            await query.message.reply_text(persian.SEND_TO_RAYA_MUSIC_FAIL)
    else:
        await query.message.reply_text(persian.NOT_SEND_TO_RAYA_MUSIC)

    return ConversationHandler.END


async def listen_music_start(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    playlists = await sync_to_async(
        lambda: list(
            Playlist.objects.filter(
                Q(is_active=True)
                & (
                    Q(owner=telegram_user)
                    | Q(accesses__user=telegram_user)
                    | Q(is_public=True, is_accessible=True)
                )
            )
            .annotate(
                access_type=Case(
                    When(owner=telegram_user, then=Value("owner")),
                    When(accesses__user=telegram_user, then=Value("shared")),
                    When(is_public=True, is_accessible=True, then=Value("public")),
                    default=Value("unknown"),
                    output_field=CharField(),
                )
            )
            .distinct()
        )
    )()
    if not playlists:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return ConversationHandler.END

    emoji_map = persian.PLAYLIST_TYPE_EMOJI_MAP
    keyboard = [
        [
            InlineKeyboardButton(
                f"{emoji_map.get(p.access_type, persian.PLAYLIST_DEFAULT_TYPE_EMOJI)} {p.name}",
                callback_data=str(p.id),
            )
        ]
        for p in playlists
    ]

    await update.message.reply_text(
        f"{persian.PLAYLIST_TYPES_EXPL}\n{persian.SELECT_PLAYLIST_TO_LISTEN}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return bot.states.LISTEN_CHOOSE_PLAYLIST


async def listen_choose_playlist(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    playlist_id = int(query.data)
    context.user_data["playlist_id"] = playlist_id

    keyboard = [
        [
            InlineKeyboardButton(persian.YES, callback_data="yes"),
            InlineKeyboardButton(persian.NO, callback_data="no"),
        ]
    ]
    await query.message.reply_text(
        persian.ASK_DELETE_PREVIOUS_SONGS,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return bot.states.CONFIRM_DELETE


async def confirm_delete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    telegram_user = await db_sync_services.get_telegram_user_by_id(
        telegram_id=telegram_id
    )

    chat_id = update.effective_chat.id
    playlist_id = context.user_data["playlist_id"]

    if query.data == "yes":
        sent_songs = await sync_to_async(
            lambda: list(SentSong.objects.filter(user=telegram_user, chat_id=chat_id))
        )()
        sleep_time = (
            min(0.3, max(0.1, min(5 / len(sent_songs), 1.5))) if sent_songs else 0
        )
        for sent in sent_songs:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=int(sent.pv_message_id)
                )
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(sleep_time)
        await sync_to_async(
            lambda: SentSong.objects.filter(
                user=telegram_user, chat_id=chat_id
            ).delete()
        )()

    playlist = await sync_to_async(lambda: Playlist.objects.get(id=playlist_id))()
    song_count = await sync_to_async(lambda: playlist.songs.count())()
    owner = await db_sync_services.get_playlist_owner(playlist=playlist)

    if playlist.cover_message_id:
        try:
            caption_text = persian.PLAYLIST_COVER_CAPTION.format(
                name=playlist.name,
                username=owner.username,
                count=song_count,
                created_at=playlist.created_at.strftime("%Y-%m-%d"),
                description=playlist.description or "No description.",
            )
            msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                message_id=int(playlist.cover_message_id),
                caption=caption_text,
            )
            await sync_to_async(SentSong.objects.create)(
                user=telegram_user,
                chat_id=str(chat_id),
                pv_message_id=str(msg.message_id),
                playlist=playlist,
            )
        except Exception as e:
            logger.error(f"Sending cover failed: {e}")

    songs = await sync_to_async(
        lambda: list(playlist.songs.all().order_by("forwarded_at"))
    )()
    sleep_time = min(0.3, max(0.1, min(5 / len(songs), 1.5))) if songs else 0

    for song in songs:
        try:
            msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                message_id=int(song.channel_message_id),
            )
            await sync_to_async(SentSong.objects.create)(
                user=telegram_user,
                chat_id=str(chat_id),
                pv_message_id=str(msg.message_id),
                playlist=playlist,
            )
            await asyncio.sleep(sleep_time)
        except Exception:
            continue

    await query.message.reply_text(persian.LISTEN_MUSIC_SUCCESS)
    return ConversationHandler.END


async def create_playlist_start(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    await update.message.reply_text(persian.PLAYLIST_NAME)
    return bot.states.CREATE_PLAYLIST_NAME


async def create_playlist_name(update: Update, context: CallbackContext):
    context.user_data["playlist_name"] = update.message.text
    await update.message.reply_text(persian.PLAYLIST_DESCRIPTIONESCRIPTION)
    return bot.states.CREATE_PLAYLIST_DESCRIPTION


async def create_playlist_description(update: Update, context: CallbackContext):
    description = update.message.text
    if description.strip() == "-":
        description = ""
    elif len(description) > 400:
        await update.message.reply_text(
            persian.PLAYLIST_DESCRIPTION_MAX_LENGTH.format(400)
        )
        return bot.states.CREATE_PLAYLIST_DESCRIPTION

    context.user_data["playlist_description"] = description
    await update.message.reply_text(persian.PLAYLIST_SEND_COVER)
    return bot.states.CREATE_PLAYLIST_COVER


async def create_playlist_cover(update: Update, context: CallbackContext):
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(telegram_id=user.id)

    photo = update.message.photo
    if not photo:
        await update.message.reply_text(persian.PLAYLIST_SEND_COVER_INVALID_PHOTO)
        return bot.states.CREATE_PLAYLIST_COVER

    sent = await context.bot.copy_message(
        chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )

    playlist = await sync_to_async(Playlist.objects.create)(
        name=context.user_data["playlist_name"],
        owner=telegram_user,
        description=context.user_data["playlist_description"],
        cover_message_id=str(sent.message_id),
        is_active=True,
    )

    await update.message.reply_text(
        persian.PLAYLIST_CREATE_SUCCESS.format(name=playlist.name)
    )
    return ConversationHandler.END


async def my_playlists(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    playlists = await sync_to_async(
        lambda: list(
            Playlist.objects.filter(
                Q(is_active=True)
                & (
                    Q(owner=telegram_user)
                    | Q(accesses__user=telegram_user)
                    | Q(is_public=True, is_accessible=True)
                )
            )
            .annotate(
                access_type=Case(
                    When(owner=telegram_user, then=Value("owner")),
                    When(accesses__user=telegram_user, then=Value("shared")),
                    When(is_public=True, is_accessible=True, then=Value("public")),
                    default=Value("unknown"),
                    output_field=CharField(),
                )
            )
            .distinct()
        )
    )()

    if not playlists:
        await update.message.reply_text(persian.NO_PLAYLIST_EXIST)
        return ConversationHandler.END

    context.user_data["my_playlists"] = {str(p.id): p for p in playlists}

    emoji_map = persian.PLAYLIST_TYPE_EMOJI_MAP
    keyboard = [
        [
            InlineKeyboardButton(
                f"{emoji_map.get(p.access_type, persian.PLAYLIST_DEFAULT_TYPE_EMOJI)} {p.name}",
                callback_data=str(p.id),
            )
        ]
        for p in playlists
    ]

    await update.message.reply_text(
        f"{persian.PLAYLIST_TYPES_EXPL}\n{persian.SELECT_PLAYLIST_TO_SEE_DETAILS}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return bot.states.SHOW_PLAYLIST_DETAILS


async def show_playlist_details(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    playlist_id = query.data
    playlist = context.user_data["my_playlists"].get(playlist_id)

    if not playlist:
        await query.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return ConversationHandler.END
    owner = await sync_to_async(lambda: playlist.owner)()
    owner_username = owner.username or owner.name or "Unknown"
    song_count = await sync_to_async(lambda: playlist.songs.count())()

    caption = persian.PLAYLIST_COVER_CAPTION.format(
        name=playlist.name,
        username=owner_username,
        count=song_count,
        created_at=playlist.created_at.strftime("%Y-%m-%d"),
        description=playlist.description or "No description.",
    )

    if update.effective_user.id == owner.telegram_id:
        if playlist.is_public:
            caption += persian.CHANGE_VISIBILITY_COMMAND.format(
                to_State="private", playlist_id=playlist.id
            )
        else:
            caption += persian.CHANGE_VISIBILITY_COMMAND.format(
                to_State="public", playlist_id=playlist.id
            )
        caption += persian.PLAYLIST_DETAIL_CAPTION.format(
            playlist_id=playlist.id, share_playlist_uri=playlist.share_playlist_uri
        )

    if playlist.cover_message_id:
        try:
            await context.bot.copy_message(
                chat_id=query.message.chat.id,
                from_chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                message_id=int(playlist.cover_message_id),
                caption=caption,
            )
        except Exception as e:
            logger.error(e)

    return ConversationHandler.END


async def toggle_playlist_visibility(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    text = update.message.text
    match = re.match(r"/(public|private)_(\d+)(?:@\w+)?", text)
    if not match:
        return

    action, playlist_id = match.groups()
    playlist = await sync_to_async(
        lambda: Playlist.objects.filter(id=playlist_id, owner=telegram_user).first()
    )()
    if not playlist:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return

    playlist.is_public = True if action == "public" else False
    await sync_to_async(playlist.save)()

    status = persian.PUBLIC_SUCCESS if playlist.is_public else persian.PRIVATE_SUCCESS
    await update.message.reply_text(
        persian.CHANGE_VISIBILITY_SUCCESS.format(name=playlist.name, status=status),
        parse_mode="Markdown",
    )


async def check_private_and_authorized(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type.upper() != "PRIVATE":
        await update.message.reply_text(persian.USE_IN_PRIVATE_CHAT)
        return ConversationHandler.END

    telegram_user = await db_sync_services.get_telegram_user_by_id(telegram_id=user.id)
    if telegram_user is None or not telegram_user.is_authorized:
        await update.message.reply_text(persian.USER_UNAUTHORIZED)
        return ConversationHandler.END

    context.user_data["telegram_user"] = telegram_user
    return None


async def edit_title(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check

    telegram_user = context.user_data["telegram_user"]
    text = update.message.text

    match = re.match(r"/edit_title_(\d+)(?:@\w+)?", text)
    if not match:
        await update.message.reply_text(persian.INVALID_COMMAND)
        return ConversationHandler.END

    playlist_id = int(match.group(1))
    playlist = await sync_to_async(
        lambda: Playlist.objects.filter(id=playlist_id, owner=telegram_user).first()
    )()
    if not playlist:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["playlist_to_edit"] = playlist
    await update.message.reply_text(persian.SEND_PLAYLIST_TITLE)
    return bot.states.EDIT_TITLE


async def receive_new_title(update: Update, context: CallbackContext):
    playlist = context.user_data["playlist_to_edit"]
    new_title = update.message.text.strip()

    playlist.name = new_title
    await sync_to_async(playlist.save)()

    await update.message.reply_text(
        persian.PLAYLIST_TITLE_UPDATE_SUCCESS.format(new_title=new_title)
        .replace("_", "\_")
        .replace("-", "\-"),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def edit_cover(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check

    telegram_user = context.user_data["telegram_user"]
    text = update.message.text

    match = re.match(r"/edit_cover_(\d+)(?:@\w+)?", text)
    if not match:
        await update.message.reply_text(persian.INVALID_COMMAND)
        return ConversationHandler.END

    playlist_id = int(match.group(1))
    playlist: Playlist = await sync_to_async(
        lambda: Playlist.objects.filter(id=playlist_id, owner=telegram_user).first()
    )()
    if not playlist:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["playlist_to_edit"] = playlist
    await update.message.reply_text(persian.PLAYLIST_SEND_NEW_COVER)
    return bot.states.EDIT_COVER


async def receive_new_cover(update: Update, context: CallbackContext):
    playlist: Playlist = context.user_data["playlist_to_edit"]
    new_photo = update.message.photo

    if not new_photo:
        await update.message.reply_text(persian.PLAYLIST_SEND_COVER_INVALID_PHOTO)
        return bot.states.EDIT_COVER

    if playlist.cover_message_id:
        try:
            await context.bot.delete_message(
                chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                message_id=int(playlist.cover_message_id),
            )
        except Exception as e:
            logger.error(f"Failed to delete old cover: {e}")

    sent = await context.bot.copy_message(
        chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
    )

    playlist.cover_message_id = str(sent.message_id)
    await sync_to_async(playlist.save)()

    await update.message.reply_text(persian.PLAYLIST_COVER_UPDATE_SUCCESS)
    return ConversationHandler.END


async def all_songs(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return

    telegram_user = context.user_data["telegram_user"]
    text = update.message.text

    match = re.match(r"/all_songs_(\d+)", text)
    if not match:
        await update.message.reply_text(persian.INVALID_COMMAND)
        return

    playlist_id = int(match.group(1))
    playlist = await sync_to_async(
        lambda: Playlist.objects.filter(id=playlist_id, owner=telegram_user).first()
    )()

    if not playlist:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return

    songs = await sync_to_async(lambda: list(playlist.songs.all()))()

    if not songs:
        await update.message.reply_text(persian.EMPTY_PLAYLIST)
        return

    song_list = "\n".join(
        [
            f"{index + 1}. {song.name} - /remove_{song.id}"
            for index, song in enumerate(songs)
        ]
    )

    await update.message.reply_text(
        persian.SONGS_LIST_PLAYLIST.format(name=playlist.name, song_list=song_list)
    )
    return


async def remove_song(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return

    telegram_user = context.user_data["telegram_user"]
    text = update.message.text

    match = re.match(r"/remove_(\d+)(?:@\w+)?", text)
    if not match:
        await update.message.reply_text(persian.INVALID_COMMAND)
        return

    song_id = int(match.group(1))
    song: Song = await sync_to_async(lambda: Song.objects.filter(id=song_id).first())()

    if not song:
        await update.message.reply_text(persian.SONG_NOT_FOUND)
        return

    playlist = await sync_to_async(lambda: song.playlists.first())()
    owner = await sync_to_async(lambda: playlist.owner)()
    if owner != telegram_user:
        await update.message.reply_text(persian.INVALID_ACCESS_TO_PLAYLIST)
        return

    await sync_to_async(lambda: playlist.songs.remove(song))()
    await sync_to_async(lambda: song.delete())()

    try:
        await context.bot.delete_message(
            chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
            message_id=int(song.channel_message_id),
        )
    except Exception as e:
        logger.error(f"Failed to delete message from channel: {e}")

    await update.message.reply_text(persian.SONG_REMOVE_SUCCESS.format(name=song.name))


async def batch_send_music_start(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    playlists = await sync_to_async(
        lambda: list(
            Playlist.objects.filter(
                Q(is_active=True) & Q(owner=telegram_user)
            ).distinct()
        )
    )()
    if not playlists:
        await update.message.reply_text(persian.PLAYLIST_NOT_FOUND)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(p.name, callback_data=str(p.id))] for p in playlists
    ]
    await update.message.reply_text(
        persian.CHOOSE_PLAYLIST_ADD_MUSIC,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return bot.states.BATCH_CHOOSE_PLAYLIST


async def choose_batch_playlist(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    playlist_id = int(query.data)
    context.user_data["batch_playlist_id"] = playlist_id

    await query.message.reply_text(persian.BATCH_SEND_MUSIC_EXPL)
    context.user_data["batch_files"] = []

    return bot.states.BATCH_RECEIVE_MUSIC


async def receive_batch_music(update: Update, context: CallbackContext):
    message = update.message
    audio = message.audio

    if not audio:
        await update.message.reply_text(persian.INVALID_AUDIO_FILE)
        return bot.states.BATCH_RECEIVE_MUSIC

    context.user_data["batch_files"].append(message)

    return bot.states.BATCH_RECEIVE_MUSIC


async def done_batch_forward(update: Update, context: CallbackContext):
    check = await check_private_and_authorized(update, context)
    if check is not None:
        return check
    telegram_user = context.user_data["telegram_user"]

    playlist_id = context.user_data["batch_playlist_id"]
    if playlist_id is None:
        update.message.reply_text(persian.PLAYLIST_NOT_SELECTED)
        return ConversationHandler.END
    playlist = await sync_to_async(lambda: Playlist.objects.get(id=playlist_id))()

    batch_files = context.user_data["batch_files"] or []
    failed_files = []

    for file_message in batch_files:
        try:
            telegram_file = await context.bot.get_file(file_message.audio.file_id)
            file_bytes = await telegram_file.download_as_bytearray()
            file_bytes = BytesIO(file_bytes)
            song_name, artist = bot.tasks.get_audio_title_and_artist(file_bytes)
            if song_name is None:
                failed_files.append(file_message)
                continue

            caption = persian.MUSIC_CAPTION.format(
                song_name=song_name,
                username=(telegram_user.username or telegram_user.name),
                rayanesh_id=settings.RAYANESH_CHANNEL_ID,
            )

            forwarded = await context.bot.copy_message(
                chat_id=settings.MUSIC_CHANNEL_CHAT_ID,
                from_chat_id=telegram_user.telegram_id,
                message_id=file_message.message_id,
                caption=caption,
            )
            try:
                await context.bot.delete_message(
                    chat_id=telegram_user.telegram_id,
                    message_id=file_message.message_id,
                )
            except Exception as e:
                logger.error(f"Failed to delete original file.")

            await sync_to_async(
                lambda: playlist.songs.add(
                    Song.objects.create(
                        name=song_name,
                        channel_message_id=str(forwarded.message_id),
                        added_by=telegram_user,
                        caption=caption,
                        artist=artist,
                    )
                )
            )()

        except Exception as e:
            logger.error(f"Failed to process {file_message.message_id}: {e}")
            failed_files.append(file_message)

    if failed_files:
        failed_count = len(failed_files)
        await update.message.reply_text(
            persian.BATCH_SEND_MUSIC_FAIL.format(failed_count=failed_count)
        )
    else:
        await update.message.reply_text(persian.BATCH_SEND_MUSIC_SUCCESS)

    context.user_data["batch_files"] = []
    context.user_data["batch_playlist_id"] = None

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(persian.CANCEL_CONVERSATION)
    return ConversationHandler.END


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(persian.HELP_SUCCESS)
    return
