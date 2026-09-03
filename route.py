# -*- coding: utf-8 -*-
"""Overnachtingsplaatsen van de Pyreneeënreis, 4 t/m 27 september 2026.

Coordinaten komen uit de eigen Google My Maps-kaart "Pyreneeen 2026 Gedeeld".
Per etappe geldt: 'van' t/m 'tot' is de periode waarin je op die plek slaapt,
dus rustdagen horen bij de camping waar je al stond.
"""

TITEL = "Pyreneeën 2026"

# De dagen thuis staan hier bewust niet in. De pagina is openbaar bereikbaar
# en hoeft niet te vermelden wanneer het huis leegstaat; buiten de reisdagen
# ziet het dashboard dus simpelweg geen overnachting.
ROUTE = [
    {"plaats": "Camping Maka",               "lat": 49.81113, "lon": 5.17507,  "van": "2026-09-04", "tot": "2026-09-04", "land": "Bertrix, België"},
    {"plaats": "Domaine Les Gandins",        "lat": 46.19339, "lon": 3.24323,  "van": "2026-09-05", "tot": "2026-09-05", "land": "Saint-Germain-de-Salles, Frankrijk"},
    {"plaats": "Les Criques de Porteils",    "lat": 42.53408, "lon": 3.06799,  "van": "2026-09-06", "tot": "2026-09-08", "land": "Argeles-sur-Mer, Frankrijk"},
    {"plaats": "Camping Port de la Vall",    "lat": 42.34264, "lon": 3.18499,  "van": "2026-09-09", "tot": "2026-09-09", "land": "El Port de la Selva, Spanje"},
    {"plaats": "Camping Can Fosses",         "lat": 42.32241, "lon": 2.10378,  "van": "2026-09-10", "tot": "2026-09-10", "land": "Planoles, Spanje"},
    {"plaats": "Camping El Cortal del Gral", "lat": 42.41662, "lon": 1.67329,  "van": "2026-09-11", "tot": "2026-09-12", "land": "Alt Urgell, Spanje"},
    {"plaats": "Camping Frontera Park",      "lat": 42.42846, "lon": 1.46346,  "van": "2026-09-13", "tot": "2026-09-13", "land": "Les Valls de Valira, Spanje"},
    {"plaats": "Camping La Mola",            "lat": 42.57021, "lon": 1.10773,  "van": "2026-09-14", "tot": "2026-09-14", "land": "Espot, Spanje"},
    {"plaats": "Camping Baliera",            "lat": 42.43927, "lon": 0.70090,  "van": "2026-09-15", "tot": "2026-09-15", "land": "Bonansa, Spanje"},
    {"plaats": "Camping Aneto",              "lat": 42.62476, "lon": 0.54475,  "van": "2026-09-16", "tot": "2026-09-18", "land": "Benasque, Spanje"},
    {"plaats": "Camping Pineta",             "lat": 42.65113, "lon": 0.14096,  "van": "2026-09-19", "tot": "2026-09-19", "land": "Bielsa, Spanje"},
    {"plaats": "Camping Selva de Oza",       "lat": 42.83508, "lon": -0.70963, "van": "2026-09-20", "tot": "2026-09-20", "land": "Valle de Hecho, Spanje"},
    {"plaats": "Camping Le Bord de Mer",     "lat": 43.40665, "lon": -1.64239, "van": "2026-09-21", "tot": "2026-09-23", "land": "Hendaye, Frankrijk"},
    {"plaats": "Chateauroux",                "lat": 46.80917, "lon": 1.70405,  "van": "2026-09-24", "tot": "2026-09-24", "land": "Frankrijk"},
    {"plaats": "Camping Prahay",             "lat": 49.81377, "lon": 5.01405,  "van": "2026-09-25", "tot": "2026-09-25", "land": "Bouillon, België"},
]

# Reisperiode, gebruikt voor de voortgangsbalk bovenaan.
REIS_START = "2026-09-04"
REIS_EIND = "2026-09-27"

# Kilometers per dag uit het routeschema; rustdagen staan op nul. De som is
# 4276, gelijk aan het totaal onderaan de spreadsheet.
KM = {
    "2026-09-04": 500, "2026-09-05": 536, "2026-09-06": 549, "2026-09-07": 0,
    "2026-09-08": 0,   "2026-09-09": 45,  "2026-09-10": 150, "2026-09-11": 120,
    "2026-09-12": 0,   "2026-09-13": 60,  "2026-09-14": 110, "2026-09-15": 136,
    "2026-09-16": 90,  "2026-09-17": 0,   "2026-09-18": 0,   "2026-09-19": 100,
    "2026-09-20": 180, "2026-09-21": 200, "2026-09-22": 0,   "2026-09-23": 0,
    "2026-09-24": 500, "2026-09-25": 500, "2026-09-26": 500, "2026-09-27": 0,
}

# Rustdagen en bijzonderheden, per datum, zoals in het routeschema.
NOTITIES = {
    "2026-09-04": "Vertrekdag, 500 km snelweg",
    "2026-09-05": "536 km, tolwegen vermijden",
    "2026-09-06": "549 km naar de Middellandse Zee",
    "2026-09-07": "Rustdag - zwemmen in de Middellandse Zee",
    "2026-09-08": "Rustdag - zwemmen in de Middellandse Zee",
    "2026-09-09": "45 km langs de kust Spanje in",
    "2026-09-10": "150 km, laatste deel off road",
    "2026-09-11": "120 km off road",
    "2026-09-12": "Rustdag - hiken",
    "2026-09-13": "60 km off road, hoogste punt van de reis",
    "2026-09-14": "110 km off road",
    "2026-09-15": "136 km off road",
    "2026-09-16": "90 km off road",
    "2026-09-17": "Rustdag - hiken",
    "2026-09-18": "Rustdag - hiken",
    "2026-09-19": "100 km off road",
    "2026-09-20": "180 km off road",
    "2026-09-21": "200 km off road naar de oceaan",
    "2026-09-22": "Rustdag - zwemmen in de oceaan",
    "2026-09-23": "Surfen",
    "2026-09-24": "500 km richting huis",
    "2026-09-25": "500 km",
    "2026-09-26": "500 km, laatste etappe naar huis",
}
