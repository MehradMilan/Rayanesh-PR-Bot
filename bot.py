import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start, send_text, folder_selected, ask_email, confirm_creation, help_command
from handlers import start, help_command, send_text, send_text_anon, edit_text_anon, finish_text, ask_anon_text, receive_anon_text, confirm_edit, update_anon_text, confirm_finish
from handlers import ask_anon_edit_code
from db import init_db
from init import get_application

ASK_EMAIL, ASK_ANON_TEXT, EDIT_ANON_CODE, EDIT_ANON_TEXT, CONFIRM_FINISH, CONFIRM_CREATION = range(6)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    init_db()
    
    application = get_application()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('send_text', send_text))
    application.add_handler(CommandHandler('send_text_anon', send_text_anon))
    application.add_handler(CommandHandler('edit_text_anon', edit_text_anon))
    application.add_handler(CommandHandler('finish_text', finish_text))

    conversation_handler_send = ConversationHandler(
        entry_points=[CallbackQueryHandler(folder_selected, pattern="^send_text\\|")],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            CONFIRM_CREATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_creation)],
        },
        fallbacks=[],
    )
    
    conversation_handler_anon = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_anon_text, pattern="^send_text_anon\\|")],
        states={
            ASK_ANON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_anon_text)],
        },
        fallbacks=[],
    )

    conversation_handler_edit = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_anon_edit_code, pattern="^edit_text_anon\\|")],
        states={
            EDIT_ANON_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_edit)],
            EDIT_ANON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_anon_text)]
        },
        fallbacks=[],
    )

    conversation_handler_finish = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(r'^\d{6}$'), confirm_finish)],
        states={
            CONFIRM_FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_finish)]
        },
        fallbacks=[],
    )

    application.add_handler(conversation_handler_send)
    application.add_handler(conversation_handler_anon)
    application.add_handler(conversation_handler_edit)
    application.add_handler(conversation_handler_finish)

    application.run_polling()

if __name__ == '__main__':
    main()