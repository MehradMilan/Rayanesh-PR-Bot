from django.urls import path
from .views import CreateDocumentView, DocumentFinalizeView

urlpatterns = [
    path("create/", CreateDocumentView.as_view(), name="create-document"),
    path("finalize/", DocumentFinalizeView.as_view(), name="finalize-document"),
]