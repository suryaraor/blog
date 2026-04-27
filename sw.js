---
layout: null
---
// Cache version auto-updates on every Jekyll build — forces fresh cache on new deployments
const CACHE = 'surya-blog-{{ site.time | date: "%Y%m%d%H%M" }}';
const OFFLINE_URL = '/offline.html';

// Pre-cache: all posts + core assets, baked in at build time by Jekyll
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/assets/css/main.css',
  '/assets/css/blog.css',
  '/assets/css/minima-overrides.css',
  '/assets/css/post-interactions.css',
  '/assets/js/post-interactions.js',
  '/manifest.json',
  '/profile.png',
  {% for post in site.posts %}'{{ post.url }}',
  {% endfor %}
];

// ── Install: pre-cache everything, activate immediately ──────────────────────
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then(cache => {
      // addAll is all-or-nothing; individual failures are absorbed so a missing
      // optional asset doesn't block the whole install
      return Promise.allSettled(
        PRECACHE_URLS.map(url => cache.add(url).catch(() => null))
      );
    })
  );
});

// ── Activate: delete stale caches, claim all open clients ────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys =>
        Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

// ── Fetch: serve from cache when offline, keep cache warm when online ─────────
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Ignore non-GET and non-http(s)
  if (req.method !== 'GET' || !url.protocol.startsWith('http')) return;

  // Cache-first for fonts (gstatic) and all static assets — they rarely change
  if (
    url.hostname === 'fonts.gstatic.com' ||
    url.hostname === 'fonts.googleapis.com' ||
    req.destination === 'font' ||
    req.destination === 'style' ||
    req.destination === 'script' ||
    req.destination === 'image'
  ) {
    event.respondWith(
      caches.match(req).then(cached => {
        if (cached) return cached;
        return fetch(req).then(res => {
          if (res.ok) {
            caches.open(CACHE).then(c => c.put(req, res.clone()));
          }
          return res;
        });
      })
    );
    return;
  }

  // Skip non-same-origin requests (comments API, analytics, etc.)
  if (url.hostname !== self.location.hostname) return;

  // Network-first for same-origin HTML pages:
  //   → online  : fresh page + update cache silently
  //   → offline : serve cached page if available, else offline fallback
  event.respondWith(
    fetch(req)
      .then(res => {
        if (res.ok) {
          caches.open(CACHE).then(c => c.put(req, res.clone()));
        }
        return res;
      })
      .catch(() =>
        caches.match(req).then(cached => cached || caches.match(OFFLINE_URL))
      )
  );
});
