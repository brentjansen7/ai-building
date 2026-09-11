# Cold Email Template — EXACT DEZE STRUCTUUR
# Toon: PERSOONLIJK, WARM, Brent 16 jaar — NIET AI-GEGENEREERD
# Lengte: ~120-130 woorden (3-4 alinea's)
# GEEN SHORTCUTS! VOLG EXACT!
#
# ⚠️ VERPLICHT VOORAF: doorloop `ceo/solution_matcher.md` (5 stappen)
# en kies de oplossing uit `ceo/solution_catalog.md`.
# Ga NIET op branche-naam af. Ga op workflow-type af.
# Fout uit verleden: A&A Thuiszorg kreeg een routeplanner terwijl ze met vaste afspraken werken → had planningssoftware moeten zijn.

Onderwerp: Korte vraag van een lokale scholier — {{BEDRIJFSNAAM}}

---

Hey {{VOORNAAM / "team van " + BEDRIJFSNAAM}},

{{SPECIFIEKE_OPENING: 1-2 zinnen DIRECT van hun website/Google — hun unieke selling point, niet generiek}}

Ik ben Brent, 16 jaar, lokale ondernemer uit Krimpen. Ik heb onlangs voor {{REFERENTIE_KLANT}} {{REFERENTIE_PRODUCT_BESCHRIJVING}}.

Voor {{BEDRIJFSNAAM}} zie ik een vergelijkbare kans: {{CONCRETE_TOEPASSING}}. {{HERHAALDE_PIJN_PUNT}}.

Of zijn er misschien nog andere dingen bij jullie die veel tijd kosten en waarbij je denkt: dit zou software eigenlijk kunnen doen?

Zou je even willen reageren? Ook als het "nee" is — dan hoor ik dat ook graag!

Bekijk wat ik heb gebouwd: {{BRANCHE_URL}}

Groetjes, Brent
brentjansen.ai.building@gmail.com

---
# CRITICAL RULES — DEZE BREKEN = SLECHTE EMAIL:

1. **SPECIFIEKE OPENING** (niet generiek): 
   - GOED: "Ik zag dat jullie sinds '85 custom energiesystemen bouwt — van biogas tot aggregaten"
   - FOUT: "Ik zag dat jullie een bedrijf bent"
   - FOUT: "Jullie doen interessante dingen"

2. **REFERENTIE_PRODUCT_BESCHRIJVING**: 
   - GOED: "voor Spanino Pizza een systeem gebouwd dat feestverzoeken en facturen automatisch afhandelt"
   - GOED: "voor Kuiper & Koning Fysiotherapie een AI-tool gebouwd die SOAP-verslagen schrijft in seconden"
   - FOUT: "een AI-tool gemaakt"
   - FOUT: "een system gebuild"

3. **CONCRETE_TOEPASSING**: 
   - GOED: "offertes of technische rapporten automatisch opstellen op basis van projectinput"
   - GOED: "routeplanner gebouwd die adressen inscant en automatisch de snelste route berekent"
   - FOUT: "AI-tool die orderverwering automatiseert"
   - FOUT: "iets om je efficient te maken"

4. **HERHAALDE_PIJNPUNT**: Noem spesifiek wat ze TIME/MONEY kosten
   - GOED: "zodat jouw engineers minder tijd kwijt zijn aan paperwerk"
   - GOED: "scheelt hen echt veel administratiewerk"
   - FOUT: weglaten of generiek houden

5. **TONE**: 
   - Warm, persoonlijk, korte zinnen
   - "Groetjes" niet "Met vriendelijke groet"
   - Eigen woordkeuze — niet te glad/polish

6. **NEVER**:
   - Portfolio → noem het "wat ik heb gebouwd"
   - Verzoek agenda link → CTA = "reageer op deze mail"
   - Meerdere applicaties → ÉÉN toepassing per email

---
# VOORBEELD CORRECT INGEVULD (Pizzeria):

Hey team van La Dolce Pizza,

Ik zag dat jullie authentieke Italiaanse pizza maken met handgemaakte deeg en verse ingrediënten — dat soort kwaliteit vraagt ook om de juiste workflow.

Ik ben Brent, 16 jaar, lokale ondernemer uit Krimpen. Ik heb onlangs voor Spanino Pizza een systeem gebouwd dat feestverzoeken en facturen automatisch afhandelt.

Voor La Dolce Pizza zie ik iets vergelijkbaars: je orders en reserveringen automatisch verwerken + administratie — zodat jij meer tijd hebt voor wat je echt wil: goede pizza maken.

Of zijn er misschien nog andere dingen bij jullie die veel tijd kosten en waarbij je denkt: dit zou software eigenlijk kunnen doen?

Zou je even willen reageren? Ook als het "nee" is — dan hoor ik dat ook graag!

Bekijk wat ik heb gebouwd: https://brentjansen7.github.io/ai-building/horeca

Groetjes, Brent
brentjansen.ai.building@gmail.com

---
# INSTRUCTIES VOOR INVULLEN:
# {{VOORNAAM}}: voornaam indien bekend, anders "team van [naam]"
# {{SPECIFIEKE_OPENING}}: Onderzoek hun website — wat is UNIEK aan hen? (oprichtingsjaar, proces, motto, specialiteit)
# {{REFERENTIE_KLANT}}: uit doelgroepen.json → [sector].referentie_klant
# {{REFERENTIE_PRODUCT_BESCHRIJVING}}: uit doelgroepen.json → [sector].referentie_uitwerking (LANG versie, niet kort)
# {{CONCRETE_TOEPASSING}}: Denk: wat kost DIT bedrijf veel tijd? (facturen, agenda, orders, rapportage?)
# {{HERHAALDE_PIJNPUNT}}: Wat TIME/MONEY scheelt het hen?
# {{BRANCHE_URL}}: uit doelgroepen.json → [sector].branche_url
