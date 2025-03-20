from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)  # User's unique Telegram ID
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username or self.telegram_id}"