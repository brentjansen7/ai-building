# TikTok Pipeline — Routeplanner

Volledig autonome video-generatie voor `@routeplanner.nl`. €0/maand. Brent doet ~10 min/week.

## Wat doet dit?

Genereert 21-28 unieke TikTok-videos per week. Stem, beeld, muziek, captions en uploadschema — allemaal automatisch. Brent uploadt 1× per week een batch in TikTok Studio.

---

## Eerste setup (eenmalig, ~30 min)

### 1. Python dependencies
```powershell
cd "marketing/tiktok_pipeline"
pip install -r requirements.txt
playwright install chromium
```

### 2. FFmpeg installeren
```powershell
winget install Gyan.FFmpeg
```
(Of via [ffmpeg.org](https://ffmpeg.org/download.html) als winget niet werkt. Zet de map waar ffmpeg.exe staat in je PATH.)

### 3. API keys (allebei gratis)
- **Pexels**: ga naar https://www.pexels.com/api/ → Sign up → Get API key
- **Pixabay** (optioneel, voor extra b-roll): https://pixabay.com/api/docs/ → Sign up

Hernoem `.env.example` naar `.env` en plak de keys erin.

### 4. Achtergrondmuziek downloaden
Maak twee mappen:
```
assets/music/upbeat/
assets/music/ambient/
```

Download ~10 tracks per mood van Pixabay Music (gratis, commercieel toegestaan):
- **Upbeat**: https://pixabay.com/music/search/genre/beats/
- **Ambient**: https://pixabay.com/music/search/genre/ambient/

Sleep MP3's naar de juiste map. Pipeline pakt random een track per video.

### 5. TikTok-account aanmaken
- Account: `@routeplanner.nl`
- Bio: "Routes klaar in 10 sec. Gratis tot 15 stops/dag." + link naar `https://brentjansen7.github.io/ai-building/routeplanner/`

---

## Wekelijkse run

### Maandagochtend (5 min)
```powershell
cd "marketing/tiktok_pipeline"
python src/run_week.py 1 2026-05-12
```

(Argument 1 = weeknummer, datum = startdatum maandag.)

Dit genereert de hele week aan video's in `output/week_1/`. Duur: ~30-45 min op een gewone PC.

### Daarna: TikTok Studio batch-upload (5 min)
1. Open https://www.tiktok.com/tiktokstudio/upload op desktop
2. Upload alle MP4's uit `output/week_1/`
3. Voor elke video:
   - Plak de caption uit `schedule.csv` (kolom `caption`)
   - Toggle **AI-generated content** aan (verplicht voor onze AI-stem)
   - Set schedule-tijd uit `schedule.csv` (max 10 dagen vooruit)
4. Save All

### Geautomatiseerd via Windows Task Scheduler
Optioneel: zet `run_week.py` als zondag-18:00 task. Dan staat de week-batch klaar voor maandagochtend.

```powershell
# Open Task Scheduler → Create Basic Task
# Trigger: Weekly, zondag 18:00
# Action: Start a program
# Program: pythonw.exe
# Arguments: src/run_week.py
# Start in: c:\Users\Naam Leerling\ai building brent jansen\marketing\tiktok_pipeline
```

---

## Posting cadens

| Week | Posts/dag | Tijden | Totaal |
|------|-----------|--------|--------|
| Week 1 | 3 | 08:00, 13:00, 19:00 | 21 |
| Week 2+ | 4 | 07:00, 12:00, 17:00, 20:30 | 28 |

(Beslissing 2026-05-09 — bewust ramp-up om shadowban te vermijden op nieuw account.)

---

## Mappen

```
marketing/tiktok_pipeline/
├── src/                  # Python pipeline modules
├── scripts/week_N.md     # gegenereerde scripts (lees baar)
├── scripts/week_N.json   # zelfde, voor pipeline-input
├── assets/
│   └── music/{upbeat,ambient}/   # Brent vult dit met Pixabay tracks
├── cache/                # gedownloade clips, voice-MP3's, work-files (gitignored)
├── output/week_N/        # finale MP4's + schedule.csv
└── tiktok_dashboard.md   # auto-rapport per run
```

---

## Troubleshooting

**`FFmpeg niet gevonden in PATH`**
Test in PowerShell: `ffmpeg -version`. Werkt het niet, herstart terminal of voeg `C:\Program Files\Gyan\FFmpeg\bin` toe aan PATH.

**`PEXELS_API_KEY ontbreekt`**
Controleer dat `.env` in `marketing/tiktok_pipeline/` staat (niet in `src/`) en dat de variabele exact zo heet.

**Pipeline draait maar `screen-rec failed`**
De selectoren in `src/broll_screenrec.py` matchen mogelijk niet met de huidige UI van de routeplanner. Pipeline gaat door met alleen Pexels b-roll. Fix later door de selectoren te updaten naar de echte ID's/classes uit `routeplanner-post/index.html`.

**Render duurt erg lang**
faster-whisper download eerste run het small-model (~244 MB). Daarna draait het sneller. CPU-render: ~2 min per video.

**Geen muziek in video**
`assets/music/{mood}/` is leeg. Pipeline rendert dan zonder achtergrondmuziek (alleen voice). Download tracks volgens stap 4.

---

## Wat te doen als TikTok views laag blijven

Na 2 weken < 1k views per video → niet stoppen, format-mix kantelen:
- Weeg `live_demo` zwaarder in `config.yml` (van 35 → 50)
- Probeer langere videos (35-45 sec) ipv 15-25
- Voeg trending TikTok-sound handmatig toe in TikTok Studio na upload (overschrijft Pixabay)
