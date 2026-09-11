#!/usr/bin/env python3
"""
Proces voor duplicate removal en datum filling:
1. Parse Gmail data voor verzend datums
2. Identify duplicate bedrijven in Notion
3. Generate Notion update instructions
"""

import json
import re
from datetime import datetime
from collections import defaultdict

# Load Gmail data
gmail_file = r"C:\Users\Naam Leerling\.claude\projects\c--Users-Naam-Leerling-ai-building-brent-jansen\0b689657-0961-45bb-86d5-28b0c835873e\tool-results\mcp-claude_ai_Gmail-gmail_search_messages-1774966027726.txt"

with open(gmail_file, 'r', encoding='utf-8') as f:
    content = f.read()

parsed = json.loads(content)
text = parsed[0].get('text', '')
data = json.loads(text)
messages = data.get('messages', [])

# Parse Gmail to recipients
send_dates = {}  # email -> date
for msg in messages:
    to = msg.get('headers', {}).get('To', '').lower().strip()
    date_str = msg.get('headers', {}).get('Date', '')

    if not to or not date_str:
        continue

    # Parse date (e.g., "Tue, 31 Mar 2026 15:41:24 +0200")
    try:
        dt = datetime.strptime(date_str.split('+')[0].split('-')[0].strip(), "%a, %d %b %Y %H:%M:%S")
        date_key = dt.strftime('%Y-%m-%d')
    except:
        date_key = date_str

    # Keep latest date for each email
    if to not in send_dates or date_key > send_dates[to]:
        send_dates[to] = date_key

print("=== SEND DATES FROM GMAIL ===\n")
for email in sorted(send_dates.keys()):
    print(f"{email}: {send_dates[email]}")

print("\n\n=== DUPLICATE COMPANIES TO PROCESS ===\n")

# Known duplicates from task description
duplicates_to_check = {
    'De Pee Logistiek': ['planning@depeelogistiek.nl'],
    'Wex Holland': ['info@wexholland.com'],
    'Berger Koerierservice': ['info@bergerkoerierservice.nl'],
    'A. Hak Transport': ['info@haktransport.nl'],
    'Blonk Logistiek': ['msprincess@live.nl'],
    'TAB Transport': ['info@tabtransport.nl'],
    'Restaurant Perceel': ['info@restaurantperceel.nl', 'restaurantperceel@gmail.com'],
    'Restaurant De Loet': ['info@deloet.nl', 'restaurantdeloet@gmail.com'],
}

for company, emails in duplicates_to_check.items():
    print(f"\n{company}:")
    for email in emails:
        if email.lower() in send_dates:
            print(f"  {email}: sent {send_dates[email.lower()]}")
        else:
            print(f"  {email}: NOT FOUND IN SENT EMAILS")
