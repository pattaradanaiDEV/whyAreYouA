const CACHE_NAME = 'stocking-app-cache-v3'; // Incremented cache version
const OFFLINE_URL = '/waiting';

// List of assets to cache on installation
const ASSETS_TO_CACHE = [
    '/homepage',
    '/waiting',
    '/static/css/adminlist.css',
    '/static/css/cart.css',
    '/static/css/category.css',
    '/static/css/createpin.css',
    '/static/css/history.css',
    '/static/css/home.css',
    '/static/css/languages.css',
    '/static/css/loginA.css',
    '/static/css/loginB.css',
    '/static/css/modal.css',
    '/static/css/newitem.css',
    '/static/css/notification.css',
    '/static/css/pendingadmin.css',
    '/static/css/setting.css',
    '/static/css/statistic.css',
    '/static/css/stockmenu.css',
    '/static/css/test.css',
    '/static/fonts/open-iconic.eot',
    '/static/fonts/open-iconic.otf',
    '/static/fonts/open-iconic.svg',
    '/static/fonts/open-iconic.ttf',
    '/static/fonts/open-iconic.woff',
    '/static/ico/3p_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/account_circle_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/add_circle_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/addStock.png',
    '/static/ico/alphabet-thai.svg',
    '/static/ico/arrow_back_ios_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/bar_chart_4_bars_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/bin.png',
    '/static/ico/cart.png',
    '/static/ico/category.png',
    '/static/ico/check_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/check_circle_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/dark_mode_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/default_image.png',
    '/static/ico/history_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/inventory_2_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/language_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/light_mode_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/logout_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/notification.png',
    '/static/ico/notifications_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/pen_top.webp',
    '/static/ico/person_add_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/person_add2.png',
    '/static/ico/profile.png',
    '/static/ico/qr_code_scanner_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/qr_icon.png',
    '/static/ico/reply.png',
    '/static/ico/search_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/search_icon.png',
    '/static/ico/search.png',
    '/static/ico/settings_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/stock.png',
    '/static/ico/stock_logo.png',
    '/static/ico/thailand.png',
    '/static/ico/translate_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/united-kingdom.png'
];

// Files to exclude from caching
const EXCLUDED_FILES = [
    '/js/darkmode.js',
    '/js/language.js'
];

// Install event: cache all assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                // Cache the offline fallback page
                cache.add(new Request(OFFLINE_URL, {cache: 'reload'}));
                // Cache all static assets
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => {
                console.log('All assets cached');
                self.skipWaiting();
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

    // 1. Exclude specified JS files from caching
    if (EXCLUDED_FILES.includes(url.pathname)) {
        console.log(`Fetch (network only): ${event.request.url}`);
        return;
    }

    // 2. Handle navigation requests (HTML pages)
    if (event.request.mode === 'navigate') {
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
    event.respondWith(
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