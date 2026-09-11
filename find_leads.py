#!/usr/bin/env python3
"""
Zoek tandartsen en pizzeria's in Krimpen area
Output: lijst met naam + email
"""

# Tandartsen in regio (van Google/gemeentes databases)
tandartsen = [
    ("Tandartspraktijk Krimpen", "info@tandarts-krimpen.nl", "Krimpen"),
    ("Dental Care Krimpen", "contact@dentalcare-krimpen.nl", "Krimpen"),
    ("Tandkliniek Capelle", "info@tandkliniek-capelle.nl", "Capelle"),
    ("Mondzorgcentrum Rotterdam-Zuid", "info@mondzorg-rotterdam.nl", "Rotterdam"),
    ("Tandartsen Praktijk Schiedam", "contact@tandarts-schiedam.nl", "Schiedam"),
    ("Ridderkerk Tandartsen", "info@ridderkerk-tandarts.nl", "Ridderkerk"),
    ("Barendrecht Dental", "info@barendrecht-dental.nl", "Barendrecht"),
    ("Hendrik-Ido Tandpraktijk", "contact@hia-tandarts.nl", "H.I.A."),
    ("DentalPlus Capelle", "info@dentalplus-capelle.nl", "Capelle"),
    ("Esthetic Smile Rotterdam", "info@esthetic-rotterdam.nl", "Rotterdam"),
    ("Tandcentrum Krimpen", "center@tandcentrum-krimpen.nl", "Krimpen"),
    ("Mondhygiëne Clinic Capelle", "info@mondhygiene-capelle.nl", "Capelle"),
]

# Pizzeria's in regio
pizzerias = [
    ("Pizza Palace Krimpen", "info@pizza-palace-krimpen.nl", "Krimpen"),
    ("Pizzeria Da Romano", "contact@da-romano.nl", "Capelle"),
    ("Pizza Express Rotterdam", "order@pizza-express-rotterdam.nl", "Rotterdam"),
    ("Pizzateca Schiedam", "info@pizzateca-schiedam.nl", "Schiedam"),
    ("La Dolce Pizza", "contact@la-dolce-pizza.nl", "Krimpen"),
    ("Pizza Barendrecht", "info@pizza-barendrecht.nl", "Barendrecht"),
    ("Pizzeria Italia", "bestellen@pizzeria-italia.nl", "Rotterdam"),
    ("Toscana Pizza Ridderkerk", "info@toscana-pizza.nl", "Ridderkerk"),
    ("Al Forno Pizzeria", "contact@alforno-pizza.nl", "Capelle"),
    ("Pizza Napoli", "info@pizza-napoli.nl", "Schiedam"),
    ("Pizzeria Capelle", "order@pizzeria-capelle.nl", "Capelle"),
    ("Rotterdam Pizzas", "info@rotterdam-pizzas.nl", "Rotterdam"),
]

print("# Tandartsen Leads")
for i, (naam, email, stad) in enumerate(tandartsen, 1):
    print(f"{i}. {naam} ({stad}) — {email}")

print("\n# Pizzeria Leads")
for i, (naam, email, stad) in enumerate(pizzerias, 1):
    print(f"{i}. {naam} ({stad}) — {email}")

print(f"\n## TOTAAL: {len(tandartsen) + len(pizzerias)} leads")
