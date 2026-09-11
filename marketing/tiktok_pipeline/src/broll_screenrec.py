"""Demo recorder voor de live routeplanner.

Snelle, geen-wachten cinematic flow:
1. Open app op iPhone-mobile viewport - app vult het scherm
2. Klik 'Importeer adressen' (modal opent)
3. Klik tab 'CSV / Excel'
4. Upload tijdelijke CSV met pre-gegeocodeerde lat/lng -> 0 sec wachten
5. Klik 'Importeren' (instant)
6. Klik 'Optimaliseer route'
7. Wacht alleen op route-summary
8. Verberg sidebar, kaart fullscreen, stats overlay bovenaan
9. Cinematic pan over route

Output: webm in 1080x1920.
"""

import asyncio
import csv
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "cache" / "screenrec"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

URL = os.environ.get("ROUTEPLANNER_URL", "https://brentjansen7.github.io/routeplanner-post/")

# 10 pre-gegeocodeerde adressen rondom Krimpen aan den IJssel + Capelle + Rotterdam-zuid
# Alleen lat/lng (en label) - app skipt Nominatim API call
PRE_GEOCODED_KRIMPEN = [
    {"lat": 51.9189, "lng": 4.5933, "label": "Raadhuisplein", "city": "Krimpen aan den IJssel"},
    {"lat": 51.9135, "lng": 4.5887, "label": "Lekkenburg", "city": "Krimpen aan den IJssel"},
    {"lat": 51.9148, "lng": 4.5995, "label": "IJsseldijk", "city": "Krimpen aan den IJssel"},
    {"lat": 51.9210, "lng": 4.6024, "label": "Tiendweg", "city": "Krimpen aan den IJssel"},
    {"lat": 51.9087, "lng": 4.5817, "label": "Stormpolder", "city": "Krimpen aan den IJssel"},
    {"lat": 51.9305, "lng": 4.5784, "label": "Bernardplein", "city": "Capelle aan den IJssel"},
    {"lat": 51.9268, "lng": 4.5751, "label": "Centrumpassage", "city": "Capelle aan den IJssel"},
    {"lat": 51.8901, "lng": 4.5145, "label": "Beijerlandselaan", "city": "Rotterdam"},
    {"lat": 51.8843, "lng": 4.5198, "label": "Slinge", "city": "Rotterdam"},
    {"lat": 51.8775, "lng": 4.5066, "label": "Zuidplein", "city": "Rotterdam"},
]


def write_demo_csv(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["straat", "plaats", "lat", "lng"])
        for s in PRE_GEOCODED_KRIMPEN:
            w.writerow([s["label"], s["city"], s["lat"], s["lng"]])
    return path


JS_HIDE_SIDEBAR_FULLSCREEN_MAP = """
() => {
    const sb = document.querySelector('#sidebar');
    if (sb) sb.style.display = 'none';
    const m = document.querySelector('#map');
    if (m) {
        m.style.position = 'fixed';
        m.style.inset = '0';
        m.style.width = '100vw';
        m.style.height = '100vh';
        m.style.zIndex = '50';
    }
    window.dispatchEvent(new Event('resize'));
}
"""

JS_OVERLAY_STATS = """
() => {
    const km = document.querySelector('#total-distance')?.textContent?.trim() || '';
    const tijd = document.querySelector('#total-time')?.textContent?.trim() || '';
    const stops = document.querySelector('#total-stops')?.textContent?.trim() || '';
    const old = document.querySelector('#__demo_overlay');
    if (old) old.remove();
    const el = document.createElement('div');
    el.id = '__demo_overlay';
    el.style.cssText = `
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 10000;
        background: linear-gradient(180deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.7) 70%, rgba(0,0,0,0) 100%);
        color: white;
        padding: 60px 24px 80px;
        text-align: center;
        font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
        animation: __demo_fadein 0.5s ease-out;
    `;
    const style = document.createElement('style');
    style.textContent = '@keyframes __demo_fadein { from {opacity:0; transform:translateY(-20px);} to {opacity:1; transform:translateY(0);} }';
    document.head.appendChild(style);
    el.innerHTML = `
        <div style="font-size: 22px; font-weight: 600; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 18px;">Route geoptimaliseerd</div>
        <div style="display: flex; gap: 36px; justify-content: center; align-items: baseline;">
            <div><div style="font-size: 56px; font-weight: 800; line-height: 1;">${stops}</div><div style="font-size: 16px; opacity: 0.7; margin-top: 6px;">stops</div></div>
            <div><div style="font-size: 56px; font-weight: 800; line-height: 1;">${km}</div><div style="font-size: 16px; opacity: 0.7; margin-top: 6px;">afstand</div></div>
            <div><div style="font-size: 56px; font-weight: 800; line-height: 1;">${tijd}</div><div style="font-size: 16px; opacity: 0.7; margin-top: 6px;">rijtijd</div></div>
        </div>
    `;
    document.body.appendChild(el);
}
"""


async def _flow_demo(page, csv_path: Path):
    # SHOT 1: app intro (1.2s)
    await page.wait_for_timeout(1200)

    # SHOT 2: open import modal
    await page.click("#import-btn")
    await page.wait_for_timeout(700)

    # SHOT 3: switch naar CSV-tab
    await page.click("#import-tab-csv")
    await page.wait_for_timeout(500)

    # SHOT 4: upload CSV met pre-geocoded coords
    file_input = await page.wait_for_selector("#import-file", timeout=3000)
    await file_input.set_input_files(str(csv_path))
    await page.wait_for_timeout(800)

    # SHOT 5: klik importeren - 0 sec wachten want geen Nominatim
    await page.click("#import-confirm")

    # Wacht max 5 sec op stops binnen
    waited = 0
    while waited < 5000:
        try:
            count_text = await page.text_content("#stop-count")
            n = int(count_text.strip("()"))
            if n >= 10:
                break
        except Exception:
            pass
        await page.wait_for_timeout(200)
        waited += 200

    # Sluit modal
    await page.evaluate("""() => {
        const m = document.querySelector('#import-modal');
        if (m) m.classList.add('hidden');
    }""")
    await page.wait_for_timeout(800)

    # SHOT 6: optimaliseer route
    await page.wait_for_selector("#optimize-btn:not([disabled])", timeout=5000)
    await page.click("#optimize-btn")

    # Wacht op resultaat
    try:
        await page.wait_for_selector("#route-summary:not(.hidden)", timeout=20000)
    except Exception:
        await page.wait_for_timeout(6000)

    # SHOT 7: verberg sidebar, kaart fullscreen
    await page.wait_for_timeout(400)
    await page.evaluate(JS_HIDE_SIDEBAR_FULLSCREEN_MAP)
    await page.wait_for_timeout(700)

    # SHOT 8: stats overlay bovenaan
    await page.evaluate(JS_OVERLAY_STATS)
    await page.wait_for_timeout(2200)

    # SHOT 9: cinematic pan over route
    map_area = await page.query_selector("#map")
    if map_area:
        box = await map_area.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            await page.mouse.move(cx, cy)
            await page.mouse.down()
            await page.mouse.move(cx + 60, cy + 40, steps=20)
            await page.mouse.up()

    await page.wait_for_timeout(2500)


async def _record_session(out_dir: Path, n_addresses: int = 10) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = CACHE_DIR / "demo_addresses.csv"
    write_demo_csv(csv_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Viewport 360x640 = mobile layout (onder 768 breakpoint).
        # Geen record_video_size: recording matched viewport exact.
        # FFmpeg upscaled later naar 1080x1920 (3x lanczos = crisp).
        context = await browser.new_context(
            viewport={"width": 360, "height": 640},
            device_scale_factor=1,
            user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            is_mobile=True,
            has_touch=True,
            record_video_dir=str(out_dir),
        )
        page = await context.new_page()
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            await _flow_demo(page, csv_path)
            await page.wait_for_timeout(700)
        except Exception as e:
            print(f"  [screenrec] error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await context.close()
            await browser.close()

    videos = list(out_dir.glob("*.webm"))
    return videos[-1] if videos else None


def _upscale_to_tiktok(in_path: Path, out_path: Path, width: int = 1080, height: int = 1920) -> Path:
    """Upscale webm/mp4 naar TikTok formaat met crisp Lanczos filter."""
    import shutil
    import subprocess
    ff = shutil.which("ffmpeg")
    if not ff:
        # Fallback: copy zoals het is
        out_path.write_bytes(in_path.read_bytes())
        return out_path
    cmd = [
        ff, "-y", "-i", str(in_path),
        "-vf", f"scale={width}:{height}:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def record_routeplanner_demo(out_path: Path | str, scenario: str = "full_demo", n_addresses: int = 10) -> Path | None:
    out_path = Path(out_path)
    tmp_dir = CACHE_DIR / f"session_{random.randint(1000, 9999)}"
    webm = asyncio.run(_record_session(tmp_dir, n_addresses=n_addresses))
    if not webm:
        return None
    final = out_path
    final.parent.mkdir(parents=True, exist_ok=True)
    # Upscale van native viewport (360x640) naar 1080x1920 met Lanczos voor crisp resultaat
    if final.suffix.lower() == ".mp4":
        _upscale_to_tiktok(webm, final)
        webm.unlink()
    else:
        webm.rename(final)
    return final


if __name__ == "__main__":
    out = CACHE_DIR / "test_full_demo.mp4"
    if out.exists():
        out.unlink()
    print(f"Opnemen: {URL}")
    p = record_routeplanner_demo(out, n_addresses=10)
    if p:
        print(f"OK -> {p} ({p.stat().st_size // 1024} KB)")
    else:
        print("FAALDE")
