(function () {
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
        const url = `https://pattmsc.online/analysis?nickname=${encodeURIComponent(nickname)}`;
        window.open(url, "_blank");
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
