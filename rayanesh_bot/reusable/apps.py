from django.apps import AppConfig


class ReusableConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reusable"
