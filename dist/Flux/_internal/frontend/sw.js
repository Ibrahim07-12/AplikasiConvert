const CACHE_NAME = "flux-v3";
const APP_SHELL = [
  "/", "/static/style.css", "/static/script.js", "/static/icons/faviconapp.png",
  "/static/icons/icon-192.png", "/static/icons/icon-512.png", "/manifest.webmanifest"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).catch(() => {
      if (event.request.mode === "navigate") return caches.match("/");
      return Response.error();
    }))
  );
});
