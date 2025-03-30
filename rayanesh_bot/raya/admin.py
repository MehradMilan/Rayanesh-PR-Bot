from django.contrib import admin
from .models import Gate


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
