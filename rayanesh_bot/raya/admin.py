from django.contrib import admin

from .models import Gate
from .models import Notification


@admin.register(Gate)
class GateAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "room_no",
        "is_open",
        "is_active",
        "scannable",
        "open_from",
        "open_to",
        "close_from",
        "close_to",
    )
    list_filter = ("is_active", "is_open", "gate_keepers_group")
    search_fields = ("title", "room_no")
    ordering = ("title",)
    fieldsets = (
        (None, {"fields": ("title", "room_no", "gate_keepers_group")}),
        ("Status", {"fields": ("is_open", "is_active")}),
        (
            "Time Ranges",
            {"fields": (("open_from", "open_to"), ("close_from", "close_to"))},
        ),
    )


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "message_id",
        "source_channel_id",
        "group",
        "created_at",
        "propagated_at",
        "is_general",
    )
    list_filter = ("is_general", "group", "created_at")
    search_fields = ("message_id", "source_channel_id", "group__name")
    list_editable = ("is_general",)
    ordering = ("-created_at",)
    fields = (
        "message_id",
        "source_channel_id",
        "group",
        "is_general",
        "created_at",
        "propagated_at",
    )
    actions = ["mark_as_sent"]


admin.site.register(Notification, NotificationAdmin)
