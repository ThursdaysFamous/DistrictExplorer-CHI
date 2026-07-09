// App-shell cache only. Never cache live district/roster API responses —
// a stale cached roster could name the wrong officeholder, and this app's
// rule is that officeholder data is never guessed or served stale.
const CACHE_NAME = "district-explorer-shell-v1";
const SHELL_URLS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js",
];

self.addEventListener("install", (event) => {
  // Cache each shell URL independently so one unreachable resource (e.g. a
  // CDN blip) doesn't fail the whole install — addAll() would abort atomically.
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(
        SHELL_URLS.map((url) => cache.add(url).catch(() => {}))
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isShellRequest = SHELL_URLS.some((shellUrl) => {
    const resolved = new URL(shellUrl, self.registration.scope);
    return resolved.href === url.href;
  });

  if (!isShellRequest) return; // let every other request (all live API calls) hit the network normally

  // Network-first for the shell. index.html carries the embedded rosters
  // (school-board / IL Senate+House / CPD), which the weekly CI refreshes —
  // a cache-first shell would show every returning visitor last deploy's
  // officeholders, exactly the staleness this file's header forbids. Online
  // this matches a plain page load and refreshes the cache; offline it falls
  // back to the last good cached shell so the app still boots.
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
