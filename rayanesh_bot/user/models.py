from django.db import models
from django.conf import settings


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_authorized = models.BooleanField(default=False)

    MANAGER_USER = "manager"
    INTERNAL_USER = "internal"

    USER_TYPE_CHOICES = (
        (MANAGER_USER, MANAGER_USER),
        (INTERNAL_USER, INTERNAL_USER),
    )

    user_type = models.CharField(
        max_length=15, choices=USER_TYPE_CHOICES, default=INTERNAL_USER
    )

    def __str__(self):
        return f"{self.username or self.telegram_id}"


class Group(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    telegram_chat_link = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def join_group_uri(self):
        import bot.commands

        return f"{settings.TELEGRAM_BASE_URL}/{settings.TELEGRAM_BOT_USERNAME}?{bot.commands.START_COMMAND}={bot.commands.JOIN_GROUP_COMMAND}-{self.id}"


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.group}"
