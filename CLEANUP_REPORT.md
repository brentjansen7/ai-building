# Notion Marketing Leads Database Cleanup Report
**Date:** 2026-03-31
**Status:** COMPLETED

---

## TASK 1: DUPLICATE REMOVAL

### Duplicates Identified & Marked for Deletion: 6 entries

#### 1. De Pee Logistiek (3 entries originally)
- **KEEP:** 331ee788-bbec-813b-aca8-e28c762a877e (2026-03-28, Status: Verstuurd)
- **MARKED DELETE:** 32cee788-bbec-81d0-a917-e8ae9cfa33cf (2026-03-23, Status: Follow-up verstuurd)
- **MARKED DELETE:** 330ee788-bbec-81a6-9741-f62c871eb158 (2026-03-27, Status: Concept gemaakt)

#### 2. Wex Holland (2 entries)
- **KEEP:** 331ee788-bbec-816b-827b-da0cab34706a (2026-03-28, Status: geen interesse)
- **MARKED DELETE:** 330ee788-bbec-8168-b668-cd61ef4ee49a (2026-03-27, Status: Concept gemaakt)

#### 3. Berger Koerierservice (2 entries)
- **KEEP:** 331ee788-bbec-8156-9abd-c733b888d4d3 (2026-03-28, Status: Verstuurd)
- **MARKED DELETE:** 330ee788-bbec-811d-a47c-d86671086860 (2026-03-27, Status: Concept gemaakt)

#### 4. A. Hak Transport (2 entries)
- **KEEP:** 331ee788-bbec-8196-b89f-f0b51f6df3a8 (2026-03-28, Status: Verstuurd)
- **MARKED DELETE:** 330ee788-bbec-81fa-9ba7-f8c37843c905 (2026-03-27, Status: Concept gemaakt)

#### 5. Blonk Logistiek Transport (2 entries)
- **KEEP:** 331ee788-bbec-810b-98f3-f7822d07e346 (2026-03-28, Status: Verstuurd)
- **MARKED DELETE:** 32cee788-bbec-81f1-8ce7-c0ec4d07cda6 (2026-03-23, Status: Verstuurd - older version)

#### 6. TAB Transport (1 entry - no duplicate)
- **KEEP:** 331ee788-bbec-8185-996b-e101924f42ac (2026-03-28, Status: geen interesse)

#### Special Cases - KEPT BOTH (different contact addresses):

**Restaurant Perceel (2 different emails - BOTH KEPT):**
- 32aee788-bbec-819d-8a7c-f9a046b7381c (2026-03-21, Email: info@restaurantperceel.nl, Status: Gereageerd)
- 331ee788-bbec-81af-b42e-d7c0f021163b (2026-03-28, Email: restaurantperceel@gmail.com, Status: geen interesse)

**Restaurant De Loet (2 different emails - BOTH KEPT):**
- 32aee788-bbec-8140-a147-d6fd73b6b5ae (2026-03-21, Email: info@deloet.nl, Status: geen interesse)
- 331ee788-bbec-8105-970a-c3e01e0797de (2026-03-28, Email: restaurantdeloet@gmail.com, Status: geen interesse)

---

## TASK 2: SEND DATES FILLED

### Entries Updated with "Datum verstuurd" (from Gmail send dates):

| Company | Email | Date Filled | Status |
|---------|-------|------------|--------|
| De Pee Logistiek | planning@depeelogistiek.nl | 2026-03-24 | Verstuurd |
| Berger Koerierservice | info@bergerkoerierservice.nl | 2026-03-31 | Verstuurd |
| A. Hak Transport | info@haktransport.nl | 2026-03-31 | Verstuurd |
| Blonk Logistiek Transport | msprincess@live.nl | 2026-03-23 | Verstuurd |
| Restaurant Perceel (info@) | info@restaurantperceel.nl | 2026-03-27 | Gereageerd |
| Restaurant Perceel (gmail) | restaurantperceel@gmail.com | 2026-03-28 | geen interesse |
| Restaurant De Loet (info@) | info@deloet.nl | 2026-03-27 | geen interesse |
| Restaurant De Loet (gmail) | restaurantdeloet@gmail.com | 2026-03-28 | geen interesse |

**Total dates filled: 8 entries**

---

## TASK 3: VERIFICATION SUMMARY

### Duplicates Marked for Deletion: 6
- De Pee Logistiek: 2 duplicates marked
- Wex Holland: 1 duplicate marked
- Berger Koerierservice: 1 duplicate marked
- A. Hak Transport: 1 duplicate marked
- Blonk Logistiek Transport: 1 duplicate marked
- TAB Transport: 0 duplicates (kept single entry)

### Send Dates Filled: 8
- 4 entries with Status "Verstuurd" now have Datum verstuurd
- 4 entries with different emails (restaurants) also updated with send dates

### Quality Checks:
✓ All duplicate companies identified from task description processed
✓ Most recent entries (highest "Datum toegevoegd") retained in all cases
✓ Different contact addresses (Restaurant Perceel & De Loet) preserved as separate entries
✓ All Gmail send dates matched correctly to Notion entries
✓ All Datum verstuurd fields populated with accurate dates

### Notes:
- 6 duplicate pages are marked with "DUPLICATE - VERWIJDERD" in Notities field
- These pages need manual deletion via Notion UI (three-dot menu → Delete)
- Alternatively, can be deleted via Notion API with proper authorization token
- After deletion, database will contain only 1 entry per bedrijf (except restaurants with 2 legitimate contact addresses)

---

**Action Required:** Manually delete the 6 pages marked as DUPLICATE in Notion, or provide API token for automated deletion.
