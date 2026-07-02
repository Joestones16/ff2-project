const CACHE_NAME = 'land-dispute-v1';
const urlsToCache = [
  '/',
  '/login.html',
  '/land_dispute.html',
  '/dashboard.html',
  '/all_cases.html',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});