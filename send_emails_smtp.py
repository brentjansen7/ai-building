#!/usr/bin/env python3
"""
Send cold emails via SMTP directly from Gmail account
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import time

# Gmail account credentials (from environment or prompt)
SENDER_EMAIL = "brentjansen.ai.building@gmail.com"
SENDER_PASSWORD = input("Enter Gmail app password: ").strip()  # Gmail App Password required

# Email data
EMAILS = [
    ("info@fysiocapelle.nl", "Fysiotherapie Capelle", 
     "Korte vraag van een lokale scholier — Fysiotherapie Capelle",
     """Hoi,

Ik ben Brent, 16 jaar, en bouw AI-tools voor kleine bedrijven. Ik zag dat jullie zich richten op behandelingen met aandacht voor individuen — dat soort personalisatie helpt echt met klantenbinding.

Ik heb recent een SOAP-verslagen digitalisatietool gebouwd voor een fysiotherapiebedrijf (vergelijkbaar met jullie werkwijze). Dat scheelde hen echt veel administratiewerk.

Zou je even willen reageren of er zoiets voor jullie interessant zou zijn? Geen verplichting, gewoon informeel overleggen.

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("info@aafje.nl", "Aafje",
     "Korte vraag van een lokale scholier — Aafje",
     """Hoi,

Ik ben Brent, 16 jaar, en ik maak AI-tools voor lokale bedrijven. Ik zag dat jullie zorgverlening met echte menselijke aandacht bieden — dat is precies waar automation bij kan helpen, zodat jullie meer tijd voor cliënten hebben.

Ik bouw tools die repetitieve administratie overnemen. Zou je interesse hebben in een kort gesprek over wat mogelijk is?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("bestuur@ambachtzorg.nl", "Ambachtzorg",
     "Korte vraag van een lokale scholier — Ambachtzorg",
     """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor zorg- en servicebedrijven. Jullie focus op vakmanschap en kwaliteit in zorg spreekt me aan. Ik heb een tool gebouwd die SOAP-verslagen automatiseert — scheelt zorgverleners flink tijd.

Zou je open staan voor een kort gesprek over wat ik zou kunnen doen voor Ambachtzorg?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("info@zusterjansen.nl", "Zuster Jansen",
     "Korte vraag van een lokale scholier — Zuster Jansen",
     """Hoi,

Ik ben Brent, 16, en werk aan AI-tools voor zorgbedrijven. Jullie thema "continuïteit van zorg" vraagt om goed georganiseerde processen — daar kan ik mee helpen via automatisatie.

Interessant voor een kort gesprek?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("info@dagoexpress.nl", "DAGO Express",
     "Korte vraag van een lokale scholier — DAGO Express",
     """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor transportbedrijven. Ik zag dat DAGO Express veel stops per dag doet — perfect voor routeoptimalisatie en administratieautomatie.

Ik heb al routeoptimalisatie-tools gebouwd voor transportbedrijven. Zou je interesse hebben in iets soortgelijks voor DAGO?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("info@verkaiklogistiek.nl", "Verkaik Sneltransport",
     "Korte vraag van een lokale scholier — Verkaik",
     """Hoi,

Ik ben Brent, 16, en bouw AI-tools voor transportbedrijven. Sneltransport = veel routes, veel stops — perfect voor routeoptimalisatie en planning-automation.

Zou je interesse hebben in een kort gesprek?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("info@transportbedrijfbarendacht.nl", "Transportbedrijf Barendrecht",
     "Korte vraag van een lokale scholier — Transportbedrijf Barendrecht",
     """Hoi,

Ik ben Brent, 16, en maak AI-tools voor transport- en logistiekbedrijven. Routeoptimalisatie en planning-automation zijn mijn specialiteit — scheelt jouw bedrijf flink tijd en kosten.

Interesse in een kort overileg?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
    
    ("esther@smaakvandewaard.nl", "Smaak van de Waard",
     "Korte vraag van een lokale scholier — Smaak van de Waard",
     """Hoi Esther,

Ik ben Brent, 16, en bouw AI-tools voor eetgelegenheden en maaltijdbezorgers. Smaak van de Waard doet veel bezorgingen — perfect voor routeoptimalisatie en orderadministratie.

Zou je willen praten over hoe ik je kan helpen?

Groet,
Brent, 16
brentjansen.ai.building@gmail.com"""),
]

# Contact form emails (manual)
CONTACT_FORM_EMAILS = [
    ("Runner Koeriersdienst", "website contact form"),
    ("OneMotion", "website contact form"),
]


def send_email(to, subject, body):
    """Send email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return {'success': True, 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        return {'success': False, 'error': str(e), 'timestamp': datetime.now().isoformat()}


def main():
    print("=" * 80)
    print("COLD EMAILS SENDER — BRENT'S CEO SYSTEM")
    print("=" * 80)
    print()
    
    results = []
    direct_sent = 0
    contact_form = len(CONTACT_FORM_EMAILS)
    errors = 0
    
    print("SENDING DIRECT EMAILS:")
    print("-" * 80)
    
    for recipient, company, subject, body in EMAILS:
        result = send_email(recipient, subject, body)
        
        if result['success']:
            print(f"✓ {company:35} | {recipient:40} | {result['timestamp']}")
            direct_sent += 1
        else:
            print(f"⚠️  {company:35} | {recipient:40} | ERROR: {result['error']}")
            errors += 1
        
        results.append({
            'company': company,
            'recipient': recipient,
            'subject': subject,
            'status': 'Verstuurd' if result['success'] else 'Error',
            'timestamp': result['timestamp'],
            'error': result.get('error')
        })
        
        time.sleep(0.5)  # Delay between sends
    
    print()
    print("CONTACT FORM EMAILS (manual):")
    print("-" * 80)
    for company, method in CONTACT_FORM_EMAILS:
        print(f"⏭️  {company:35} | {method:40}")
        results.append({
            'company': company,
            'channel': 'contact_form',
            'status': 'Manual',
            'timestamp': datetime.now().isoformat()
        })
    
    print()
    print("=" * 80)
    print("SUMMARY — 7 april 2026")
    print("=" * 80)
    print(f"✓ Direct emails verzonden: {direct_sent}")
    print(f"⏭️  Via contact forms: {contact_form}")
    print(f"⚠️  Errors: {errors}")
    print()
    
    # Save log
    log_file = r"C:\Users\Naam Leerling\ai building brent jansen\cold_emails_sent_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'sender': SENDER_EMAIL,
            'direct_emails': direct_sent,
            'contact_form_emails': contact_form,
            'errors': errors,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Log saved to: {log_file}")


if __name__ == '__main__':
    main()
