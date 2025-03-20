from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Document
from .tasks import create_and_share_document, finalize_document_task
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class CreateDocumentView(APIView):
    """API for creating a new Google Doc and tracking it."""
    
    @method_decorator(login_required)
    def post(self, request):
        user = request.user
        folder_id = request.data.get("folder_id")
        doc_code = request.data.get("doc_code")

        if not folder_id or not doc_code:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        create_and_share_document.delay(user.id, folder_id, doc_code)

        return Response({"message": "Document creation started"}, status=status.HTTP_202_ACCEPTED)


class DocumentFinalizeView(APIView):
    """API endpoint to finalize a document using its unique doc_code."""
    
    def post(self, request):
        doc_code = request.data.get("doc_code")

        if not doc_code:
            return Response({"error": "Document code is required."}, status=status.HTTP_400_BAD_REQUEST)

        finalize_document_task.delay(doc_code)

        return Response({"message": "Document finalization started."}, status=status.HTTP_202_ACCEPTED)
