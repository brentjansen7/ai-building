#!/usr/bin/env python3
import json
import re
from datetime import datetime

filepath = r"C:\Users\Naam Leerling\.claude\projects\c--Users-Naam-Leerling-ai-building-brent-jansen\0b689657-0961-45bb-86d5-28b0c835873e\tool-results\mcp-claude_ai_Gmail-gmail_search_messages-1774966027726.txt"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract JSON from the text field
try:
    parsed = json.loads(content)
    if isinstance(parsed, list) and len(parsed) > 0:
        text = parsed[0].get('text', '')
        data = json.loads(text)
    else:
        data = parsed
except Exception as e:
    print(f"Error parsing: {e}")
    exit(1)

messages = data.get('messages', [])
print(f"Total emails found: {len(messages)}\n")

# Track by recipient and company
by_recipient = {}
for msg in messages:
    to = msg.get('headers', {}).get('To', 'Unknown')
    date_str = msg.get('headers', {}).get('Date', '')
    subj = msg.get('headers', {}).get('Subject', '')

    # Parse date (e.g., "Tue, 31 Mar 2026 15:41:24 +0200")
    try:
        dt = datetime.strptime(date_str.split('+')[0].split('-')[0].strip(), "%a, %d %b %Y %H:%M:%S")
        date_key = dt.strftime('%Y-%m-%d')
    except:
        date_key = date_str

    if to not in by_recipient:
        by_recipient[to] = []
    by_recipient[to].append({'date': date_key, 'date_full': date_str, 'subject': subj})

# Sort and print
for to in sorted(by_recipient.keys()):
    items = by_recipient[to]
    # Sort by date descending
    items.sort(key=lambda x: x['date'], reverse=True)
    latest = items[0]
    company = latest['subject'].split('—')[-1].strip() if '—' in latest['subject'] else 'N/A'
    print(f"{company:30} | {to:35} | {latest['date']}")
    if len(items) > 1:
        print(f"{'  (older):':30} | {' ':35} | {items[-1]['date']}")

