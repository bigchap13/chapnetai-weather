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


  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function setupServiceWorkerPush() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      return {ok: false, reason: "service_worker_push_not_supported"};
    }

    const keyRes = await fetch("/api/watchman/web-push/public-key");
    const keyData = await keyRes.json();

    if (!keyData.enabled || !keyData.publicKey) {
      return {ok: false, reason: "vapid_not_ready"};
    }

    const registration = await navigator.serviceWorker.register("/static/watchman_service_worker.js");
    await navigator.serviceWorker.ready;

    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(keyData.publicKey)
      });
    }

    return await postJson("/api/watchman/web-push/subscribe", {
      deviceId: getDeviceId(),
      subscription: subscription.toJSON(),
      userAgent: navigator.userAgent || ""
    });
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

    try {
      const pushStatus = await setupServiceWorkerPush();
      if (pushStatus && pushStatus.ok) {
        setStatus("Background push enabled · requesting current phone location...");
      }
    } catch (e) {
      console.warn("Watchman web push setup skipped", e);
    }

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
