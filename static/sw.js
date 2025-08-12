// Safe Service Worker - No caching to avoid errors
console.log('Service Worker loaded');

self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // Don't cache dashboard or mobile app routes
  if (event.request.url.includes('/dashboard') || event.request.url.includes('/mobile/app')) {
    // Let these requests pass through normally without caching
    return;
  }
  
  // For all other requests, just fetch normally
}); 