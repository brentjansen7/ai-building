# Juridische Aandachtspunten — Vastgoed AI Dealfinder

⚠️ **Dit is geen juridisch advies. Raadpleeg een advocaat voor specifieke situaties.**

---

## 🔍 Web Scraping

### Pararius, Jaap.nl, Huislijn.nl

**Status**: ⚠️ Grijze zone (juridisch complex in Nederland)

**Huidige Compliance:**
- ✅ Respect voor `robots.txt`
- ✅ Rate limiting (2-8s delays)
- ✅ No overload (max 20 listings/min per site)
- ✅ No personal data extraction
- ✅ No bot blocking circumvention
- ✅ User-agent honesty

**Risico's:**
- ⚠️ **ToS Violation**: Websites verbieden scraping expliciet
  - Pararius ToS: "automated access prohibited"
  - Jaap.nl ToS: "no scraping or bots"
  - Huislijn ToS: "no automated collection"

- ⚠️ **Account bans**: IP-adres geblokkeerd
  - Mitigation: Proxy rotation (Bright Data, Oxylabs)

- ⚠️ **Rechtszaak**: Theoretisch mogelijk (onwaarschijnlijk)
  - Nederlandse rechtbank: "lightweight scraping" voor private use meestal OK
  - Commercial use: risico hoger

**Aanbevelingen:**
1. **Niet aanmoedigen** als business model (risk vs reward)
2. **Proxy service** gebruiken (verhult je origin)
3. **Rate limiting** strikt handhaven
4. **ToS respecteren** waar mogelijk
5. **Disclaimer** op website: "Data uit publieke sources"
6. **Gebruikersakkoord** dat ze ToS accepteren

---

## 📋 WOZ Data & BAG

### Status: ✅ Volledig Legal

WOZ (Waarde Onroerende Zaken) waarden zijn **publieke Nederlandse overheidsdata**.

**Bronnen:**
- ✅ BAG API (Kadaster) — Gratis, publiek
- ✅ wozwaardeloket.nl — Openbaar, geen ToS restricties
- ✅ CBS (Centraal Bureau voor Statistiek) — Publieke datasets
- ✅ NVM transactiedata — Anoniem gepubliceerd

**Geen restricties**:
- Geen licentie nodig
- Geen copyright
- Geen GDPR issues (niet persoonlijk)
- Mag commercieel gebruikt worden

**Voorzichtigheid:**
- Combineer niet met persoonlijke info (GDPR risk)
- Attributeer originele bron waar ethisch
- Geen "Kadaster Unauthorized" claim

---

## 🔐 GDPR & Privacy

### Adressen

**Beschouwing**: Half-publiek (niet persoonlijk)

```
Persoonsgegevens?
├── Adres ALLEEN → Nee (publiek)
├── Adres + Naam → Ja (GDPR)
├── Adres + ID → Ja (GDPR)
└── Adres + Photos → Ja (GDPR)
```

**Compliance:**
- ✅ Store ONLY: {address, postcode, price, analysis}
- ✅ NO: Eigenaar naam/contact
- ✅ NO: Huisnummer + deur
- ✅ NO: Foto's archiveren
- ✅ NO: User tracking/profiling

**Retention:**
- Max 12 maanden (oude listings)
- Auto-delete na 24 maanden
- Right to deletion: 30 dagen

**Transparency:**
- Privacy policy op website
- Duidelijk: "Adressen uit publieke bron"
- Geen verstopte tracking

---

## 💼 Business Model

### Scenario's & Risico's

#### Scenario 1: Personal Use (Laag risico ✅)
- Jij analyzeert woningen voor jezelf
- Private API key
- Geen verkoop van data
- **Status**: ✅ Legal, geen aandachtspunten

#### Scenario 2: Affiliate/Lead Gen (Middelmatig risico ⚠️)
- Analyseer listings → sell referrals naar agents/investors
- Scraping ToS violation risk
- Privacy: OK (adressen zijn semi-public)
- **Aanbeveling**: Gebruik legale data bronnen (Funda API, BAG)

#### Scenario 3: Saas Platform ($, Hoog risico ⚠️)
- Bied analyse-tool aan via subscription
- Scraping → legal exposure
- Competitor vragen mogelijk
- **Aanbeveling**: Partnership met property sites (Funda API license)

#### Scenario 4: Aggregator/Portal (Zeer hoog risico 🚫)
- Crawl alle sites → maak eigen portal
- **Risico**: Direct ToS violation + copetitor lawsuit
- **Aanbeveling**: Don't do this

---

## 📄 Disclaimers & Liabilities

### Aanbevolen Website Disclaimer

```
⚠️ DISCLAIMER

Dit systeem analyseert openbare woningadvertenties van derden.

GEEN GARANTIES:
- Analyses zijn indicatief, geen investeringsadvies
- Prijzen kunnen onjuist/verouderd zijn
- Renovatiekosten zijn schattingen (niet bindend)
- Deal scores zijn algoritme-gebaseerd, geen professioneel advies

EIGENAAR-VERANTWOORDELIJKHEID:
- Eigen onderzoek doen (bezichtiging, inspectie)
- Juridisch advies raadplegen (advocaat)
- Financieel advies raadplegen (accountant)
- Niet verantwoordelijk voor verlies/schade

DATA SOURCES:
- Analyses gebaseerd op publieke data
- WOZ waarden van wozwaardeloket.nl (Overheid)
- Huisprijzen van NVM/Funda datasets
- Foto's van originele advertenties

EIGENDOM:
- Dit product is NOT affiliated met Pararius, Jaap, Huislijn, Funda
- Alle merken zijn eigendom van hun respectieve houders
```

---

## ⚖️ Contractuele Bescherming

### Terms of Service (TOS)

Wat te vermelden in je TOS:

1. **Scraping Clause**
   ```
   "Dit systeem analyseert data van derden websites.
   Gebruiker aanvaardt alle ToS van originele bron.
   Wij zijn niet verantwoordelijk voor account-bans.
   Proxy-gebruik is risico gebruiker."
   ```

2. **Liability Disclaimer**
   ```
   "Analyses zijn voor informatief doel.
   Geen investeringsadvies.
   Geen garantie op nauwkeurigheid.
   Alle risico's gebruiker."
   ```

3. **Fair Use**
   ```
   "No commercial redistribution of scraped data.
   No framing/embedding proprietary content.
   Analysis output = your own use only."
   ```

---

## 🏦 Accountant & Belastingen

### NL Belastingaspecten

- ✅ **Scraping data**: Niet belastbaar (gratis)
- ✅ **Analysis output**: Jouw eigendom (marktvaardig)
- ⚠️ **Affiliate income**: Belastbaar (IB/vpB)
- ⚠️ **Saas subscriptions**: Belastbaar (omzetbelasting)

**Registratie:**
- Solo operator: KvK "Diensten aan ondernemingen"
- vennootschap: BV/NV (kosten vs. risico afweging)

---

## 🤝 Partnerships & Licenties

### Funda API (Official)

Funda biedt API voor agents (registration required):

```
- Voordelen: ✅ 100% legal, ✅ Officieel
- Nadelen: ⚠️ €200-500/maand, ⚠️ Agent-only
- Alternative: Affiliate program (commissies)
```

### Pararius / Jaap

- ❌ Geen official API
- ❌ Geen affiliate program
- ⚠️ Scraping risico

**Strategy**: Focus op legal alternatives (Funda, BAG, CBS).

---

## 🚨 If You Get Legal Notice

Wat doen als je een cease-and-desist ontvangt?

1. **Panikeer niet** (gebeurt zelden)
2. **Forward naar advocaat** (niet zelf antwoorden)
3. **Zet scraper uit** (stop immediately)
4. **Pas analyses aan** (use only legal data)
5. **Document everything** (logs, screenshots)

**Advocate budget**: €500-2000 voor first review

---

## ✅ Compliance Checklist

- [ ] Privacy policy op website
- [ ] Disclaimer op analyses
- [ ] TOS inclusief scraping clause
- [ ] Geen persoonlijke data (NO adressen + namen)
- [ ] Robot.txt respected
- [ ] Rate limiting enabled
- [ ] Proxy rotation (waar applicable)
- [ ] GDPR: 12 maand retention, auto-delete
- [ ] Right to deletion process
- [ ] Data processing agreement (if B2B)
- [ ] Insurance (werkgever aansprakelijkheid)
- [ ] Accountant advies (belastingen)

---

## 🔗 Nuttige Resources

- 🇳🇱 **NVWA** (Autoriteit Consument & Markt) — Bot guidelines
- 🇳🇱 **Kadaster BAG API** — Legal property data
- 🇳🇱 **CBS Statline** — Legal statistics
- 🇪🇺 **GDPR.eu** — Privacy regulations
- 🔗 **robots.txt** specification — Scraping etiquette

---

## Final Recommendation

**For your use case (deal analysis):**

✅ **Legal path:**
1. Use BAG/WOZ/CBS public data (official)
2. Build analysis engine
3. Sell as B2B SaaS (no scraping)

⚠️ **Medium-risk path:**
1. Scrape with strong anti-detection (proxies, delays)
2. Limit to personal/small team use
3. Expect potential blocks/ToS violation

🚫 **Avoid:**
1. Commercial resale of scraped data
2. High-volume scraping (>100K/day without permission)
3. Circumventing anti-bot measures
4. Personal data extraction

**Bottom line**: Profiteer van legale data bronnen. Scraping is juridisch riskant in NL.

---

*Laatste update: 2025-03*
