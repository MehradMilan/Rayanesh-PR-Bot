import logging
import re
from telegram import Update, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from datetime import timedelta
from asgiref.sync import sync_to_async
import typing

from django.conf import settings
from django.utils import timezone
from django.db.models import Case, When, IntegerField, Value

from user.models import TelegramUser, Group, Task
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
        message = f"Group {chat.title} chat ID:\n`{chat.id}`"
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
                scope_group=group, state__in=[Task.INITIAL_STATE, Task.TAKEN_STATE]
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
        task_message += f"/details_{task.id}"
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


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(persian.CANCEL_CONVERSATION)
    return ConversationHandler.END


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(persian.HELP_SUCCESS)
    return
