const CACHE_NAME = 'aset-dashboard-cache-v1';
const urlsToCache = [
    '/',
    '/dashboard',
    '/input',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png',
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

// 🌐 Fetch event
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            if (response) {
                return response; // ✅ Use cached version
            }
            return fetch(event.request) // 🔄 Try to fetch from network
                .catch(() => {
                    // ❌ Offline fallback (optional: serve offline.html here)
                    if (event.request.mode === 'navigate') {
                        return caches.match('/dashboard');
                    }
                });
        })
    );
});
