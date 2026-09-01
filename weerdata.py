# -*- coding: utf-8 -*-
"""Haalt de weersvoorspelling op voor de overnachtingsplaatsen uit de route.

Levert per dag: neerslag, temperatuur om 15:00, om 21:00 en om 03:00 in de
nacht erna. Bron: Open-Meteo (gratis, geen API-sleutel nodig).

Alle bestemmingen liggen in NL/BE/FR/ES en delen dus dezelfde klok (CET/CEST),
waardoor 15:00, 21:00 en 03:00 overal lokale tijd zijn.
"""
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIJDZONE = "Europe/Paris"

# Vijf dagen met alle details, daarna nog vijf als ruwe vooruitblik. Verder dan
# tien dagen heeft geen zin: dan lopen de modellen zo uiteen dat het ruis wordt.
DAGEN_VOORUIT = 5
DAGEN_TOTAAL = 10

# Beginuren van de blokken van twee uur waarin we de dag opdelen, zodat je ziet
# op welk moment de neerslag valt. Daarna volgt een nachtblok van 22:00 tot
# 08:00 de volgende ochtend: dat zijn de uren dat je in de tent ligt, en die
# hoef je niet per twee uur te weten.
DAG_UREN = [8, 10, 12, 14, 16, 18, 20]
NACHT_UREN = [22, 23]          # op de dag zelf
NACHT_UREN_ERNA = list(range(8))  # 00:00 t/m 07:00 de ochtend erna


def _haal(url, params):
    qs = urllib.parse.urlencode(params, doseq=True)
    with urllib.request.urlopen(f"{url}?{qs}", timeout=30) as r:
        return json.load(r)


def _datums(van, tot):
    d, eind = date.fromisoformat(van), date.fromisoformat(tot)
    while d <= eind:
        yield d
        d += timedelta(days=1)


def route_naar_kalender(route):
    """Kaart datum -> etappe, zodat elke dag weet waar je die nacht slaapt."""
    kalender = {}
    for etappe in route:
        for d in _datums(etappe["van"], etappe["tot"]):
            kalender[d] = etappe
    return kalender


def haal_voorspelling(etappe, start, eind):
    return _haal(FORECAST_URL, {
        "latitude": etappe["lat"],
        "longitude": etappe["lon"],
        "hourly": ("temperature_2m,precipitation,precipitation_probability,weather_code,"
                   "wind_speed_10m,wind_direction_10m,wind_gusts_10m"),
        "daily": "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,weather_code",
        "start_date": start.isoformat(),
        "end_date": eind.isoformat(),
        "timezone": TIJDZONE,
    })


def _op_uur(vp, wanneer):
    """Uurwaarde, of None als dat uur buiten de opgehaalde reeks valt."""
    uren = vp["hourly"]
    try:
        i = uren["time"].index(wanneer.strftime("%Y-%m-%dT%H:00"))
    except ValueError:
        return None
    return {
        "temp": uren["temperature_2m"][i],
        "neerslag": uren["precipitation"][i],
        "kans": uren["precipitation_probability"][i],
        "code": uren["weather_code"][i],
    }


KOMPAS = ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"]


def windstreek(graden):
    """Zet een windrichting in graden om naar de streek waar hij vandaan komt."""
    if graden is None:
        return None
    return KOMPAS[round(graden / 45) % 8]


def _samenvatting(uren, indexen, label, nacht=False):
    """Vat een reeks uren samen tot een blok.

    De wind is die van het hardste uur, niet het gemiddelde: waait het in een
    van de uren stevig, dan wil je dat zien en niet weggemiddeld krijgen.
    """
    if not indexen:
        return {"label": label, "nacht": nacht, "mm": None, "kans": None,
                "wind": None, "streek": None, "stoot": None}
    mm, kans = 0.0, 0
    wind, richting, stoot = None, None, None
    for i in indexen:
        mm += uren["precipitation"][i] or 0
        k = uren["precipitation_probability"][i]
        if k is not None:
            kans = max(kans, k)
        snelheid = uren["wind_speed_10m"][i]
        if snelheid is not None and (wind is None or snelheid > wind):
            wind = snelheid
            richting = uren["wind_direction_10m"][i]
            stoot = uren["wind_gusts_10m"][i]
    return {
        "label": label,
        "nacht": nacht,
        "mm": round(mm, 2),
        "kans": kans,
        "wind": None if wind is None else round(wind),
        "streek": windstreek(richting),
        "stoot": None if stoot is None else round(stoot),
    }


def blokken_per_twee_uur(vp, d):
    """Neerslag en wind per blok: overdag per twee uur, plus een nachtblok."""
    uren = vp["hourly"]
    morgen = d + timedelta(days=1)

    def index(dag, uur):
        try:
            return uren["time"].index(f"{dag.isoformat()}T{uur:02d}:00")
        except ValueError:
            return None

    blokken = []
    for h in DAG_UREN:
        indexen = [i for i in (index(d, h), index(d, h + 1)) if i is not None]
        blokken.append(_samenvatting(uren, indexen, f"{h:02d}"))

    nacht = [index(d, u) for u in NACHT_UREN] + [index(morgen, u) for u in NACHT_UREN_ERNA]
    blokken.append(_samenvatting(uren, [i for i in nacht if i is not None],
                                 "22-08", nacht=True))
    return blokken


def bouw_dagen(route, vandaag=None, dagen=DAGEN_TOTAAL):
    vandaag = vandaag or date.today()
    kalender = route_naar_kalender(route)
    gevraagd = [vandaag + timedelta(days=i) for i in range(dagen)]

    # Groepeer per plaats: een API-aanroep per locatie in plaats van per dag.
    per_plaats, volgorde = {}, []
    for d in gevraagd:
        etappe = kalender.get(d)
        if not etappe:
            continue
        sleutel = etappe["plaats"]
        if sleutel not in per_plaats:
            per_plaats[sleutel] = {"etappe": etappe, "datums": []}
            volgorde.append(sleutel)
        per_plaats[sleutel]["datums"].append(d)

    voorspellingen = {}
    for sleutel in volgorde:
        blok = per_plaats[sleutel]
        # Een dag extra, want 03:00 hoort bij de nacht na de laatste dag.
        voorspellingen[sleutel] = haal_voorspelling(
            blok["etappe"], min(blok["datums"]), max(blok["datums"]) + timedelta(days=1)
        )

    resultaat = []
    for d in gevraagd:
        etappe = kalender.get(d)
        if not etappe:
            resultaat.append({"datum": d, "etappe": None})
            continue
        vp = voorspellingen[etappe["plaats"]]
        i = vp["daily"]["time"].index(d.isoformat())
        resultaat.append({
            "datum": d,
            "etappe": etappe,
            "hoogte": vp.get("elevation"),
            "neerslag_mm": vp["daily"]["precipitation_sum"][i],
            "neerslag_kans": vp["daily"]["precipitation_probability_max"][i],
            "code": vp["daily"]["weather_code"][i],
            "max_temp": vp["daily"]["temperature_2m_max"][i],
            "min_temp": vp["daily"]["temperature_2m_min"][i],
            "blokken": blokken_per_twee_uur(vp, d),
            "middag": _op_uur(vp, datetime.combine(d, time(15))),
            "avond": _op_uur(vp, datetime.combine(d, time(21))),
            "nacht": _op_uur(vp, datetime.combine(d + timedelta(days=1), time(3))),
        })
    return resultaat
