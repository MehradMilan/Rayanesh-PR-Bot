from django.db import models
from django.conf import settings

from user.models import Group


class Gate(models.Model):
    title = models.CharField(max_length=31)
    room_no = models.IntegerField(null=True, blank=True)
    scannable = models.BooleanField(default=True)
    is_open = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    gate_keepers_group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    open_from = models.TimeField(null=True, blank=True)
    open_to = models.TimeField(null=True, blank=True)
    close_from = models.TimeField(null=True, blank=True)
    close_to = models.TimeField(null=True, blank=True)


class Notification(models.Model):
    message_id = models.CharField(max_length=255)
    source_channel_id = models.CharField(
        max_length=255, default=settings.HEALTHCHECK_CHAT_ID
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    propagated_at = models.DateTimeField(null=True)
    is_general = models.BooleanField(default=False)
