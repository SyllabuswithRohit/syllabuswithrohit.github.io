const CACHE_NAME = 'swr-cache-v2';
const urlsToCache = [
  './index.html',
  './manifest.json',
  './myprofile.jpg',
  './qr.png',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400..700;1,400..700&display=swap',
  'https://cdn.tailwindcss.com'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      // Local shell assets and optional CDN resources are attempted independently.
      // One unavailable external resource must not prevent the service worker from installing.
      await Promise.allSettled(urlsToCache.map(url => cache.add(url)));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
          return undefined;
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) return cachedResponse;

      return fetch(event.request)
        .then(fetchResponse => {
          const requestUrl = new URL(event.request.url);
          const isSameOrigin = requestUrl.origin === self.location.origin;
          const isCacheablePage =
            isSameOrigin &&
            fetchResponse.ok &&
            (requestUrl.pathname.includes('/books/') || requestUrl.pathname.endsWith('.html'));

          if (!isCacheablePage) return fetchResponse;

          return caches.open(CACHE_NAME).then(cache => {
            return cache.put(event.request, fetchResponse.clone()).then(() => fetchResponse);
          });
        })
        .catch(async () => {
          // Previously visited pages are returned by the cache-first branch above. For a new
          // offline navigation, return the local Library shell instead of resolving undefined.
          if (event.request.mode === 'navigate') {
            const shell = await caches.match('./index.html');
            if (shell) return shell;
          }
          return new Response('Offline resource unavailable.', {
            status: 504,
            statusText: 'Offline',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        });
    })
  );
});
