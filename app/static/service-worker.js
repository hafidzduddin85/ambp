const CACHE_NAME = 'aset-dashboard-cache-v1';
const urlsToCache = [
    '/',
    '/dashboard',
    '/input',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png'
    // Removed external CDN link from pre-cache list
];

// List of external resources to cache on fetch
const externalResources = [
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// 🔧 Install event
self.addEventListener('install', event => {
    console.log('📦 Service Worker: Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('📁 Caching app shell...');
            return cache.addAll(urlsToCache);
        })
    );
});

// 🔁 Activate event
self.addEventListener('activate', event => {
    console.log('⚙️ Service Worker: Activated');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(name => {
                    if (name !== CACHE_NAME) {
                        console.log('🧹 Deleting old cache:', name);
                        return caches.delete(name);
                    }
                })
            );
        })
    );
});

// 🔄 Fetch event
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            if (response) {
                return response; // ✅ Use cached version
            }
            return fetch(event.request).then(networkResponse => {
                // Optionally cache external resources on fetch
                if (
                    networkResponse &&
                    networkResponse.status === 200 &&
                    externalResources.some(url => event.request.url.startsWith(url))
                ) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, networkResponse.clone());
                    });
                }
                return networkResponse;
            }).catch(() => {
                // ❌ Offline fallback (optional: serve offline.html here)
                if (event.request.mode === 'navigate') {
                    return caches.match('/dashboard');
                }
            });
        })
    );
});
