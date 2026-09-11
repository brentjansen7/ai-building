# API Documentatie — Vastgoed AI Dealfinder

Base URL: `http://localhost:8000` (of je deployment URL)

Authentication: Header `X-Api-Key: your_api_key`

---

## Endpoints

### 1. Deal Feed

**GET** `/api/deals`

Haal een gepagineerde feed van deals op met filters.

**Parameters:**
- `page` (int, default 1) — Pagina nummer
- `per_page` (int, default 20, max 100) — Items per pagina
- `city` (string, optional) — Filter op stad
- `min_score` (int, default 0) — Minimum deal score (0-100)
- `grade` (string, optional) — Filter op grade (A, B, C, D, F)
- `min_profit` (int, default 0) — Minimum potentiële winst in €
- `source` (string, optional) — Filter op bron (pararius, jaap, huislijn, funda)
- `klus_only` (bool, default false) — Alleen kluswoningen

**Response:**
```json
{
  "items": [
    {
      "listing_id": "uuid",
      "address": "Meierplein 123",
      "city": "Rotterdam",
      "price_ask": 260000,
      "deal_score": 84,
      "deal_grade": "A",
      "potential_profit": 95000,
      "roi_percentage": 22.6,
      "reno_cost_mid": 35000,
      "estimated_value_after_reno": 390000,
      "url": "https://...",
      "source": "pararius"
    }
  ],
  "total": 342,
  "page": 1,
  "per_page": 20
}
```

---

### 2. Listing Details

**GET** `/api/listings/{listing_id}`

Haal volledige details van één listing op inclusief nieuwste analyse.

**Response:**
```json
{
  "id": "uuid",
  "source": "pararius",
  "url": "https://...",
  "title": "Ruim huis Meierplein",
  "price_ask": 260000,
  "address": "Meierplein 123",
  "city": "Rotterdam",
  "size_sqm": 75,
  "year_built": 1975,
  "is_klus_likely": true,
  "woz_value": 310000,
  "latest_analysis": {
    "klus_probability": 0.78,
    "reno_cost_min": 25000,
    "reno_cost_mid": 35000,
    "reno_cost_max": 50000,
    "estimated_value_after_reno": 390000,
    "roi_percentage": 22.6,
    "deal_score": 84,
    "deal_grade": "A"
  }
}
```

---

### 3. Live Analyse (Extension)

**POST** `/api/analyze`

Voer een volledige analyse uit op een listing. Gebruikt in Chrome extension.

**Authentication:** Header `X-Api-Key` verplicht

**Request Body:**
```json
{
  "url": "https://www.pararius.nl/koopwoning/...",
  "address": "Meierplein 123, Rotterdam",
  "price_ask": 260000,
  "size_sqm": 75,
  "rooms": 4,
  "bedrooms": 3,
  "year_built": 1975,
  "city": "Rotterdam",
  "postcode": "3071PX",
  "description": "Ruim hoekwoning met veel...",
  "image_urls": ["https://...", "https://..."],
  "source": "pararius"
}
```

**Response:**
```json
{
  "address": "Meierplein 123, Rotterdam",
  "city": "Rotterdam",
  "price_ask": 260000,
  "size_sqm": 75,
  "woz_value": 310000,
  "woz_year": 2024,
  "woz_diff": 50000,
  "is_klus": true,
  "klus_confidence": 0.78,
  "klus_keywords": ["opknapper", "renovatie nodig"],
  "reno_cost_min": 25000,
  "reno_cost_mid": 35000,
  "reno_cost_max": 50000,
  "reno_breakdown": {
    "keuken": 9000,
    "badkamer": 7000,
    "vloeren": 4000,
    "schilderwerk": 3500,
    "elektra": 5500,
    "isolatie": 5000
  },
  "price_per_sqm": 3467,
  "neighborhood_price_per_sqm": 4200,
  "estimated_value_after_reno": 390000,
  "total_investment": 295000,
  "potential_profit": 95000,
  "roi_percentage": 22.6,
  "deal_score": 84,
  "deal_grade": "A",
  "score_components": {
    "roi": 25,
    "price_vs_woz": 20,
    "price_per_sqm": 15,
    "reno_efficiency": 12,
    "klus_upside": 8
  },
  "listing_id": "uuid",
  "cached": false
}
```

**Mogelijke Errors:**
- `401 Unauthorized` — Ongeldige/ontbrekende API key
- `400 Bad Request` — Ontbrekende vereiste velden
- `500 Internal Server Error` — Backend fout (controleer logs)

---

### 4. Admin — Scraper Triggeren

**POST** `/api/admin/scrape/{source}`

Handmatig een scraper starten.

**Parameters:**
- `source` (string) — `pararius`, `jaap`, of `huislijn`

**Authentication:** Header `X-Api-Key` verplicht

**Response:**
```json
{
  "status": "queued",
  "job_id": "job_uuid_123",
  "source": "pararius"
}
```

**Voorbeeld:**
```bash
curl -X POST http://localhost:8000/api/admin/scrape/pararius \
  -H "X-Api-Key: your_api_key"
```

---

### 5. Admin — Analyse Triggeren

**POST** `/api/admin/analyze/{listing_id}`

Analyseer een bestaande listing opnieuw.

**Response:**
```json
{
  "status": "queued",
  "job_id": "job_uuid_456"
}
```

---

### 6. Platform Stats

**GET** `/api/stats`

Haal platform-brede statistieken op.

**Response:**
```json
{
  "total_listings": 5234,
  "total_analyses": 4891,
  "avg_deal_score": 62.4,
  "deals_by_grade": {
    "A": 156,
    "B": 723,
    "C": 1456,
    "D": 1203,
    "F": 353
  }
}
```

---

## Filters Voorbeeld

### Alle Grade A deals in Amsterdam
```bash
curl "http://localhost:8000/api/deals?city=Amsterdam&grade=A&per_page=100" \
  -H "X-Api-Key: your_api_key"
```

### Kluswoningen met >20% ROI en >€50k winst
```bash
# Let op: deze filters zijn via code filterwerk (niet direct in query)
# Implementeer filter logic in frontend
```

### Deals met minimaal score 80
```bash
curl "http://localhost:8000/api/deals?min_score=80" \
  -H "X-Api-Key: your_api_key"
```

---

## Rate Limits

- Geen expliciete rate limit (development mode)
- **Productie**: 100 requests/minuut per API key (planned)

---

## Webhook Responses

Wanneer een hoge-score deal gevonden wordt, verstuurt het systeem automatisch:
- 🔔 **Telegram** (indien geconfigureerd)
- 🔔 **Discord** (indien geconfigureerd)
- 📧 **Email** (indien geconfigureerd)

Pas thresholds aan in `/api/settings` (TODO: endpoint).

---

## Error Handling

Alle endpoints returnen error responses in dit format:

```json
{
  "detail": "Listing niet gevonden"
}
```

**Common Status Codes:**
- `200 OK` — Succes
- `400 Bad Request` — Ongeldige input
- `401 Unauthorized` — Ongeldige API key
- `404 Not Found` — Resource niet gevonden
- `500 Internal Server Error` — Server fout

---

## WebSocket (Future)

Planned: Real-time deal alerts via WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/deals?api_key=...');
ws.onmessage = (event) => {
  const deal = JSON.parse(event.data);
  console.log('Nieuwe deal:', deal.deal_grade, deal.potential_profit);
};
```

---

## SDK / Client Libraries

### Python
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000"

# Get deals
response = requests.get(
    f"{BASE_URL}/api/deals?city=Rotterdam&min_score=70",
    headers={"X-Api-Key": API_KEY}
)
deals = response.json()

# Analyze listing
analyze_resp = requests.post(
    f"{BASE_URL}/api/analyze",
    headers={"X-Api-Key": API_KEY},
    json={
        "url": "https://...",
        "address": "Meierplein 123",
        "price_ask": 260000,
        "city": "Rotterdam"
    }
)
analysis = analyze_resp.json()
```

### JavaScript/Node
```javascript
const apiKey = "your_api_key";
const baseUrl = "http://localhost:8000";

// Get deals
const deals = await fetch(
  `${baseUrl}/api/deals?city=Rotterdam&min_score=70`,
  { headers: { "X-Api-Key": apiKey } }
).then(r => r.json());

// Analyze
const analysis = await fetch(
  `${baseUrl}/api/analyze`,
  {
    method: "POST",
    headers: {
      "X-Api-Key": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      url: "https://...",
      address: "Meierplein 123",
      price_ask: 260000,
      city: "Rotterdam"
    })
  }
).then(r => r.json());
```

---

## OpenAPI / Swagger Docs

Volledige interactieve API documentatie beschikbaar op:
```
http://localhost:8000/docs
```

ReDoc alternatief:
```
http://localhost:8000/redoc
```
