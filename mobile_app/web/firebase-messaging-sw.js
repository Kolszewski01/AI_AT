// Firebase Messaging Service Worker for background push notifications
// This file MUST be named firebase-messaging-sw.js and be in the web root

importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Firebase configuration from FlutterFire CLI
const firebaseConfig = {
  apiKey: "AIzaSyCpYoMgTY0a5zzQGFYi29BKWrHRJen1ugI",
  authDomain: "ai-at-2d172.firebaseapp.com",
  projectId: "ai-at-2d172",
  storageBucket: "ai-at-2d172.firebasestorage.app",
  messagingSenderId: "1074309111656",
  appId: "1:1074309111656:web:685c3ddd7568a26df380dd"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Background message received:', payload);

  const notificationTitle = payload.notification?.title || 'Trading Alert';
  const notificationOptions = {
    body: payload.notification?.body || '',
    icon: '/icons/Icon-192.png',
    badge: '/icons/Icon-192.png',
    tag: payload.data?.alertId || 'trading-alert',
    data: payload.data,
    requireInteraction: true, // Keep notification visible until user interacts
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[firebase-messaging-sw.js] Notification clicked:', event);
  event.notification.close();

  // Open the app or focus existing window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // If app is already open, focus it
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            return client.focus();
          }
        }
        // Otherwise open new window
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
  );
});
