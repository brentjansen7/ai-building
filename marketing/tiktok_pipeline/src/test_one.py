"""Smoke test: rendert 1 complete video end-to-end vanuit een hardcoded script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import voice
import broll_pexels
import captions
import music
import render

ROOT = Path(__file__).resolve().parent.parent

SCRIPT = {
    "id": "test_one",
    "format": "live_demo",
    "hook": "Een 16-jarige bouwde dit voor zijn eigen postroute",
    "body": "Ik plak 80 adressen, klik op optimaliseer, en de route staat in 10 seconden klaar. Geen Google Maps gepuzzel meer.",
    "cta": "Link in bio. Gratis proberen.",
    "broll_keywords": ["delivery van", "courier package"],
    "music_mood": "upbeat",
}


def voice_text(s):
    return f"{s['hook']}. {s['body']} {s['cta']}"


def main():
    work = ROOT / "cache" / "work" / SCRIPT["id"]
    work.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "output" / "test"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[1/5] Voice...")
    voice_mp3 = work / "voice.mp3"
    voice.synthesize(voice_text(SCRIPT), voice_mp3)
    print(f"  ok ({voice_mp3.stat().st_size // 1024} KB)")

    print("[2/5] B-roll Pexels...")
    clips = broll_pexels.fetch_clips_for_keywords(SCRIPT["broll_keywords"], n_per_keyword=2)
    print(f"  {len(clips)} clips")

    print("[3/5] Captions...")
    ass_path = work / "subs.ass"
    captions.mp3_to_ass(voice_mp3, ass_path)
    print("  ok")

    print("[4/5] Music pick...")
    track = music.pick_track(SCRIPT["music_mood"])
    print(f"  track: {track}" if track else "  (geen muziek beschikbaar - render zonder)")

    print("[5/5] Render...")
    out_mp4 = out_dir / "test_one.mp4"
    render.assemble_video(
        clips=clips,
        voice_mp3=voice_mp3,
        music_mp3=track,
        ass_subs=ass_path,
        output_path=out_mp4,
        work_dir=work / "render",
    )
    print(f"\nKLAAR -> {out_mp4}")
    print(f"Grootte: {out_mp4.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
