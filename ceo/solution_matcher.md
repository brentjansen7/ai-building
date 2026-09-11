# Solution Matcher — VERPLICHT STAPPENPLAN voor cold email

## Doel
Voorkomen dat er een oplossing wordt voorgesteld die niet past bij wat het bedrijf ECHT doet.
Historische fout: aan A&A Thuiszorg werd een routeplanner voorgesteld, terwijl thuiszorg werkt met vaste afspraken per cliënt → planning is het pijnpunt, niet route-optimalisatie.

## Verplichte stappen (in deze volgorde)

### STAP -1 — VERPLICHTE LEAD-VERIFICATIE (doe dit ALTIJD als eerste, vóór STAP 0)
Zie `ceo/lead_verification.md`. Bedrijf moet bestaan + email moet uit echte bron komen, niet geraden.
Als verificatie faalt → SKIP, geen email.

### STAP 0 — VERPLICHTE DUPLICAAT-CHECK (doe dit na STAP -1, vóór de rest)
Voer voor elke kandidaat-lead VIER checks uit. Eén hit = SKIP.

**Gmail SENT (3 aparte queries — geen subject-filter, geen pageSize-limit):**
1. `label:sent to:[exact emailadres]` — vangt zelfde mailbox
2. `label:sent [emaildomein]` (zonder @) bijv. `label:sent groenebeek.nl` — vangt andere mailbox op zelfde domein (kantoor@ vs info@)
3. `label:sent [unieke bedrijfsnaam-keyword]` ZONDER subject-filter — vangt eerdere mails met afwijkende subjects (bijv. "AI-tool voor logopedie-verslagen" ipv standaard "Korte vraag…")

**Notion (1 query):**
4. Zoek op bedrijfsnaam in Marketing Leads database.

Als één van de vier een hit geeft → **SKIP direct**. Geen email, geen draft, geen Notion entry.
Geldt voor VOLLEDIGE history, niet recent venster. NOOIT pageSize-limit op deze checks zetten.

**Historische fouten:**
- 22 april 2026: 3 dubbelen gemist omdat alleen recente dagrapportages gecheckt werden (Fysiotherapie Ridderkerk, Vuik Logistics, Eetcafé De Crimpenaar 4x).
- 5 mei 2026: 6 dubbelen gemist omdat eerste dedup-zoekopdracht filterde op subject "Korte vraag van een lokale scholier" + pageSize 50 (FysioVitaal 20 mrt, Fysio Schiedam Noord 22 apr, Top Koeriers 21 apr, Logopedie HIA 1 mei met afwijkend subject, Centrum Apotheek Schiedam 1 mei met afwijkend subject, Groenebeek 17 apr op kantoor@ ipv info@).

**Verboden shortcuts bij dedup:**
- ❌ Eén globale subject-filtered scan — mist afwijkende subjects en oudere mails
- ❌ pageSize beperken tot 30/50 — mist mails buiten venster
- ❌ Alleen op @info-adres checken — mist mails op kantoor@/contact@/planning@ etc.

### STAP 1 — Wat doen ze PRECIES? (workflow-analyse)
Lees hun website en beantwoord alle 5 vragen letterlijk op papier:
1. **Wie zijn hun klanten?** (bedrijven, particulieren, instellingen, ouderen, …)
2. **Wat leveren ze?** (product, dienst, uur-werk, project-werk)
3. **Hoe vaak interactie per klant?** (eenmalig, wekelijks, dagelijks, vast schema)
4. **Waar gebeurt het werk?** (op locatie bij klant, eigen zaak, onderweg, remote)
5. **Wie doet het werk?** (eigenaar solo, vast team, flex-personeel, chauffeurs, monteurs)

**Stop als een van deze 5 niet duidelijk is uit hun website.** Niet raden.

### STAP 2 — Welk workflow-type is dit?
Match het antwoord op STAP 1 aan één workflow-type uit solution_catalog.md.
Het is bijna nooit "de branche" die bepaalt — het is de workflow.

### STAP 3 — Welke oplossing past bij dit workflow-type?
Pak uit solution_catalog.md de juiste oplossing.
Check: "klopt de oplossing met STAP 1 antwoorden?" Als niet → terug naar STAP 2.

### STAP 4 — Sanity check (VERPLICHT — sla nooit over)
Beantwoord deze 3 vragen hardop:
- **a.** Klopt mijn oplossing met hoe ze hun dagen/weken plannen?
- **b.** Wat is het grootste OPERATIONELE probleem? (niet marketing/sales — operationeel)
- **c.** Als ik eigenaar was van dit bedrijf: zou ik dit kopen?

Als één van deze drie twijfelachtig is → andere oplossing kiezen.

### STAP 5 — Pas dan pas de email schrijven
Gebruik `templates/cold_email.md` met de gevonden oplossing.

## Voorbeelden

### ✅ A&A Thuiszorg (goed)
- STAP 1: klanten = ouderen thuis | levert = zorg in uren | frequentie = vast schema/meerdere x per week | waar = bij cliënt thuis | wie = team zorgverleners
- STAP 2: workflow-type = **terugkerende afspraken met vast team bij vaste klanten**
- STAP 3: oplossing = **planningssoftware** (rooster, ziekte-invallers, dienstenruil, cliëntverdeling)
- STAP 4a: ja ze plannen op vaste tijden ✓ / 4b: grootste pijn = uitval personeel & roosterpuzzel ✓ / 4c: ja planner kopen ✓

### ❌ A&A Thuiszorg (fout die gemaakt is)
- "Thuiszorg gaat naar adressen → routeplanner!" → 4a faalt: routes zijn al vast, niet optimaliseerbaar. Fout dus.

### ✅ Fysiotherapiepraktijk
- STAP 1: klanten = patiënten | levert = behandeling 25-30 min | frequentie = 1-10x per traject | waar = eigen praktijk | wie = fysio's solo
- STAP 2: workflow-type = **klant-op-afspraak met verslaglegging per sessie**
- STAP 3: oplossing = **AI SOAP-verslag** (verslag per sessie is wettelijk verplicht + kost tijd)

### ✅ Pakketbezorger met 80 stops/dag
- STAP 1: klanten = ontvangers (wisselend) | levert = pakket | frequentie = eenmalig per adres | waar = onderweg | wie = chauffeur
- STAP 2: workflow-type = **veel stops per dag zonder vast patroon**
- STAP 3: oplossing = **routeplanner** (scheelt 30-90 min/dag)

### ✅ Restaurant
- STAP 1: klanten = gasten | levert = gerechten | frequentie = wisselend | waar = eigen zaak | wie = eigenaar + keuken
- STAP 2: workflow-type = **inkomende orders & administratie naast kerntaak**
- STAP 3: oplossing = **order/factuur-automatisering** (tijd terug voor keuken)

## NOOIT
- Oplossing kiezen op basis van branche-naam alleen
- Routeplanner voorstellen als hun route al vast ligt
- SOAP-verslag voorstellen aan bedrijven zonder verslagplicht
- Order-automatisering voorstellen zonder hoog orderaantal
- Een oplossing voorstellen zonder STAP 1 ingevuld te hebben

## Edge cases

### Als GEEN van de 9 types past
→ SKIP deze lead. Geen email sturen. Beter geen email dan een foute.
(Voorbeeld: verhuisbedrijf — workflow past nergens op een van de 9 types waarvoor wij echt pijn verlichten.)

### Als MEERDERE types passen
→ Kies het type met de HOOGSTE frequentie-pijn. Regel: "wat doen ze elke dag/week meerdere uren?" wint van "wat doen ze soms".
(Voorbeeld: restaurant = kan type 5 én 9 zijn. Bij kleine zaak = 5 (orders/admin dagelijks). Bij vers-eetcafé met veel weggooi = 9.)
Noem in de email ÉÉN toepassing, niet twee.

### Als je twijfelt over STAP 1
→ Niet raden. Lees hun website grondiger, of skip de lead. Een verkeerde aanname = verkeerde oplossing = verbrande lead.
