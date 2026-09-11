# 🚀 START HERE - Arbitrage System Setup

**Volg deze stappen in volgorde. Je hebt niets meer handmatig in te typen.**

---

## STAP 1: PostgreSQL Installeren (5 min)

1. Download: https://www.postgresql.org/download/windows/
2. Run installer
3. **Onthoud het wachtwoord:** `arbitrage_dev_pass_123`
4. Port: `5432` (default)
5. Install voltooid → sluiten

---

## STAP 2: Redis Installeren (5 min)

### Via Chocolatey (makkelijker):

1. Open PowerShell **als Administrator**
2. Run:
```powershell
choco install redis-64
```
3. Klaar!

### Of handmatig:

1. Download: https://github.com/microsoftarchive/redis/releases/download/7.2.4/Redis-x64-7.2.4.zip
2. Extract zip → folder: `C:\redis`
3. Dubbelklik: `redis-server.exe`
4. Redis draait nu

---

## STAP 3: Automated Setup (10 min)

1. Open PowerShell **als Administrator**
2. Navigate naar arbitrage folder:
```powershell
cd "C:\Users\Naam Leerling\ai building brent jansen\arbitrage"
```

3. **Run the setup script:**
```powershell
powershell -ExecutionPolicy Bypass -File "SETUP_WINDOWS.ps1"
```

**OF**

Dubbelklik op: `RUN_SETUP.bat`

Het script doet automatisch:
- ✅ Python virtual environment
- ✅ Alle packages installeren
- ✅ PostgreSQL database aanmaken
- ✅ Schema initialiseren
- ✅ .env bestand aanmaken

Wacht tot het klaar is (3-5 minuten).

---

## STAP 4: Systeem Starten (1 min)

Dubbelklik op: **`RUN_SYSTEM.bat`**

Dit opent 2 PowerShell vensters:
- **Venster 1:** API server (http://localhost:8000)
- **Venster 2:** Scraper worker (scant platforms)

**Beide moeten draaien.** Laat ze open staan.

---

## STAP 5: Browser Extensie Installeren (2 min)

1. Open **Chrome**
2. Type in address bar: `chrome://extensions`
3. Toggle **"Developer mode"** (rechts bovenin)
4. Click **"Load unpacked"**
5. Navigate naar: `C:\Users\Naam Leerling\ai building brent jansen\arbitrage\extension`
6. Click **"Select Folder"**
7. Done! Extension is installed

---

## STAP 6: Test Het Systeem (1 min)

### Test 1: API Health Check
Open browser en ga naar:
```
http://localhost:8000/health
```

Je zou dit moeten zien:
```json
{"status": "healthy", "services": {...}}
```

### Test 2: Browser Overlay
1. Ga naar https://www.marktplaats.nl/
2. Scroll door listings
3. Je zou groene/rode badges moeten zien met `+€XXX (Y%)`
4. Klik op badge → zie volledige analyse

### Test 3: Telegram Alert (optioneel)
Zie: **Optional Setup** hieronder

---

## Klaar! 🎉

**Systeem draait automatisch. Deals worden gezocht en alerts komen door.**

- **API:** http://localhost:8000
- **Marktplaats:** Overlays zichtbaar
- **Telegram:** Alerts (als geconfigureerd)

---

## Optional: Telegram Setup (5 min)

Voor automatische alerts via Telegram:

1. Open Telegram
2. Zoek: `@BotFather`
3. Type: `/newbot`
4. Geef je bot een naam (bv: "ArbitrageBot")
5. Geef username (bv: "username_arbitrage_bot")
6. **Kopieer de token** dat je krijgt

7. Edit bestand: `.env` in arbitrage folder
8. Vind deze regels:
```ini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

9. Vervang:
```ini
TELEGRAM_BOT_TOKEN=xxx_PASTE_TOKEN_HERE_xxx
```

10. Stuur `/start` naar je bot op Telegram
11. In de logs van de bot zie je een chat ID
12. Vul in:
```ini
TELEGRAM_CHAT_ID=123456789
```

13. Restart het systeem (sluit `RUN_SYSTEM.bat` en open het opnieuw)

Nu krijg je Telegram alerts voor goede deals!

---

## Troubleshooting

### "PowerShell script execution disabled"
Run in PowerShell als Admin:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

### "PostgreSQL not found"
→ Download en install van https://www.postgresql.org/download/windows/

### "Redis connection refused"
→ Start Redis:
  - Via `redis-server.exe` (if installed)
  - Of via: `redis-cli ping` check

### "ModuleNotFoundError"
→ Zorg dat je in de `arbitrage` folder bent en het setup script heeft gedraaid

### "Port 8000 already in use"
→ Ander programma gebruikt poort 8000:
```powershell
netstat -ano | findstr :8000
taskkill /PID xxxxx /F
```

### Eerste keer downloaden van embedding model duurt lang
→ Normaal. Kan 2-5 minuten duren. Geduld!

---

## Volgende Stappen

**Nu het systeem draait:**

1. **Wacht op alerts** → eerste deals duiken op in Telegram (of check Marktplaats overlays)
2. **Click badge** op Marktplaats → zie volledige profit analyse
3. **Optimaliseer** → edit `.env` voor andere thresholds
4. **Schaal** → voeg Vinted tokens toe voor 3x throughput

---

## Support

Als iets niet werkt:
- Check `QUICK_START.md` voor details
- Check `BUILD_STATUS.md` voor architecture info
- Monitor de PowerShell vensters voor error messages

---

**Je bent klaar! Het systeem zoekt nu automatisch naar deals.** 🚀
