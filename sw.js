// Service worker: zorgt dat de app zelf opent zonder bereik.
// De weerdata wordt hier bewust NIET bewaard; dat doet de pagina zelf in
// localStorage, zodat je altijd ziet wanneer de cijfers zijn opgehaald.

const VERSIE = "weerpost-v1";
const SCHIL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icoon-180.png",
  "./icoon-192.png",
  "./icoon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(VERSIE)
      .then((c) => c.addAll(SCHIL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((namen) => Promise.all(
        namen.filter((n) => n !== VERSIE).map((n) => caches.delete(n))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // Alleen onze eigen bestanden; weerverzoeken gaan altijd rechtstreeks.
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;

  // Eerst het netwerk, zodat een nieuwe versie meteen doorkomt; lukt dat niet,
  // dan de opgeslagen kopie.
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const kopie = res.clone();
        caches.open(VERSIE).then((c) => c.put(e.request, kopie)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html")))
  );
});
