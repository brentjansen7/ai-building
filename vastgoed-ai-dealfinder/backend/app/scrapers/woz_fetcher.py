import aiohttp
import asyncio
from typing import Optional, Dict
import structlog
import re

logger = structlog.get_logger()


class WOZFetcher:
    """Haal WOZ waarden op via publieke Nederlandse APIs."""

    # BAG (Basisregistraties Adressen en Gebouwen) API - gratis, publiek
    BAG_API_BASE = "https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2"

    # WOZ Waardeloket - publieke lookup
    WOZ_LOKET_BASE = "https://www.wozwaardeloket.nl/wozwaardeloket/api"

    # CBS Statline - buurtprijzen statistieken
    CBS_BASE = "https://opendata.cbs.nl/ODataApi/odata"

    def __init__(self, bag_api_key: Optional[str] = None):
        self.bag_api_key = bag_api_key

    async def get_woz(self, address: str, postcode: str) -> Optional[Dict]:
        """
        Haal WOZ waarde op voor een adres.
        Probeert meerdere bronnen in volgorde.
        """

        # 1. Probeer via WOZ Waardeloket (meest accuraat, gratis)
        woz = await self._fetch_woz_waardeloket(postcode, address)
        if woz:
            return woz

        # 2. Fallback: schat via buurtgemiddelden
        woz = await self._estimate_from_cbs(postcode)
        if woz:
            return {**woz, "estimated": True}

        logger.warning("WOZ niet gevonden", address=address, postcode=postcode)
        return None

    async def _fetch_woz_waardeloket(self, postcode: str, address: str) -> Optional[Dict]:
        """
        Haal WOZ op via WOZ Waardeloket API.
        Let op: dit is een publieke API met rate limits.
        """
        try:
            # Normaliseer postcode
            clean_postcode = postcode.upper().replace(" ", "")
            huisnummer_match = re.search(r"\b(\d+)\b", address)
            huisnummer = huisnummer_match.group(1) if huisnummer_match else "1"

            async with aiohttp.ClientSession() as session:
                # Zoek via postcode + huisnummer
                url = f"{self.WOZ_LOKET_BASE}/wozobjecten"
                params = {
                    "postcode": clean_postcode,
                    "huisnummer": huisnummer,
                }
                headers = {"Accept": "application/json"}

                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Verwerk respons
                        if data and "wozObjecten" in data:
                            objects = data["wozObjecten"]
                            if objects:
                                obj = objects[0]
                                waarden = obj.get("wozWaarden", [])

                                if waarden:
                                    # Pak meest recente waarde
                                    meest_recent = sorted(waarden, key=lambda x: x.get("peildatum", ""), reverse=True)[0]
                                    return {
                                        "woz_value": int(meest_recent.get("vastgesteldeWaarde", 0)),
                                        "woz_year": int(meest_recent.get("peildatum", "2024")[:4]),
                                        "source": "wozwaardeloket",
                                        "estimated": False,
                                    }

        except Exception as e:
            logger.warning("WOZ Waardeloket fout", error=str(e))

        return None

    async def _estimate_from_cbs(self, postcode: str) -> Optional[Dict]:
        """
        Schat WOZ via CBS buurtdata als fallback.
        Geeft een ruwe schatting terug op basis van de postcode.
        """
        try:
            postcode4 = postcode[:4] if len(postcode) >= 4 else postcode

            # CBS heeft gemiddelde WOZ waarden per postcode4
            async with aiohttp.ClientSession() as session:
                url = f"{self.CBS_BASE}/83295NED/UntypedDataSet"
                params = {
                    "$filter": f"PostcodeHuisnummerreeks eq '{postcode4}'",
                    "$select": "GemiddeldeWOZWaardeVanWoningen_1, Perioden",
                    "$top": "1",
                    "$format": "json"
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        value = data.get("value", [])
                        if value and value[0].get("GemiddeldeWOZWaardeVanWoningen_1"):
                            woz_avg = int(value[0]["GemiddeldeWOZWaardeVanWoningen_1"]) * 1000
                            year = str(value[0].get("Perioden", "2023"))[:4]
                            return {
                                "woz_value": woz_avg,
                                "woz_year": int(year),
                                "source": "cbs_estimate",
                                "estimated": True,
                            }

        except Exception as e:
            logger.warning("CBS WOZ schatting fout", postcode=postcode, error=str(e))

        return None

    async def get_neighborhood_prices(self, postcode: str) -> Optional[Dict]:
        """
        Haal gemiddelde prijzen op voor de buurt via CBS/BAG data.
        Geeft prijs per m² en gemiddelde verkoopprijs.
        """
        try:
            postcode4 = postcode[:4] if len(postcode) >= 4 else postcode

            async with aiohttp.ClientSession() as session:
                # CBS vastgoedprijzen per postcode
                url = f"{self.CBS_BASE}/83625NED/UntypedDataSet"
                params = {
                    "$filter": f"RegioS eq '{postcode4}'",
                    "$select": "GemiddeldeVerkoopprijs_1, Perioden",
                    "$top": "5",
                    "$orderby": "Perioden desc",
                    "$format": "json"
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        values = data.get("value", [])
                        if values:
                            avg_price = int(values[0].get("GemiddeldeVerkoopprijs_1", 0)) * 1000
                            return {
                                "avg_sale_price": avg_price,
                                "postcode4": postcode4,
                                "source": "cbs",
                                "year": str(values[0].get("Perioden", "2023"))[:4],
                            }

        except Exception as e:
            logger.warning("Buurtprijzen fout", postcode=postcode, error=str(e))

        # Fallback: stadsgemiddelden (hard-coded als nood fallback)
        return None

    async def get_bag_details(self, address: str, postcode: str) -> Optional[Dict]:
        """
        Haal BAG (basisregistratie) details op voor een adres.
        Gratis API van het Kadaster.
        """
        if not self.bag_api_key:
            return None

        try:
            clean_postcode = postcode.upper().replace(" ", "")
            huisnummer_match = re.search(r"\b(\d+)\b", address)
            huisnummer = int(huisnummer_match.group(1)) if huisnummer_match else 1

            async with aiohttp.ClientSession() as session:
                url = f"{self.BAG_API_BASE}/adressen"
                params = {
                    "postcode": clean_postcode,
                    "huisnummer": huisnummer,
                    "exacteMatch": "true",
                }
                headers = {
                    "X-Api-Key": self.bag_api_key,
                    "Accept": "application/hal+json",
                }

                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        embedded = data.get("_embedded", {})
                        adressen = embedded.get("adressen", [])
                        if adressen:
                            adres = adressen[0]
                            return {
                                "bag_id": adres.get("adresseerbaarObjectIdentificatie"),
                                "bouwjaar": adres.get("bouwjaar"),
                                "gebruiksdoel": adres.get("gebruiksdoelen", []),
                                "oppervlakte": adres.get("oppervlakte"),
                                "pandstatus": adres.get("pandstatus"),
                            }

        except Exception as e:
            logger.warning("BAG API fout", address=address, error=str(e))

        return None
