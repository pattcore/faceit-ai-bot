(function () {
  function openOverlay(nickname) {
    try {
      const existing = document.getElementById("faceit-ai-bot-overlay");
      const baseUrl = chrome.runtime.getURL("popup.html");
      const src = `${baseUrl}?mode=overlay&nickname=${encodeURIComponent(
        nickname || ""
      )}`;

      if (existing) {
        const frame = existing.querySelector("iframe");
        if (frame) {
          frame.src = src;
        }
        existing.style.display = "flex";
        return;
      }

      const overlay = document.createElement("div");
      overlay.id = "faceit-ai-bot-overlay";
      overlay.style.position = "fixed";
      overlay.style.top = "0";
      overlay.style.right = "0";
      overlay.style.width = "380px";
      overlay.style.height = "100%";
      overlay.style.zIndex = "99999";
      overlay.style.backgroundColor = "#020617";
      overlay.style.borderLeft = "1px solid rgba(15,23,42,0.9)";
      overlay.style.boxShadow = "0 10px 25px rgba(0,0,0,0.7)";
      overlay.style.display = "flex";
      overlay.style.flexDirection = "column";

      const header = document.createElement("div");
      header.style.display = "flex";
      header.style.alignItems = "center";
      header.style.justifyContent = "space-between";
      header.style.padding = "8px 10px";
      header.style.borderBottom = "1px solid #111827";

      const title = document.createElement("div");
      title.textContent = "Faceit AI Bot";
      title.style.fontSize = "13px";
      title.style.fontWeight = "600";
      title.style.color = "#f9fafb";

      const close = document.createElement("button");
      close.textContent = "×";
      close.style.border = "none";
      close.style.background = "transparent";
      close.style.color = "#9ca3af";
      close.style.cursor = "pointer";
      close.style.fontSize = "18px";
      close.addEventListener("click", () => {
        overlay.style.display = "none";
      });

      header.appendChild(title);
      header.appendChild(close);

      const frame = document.createElement("iframe");
      frame.style.border = "none";
      frame.style.width = "100%";
      frame.style.height = "100%";
      frame.src = src;

      overlay.appendChild(header);
      overlay.appendChild(frame);

      document.body.appendChild(overlay);
    } catch (e) {}
  }

  function tryInjectButton() {
    try {
      const host = window.location.hostname.toLowerCase();
      // Allow only faceit.com and its subdomains, not arbitrary hosts that
      // merely contain "faceit.com" inside the hostname.
      const isFaceitHost =
        host === "faceit.com" || host.endsWith(".faceit.com");
      if (!isFaceitHost) return;

      const path = window.location.pathname.toLowerCase();
      const idx = path.indexOf("/players/");
      if (idx === -1) return;

      const nicknameRaw = window.location.pathname.substring(idx + 9).split("/")[0];
      const nickname = decodeURIComponent(nicknameRaw || "");
      if (!nickname) return;

      if (document.querySelector("#faceit-ai-bot-analyze-player")) return;

      const button = document.createElement("button");
      button.id = "faceit-ai-bot-analyze-player";
      button.textContent = "Analyze player with Faceit AI Bot";
      button.style.position = "fixed";
      button.style.bottom = "20px";
      button.style.right = "20px";
      button.style.zIndex = "99999";
      button.style.padding = "8px 14px";
      button.style.borderRadius = "9999px";
      button.style.border = "none";
      button.style.cursor = "pointer";
      button.style.backgroundImage = "linear-gradient(to right, #f97316, #facc15)";
      button.style.color = "#f9fafb";
      button.style.fontSize = "13px";
      button.style.fontWeight = "600";
      button.style.boxShadow = "0 10px 15px -3px rgba(0,0,0,0.3)";

      button.addEventListener("click", () => {
        openOverlay(nickname);
      });

      document.body.appendChild(button);
    } catch (e) {
      // Fail silently, do not break the Faceit page
    }
  }

  // Initial run on page load
  tryInjectButton();

  // Support SPA-style navigation on Faceit: react to pathname changes
  let lastPath = window.location.pathname;
  setInterval(() => {
    const currentPath = window.location.pathname;
    if (currentPath !== lastPath) {
      lastPath = currentPath;
      tryInjectButton();
    }
  }, 1500);
})();
