# -*- coding: utf-8 -*-
"""Bouwt de zelfstandige webapp (index.html) voor GitHub Pages.

Anders dan dashboard.py bakt deze versie de weerdata niet in: de pagina haalt
de verwachting zelf op bij Open-Meteo zodra je hem opent. Vormgeving, teksten
en weercodes komen uit dashboard.py, zodat er maar een bron van waarheid is.
"""
import json

import dashboard
import route

UITVOER = "index.html"

EXTRA_CSS = """
.balkje {
  display: flex;
  align-items: center;
  gap: .6rem;
  padding: .6rem .8rem;
  border-radius: 4px;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .72rem;
  line-height: 1.5;
  background: var(--kaart);
  border: 1px solid var(--lijn);
  color: var(--gedempt);
}
.balkje-waarschuwing { border-left: 3px solid var(--accent); }
.balkje[hidden] { display: none; }

.kopregel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.ververs {
  flex: none;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .68rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  color: var(--accent);
  background: transparent;
  border: 1px solid var(--lijn);
  border-radius: 3px;
  padding: .45rem .7rem;
  cursor: pointer;
  transition: border-color .15s ease;
}
.ververs:hover { border-color: var(--accent); }
.ververs:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.ververs[disabled] { opacity: .5; cursor: default; }

.laden {
  padding: 2.5rem 0;
  text-align: center;
  color: var(--gedempt);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: .78rem;
}
.laden-punt {
  display: inline-block;
  width: 6px; height: 6px;
  margin: 0 2px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulseren 1.2s ease-in-out infinite;
}
.laden-punt:nth-child(2) { animation-delay: .15s; }
.laden-punt:nth-child(3) { animation-delay: .3s; }
@keyframes pulseren {
  0%, 100% { opacity: .25; }
  50% { opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .laden-punt { animation: none; opacity: .6; }
  .ververs { transition: none; }
}
"""

SCRIPT = r"""
const ROUTE = __ROUTE__;
const NOTITIES = __NOTITIES__;
const WEER = __WEER__;
const IKONEN = __IKONEN__;
const TEMP_SCHAAL = __TEMP_SCHAAL__;

const DAGEN_NL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"];
const MAANDEN_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
                    "augustus", "september", "oktober", "november", "december"];
const REIS_START = "2026-09-04";
const REIS_EIND = "2026-09-27";
const DAGEN_VOORUIT = 5;
const OPSLAG_SLEUTEL = "weerpost-laatste";

// ---- datumhulpjes, allemaal in lokale tijd ----
const isoDatum = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const plusDagen = (d, n) => { const k = new Date(d); k.setDate(k.getDate() + n); return k; };
const uitIso = (s) => { const [j, m, d] = s.split("-").map(Number); return new Date(j, m - 1, d); };

function nlDatum(iso) {
  const d = uitIso(iso);
  const wd = (d.getDay() + 6) % 7;  // zondag=0 omzetten naar maandag=0
  return `${DAGEN_NL[wd]} ${d.getDate()} ${MAANDEN_NL[d.getMonth()]}`;
}

function reisdagNummer(iso) {
  if (iso < REIS_START || iso > REIS_EIND) return null;
  return Math.round((uitIso(iso) - uitIso(REIS_START)) / 86400000) + 1;
}

function etappeVoor(iso) {
  return ROUTE.find((e) => iso >= e.van && iso <= e.tot) || null;
}

function tempKleuren(t) {
  if (t === null || t === undefined) return ["var(--gedempt)", "var(--gedempt)"];
  for (const [grens, licht, donker] of TEMP_SCHAAL) {
    if (t <= grens) return [licht, donker];
  }
  const laatste = TEMP_SCHAAL[TEMP_SCHAAL.length - 1];
  return [laatste[1], laatste[2]];
}

const ontsnap = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const toonTemp = (t) => (t === null || t === undefined) ? "--" : String(Math.round(t));

// ---- data ophalen ----
async function haalVoorspelling(etappe, start, eind) {
  const p = new URLSearchParams({
    latitude: etappe.lat,
    longitude: etappe.lon,
    hourly: "temperature_2m,precipitation,precipitation_probability,weather_code",
    daily: "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,weather_code",
    start_date: start,
    end_date: eind,
    timezone: "Europe/Paris",
  });
  const r = await fetch(`https://api.open-meteo.com/v1/forecast?${p}`);
  if (!r.ok) throw new Error(`Open-Meteo gaf status ${r.status}`);
  return r.json();
}

function opUur(vp, isoDag, uur) {
  const sleutel = `${isoDag}T${String(uur).padStart(2, "0")}:00`;
  const i = vp.hourly.time.indexOf(sleutel);
  if (i === -1) return null;
  return {
    temp: vp.hourly.temperature_2m[i],
    kans: vp.hourly.precipitation_probability[i],
    code: vp.hourly.weather_code[i],
  };
}

async function bouwDagen() {
  const vandaag = new Date();
  const gevraagd = [];
  for (let i = 0; i < DAGEN_VOORUIT; i++) gevraagd.push(isoDatum(plusDagen(vandaag, i)));

  // Groepeer per plaats: een aanroep per locatie in plaats van per dag.
  const groepen = new Map();
  for (const iso of gevraagd) {
    const e = etappeVoor(iso);
    if (!e) continue;
    if (!groepen.has(e.plaats)) groepen.set(e.plaats, { etappe: e, datums: [] });
    groepen.get(e.plaats).datums.push(iso);
  }

  const voorspellingen = new Map();
  await Promise.all([...groepen.entries()].map(async ([naam, blok]) => {
    const eerste = blok.datums[0];
    // Een dag extra, want 03:00 hoort bij de nacht na de laatste dag.
    const laatste = isoDatum(plusDagen(uitIso(blok.datums[blok.datums.length - 1]), 1));
    voorspellingen.set(naam, await haalVoorspelling(blok.etappe, eerste, laatste));
  }));

  return gevraagd.map((iso) => {
    const etappe = etappeVoor(iso);
    if (!etappe) return { datum: iso, etappe: null };
    const vp = voorspellingen.get(etappe.plaats);
    const i = vp.daily.time.indexOf(iso);
    const volgende = isoDatum(plusDagen(uitIso(iso), 1));
    return {
      datum: iso,
      etappe,
      hoogte: vp.elevation,
      neerslag_mm: vp.daily.precipitation_sum[i],
      neerslag_kans: vp.daily.precipitation_probability_max[i],
      code: vp.daily.weather_code[i],
      max_temp: vp.daily.temperature_2m_max[i],
      middag: opUur(vp, iso, 15),
      avond: opUur(vp, iso, 21),
      nacht: opUur(vp, volgende, 3),
    };
  });
}

// ---- weergave ----
function icoon(soort) {
  const pad = IKONEN[soort] || IKONEN["bewolkt"];
  return `<svg class="ikoon" viewBox="0 0 24 25" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${pad}</svg>`;
}

function blokTijdstip(label, toelichting, meting, nadruk) {
  const t = meting ? meting.temp : null;
  const [licht, donker] = tempKleuren(t);
  return `<div class="stop${nadruk ? " stop-nadruk" : ""}">
    <div class="stop-tijd">${label}</div>
    <div class="stop-temp" style="--tl:${licht};--td:${donker}">${toonTemp(t)}<span class="graad">&deg;</span></div>
    <div class="stop-uitleg">${toelichting}</div>
  </div>`;
}

function kaart(dag, vandaagIso) {
  const nummer = reisdagNummer(dag.datum);
  const eyebrow = nummer ? `Dag ${nummer}` : "Voor vertrek";
  const isVandaag = dag.datum === vandaagIso;

  if (!dag.etappe) {
    return `<article class="kaart kaart-leeg">
      <div class="kop"><span class="eyebrow">${eyebrow}</span><span class="datum">${nlDatum(dag.datum)}</span></div>
      <p class="leeg-tekst">Geen overnachting gepland.</p>
    </article>`;
  }

  const [omschrijving, soort] = WEER[String(dag.code)] || ["Onbekend", "bewolkt"];
  const mm = dag.neerslag_mm || 0;
  const kans = dag.neerslag_kans || 0;
  const droog = mm < 0.2;
  const neerslagTekst = droog ? "0 mm" : `${mm.toFixed(1).replace(".", ",")} mm`;
  const balk = Math.min(100, (mm / 15) * 100);
  const notitie = NOTITIES[dag.datum];

  let regio = ontsnap(dag.etappe.land || "");
  if (dag.hoogte !== undefined && dag.hoogte !== null) regio += ` &middot; ${Math.round(dag.hoogte)} m`;

  return `<article class="kaart${isVandaag ? " kaart-vandaag" : ""}">
    <div class="kop">
      <span class="eyebrow">${eyebrow}${isVandaag ? " &middot; vandaag" : ""}</span>
      <span class="datum">${nlDatum(dag.datum)}</span>
    </div>
    <div class="plek">
      <h2 class="plek-naam">${ontsnap(dag.etappe.plaats)}</h2>
      <p class="plek-regio">${regio}</p>
    </div>
    ${notitie ? `<p class="notitie">${ontsnap(notitie)}</p>` : ""}
    <div class="weer">
      <div class="weer-icoon">${icoon(soort)}</div>
      <div class="weer-tekst">
        <div class="weer-omschrijving">${ontsnap(omschrijving)}<span class="dagmax">warmste piek ${toonTemp(dag.max_temp)}&deg;</span></div>
        <div class="neerslag">
          <span class="neerslag-mm${droog ? " is-droog" : ""}">${neerslagTekst}</span>
          <span class="neerslag-kans">${Math.round(kans)}% kans op neerslag</span>
        </div>
        <div class="balk" role="img" aria-label="Neerslag ${neerslagTekst}">
          <div class="balk-vulling" style="width:${balk.toFixed(0)}%"></div>
        </div>
      </div>
    </div>
    <div class="spoor">
      ${blokTijdstip("15:00", "middag", dag.middag, false)}
      <span class="pijl" aria-hidden="true"></span>
      ${blokTijdstip("21:00", "avond", dag.avond, false)}
      <span class="pijl" aria-hidden="true"></span>
      ${blokTijdstip("03:00", "nacht erna", dag.nacht, true)}
    </div>
  </article>`;
}

function samenvatting(dagen) {
  const eerste = dagen.find((d) => d.etappe && d.nacht);
  if (!eerste) return "";
  const [licht, donker] = tempKleuren(eerste.nacht.temp);
  const hoogte = (eerste.hoogte !== undefined && eerste.hoogte !== null)
    ? `${Math.round(eerste.hoogte)} m boven zeeniveau` : "";
  return `<section class="vannacht">
    <div class="vannacht-getal" style="--tl:${licht};--td:${donker}">${toonTemp(eerste.nacht.temp)}<span class="graad">&deg;</span></div>
    <div class="vannacht-tekst">
      <span class="vannacht-label">Vannacht om 03:00</span>
      <span class="vannacht-plek">${ontsnap(eerste.etappe.plaats)}</span>
      <span class="vannacht-extra">${hoogte}</span>
    </div>
  </section>`;
}

function teken(dagen, opgehaaldOp, uitOpslag) {
  const vandaagIso = isoDatum(new Date());
  document.getElementById("inhoud").innerHTML =
    samenvatting(dagen) + dagen.map((d) => kaart(d, vandaagIso)).join("");

  const stempel = new Date(opgehaaldOp);
  const wanneer = `${String(stempel.getDate()).padStart(2, "0")}-${String(stempel.getMonth() + 1).padStart(2, "0")} om ${String(stempel.getHours()).padStart(2, "0")}:${String(stempel.getMinutes()).padStart(2, "0")}`;

  const melding = document.getElementById("melding");
  if (uitOpslag) {
    melding.hidden = false;
    melding.className = "balkje balkje-waarschuwing";
    melding.textContent = `Geen verbinding. Dit is de verwachting van ${wanneer}; trek hem niet te serieus.`;
  } else {
    melding.hidden = true;
  }
  document.getElementById("stempel").textContent = `Bijgewerkt ${wanneer}`;
}

async function laden() {
  const knop = document.getElementById("ververs");
  knop.disabled = true;
  try {
    const dagen = await bouwDagen();
    const opgehaaldOp = new Date().toISOString();
    try {
      localStorage.setItem(OPSLAG_SLEUTEL, JSON.stringify({ dagen, opgehaaldOp }));
    } catch (e) { /* privemodus of volle opslag: niet erg, alleen geen cache */ }
    teken(dagen, opgehaaldOp, false);
  } catch (fout) {
    let bewaard = null;
    try { bewaard = JSON.parse(localStorage.getItem(OPSLAG_SLEUTEL) || "null"); } catch (e) {}
    if (bewaard && bewaard.dagen) {
      teken(bewaard.dagen, bewaard.opgehaaldOp, true);
    } else {
      document.getElementById("inhoud").innerHTML = "";
      const melding = document.getElementById("melding");
      melding.hidden = false;
      melding.className = "balkje balkje-waarschuwing";
      melding.textContent = "De verwachting kon niet worden opgehaald en er staat nog niets in het geheugen. Probeer het opnieuw zodra je bereik hebt.";
    }
  } finally {
    knop.disabled = false;
  }
}

document.getElementById("ververs").addEventListener("click", laden);
// Bij terugkeren naar de app opnieuw ophalen, zodat je nooit naar oude cijfers kijkt.
document.addEventListener("visibilitychange", () => { if (!document.hidden) laden(); });
laden();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => { /* offline-cache is een extraatje */ });
  });
}
"""


def bouw():
    script = (SCRIPT
              .replace("__ROUTE__", json.dumps(route.ROUTE, ensure_ascii=False))
              .replace("__NOTITIES__", json.dumps(route.NOTITIES, ensure_ascii=False))
              .replace("__WEER__", json.dumps({str(k): list(v) for k, v in dashboard.WEER.items()}, ensure_ascii=False))
              .replace("__IKONEN__", json.dumps(dashboard.IKONEN, ensure_ascii=False))
              .replace("__TEMP_SCHAAL__", json.dumps([list(r) for r in dashboard.TEMP_SCHAAL])))

    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pyreneeën Weerpost</title>
<meta name="description" content="Weersverwachting vijf dagen vooruit voor de camping waar we die nacht staan.">
<meta name="theme-color" content="#E9ECEF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0D1218" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icoon-180.png">
<link rel="icon" href="icoon-192.png" type="image/png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Weerpost">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans+Condensed:wght@600&amp;family=IBM+Plex+Sans:wght@400;500&amp;display=swap">
<style>{dashboard.CSS}{EXTRA_CSS}</style>
</head>
<body>
<main class="omslag">
  <header class="titelblok">
    <div class="kopregel">
      <div>
        <span class="reis">Pyreneeën 2026</span>
        <h1>Weer op de slaapplek</h1>
      </div>
      <button type="button" id="ververs" class="ververs">Ververs</button>
    </div>
    <p class="bijschrift">4 t/m 27 september. Vijf dagen vooruit, steeds voor de camping waar je die nacht staat.</p>
  </header>

  <div id="melding" class="balkje" hidden></div>

  <div id="inhoud">
    <div class="laden">
      Verwachting ophalen
      <span class="laden-punt"></span><span class="laden-punt"></span><span class="laden-punt"></span>
    </div>
  </div>

  <footer class="voet">
    <span id="stempel">Nog niet opgehaald</span> &middot; bron Open-Meteo<br>
    Alle tijden zijn lokale tijd. 03:00 is de nacht na de genoemde dag.
  </footer>
</main>
<script>{script}</script>
</body>
</html>
"""


def main():
    with open(UITVOER, "w", encoding="utf-8") as f:
        f.write(bouw())
    print(f"{UITVOER} geschreven")


if __name__ == "__main__":
    main()
