const CACHE_NAME = 'invi-premium-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/css/templates.css',
  '/static/js/main.js',
  '/static/js/envelope.js',
  '/static/manifest.json'
];

// Instalar el Service Worker y almacenar recursos en caché
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Almacenando assets en caché...');
      return cache.addAll(ASSETS_TO_CACHE).catch(err => console.log("Error al cachear assets iniciales:", err));
    })
  );
  self.skipWaiting();
});

// Activar y limpiar cachés antiguas
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Limpiando caché antigua:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Estrategia de red con fallback a caché
self.addEventListener('fetch', (event) => {
  // Solo interceptar peticiones GET locales
  if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
    return;
  }
  
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clonar y almacenar la respuesta exitosa en la caché
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // En caso de fallo de red, retornar de la caché
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Si no está en caché, retornar página básica de offline
          return new Response('Sin conexión a Internet. Por favor verifica tu red.', {
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        });
      })
  );
});
