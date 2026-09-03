# -*- coding: utf-8 -*-
"""Bouwt de HTML-pagina voor het vakantiedashboard uit de opgehaalde weerdata."""
import html
import sys
from datetime import date, datetime, timedelta

import route
import weerdata

DAGEN_NL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MAANDEN_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
              "augustus", "september", "oktober", "november", "december"]
DAGEN_KORT = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MAANDEN_KORT = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul",
                "aug", "sep", "okt", "nov", "dec"]

# WMO-weercodes naar een korte omschrijving en een icoonsoort.
WEER = {
    0: ("Helder", "zon"), 1: ("Overwegend helder", "zon"), 2: ("Half bewolkt", "halfbewolkt"),
    3: ("Bewolkt", "bewolkt"), 45: ("Mist", "mist"), 48: ("Aanvriezende mist", "mist"),
    51: ("Lichte motregen", "motregen"), 53: ("Motregen", "motregen"), 55: ("Dichte motregen", "motregen"),
    56: ("IJzelmotregen", "motregen"), 57: ("Dichte ijzelmotregen", "motregen"),
    61: ("Lichte regen", "regen"), 63: ("Regen", "regen"), 65: ("Zware regen", "regen"),
    66: ("IJzelregen", "regen"), 67: ("Zware ijzelregen", "regen"),
    71: ("Lichte sneeuw", "sneeuw"), 73: ("Sneeuw", "sneeuw"), 75: ("Zware sneeuw", "sneeuw"),
    77: ("Sneeuwkorrels", "sneeuw"), 80: ("Lichte buien", "buien"), 81: ("Buien", "buien"),
    82: ("Zware buien", "buien"), 85: ("Sneeuwbuien", "sneeuw"), 86: ("Zware sneeuwbuien", "sneeuw"),
    95: ("Onweer", "onweer"), 96: ("Onweer met hagel", "onweer"), 99: ("Zwaar onweer met hagel", "onweer"),
}

# Temperatuurschaal: koud blauw, via een neutrale olijftint naar warm.
# Per stap een kleur voor het lichte en een voor het donkere thema.
TEMP_SCHAAL = [
    (0,  "#16457C", "#7FB4EC"),
    (7,  "#2A6A9E", "#8CC3EA"),
    (13, "#3A7E8E", "#86C5CE"),
    (19, "#6B7A5E", "#B7BFA4"),
    (25, "#A8721B", "#E3B45E"),
    (99, "#B24327", "#F08E6C"),
]

IKONEN = {
    "zon": '<circle cx="12" cy="12" r="5"/><g stroke-linecap="round"><path d="M12 1.5v2.5M12 20v2.5M22.5 12H20M4 12H1.5M19.4 4.6l-1.8 1.8M6.4 17.6l-1.8 1.8M19.4 19.4l-1.8-1.8M6.4 6.4L4.6 4.6"/></g>',
    "halfbewolkt": '<circle cx="8.5" cy="8" r="3.4"/><g stroke-linecap="round"><path d="M8.5 1.4v1.8M14.6 8h-1.8M4.2 8H2.4M12.8 3.7l-1.3 1.3M5.5 11l-1.3 1.3M12.8 12.3l-1.3-1.3M4.2 3.7L5.5 5"/></g><path d="M9 20.5h8.5a3.5 3.5 0 0 0 .3-7 5 5 0 0 0-9.4-1.2A3.6 3.6 0 0 0 9 20.5z" fill="var(--kaart)"/>',
    "bewolkt": '<path d="M7.5 19.5h9.5a4 4 0 0 0 .3-8 5.6 5.6 0 0 0-10.6-1.3A4.1 4.1 0 0 0 7.5 19.5z"/>',
    "mist": '<path d="M7.5 14h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 4.7 4.1 4.1 0 0 0 7.5 14z"/><g stroke-linecap="round"><path d="M4 18h16M6.5 21.5h11"/></g>',
    "motregen": '<path d="M7.5 15.5h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 6.2 4.1 4.1 0 0 0 7.5 15.5z"/><g stroke-linecap="round"><path d="M9.5 19v1.5M14.5 19v1.5"/></g>',
    "regen": '<path d="M7.5 14.5h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 5.2 4.1 4.1 0 0 0 7.5 14.5z"/><g stroke-linecap="round"><path d="M8.5 17.5l-1 4M13 17.5l-1 4M17.5 17.5l-1 4"/></g>',
    "buien": '<path d="M7.5 14.5h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 5.2 4.1 4.1 0 0 0 7.5 14.5z"/><g stroke-linecap="round"><path d="M8.5 17.5l-1 3M13 17.5l-1 3M17.5 17.5l-1 3M10.7 21.5l-.5 1.5M15.2 21.5l-.5 1.5"/></g>',
    "sneeuw": '<path d="M7.5 14.5h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 5.2 4.1 4.1 0 0 0 7.5 14.5z"/><g stroke-linecap="round"><path d="M9 18.5v3M7.7 19.2l2.6 1.6M10.3 19.2l-2.6 1.6M15.5 18.5v3M14.2 19.2l2.6 1.6M16.8 19.2l-2.6 1.6"/></g>',
    "onweer": '<path d="M7.5 14.5h9.5a4 4 0 0 0 .3-8A5.6 5.6 0 0 0 6.7 5.2 4.1 4.1 0 0 0 7.5 14.5z"/><path d="M13 17l-3.5 4.5h3L11 24" stroke-linecap="round" stroke-linejoin="round"/>',
}


def icoon(soort, klasse="ikoon"):
    pad = IKONEN.get(soort, IKONEN["bewolkt"])
    return (f'<svg class="{klasse}" viewBox="0 0 24 25" fill="none" stroke="currentColor" '
            f'stroke-width="1.5" aria-hidden="true">{pad}</svg>')


def temp_kleuren(t):
    """Geeft (lichte, donkere) tekstkleur voor een temperatuur."""
    if t is None:
        return ("var(--gedempt)", "var(--gedempt)")
    for grens, licht, donker in TEMP_SCHAAL:
        if t <= grens:
            return (licht, donker)
    return (TEMP_SCHAAL[-1][1], TEMP_SCHAAL[-1][2])


def nl_datum(d):
    return f"{DAGEN_NL[d.weekday()]} {d.day} {MAANDEN_NL[d.month - 1]}"


def kort_datum(d):
    return f"{DAGEN_KORT[d.weekday()]} {d.day} {MAANDEN_KORT[d.month - 1]}"


def reisdag_nummer(d):
    """Dagnummer binnen de reis, of None buiten de reisperiode."""
    if date(2026, 9, 4) <= d <= date(2026, 9, 27):
        return (d - date(2026, 9, 4)).days + 1
    return None


def _temp(waarde):
    return "--" if waarde is None else f"{round(waarde)}"


def _mm(waarde):
    return f"{waarde:.1f}".replace(".", ",")


def _blok_titel(b):
    """Tekst voor de tooltip van een blok."""
    stukken = [f'{b["van"]} - {b["tot"]}', f'{_mm(b["mm"])} mm',
               f'{round(b.get("kans") or 0)}% kans']
    if b.get("wind") is not None:
        wind = f'wind {b.get("streek") or "?"} {b["wind"]} km/u'
        if b.get("stoot") is not None and b["stoot"] > b["wind"]:
            wind += f', uitschieters {b["stoot"]}'
        stukken.append(wind)
    return html.escape(" - ".join(stukken))


def tijdstrip(blokken):
    """Neerslag en wind per blok: overdag per twee uur, plus de nacht.

    Anders dan eerder verschijnt deze strip ook op droge dagen, want de wind
    is dan net zo goed nieuws als de regen.
    """
    geldig = [b for b in blokken if b.get("mm") is not None]
    if not geldig:
        return ""

    overdag = [b for b in geldig if not b.get("nacht")]
    # De schaal ijken op de daguren. Het nachtblok beslaat tien uur en zou de
    # daguren anders platdrukken; dat staafje mag tegen het plafond lopen,
    # want het getal eronder vertelt de werkelijke hoeveelheid.
    schaal = max(1.0, max((b["mm"] for b in overdag), default=0))

    piek = max(geldig, key=lambda b: b["mm"])
    if piek["mm"] < 0.1:
        samenvatting = "droog"
    elif piek.get("nacht"):
        samenvatting = f'piek {_mm(piek["mm"])} mm in de nacht'
    else:
        samenvatting = f'piek {_mm(piek["mm"])} mm om {piek["van"]}'

    kolommen, voorlezen = [], []
    for b in blokken:
        klasse = "regen-kolom is-nacht" if b.get("nacht") else "regen-kolom"
        tijd = (f'<span class="regen-tijd">'
                f'<span class="regen-tijd-van">{b["van"]}</span>'
                f'<span class="regen-tijd-tot">{b["tot"]}</span></span>')
        mm = b.get("mm")
        if mm is None:
            kolommen.append(f'<div class="{klasse}"><div class="regen-vak"></div>'
                            f'<span class="regen-mm is-leeg">&ndash;</span>'
                            f'<span class="regen-streek is-leeg">&ndash;</span>'
                            f'<span class="regen-kmu is-leeg">&ndash;</span>'
                            f'{tijd}</div>')
            continue
        leeg = mm < 0.05
        deel = 0 if mm <= 0 else min(100, max(8, round(mm / schaal * 100)))
        staaf = f'<div class="regen-staaf" style="height:{deel}%"></div>' if deel else ""
        wind = b.get("wind")
        kolommen.append(
            f'<div class="{klasse}" title="{_blok_titel(b)}">'
            f'<div class="regen-vak">{staaf}</div>'
            f'<span class="regen-mm{" is-leeg" if leeg else ""}">'
            f'{"0" if leeg else _mm(mm)}</span>'
            f'<span class="regen-streek">{b.get("streek") or "&ndash;"}</span>'
            f'<span class="regen-kmu">{"&ndash;" if wind is None else wind}</span>'
            f'{tijd}</div>')
        span = "de nacht" if b.get("nacht") else f'{b["van"]} tot {b["tot"]}'
        voorlezen.append(f'{span}: {_mm(mm)} mm, wind {b.get("streek") or "onbekend"} '
                         f'{"onbekend" if wind is None else wind} kilometer per uur')

    return (f'<div class="regen">'
            f'<div class="regen-kop">'
            f'<span class="regen-titel">Neerslag mm &middot; wind km/u</span>'
            f'<span class="regen-piek">{samenvatting}</span>'
            f'</div>'
            f'<div class="regen-strip" role="img" '
            f'aria-label="Per blok: {html.escape("; ".join(voorlezen))}">'
            + "".join(kolommen)
            + f'</div></div>')


# ---- Slingerende route bovenaan ----
# Vier rijen van zes dagen, om en om naar rechts en naar links, met bochten
# aan de uiteinden. Die bochten zijn wat het onderscheidt van een kalender:
# zonder die U-keer leest het als een raster in plaats van als een route.
PER_RIJ = 8
SPOOR_LINKS, SPOOR_RECHTS = 10.0, 90.0
SPOOR_TOP, SPOOR_RIJHOOGTE, SPOOR_BODEM = 6.0, 14.0, 8.0
SPOOR_AANLOOP = 2.0  # waar het pad begint, links van de eerste dag
STREEP_HOOG, STREEP_HOOG_NU = 8.0, 11.0


def spoor_labels():
    """Korte datum per reisdag, zoals 'vr 04', voor onder de streepjes."""
    start = date.fromisoformat(route.REIS_START)
    aantal = (date.fromisoformat(route.REIS_EIND) - start).days + 1
    labels = []
    for i in range(aantal):
        d = start + timedelta(days=i)
        labels.append(f"{DAGEN_KORT[d.weekday()]} {d.day:02d}")
    return labels


def spoor_km():
    """Te rijden kilometers per reisdag, in dezelfde volgorde als de labels."""
    start = date.fromisoformat(route.REIS_START)
    aantal = (date.fromisoformat(route.REIS_EIND) - start).days + 1
    return [route.KM.get((start + timedelta(days=i)).isoformat(), 0)
            for i in range(aantal)]


def _bochtlengte(p0, p1, p2, p3, n=32):
    """Lengte van een kubische bocht, benaderd door hem op te delen."""
    lengte, vorige = 0.0, p0
    for k in range(1, n + 1):
        t, mt = k / n, 1 - k / n
        x = (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
             + 3 * mt * t * t * p2[0] + t ** 3 * p3[0])
        y = (mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
             + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])
        lengte += ((x - vorige[0]) ** 2 + (y - vorige[1]) ** 2) ** 0.5
        vorige = (x, y)
    return lengte


def bouw_spoor(aantal):
    """Rekent het pad, de dagposities en de afstand langs het pad uit.

    Die afstanden maken het mogelijk de lijn te kleuren tot precies de dag
    waar je bent. De vorm hangt niet af van de datum, dus dit kan een keer
    berekend worden en door beide versies gedeeld.
    """
    rijen = -(-aantal // PER_RIJ)
    stap = (SPOOR_RECHTS - SPOOR_LINKS) / (PER_RIJ - 1)
    rijlengte = SPOOR_RECHTS - SPOOR_LINKS
    punten, lengtes, stukken = [], [], []
    # Kort aanloopstuk voor de eerste dag: die rit begint thuis, en thuis staat
    # niet op het spoor. Zonder dat stukje heeft die etappe nergens plek.
    tot_hier = SPOOR_LINKS - SPOOR_AANLOOP

    for r in range(rijen):
        y = SPOOR_TOP + r * SPOOR_RIJHOOGTE
        naar_rechts = r % 2 == 0
        start = SPOOR_LINKS if naar_rechts else SPOOR_RECHTS
        richting = stap if naar_rechts else -stap
        eind = SPOOR_RECHTS if naar_rechts else SPOOR_LINKS

        for i in range(min(PER_RIJ, aantal - r * PER_RIJ)):
            punten.append((round(start + i * richting, 2), y))
            lengtes.append(round(tot_hier + abs(i * richting), 2))

        if r == 0:
            stukken.append(f"M {SPOOR_AANLOOP} {y}")
            stukken.append(f"L {eind} {y}")
        else:
            stukken.append(f"L {start} {y}")
            stukken.append(f"L {eind} {y}")
        tot_hier += rijlengte

        if r < rijen - 1:
            y2 = y + SPOOR_RIJHOOGTE
            # Bocht buiten de rij om, links of rechts al naar gelang de richting.
            bocht = 95.5 if naar_rechts else 4.5
            stukken.append(f"C {bocht} {y} {bocht} {y2} {eind} {y2}")
            tot_hier += _bochtlengte((eind, y), (bocht, y), (bocht, y2), (eind, y2))

    # Middens van de trajecten: daar komen de kilometers te staan. Het traject
    # naar dag N loopt van kamp N-1 naar kamp N; voor dag 1 is dat het
    # aanloopstuk. Valt een traject in een bocht, dan gaat het label naar de
    # buitenkant daarvan.
    tussen = [((SPOOR_AANLOOP + SPOOR_LINKS) / 2, punten[0][1])]
    for i in range(1, len(punten)):
        (vx, vy), (nx, ny) = punten[i - 1], punten[i]
        if vy == ny:
            tussen.append((round((vx + nx) / 2, 2), vy))
        else:
            bocht = 95.5 if ((i - 1) // PER_RIJ) % 2 == 0 else 4.5
            tussen.append((bocht, round((vy + ny) / 2, 2)))

    return {
        "pad": " ".join(stukken),
        "punten": punten,
        "tussen": tussen,
        "lengtes": lengtes,
        "totaal": round(tot_hier, 2),
        "hoogte": SPOOR_TOP + (rijen - 1) * SPOOR_RIJHOOGTE + SPOOR_BODEM,
        "hoog": STREEP_HOOG,
        "per_rij": PER_RIJ,
        "defender": DEFENDER,
        "defender_breed": DEFENDER_BREED,
        "defender_midden": DEFENDER_MIDDEN_Y,
        "defender_span": DEFENDER_SPAN,
    }


# De Defender 110 als markering, getekend in een eigen vlak van 24 bij 13 en
# daarna op het spoor geschaald. Wat hem herkenbaar maakt op klein formaat is
# de lange platte daklijn, de korte schuine voorruit en het reservewiel achter.
DEFENDER_BREED = 24.5
DEFENDER_MIDDEN_Y = 7.5
DEFENDER = (
    # Reservewiel op de achterklep; de naaf wordt uitgespaard zodat het als
    # wiel leest en niet als een bult aan de achterkant.
    '<circle class="defender-body" cx="2.4" cy="6.6" r="2.2"></circle>'
    # Carrosserie: lange platte daklijn, korte schuine ruit, vlakke motorkap.
    '<path class="defender-body" d="M3.6 10.2 L3.6 2.6 L19.2 2.6 L20.7 5.3 '
    'L24 5.3 L24 10.2 Z"></path>'
    '<circle class="defender-body" cx="7.8" cy="10.4" r="2"></circle>'
    '<circle class="defender-body" cx="20.6" cy="10.4" r="2"></circle>'
    '<path class="defender-glas" d="M4.8 3.6 H11.4 V6.2 H4.8 Z '
    'M12.4 3.6 H18.4 V6.2 H12.4 Z"></path>'
    '<circle class="defender-glas" cx="2.4" cy="6.6" r="0.95"></circle>'
    '<circle class="defender-glas" cx="7.8" cy="10.4" r="0.75"></circle>'
    '<circle class="defender-glas" cx="20.6" cy="10.4" r="0.75"></circle>'
)
DEFENDER_SPAN = 11.0  # breedte op het spoor


def defender(x, y, naar_rechts):
    """Plaatst de Defender op het spoor, kijkend in de rijrichting."""
    s = DEFENDER_SPAN / DEFENDER_BREED
    dx = DEFENDER_BREED / 2 * s
    dy = DEFENDER_MIDDEN_Y * s
    if naar_rechts:
        t = f"translate({x - dx:.2f} {y - dy:.2f}) scale({s:.4f})"
    else:
        t = f"translate({x + dx:.2f} {y - dy:.2f}) scale({-s:.4f} {s:.4f})"
    return f'<g class="defender" transform="{t}">{DEFENDER}</g>'


def voortgang(vandaag):
    """Waar we op de route staan: dagnummer en gereden kilometers."""
    start = date.fromisoformat(route.REIS_START)
    eind = date.fromisoformat(route.REIS_EIND)
    totaal_dagen = (eind - start).days + 1
    km_totaal = sum(route.KM.values())

    # Gereden is wat achter de rug is: de dagen vóór vandaag.
    km_gereden = sum(km for datum, km in route.KM.items()
                     if date.fromisoformat(datum) < vandaag)

    if vandaag < start:
        dagen_tot = (start - vandaag).days
        kop = "Vertrek morgen" if dagen_tot == 1 else f"Vertrek over {dagen_tot} dagen"
        nummer = None
    elif vandaag > eind:
        kop = "Reis afgerond"
        nummer = None
    else:
        nummer = (vandaag - start).days + 1
        kop = f"Dag {nummer} van {totaal_dagen}"

    return {"kop": kop, "nummer": nummer, "totaal_dagen": totaal_dagen,
            "km_gereden": km_gereden, "km_totaal": km_totaal}


def _km(getal):
    return f"{getal:,}".replace(",", ".")


def reisvoortgang(vandaag):
    v = voortgang(vandaag)
    spoor = bouw_spoor(v["totaal_dagen"])

    voorbij = vandaag > date.fromisoformat(route.REIS_EIND)
    labels, kilometers = spoor_labels(), spoor_km()
    strepen, merken, wagen = [], [], ""
    for i, (x, y) in enumerate(spoor["punten"], start=1):
        nu = v["nummer"] is not None and i == v["nummer"]
        if nu:
            # Op de plek van vandaag staat de Defender in plaats van een streep.
            wagen = defender(x, y, ((i - 1) // PER_RIJ) % 2 == 0)
        else:
            if v["nummer"] is None:
                stand = "was" if voorbij else "komt"
            else:
                stand = "was" if i < v["nummer"] else "komt"
            strepen.append(
                f'<rect class="streep streep-{stand}" x="{x - 1.2:.2f}" '
                f'y="{y - STREEP_HOOG / 2:.2f}" width="2.4" height="{STREEP_HOOG:.0f}" '
                f'rx="1.2"></rect>')
        merken.append(
            f'<text class="spoor-datum{" is-nu" if nu else ""}" x="{x:.2f}" '
            f'y="{y + 7:.2f}" text-anchor="middle">{labels[i - 1]}</text>')
        # De kilometers staan op het traject ernaartoe, niet onder de dag.
        km = kilometers[i - 1]
        tx, ty = spoor["tussen"][i - 1]
        merken.append(
            f'<text class="spoor-km{" is-nul" if not km else ""}" x="{tx:.2f}" '
            f'y="{ty - 2.4:.2f}" text-anchor="middle">{km}</text>')

    # De lijn gekleurd tot waar we staan; dat leest als afgelegde weg.
    if v["nummer"] is None:
        afgelegd = spoor["totaal"] if voorbij else 0
    else:
        afgelegd = spoor["lengtes"][v["nummer"] - 1]
    afgelegde_lijn = (
        f'<path class="spoor-lijn spoor-af" d="{spoor["pad"]}" fill="none" '
        f'stroke-dasharray="{afgelegd:.2f} {spoor["totaal"]:.2f}"></path>'
        if afgelegd > 0 else "")

    start = date.fromisoformat(route.REIS_START)
    eind = date.fromisoformat(route.REIS_EIND)

    return (f'<section class="voortgang">'
            f'<div class="voortgang-kop">'
            f'<span class="voortgang-titel">Waar we zijn</span>'
            f'<span class="voortgang-km">{_km(v["km_gereden"])} van '
            f'{_km(v["km_totaal"])} km gereden</span>'
            f'</div>'
            f'<p class="voortgang-dag">{v["kop"]}</p>'
            f'<svg class="spoor" viewBox="0 0 100 {spoor["hoogte"]:.0f}" '
            f'role="img" aria-label="Routevoortgang: {html.escape(v["kop"])}, '
            f'{_km(v["km_gereden"])} van {_km(v["km_totaal"])} kilometer gereden">'
            f'<path class="spoor-lijn" d="{spoor["pad"]}" fill="none"></path>'
            + afgelegde_lijn
            + "".join(strepen)
            + "".join(merken)
            + wagen
            + f'</svg></section>')


def vooruitblik(dagen):
    """Ruwe vooruitblik voor dag 6 tot en met 10: alleen plek, piek en regen.

    Bewust karig van vorm. Op deze afstand is de voorspelling een richting,
    geen planning, en dat mag je aan de opmaak kunnen zien.
    """
    rijen = []
    for dag in dagen:
        etappe = dag.get("etappe")
        if not etappe:
            continue
        omschrijving, soort = WEER.get(dag["code"], ("Onbekend", "bewolkt"))
        mm = dag.get("neerslag_mm") or 0
        droog = mm < 0.2
        licht, donker = temp_kleuren(dag.get("max_temp"))
        rijen.append(
            f'<div class="blik-rij">'
            f'<div class="blik-links">'
            f'<span class="blik-datum">{kort_datum(dag["datum"])}</span>'
            f'<span class="blik-plek">{html.escape(etappe["plaats"])}</span>'
            f'</div>'
            f'<div class="blik-rechts">'
            f'<span class="blik-icoon" title="{html.escape(omschrijving)}">'
            f'{icoon(soort, "ikoon-klein")}</span>'
            f'<span class="blik-temp" style="--tl:{licht};--td:{donker}">'
            f'{_temp(dag.get("max_temp"))}<span class="graad">&deg;</span></span>'
            f'<span class="blik-regen{" is-droog" if droog else ""}">'
            f'{"0" if droog else _mm(mm)} mm</span>'
            f'</div></div>'
        )
    if not rijen:
        return ""
    return (f'<section class="blik">'
            f'<div class="blik-kop">'
            f'<span class="blik-titel">Vooruitblik</span>'
            f'<span class="blik-toelichting">richting, geen planning</span>'
            f'</div>'
            + "".join(rijen)
            + f'</section>')


def blok_tijdstip(label, toelichting, meting, nadruk=False):
    t = None if meting is None else meting["temp"]
    licht, donker = temp_kleuren(t)
    klassen = "stop stop-nadruk" if nadruk else "stop"
    return (f'<div class="{klassen}">'
            f'<div class="stop-tijd">{label}</div>'
            f'<div class="stop-temp" style="--tl:{licht};--td:{donker}">{_temp(t)}<span class="graad">&deg;</span></div>'
            f'<div class="stop-uitleg">{html.escape(toelichting)}</div>'
            f'</div>')


def kaart(dag, vandaag):
    d = dag["datum"]
    etappe = dag["etappe"]
    nummer = reisdag_nummer(d)
    eyebrow = f"Dag {nummer}" if nummer else "Voor vertrek"
    is_vandaag = d == vandaag

    if etappe is None:
        return (f'<article class="kaart kaart-leeg">'
                f'<div class="kop"><span class="eyebrow">{eyebrow}</span>'
                f'<span class="datum">{nl_datum(d)}</span></div>'
                f'<p class="leeg-tekst">Geen overnachting gepland.</p></article>')

    omschrijving, soort = WEER.get(dag["code"], ("Onbekend", "bewolkt"))
    mm = dag["neerslag_mm"] or 0
    kans = dag["neerslag_kans"] or 0
    notitie = route.NOTITIES.get(d.isoformat())
    hoogte = dag.get("hoogte")

    droog = mm < 0.2
    neerslag_tekst = "0 mm" if droog else _mm(mm) + " mm"
    dagmax = dag.get("max_temp")

    regio = html.escape(etappe.get("land", ""))
    if hoogte is not None:
        regio += f" &middot; {round(hoogte)} m"

    return (f'<article class="kaart{" kaart-vandaag" if is_vandaag else ""}">'
            f'<div class="kop">'
            f'<span class="eyebrow">{eyebrow}{" &middot; vandaag" if is_vandaag else ""}</span>'
            f'<span class="datum">{nl_datum(d)}</span>'
            f'</div>'
            f'<div class="plek">'
            f'<h2 class="plek-naam">{html.escape(etappe["plaats"])}</h2>'
            f'<p class="plek-regio">{regio}</p>'
            f'</div>'
            + (f'<p class="notitie">{html.escape(notitie)}</p>' if notitie else '')
            + f'<div class="weer">'
            f'<div class="weer-icoon">{icoon(soort)}</div>'
            f'<div class="weer-tekst">'
            f'<div class="weer-omschrijving">{html.escape(omschrijving)}'
            + (f'<span class="dagmax">warmste piek {_temp(dagmax)}&deg;</span>'
               if dagmax is not None else '')
            + f'</div>'
            f'<div class="neerslag">'
            f'<span class="neerslag-mm{" is-droog" if droog else ""}">{neerslag_tekst}</span>'
            + ('' if droog else '<span class="neerslag-kans">in 24 uur</span>')
            + f'<span class="neerslag-kans">{round(kans)}% kans op neerslag</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            + tijdstrip(dag.get("blokken") or [])
            + f'<div class="spoor">'
            + blok_tijdstip("15:00", "middag", dag["middag"])
            + '<span class="pijl" aria-hidden="true"></span>'
            + blok_tijdstip("21:00", "avond", dag["avond"])
            + '<span class="pijl" aria-hidden="true"></span>'
            + blok_tijdstip("03:00", "nacht erna", dag["nacht"], nadruk=True)
            + f'</div></article>')


CSS = """
:root {
  --grond: #E9ECEF;
  --kaart: #FFFFFF;
  --kaart-2: #F1F4F7;
  --inkt: #141A20;
  --gedempt: #5B6874;
  --lijn: #D3D9DF;
  --accent: #8F6115;
  --nat: #2F6FA6;
  --nat-zacht: rgba(47, 111, 166, .16);
  --defender: #3F6B45;
  --schaduw: 0 1px 2px rgba(20, 26, 32, .06), 0 8px 20px -12px rgba(20, 26, 32, .3);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --grond: #0D1218;
    --kaart: #151C23;
    --kaart-2: #1B232B;
    --inkt: #E4EAF0;
    --gedempt: #8794A1;
    --lijn: #28313A;
    --accent: #D7A24A;
    --nat: #6FAEE0;
    --nat-zacht: rgba(111, 174, 224, .18);
    --defender: #79B37C;
    --schaduw: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 20px -12px rgba(0, 0, 0, .85);
  }
}
:root[data-theme="dark"] {
  --grond: #0D1218;
  --kaart: #151C23;
  --kaart-2: #1B232B;
  --inkt: #E4EAF0;
  --gedempt: #8794A1;
  --lijn: #28313A;
  --accent: #D7A24A;
  --nat: #6FAEE0;
  --nat-zacht: rgba(111, 174, 224, .18);
  --defender: #79B37C;
  --schaduw: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 20px -12px rgba(0, 0, 0, .85);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--grond);
  color: var(--inkt);
  font-family: "IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.5;
  -webkit-text-size-adjust: 100%;
}

.omslag {
  max-width: 34rem;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.titelblok { display: flex; flex-direction: column; gap: .3rem; }
.titelblok .reis {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .69rem;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: var(--accent);
}
.titelblok h1 {
  margin: 0;
  font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", sans-serif;
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: -.01em;
  line-height: 1.1;
  text-wrap: balance;
}
.titelblok .bijschrift { margin: 0; color: var(--gedempt); font-size: .88rem; }

/* ---- Slingerende route ---- */
.voortgang {
  background: var(--kaart);
  border: 1px solid var(--lijn);
  border-radius: 4px;
  padding: .9rem 1.1rem 1rem;
  box-shadow: var(--schaduw);
}
.voortgang-kop {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: .3rem .6rem;
  flex-wrap: wrap;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .66rem;
}
.voortgang-titel {
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--accent);
}
.voortgang-km {
  margin-left: auto;
  color: var(--gedempt);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.voortgang-dag {
  margin: .15rem 0 .6rem;
  font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", sans-serif;
  font-size: 1.3rem;
  font-weight: 600;
  line-height: 1.15;
}
.spoor { display: block; width: 100%; height: auto; overflow: visible; }
.spoor-lijn {
  stroke: var(--lijn);
  stroke-width: 1.1;
  stroke-linecap: round;
}
/* 2,85 eenheden komt op een telefoonscherm uit op 8,8 px, gelijk aan de
   tijden onder de neerslagstrip. */
.spoor-datum,
.spoor-km {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 2.85px;
  fill: var(--gedempt);
}
.spoor-datum.is-nu { fill: var(--accent); }
.spoor-km { opacity: .75; }
.spoor-km.is-nul { opacity: .4; }
.streep { fill: var(--lijn); }
.streep-was { fill: var(--accent); opacity: .55; }
.spoor-af { stroke: var(--accent); opacity: .55; }
.defender-body { fill: var(--defender); }
.defender-glas { fill: var(--kaart); }

.kaart {
  background: var(--kaart);
  border: 1px solid var(--lijn);
  border-radius: 4px;
  padding: 1rem 1.1rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: .75rem;
  box-shadow: var(--schaduw);
}
.kaart-vandaag { border-left: 3px solid var(--accent); }
.kaart-leeg { color: var(--gedempt); }
.leeg-tekst { margin: 0; font-size: .9rem; }

.kop {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: .2rem .75rem;
  flex-wrap: wrap;
}
.eyebrow {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .67rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--accent);
  white-space: nowrap;
}
.datum {
  font-size: .8rem;
  color: var(--gedempt);
  text-align: right;
  white-space: nowrap;
  margin-left: auto;
}

.plek { display: flex; flex-direction: column; gap: .1rem; }
.plek-naam {
  margin: 0;
  font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", sans-serif;
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.15;
  text-wrap: balance;
}
.plek-regio {
  margin: 0;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .73rem;
  color: var(--gedempt);
}
.notitie {
  margin: 0;
  font-size: .84rem;
  color: var(--gedempt);
  padding-left: .7rem;
  border-left: 2px solid var(--lijn);
}

.weer { display: flex; align-items: flex-start; gap: .85rem; }
.weer-icoon { color: var(--gedempt); flex: none; padding-top: .1rem; }
.ikoon { width: 2.1rem; height: 2.1rem; display: block; }
.weer-tekst { display: flex; flex-direction: column; gap: .28rem; flex: 1; min-width: 0; }
.weer-omschrijving {
  font-size: .94rem;
  font-weight: 500;
  display: flex;
  align-items: baseline;
  gap: .5rem;
  flex-wrap: wrap;
}
.dagmax {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .74rem;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
  color: var(--gedempt);
}
.neerslag {
  display: flex;
  align-items: baseline;
  gap: .55rem;
  flex-wrap: wrap;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}
.neerslag-mm { font-size: 1.05rem; font-weight: 500; color: var(--nat); }
.neerslag-mm.is-droog { color: var(--gedempt); }
.neerslag-kans { font-size: .74rem; color: var(--gedempt); }

/* ---- Neerslag per blok van twee uur ---- */
.regen { display: flex; flex-direction: column; gap: .45rem; }
.regen-kop {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: .3rem .6rem;
  flex-wrap: wrap;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .66rem;
  color: var(--gedempt);
}
.regen-titel { letter-spacing: .1em; text-transform: uppercase; }
.regen-piek {
  margin-left: auto;
  color: var(--nat);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.regen-strip { display: grid; grid-template-columns: repeat(8, 1fr); gap: 3px; }
.regen-kolom { display: flex; flex-direction: column; gap: .18rem; }
.regen-mm {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .58rem;
  line-height: 1.2;
  color: var(--nat);
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.regen-mm.is-leeg { color: var(--gedempt); opacity: .55; }
.regen-streek,
.regen-kmu {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .58rem;
  line-height: 1.2;
  color: var(--gedempt);
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.regen-streek { color: var(--inkt); opacity: .7; }
.regen-streek.is-leeg, .regen-kmu.is-leeg { opacity: .45; }
/* Het nachtblok beslaat tien uur in plaats van twee; dat mag je zien. */
.regen-kolom.is-nacht .regen-vak {
  background: var(--kaart-2);
  box-shadow: inset 0 0 0 1px var(--lijn);
}
.regen-vak {
  height: 34px;
  display: flex;
  align-items: flex-end;
  background: var(--nat-zacht);
  border-radius: 2px;
}
.regen-staaf {
  width: 100%;
  min-height: 2px;
  background: var(--nat);
  border-radius: 3px 3px 0 0;
}
/* Begintijd met de eindtijd eronder: "08:00 - 10:00" past niet op een kolom
   van 36 pixels, gestapeld wel. De eindtijd staat gedempt, zodat het paar als
   een bereik leest en niet als twee losse tijdstippen. */
.regen-tijd {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .55rem;
  line-height: 1.25;
  color: var(--gedempt);
  font-variant-numeric: tabular-nums;
}
.regen-tijd-tot { opacity: .5; }
.regen-droog {
  margin: 0;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .68rem;
  color: var(--gedempt);
}

/* ---- Vooruitblik dag 6 t/m 10 ---- */
.blik {
  background: var(--kaart);
  border: 1px solid var(--lijn);
  border-radius: 4px;
  padding: .9rem 1.1rem 1rem;
  box-shadow: var(--schaduw);
}
.blik-kop {
  display: flex;
  align-items: baseline;
  gap: .6rem;
  flex-wrap: wrap;
  padding-bottom: .5rem;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .67rem;
}
.blik-titel {
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--accent);
}
.blik-toelichting { color: var(--gedempt); }
.blik-rij {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .75rem;
  padding: .55rem 0;
  border-top: 1px solid var(--lijn);
}
.blik-links { display: flex; flex-direction: column; gap: .05rem; min-width: 0; }
.blik-datum {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .67rem;
  color: var(--gedempt);
}
.blik-plek {
  font-family: "IBM Plex Sans Condensed", "IBM Plex Sans", sans-serif;
  font-size: .98rem;
  font-weight: 600;
  line-height: 1.2;
}
.blik-rechts {
  display: flex;
  align-items: center;
  gap: .55rem;
  flex: none;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}
.blik-icoon { color: var(--gedempt); display: flex; }
.ikoon-klein { width: 1.3rem; height: 1.3rem; display: block; }
.blik-temp { font-size: 1.15rem; font-weight: 500; color: var(--tl); }
.blik-regen { font-size: .73rem; color: var(--nat); min-width: 3.4em; text-align: right; }
.blik-regen.is-droog { color: var(--gedempt); }

.spoor {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  align-items: stretch;
  gap: .25rem;
  padding-top: .8rem;
  border-top: 1px solid var(--lijn);
}
.stop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: .12rem;
  padding: .45rem .15rem;
  border-radius: 3px;
  text-align: center;
}
.stop-nadruk { background: var(--kaart-2); }
.stop-tijd {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .69rem;
  letter-spacing: .07em;
  color: var(--gedempt);
}
.stop-temp {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 1.65rem;
  font-weight: 500;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  color: var(--tl);
}
.graad { font-size: .78em; opacity: .5; }
.stop-uitleg { font-size: .67rem; color: var(--gedempt); line-height: 1.25; }
.pijl {
  align-self: center;
  width: 10px;
  height: 1px;
  background: var(--lijn);
  position: relative;
}
.pijl::after {
  content: "";
  position: absolute;
  right: 0;
  top: -2px;
  border-left: 4px solid var(--lijn);
  border-top: 2.5px solid transparent;
  border-bottom: 2.5px solid transparent;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .stop-temp,
  :root:not([data-theme="light"]) .blik-temp { color: var(--td); }
}
:root[data-theme="dark"] .stop-temp,
:root[data-theme="dark"] .blik-temp { color: var(--td); }

.voet {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .69rem;
  color: var(--gedempt);
  line-height: 1.7;
  border-top: 1px solid var(--lijn);
  padding-top: .9rem;
}

@media (max-width: 380px) {
  .titelblok h1 { font-size: 1.75rem; }
  .plek-naam { font-size: 1.3rem; }
  .stop-temp { font-size: 1.4rem; }
}
"""


APP_URL = "https://stijnbrasse-lab.github.io/weerpost/"

# Alleen voor de ingebakken reservekopie. De app heeft dit niet nodig: die
# ververst zichzelf en weet dus altijd hoe oud zijn cijfers zijn.
CSS_RESERVE = """
.verouderd {
  padding: .85rem 1rem;
  border-radius: 4px;
  background: var(--kaart);
  border: 1px solid var(--lijn);
  border-left: 3px solid var(--accent);
  box-shadow: var(--schaduw);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .72rem;
  line-height: 1.6;
  color: var(--gedempt);
}
.verouderd[hidden] { display: none; }
.verouderd a { color: var(--accent); }
.voet a { color: var(--accent); }
"""

# Let op: dit script wordt bewust in puur ASCII geschreven. De pagina gaat er
# met tekenentiteiten uit, en die worden binnen een script-blok niet ontleed.
SCRIPT_RESERVE = """
(function () {
  var gemaakt = new Date("%s");
  var uren = (Date.now() - gemaakt.getTime()) / 3600000;
  if (!(uren >= 36)) return;
  var el = document.getElementById("verouderd");
  if (!el) return;
  var dagen = Math.round(uren / 24);
  el.innerHTML = "Deze reservekopie is " + dagen + " dagen oud en wordt nu niet "
    + "ververst. Open <a href=\\"%s\\">de app</a> voor de actuele verwachting.";
  el.hidden = false;
})();
"""


def bouw_pagina(dagen, opgehaald):
    vandaag = dagen[0]["datum"]
    kaarten = "\n  ".join(kaart(d, vandaag) for d in dagen[:weerdata.DAGEN_VOORUIT])
    blik = vooruitblik(dagen[weerdata.DAGEN_VOORUIT:])
    stempel = opgehaald.strftime("%d-%m-%Y om %H:%M")

    return f"""<title>Pyreneeën Weerpost</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans+Condensed:wght@600&amp;family=IBM+Plex+Sans:wght@400;500&amp;display=swap">
<style>{CSS}{CSS_RESERVE}</style>

<main class="omslag">
  <header class="titelblok">
    <span class="reis">Pyreneeën 2026 &middot; 4 t/m 27 september</span>
    <h1>Weer op de slaapplek</h1>
    <p class="bijschrift">Vijf dagen in detail, daarna vijf op hoofdlijnen &mdash; steeds voor de camping waar je die nacht staat.</p>
  </header>

  <div id="verouderd" class="verouderd" hidden></div>

  {reisvoortgang(vandaag)}

  {kaarten}

  {blik}

  <footer class="voet">
    Bijgewerkt op {stempel} &middot; bron Open-Meteo<br>
    Alle tijden zijn lokale tijd. 03:00 is de nacht na de genoemde dag.<br>
    Dit is de reservekopie &middot; <a href="{APP_URL}">open de app</a>
  </footer>
</main>
<script>{SCRIPT_RESERVE % (opgehaald.strftime("%Y-%m-%dT%H:%M:%S"), APP_URL)}</script>
"""


def main():
    vandaag = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    dagen = weerdata.bouw_dagen(route.ROUTE, vandaag=vandaag)
    pagina = bouw_pagina(dagen, datetime.now())
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(pagina.encode("ascii", "xmlcharrefreplace").decode("ascii"))
    print(f"dashboard.html geschreven ({len(pagina)} tekens), peildatum {vandaag}")


if __name__ == "__main__":
    main()
