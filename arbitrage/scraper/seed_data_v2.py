"""
Seed database with realistic sold listing data
Focused on 3 most profitable categories with resale prices
"""

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import random

def get_db():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="5af53c8cf9ab47a6a158e515636285bf"
    )

def generate_variants(base_title, base_resale_price, count, variance=0.12):
    """Generate multiple price variants of same product

    base_resale_price = typical selling price on 2nd hand market
    This is what we can realistically sell it for
    """
    results = []
    variants_list = ["128GB", "256GB", "512GB", "1TB", "Space Gray", "Gold", "Silver", "Black", "Blue", "Red"]

    for i in range(count):
        variant = random.choice(variants_list)

        # Vary price around base with gaussian distribution
        price = base_resale_price + random.gauss(0, base_resale_price * variance)
        price = max(10, round(price, 2))

        title = f"{base_title} {variant}"
        results.append((title, price, "used"))

    return results

def generate_all_data():
    """
    Generate data for top 3 profit categories:
    1. HIGH-END (€800+): Electronics - phones, laptops, cameras
    2. MID-RANGE (€200-800): Tablets, smartwatches, headphones
    3. BUDGET (€20-200): Accessories, small appliances
    """
    data = []

    print("=" * 60)
    print("CATEGORIE 1: PREMIUM (€800+) - Telefoons & Laptops")
    print("Winst: 20-30% | Werk: Gemiddeld")
    print("=" * 60)

    # PREMIUM: iPhones & Samsung flagships - 20-30% margins
    data.extend(generate_variants("iPhone 15 Pro Max", 1400, 120))  # Sell for €1400, buy cheaper
    data.extend(generate_variants("iPhone 15 Pro", 1100, 120))
    data.extend(generate_variants("iPhone 14 Pro Max", 1200, 100))
    data.extend(generate_variants("iPhone 14 Pro", 950, 100))
    data.extend(generate_variants("Samsung Galaxy S24 Ultra", 1300, 80))
    data.extend(generate_variants("Samsung Galaxy S24", 950, 80))
    data.extend(generate_variants("MacBook Air M3", 1400, 70))
    data.extend(generate_variants("MacBook Pro 14", 2000, 60))

    print("\n" + "=" * 60)
    print("CATEGORIE 2: MID-RANGE (€200-800) - Audio & Tablets")
    print("Winst: 35-50% | Werk: Laag (populair, veel kopers)")
    print("=" * 60)

    # MID-RANGE: Audio equipment & tablets - 35-50% margins (BEST PROFIT/EFFORT)
    data.extend(generate_variants("Sony WH-1000XM5", 320, 150))     # Buy €220, sell €320 = 45%
    data.extend(generate_variants("Sony WH-1000XM4", 240, 120))     # Buy €160, sell €240 = 50%
    data.extend(generate_variants("AirPods Pro Max", 580, 100))     # Buy €400, sell €580 = 45%
    data.extend(generate_variants("AirPods Pro Gen 2", 180, 150))   # Buy €120, sell €180 = 50%
    data.extend(generate_variants("iPad Pro 11", 780, 90))          # Buy €550, sell €780 = 41%
    data.extend(generate_variants("iPad Air", 550, 80))             # Buy €400, sell €550 = 37%
    data.extend(generate_variants("iPad Mini", 420, 70))            # Buy €300, sell €420 = 40%
    data.extend(generate_variants("Apple Watch Series 9", 380, 100))
    data.extend(generate_variants("Samsung Galaxy Tab S9", 600, 80))

    print("\n" + "=" * 60)
    print("CATEGORIE 3: BUDGET (€20-200) - Accessories & Small items")
    print("Winst: 60-100% | Werk: Veel (veel kleine deals)")
    print("=" * 60)

    # BUDGET: Accessories - HIGHEST margins but more items to handle
    data.extend(generate_variants("Apple AirTag 4-pack", 95, 200))   # Buy €50, sell €95 = 90%
    data.extend(generate_variants("USB-C cable official", 25, 300))  # Buy €12, sell €25 = 108%
    data.extend(generate_variants("iPhone case OtterBox", 35, 250))  # Buy €20, sell €35 = 75%
    data.extend(generate_variants("Screen protector glass", 15, 400))  # Buy €6, sell €15 = 150%
    data.extend(generate_variants("Phone charger 30W", 28, 280))     # Buy €15, sell €28 = 87%
    data.extend(generate_variants("Charging cable", 12, 350))        # Buy €5, sell €12 = 140%
    data.extend(generate_variants("Pop socket", 8, 500))             # Buy €3, sell €8 = 167%
    data.extend(generate_variants("Phone stand", 18, 400))           # Buy €10, sell €18 = 80%
    data.extend(generate_variants("Webcam cover", 6, 600))           # Buy €2, sell €6 = 200%
    data.extend(generate_variants("USB hub", 22, 300))               # Buy €12, sell €22 = 83%

    # Fill out more mid and high end for volume
    data.extend(generate_variants("GoPro Hero 12", 380, 80))
    data.extend(generate_variants("DJI Mini 4 Pro", 600, 70))
    data.extend(generate_variants("Nintendo Switch OLED", 360, 100))
    data.extend(generate_variants("PlayStation 5 Slim", 500, 80))
    data.extend(generate_variants("Sony A6400", 750, 60))

    return data

def seed_sold_listings():
    """Insert seed data into sold_listings table"""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Clear existing data
        cur.execute("DELETE FROM sold_listings")
        conn.commit()
        print("\n[DB] Cleared existing sold_listings\n")

        # Generate all data
        all_data = generate_all_data()
        print(f"\n[DB] Generated {len(all_data)} total listings\n")

        # Prepare data with dates
        data = []
        now = datetime.now()

        for title, price, condition in all_data:
            # Vary the sold_at dates over last 90 days
            days_ago = random.randint(1, 90)
            sold_at = now - timedelta(days=days_ago)

            data.append((
                "marktplaats",  # platform (Dutch market)
                None,  # external_id
                title,  # title
                price,  # sold_price (RESALE PRICE - what we can sell for)
                condition,  # condition
                "electronics",  # category
                sold_at  # sold_at
            ))

        # Insert in batches
        batch_size = 500
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            query = """
            INSERT INTO sold_listings
            (platform, external_id, title, sold_price, condition, category, sold_at)
            VALUES %s
            """
            execute_values(cur, query, batch)
            conn.commit()
            print(f"[DB] Inserted batch {i//batch_size + 1}")

        # Show summary
        cur.execute("SELECT COUNT(*) FROM sold_listings")
        total = cur.fetchone()[0]
        print(f"\n✓ Total sold_listings in DB: {total}\n")

        print("=" * 60)
        print("KLAAR! Database is gevuld met realistische resale prijzen")
        print("=" * 60)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_sold_listings()
