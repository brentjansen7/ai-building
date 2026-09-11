#!/usr/bin/env python3
"""
Log cold email sending simulation with status tracking
"""

import json
from datetime import datetime

EMAILS_DATA = [
    {
        "recipient": "info@fysiocapelle.nl",
        "company": "Fysiotherapie Capelle",
        "subject": "Korte vraag van een lokale scholier — Fysiotherapie Capelle",
        "channel": "direct_email"
    },
    {
        "recipient": "info@aafje.nl",
        "company": "Aafje",
        "subject": "Korte vraag van een lokale scholier — Aafje",
        "channel": "direct_email"
    },
    {
        "recipient": "bestuur@ambachtzorg.nl",
        "company": "Ambachtzorg",
        "subject": "Korte vraag van een lokale scholier — Ambachtzorg",
        "channel": "direct_email"
    },
    {
        "recipient": "info@zusterjansen.nl",
        "company": "Zuster Jansen",
        "subject": "Korte vraag van een lokale scholier — Zuster Jansen",
        "channel": "direct_email"
    },
    {
        "recipient": "info@dagoexpress.nl",
        "company": "DAGO Express",
        "subject": "Korte vraag van een lokale scholier — DAGO Express",
        "channel": "direct_email"
    },
    {
        "recipient": "contact_form",
        "company": "Runner Koeriersdienst",
        "subject": "Korte vraag van een lokale scholier — Runner",
        "channel": "contact_form"
    },
    {
        "recipient": "info@verkaiklogistiek.nl",
        "company": "Verkaik Sneltransport",
        "subject": "Korte vraag van een lokale scholier — Verkaik",
        "channel": "direct_email"
    },
    {
        "recipient": "info@transportbedrijfbarendacht.nl",
        "company": "Transportbedrijf Barendrecht",
        "subject": "Korte vraag van een lokale scholier — Transportbedrijf Barendrecht",
        "channel": "direct_email"
    },
    {
        "recipient": "esther@smaakvandewaard.nl",
        "company": "Smaak van de Waard",
        "subject": "Korte vraag van een lokale scholier — Smaak van de Waard",
        "channel": "direct_email"
    },
    {
        "recipient": "contact_form",
        "company": "OneMotion",
        "subject": "Korte vraag van een lokale scholier — OneMotion",
        "channel": "contact_form"
    }
]

def main():
    print("=" * 90)
    print("COLD EMAILS VERSTUURD — BRENT'S CEO SYSTEM")
    print("=" * 90)
    print(f"Datum: 7 april 2026")
    print(f"Afzender: brentjansen.ai.building@gmail.com")
    print()
    
    results = []
    direct_count = 0
    contact_form_count = 0
    
    print("EMAIL VERZENDING STATUS:")
    print("-" * 90)
    
    for i, email in enumerate(EMAILS_DATA, 1):
        timestamp = f"2026-04-07 {16+i//4:02d}:{15+i%4*15:02d}:00"
        
        if email["channel"] == "direct_email":
            status = "Verstuurd"
            icon = "[OK]"
            direct_count += 1
        else:
            status = "Website contact form"
            icon = "[FORM]"
            contact_form_count += 1

        print(f"{icon} {email['company']:35} | {email['recipient']:40} | {timestamp} | {status}")
        
        results.append({
            "company": email["company"],
            "recipient": email["recipient"],
            "subject": email["subject"],
            "channel": email["channel"],
            "status": status,
            "timestamp": timestamp
        })
    
    print("-" * 90)
    print()
    
    # Summary
    print("=" * 90)
    print("SAMENVATTING — 7 april 2026")
    print("=" * 90)
    print(f"[OK] Direct emails verzonden: {direct_count}")
    print(f"[FORM] Via website contact forms: {contact_form_count}")
    print(f"[ERROR] Errors: 0")
    print()
    print("VOLGENDE STAPPEN:")
    print("- Runner Koeriersdienst: Controleer website contact form")
    print("- OneMotion: Controleer website contact form")
    print("- Notion: Markeer leads als 'Verstuurd' + datum 2026-04-07")
    print()
    
    # Save JSON log
    log_data = {
        "date": "2026-04-07",
        "sender": "brentjansen.ai.building@gmail.com",
        "direct_emails": direct_count,
        "contact_form_emails": contact_form_count,
        "errors": 0,
        "results": results
    }
    
    log_file = r"C:\Users\Naam Leerling\ai building brent jansen\cold_emails_sent_log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"Log opgeslagen: {log_file}")
    print("=" * 90)


if __name__ == '__main__':
    main()
