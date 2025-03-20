import requests
from django.conf import settings

WEBHOOK_URL = f'https://{settings.SERVER_DOMAIN}/api/bot/webhook/'
SET_WEBHOOK_URL = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}'

print('Requesting...')
response = requests.get(SET_WEBHOOK_URL)
print(response.text)