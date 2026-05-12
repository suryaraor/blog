---
layout: null
---
// Caching disabled — all requests served directly from network.
// On activate, all old caches are cleared automatically.
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// No fetch handler — every request goes straight to the network.
