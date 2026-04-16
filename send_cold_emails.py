#!/usr/bin/env python3
"""
Send 10 cold emails to new leads via Gmail API
"""

import os
import base64
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import credentials as oauth2_credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import webbrowser
import time

# Email data (extracted from cold_emails_13_leads.txt)
EMAILS_TO_SEND = [
    {
        "recipient": "info@fysiocapelle.nl",
        "company": "Fysiotherapie Capelle",
        "subject": "Korte vraag van een lokale scholier — Fysiotherapie Capelle",
        "body": """Hoi,

Ik ben Brent, 16 jaar, en bouw AI-tools voor kleine bedrijven. Ik zag dat jullie zich richten op behandelingen met aandacht voor individuen — dat soort personalisatie helpt echt met klantenbinding.

Ik heb recent een SOAP-verslagen digitalisatietool gebouwd voor een fysiotherapiebedrijf (vergelijkbaar met jullie werkwijze). Dat scheelde hen echt veel administratiewerk.

Zou je even willen reageren of er zoiets voor jullie interessant zou zijn? Geen verplichting, gewoon informeel overleggen.

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "info@aafje.nl",
        "company": "Aafje",
        "subject": "Korte vraag van een lokale scholier — Aafje",
        "body": """Hoi,

Ik ben Brent, 16 jaar, en ik maak AI-tools voor lokale bedrijven. Ik zag dat jullie zorgverlening met echte menselijke aandacht bieden — dat is precies waar automation bij kan helpen, zodat jullie meer tijd voor cliënten hebben.

Ik bouw tools die repetitieve administratie overnemen. Zou je interesse hebben in een kort gesprek over wat mogelijk is?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "bestuur@ambachtzorg.nl",
        "company": "Ambachtzorg",
        "subject": "Korte vraag van een lokale scholier — Ambachtzorg",
        "body": """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor zorg- en servicebedrijven. Jullie focus op vakmanschap en kwaliteit in zorg spreekt me aan. Ik heb een tool gebouwd die SOAP-verslagen automatiseert — scheelt zorgverleners flink tijd.

Zou je open staan voor een kort gesprek over wat ik zou kunnen doen voor Ambachtzorg?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "info@zusterjansen.nl",
        "company": "Zuster Jansen",
        "subject": "Korte vraag van een lokale scholier — Zuster Jansen",
        "body": """Hoi,

Ik ben Brent, 16, en werk aan AI-tools voor zorgbedrijven. Jullie thema "continuïteit van zorg" vraagt om goed georganiseerde processen — daar kan ik mee helpen via automatisatie.

Interessant voor een kort gesprek?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "info@dagoexpress.nl",
        "company": "DAGO Express",
        "subject": "Korte vraag van een lokale scholier — DAGO Express",
        "body": """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor transportbedrijven. Ik zag dat DAGO Express veel stops per dag doet — perfect voor routeoptimalisatie en administratieautomatie.

Ik heb al routeoptimalisatie-tools gebouwd voor transportbedrijven. Zou je interesse hebben in iets soortgelijks voor DAGO?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "contact_form_runner",
        "company": "Runner Koeriersdienst",
        "channel": "contact_form",
        "subject": "Korte vraag van een lokale scholier — Runner",
        "body": """Hoi Runner-team,

Ik ben Brent, 16, en maak AI-tools voor koeriersdiensten. Jullie snelle bezorgingen vragen om slimme planning — daar specialiseer ik me in.

Zou je willen praten over optimalisatiemogelijkheden?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "info@verkaiklogistiek.nl",
        "company": "Verkaik Sneltransport",
        "subject": "Korte vraag van een lokale scholier — Verkaik",
        "body": """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor transportbedrijven. Sneltransport = veel routes, veel stops — perfect voor routeoptimalisatie en planning-automation.

Zou je interesse hebben in een kort gesprek?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "info@transportbedrijfbarendacht.nl",
        "company": "Transportbedrijf Barendrecht",
        "subject": "Korte vraag van een lokale scholier — Transportbedrijf Barendrecht",
        "body": """Hoi,

Ik ben Brent, 16, en maak AI-tools voor transport- en logistiekbedrijven. Routeoptimalisatie en planning-automation zijn mijn specialiteit — scheelt jouw bedrijf flink tijd en kosten.

Interesse in een kort overileg?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "esther@smaakvandewaard.nl",
        "company": "Smaak van de Waard",
        "subject": "Korte vraag van een lokale scholier — Smaak van de Waard",
        "body": """Hoi Esther,

Ik ben Brent, 16, en bouw AI-tools voor eetgelegenheden en maaltijdbezorgers. Smaak van de Waard doet veel bezorgingen — perfect voor routeoptimalisatie en orderadministratie.

Zou je willen praten over hoe ik je kan helpen?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    },
    {
        "recipient": "contact_form_onemotion",
        "company": "OneMotion",
        "channel": "contact_form",
        "subject": "Korte vraag van een lokale scholier — OneMotion",
        "body": """Hoi OneMotion-team,

Ik ben Brent, 16, en bouw AI-tools voor bedrijven die mobiel werken of veel stops maken. Zou interessant kunnen zijn voor jullie operaties.

Zou je willen reageren op deze vraag?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""
    }
]

SENDER_EMAIL = "brentjansen.ai.building@gmail.com"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]
TOKEN_PATH = os.path.expanduser("~/.claude/gmail-mcp/tokens/token.json")
CREDENTIALS_PATH = os.path.expanduser("~/.claude/gmail-mcp/credentials.json")


def authenticate_gmail():
    """Authenticate with Gmail API"""
    creds = None

    # Check if we have saved credentials
    if os.path.exists(TOKEN_PATH):
        try:
            creds = oauth2_credentials.Credentials.from_authorized_user_file(
                TOKEN_PATH, SCOPES
            )
        except Exception as e:
            print(f"Error loading saved token: {e}")

    # If not, try to get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(CREDENTIALS_PATH):
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        else:
            print("ERROR: credentials.json not found!")
            print(f"Expected at: {CREDENTIALS_PATH}")
            return None

        # Save credentials for next time
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds


def send_email(service, to, subject, body):
    """Send an email via Gmail API"""
    try:
        message = {
            'raw': base64.urlsafe_b64encode(
                f"From: {SENDER_EMAIL}\nTo: {to}\nSubject: {subject}\n\n{body}".encode()
            ).decode()
        }

        sent_message = service.users().messages().send(userId='me', body=message).execute()
        return {
            'success': True,
            'message_id': sent_message['id'],
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def log_result(results, email_info, send_result):
    """Log the result of sending an email"""
    result_entry = {
        'company': email_info.get('company'),
        'recipient': email_info.get('recipient'),
        'channel': email_info.get('channel', 'email'),
        'subject': email_info.get('subject'),
        'status': 'Verstuurd' if send_result['success'] else 'Error',
        'timestamp': send_result['timestamp'],
        'message_id': send_result.get('message_id'),
        'error': send_result.get('error')
    }
    results.append(result_entry)

    # Print status
    status_icon = '✓' if send_result['success'] else '⚠️'
    print(f"{status_icon} {email_info.get('company'):35} | {email_info.get('recipient'):40} | {send_result['timestamp']}")
    if not send_result['success']:
        print(f"   Error: {send_result.get('error')}")


def main():
    print("=" * 80)
    print("COLD EMAILS SENDER — BRENT'S CEO SYSTEM")
    print("=" * 80)
    print(f"Authenticating with Gmail account: {SENDER_EMAIL}")
    print()

    # Authenticate
    creds = authenticate_gmail()
    if not creds:
        print("ERROR: Authentication failed!")
        return

    service = build('gmail', 'v1', credentials=creds)
    print(f"✓ Successfully authenticated\n")

    # Send emails
    results = []
    direct_emails = 0
    contact_form_emails = 0
    errors = 0

    print("SENDING EMAILS:")
    print("-" * 80)

    for email_info in EMAILS_TO_SEND:
        # Skip contact form emails (manual action needed)
        if email_info.get('channel') == 'contact_form':
            print(f"⏭️  {email_info.get('company'):35} | Website contact form (manual)")
            log_result(results, email_info, {
                'success': False,
                'error': 'Manual contact form - use website',
                'timestamp': datetime.now().isoformat()
            })
            contact_form_emails += 1
            continue

        # Send direct email
        send_result = send_email(
            service,
            email_info['recipient'],
            email_info['subject'],
            email_info['body']
        )

        log_result(results, email_info, send_result)

        if send_result['success']:
            direct_emails += 1
        else:
            errors += 1

        # Small delay between sends
        time.sleep(0.5)

    print("-" * 80)
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY — 7 april 2026")
    print("=" * 80)
    print(f"✓ Direct emails verzonden: {direct_emails}")
    print(f"⏭️  Via contact forms: {contact_form_emails}")
    print(f"⚠️  Errors: {errors}")
    print()

    # Save results to file
    output_file = r"C:\Users\Naam Leerling\ai building brent jansen\cold_emails_sent_log.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'sender': SENDER_EMAIL,
            'direct_emails': direct_emails,
            'contact_form_emails': contact_form_emails,
            'errors': errors,
            'results': results
        }, f, indent=2, ensure_ascii=False)

    print(f"Log saved to: {output_file}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
