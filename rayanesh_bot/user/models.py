from django.db import models
from django.conf import settings
from django.utils import timezone


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
    chat_id = models.CharField(max_length=63, null=True)

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


class Task(models.Model):
    title = models.CharField(max_length=255, blank=True)
    assignee_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    owner_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="owned_tasks"
    )
    scope_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    deadline = models.DateTimeField(null=True, blank=True)

    LOW_PRIORITY = "low"
    MEDIUM_PRIORITY = "medium"
    HIGH_PRIORITY = "high"
    VERY_HIGH_PRIORITY = "very_high"
    PRIORITY_LEVEL_CHOICES = (
        (LOW_PRIORITY, LOW_PRIORITY),
        (MEDIUM_PRIORITY, MEDIUM_PRIORITY),
        (HIGH_PRIORITY, HIGH_PRIORITY),
        (VERY_HIGH_PRIORITY, VERY_HIGH_PRIORITY),
    )
    priority_level = models.CharField(
        max_length=10, choices=PRIORITY_LEVEL_CHOICES, default=LOW_PRIORITY
    )

    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    done_at = models.DateTimeField(null=True, blank=True)

    INITIAL_STATE = "initial"
    TAKEN_STATE = "taken"
    DONE_STATE = "done"
    STATE_CHOICES = (
        (INITIAL_STATE, INITIAL_STATE),
        (TAKEN_STATE, TAKEN_STATE),
        (DONE_STATE, DONE_STATE),
    )
    state = models.CharField(
        max_length=10, choices=STATE_CHOICES, default=INITIAL_STATE
    )

    class Meta:
        unique_together = ("scope_group", "title", "created_at")
        indexes = [
            models.Index(fields=["scope_group"]),
            models.Index(fields=["state"]),
            models.Index(fields=["assignee_user"]),
        ]

    def save(self, *args, **kwargs):
        if self.state == self.TAKEN_STATE and not self.assigned_at:
            if not self.assignee_user:
                raise ValueError("Assigned user must be provided when a task is taken.")
            self.assigned_at = timezone.now()

        elif self.state == self.DONE_STATE and not self.done_at:
            if not self.assignee_user:
                raise ValueError(
                    "Assigned user should not be provided for a task that is done."
                )
            self.done_at = timezone.now()

        super().save(*args, **kwargs)
