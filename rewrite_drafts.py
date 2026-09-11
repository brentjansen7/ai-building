#!/usr/bin/env python3
"""
Herschrijf alle Gmail drafts naar correct format (template cold_email.md)
"""

import os
import json
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import credentials as oauth2_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticate with Gmail API"""
    creds = None

    # Try existing token
    if os.path.exists('token.json'):
        creds = oauth2_credentials.Credentials.from_authorized_user_file('token.json', SCOPES)

    # If not, create new
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_doelgroepen():
    """Load doelgroepen.json"""
    with open('ceo/config/doelgroepen.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_draft_messages(service):
    """Get all draft messages"""
    try:
        results = service.users().drafts().list(userId='me').execute()
        return results.get('drafts', [])
    except Exception as e:
        print(f"Error fetching drafts: {e}")
        return []

def get_message_content(service, draft_id):
    """Get full message content from draft"""
    try:
        draft = service.users().drafts().get(userId='me', id=draft_id).execute()
        msg = draft['message']

        headers = {}
        for h in msg.get('payload', {}).get('headers', []):
            headers[h['name']] = h['value']

        # Get body
        body = ""
        if 'parts' in msg.get('payload', {}):
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            data = msg.get('payload', {}).get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        return {
            'id': draft_id,
            'to': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'body': body
        }
    except Exception as e:
        print(f"Error getting message {draft_id}: {e}")
        return None

def extract_bedrijfsnaam(subject, body):
    """Extract company name from subject or body"""
    # Subject format: "Korte vraag van een lokale scholier — [BEDRIJFSNAAM]"
    match = re.search(r'— (.+)$', subject)
    if match:
        return match.group(1).strip()
    return None

def delete_draft(service, draft_id):
    """Delete a draft"""
    try:
        service.users().drafts().delete(userId='me', id=draft_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting draft {draft_id}: {e}")
        return False

def create_draft(service, to, subject, body):
    """Create a new draft"""
    try:
        message = {
            'raw': base64.urlsafe_b64encode(
                f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}".encode('utf-8')
            ).decode('utf-8')
        }

        draft = service.users().drafts().create(userId='me', body={'message': message}).execute()
        return draft['id']
    except Exception as e:
        print(f"Error creating draft: {e}")
        return None

# Main execution
if __name__ == '__main__':
    print("🔄 Herschrijven Gmail drafts naar correct format...")

    service = get_gmail_service()
    doelgroepen = get_doelgroepen()

    drafts = get_draft_messages(service)
    print(f"Found {len(drafts)} drafts")

    for draft_info in drafts:
        draft_id = draft_info['id']
        msg = get_message_content(service, draft_id)

        if not msg:
            continue

        bedrijf = extract_bedrijfsnaam(msg['subject'], msg['body'])
        print(f"\nDraft: {bedrijf} → {msg['to']}")
        print(f"   Current length: {len(msg['body'].split())} words")

        # TODO: Here you would rewrite the body according to the template
        # For now, just show what needs to be done
        print(f"   Status: Needs rewrite")

    print("\nScan complete. Drafts need manual review or script enhancement.")
