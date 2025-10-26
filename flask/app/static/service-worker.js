const CACHE_NAME = 'stocking-app-cache-v5'; 
const OFFLINE_URL = '/waiting';

// (ASSETS_TO_CACHE ถูกลบออกแล้ว เพราะเราใช้แบบอัตโนมัติ)

// Files to exclude from caching
const EXCLUDED_FILES = [
    '/js/darkmode.js',
    '/js/language.js'
];


// Install event: Fetch the dynamic manifest and cache all assets robustly
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(async (cache) => {
                console.log('Opened cache');
                
                // 1. Cache the offline fallback page (critical)
                try {
                    await cache.add(new Request(OFFLINE_URL, {cache: 'reload'}));
                } catch (err) {
                    console.error('Failed to cache OFFLINE_URL:', err);
                }

                // 2. Fetch the dynamic asset list from our Flask route
                console.log('Fetching dynamic asset manifest...');
                try {
                    const response = await fetch('/asset-manifest.json');
                    if (!response.ok) {
                        throw new Error('Failed to fetch asset manifest');
                    }
                    const assetsToCache = await response.json();
                    
                    console.log('Caching all assets from manifest...');
                    
                    // 3. Loop and cache one-by-one (robust method)
                    for (const asset of assetsToCache) {
                        try {
                            await cache.add(new Request(asset, {cache: 'reload'}));
                        } catch (err) {
                            // Log a warning, but don't stop the loop
                            console.warn(`Failed to cache asset: ${asset}`, err);
                        }
                    }
                } catch (err) {
                    console.error('Failed to cache dynamic assets:', err);
                }
                
                console.log('All assets processed');
                self.skipWaiting();
            })
            .catch(err => {
                // This catch is for errors opening the cache itself
                console.error('Cache open failed:', err);
            })
    );
});


// Activate event: clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
        .then(() => self.clients.claim())
    );
});

// Fetch event: apply caching strategy
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Ignore non-http/https requests (like chrome-extension://)
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // ★★★ START: โค้ดที่เพิ่มเข้ามาแก้ไขบั๊ก ★★★
    //
    // 0. Only cache GET requests. 
    // Ignore POST, PUT, DELETE, etc.
    if (event.request.method !== 'GET') {
        console.log(`Fetch (skipping cache, non-GET): ${event.request.method} ${event.request.url}`);
        return; // Let the browser handle it without caching
    }
    //
    // ★★★ END: โค้ดที่เพิ่มเข้ามาแก้ไขบั๊ก ★★★


    // 1. Exclude specified JS files from caching
    if (EXCLUDED_FILES.includes(url.pathname)) { //
        console.log(`Fetch (network only): ${event.request.url}`);
        return;
    }
    if (url.pathname.startsWith('/export/')) {
        console.log(`Fetch (network only, bypassing SW cache): ${event.request.url}`);
        return; 
    }
    // 2. Handle navigation requests (HTML pages)
    if (event.request.mode === 'navigate') { //
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    // On network failure, serve the offline page from cache
                    return caches.match(OFFLINE_URL);
                })
        );
        return;
    }

    // 3. Stale-While-Revalidate for all other requests (CSS, JS, images, etc.)
    event.respondWith( //
        caches.open(CACHE_NAME).then(cache => {
            return cache.match(event.request).then(cachedResponse => {
                const fetchPromise = fetch(event.request).then(networkResponse => {
                    // If the request is successful, update the cache
                    if (networkResponse && networkResponse.status === 200) {
                        cache.put(event.request, networkResponse.clone());
                    }
                    return networkResponse;
                });

                // Return cached response immediately, then update from network
                return cachedResponse || fetchPromise;
            });
        })
    );
});