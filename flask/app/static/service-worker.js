const CACHE_NAME = 'stocking-app-cache-v5'; // Incremented cache version
const OFFLINE_URL = '/waiting';

// List of assets to cache on installation
const ASSETS_TO_CACHE = [
    '/homepage',
    '/waiting',
    '/static/css/adminlist.css',
    '/static/css/appearance.css',
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
    '/static/ico/contact_page_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg',
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
    '/static/ico/pman.jpg',
    '/static/ico/profile.png',
    '/static/ico/qr_code_scanner_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/qr_icon.png',
    '/static/ico/reply.png',
    '/static/ico/routine_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/search_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/search_icon.png',
    '/static/ico/search.png',
    '/static/ico/settings_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/stock.png',
    '/static/ico/stock_logo.png',
    '/static/ico/thailand.png',
    '/static/ico/translate_24dp_E3E3E3_FILL1_wght400_GRAD0_opsz24.svg',
    '/static/ico/united-kingdom.png',
    '/static/img/2025-09-28_015248.png',
    '/static/img/2025-09-28_025152.png',
    '/static/img/2025-09-28_170205.png',
    '/static/img/2025-10-13_015603.png',
    '/static/img/9412918c-6ca6-4ade-8673-53cf6ce97856.gif',
    '/static/img/Ballpoint_Pen.jpg',
    '/static/img/duck.png',
    '/static/img/duck_test.jpeg',
    '/static/img/edit_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg',
    '/static/img/Electric_Drill.jpg',
    '/static/img/External_HDD_1TB.jpg',
    '/static/img/Hammer.jpg',
    '/static/img/Highlighter_Set.jpg',
    '/static/img/Laptop_Dell_XPS.jpg',
    '/static/img/Mechanical_Keyboard.jpg',
    '/static/img/Monitor_24.jpg',
    '/static/img/Notebook_A5.jpg',
    '/static/img/Paper_Clips_Box.jpg',
    '/static/img/pngtree-chubby-emoji-emoticon-rubbing-his-belly-png-image_4708253.png',
    '/static/img/rabbit.jpg',
    '/static/img/rsz_s-l1600.png',
    '/static/img/Screenshot_11.png',
    '/static/img/Screenshot_13_cropped.png',
    '/static/img/Screenshot_2.png',
    '/static/img/Screenshot_2025-05-25_013901.png',
    '/static/img/Screenshot_3.png',
    '/static/img/Screwdriver_Set.jpg',
    '/static/img/s-l1600.png',
    '/static/img/Stapler.jpg',
    '/static/img/Strawberry_Stick_Cookie.jpg',
    '/static/img/sup_bro.jpg',
    '/static/img/Tape_Measure.jpg',
    '/static/img/think-emoji.gif',
    '/static/img/troll.jpg',
    '/static/img/Wireless_Mouse.jpg',
    '/static/img/Wrench.jpg',
    '/static/manifest.json',
    '/static/service-worker.js'
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