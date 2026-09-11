# 🏠 Vastgoed AI Dealfinder

**Automatisch Nederlandse woningdeals analyseren op winstpotentieel**

Een volledig AI-systeem dat:
- Woningadvertenties scrapet van Pararius, Jaap.nl, Huislijn
- Detecteert of een woning een "kluswoning" is (renovatieproject)
- Schat renovatiekosten als een aannemer
- Analyzeert WOZ waarden en marktprijzen
- Berekent potentiële winst & ROI
- Geeft deal score (1-100) en grade (A-F)
- Chrome extension overlay op woningpagina's
- Telegram/Discord/Email alerts voor goede deals

---

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/brent/vastgoed-ai-dealfinder
cd vastgoed-ai-dealfinder
cp backend/.env.example backend/.env

# 2. Vul je API keys in .env
# ANTHROPIC_API_KEY=sk-ant-...
# EXTENSION_API_KEY=willekeurig_lange_sleutel

# 3. Start services
make dev

# 4. Install Chrome extension
# - Chrome → chrome://extensions
# - "Uitgepakte extensie laden"
# - Selecteer: vastgoed-ai-dealfinder/chrome-extension

# 5. Configureer extension
# - Klik 🏠 icoontje
# - API Endpoint: http://localhost:8000
# - API Key: je EXTENSION_API_KEY

# 6. Test op een woningpagina
# Open Pararius → analayse verschijnt automatisch!
```

---

## 📋 Architektuur

```
┌─────────────────────────────────────────────────────┐
│   Chrome Extension (Manifest V3)                    │
│   • Injecteert overlay op woningpagina's            │
│   • Extraheert listing data (prijs, m², adres)      │
│   • Roept backend API aan voor analyse              │
└────────────────┬────────────────────────────────────┘
                 │ HTTP POST /api/analyze
                 ▼
┌─────────────────────────────────────────────────────┐
│   FastAPI Backend (Python 3.12)                     │
│   ┌──────────────────────────────────────────────┐  │
│   │ Scrapers (Pararius, Jaap, Huislijn)         │  │
│   │ • Playwright browser automation              │  │
│   │ • Proxy rotation (anti-ban)                  │  │
│   │ • WOZ API fetcher (BAG, CBS)                 │  │
│   └──────────────────────────────────────────────┘  │
│   ┌──────────────────────────────────────────────┐  │
│   │ AI Services                                  │  │
│   │ • Klus Detector (Claude Vision + NLP)       │  │
│   │ • Renovation Cost Estimator (rule-based)    │  │
│   │ • Market Valuation Engine (comps-based)     │  │
│   │ • Deal Scorer (multi-factor weighting)      │  │
│   └──────────────────────────────────────────────┘  │
│   ┌──────────────────────────────────────────────┐  │
│   │ Queue System (RQ + Redis)                   │  │
│   │ • Async job processing                      │  │
│   │ • Scheduled scrapes (hourly/daily)          │  │
│   │ • Alert dispatcher                          │  │
│   └──────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬──────────────┐
    ▼            ▼            ▼              ▼
PostgreSQL    Redis      Telegram       Discord
(Listings,   (Queue,     (Alerts)       (Alerts)
Analysis)    Cache)
```

---

## 📦 Componenten

### Backend
- **API** (`/api/`)
  - `/deals` — Deal feed met filters
  - `/listings/{id}` — Listing details
  - `/analyze` — Live analyse (extension endpoint)
  - `/admin/scrape/{source}` — Handmatig scraper triggeren
  - `/stats` — Platform statistieken

- **Scrapers** (`/scrapers/`)
  - `base.py` — Base klasse (anti-ban, proxy rotation)
  - `pararius.py` — Pararius.nl scraper
  - `jaap.py` — Jaap.nl scraper
  - `huislijn.py` — Huislijn.nl scraper
  - `woz_fetcher.py` — WOZ/BAG/CBS data ophaler

- **AI Services** (`/services/`)
  - `klus_detector.py` — Claude Vision + trefwoorden analyse
  - `renovation_cost.py` — Nederlandse contractor prijzen model
  - `market_value.py` — Comparable sales + prijs/m² valuation
  - `deal_scorer.py` — Multi-factor deal scoring (1-100)
  - `alert_service.py` — Telegram/Discord/Email dispatcher

- **Queue** (`/queue/`)
  - `jobs.py` — RQ job definitions
  - `pipeline.py` — Analyse orchestration
  - `worker.py` — RQ worker + scheduler

### Database
- **PostgreSQL**
  - `listings` — Woningadvertenties
  - `analyses` — Gedetailleerde analyses
  - `comps` — Vergelijkbare verkopen
  - `woz_cache` — WOZ waarde cache
  - `alerts` — Verstuurde deal alerts
  - `scraper_logs` — Scrape activiteitslog

### Chrome Extension
- **manifest.json** — Manifest v3 config
- **content-script.js** — Geïnjecteerd in pagina (data extraction + overlay)
- **background-worker.js** — Service Worker (API calls, notificaties)
- **popup.html/js** — Extension instellingen panel
- **overlay.css** — Styling van deal card overlay

### Deployment
- **Docker** — Containerized architecture
- **Docker Compose** — Orchestration (API, Worker, DB, Redis, Nginx)
- **Nginx** — Reverse proxy + load balancing
- **Makefile** — Lokale development shortcuts

---

## 🎯 Deal Score Formule

```
Deal Score (0-100):
├── ROI potentieel (max 30pt)
│   ├── 30%+ ROI → 30pt
│   ├── 20-30% → 25pt
│   ├── 15-20% → 18pt
│   └── <5% → 0pt
├── Prijs vs WOZ (max 25pt)
│   ├── <75% WOZ → 25pt
│   ├── 75-85% → 20pt
│   ├── 85-100% → 15pt
│   └── >110% → 0pt
├── Prijs/m² vs buurt (max 20pt)
│   ├── <65% buurt → 20pt
│   ├── 75-85% → 13pt
│   └── >105% → 0pt
├── Renovatie efficiëntie (max 15pt)
│   ├── <8% van waarde → 15pt
│   ├── 8-25% → 9pt
│   └── >25% → 2pt
└── Klus upside (max 10pt)
    ├── 80%+ klus kans → 10pt
    ├── 40-60% → 5pt
    └── <20% → 1pt

Grades:
├── A: 85-100 (Uitzonderlijk)
├── B: 70-84  (Sterk)
├── C: 55-69  (Redelijk)
├── D: 40-54  (Zwak)
└── F: <40    (Slechte deal)
```

---

## 💰 Renovatiekosten (2024-2025 Prijzen)

Gebaseerd op echte Nederlandse markt data:

| Item | Min | Gem | Max | Opmerking |
|------|-----|-----|-----|-----------|
| Schilderwerk | €2.5k | €3.5k | €6k | per 80m² |
| Keuken | €5.5k | €9k | €16k | basic |
| Badkamer | €4.5k | €7k | €12k | compleet |
| Vloeren | €2.5k | €4k | €7.5k | laminaat/PVC |
| Dak | €5k | €9k | €18k | pannen |
| Elektra | €3.5k | €5.5k | €9.5k | herinstallatie |
| CV-systeem | €2k | €3.5k | €5.5k | nieuwe ketel |
| Isolatie | €3k | €5k | €8k | combinatie |
| **Totaal klus** | **€30k** | **€50k** | **€85k** | worst case |

*Prijzen inclusief arbeid + materialen, afhankelijk van stad*

---

## 🔌 API Voorbeelden

### Get Deal Feed
```bash
curl "http://localhost:8000/api/deals?page=1&per_page=20&city=Rotterdam&min_score=70&grade=A" \
  -H "X-Api-Key: your_api_key"
```

### Analyze Listing (Extension)
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_api_key" \
  -d '{
    "url": "https://www.pararius.nl/koopwoning/...",
    "address": "Meierplein 123, Rotterdam",
    "price_ask": 260000,
    "size_sqm": 75,
    "year_built": 1975,
    "city": "Rotterdam",
    "postcode": "3071PX"
  }'
```

### Response
```json
{
  "address": "Meierplein 123, Rotterdam",
  "city": "Rotterdam",
  "price_ask": 260000,
  "woz_value": 310000,
  "woz_diff": 50000,
  "is_klus": true,
  "klus_confidence": 0.78,
  "reno_cost_mid": 35000,
  "estimated_value_after_reno": 390000,
  "potential_profit": 95000,
  "roi_percentage": 22.6,
  "deal_score": 84,
  "deal_grade": "A",
  "verdict": "Uitstekende deal. ROI 22.6%, potentiële winst €95.000. Direct actie aanbevolen."
}
```

---

## 🔐 Security & Rate Limiting

- ✅ API key authentication (header `X-Api-Key`)
- ✅ Proxy rotation (Bright Data / custom)
- ✅ User-agent rotation
- ✅ Random delays (2-8 seconden tussen requests)
- ✅ robots.txt respect
- ✅ Rate limit aware (retry 503s)
- ✅ No sensitive data in logs (GDPR compliant)

---

## 📊 Performance Metrics

- Scraper: ~10-20 listings/minuut per source
- Analyse: ~5-10 listings/minuut (bottleneck: Claude Vision API)
- Database: <50ms query latency (met indexes)
- Extension overlay: <3 seconden response time (cached)

---

## 🛣️ Roadmap

### Phase 1 (Done)
- ✅ Basis scraper (Pararius, Jaap, Huislijn)
- ✅ Klus detectie (text + Vision)
- ✅ Renovatiekosten model
- ✅ Deal scoring
- ✅ Chrome extension overlay
- ✅ FastAPI backend
- ✅ Docker deployment

### Phase 2 (TODO)
- [ ] Funda scraper (afzonderlijke API)
- [ ] ML valuation model (trained on 1K+ comps)
- [ ] Historical price tracking
- [ ] Advanced alerts (custom webhooks)
- [ ] Dashboard (React app)
- [ ] Mobile app (React Native)

### Phase 3 (Long-term)
- [ ] Market prediction (prijs trends)
- [ ] Auction platform (connectie aanbieders)
- [ ] Mortgage calculator integration
- [ ] PDF rapportages genereren
- [ ] Multi-country support (België, Duitsland)

---

## 👨‍💻 Development

```bash
# Install + run locally
make install
make dev

# Run worker
make worker

# Run scheduler
make scheduler

# View logs
make logs

# Run tests
make test

# Cleanup
make clean
```

---

## 📝 License

MIT — Open source. Gebruik voor persoonlijk & commercial gebruik.

---

## ⚠️ Juridische Aandachtspunten

- ⚖️ **Scraping**: Respect voor `robots.txt`, rate limiting, geen overload
- 📋 **WOZ Data**: Publiek beschikbaar in Nederland (geen restricties)
- 🔒 **GDPR**: Adressen zijn semi-publiek, geen persoonlijke data opslag
- ✅ **Disclaimer**: Zie `docs/LEGAL.md` voor volledige details

---

## 🤝 Contributing

Bijdragen welkom! Open een issue of PR.

---

## 📧 Contact

Vragen? → brent@vastgoed-ai.local

---

**Gemaakt met ❤️ door Brent | Automade**
