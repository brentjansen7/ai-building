"""Random music picker uit assets/music/<mood>/. Geen API nodig — Brent download
1x een set Pixabay tracks volgens README en de pipeline kiest random per video."""

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIR = ROOT / "assets" / "music"


def list_tracks(mood: str = "upbeat") -> list[Path]:
    folder = MUSIC_DIR / mood
    if not folder.exists():
        # Fallback: alle music in assets/music/
        return list(MUSIC_DIR.glob("*.mp3"))
    return list(folder.glob("*.mp3"))


def pick_track(mood: str = "upbeat") -> Path | None:
    tracks = list_tracks(mood)
    if not tracks:
        # Fallback naar generic folder
        tracks = list(MUSIC_DIR.glob("*.mp3"))
    return random.choice(tracks) if tracks else None


if __name__ == "__main__":
    for mood in ["upbeat", "ambient"]:
        t = pick_track(mood)
        print(f"{mood}: {t}")
