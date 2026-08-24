/* Root service worker — A KILL SWITCH, not a cache.
 *
 * The app moved from this origin's root to /il/ (docs/DEV_PROCESS_ASSESSMENT.md,
 * stage R2.3) and registers its own worker at /il/sw.js with scope /il/. This
 * file exists only so that browsers holding the OLD root registration have
 * something to update to that takes itself out of the way.
 *
 * Returning visitors are never stranded: the old root worker served navigations
 * network-first, so the redirect stub at / reaches them on their first online
 * visit whether or not this update has landed yet. What this file prevents is
 * the slower problem — a permanent second worker at / that competes with the
 * /il/ instance over one origin's CacheStorage.
 *
 * THREE DELIBERATE ABSENCES, each load-bearing:
 *
 * 1. NO fetch handler. A worker with no fetch handler is skipped entirely for
 *    navigations, so the root stub is served straight from the network even in
 *    the window before unregister() resolves. It also makes an offline redirect
 *    loop structurally impossible: the old worker's navigation fallback was
 *    "serve the cached shell at ./", which — once ./ IS the redirect stub —
 *    would have answered an offline /il/ request with a page that redirects to
 *    /il/, forever. Root scope covers /il/ until the /il/ registration claims
 *    its client, so that was a real window, not a hypothetical one.
 *
 * 2. NO cache prefix sweep. CacheStorage is per-ORIGIN. Deleting by prefix, or
 *    by iterating caches.keys(), would take the /il/ instance's precache with
 *    it. Only exact names this root ever used are removed. (The /il/ instance
 *    was also renamed to districtry-il-shell-* in the same change, so neither
 *    side can name the other's cache even by accident — and the engine's own
 *    "delete every cache that isn't mine" activate step stops being a weapon
 *    the moment two instances share an origin, which is exactly what /ny/ and
 *    /ca/ now do.)
 *
 * 3. NO re-registration from the stub page. The browser's own on-navigation
 *    update check is what delivers this file; a register() call in the stub
 *    would reinstall the killer on every visit only for it to unregister
 *    itself again.
 */

const LEGACY_CACHES = ["district-explorer-shell-v51"];

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    await Promise.all(LEGACY_CACHES.map((name) => caches.delete(name)));
    await self.registration.unregister();
    // Drop any window this worker still controls back to a normal, uncontrolled
    // load — otherwise a tab opened before the update keeps the dead worker for
    // the rest of its life.
    const windows = await self.clients.matchAll({ type: "window" });
    windows.forEach((client) => client.navigate(client.url));
  })());
});
