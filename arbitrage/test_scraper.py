#!/usr/bin/env python3
"""
Quick test script for scrapers.
Run: python test_scraper.py
"""

import asyncio
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from scraper.platforms.auctionet import scrape_auctionet_open
from scraper.platforms.bva_auctions import scrape_bva_auctions


async def test_auctionet():
    """Test Auctionet scraper."""
    print("\n" + "="*60)
    print("TESTING AUCTIONET SCRAPER")
    print("="*60)

    try:
        items = await scrape_auctionet_open()
        print(f"\n✓ Successfully fetched {len(items)} items from Auctionet")

        if items:
            print(f"\nFirst item:")
            item = items[0]
            print(f"  Title: {item.get('title')}")
            print(f"  Price: €{item.get('price')}")
            print(f"  Platform: {item.get('platform')}")
            print(f"  URL: {item.get('url')}")
            print(f"  Category: {item.get('category')}")

        return len(items) > 0

    except Exception as e:
        print(f"\n✗ Auctionet scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bva():
    """Test BVA Auctions scraper."""
    print("\n" + "="*60)
    print("TESTING BVA AUCTIONS SCRAPER")
    print("="*60)

    try:
        lots = await scrape_bva_auctions()
        print(f"\n✓ Successfully fetched {len(lots)} lots from BVA Auctions")

        if lots:
            print(f"\nFirst lot:")
            lot = lots[0]
            print(f"  Title: {lot.get('title')}")
            print(f"  Price: €{lot.get('price')}")
            print(f"  Platform: {lot.get('platform')}")
            print(f"  URL: {lot.get('url')}")
            print(f"  Category: {lot.get('category')}")

        return len(lots) > 0

    except Exception as e:
        print(f"\n✗ BVA Auctions scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n🔍 ARBITRAGE SYSTEM - SCRAPER TESTS")
    print("="*60)

    results = {}

    # Test Auctionet (easier API)
    results['auctionet'] = await test_auctionet()

    # Test BVA (HTML parsing)
    results['bva'] = await test_bva()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed. Check errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
