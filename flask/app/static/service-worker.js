// flask/app/static/service-worker.js
const CACHE_NAME = 'stocking-app-v1';
const STATIC_ASSETS = [
  '/',
  '/homepage',
  '/static/css/home.css',
  '/static/css/category.css',
  '/static/ico/stock_logo.png'
];

// install
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// activate
self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

// fetch - cache first for static
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // network-first for API calls (so notifications remain fresh)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(req).catch(() => caches.match(req))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(match => match || fetch(req).then(r => {
      if (req.method === 'GET' && req.url.startsWith(self.location.origin)) {
        caches.open(CACHE_NAME).then(cache => cache.put(req, r.clone()));
      }
      return r;
    })).catch(() => caches.match('/'))
  );
});


//old version here
// self.addEventListener("install", (event) => {
//   console.log("Service Worker installed");
//   self.skipWaiting();
// });

// self.addEventListener("activate", (event) => {
//   console.log("Service Worker activated");
// });

// self.addEventListener("fetch", (event) => {
//   event.respondWith(fetch(event.request));
// });