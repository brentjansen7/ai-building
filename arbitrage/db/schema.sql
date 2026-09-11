-- PostgreSQL 16 + pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Listings table (main incoming data from all platforms)
CREATE TABLE listings (
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
    image_urls      TEXT[],
    posted_at       TIMESTAMPTZ,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    embedding       vector(1024),
    image_embedding vector(512),
    metadata        JSONB,
    UNIQUE(platform, external_id),
    CREATED INDEX idx_listings_platform ON listings(platform),
    INDEX idx_listings_category ON listings(category),
    INDEX idx_listings_scraped_at ON listings(scraped_at DESC)
);

CREATE INDEX idx_listings_embedding ON listings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_listings_title ON listings USING gin (to_tsvector('english', title));

-- Sold/Completed listings (price reference data)
CREATE TABLE sold_listings (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20) NOT NULL,
    external_id     VARCHAR(255),
    title           TEXT NOT NULL,
    sold_price      NUMERIC(10,2) NOT NULL,
    condition       VARCHAR(20),
    category        VARCHAR(100),
    brand           VARCHAR(100),
    sold_at         TIMESTAMPTZ,
    embedding       vector(1024),
    UNIQUE(platform, external_id),
    INDEX idx_sold_platform ON sold_listings(platform),
    INDEX idx_sold_category ON sold_listings(category),
    INDEX idx_sold_sold_at ON sold_listings(sold_at DESC)
);

CREATE INDEX idx_sold_embedding ON sold_listings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Price history (for tracking bids on auctions)
CREATE TABLE price_history (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    price           NUMERIC(10,2),
    bid_count       INTEGER,
    observed_at     TIMESTAMPTZ NOT NULL,
    INDEX idx_price_listing ON price_history(listing_id),
    INDEX idx_price_observed ON price_history(observed_at DESC)
);

SELECT create_hypertable('price_history', 'observed_at', if_not_exists => TRUE);

-- Price estimates
CREATE TABLE estimates (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    estimated_value NUMERIC(10,2),
    resale_price    NUMERIC(10,2),
    profit_score    NUMERIC(10,2),
    profit_pct      NUMERIC(5,4),
    confidence      NUMERIC(4,3),
    platform_fee    NUMERIC(10,2),
    shipping_est    NUMERIC(10,2),
    comparable_count INTEGER,
    comparable_ids  BIGINT[],
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_estimates_listing ON estimates(listing_id),
    INDEX idx_estimates_profit ON estimates(profit_score DESC),
    INDEX idx_estimates_created ON estimates(created_at DESC)
);

-- Alerts triggered
CREATE TABLE alerts_log (
    id              BIGSERIAL PRIMARY KEY,
    listing_id      BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    channel         VARCHAR(20),
    message         TEXT,
    profit_at_send  NUMERIC(10,2),
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_alerts_listing ON alerts_log(listing_id),
    INDEX idx_alerts_sent ON alerts_log(sent_at DESC)
);

-- Category performance tracking
CREATE TABLE niche_performance (
    id              BIGSERIAL PRIMARY KEY,
    category        VARCHAR(100),
    platform        VARCHAR(20),
    avg_margin      NUMERIC(10,2),
    deal_count      INTEGER,
    success_rate    NUMERIC(4,3),
    listings_seen   INTEGER,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, platform),
    INDEX idx_niche_category ON niche_performance(category),
    INDEX idx_niche_margin ON niche_performance(avg_margin DESC)
);

-- Scraper job tracking
CREATE TABLE scraper_runs (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(20) NOT NULL,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    listings_found  INTEGER DEFAULT 0,
    listings_new    INTEGER DEFAULT 0,
    status          VARCHAR(20) DEFAULT 'running',
    error_message   TEXT,
    INDEX idx_scraper_platform ON scraper_runs(platform),
    INDEX idx_scraper_started ON scraper_runs(started_at DESC)
);

-- User alerts configuration (for future multi-user support)
CREATE TABLE user_alerts_config (
    id              BIGSERIAL PRIMARY KEY,
    user_id         VARCHAR(100),
    min_profit_eur  NUMERIC(10,2) DEFAULT 30,
    min_profit_pct  NUMERIC(5,4) DEFAULT 0.25,
    min_confidence  NUMERIC(4,3) DEFAULT 0.70,
    telegram_enabled BOOLEAN DEFAULT true,
    discord_enabled BOOLEAN DEFAULT false,
    email_enabled   BOOLEAN DEFAULT false,
    active_categories VARCHAR(100)[],
    excluded_categories VARCHAR(100)[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Deduplication tracking (for Redis Bloom filter recovery)
CREATE TABLE dedupe_tracking (
    id              BIGSERIAL PRIMARY KEY,
    listing_hash    VARCHAR(64),
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_dedupe_hash ON dedupe_tracking(listing_hash),
    UNIQUE(listing_hash)
);

-- Create materialized view for quick dashboard queries
CREATE MATERIALIZED VIEW listings_summary AS
SELECT
    platform,
    category,
    COUNT(*) as total_listings,
    AVG(CAST(e.profit_score AS NUMERIC)) as avg_profit,
    MAX(CAST(e.profit_score AS NUMERIC)) as max_profit,
    COUNT(CASE WHEN e.profit_score > 30 THEN 1 END) as high_profit_count,
    NOW() as last_updated
FROM listings l
LEFT JOIN estimates e ON l.id = e.listing_id
WHERE l.scraped_at > NOW() - INTERVAL '7 days'
GROUP BY platform, category;

CREATE UNIQUE INDEX idx_listings_summary ON listings_summary(platform, category);
