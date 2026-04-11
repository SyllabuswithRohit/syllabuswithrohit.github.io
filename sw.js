const CACHE_NAME = 'swr-cache-v1';
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
    caches.open(CACHE_NAME)
      .then(cache => {
        // Cache silently (do not fail if some map/CDN fails)
        urlsToCache.forEach(url => {
          cache.add(url).catch(err => console.log('SW: cache error', url, err));
        });
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
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Navigation requests fall back to network, then cache.
  // Book pages will dynamically cache themselves as they are visited.
  if (event.request.method !== 'GET') return;
  
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).then(fetchRes => {
        return caches.open(CACHE_NAME).then(cache => {
          // Cache newly visited books automatically
          if(event.request.url.includes('/books/') || event.request.url.includes('.html')) {
             cache.put(event.request, fetchRes.clone());
          }
          return fetchRes;
        });
      }).catch(() => {
         // Offline fallback could go here
      });
    })
  );
});
