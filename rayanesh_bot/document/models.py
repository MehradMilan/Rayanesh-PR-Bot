from django.db import models
from user.models import TelegramUser, Group


class Document(models.Model):
    owner_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="documents"
    )

    google_id = models.CharField(max_length=255, unique=True)
    directory_id = models.CharField(max_length=255)
    link = models.CharField(max_length=255, null=True)
    is_directory = models.BooleanField(default=False)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document {self.google_id} by {self.owner_user.name}"


class DocumentUserAccess(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    access_count = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now_add=True)

    EDIT_ACCESS_LEVEL = "edit"
    COMMENT_ACCESS_LEVEL = "comment"
    VIEW_ACCESS_LEVEL = "view"
    ACCESS_LEVEL_CHOICES = (
        (EDIT_ACCESS_LEVEL, EDIT_ACCESS_LEVEL),
        (COMMENT_ACCESS_LEVEL, COMMENT_ACCESS_LEVEL),
        (VIEW_ACCESS_LEVEL, VIEW_ACCESS_LEVEL),
    )
    access_level = models.CharField(
        max_length=10, choices=ACCESS_LEVEL_CHOICES, default=VIEW_ACCESS_LEVEL
    )


class DocumentGroupAccess(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    EDIT_ACCESS_LEVEL = "edit"
    COMMENT_ACCESS_LEVEL = "comment"
    VIEW_ACCESS_LEVEL = "view"
    ACCESS_LEVEL_CHOICES = (
        (EDIT_ACCESS_LEVEL, EDIT_ACCESS_LEVEL),
        (COMMENT_ACCESS_LEVEL, COMMENT_ACCESS_LEVEL),
        (VIEW_ACCESS_LEVEL, VIEW_ACCESS_LEVEL),
    )
    access_level = models.CharField(
        max_length=10, choices=ACCESS_LEVEL_CHOICES, default=VIEW_ACCESS_LEVEL
    )

    class Meta:
        unique_together = ("group", "document")
