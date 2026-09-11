# Lead Verificatie — VERPLICHTE STAP -1 (vóór solution_matcher.md)

## Doel
Voorkomen dat er emails worden gegenereerd voor bedrijven die niet bestaan of waar het emailadres geraden is.

## Historische fout (april 2026)
25 emails in één week gebounced omdat:
- Bedrijfsnamen waren verzonnen (Pizza Palace Krimpen, Toscana Pizza Ridderkerk, DentalPlus Capelle — bestaan niet)
- Domeinen waren geraden (`pizza-napoli.nl`, `tandarts-krimpen.nl` — bestaan niet)
- Emailformat was geraden (`info@`, `contact@` zonder bron)

→ Tijd verspild + sender reputation schade.

## Verplichte verificatie (in deze volgorde, vóór alles)

### STAP -1A — Bestaat het bedrijf?
Zoek op Google: `"[exacte bedrijfsnaam]" "[stad]"`

**MOET hits geven op minstens één van:**
- Eigen website (.nl domein dat ook echt opent)
- Google Business profiel (Google Maps listing)
- KvK / OpenKvK
- LinkedIn pagina

**Geen hits = bedrijf bestaat niet (of niet onder die naam) → SKIP.**

Niet raden welke naam ze "waarschijnlijk hebben". Niet "het zal vast wel ergens een tandartspraktijk in Krimpen zijn". Exact die naam, of niets.

### STAP -1B — Werkend emailadres ophalen
Het emailadres moet komen uit één van deze bronnen:

1. **Hun eigen website** — contact-pagina, footer, "over ons"
2. **Google Business** — als email daar staat ingevuld
3. **KvK/OpenKvK** — als email daar staat
4. **LinkedIn** — bedrijfspagina contact

**NOOIT:**
- Email format raden (`info@bedrijfsnaam.nl`, `contact@bedrijfsnaam.nl`)
- Domein raden op basis van bedrijfsnaam
- "Het zal wel `info@` zijn" — nee, kijken

### STAP -1C — Domein-check
Open de website één keer in browser/WebFetch. Als die niet laadt (`ECONNREFUSED`, cert error, 404) → SKIP. Dood bedrijf of dood domein = dood lead.

### STAP -1D — Naam vs domein cross-check
Het emaildomein moet matchen met de website van het bedrijf.

❌ Fout (gebeurd):
- Bedrijf: Brasserie Stadhuis → email geraden: `brasserie@stadhuis.nl` → domein bestaat niet
- Bedrijf: De Beren → email geraden: `barendrecht@deberengroep.nl` → domein bestaat niet (echt: `beren.nl`)

✅ Goed:
- Website opent op `brasseriestadhuis.nl` → email vinden op die site → `info@brasseriestadhuis.nl`

## Pas hierna door naar solution_matcher.md
Zonder STAP -1 verificatie: GEEN email genereren. Geen draft. Geen Notion entry.

## Quick rejection rules
SKIP de lead direct als:
- Naam is generiek/verzonnen klinkend ("Pizza Palace", "DentalPlus", "Barendrecht Dental")
- Geen Google hits op exacte naam
- Website laadt niet
- Email moet geraden worden

## Checklist (verplicht doorlopen per lead)
```
[ ] Exacte bedrijfsnaam gegoogled → hits gevonden
[ ] Website opent zonder error
[ ] Email gevonden op website/Google Business/KvK (NIET geraden)
[ ] Emaildomein matcht website-domein
[ ] Door naar solution_matcher.md STAP 0
```

Als één vinkje mist: SKIP.
