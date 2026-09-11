# TikTok Automation — Onderzoek & Plan

Datum: 2026-05-09
Doel: 4 video's per dag, elke dag, voor de routeplanner. €0/maand. Brent doet zo min mogelijk.

---

## TL;DR — De gekozen stack

| Onderdeel | Tool | Kosten | Waarom |
|-----------|------|--------|--------|
| Stem (TTS) | **edge-tts** (Microsoft Edge neural TTS) | €0 | Geen API key, Nederlandse stemmen (Colette, Maarten, Fenna), goede kwaliteit |
| B-roll video | **Pexels API** + **Playwright screen-recordings** | €0 | Pexels: gratis stock van koeriers/auto's. Playwright: maakt unieke demo's van de routeplanner zelf |
| Achtergrondmuziek | **Pixabay Music** | €0 | Gratis commercieel, geen attribution, "TikTok no copyright" categorie |
| Captions (woord-voor-woord) | **faster-whisper** (small model) | €0 | Lokaal op CPU, Nederlandse taal, word-timestamps |
| Video render | **FFmpeg** + **MoviePy** | €0 | Industriestandaard, alles wat we nodig hebben |
| Script-generator | **Claude / Python templates** | €0 | Ik schrijf 28 unieke scripts per week |
| Posten naar TikTok | **TikTok Studio web-scheduler** (handmatig 1×/week, 5 min) | €0 | Geen developer account-approval (5-10 dagen) nodig, geen TOS-risico |
| Hosting/orchestratie | Brent's PC + Windows Task Scheduler | €0 | Wanneer PC aanstaat draait pipeline; videos worden 1×/week geüpload |

**Totale kosten: €0/maand. Brent's tijd: ~10 min/week (5 min batch-uploaden, 5 min checken).**

---

## 1. Onderzoek per dimensie

### 1.1 Text-to-Speech (TTS)

**Gekozen: edge-tts** (Python lib, lib versie 7.2.8 maart 2026, actief onderhouden).

**Waarom:**
- 100% gratis, geen API-key, geen rate-limit voor onze volumes (~120 video's/maand)
- Microsoft's neural voices, kwaliteit ≈ ElevenLabs starter-tier
- Native Nederlandse stemmen:
  - `nl-NL-ColetteNeural` (vrouw, neutraal, warm)
  - `nl-NL-MaartenNeural` (man, vriendelijk)
  - `nl-NL-FennaNeural` (vrouw, jonger)
- Ondersteunt SSML tags voor pauzes, emfase, snelheid
- Open source (MIT), runs op Windows

**Alternatieven overwogen:**
- ElevenLabs: $22/maand voor onze volume → afgewezen (kost geld)
- Coqui TTS: lokaal model, kwaliteit ok maar setup zwaar (~2GB models)
- Piper TTS: lichter alternatief, NL voices ok maar minder natuurlijk dan Edge
- gTTS (Google Translate): robotachtig, niet voor 2026 brand-niveau

### 1.2 B-roll video

**Gekozen: dubbele bron**
1. **Pexels API** voor stock-video van koeriers, pakketten, auto's, kaarten — gratis met key
2. **Playwright screen-recordings** voor unieke demo's van de routeplanner zelf (open browser → plak 50 nep-adressen → klik optimaliseer → opname start → klaar in 30s)

**Waarom screen-recordings cruciaal zijn:**
- TikTok-algoritme straft duplicate content; stock-only = lage reach
- "Het echte product in actie" converteert beter dan stockfoto's met tekst
- Playwright kan in Python met `record_video_dir` parameter de hele browser-sessie naar MP4 opnemen (officiële feature)

**Alternatieven:**
- Pixabay video: backup-bron, ook gratis
- Coverr / Mixkit: gratis maar geen API → handmatig downloaden, minder schaalbaar

### 1.3 Achtergrondmuziek

**Gekozen: Pixabay Music**
- 170.000+ tracks, gratis voor commercieel gebruik, geen attribution
- API beschikbaar (gratis key)
- Aparte "TikTok no copyright" categorie
- Pas op: TikTok eigen sound library bevat trending audio die de algoritme boost. Pixabay-muziek geeft minder boost maar is veilig (geen copyright-claim).

**Strategie:** voor video's met gesproken AI-stem → Pixabay achtergrond op laag volume (-20 dB). Voor stille split-screen video's → Brent kan optioneel handmatig een trending TikTok-sound toevoegen via TikTok Studio (komt na render).

### 1.4 Captions (woord-voor-woord highlight)

**Gekozen: faster-whisper (small/base model)**
- Open-source Whisper-implementatie, runs lokaal op CPU
- `word_timestamps=True` levert per-woord timing → karaoke-style highlight captions
- Nederlandse taal-detectie werkt out-of-the-box
- Small model (~244MB) volstaat voor onze duidelijke AI-stem

**Output:** SRT-bestand met word-timings → FFmpeg `subtitles` filter met ASS-styling voor TikTok-look (witte tekst, gele highlight op huidig woord, dikke shadow).

### 1.5 Video-rendering

**Gekozen: FFmpeg via Python subprocess + MoviePy voor complexe scènes**
- FFmpeg: alles-in-één video processor, gratis, super snel
- MoviePy: Python wrapper als de FFmpeg-commando-string te complex wordt
- Output: 1080×1920 MP4 (TikTok native), 30fps, H.264

**Pipeline per video:**
```
b-roll clips concat → +AI voice-over (edge-tts) → +Pixabay music (-20dB)
  → faster-whisper transcribe → ASS-subtitle overlay → AI-label disclaimer
  → final MP4 (15-45 sec)
```

### 1.6 Posten naar TikTok — de kritische beslissing

**Drie paden onderzocht:**

| Pad | Voordeel | Nadeel | Kosten |
|-----|----------|--------|--------|
| A. **TikTok Content Posting API + Postiz self-hosted** | Volledig autonoom, geen weekly werk | 5-10 dagen developer-approval; unaudited apps mogen alleen SELF_ONLY (privé) posten tot audit; vereist publieke HTTPS-site met file-upload-verificatie | €0 maar weken setup |
| B. **TikTok Studio web-scheduler** (handmatig batch) | Geen approval, geen TOS-risico, posts gaan 100% publiek live, native scheduling | Brent uploadt 1× per week ~28 video's (~5 min) | €0 |
| C. **Buffer free tier** | Officiële integratie | Slechts 10 posts/maand → niet genoeg voor 4/dag | €0 maar onbruikbaar |
| D. **Browser-automation (Playwright) op TikTok-web** | "Echt 0 minuten" voor Brent | Tegen TikTok TOS, ban-risico, niet aanbevolen | €0 |

**Gekozen: Pad B nu, Pad A zodra Phase-2 (na 5 betalende klanten)**

**Reden:** Postiz API-route kost weken om operationeel te krijgen vóór Brent z'n eerste video kan posten. Elke dag uitstel = minder content = minder views = minder klanten. TikTok Studio scheduler doet exact wat we nodig hebben, ondersteunt 7-15 dagen vooruit plannen, en kost Brent 5 min per week. Dat is acceptabel.

Pad A blijft op de roadmap voor wanneer het volume relevant wordt.

### 1.7 Posting-cadens — kritisch voor shadowban-preventie

**Onderzoek:** TikTok-algoritme verwacht voor nieuwe accounts in eerste 2-3 weken **1-3 posts per dag**, met 2-4 uur tussenruimte. Direct beginnen met 4-5/dag triggert spam-detectie en kan een nieuw account in shadowban-modus zetten (2-4 weken laag bereik, geen notificatie).

**Beslissing Brent (2026-05-09): tussenweg cadens**

| Week | Posts/dag | Tijden | Cumulatief |
|------|-----------|--------|------------|
| Week 1 | 3 | 8:00, 13:00, 19:00 | 21 video's |
| Week 2+ | 4 | 7:00, 12:00, 17:00, 20:30 | 28 video's/week |

**Account:** `@routeplanner.nl` (product-gericht, SEO-vriendelijk).

### 1.8 AI-content disclosure (TikTok regels 2026)

**Onderzoek:** TikTok Community Guidelines vereisen "AI-generated content" toggle bij:
- Realistische AI-portretten van mensen → JA
- Synthetische stem (zoals onze edge-tts AI voice) → grijs gebied, advies: **ja toggelen**

**Goed nieuws:** label heeft GEEN negatieve impact op reach (officieel TikTok-standpunt). Niet labelen heeft wel risico (auto-gedetecteerd → demoting).

**Oplossing:** in elke upload via TikTok Studio toggle "AI-generated" aan. Brent doet dit één klik per video tijdens de wekelijkse batch-upload.

---

## 2. De pipeline architectuur

```
┌────────────────────────────────────────────────────────────────────┐
│  Op Brent's PC, draait elke zondag om 18:00 (Windows Task Scheduler) │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────┐
        │  run_week.py — orchestrator              │
        │  Genereert 28 video's voor komende week  │
        └──────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌──────────────┐         ┌──────────────────┐        ┌──────────────────┐
│ scripts.py   │         │ broll.py         │        │ voice.py          │
│ Claude-      │         │ - Pexels API     │        │ - edge-tts NL     │
│ generated    │         │ - Playwright     │        │ - SSML pauzes     │
│ 28 scripts   │         │   screen-rec     │        │ - MP3 output      │
└──────────────┘         └──────────────────┘        └──────────────────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   ▼
                       ┌──────────────────────┐
                       │ captions.py          │
                       │ - faster-whisper     │
                       │ - SRT word timings   │
                       │ - ASS karaoke style  │
                       └──────────────────────┘
                                   │
                                   ▼
                       ┌──────────────────────┐
                       │ render.py            │
                       │ - FFmpeg combineert  │
                       │   alles + Pixabay    │
                       │   muziek -20dB       │
                       │ - Output 1080x1920   │
                       │   MP4 H.264          │
                       └──────────────────────┘
                                   │
                                   ▼
                       ┌──────────────────────┐
                       │ output/week_N/       │
                       │ ├─ ma_07.mp4         │
                       │ ├─ ma_12.mp4         │
                       │ ├─ ... 28 totaal     │
                       │ └─ schedule.csv      │
                       └──────────────────────┘
                                   │
                                   ▼
                       ┌──────────────────────┐
                       │  Brent: 5 min/week   │
                       │  TikTok Studio web   │
                       │  → Schedule          │
                       │  → AI-label aan      │
                       └──────────────────────┘
```

---

## 3. Mappen-structuur

```
marketing/tiktok_pipeline/
├── README.md                    # quickstart voor Brent
├── RESEARCH_AND_PLAN.md         # dit document
├── requirements.txt             # python deps
├── .env.example                 # API keys template
├── .env                         # echte keys (gitignored)
├── config.yml                   # tone, hashtags, posting times
├── scripts/
│   ├── week_1.md                # 28 scripts in markdown
│   └── week_2.md
├── src/
│   ├── run_week.py              # orchestrator
│   ├── script_generator.py      # template-based variation
│   ├── voice.py                 # edge-tts wrapper
│   ├── broll_pexels.py          # Pexels stock fetcher
│   ├── broll_screenrec.py       # Playwright recorder van routeplanner
│   ├── captions.py              # faster-whisper + ASS-styling
│   ├── music.py                 # Pixabay music picker
│   ├── render.py                # FFmpeg orchestration
│   └── upload_helper.py         # genereert schedule.csv voor Brent
├── assets/
│   ├── fonts/                   # TikTok-style font (Montserrat Bold)
│   ├── intros/                  # 1-sec brand intro met logo
│   └── outros/                  # CTA outro template
├── cache/
│   ├── pexels/                  # gedownloade stock-clips
│   └── music/                   # gedownloade muziek-clips
└── output/
    ├── week_1/
    │   ├── ma_08_post1.mp4
    │   ├── schedule.csv         # bevat: filename, datum, tijd, caption, hashtags
    │   └── thumbnails/          # screenshot frame voor preview
    └── week_2/
```

---

## 4. Content-strategie (voorkomt duplicate-content shadowban)

### 4.1 Vijf format-types — rouleren per dag
1. **Live demo** (35%) — screen-recording routeplanner: "Kijk wat 80 adressen doet in 10 sec"
2. **Voor/na split-screen** (20%) — links Google Maps chaos, rechts onze planner
3. **Pijn-punt storytelling** (20%) — koerier-b-roll, AI voice vertelt over "die ene klant die te lang wacht"
4. **Cijfer-hooks** (15%) — vol-scherm cijfers ("7 uur per week", "30% sneller", "€19/mnd")
5. **POV / "een dag uit het leven"** (10%) — koerier ochtend → met onze tool vs zonder

### 4.2 Hook-bibliotheek (rouleren, nooit hetzelfde 2× achter elkaar)
- "Een 16-jarige bouwde dit voor zijn eigen postroute"
- "PostNL/DHL-bezorgers, kijk dit even"
- "Waarom rijden bezorgers nog steeds met print-lijsten in 2026?"
- "Dit kost €19/mnd en bespaart je 1 uur per dag"
- "Een koerier verspilt 7 uur per week aan deze fout"
- "Gratis tool die elke koerier zou moeten kennen"
- "Dit doe je verkeerd als bezorger"
- "Hoe ik 100 pakketten in 30 seconden sorteer"

### 4.3 CTA's (afwisselend)
- "Link in bio — gratis proberen"
- "Zoek 'Automade routeplanner' op Google"
- "Reageer 'route' voor de link"
- "Comment 'send' — stuur ik 'm in DM"

### 4.4 Hashtags (maximaal 4 per video, mix van groot/niche)
- Groot: #koerier #pakketbezorger #postnl #dhl #zzp
- Niche: #bezorgservice #routeoptimalisatie #ai #automatisering
- Lokaal: #krimpen #rotterdam #zuidholland

---

## 5. Stappenplan — uitvoering (volgorde)

### Stap 1 — Folder + dependencies (15 min, geen Brent-input)
- Maak `marketing/tiktok_pipeline/` met submappen
- Schrijf `requirements.txt`: `edge-tts`, `faster-whisper`, `playwright`, `moviepy`, `requests`, `pyyaml`, `python-dotenv`
- Schrijf `.env.example` met `PEXELS_API_KEY=` en `PIXABAY_API_KEY=`
- Schrijf `config.yml` met posting-tijden, hooks, hashtags

### Stap 2 — Script generator (30 min)
- `script_generator.py`: combineert `hook × format × CTA × variabele cijfers` → unieke scripts
- Output: `scripts/week_1.md` met 28 scripts in vast format (titel, hook, body, CTA, b-roll-keyword, format-type)

### Stap 3 — Voice module (15 min)
- `voice.py`: edge-tts wrapper, neemt script-tekst → MP3 met `nl-NL-FennaNeural` (jonge stem, past bij Brent-positionering "16 jaar")
- Test: 1 voorbeeld-MP3 genereren

### Stap 4 — B-roll modules (45 min)
- `broll_pexels.py`: download per script-keyword 3-5 clips, cachen
- `broll_screenrec.py`: Playwright opent `https://brentjansen7.github.io/routeplanner-post/`, plakt nep-adressen via JavaScript, klikt optimaliseer, neemt context op → MP4
  - Vereist: 50 nep-Krimpen-adressen lijst (kan ik genereren via Nominatim API)

### Stap 5 — Captions module (20 min)
- `captions.py`: faster-whisper laadt small-model lazily, transcribeert MP3 → SRT met word-timings
- ASS-styling: witte Montserrat Bold 60pt, gele highlight op huidig woord, zwarte shadow
- Test: 1 voice-MP3 → SRT → preview

### Stap 6 — Music module (10 min)
- `music.py`: lijst van 20 vooraf gedownloade Pixabay tracks (uplifting/corporate/upbeat), random pick per video
- Brent moet 1× ze downloaden (instructie in README)

### Stap 7 — Render module (45 min)
- `render.py`: FFmpeg-pipeline:
  1. Concat b-roll-clips → 1 video stream
  2. Mix voice + music (voice 0dB, music -20dB)
  3. Burn ASS-subtitles in
  4. Resize naar 1080×1920, 30fps
  5. Output `mp4` met yuv420p H.264
- Test: 1 complete video van begin tot eind

### Stap 8 — Orchestrator (30 min)
- `run_week.py`: laadt scripts/week_N.md → loopt over 28 scripts → roept voice/broll/captions/music/render aan → output naar `output/week_N/`
- Genereert `schedule.csv` met geplande post-tijden conform week-cadens
- Logt naar `output/week_N/run_log.txt`

### Stap 9 — Brent's upload-werkblad (15 min)
- `README.md` in `marketing/tiktok_pipeline/`: 5-stappen quickstart voor Brent
  1. `pip install -r requirements.txt`
  2. Edit `.env` met Pexels-key
  3. Download Pixabay-tracks (link-lijst)
  4. Run `python src/run_week.py`
  5. Open TikTok Studio → upload alles uit `output/week_N/` → schedule volgens `schedule.csv` → AI-label aan

### Stap 10 — Eerste batch genereren + dry-run (1 uur)
- Run pipeline voor week 1 (14 video's, ramp-up cadens)
- Brent checkt 2 video's op kwaliteit
- Brent doet eerste TikTok-batch-upload

### Stap 11 — Windows Task Scheduler (10 min)
- Zet `run_week.py` als task elke zondag 18:00
- Zorgt dat zondagavond automatisch alle video's voor de komende week klaar staan
- Brent doet maandagochtend de upload

### Stap 12 — Wekelijkse rapportage (auto)
- Na elke `run_week.py` schrijft de pipeline `marketing/tiktok_dashboard.md` met:
  - Aantal video's gegenereerd
  - Welke hooks/formats gebruikt
  - Post-schedule
  - (Later) views/clicks gescraped van TikTok analytics

---

## 6. Wat Brent moet doen

### Eenmalig (~30 min totaal)
1. **Pexels API key** aanmaken op pexels.com/api → toevoegen aan `.env` (5 min)
2. **TikTok-account** aanmaken `@brent.bouwt` of `@automade.routes` (5 min)
3. **FFmpeg installeren**: `winget install Gyan.FFmpeg` in PowerShell (5 min)
4. **Python 3.11+** check (waarschijnlijk al geïnstalleerd)
5. **Pixabay-tracks downloaden**: 20 tracks via link-lijst → `assets/music/` (15 min)

### Wekelijks (~10 min)
1. **Maandagochtend**: open TikTok Studio web → upload 14-28 video's uit `output/week_N/` → kopieer captions uit `schedule.csv` → AI-label toggle aan → schedule volgens tijden → save (5 min)
2. **Vrijdag**: kort kijken naar dashboard, eventueel hook-feedback aan Claude geven (5 min)

### Niets meer
- Geen scripts schrijven, geen video-edit, geen filming, geen voice-overs

---

## 7. Risico's en mitigaties

| Risico | Kans | Impact | Mitigatie |
|--------|------|--------|-----------|
| Shadowban op nieuw account door 4/dag direct | Hoog | Hoog | Ramp-up 2→3→4/dag over 3 weken (zie §1.7) |
| TikTok klassificeert AI-content als ongelabeld → demote | Middel | Middel | AI-toggle bij elke upload aan |
| FFmpeg installatie mislukt op Brent's PC | Laag | Hoog | Backup: stap-voor-stap troubleshooting in README + `winget` als primair pad |
| Pexels API rate-limit | Laag | Laag | Cachen wat we al gedownload hebben in `cache/pexels/` |
| Edge-TTS Microsoft trekt service in | Laag | Hoog | Backup: pre-genereer veelgebruikte zinnen, fallback naar Piper TTS |
| Playwright crasht op screen-recording | Middel | Middel | Try/except rond elke recording, val terug op pure Pexels-mix |
| Brent vergeet wekelijks uploaden | Middel | Hoog | Notificatie via Notion-page elke maandagochtend met checklist |
| Content wordt repetitief → reach daalt | Middel | Hoog | Format-rotatie + hook-bibliotheek + 5 verschillende b-roll-pools per format |

---

## 8. Succes-metrics (eerste 30 dagen)

| Week | Mijlpaal |
|------|----------|
| Week 1 | Pipeline draait; 14 video's live; eerste video met >1k views |
| Week 2 | 21 video's live; 1 video met >5k views; eerste signups via TikTok-link |
| Week 3 | 28 video's live; 1 video met >20k views; >50 free signups; 1 betalende klant |
| Week 4 | Format optimaliseren op winners; conversie naar Premium >2% |

**Failure-trigger:** als na week 2 geen enkele video meer dan 1k views haalt → format/hook reset, mogelijk content-niche aanpassen (bv. zzp-ondernemers ipv specifiek koeriers).

---

## 9. Wat NIET in deze fase

Bewust uitgesteld tot na klant 1-5:
- **Postiz self-hosted setup** (vereist TikTok dev-account, weken werk)
- **Volledig autonoom posten** (TOS-risico, weeg na validatie)
- **AI-video generators (Runway, Sora)** (kost geld + AI-content-detectie risico)
- **Real-time trending-sound integratie** (handmatig betere keuze tot dev-account er is)
- **Cross-posten naar Instagram Reels / YouTube Shorts** (focus eerst TikTok)

---

## Sources

- [edge-tts on PyPI](https://pypi.org/project/edge-tts/) — current version 7.2.8 (March 2026)
- [edge-tts GitHub](https://github.com/rany2/edge-tts)
- [TikTok Content Posting API docs](https://developers.tiktok.com/products/content-posting-api/)
- [TikTok Posting API Developer Guide 2026](https://zernio.com/blog/tiktok-developer-api)
- [How to Schedule TikToks in 2026 (Without Shadowbans)](https://posteverywhere.ai/blog/how-to-schedule-tiktoks)
- [Postiz GitHub](https://github.com/gitroomhq/postiz-app)
- [Postiz TikTok docs](https://docs.postiz.com/providers/tiktok)
- [TikTok Shadow Ban 2026 Guide](https://www.shopify.com/blog/tiktok-shadow-ban)
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [Playwright Python Video Recording](https://playwright.dev/python/docs/videos)
- [Pixabay API](https://pixabay.com/service/about/api/)
- [TikTok AI Content Labeling 2026](https://www.auditsocials.com/blog/tiktok-ai-content-disclosure-rules-2026)
- [Best Free Social Media Scheduling Tools 2026](https://posteverywhere.ai/blog/best-free-social-media-scheduling-tools)
