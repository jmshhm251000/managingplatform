import os
import re
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from llama_index.core import Document, VectorStoreIndex


def get_document_text(document_id, scopes) -> Optional[List[Document]]:
    """
    Retrieves Q&A pairs from a Google Doc via the Google Docs API and returns them
    as a list of Document objects, each containing one Q&A pair.

    Returns:
        Optional[List[Document]]: A list of Document objects with Q&A text,
                                  or None if DOCUMENT_ID is not set or retrieval fails.
    """

    if not document_id:
        print("❌ Error: DOCUMENT_ID not set.")
        return None

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('docs', 'v1', credentials=creds)
    document_data = service.documents().get(documentId=document_id).execute()
    #print(f"📄 Document title: {document_data.get('title')}")

    full_text = ''
    for element in document_data.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for run in element['paragraph'].get('elements', []):
                if 'textRun' in run:
                    content = run['textRun'].get('content', '')
                    full_text += content

    # Use regex to extract Q&A pairs robustly
    documents = []
    qa_matches = re.findall(r"Q:(.*?)A:(.*?)(?=(?:Q:|$))", full_text, re.DOTALL)
    for question, answer in qa_matches:
        question = question.strip()
        answer = answer.strip()
        if question and answer:
            text = f"Q: {question}\nA: {answer}"
            documents.append(Document(text=text))
    
    if not documents:
        print("⚠️ No Q&A pairs found in the document.")
        return None

    return documents