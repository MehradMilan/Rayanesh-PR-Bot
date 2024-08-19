import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start, send_text, folder_selected, ask_email, confirm_creation, help_command
from db import init_db
from config import get_config

ASK_EMAIL, CONFIRM_CREATION = range(2)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def post_init(application):
    await application.bot.set_my_commands([
        ('send_text', 'ایجاد سند جدید'),
        ('help', 'راهنمایی'),
    ])

def main():
    init_db()
    
    TELEGRAM_TOKEN = get_config()['TELEGRAM.BOT']['TOKEN']
    application = Application.builder().post_init(post_init).token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('send_text', send_text))
    application.add_handler(CommandHandler('help', help_command))

    conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(folder_selected)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT, ask_email)],
            CONFIRM_CREATION: [MessageHandler(filters.TEXT, confirm_creation)],
        },
        fallbacks=[],
    )
    
    application.add_handler(conversation_handler)
    application.run_polling()

if __name__ == '__main__':
    main()