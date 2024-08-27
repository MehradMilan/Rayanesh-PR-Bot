from telegram.ext import Application
from config import get_config

APPLICATION = None

def get_application():
    global APPLICATION
    if APPLICATION:
        return APPLICATION
    TELEGRAM_TOKEN = get_config()['TELEGRAM.BOT']['TOKEN']
    application = Application.builder().post_init(post_init).token(TELEGRAM_TOKEN).build()
    APPLICATION = application
    return application

async def post_init(application):
    await application.bot.set_my_commands([
        ('send_text', 'ارسال متن جدید'),
        ('finish_text', 'پایان نگارش متن'),
        ('send_text_anon', 'ارسال متن ناشناس'),
        ('edit_text_anon', 'ویرایش متن ناشناس'),
        ('random_poem', 'شعر تصادفی'),
        ('select_poet', 'شعر از شاعر خاص'),
        ('feedback', 'ارسال بازخورد'),
        ('help', 'راهنمایی'),
    ])