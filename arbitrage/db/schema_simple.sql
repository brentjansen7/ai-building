-- Simple schema without pgvector/timescaledb (Windows compatibility)

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Listings table
CREATE TABLE IF NOT EXISTS listings (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20) NOT NULL,
    external_id     VARCHAR(255) NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    price           NUMERIC(10,2) NOT NULL,
    condition       VARCHAR(20),
    category        VARCHAR(100),
    brand           VARCHAR(100),
    seller_id       VARCHAR(100),
    location        VARCHAR(200),
    url             TEXT NOT NULL,
    posted_at       TIMESTAMPTZ,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB,
    UNIQUE(platform, external_id)
);

CREATE INDEX IF NOT EXISTS idx_listings_platform ON listings(platform);
CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category);
CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_listings_title ON listings USING gin (to_tsvector('english', title));

-- Sold listings
CREATE TABLE IF NOT EXISTS sold_listings (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20) NOT NULL,
    external_id     VARCHAR(255),
    title           TEXT NOT NULL,
    sold_price      NUMERIC(10,2) NOT NULL,
    condition       VARCHAR(20),
    category        VARCHAR(100),
    brand           VARCHAR(100),
    sold_at         TIMESTAMPTZ,
    UNIQUE(platform, external_id)
);

CREATE INDEX IF NOT EXISTS idx_sold_platform ON sold_listings(platform);

-- Price history
CREATE TABLE IF NOT EXISTS price_history (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    price           NUMERIC(10,2) NOT NULL,
    observed_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_listing ON price_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_price_observed ON price_history(observed_at);

-- Arbitrage opportunities
CREATE TABLE IF NOT EXISTS estimates (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    sold_price_avg  NUMERIC(10,2),
    profit_margin   NUMERIC(5,2),
    confidence      NUMERIC(3,2),
    calculated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_estimates_listing ON estimates(listing_id);
CREATE INDEX IF NOT EXISTS idx_estimates_margin ON estimates(profit_margin DESC);

-- Alerts/notifications
CREATE TABLE IF NOT EXISTS alerts_log (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    alert_type      VARCHAR(50),
    message         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_listing ON alerts_log(listing_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts_log(alert_type);

-- Niche performance metrics
CREATE TABLE IF NOT EXISTS niche_performance (
    id              BIGSERIAL PRIMARY KEY,
    category        VARCHAR(100),
    avg_price       NUMERIC(10,2),
    sell_through    NUMERIC(3,2),
    profit_potential NUMERIC(5,2),
    last_updated    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_niche_category ON niche_performance(category);

-- Scraper monitoring
CREATE TABLE IF NOT EXISTS scraper_runs (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20),
    status          VARCHAR(20),
    items_found     INT,
    items_saved     INT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_scraper_platform ON scraper_runs(platform);
CREATE INDEX IF NOT EXISTS idx_scraper_status ON scraper_runs(status);

-- Deduplication tracking
CREATE TABLE IF NOT EXISTS dedupe_tracking (
    id              BIGSERIAL PRIMARY KEY,
    listing_hash    VARCHAR(255) UNIQUE,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    hash_confidence NUMERIC(3,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dedupe_hash ON dedupe_tracking(listing_hash);
CREATE INDEX IF NOT EXISTS idx_dedupe_listing ON dedupe_tracking(listing_id);

-- Users/accounts
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE,
    email           VARCHAR(100) UNIQUE,
    api_key         VARCHAR(255) UNIQUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- System configuration
CREATE TABLE IF NOT EXISTS config (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default config
INSERT INTO config (key, value) VALUES
    ('last_scrape_marktplaats', '2025-01-01T00:00:00Z'),
    ('last_scrape_vinted', '2025-01-01T00:00:00Z'),
    ('last_scrape_ebay', '2025-01-01T00:00:00Z'),
    ('min_profit_margin', '15')
ON CONFLICT (key) DO NOTHING;
