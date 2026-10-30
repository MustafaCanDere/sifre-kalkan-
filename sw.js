// Uygulama dosyalarını önbelleğe alır, internet yokken de açılır.
// Şifre kontrolü isteği önbelleğe alınmaz.
const SURUM = "sifre-kalkani-v1";
const DOSYALAR = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];
self.addEventListener("install", e => e.waitUntil(caches.open(SURUM).then(c => c.addAll(DOSYALAR)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(k => Promise.all(k.filter(x => x !== SURUM).map(x => caches.delete(x)))).then(() => self.clients.claim())
));
self.addEventListener("fetch", e => {
  if (new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(r => {
    const kopya = r.clone();
    caches.open(SURUM).then(c => c.put(e.request, kopya));
    return r;
  }).catch(() => caches.match(e.request)));
});
