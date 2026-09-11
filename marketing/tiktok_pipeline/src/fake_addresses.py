"""Echte Krimpen aan den IJssel + Rotterdam-zuid straatnamen voor demo screen-recordings.
Geen echte huisnummers/personen — alleen straatnaam + plaats + postcode-prefix.
"""

DEMO_ADDRESSES = [
    # Krimpen aan den IJssel
    "Raadhuisplein 2, Krimpen aan den IJssel",
    "Lekkenburg 12, Krimpen aan den IJssel",
    "Boveneind 5, Krimpen aan den IJssel",
    "Tiendweg 8, Krimpen aan den IJssel",
    "Hoflaan 3, Krimpen aan den IJssel",
    "IJsseldijk 50, Krimpen aan den IJssel",
    "Schoolstraat 14, Krimpen aan den IJssel",
    "Rotterdamseweg 100, Krimpen aan den IJssel",
    "Nieuwe Tiendweg 22, Krimpen aan den IJssel",
    "Stormpolder 5, Krimpen aan den IJssel",
    "Industrieweg 30, Krimpen aan den IJssel",
    "Kortland 18, Krimpen aan den IJssel",
    "Memlinghof 7, Krimpen aan den IJssel",
    "Couperuslaan 25, Krimpen aan den IJssel",
    "Fonteyn 11, Krimpen aan den IJssel",
    # Capelle aan den IJssel
    "Bernardplein 5, Capelle aan den IJssel",
    "Slotplein 12, Capelle aan den IJssel",
    "Centrumpassage 18, Capelle aan den IJssel",
    "Hoofdweg 80, Capelle aan den IJssel",
    "Wormerhoek 3, Capelle aan den IJssel",
    # Rotterdam zuid
    "Beijerlandselaan 100, Rotterdam",
    "Putselaan 50, Rotterdam",
    "Slinge 25, Rotterdam",
    "Zuidplein 20, Rotterdam",
    "Pleinweg 10, Rotterdam",
    "Lange Hilleweg 80, Rotterdam",
    "Carnisselaan 15, Rotterdam",
    "Bloemfonteinstraat 22, Rotterdam",
    "Coolhaven 12, Rotterdam",
    "Wolphaertsbocht 5, Rotterdam",
    # Ridderkerk
    "Koningsplein 8, Ridderkerk",
    "Rijnsingel 30, Ridderkerk",
    "Vlietlaan 18, Ridderkerk",
    "Donkerslootweg 12, Ridderkerk",
    # Hendrik-Ido-Ambacht
    "Kerkplein 5, Hendrik-Ido-Ambacht",
    "Nijverheidsweg 25, Hendrik-Ido-Ambacht",
    "Antoniuslaan 14, Hendrik-Ido-Ambacht",
    "Van Godewijckstraat 8, Hendrik-Ido-Ambacht",
    # Schiedam
    "Hoogstraat 50, Schiedam",
    "Lange Haven 10, Schiedam",
    "Broersvest 25, Schiedam",
    "Singel 30, Schiedam",
    # Vlaardingen
    "Markt 1, Vlaardingen",
    "Westhavenkade 80, Vlaardingen",
    "Oranjeplein 4, Vlaardingen",
    "Liesveld 12, Vlaardingen",
    # Maassluis
    "Markt 12, Maassluis",
    "Veerstraat 8, Maassluis",
    "Noorddijk 18, Maassluis",
    "Westlandseweg 30, Maassluis",
]


def sample(n: int = 60) -> list[str]:
    import random
    return random.sample(DEMO_ADDRESSES, min(n, len(DEMO_ADDRESSES)))
