from django.urls import path
from .views import TelegramUserList

urlpatterns = [
    path("users/", TelegramUserList.as_view(), name="user-list"),
]