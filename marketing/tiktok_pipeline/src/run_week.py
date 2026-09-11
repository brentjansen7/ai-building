"""Orchestrator: genereert N video's voor een week en maakt schedule.csv klaar voor TikTok-upload."""

import csv
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Lokale imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from script_generator import generate_week, save_scripts
import voice
import broll_pexels
import broll_screenrec
import captions
import music
import render

ROOT = Path(__file__).resolve().parent.parent


def _voice_text(s: dict) -> str:
    return f"{s['hook']}. {s['body']} {s['cta']}"


def _hashtags_str(hashtags: list, ai_label: bool = True) -> str:
    base = " ".join(hashtags)
    return base + (" #AIgenerated" if ai_label else "")


def _caption_for_post(s: dict) -> str:
    return f"{s['hook']}\n\n{s['body']}\n\n{s['cta']}\n\n{_hashtags_str(s['hashtags'])}"


def render_one_video(s: dict, week_dir: Path, work_root: Path, screenrec_cache: Path | None) -> Path | None:
    vid = s["id"]
    print(f"\n[{vid}] format={s['format']}  hook={s['hook'][:60]}...")

    work = work_root / vid
    work.mkdir(parents=True, exist_ok=True)

    # 1. Voice
    voice_mp3 = work / "voice.mp3"
    try:
        voice.synthesize(_voice_text(s), voice_mp3)
        print(f"  voice ok ({voice_mp3.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"  voice FAILED: {e}")
        return None

    # 2. B-roll
    clips = []
    if "screen_recording_routeplanner" in s["broll_keywords"] and screenrec_cache:
        if screenrec_cache.exists():
            clips.append(screenrec_cache)
        else:
            print("  screen-rec cache leeg, val terug op Pexels")

    pexels_kws = [k for k in s["broll_keywords"] if k != "screen_recording_routeplanner"]
    if pexels_kws:
        try:
            pexels_clips = broll_pexels.fetch_clips_for_keywords(pexels_kws, n_per_keyword=2)
            clips.extend(pexels_clips)
        except Exception as e:
            print(f"  pexels FAILED: {e}")

    if not clips:
        print("  geen b-roll clips beschikbaar — skip")
        return None

    # 3. Captions
    ass_path = work / "subs.ass"
    try:
        captions.mp3_to_ass(voice_mp3, ass_path)
        print(f"  captions ok")
    except Exception as e:
        print(f"  captions FAILED ({e}) — render zonder subs")
        ass_path = None

    # 4. Music
    track = music.pick_track(s.get("music_mood", "upbeat"))
    if track:
        print(f"  music: {track.name}")
    else:
        print(f"  geen muziek beschikbaar (assets/music/ leeg) — render zonder")

    # 5. Render
    out_mp4 = week_dir / f"{vid}.mp4"
    try:
        render.assemble_video(
            clips=clips,
            voice_mp3=voice_mp3,
            music_mp3=track,
            ass_subs=ass_path,
            output_path=out_mp4,
            work_dir=work / "render",
        )
        print(f"  RENDER OK -> {out_mp4.name} ({out_mp4.stat().st_size // 1024} KB)")
        return out_mp4
    except Exception as e:
        print(f"  RENDER FAILED: {e}")
        traceback.print_exc()
        return None


def write_schedule_csv(scripts: list, rendered: dict, week_dir: Path):
    csv_path = week_dir / "schedule.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "day", "post_time", "format", "caption", "hashtags", "ai_label"])
        for s in scripts:
            mp4 = rendered.get(s["id"])
            if not mp4:
                continue
            w.writerow([
                mp4.name,
                s["day"],
                s["time"],
                s["format"],
                _caption_for_post(s),
                " ".join(s["hashtags"]),
                "Ja",
            ])
    return csv_path


def write_dashboard(week_n: int, scripts: list, rendered: dict, week_dir: Path):
    dash = ROOT / "tiktok_dashboard.md"
    counts = {}
    for s in scripts:
        if s["id"] in rendered:
            counts[s["format"]] = counts.get(s["format"], 0) + 1

    with open(dash, "w", encoding="utf-8") as f:
        f.write(f"# TikTok Pipeline Dashboard\n\n")
        f.write(f"**Laatste run:** {datetime.now():%Y-%m-%d %H:%M}\n\n")
        f.write(f"**Week:** {week_n}\n\n")
        f.write(f"**Video's gerenderd:** {len(rendered)} / {len(scripts)}\n\n")
        f.write(f"## Format-verdeling deze week\n\n")
        for fmt, n in sorted(counts.items(), key=lambda x: -x[1]):
            f.write(f"- {fmt}: {n}\n")
        f.write(f"\n## Output locatie\n\n`{week_dir}`\n\n")
        f.write(f"## Volgende stap\n\n")
        f.write("Open TikTok Studio web -> Upload -> kies alle MP4's uit deze map -> ")
        f.write("kopieer captions uit `schedule.csv` -> AI-label aan -> schedule volgens tijden.\n")
    return dash


def run(week_n: int, start_date: datetime | None = None) -> Path:
    print(f"=== TikTok Pipeline — Week {week_n} ===\n")

    # 1. Genereer scripts
    if start_date is None:
        start_date = datetime.now()
    scripts_objs = generate_week(week_n, start_date)
    save_scripts(scripts_objs, week_n)
    scripts = [s.__dict__ for s in scripts_objs]
    print(f"Scripts: {len(scripts)}")

    # 2. Eenmalige screen-recording per week (hergebruikt voor live_demo videos)
    screenrec_cache = ROOT / "cache" / "screenrec" / f"week_{week_n}_demo.webm"
    if not screenrec_cache.exists():
        print("\n-> Eenmalige screen-recording van routeplanner...")
        try:
            broll_screenrec.record_routeplanner_demo(screenrec_cache, n_addresses=60)
            if screenrec_cache.exists():
                print(f"  screen-rec ok ({screenrec_cache.stat().st_size // 1024} KB)")
            else:
                print("  screen-rec failed — selectoren matchen mogelijk niet")
                screenrec_cache = None
        except Exception as e:
            print(f"  screen-rec exception: {e}")
            screenrec_cache = None

    # 3. Render alle videos
    week_dir = ROOT / "output" / f"week_{week_n}"
    week_dir.mkdir(parents=True, exist_ok=True)
    work_root = ROOT / "cache" / "work" / f"week_{week_n}"
    work_root.mkdir(parents=True, exist_ok=True)

    rendered = {}
    for s in scripts:
        mp4 = render_one_video(s, week_dir, work_root, screenrec_cache)
        if mp4:
            rendered[s["id"]] = mp4

    # 4. Schedule CSV + dashboard
    csv_path = write_schedule_csv(scripts, rendered, week_dir)
    dash_path = write_dashboard(week_n, scripts, rendered, week_dir)

    print(f"\n=== KLAAR ===")
    print(f"Gerenderd: {len(rendered)} / {len(scripts)}")
    print(f"Output:    {week_dir}")
    print(f"Schedule:  {csv_path}")
    print(f"Dashboard: {dash_path}")
    print(f"\n-> Open TikTok Studio en upload alle MP4's. AI-label toggle aan.")
    return week_dir


if __name__ == "__main__":
    week_n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start_str = sys.argv[2] if len(sys.argv) > 2 else None
    start = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
    run(week_n, start)
