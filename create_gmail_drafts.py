#!/usr/bin/env python3
"""
Create Gmail drafts from herschreven emails list
"""

import os
import base64
import json
import re
from google.auth.transport.requests import Request
from google.oauth2 import credentials as oauth2_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticate with Gmail API"""
    creds = None

    if os.path.exists('token.json'):
        creds = oauth2_credentials.Credentials.from_authorized_user_file('token.json', SCOPES)

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

def parse_drafts_file(filepath):
    """Parse drafts_herschreven.txt and extract email data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    emails = []

    # Split by numbered sections
    sections = re.split(r'^---\n', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip header
        lines = section.strip().split('\n')

        # Extract metadata
        to = None
        subject = None
        body_start = 0

        for i, line in enumerate(lines):
            if line.startswith('To:'):
                to = line.replace('To:', '').strip()
            elif line.startswith('Subject:'):
                subject = line.replace('Subject:', '').strip()
                body_start = i + 1
                break

        if to and subject and body_start < len(lines):
            body = '\n'.join(lines[body_start:]).strip()

            # Clean up body
            body = body.replace('\n\n---', '').strip()

            emails.append({
                'to': to,
                'subject': subject,
                'body': body
            })

    return emails

def create_draft(service, to, subject, body):
    """Create a Gmail draft"""
    try:
        # Format message
        message_text = f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}"

        # Create message object
        message = {
            'raw': base64.urlsafe_b64encode(
                message_text.encode('utf-8')
            ).decode('utf-8')
        }

        # Create draft
        draft = service.users().drafts().create(userId='me', body={'message': message}).execute()
        return draft['id']
    except Exception as e:
        print(f"Error creating draft for {to}: {e}")
        return None

# Main
if __name__ == '__main__':
    print("Parsing drafts from ceo/drafts_herschreven.txt...")

    emails = parse_drafts_file('ceo/drafts_herschreven.txt')
    print(f"Found {len(emails)} emails to create as drafts\n")

    print("Connecting to Gmail API...")
    service = get_gmail_service()

    created = 0
    for i, email in enumerate(emails, 1):
        print(f"{i}. Creating draft for {email['to']}...")
        draft_id = create_draft(service, email['to'], email['subject'], email['body'])

        if draft_id:
            print(f"   SUCCESS: Draft created (ID: {draft_id[:20]}...)")
            created += 1
        else:
            print(f"   FAILED: Could not create draft")

    print(f"\n✓ {created}/{len(emails)} drafts created successfully!")
