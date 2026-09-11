"""
Seed database with realistic sold listing data
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

def generate_variants(base_title, base_price, count, variance=0.15):
    """Generate multiple price variants of same product"""
    results = []
    for i in range(count):
        # Add storage/color variants to title
        variants = ["128GB", "256GB", "512GB", "1TB", "Space Gray", "Gold", "Silver", "Black"]
        variant = random.choice(variants)

        # Vary price around base with gaussian distribution
        price = base_price + random.gauss(0, base_price * variance)
        price = max(10, round(price, 2))  # Min €10, round to 2 decimals

        title = f"{base_title} {variant}"
        results.append((title, price, "used"))

    return results

# Generate comprehensive sold data
def generate_all_data():
    data = []

    # iPhones - most popular
    data.extend(generate_variants("iPhone 14 Pro", 850, 80))
    data.extend(generate_variants("iPhone 14", 700, 60))
    data.extend(generate_variants("iPhone 13 Pro", 750, 50))
    data.extend(generate_variants("iPhone 13", 600, 70))
    data.extend(generate_variants("iPhone 12", 450, 40))

    # Samsung
    data.extend(generate_variants("Samsung Galaxy S23", 650, 60))
    data.extend(generate_variants("Samsung Galaxy S23 Ultra", 900, 40))
    data.extend(generate_variants("Samsung Galaxy S22", 500, 50))
    data.extend(generate_variants("Samsung Galaxy A53", 300, 30))

    # Apple tablets & computers
    data.extend(generate_variants("iPad Pro 11", 700, 50))
    data.extend(generate_variants("iPad Pro 12.9", 800, 40))
    data.extend(generate_variants("iPad Air", 500, 40))
    data.extend(generate_variants("MacBook Air M1", 900, 50))
    data.extend(generate_variants("MacBook Air M2", 1200, 40))
    data.extend(generate_variants("MacBook Pro 14", 1800, 30))
    data.extend(generate_variants("MacBook Pro 16", 2200, 25))

    # Audio equipment
    data.extend(generate_variants("Sony WH-1000XM5", 280, 80))
    data.extend(generate_variants("Sony WH-1000XM4", 200, 70))
    data.extend(generate_variants("AirPods Pro", 150, 100))
    data.extend(generate_variants("AirPods Max", 500, 30))
    data.extend(generate_variants("Bose QuietComfort 45", 250, 60))
    data.extend(generate_variants("Bose QuietComfort 25", 180, 40))

    # TVs
    data.extend(generate_variants("Samsung QLED 55", 600, 40))
    data.extend(generate_variants("Samsung QLED 65", 900, 35))
    data.extend(generate_variants("Samsung QLED 75", 1300, 25))
    data.extend(generate_variants("LG OLED 55", 700, 40))
    data.extend(generate_variants("LG OLED 65", 1000, 35))
    data.extend(generate_variants("Sony Bravia 55", 650, 35))

    # Gaming
    data.extend(generate_variants("Nintendo Switch", 280, 100))
    data.extend(generate_variants("PlayStation 5", 450, 80))
    data.extend(generate_variants("Xbox Series X", 480, 70))
    data.extend(generate_variants("Nintendo Switch OLED", 320, 60))

    # Cameras
    data.extend(generate_variants("DJI Mavic 3", 1400, 50))
    data.extend(generate_variants("DJI Air 3", 900, 60))
    data.extend(generate_variants("Nikon D850", 1200, 40))
    data.extend(generate_variants("Canon EOS R5", 2200, 30))
    data.extend(generate_variants("Sony A7IV", 1800, 35))
    data.extend(generate_variants("GoPro Hero 11", 350, 70))
    data.extend(generate_variants("DJI Osmo Action", 200, 50))

    # Smartwatches & wearables
    data.extend(generate_variants("Apple Watch Series 8", 350, 80))
    data.extend(generate_variants("Apple Watch Ultra", 700, 50))
    data.extend(generate_variants("Garmin Fenix 7", 500, 40))
    data.extend(generate_variants("Samsung Galaxy Watch 5", 250, 60))

    # Home appliances
    data.extend(generate_variants("Dyson V15", 350, 70))
    data.extend(generate_variants("Dyson V12", 280, 60))
    data.extend(generate_variants("Shark Navigator", 200, 50))
    data.extend(generate_variants("Philips Airfryer", 120, 80))
    data.extend(generate_variants("Nespresso Lattissima", 300, 50))

    # Furniture & home
    data.extend(generate_variants("Herman Miller Aeron Chair", 600, 40))
    data.extend(generate_variants("Steelcase Leap Chair", 500, 35))
    data.extend(generate_variants("IKEA Billy Bookcase", 50, 100))
    data.extend(generate_variants("IKEA MALM Desk", 100, 80))

    # Laptops
    data.extend(generate_variants("Dell XPS 13", 800, 50))
    data.extend(generate_variants("Lenovo ThinkPad X1", 700, 45))
    data.extend(generate_variants("ASUS ROG Gaming Laptop", 1200, 40))

    # Keyboards & peripherals
    data.extend(generate_variants("Logitech MX Master 3S", 80, 60))
    data.extend(generate_variants("Corsair K95 Keyboard", 150, 50))
    data.extend(generate_variants("Razer DeathAdder", 50, 70))

    return data

def seed_sold_listings():
    """Insert seed data into sold_listings table"""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Clear existing data
        cur.execute("DELETE FROM sold_listings")
        conn.commit()
        print("Cleared existing sold_listings")

        # Generate all data
        all_data = generate_all_data()
        print(f"Generated {len(all_data)} listings")

        # Prepare data with dates
        data = []
        now = datetime.now()

        for title, price, condition in all_data:
            # Vary the sold_at dates over last 90 days
            days_ago = random.randint(1, 90)
            sold_at = now - timedelta(days=days_ago)

            data.append((
                "ebay",  # platform
                None,  # external_id
                title,  # title
                price,  # sold_price
                condition,  # condition
                "electronics",  # category
                sold_at  # sold_at
            ))

        # Insert in batches to avoid memory issues
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
            print(f"Inserted batch {i//batch_size + 1}")

        # Show summary
        cur.execute("SELECT COUNT(*) FROM sold_listings")
        total = cur.fetchone()[0]
        print(f"\n✓ Total sold_listings in DB: {total}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_sold_listings()
