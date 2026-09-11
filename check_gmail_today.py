#!/usr/bin/env python3
"""
Check Gmail inbox and SENT folder for today (2026-04-22)
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2 import credentials as oauth2_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Authenticate with Gmail API"""
    creds = None

    if os.path.exists('token.json'):
        creds = oauth2_credentials.Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def decode_body(data):
    """Decode base64 email body"""
    try:
        return urlsafe_b64decode(data).decode('utf-8')
    except:
        return "[Could not decode]"

def check_emails():
    service = get_gmail_service()

    # Check inbox for today
    query = 'is:inbox after:2026-04-21'
    results = service.users().messages().list(userId='me', q=query).execute()
    inbox_messages = results.get('messages', [])

    # Check SENT for today
    query_sent = 'label:SENT after:2026-04-21'
    results_sent = service.users().messages().list(userId='me', q=query_sent).execute()
    sent_messages = results_sent.get('messages', [])

    print("=" * 60)
    print("INBOX (today)")
    print("=" * 60)

    if not inbox_messages:
        print("No emails in inbox today.\n")
    else:
        for msg in inbox_messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            print(f"From: {headers.get('From', 'Unknown')}")
            print(f"Subject: {headers.get('Subject', 'No subject')}")
            print(f"Date: {headers.get('Date', 'Unknown')}")
            print(f"---")

    print("\n" + "=" * 60)
    print("SENT (today)")
    print("=" * 60)

    if not sent_messages:
        print("No emails sent today.\n")
    else:
        for msg in sent_messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            print(f"To: {headers.get('To', 'Unknown')}")
            print(f"Subject: {headers.get('Subject', 'No subject')}")
            print(f"Date: {headers.get('Date', 'Unknown')}")
            print(f"---")

if __name__ == '__main__':
    check_emails()
