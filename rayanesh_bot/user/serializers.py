from rest_framework import serializers
from .models import TelegramUser


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = [
            "id",
            "telegram_id",
            "username",
            "name",
            "user_type",
            "email",
            "is_authorized",
            "created_at",
        ]
