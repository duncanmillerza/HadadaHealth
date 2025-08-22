const CACHE_NAME = 'hadadahealth-v1';
const OFFLINE_URL = '/offline.html';

// Files to cache for offline functionality
const STATIC_CACHE_URLS = [
  '/',
  '/static/calendar.css',
  '/static/nav.css',
  '/static/cards.css',
  '/static/forms.css',
  '/static/table.css',
  '/static/css/appointment-type-modal.css',
  '/static/css/outcome-measures.css',
  '/static/js/nav-bar.js',
  '/static/js/booking-table.js',
  '/static/js/patient-modal.js',
  '/static/js/appointment-type-modal.js',
  '/static/js/calendar-appointment-type-integration.js',
  '/static/hadada_health_logo.svg',
  '/static/Hadada Health Logo Light.svg',
  '/static/favicon.ico',
  '/static/fonts/MaterialIcons-Regular.woff2',
  '/static/fonts/MaterialIcons-Regular.ttf'
];

// API endpoints to cache
const API_CACHE_URLS = [
  '/api/appointments',
  '/api/patients',
  '/api/therapists'
];

// Install event - cache static resources
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching static resources');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('Service Worker installed');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
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
    }).then(() => {
      console.log('Service Worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // If successful, cache the response for offline use
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // If network fails, try to serve from cache
          return caches.match(request)
            .then(cachedResponse => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // Return offline data structure for critical endpoints
              if (url.pathname === '/api/appointments') {
                return new Response(JSON.stringify([]), {
                  headers: { 'Content-Type': 'application/json' }
                });
              }
              if (url.pathname === '/api/patients') {
                return new Response(JSON.stringify([]), {
                  headers: { 'Content-Type': 'application/json' }
                });
              }
              throw new Error('No cached response available');
            });
        })
    );
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.match('/') || caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  // Handle static resources with cache-first strategy
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request)
          .then(response => {
            // Cache successful responses for static resources
            if (response.ok && (
              request.url.includes('/static/') ||
              request.url.includes('/templates/')
            )) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(cache => {
                cache.put(request, responseClone);
              });
            }
            return response;
          });
      })
  );
});

// Handle background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('Background sync triggered');
    event.waitUntil(syncOfflineActions());
  }
});

// Sync offline actions when network is available
async function syncOfflineActions() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const offlineActions = await cache.match('/offline-actions');
    
    if (offlineActions) {
      const actions = await offlineActions.json();
      
      for (const action of actions) {
        try {
          await fetch(action.url, {
            method: action.method,
            headers: action.headers,
            body: action.body
          });
        } catch (error) {
          console.error('Failed to sync action:', error);
        }
      }
      
      // Clear synced actions
      await cache.delete('/offline-actions');
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Handle push notifications (for future use)
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/static/hadada_health_logo.svg',
      badge: '/static/favicon.ico',
      vibrate: [200, 100, 200],
      data: data
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});