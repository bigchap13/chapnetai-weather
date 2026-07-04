self.addEventListener("install", function (event) {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", function (event) {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = {title: "Watchman Weather Alert", body: event.data ? event.data.text() : ""};
  }

  const title = data.title || "Watchman Weather Alert";
  const options = {
    body: data.body || "Weather risk changed near your current phone location.",
    tag: data.tag || data.deviceId || "watchman-weather-alert",
    badge: "/static/favicon.ico",
    icon: "/static/favicon.ico",
    data: {
      url: data.url || "/",
      extra: data.extra || {}
    }
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();

  const targetUrl = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    self.clients.matchAll({type: "window", includeUncontrolled: true}).then(function (clients) {
      for (const client of clients) {
        if ("focus" in client) {
          client.focus();
          return;
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
