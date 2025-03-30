from django.db import models
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
