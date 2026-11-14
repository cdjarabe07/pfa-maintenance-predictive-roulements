/* Service worker du jumeau numérique : l'application s'ouvre même sans réseau.
   Pages : réseau d'abord (on voit toujours la dernière version), cache en secours.
   Fichiers statiques du même site : cache d'abord, mis à jour en arrière-plan.
   Pour forcer une mise à jour du cache, changer VERSION. */
const VERSION = 'v2';
const CACHE = 'jumeau-' + VERSION;
const PRECACHE = ['/', '/index.html', '/jumeau_roulements.html', '/manifest.webmanifest', '/fond_roulement.jpg',
  '/icons/icon.svg', '/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-monochrome-512.png', '/icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('jumeau-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET' || new URL(r.url).origin !== location.origin) return;
  if (r.mode === 'navigate') {
    e.respondWith(fetch(r).then(res => { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); return res; })
      .catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || caches.match('/index.html'))));
    return;
  }
  e.respondWith(caches.match(r).then(m => {
    const net = fetch(r).then(res => { if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); } return res; }).catch(() => m);
    return m || net;
  }));
});
