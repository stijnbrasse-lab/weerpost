# -*- coding: utf-8 -*-
"""Bouwt de zelfstandige webapp (index.html) voor GitHub Pages.

Anders dan dashboard.py bakt deze versie de weerdata niet in: de pagina haalt
de verwachting zelf op bij Open-Meteo zodra je hem opent. Vormgeving, teksten
en weercodes komen uit dashboard.py, zodat er maar een bron van waarheid is.
"""
import json
from datetime import date

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
const DAGEN_KORT = ["ma", "di", "wo", "do", "vr", "za", "zo"];
const MAANDEN_KORT = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul",
                      "aug", "sep", "okt", "nov", "dec"];
const REIS_START = "__REIS_START__";
const REIS_EIND = "__REIS_EIND__";
const KM = __KM__;
const SPOOR = __SPOOR__;
// Vijf dagen met alle details, daarna nog vijf als ruwe vooruitblik.
const DAGEN_VOORUIT = 5;
const DAGEN_TOTAAL = 10;
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

function kortDatum(iso) {
  const d = uitIso(iso);
  return `${DAGEN_KORT[(d.getDay() + 6) % 7]} ${d.getDate()} ${MAANDEN_KORT[d.getMonth()]}`;
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
    hourly: "temperature_2m,precipitation,precipitation_probability,weather_code,"
          + "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
    daily: "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,weather_code",
    start_date: start,
    end_date: eind,
    timezone: "Europe/Paris",
  });
  // Open-Meteo stuurt geen cache-headers mee, dus zonder no-store mag de
  // browser zelf gokken hoe lang hij een antwoord hergebruikt. Elke verversing
  // moet echt langs het netwerk, anders kijk je naar oude cijfers.
  const r = await fetch(`https://api.open-meteo.com/v1/forecast?${p}`, { cache: "no-store" });
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

// Overdag per twee uur, daarna een nachtblok van 22:00 tot 08:00: dat zijn de
// uren dat je in de tent ligt, en die hoef je niet per twee uur te weten.
const DAG_UREN = [8, 10, 12, 14, 16, 18, 20];
const KOMPAS = ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"];

const windstreek = (graden) =>
  (graden === null || graden === undefined) ? null : KOMPAS[Math.round(graden / 45) % 8];

function samenvatting_blok(vp, indexen, van, tot, nacht) {
  if (!indexen.length) {
    return { van, tot, nacht, mm: null, kans: null, wind: null, streek: null, stoot: null };
  }
  let mm = 0, kans = 0, wind = null, richting = null, stoot = null;
  for (const i of indexen) {
    mm += vp.hourly.precipitation[i] || 0;
    const k = vp.hourly.precipitation_probability[i];
    if (k !== null && k !== undefined) kans = Math.max(kans, k);
    // De wind van het hardste uur, niet het gemiddelde: waait het in een van
    // de uren stevig, dan wil je dat zien en niet weggemiddeld krijgen.
    const s = vp.hourly.wind_speed_10m[i];
    if (s !== null && s !== undefined && (wind === null || s > wind)) {
      wind = s;
      richting = vp.hourly.wind_direction_10m[i];
      stoot = vp.hourly.wind_gusts_10m[i];
    }
  }
  return {
    van, tot, nacht,
    mm: Math.round(mm * 100) / 100,
    kans,
    wind: wind === null ? null : Math.round(wind),
    streek: windstreek(richting),
    stoot: stoot === null || stoot === undefined ? null : Math.round(stoot),
  };
}

function blokkenPerTweeUur(vp, iso) {
  const morgen = isoDatum(plusDagen(uitIso(iso), 1));
  const index = (dag, uur) =>
    vp.hourly.time.indexOf(`${dag}T${String(uur).padStart(2, "0")}:00`);

  const blokken = DAG_UREN.map((h) =>
    samenvatting_blok(vp, [index(iso, h), index(iso, h + 1)].filter((i) => i !== -1),
                      `${String(h).padStart(2, "0")}:00`,
                      `${String(h + 2).padStart(2, "0")}:00`, false));

  const nacht = [index(iso, 22), index(iso, 23)];
  for (let u = 0; u < 8; u++) nacht.push(index(morgen, u));
  blokken.push(samenvatting_blok(vp, nacht.filter((i) => i !== -1), "22:00", "08:00", true));
  return blokken;
}

async function bouwDagen() {
  const vandaag = new Date();
  const gevraagd = [];
  for (let i = 0; i < DAGEN_TOTAAL; i++) gevraagd.push(isoDatum(plusDagen(vandaag, i)));

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
      blokken: blokkenPerTweeUur(vp, iso),
      middag: opUur(vp, iso, 15),
      avond: opUur(vp, iso, 21),
      nacht: opUur(vp, volgende, 3),
    };
  });
}

// ---- weergave ----
function icoon(soort, klasse = "ikoon") {
  const pad = IKONEN[soort] || IKONEN["bewolkt"];
  return `<svg class="${klasse}" viewBox="0 0 24 25" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${pad}</svg>`;
}

const toonMm = (v) => v.toFixed(1).replace(".", ",");

function blokTitel(b) {
  const stukken = [`${b.van} - ${b.tot}`, `${toonMm(b.mm)} mm`,
                   `${Math.round(b.kans || 0)}% kans`];
  if (b.wind !== null && b.wind !== undefined) {
    let wind = `wind ${b.streek || "?"} ${b.wind} km/u`;
    if (b.stoot !== null && b.stoot !== undefined && b.stoot > b.wind) {
      wind += `, uitschieters ${b.stoot}`;
    }
    stukken.push(wind);
  }
  return ontsnap(stukken.join(" - "));
}

function tijdstrip(blokken) {
  const geldig = (blokken || []).filter((b) => b.mm !== null && b.mm !== undefined);
  if (!geldig.length) return "";
  // Een bewaarde verwachting van voor deze versie kent van/tot nog niet. Liever
  // geen strip dan een strip vol "undefined"; de volgende ophaal herstelt hem.
  if (!geldig[0].van) return "";

  // De schaal ijken op de daguren. Het nachtblok beslaat tien uur en zou de
  // daguren anders platdrukken; dat staafje mag tegen het plafond lopen, want
  // het getal eronder vertelt de werkelijke hoeveelheid.
  const overdag = geldig.filter((b) => !b.nacht);
  const schaal = Math.max(1.0, ...overdag.map((b) => b.mm), 0);

  const piek = geldig.reduce((a, b) => (b.mm > a.mm ? b : a));
  const samenvattingTekst = piek.mm < 0.1
    ? "droog"
    : (piek.nacht ? `piek ${toonMm(piek.mm)} mm in de nacht`
                  : `piek ${toonMm(piek.mm)} mm om ${piek.van}`);

  const voorlezen = [];
  const kolommen = blokken.map((b) => {
    const klasse = b.nacht ? "regen-kolom is-nacht" : "regen-kolom";
    const tijd = `<span class="regen-tijd"><span class="regen-tijd-van">${b.van}</span><span class="regen-tijd-tot">${b.tot}</span></span>`;
    if (b.mm === null || b.mm === undefined) {
      return `<div class="${klasse}"><div class="regen-vak"></div><span class="regen-mm is-leeg">&ndash;</span><span class="regen-streek is-leeg">&ndash;</span><span class="regen-kmu is-leeg">&ndash;</span>${tijd}</div>`;
    }
    const leeg = b.mm < 0.05;
    const deel = b.mm <= 0 ? 0 : Math.min(100, Math.max(8, Math.round((b.mm / schaal) * 100)));
    const staaf = deel ? `<div class="regen-staaf" style="height:${deel}%"></div>` : "";
    voorlezen.push(`${b.nacht ? "de nacht" : b.van + " tot " + b.tot}: ${toonMm(b.mm)} mm, wind ${b.streek || "onbekend"} ${b.wind === null ? "onbekend" : b.wind} kilometer per uur`);
    return `<div class="${klasse}" title="${blokTitel(b)}"><div class="regen-vak">${staaf}</div><span class="regen-mm${leeg ? " is-leeg" : ""}">${leeg ? "0" : toonMm(b.mm)}</span><span class="regen-streek">${b.streek || "&ndash;"}</span><span class="regen-kmu">${b.wind === null ? "&ndash;" : b.wind}</span>${tijd}</div>`;
  }).join("");

  return `<div class="regen">
    <div class="regen-kop">
      <span class="regen-titel">Neerslag mm &middot; wind km/u</span>
      <span class="regen-piek">${samenvattingTekst}</span>
    </div>
    <div class="regen-strip" role="img" aria-label="Per blok: ${ontsnap(voorlezen.join("; "))}">${kolommen}</div>
  </div>`;
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
  const neerslagTekst = droog ? "0 mm" : `${toonMm(mm)} mm`;
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
          ${droog ? "" : `<span class="neerslag-kans">in 24 uur</span>`}
          <span class="neerslag-kans">${Math.round(kans)}% kans op neerslag</span>
        </div>
      </div>
    </div>
    ${tijdstrip(dag.blokken)}
    <div class="spoor">
      ${blokTijdstip("15:00", "middag", dag.middag, false)}
      <span class="pijl" aria-hidden="true"></span>
      ${blokTijdstip("21:00", "avond", dag.avond, false)}
      <span class="pijl" aria-hidden="true"></span>
      ${blokTijdstip("03:00", "nacht erna", dag.nacht, true)}
    </div>
  </article>`;
}

// ---- Slingerende route bovenaan ----
// De vorm komt kant-en-klaar uit dashboard.py, zodat app en reservekopie
// dezelfde bochten tekenen. Alleen de stand per dag hangt van vandaag af.
const kmGetal = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");

function defenderSvg(x, y, naarRechts) {
  const s = SPOOR.defender_span / SPOOR.defender_breed;
  const dx = (SPOOR.defender_breed / 2) * s;
  const dy = SPOOR.defender_midden * s;
  const t = naarRechts
    ? `translate(${(x - dx).toFixed(2)} ${(y - dy).toFixed(2)}) scale(${s.toFixed(4)})`
    : `translate(${(x + dx).toFixed(2)} ${(y - dy).toFixed(2)}) scale(${(-s).toFixed(4)} ${s.toFixed(4)})`;
  return `<g class="defender" transform="${t}">${SPOOR.defender}</g>`;
}

function reisvoortgang() {
  const vandaag = isoDatum(new Date());
  const kmTotaal = Object.values(KM).reduce((s, n) => s + n, 0);
  // Gereden is wat achter de rug is: de dagen voor vandaag.
  const kmGereden = Object.entries(KM)
    .filter(([datum]) => datum < vandaag)
    .reduce((s, [, n]) => s + n, 0);

  let nummer = null, kop;
  if (vandaag < REIS_START) {
    const tot = Math.round((uitIso(REIS_START) - uitIso(vandaag)) / 86400000);
    kop = tot === 1 ? "Vertrek morgen" : `Vertrek over ${tot} dagen`;
  } else if (vandaag > REIS_EIND) {
    kop = "Reis afgerond";
  } else {
    nummer = Math.round((uitIso(vandaag) - uitIso(REIS_START)) / 86400000) + 1;
    kop = `Dag ${nummer} van ${SPOOR.punten.length}`;
  }

  const voorbij = vandaag > REIS_EIND;
  let wagen = "";
  const merken = [];
  const strepen = SPOOR.punten.map(([x, y], i) => {
    const dag = i + 1;
    const nu = nummer !== null && dag === nummer;
    const km = SPOOR.km[i];
    merken.push(`<text class="spoor-datum${nu ? " is-nu" : ""}" x="${x.toFixed(2)}" y="${(y + 6.6).toFixed(2)}" text-anchor="middle">${SPOOR.labels[i]}</text>`
              + `<text class="spoor-km${km ? "" : " is-nul"}" x="${x.toFixed(2)}" y="${(y + 9.9).toFixed(2)}" text-anchor="middle">${km}</text>`);
    if (nu) {
      // Op de plek van vandaag staat de Defender in plaats van een streep.
      wagen = defenderSvg(x, y, Math.floor(i / SPOOR.per_rij) % 2 === 0);
      return "";
    }
    const stand = nummer === null
      ? (voorbij ? "was" : "komt")
      : (dag < nummer ? "was" : "komt");
    return `<rect class="streep streep-${stand}" x="${(x - 1.2).toFixed(2)}" y="${(y - SPOOR.hoog / 2).toFixed(2)}" width="2.4" height="${SPOOR.hoog}" rx="1.2"></rect>`;
  }).join("");

  // De lijn gekleurd tot waar we staan; dat leest als afgelegde weg.
  const afgelegd = nummer === null
    ? (voorbij ? SPOOR.totaal : 0)
    : SPOOR.lengtes[nummer - 1];
  const afgelegdeLijn = afgelegd > 0
    ? `<path class="spoor-lijn spoor-af" d="${SPOOR.pad}" fill="none" stroke-dasharray="${afgelegd} ${SPOOR.totaal}"></path>`
    : "";

  return `<section class="voortgang">
    <div class="voortgang-kop">
      <span class="voortgang-titel">Waar we zijn</span>
      <span class="voortgang-km">${kmGetal(kmGereden)} van ${kmGetal(kmTotaal)} km gereden</span>
    </div>
    <p class="voortgang-dag">${kop}</p>
    <svg class="spoor" viewBox="0 0 100 ${SPOOR.hoogte}" role="img" aria-label="Routevoortgang: ${ontsnap(kop)}, ${kmGetal(kmGereden)} van ${kmGetal(kmTotaal)} kilometer gereden">
      <path class="spoor-lijn" d="${SPOOR.pad}" fill="none"></path>${afgelegdeLijn}${strepen}${merken.join("")}${wagen}
    </svg>
  </section>`;
}

function vooruitblik(dagen) {
  // Bewust karig van vorm: op deze afstand is het een richting, geen planning.
  const rijen = dagen.filter((d) => d.etappe).map((dag) => {
    const [omschrijving, soort] = WEER[String(dag.code)] || ["Onbekend", "bewolkt"];
    const mm = dag.neerslag_mm || 0;
    const droog = mm < 0.2;
    const [licht, donker] = tempKleuren(dag.max_temp);
    return `<div class="blik-rij">
      <div class="blik-links">
        <span class="blik-datum">${kortDatum(dag.datum)}</span>
        <span class="blik-plek">${ontsnap(dag.etappe.plaats)}</span>
      </div>
      <div class="blik-rechts">
        <span class="blik-icoon" title="${ontsnap(omschrijving)}">${icoon(soort, "ikoon-klein")}</span>
        <span class="blik-temp" style="--tl:${licht};--td:${donker}">${toonTemp(dag.max_temp)}<span class="graad">&deg;</span></span>
        <span class="blik-regen${droog ? " is-droog" : ""}">${droog ? "0" : toonMm(mm)} mm</span>
      </div>
    </div>`;
  }).join("");

  if (!rijen) return "";
  return `<section class="blik">
    <div class="blik-kop">
      <span class="blik-titel">Vooruitblik</span>
      <span class="blik-toelichting">richting, geen planning</span>
    </div>${rijen}
  </section>`;
}

function teken(dagen, opgehaaldOp, uitOpslag) {
  const vandaagIso = isoDatum(new Date());
  document.getElementById("inhoud").innerHTML =
    reisvoortgang()
    + dagen.slice(0, DAGEN_VOORUIT).map((d) => kaart(d, vandaagIso)).join("")
    + vooruitblik(dagen.slice(DAGEN_VOORUIT));

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
    reisdagen = (date.fromisoformat(route.REIS_EIND)
                 - date.fromisoformat(route.REIS_START)).days + 1
    script = (SCRIPT
              .replace("__REIS_START__", route.REIS_START)
              .replace("__REIS_EIND__", route.REIS_EIND)
              .replace("__KM__", json.dumps(route.KM))
              .replace("__SPOOR__", json.dumps(dict(dashboard.bouw_spoor(reisdagen),
                                      labels=dashboard.spoor_labels(),
                                      km=dashboard.spoor_km())))
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
<meta name="robots" content="noindex, nofollow">
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
    <p class="bijschrift">4 t/m 27 september. Vijf dagen in detail, daarna vijf op hoofdlijnen &mdash; steeds voor de camping waar je die nacht staat.</p>
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
