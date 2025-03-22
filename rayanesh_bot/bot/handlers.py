import logging
import re
from telegram import Update, User
from telegram.ext import CallbackContext, ConversationHandler

from django.conf import settings

from user.models import TelegramUser
import reusable.db_sync_services as db_sync_services
from bot.tasks import extract_deeplink_from_message
import bot.commands
import reusable.persian_response as persian
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


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Authorization cancelled.")
    return ConversationHandler.END
