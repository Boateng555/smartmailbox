// Service Worker for Smart Mailbox PWA
const CACHE_NAME = 'smartmailbox-v2.0';
const RUNTIME_CACHE = 'smartmailbox-runtime-v2.0';
const IMAGE_CACHE = 'smartmailbox-images-v2.0';
const OFFLINE_PAGE = '/';

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/dashboard',
  '/gallery/',
  '/settings/',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE && cacheName !== IMAGE_CACHE) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests (except CDN resources)
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin && !url.hostname.includes('cdn.tailwindcss.com')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        // Return cached version if available
        if (cachedResponse) {
          // For images, also try to update cache in background
          if (event.request.destination === 'image') {
            fetch(event.request).then((response) => {
              if (response && response.status === 200) {
                caches.open(IMAGE_CACHE).then((cache) => {
                  cache.put(event.request, response.clone());
                });
              }
            }).catch(() => {});
          }
          return cachedResponse;
        }

        // Otherwise fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses or non-basic responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            // Cache images separately for better management
            const cacheToUse = event.request.destination === 'image' ? IMAGE_CACHE : RUNTIME_CACHE;
            
            caches.open(cacheToUse)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // If network fails, try to return a cached offline page
            if (event.request.destination === 'document') {
              return caches.match(OFFLINE_PAGE) || caches.match('/');
            }
            // For images, return a placeholder
            if (event.request.destination === 'image') {
              return new Response(
                '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#f3f4f6"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#9ca3af" font-family="sans-serif" font-size="14">Offline</text></svg>',
                { headers: { 'Content-Type': 'image/svg+xml' } }
              );
            }
            // For other requests, return a basic offline response
            return new Response('Offline', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({
                'Content-Type': 'text/plain'
              })
            });
          });
      })
  );
});

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');
  
  let notificationData = {
    title: 'Smart Camera',
    body: 'You have a new notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-192x192.png',
    tag: 'smartcamera-notification',
    requireInteraction: false,
  };

  // Parse push data if available
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = {
        ...notificationData,
        ...data,
      };
    } catch (e) {
      notificationData.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, {
      body: notificationData.body,
      icon: notificationData.icon,
      badge: notificationData.badge,
      tag: notificationData.tag,
      requireInteraction: notificationData.requireInteraction || false,
      data: notificationData.data || {},
      actions: notificationData.actions || [
        { action: 'view', title: 'View Device' },
        { action: 'dismiss', title: 'Dismiss' }
      ],
      vibrate: [200, 100, 200],
      sound: '/static/notification.mp3', // Optional sound file
    })
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  event.notification.close();

  const notificationData = event.notification.data || {};
  const urlToOpen = notificationData.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync event (for offline actions)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-device-data') {
    event.waitUntil(
      syncDeviceData()
    );
  }
  
  if (event.tag === 'sync-captures') {
    event.waitUntil(
      syncCaptures()
    );
  }
});

// Sync device data when back online
async function syncDeviceData() {
  try {
    // Get pending sync data from IndexedDB or cache
    // This is a placeholder - implement based on your needs
    console.log('[Service Worker] Syncing device data...');
    return Promise.resolve();
  } catch (error) {
    console.error('[Service Worker] Sync error:', error);
    throw error;
  }
}

// Sync captures when back online
async function syncCaptures() {
  try {
    console.log('[Service Worker] Syncing captures...');
    // Implement capture sync logic here
    return Promise.resolve();
  } catch (error) {
    console.error('[Service Worker] Capture sync error:', error);
    throw error;
  }
}

// Message event (for communication with main thread)
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(RUNTIME_CACHE).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }
});

