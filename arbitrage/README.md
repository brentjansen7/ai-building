# AI Arbitrage System

Automatisch tweedehands platforms scannen, ondergeprijsde producten detecteren, en realtime winst-alerts sturen.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   SCRAPER WORKERS                        │
│  Auctionet │ BVA │ Catawiki │ Troostwijk │ Marktplaats  │
│  (API)     │(HTML)│ (API)   │   (API)    │   (API)      │
└──────────────────┬──────────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   Redis Queue     │
         │  (dedup + cache)  │
         └────────┬──────────┘
                  │
         ┌────────▼──────────┐
         │  PostgreSQL+       │
         │  pgvector         │
         └────────┬──────────┘
                  │
    ┌─────────────┼──────────────┐
    │             │              │
┌───▼──┐  ┌──────▼────┐  ┌──────▼──────┐
│Embed-│  │ Similarity│  │  XGBoost    │
│ding  │  │  Search   │  │  Estimator  │
└───┬──┘  └────┬──────┘  └──────┬──────┘
    └────┬──────┴────────────────┘
         │
    ┌────▼───────────────┐
    │  Profit Calculator │
    │  (30€, 25% min)    │
    └────┬───────────────┘
         │
    ┌────▼─────────┐
    │Alert Engine  │
    │  Telegram    │
    │  Discord     │
    └──────┬───────┘
           │
       ┌───▼───────┐
       │ Browser   │
       │Extension  │
       │(Overlay)  │
       └───────────┘
```

## Quick Start

### 1. Setup

```bash
cd arbitrage

# Create environment file
cp .env.example .env
# Edit .env with your credentials (Telegram token, DB password, etc.)

# Start Docker services
docker-compose up -d

# Wait for database to be ready
sleep 10

# Check services
docker-compose ps
```

### 2. Test Database Connection

```bash
docker-compose exec postgres psql -U arbitrage_user -d arbitrage -c "\dt"
```

### 3. Start Scrapers

```bash
# In a separate terminal
docker-compose exec scraper_worker python -m scraper.auctionet
```

### 4. Start API (already running in Docker)

```bash
# API available at http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Project Structure

```
arbitrage/
├── scraper/
│   ├── __init__.py
│   ├── platforms/
│   │   ├── auctionet.py         # Semi-public API (easiest)
│   │   ├── bva_auctions.py      # HTML + LD+JSON
│   │   ├── catawiki.py          # REST API (Cloudflare)
│   │   ├── troostwijk.py        # REST + bearer token
│   │   ├── marktplaats.py       # Reverse-engineered API
│   │   ├── vinted.py            # Mobile API
│   │   └── ebay.py              # Official API
│   ├── proxy_pool.py            # Proxy rotation
│   ├── dedup.py                 # Redis Bloom filter
│   ├── tasks.py                 # ARQ task definitions
│   └── worker.py                # Main worker loop
│
├── pipeline/
│   ├── __init__.py
│   ├── embedder.py              # multilingual-e5-large
│   ├── price_estimator.py       # KNN + XGBoost
│   ├── profit_calculator.py     # Deal scoring
│   ├── niche_discovery.py       # Auto category ranking
│   └── embedding_worker.py      # Async embedding worker
│
├── alerts/
│   ├── __init__.py
│   ├── telegram_bot.py          # aiogram
│   ├── discord_webhook.py       # Discord integration
│   └── alert_engine.py          # Threshold & dedup
│
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── models.py                # Pydantic schemas
│   ├── routes/
│   │   ├── estimate.py          # POST /estimate (extension)
│   │   ├── listings.py          # GET /listings
│   │   └── alerts.py            # GET/POST /alerts
│   └── auth.py                  # API key auth
│
├── extension/
│   ├── manifest.json            # MV3 config
│   ├── content.js               # Content script
│   ├── background.js            # Service worker
│   ├── popup/
│   │   ├── popup.html
│   │   └── popup.js
│   └── styles.css               # Overlay styles
│
├── db/
│   ├── schema.sql               # PostgreSQL schema
│   └── migrations/              # Alembic migrations
│
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

## Configuration

Edit `.env`:

```env
# Database
DB_PASSWORD=strong_password
DATABASE_URL=postgresql://arbitrage_user:strong_password@postgres:5432/arbitrage

# Telegram alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Proxy (optional)
PROXY_POOL_URL=http://proxy:port

# Thresholds
MIN_PROFIT_EUR=30
MIN_PROFIT_PCT=0.25
CONFIDENCE_THRESHOLD=0.70
```

## Scraper Platforms

| Platform | Status | Start | Difficulty |
|---|---|---|---|
| Auctionet | ✅ Ready | Week 1 | Easy (semi-public API) |
| BVA Auctions | ✅ Ready | Week 1 | Medium (HTML) |
| eBay | ✅ Ready | Week 1 | Easy (official API) |
| Marktplaats | ⚠️ Draft | Week 2 | Medium (Cloudflare) |
| Vinted | ⚠️ Draft | Week 2 | Easy (mobile API) |
| Catawiki | ⚠️ Draft | Week 3 | Hard (Cloudflare) |
| Troostwijk | ⚠️ Draft | Week 3 | Medium (token auth) |
| Facebook | ❌ Future | Week 4+ | Hard (Apify) |

## Database

PostgreSQL 16 with extensions:
- **pgvector**: Embeddings + similarity search
- **TimescaleDB**: Price history time-series
- **pg_trgm**: Full-text search on titles

Automatic initialization via `db/schema.sql`.

## API Endpoints

```bash
# Estimate price for a listing (used by extension)
POST /api/v1/estimate
{
  "title": "Sony WH-1000XM4",
  "price": 120,
  "platform": "marktplaats",
  "condition": "good"
}

# Get recent high-profit deals
GET /api/v1/listings?profit_min=50&limit=20

# Get alert history
GET /api/v1/alerts

# Configure user alerts
POST /api/v1/alerts/config
{
  "min_profit_eur": 30,
  "min_confidence": 0.70,
  "platforms": ["marktplaats", "auctionet"]
}
```

## Development

```bash
# Format code
docker-compose exec api black .

# Run tests
docker-compose exec api pytest tests/

# View logs
docker-compose logs -f api
docker-compose logs -f scraper_worker

# Database shell
docker-compose exec postgres psql -U arbitrage_user -d arbitrage
```

## Troubleshooting

### Postgres won't start
```bash
docker-compose down -v  # Remove volumes
docker-compose up postgres -d  # Rebuild
```

### Redis connection error
```bash
docker-compose logs redis
docker-compose restart redis
```

### API can't connect to DB
```bash
# Wait longer for Postgres to initialize
docker-compose exec postgres pg_isready -U arbitrage_user
```

## Legal Notes

- Scraping platforms may violate ToS — civil risk, not criminal
- Use official APIs where available (eBay, Auctionet)
- GDPR: Don't store seller personal data longer than needed
- No automated bidding — system is info-only

## Next Steps

1. **Week 1**: Auctionet + BVA + eBay scrapers working
2. **Week 2**: Embeddings + price estimation running
3. **Week 3**: Telegram alerts working
4. **Week 4**: Chrome extension complete
5. **Week 5+**: Scale to full platform coverage

See `sleepy-hugging-dream.md` for complete technical plan.
