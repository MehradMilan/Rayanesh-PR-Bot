from django.db import models
from user.models import TelegramUser


class Document(models.Model):
    user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE, related_name="documents"
    )

    google_doc_id = models.CharField(max_length=255, unique=True)
    folder_id = models.CharField(max_length=255)
    doc_code = models.CharField(max_length=6, unique=True)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def finalize(self):
        self.is_finalized = True
        self.save()

    def __str__(self):
        return f"Document {self.google_doc_id} by {self.user}"
