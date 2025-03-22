import logging
import re
from telegram import Update, User
from telegram.ext import CallbackContext

from django.conf import settings

from user.models import TelegramUser
import reusable.db_sync_services as db_sync_services
from bot.tasks import extract_deeplink_from_message
import reusable.telegram_bot.bot_command
import reusable.persian_response as persian

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user
    command, params = extract_deeplink_from_message(update.message.text)
    if command is None:
        telegram_user, created = await db_sync_services.get_or_create_telegram_user(
            user
        )
        await update.message.reply_text(persian.START_SUCCESS)
    elif command in reusable.telegram_bot.bot_command.DEEPLINK_HANDLERS.keys():
        response: str = await reusable.telegram_bot.bot_command.DEEPLINK_HANDLERS[
            command
        ](telegram_user.id, params[0])
        await update.message.reply_text(response)
        return
    else:
        return


async def authorize(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user
    telegram_user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        user.id
    )

    if not telegram_user:
        await update.message.reply_text(persian.USER_NOT_EXIST)
        return

    if telegram_user.is_authorized:
        await update.message.reply_text(persian.USER_AUTH_ALREADY_EXIST)
        return

    if not telegram_user.name:
        await update.message.reply_text(persian.ENTER_NAME)
        telegram_user.state = TelegramUser.AWAITING_NAME_STATE
        await db_sync_services.save_user(telegram_user)
        return

    if not telegram_user.email:
        await update.message.reply_text(persian.ENTER_EMAIL)
        telegram_user.state = TelegramUser.AWAITING_EMAIL_STATE
        await db_sync_services.save_user(telegram_user)
        return

    telegram_user.is_authorized = True
    await db_sync_services.save_user(telegram_user)
    await update.message.reply_text(
        f"{persian.USER_AUTH_SUCCESS}, {telegram_user.name}:)"
    )


async def handle_name(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user or telegram_user.state != TelegramUser.AWAITING_NAME_STATE:
        return

    telegram_user.name = update.message.text.strip()
    telegram_user.state = TelegramUser.AWAITING_EMAIL_STATE
    await db_sync_services.save_user(telegram_user)

    await update.message.reply_text(persian.ENTER_EMAIL)


async def handle_email(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user or telegram_user.state != TelegramUser.AWAITING_EMAIL_STATE:
        return

    email = update.message.text.strip()

    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
    if not re.match(EMAIL_REGEX, email):
        await update.message.reply_text(persian.EMAIL_INVALID)
        return

    telegram_user.email = email
    telegram_user.is_authorized = True
    telegram_user.state = None
    await db_sync_services.save_user(telegram_user)

    await update.message.reply_text(persian.USER_AUTH_SUCCESS)
