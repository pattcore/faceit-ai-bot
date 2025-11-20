(function () {
  try {
    const host = window.location.hostname.toLowerCase();
    // Allow only steamcommunity.com and its subdomains, not arbitrary hosts
    // that merely contain "steamcommunity.com" inside the hostname.
    const isSteamHost =
      host === "steamcommunity.com" || host.endsWith(".steamcommunity.com");
    if (!isSteamHost) return;

    if (document.querySelector("#faceit-ai-bot-open-site")) return;

    const button = document.createElement("button");
    button.id = "faceit-ai-bot-open-site";
    button.textContent = "Open Faceit AI Bot";
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
      const url = "https://pattmsc.online";
      window.open(url, "_blank");
    });

    document.body.appendChild(button);
  } catch (e) {
    // Fail silently
  }
})();
