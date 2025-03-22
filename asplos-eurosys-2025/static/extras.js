function patchShadowRooms(shadowRoot) {
  const sessions = shadowRoot.querySelectorAll(".c-linear-schedule-session");
  sessions.forEach((session) => {
    const trackDiv = session.querySelector(".track");
    const roomDiv = session.querySelector(".room");
    if (trackDiv && trackDiv.textContent.trim() === "Catering area") {
        if (roomDiv) {
            // Copy track text to room
            roomDiv.textContent = trackDiv.textContent;
            // Clear the track
            trackDiv.textContent = "";
        }

        // Set href="" on the nearest <a> ancestor
        const anchor = trackDiv.closest("a");
        if (anchor) {
          anchor.removeAttribute("href");
        }
    }
  });
}

function observePretalxSchedule() {
  const schedule = document.querySelector("pretalx-schedule");
  if (!schedule) return;
  const tryPatch = () => {
    const root = schedule.shadowRoot;
    if (!root) return;
    patchShadowRooms(root);
    const shadowObserver = new MutationObserver(() => patchShadowRooms(root));
    shadowObserver.observe(root, { childList: true, subtree: true });
  };
  const outerObserver = new MutationObserver(tryPatch);
  outerObserver.observe(schedule, { attributes: true, childList: true });
  tryPatch();
}

window.addEventListener("load", observePretalxSchedule);
