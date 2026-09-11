/**
 * Vastgoed AI Dealfinder — Background Service Worker
 * Communiceert met de backend API voor analyses.
 */

const DEFAULT_API_BASE = "http://localhost:8000";

// ── Settings laden ─────────────────────────────────────────────────────────

async function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      {
        apiBase: DEFAULT_API_BASE,
        apiKey: "dev_key_change_in_prod",
        minScore: 70,
        minROI: 15,
        minProfit: 30000,
        grades: ["A", "B"],
        theme: "dark",
      },
      resolve
    );
  });
}

// ── Message Handler ────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeListing") {
    handleAnalyze(request.listing, request.source)
      .then((analysis) => sendResponse({ analysis }))
      .catch((err) => sendResponse({ error: err.message }));
    return true; // Async response
  }

  if (request.action === "getSettings") {
    getSettings().then(sendResponse);
    return true;
  }

  if (request.action === "saveSettings") {
    chrome.storage.local.set(request.settings, () => sendResponse({ ok: true }));
    return true;
  }

  if (request.action === "getSavedDeals") {
    chrome.storage.local.get("savedDeals", (data) => {
      sendResponse({ deals: data.savedDeals || [] });
    });
    return true;
  }

  if (request.action === "clearSavedDeals") {
    chrome.storage.local.set({ savedDeals: [] }, () => sendResponse({ ok: true }));
    return true;
  }
});

// ── Analyse API aanroep ────────────────────────────────────────────────────

async function handleAnalyze(listing, source) {
  const settings = await getSettings();
  const { apiBase, apiKey } = settings;

  const payload = {
    url: listing.url,
    address: listing.address,
    price_ask: listing.price_ask,
    size_sqm: listing.size_sqm,
    rooms: listing.rooms,
    bedrooms: listing.bedrooms,
    year_built: listing.year_built,
    city: listing.city,
    postcode: listing.postcode,
    description: listing.description,
    image_urls: listing.image_urls || [],
    source: source,
  };

  const response = await fetch(`${apiBase}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API ${response.status}: ${errorText}`);
  }

  const data = await response.json();

  // Stuur notificatie als deal goed is
  if (shouldNotify(data, settings)) {
    sendNotification(data, listing);
  }

  return data;
}

// ── Notificaties ───────────────────────────────────────────────────────────

function shouldNotify(analysis, settings) {
  return (
    analysis.deal_score >= settings.minScore &&
    settings.grades.includes(analysis.deal_grade) &&
    analysis.roi_percentage >= settings.minROI &&
    analysis.potential_profit >= settings.minProfit
  );
}

function sendNotification(analysis, listing) {
  const grade = analysis.deal_grade;
  const profit = Math.round(analysis.potential_profit || 0).toLocaleString("nl-NL");
  const city = listing.city || "";

  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon-128.png",
    title: `🏠 Deal Grade ${grade} gevonden in ${city}!`,
    message: `Potentiële winst: €${profit} | ROI: ${(analysis.roi_percentage || 0).toFixed(1)}%`,
    buttons: [{ title: "Bekijk" }],
    priority: 2,
  });
}

// Klik op notificatie knop
chrome.notifications.onButtonClicked.addListener((notificationId) => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.reload(tabs[0].id);
    }
  });
});
