# Pyreneeën Weerpost

Weerdashboard voor de Pyreneeënreis van 4 t/m 27 september 2026. Toont vijf
dagen vooruit, steeds voor de camping waar we die nacht staan: neerslag, en de
temperatuur om 15:00, 21:00 en 03:00 in de nacht erna.

De pagina haalt de verwachting zelf op bij [Open-Meteo](https://open-meteo.com)
zodra je hem opent. Er is dus geen server, geen sleutel en geen geplande taak
nodig. De laatst opgehaalde verwachting blijft in de browser bewaard, zodat er
op een camping zonder bereik nog steeds iets te zien is.

## Op je telefoon zetten

Open de pagina en kies *Zet op beginscherm* (iPhone, via Safari) of
*Toevoegen aan startscherm* (Android, via Chrome). Hij opent dan schermvullend,
met het tentje als icoon.

## Opbouw

| Bestand | Wat het doet |
| --- | --- |
| `route.py` | De reisroute: per etappe de overnachtingsplaats met coördinaten, plus de dagnotities. Dit is het enige bestand dat je aanpast als de route wijzigt. |
| `weerdata.py` | Haalt de verwachting op bij Open-Meteo. Alleen nodig voor de ingebakken variant. |
| `dashboard.py` | Vormgeving (CSS), weercodes en icoontjes. Bouwt daarnaast `dashboard.html`, een variant met de data er statisch in. |
| `bouw_app.py` | Bouwt `index.html`: dezelfde vormgeving, maar de data wordt in de browser opgehaald. Dit is de versie die online staat. |
| `maak_icoon.py` | Tekent de app-icoontjes als PNG. |
| `sw.js` | Service worker, zodat de app ook zonder bereik opent. |

## Opnieuw bouwen

Na een wijziging in `route.py` of in de vormgeving:

```bash
python bouw_app.py
```

Commit daarna `index.html`; GitHub Pages zet het binnen een minuut online.

De icoontjes hoef je alleen opnieuw te maken als het ontwerp wijzigt:

```bash
python maak_icoon.py
```
