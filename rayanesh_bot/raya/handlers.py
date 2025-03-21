import logging
from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

async def accept_join(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Accepted!')