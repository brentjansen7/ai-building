"""Pexels API: download stock-video clips per keyword. Cache lokaal."""

import hashlib
import os
import random
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "cache" / "pexels"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://api.pexels.com/videos"


def _key():
    k = os.environ.get("PEXELS_API_KEY")
    if not k:
        raise RuntimeError("PEXELS_API_KEY ontbreekt in .env")
    return k


def search_videos(query: str, per_page: int = 10, orientation: str = "portrait") -> list:
    headers = {"Authorization": _key()}
    params = {"query": query, "per_page": per_page, "orientation": orientation}
    r = requests.get(f"{API_BASE}/search", headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("videos", [])


def _pick_file(video: dict) -> dict | None:
    files = video.get("video_files", [])
    portrait = [f for f in files if f.get("height", 0) >= f.get("width", 0)]
    pool = portrait or files
    pool = [f for f in pool if 720 <= f.get("height", 0) <= 1920]
    if not pool:
        pool = files
    return max(pool, key=lambda f: f.get("height", 0)) if pool else None


def download_clip(video: dict) -> Path | None:
    f = _pick_file(video)
    if not f:
        return None
    url = f["link"]
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    out = CACHE_DIR / f"pexels_{video['id']}_{h}.mp4"
    if out.exists():
        return out
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(out, "wb") as fp:
        for chunk in r.iter_content(chunk_size=8192):
            fp.write(chunk)
    return out


def fetch_clips_for_keywords(keywords: list, n_per_keyword: int = 2) -> list[Path]:
    paths = []
    for kw in keywords:
        if kw == "screen_recording_routeplanner":
            continue
        try:
            videos = search_videos(kw, per_page=10)
        except Exception as e:
            print(f"  [pexels] search failed for '{kw}': {e}")
            continue
        random.shuffle(videos)
        for v in videos[:n_per_keyword]:
            try:
                p = download_clip(v)
                if p:
                    paths.append(p)
            except Exception as e:
                print(f"  [pexels] download failed: {e}")
    return paths


if __name__ == "__main__":
    import sys
    kws = sys.argv[1:] or ["delivery van", "courier package"]
    clips = fetch_clips_for_keywords(kws)
    print(f"Downloaded {len(clips)} clips:")
    for c in clips:
        print(f"  - {c}")
