(function () {
  const DEVICE_KEY = "watchmanCurrentDeviceId";
  const STATUS_ID = "watchman-gps-notification-status";

  function getDeviceId() {
    let id = localStorage.getItem(DEVICE_KEY);
    if (!id) {
      id = "watchman-device-" + Math.random().toString(16).slice(2) + Date.now().toString(16);
      localStorage.setItem(DEVICE_KEY, id);
    }
    return id;
  }

  function setStatus(text) {
    const el = document.getElementById(STATUS_ID);
    if (el) el.textContent = text;
  }

  async function postJson(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    return await res.json();
  }

  async function registerDevice() {
    return await postJson("/api/watchman/device/register", {
      deviceId: getDeviceId(),
      notificationPermission: Notification.permission,
      userAgent: navigator.userAgent || ""
    });
  }

  async function sendLocation(position) {
    const c = position.coords;
    const data = await postJson("/api/watchman/device/location", {
      deviceId: getDeviceId(),
      lat: c.latitude,
      lon: c.longitude,
      accuracy: c.accuracy
    });

    const risk = data.lastRisk || {};
    setStatus("Location allowed · notifications " + Notification.permission + " · last risk " + (risk.risk || "checking"));
  }

  async function pollPending() {
    const deviceId = encodeURIComponent(getDeviceId());
    const res = await fetch("/api/watchman/device/push/pending?deviceId=" + deviceId);
    const data = await res.json();

    if (!data.pushes) return;

    for (const push of data.pushes) {
      if (Notification.permission === "granted") {
        new Notification(push.title || "Watchman Weather Alert", {
          body: push.body || "Weather changed near your current phone location.",
          tag: push.id
        });
      }

      await fetch("/api/watchman/device/push/ack?id=" + encodeURIComponent(push.id) + "&deviceId=" + deviceId, {
        method: "POST"
      });
    }
  }

  async function enableWatchmanGpsNotifications() {
    if (!("Notification" in window)) {
      setStatus("Notifications are not supported in this browser.");
      return;
    }

    if (!navigator.geolocation) {
      setStatus("Location is not supported in this browser.");
      return;
    }

    setStatus("Requesting notification permission...");
    if (Notification.permission !== "granted") {
      await Notification.requestPermission();
    }

    await registerDevice();

    setStatus("Requesting current phone location...");
    navigator.geolocation.watchPosition(
      sendLocation,
      function (err) {
        setStatus("Location permission needed for current-device weather alerts.");
      },
      {
        enableHighAccuracy: false,
        maximumAge: 60000,
        timeout: 15000
      }
    );

    setInterval(pollPending, 15000);
    pollPending();
  }

  window.enableWatchmanGpsNotifications = enableWatchmanGpsNotifications;

  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("watchman-enable-gps-notifications");
    if (btn) {
      btn.addEventListener("click", enableWatchmanGpsNotifications);
    }
  });
})();
