from celery import shared_task
from .services import create_google_doc, share_document, finalize_google_doc
from .models import Document
from user.models import TelegramUser

@shared_task
def create_and_share_document(user_id, folder_id, doc_code):
    """Celery task to create a Google Doc and share it with the user."""
    user = TelegramUser.objects.get(id=user_id)
    doc_name = f"Document-{doc_code}"

    doc_id = create_google_doc(folder_id, doc_name)
    
    share_document(doc_id, user.email)

    Document.objects.create(
        user=user, google_doc_id=doc_id, folder_id=folder_id, doc_code=doc_code
    )

    return doc_id

@shared_task
def finalize_document_task(doc_code):
    """Finalize a document by marking it as finalized both in Google Docs and the database."""
    document = Document.objects.get(doc_code=doc_code)
    
    finalize_google_doc(document.google_doc_id, f"Document-{doc_code}")
    
    document.finalize()

    return f"Document {doc_code} finalized."