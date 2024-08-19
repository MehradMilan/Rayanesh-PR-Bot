from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import get_config

def get_drive_service():
    creds_path = get_config()['GOOGLE.API']['CREDS_PATH']
    scopes = get_config()['GOOGLE.API']['SCOPES'].split(',')
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

async def create_document_and_share_with_user(update, user_email, selected_folder_id):
    drive_service = get_drive_service()
    template_doc_id = get_config()['GOOGLE.DRIVE']['TEMPLATE_DOC_ID']
    copy_body = {'name': 'سند جدید', 'parents': [selected_folder_id]}
    copy = drive_service.files().copy(fileId=template_doc_id, body=copy_body).execute()
    doc_id = copy['id']

    permission_body = {'type': 'user', 'role': 'writer', 'emailAddress': user_email}
    drive_service.permissions().create(fileId=doc_id, body=permission_body).execute()

    return doc_id