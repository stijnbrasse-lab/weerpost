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
DAGEN_VOORUIT = 5


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
        "hourly": "temperature_2m,precipitation,precipitation_probability,weather_code",
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


def bouw_dagen(route, vandaag=None, dagen=DAGEN_VOORUIT):
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
            "middag": _op_uur(vp, datetime.combine(d, time(15))),
            "avond": _op_uur(vp, datetime.combine(d, time(21))),
            "nacht": _op_uur(vp, datetime.combine(d + timedelta(days=1), time(3))),
        })
    return resultaat
