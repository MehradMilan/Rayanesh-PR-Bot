from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from django.conf import settings

def get_drive_service():
    """Creates and returns an authenticated Google Drive API service."""
    creds_path = settings.GOOGLE_CREDS_PATH
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

def create_google_doc(folder_id, doc_name):
    """Creates a new Google Doc inside the specified folder."""
    drive_service = get_drive_service()

    template_doc_id = settings.GOOGLE_TEMPLATE_DOC_ID
    copy_body = {'name': doc_name, 'parents': [folder_id]}
    copy = drive_service.files().copy(fileId=template_doc_id, body=copy_body).execute()
    
    return copy['id']

def share_document(doc_id, user_email):
    """Grants edit access to a Google Doc for a given user."""
    drive_service = get_drive_service()
    permission_body = {'type': 'user', 'role': 'writer', 'emailAddress': user_email}
    drive_service.permissions().create(fileId=doc_id, body=permission_body).execute()
    
def finalize_google_doc(doc_id, doc_name):
    """Finalize the Google Doc by renaming it to indicate completion."""
    drive_service = get_drive_service()

    # Append '-FINAL' to the document name
    final_name = f"{doc_name}-FINAL"
    drive_service.files().update(
        fileId=doc_id,
        body={'name': final_name}
    ).execute()

    return final_name