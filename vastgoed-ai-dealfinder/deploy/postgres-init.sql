-- PostgreSQL initialisatiescript voor Vastgoed AI Dealfinder
-- Tables worden aangemaakt via SQLAlchemy op startup

-- Indexen voor performance worden ook via SQLAlchemy aangemaakt.
-- Dit bestand is bedoeld voor eventuele extra configuratie.

-- Stel tijdzone in
SET timezone = 'Europe/Amsterdam';

-- Maak extra indexen aan na tabel creatie (optioneel, voor productie tuning)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_listings_postcode_price ON listings(postcode, price_ask);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analyses_score_grade ON analyses(deal_score DESC, deal_grade);

SELECT 'Database initialisatie klaar' AS status;
