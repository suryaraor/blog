---
layout: null
---
// Cache name is date-stamped at Jekyll build time — old cache is evicted on next deploy
const CACHE = 'surya-blog-{{ site.time | date: "%Y%m%d%H%M" }}';
const OFFLINE_URL = '/offline.html';

// All URLs baked in at Jekyll build time
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

// ── Install: pre-cache everything, take over immediately ─────────────────────
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then(cache =>
      Promise.allSettled(PRECACHE_URLS.map(url => cache.add(url).catch(() => null)))
    )
  );
});

// ── Activate: evict stale caches, claim clients, tell the page we're ready ───
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: 'window' }))
      .then(clients => clients.forEach(c => c.postMessage({ type: 'OFFLINE_READY' })))
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method !== 'GET' || !url.protocol.startsWith('http')) return;

  // Cache-first for fonts and static assets (CSS/JS/images) — safe to clone freely
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
            // Clone SYNCHRONOUSLY before any async work — avoids "body already used" error
            const clone = res.clone();
            caches.open(CACHE).then(c => c.put(req, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  // Skip non-same-origin (comments API, etc.)
  if (url.hostname !== self.location.hostname) return;

  // Network-first for same-origin HTML pages
  //   online  → fresh from network, cache updated in background
  //   offline → cached version, or offline fallback if page was never visited
  event.respondWith(
    fetch(req)
      .then(res => {
        if (res.ok) {
          // Clone SYNCHRONOUSLY before entering the async caches.open chain
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      })
      .catch(() =>
        caches.match(req).then(cached => cached || caches.match(OFFLINE_URL))
      )
  );
});
