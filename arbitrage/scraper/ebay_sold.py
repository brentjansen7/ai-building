"""
eBay sold listings scraper
Fetches historical sold data to build price estimation model
"""

import requests
import time
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import json

# Database connection
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="5af53c8cf9ab47a6a158e515636285bf"
    )

def scrape_ebay_sold(search_term, max_results=100):
    """
    Scrape eBay sold listings using simple HTML scraping
    Returns list of (title, sold_price, condition)
    """
    results = []

    # eBay search URL for sold items
    url = f"https://www.ebay.nl/sch/i.html"
    params = {
        "_nkw": search_term,
        "LH_Sold": 1,
        "LH_Complete": 1,
        "rt": "nc",
        "LH_ItemCondition": "3000"  # Used items
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        print(f"Fetching eBay sold listings for: {search_term}")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML - look for price patterns
        import re
        html = response.text

        # Look for price patterns like "€ 123,45"
        price_pattern = r'€\s*([\d.,]+)'
        prices = re.findall(price_pattern, html)

        # Look for title patterns in listing items
        # This is simplified - real scraping would need proper HTML parsing
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if '€' in line and any(x in line for x in ['sold', 'verkocht', 'Sold']):
                match = re.search(price_pattern, line)
                if match and len(results) < max_results:
                    price_str = match.group(1).replace('.', '').replace(',', '.')
                    try:
                        price = float(price_str)
                        if 5 < price < 10000:  # Reasonable price range
                            results.append({
                                'title': search_term,
                                'sold_price': price,
                                'condition': 'used',
                                'platform': 'ebay',
                                'sold_at': datetime.now()
                            })
                    except ValueError:
                        pass

        time.sleep(2)  # Be respectful

    except Exception as e:
        print(f"Error scraping {search_term}: {e}")

    return results

def insert_sold_listings(listings):
    """Insert sold listings into database"""
    if not listings:
        return

    try:
        conn = get_db()
        cur = conn.cursor()

        # Prepare data for insertion
        data = [
            (
                item['platform'],
                None,  # external_id
                item['title'],
                item['sold_price'],
                item['condition'],
                'electronics',  # category
                item['sold_at']
            )
            for item in listings
        ]

        # Insert with conflict handling
        query = """
        INSERT INTO sold_listings (platform, external_id, title, sold_price, condition, category, sold_at)
        VALUES %s
        ON CONFLICT (platform, external_id) DO NOTHING
        """

        execute_values(cur, query, data)
        conn.commit()
        print(f"Inserted {cur.rowcount} listings")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Database error: {e}")

def scrape_popular_items():
    """Scrape a selection of popular items"""

    items = [
        "iPhone 14 Pro",
        "iPhone 13",
        "Samsung Galaxy S23",
        "iPad Pro",
        "MacBook Air",
        "Sony WH-1000XM5",
        "AirPods Pro",
        "Samsung QLED TV",
        "Dyson V15",
        "Nintendo Switch",
        "PlayStation 5",
        "DJI Mavic 3",
        "Nikon D850",
        "Canon EOS R5",
    ]

    all_results = []

    for item in items:
        print(f"\n--- Scraping: {item} ---")
        results = scrape_ebay_sold(item, max_results=20)
        all_results.extend(results)
        print(f"Found {len(results)} listings")

    print(f"\nTotal results: {len(all_results)}")
    insert_sold_listings(all_results)
    print("Done!")

if __name__ == "__main__":
    scrape_popular_items()
