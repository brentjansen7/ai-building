# Setup Gids — Vastgoed AI Dealfinder

## 1. Vereisten

- Python 3.12+
- Docker Desktop
- Google Chrome
- Anthropic API key (voor klus detectie)

---

## 2. Backend Installatie

```bash
cd backend

# Kopieer env bestand
cp .env.example .env

# Vul je API keys in .env:
# ANTHROPIC_API_KEY=sk-ant-...
# TELEGRAM_TOKEN=...
# EXTENSION_API_KEY=willekeurige_lange_sleutel

# Installeer dependencies
pip install -r requirements.txt

# Installeer Playwright browsers
playwright install chromium
```

---

## 3. Database & Services Starten

```bash
# Vanuit project root:
make dev

# Dit start:
# - PostgreSQL (poort 5432)
# - Redis (poort 6379)
# - FastAPI API (poort 8000)
# - RQ Worker
# - RQ Scheduler
```

API docs bereikbaar op: http://localhost:8000/docs

---

## 4. Chrome Extension Installeren

1. Open Chrome
2. Ga naar `chrome://extensions`
3. Zet "Ontwikkelaarsmodus" aan (rechtsboven)
4. Klik "Uitgepakte extensie laden"
5. Selecteer de map: `vastgoed-ai-dealfinder/chrome-extension`
6. De extensie verschijnt in je toolbar

### Extension Configureren

1. Klik op het 🏠 icoontje
2. Ga naar ⚙️ Instellingen
3. Vul in:
   - API Endpoint: `http://localhost:8000` (of je server URL)
   - API Key: de waarde uit je `.env` bij `EXTENSION_API_KEY`
4. Klik "Instellingen Opslaan"

---

## 5. Eerste Scrape Starten

```bash
# Handmatig triggeren via API:
curl -X POST http://localhost:8000/api/admin/scrape/pararius \
  -H "X-Api-Key: jouw_api_key"

# Of via Makefile:
# make worker
```

---

## 6. Chrome Extension Testen

1. Open een woningpagina op Pararius.nl
2. De extensie analyseert automatisch
3. Na ~3-5 seconden verschijnt de deal overlay rechtsonder

---

## 7. Alerts Configureren

In `.env`:

```env
# Telegram
TELEGRAM_TOKEN=jouw_bot_token
TELEGRAM_CHAT_ID=jouw_chat_id

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Email
ALERT_EMAIL=jouw@email.nl
SMTP_USER=jouw@gmail.com
SMTP_PASS=gmail_app_wachtwoord
```

---

## 8. Productie Deployment

### Railway (Aanbevolen voor start)

```bash
# Installeer Railway CLI
npm install -g @railway/cli

railway login
railway new
railway add --database postgresql
railway add --database redis
railway deploy
```

### VPS (Hetzner / DigitalOcean)

```bash
# Server instellen
apt install docker.io docker-compose

# Clone repo + env instellen
git clone ...
cd vastgoed-ai-dealfinder
cp backend/.env.example backend/.env
nano backend/.env

# Starten
cd deploy && docker-compose up -d
```

---

## 9. Veelgestelde Vragen

**Q: Pararius geeft een block?**
A: Voeg proxies toe aan `PROXY_LIST` in `.env`. Gebruik Bright Data of Oxylabs.

**Q: WOZ data wordt niet gevonden?**
A: WOZ Waardeloket heeft een rate limit. Voeg een `BAG_API_KEY` toe van kadaster.nl.

**Q: Chrome extension geeft "API error"?**
A: Controleer of de API draait op `http://localhost:8000` en de API key correct is in de extension instellingen.

**Q: Hoe test ik zonder echte scraper?**
A: POST direct naar `/api/analyze` met handmatige listing data.
