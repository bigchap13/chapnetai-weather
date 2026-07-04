(function () {
  const POLL_MS = 15000;

  async function notify(push) {
    if (!("Notification" in window)) return;

    if (Notification.permission === "default") {
      await Notification.requestPermission();
    }

    if (Notification.permission !== "granted") return;

    new Notification(push.title || "Watchman Alert", {
      body: push.body || "",
      tag: "watchman-" + push.id,
      requireInteraction: push.severity === "urgent" || push.severity === "emergency",
      data: push
    });

    await fetch("/api/watchman/phone/push/ack?id=" + encodeURIComponent(push.id));
  }

  async function pollWatchmanPushes() {
    try {
      const res = await fetch("/api/watchman/phone/push/pending", { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      for (const push of data.pushes || []) await notify(push);
    } catch (e) {}
  }

  window.WatchmanPhonePush = {
    start: function () {
      pollWatchmanPushes();
      setInterval(pollWatchmanPushes, POLL_MS);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", window.WatchmanPhonePush.start);
  } else {
    window.WatchmanPhonePush.start();
  }
})();
