"""Genereert per week N unieke TikTok-scripts uit hooks, formats, CTAs."""

import json
import random
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"


@dataclass
class Script:
    id: str
    week: int
    day: str
    time: str
    format: str
    hook: str
    body: str
    cta: str
    broll_keywords: list
    music_mood: str
    hashtags: list
    ai_label: bool = True


BODY_TEMPLATES = {
    "live_demo": [
        "Ik plak {n} adressen, klik op optimaliseer, en de route staat in {sec} seconden klaar. Geen Google Maps gepuzzel meer.",
        "Kijk wat {n} pakketten doet als je ze in de juiste volgorde rijdt. Bespaart {min} minuten elke ochtend.",
        "Dit is mijn echte postroute van vandaag. {n} stops, klaar in {sec} seconden, route klopt in een keer.",
    ],
    "before_after": [
        "Links: handmatig in Google Maps. Rechts: routeplanner. Zelfde adressen, {pct} procent minder kilometers.",
        "Voor: 30 minuten puzzelen op de bank. Na: 10 seconden. Zelfde resultaat, andere ochtend.",
        "Dit is wat 80 procent van de bezorgers nog steeds doet. En dit is wat ik doe sinds vorige maand.",
    ],
    "pain_point": [
        "Klant nummer 3 wacht een half uur omdat de bezorger eerst nummer 14 doet. Dat is geen pech, dat is slechte route.",
        "Bezorgers verspillen gemiddeld {hours} uur per week aan slecht geplande routes. Dat is bijna een hele werkdag.",
        "Niets is zo frustrerend als zien dat je drie keer langs hetzelfde punt rijdt. Bij {n} stops is dat geld.",
    ],
    "numbers_hook": [
        "{hours} uur per week. Dat verspilt een gemiddelde koerier aan handmatig routes plannen.",
        "{pct} procent. Zoveel kilometer minder als je je route optimaal rijdt.",
        "19 euro per maand. Een uur per dag besparen. Dat is meer dan 240 euro per maand minder werk.",
    ],
    "pov_day": [
        "Ochtend bij een koerier zonder routeplanner: print, sorteren, hopen dat je niks vergeet. Met routeplanner: open de app, klik, rijden.",
        "Mijn ochtend voor de routeplanner: 45 minuten plannen op de bank. Mijn ochtend nu: nul minuten.",
        "Een dag uit het leven van een bezorger met de juiste tools. Spoiler: je rijdt eerder thuis.",
    ],
}


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def pick_format(formats):
    weights = [f["weight"] for f in formats.values()]
    names = list(formats.keys())
    return random.choices(names, weights=weights, k=1)[0]


def fill_body(template: str) -> str:
    return template.format(
        n=random.choice([50, 60, 70, 80, 90, 100, 120]),
        sec=random.choice([8, 10, 12, 15]),
        min=random.choice([20, 30, 45, 60]),
        pct=random.choice([15, 20, 25, 30, 35]),
        hours=random.choice([5, 6, 7, 8]),
    )


def make_broll_keywords(format_name: str, hook: str) -> list:
    base = {
        "live_demo": ["screen_recording_routeplanner"],
        "before_after": ["screen_recording_routeplanner", "google maps screen"],
        "pain_point": ["delivery van", "courier package", "stressed driver"],
        "numbers_hook": ["money counting", "clock fast", "delivery van"],
        "pov_day": ["morning coffee delivery", "courier loading van", "package delivery"],
    }
    return base.get(format_name, ["delivery van"])


def make_hashtags(cfg) -> list:
    primary = random.sample(cfg["hashtags"]["primary"], 2)
    secondary = random.sample(cfg["hashtags"]["secondary"], 1)
    local = random.sample(cfg["hashtags"]["local"], 1)
    return primary + secondary + local


def generate_week(week_number: int, start_date: datetime) -> list:
    cfg = load_config()
    schedule_key = "week_1" if week_number == 1 else "week_2_plus"
    sched = cfg["posting_schedule"][schedule_key]
    posts_per_day = sched["posts_per_day"]
    times = sched["times"]

    used_hooks = []
    scripts = []

    for day_offset in range(7):
        day_date = start_date + timedelta(days=day_offset)
        day_name = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"][day_date.weekday()]
        for slot in range(posts_per_day):
            available_hooks = [h for h in cfg["hooks"] if h not in used_hooks[-4:]]
            hook = random.choice(available_hooks)
            used_hooks.append(hook)

            fmt = pick_format(cfg["formats"])
            body_template = random.choice(BODY_TEMPLATES[fmt])
            body = fill_body(body_template)
            cta = random.choice(cfg["ctas"])

            script = Script(
                id=f"w{week_number}_d{day_offset+1}_s{slot+1}",
                week=week_number,
                day=f"{day_name} {day_date.strftime('%d-%m')}",
                time=times[slot],
                format=fmt,
                hook=hook,
                body=body,
                cta=cta,
                broll_keywords=make_broll_keywords(fmt, hook),
                music_mood="upbeat" if fmt in ("live_demo", "before_after", "numbers_hook") else "ambient",
                hashtags=make_hashtags(cfg),
            )
            scripts.append(script)
    return scripts


def save_scripts(scripts: list, week_number: int):
    out_md = ROOT / "scripts" / f"week_{week_number}.md"
    out_json = ROOT / "scripts" / f"week_{week_number}.json"
    out_md.parent.mkdir(exist_ok=True)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in scripts], f, indent=2, ensure_ascii=False)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# Week {week_number} TikTok Scripts\n\n")
        f.write(f"Aantal: {len(scripts)} videos\n\n---\n\n")
        for s in scripts:
            f.write(f"## {s.id} — {s.day} {s.time}\n\n")
            f.write(f"**Format:** {s.format}\n\n")
            f.write(f"**Hook:** {s.hook}\n\n")
            f.write(f"**Body:** {s.body}\n\n")
            f.write(f"**CTA:** {s.cta}\n\n")
            f.write(f"**Voice-over tekst (volledige):**\n> {s.hook}. {s.body} {s.cta}\n\n")
            f.write(f"**B-roll keywords:** {', '.join(s.broll_keywords)}\n\n")
            f.write(f"**Music mood:** {s.music_mood}\n\n")
            f.write(f"**Hashtags:** {' '.join(s.hashtags)}\n\n")
            f.write("---\n\n")
    return out_md, out_json


if __name__ == "__main__":
    import sys
    week_n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    start_str = sys.argv[2] if len(sys.argv) > 2 else None
    start = datetime.strptime(start_str, "%Y-%m-%d") if start_str else datetime.now()
    scripts = generate_week(week_n, start)
    md, js = save_scripts(scripts, week_n)
    print(f"Generated {len(scripts)} scripts -> {md}")
