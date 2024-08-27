from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import get_config
from init import get_application

def get_drive_service(api='drive', version='v3'):
    creds_path = get_config()['GOOGLE.API']['CREDS_PATH']
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build(api, version, credentials=credentials)

async def create_document_and_share_with_user(update, user_email, selected_folder_id, doc_code):
    drive_service = get_drive_service()
    template_doc_id = get_config()['GOOGLE.DRIVE']['TEMPLATE_DOC_ID']
    copy_body = {'name': f"YourTitleHere-{doc_code}", 'parents': [selected_folder_id]}
    copy = drive_service.files().copy(fileId=template_doc_id, body=copy_body).execute()
    doc_id = copy['id']

    permission_body = {'type': 'user', 'role': 'writer', 'emailAddress': user_email}
    drive_service.permissions().create(fileId=doc_id, body=permission_body).execute()

    return doc_id

def get_folder_name(folder_id):
    drive_service = get_drive_service()
    folder = drive_service.files().get(fileId=folder_id, fields="name").execute()
    return folder['name']

async def create_document_with_text(doc_title, selected_folder_id, text):
    drive_service = get_drive_service()
    template_doc_id = get_config()['GOOGLE.DRIVE']['ANON_TEMPLATE_DOC_ID']

    copy_body = {'name': doc_title, 'parents': [selected_folder_id]}
    copy = drive_service.files().copy(fileId=template_doc_id, body=copy_body).execute()
    doc_id = copy['id']

    await edit_document_text(doc_id, text)
    return doc_id

async def get_document_text_part(doc_id, marker):
    docs_service = get_drive_service('docs', 'v1')

    document = docs_service.documents().get(documentId=doc_id).execute()
    content = document.get('body').get('content', [])

    marker_index = None

    for index, element in enumerate(content):
        if 'paragraph' in element:
            for para_element in element.get('paragraph').get('elements', []):
                text_run = para_element.get('textRun')
                if text_run:
                    text = text_run.get('content')
                    if marker in text:
                        marker_index = element.get('endIndex')
                        break
                        
    doc_end_index = content[-1].get('endIndex') - 1

    return marker_index, doc_end_index


async def edit_document_text(doc_id, new_text):
    docs_service = get_drive_service('docs', 'v1')
    text_marker = get_config()['GOOGLE.DOC']['TEXT_MARKER']

    marker_index, doc_end_index = await get_document_text_part(doc_id, text_marker)

    if marker_index is None:
        return

    requests = [
        {
            'deleteContentRange': {
                'range': {
                    'startIndex': marker_index,
                    'endIndex': doc_end_index - 1
                }
            }
        },
        {
            'insertText': {
                'location': {
                    'index': marker_index
                },
                'text': new_text,
            }
        }
    ]

    try:
        result = docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    except Exception as e:
        pass

async def finalize_document(doc_id, doc_name):
    drive_service = get_drive_service()
    final_name = str(doc_name) + '-FINAL'
    drive_service.files().update(fileId=doc_id, body={'name': final_name}).execute()
    return final_name

async def notify_group(doc_name, doc_id):
    group_id = get_config()['TELEGRAM.BOT']['GROUP_ID']
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    bot = get_application().bot
    await bot.send_message(chat_id=group_id, text=f"""
🟢 یک سند نهایی شد.

🔹 نام سند: {doc_name}

🔸 لینک سند:
🔗 {doc_url}
""")
    
async def get_document_name_by_id(doc_id):
    drive_service = get_drive_service()
    doc = drive_service.files().get(fileId=doc_id, fields="name").execute()
    return doc['name']