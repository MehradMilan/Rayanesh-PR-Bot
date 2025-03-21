from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# @csrf_exempt
# def webhook(request):
#     """
#     Handle incoming webhook updates from Telegram.
#     """
#     json_str = request.body.decode('UTF-8')
#     update = Update.de_json(json_str, application.bot)
#     application.update_queue.put(update)

#     return JsonResponse({"status": "ok"})